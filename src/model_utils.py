from models.td_models import Concat
from models.td_models import ConcatConv
from models.td_models import RNN2Conv
from models.td_models import LingUNet
from models.visualbert import VisualBert
from models.lxmert import LXMERTLocalizer

import torch

from detectron2.modeling.postprocessing import detector_postprocess
from detectron2.modeling.roi_heads.fast_rcnn import FastRCNNOutputs
from torchvision.ops import nms
from detectron2.structures import Boxes, Instances
import numpy as np
MIN_BOXES = 36
MAX_BOXES = 36


def get_localizer(args, n_vocab):
  '''Return a localizer module.
  '''
  args.use_raw_image = False
  rnn_args = {}
  rnn_args['input_size'] = n_vocab
  rnn_args['embed_size'] = args.n_emb
  rnn_args['rnn_hidden_size'] = int(args.n_hid /
                                    2) if args.bidirectional else args.n_hid
  rnn_args['num_rnn_layers'] = args.n_layers
  rnn_args['embed_dropout'] = args.dropout
  rnn_args['bidirectional'] = args.bidirectional
  rnn_args['reduce'] = 'last' if not args.bidirectional else 'mean'

  cnn_args = {}
  out_layer_args = {'linear_hidden_size': args.n_hid,
                    'num_hidden_layers': args.n_layers}
  image_channels = args.n_img_channels

  if args.model == 'concat':
    model = Concat(rnn_args, out_layer_args,
                   image_channels=image_channels)

  elif args.model == 'concat_conv':
    cnn_args = {'kernel_size': 5, 'padding': 2,
                'num_conv_layers': args.n_layers, 'conv_dropout': args.dropout}
    model = ConcatConv(rnn_args, cnn_args, out_layer_args,
                       image_channels=image_channels)

  elif args.model == 'rnn2conv':
    assert args.n_layers is not None
    cnn_args = {'kernel_size': 5, 'padding': 2,
                'conv_dropout': args.dropout}
    model = RNN2Conv(rnn_args, cnn_args, out_layer_args,
                     args.n_layers,
                     image_channels=image_channels)

  elif args.model == 'lingunet':
    assert args.n_layers is not None
    cnn_args = {'kernel_size': 5, 'padding': 2,
                'deconv_dropout': args.dropout}
    model = LingUNet(rnn_args, cnn_args, out_layer_args,
                     m=args.n_layers,
                     image_channels=image_channels)
  elif args.model == 'visualbert':
    args.use_masks = True
    model = VisualBert(args, n_vocab)
  elif args.model == 'lxmert':
    args.use_raw_image = True
    model = LXMERTLocalizer(args)
  else:
    raise NotImplementedError('Model {} is not implemented'.format(args.model))
  print('using {} localizer'.format(args.model))
  return model.cuda()


def fast_rcnn_inference_single_image(
    boxes, scores, image_shape, score_thresh, nms_thresh, topk_per_image
):
  scores = scores[:, :-1]
  num_bbox_reg_classes = boxes.shape[1] // 4
  # Convert to Boxes to use the `clip` function ...
  boxes = Boxes(boxes.reshape(-1, 4))
  boxes.clip(image_shape)
  boxes = boxes.tensor.view(-1, num_bbox_reg_classes, 4)  # R x C x 4

  # Select max scores
  max_scores, max_classes = scores.max(1)       # R x C --> R
  num_objs = boxes.size(0)
  boxes = boxes.view(-1, 4)
  idxs = torch.arange(num_objs).cuda() * num_bbox_reg_classes + max_classes
  max_boxes = boxes[idxs]     # Select max boxes according to the max scores.

  # Apply NMS
  keep = nms(max_boxes, max_scores, nms_thresh)
  if topk_per_image >= 0:
    keep = keep[:topk_per_image]
  boxes, scores = max_boxes[keep], max_scores[keep]

  result = Instances(image_shape)
  result.pred_boxes = Boxes(boxes)
  result.scores = scores
  result.pred_classes = max_classes[keep]

  return result, keep


def extract_detectron2_features(detector, raw_images):
  with torch.no_grad():
    # Preprocessing
    inputs = []
    for raw_image in raw_images:
      image = detector.transform_gen.get_transform(
          raw_image).apply_image(raw_image)
      image = torch.as_tensor(image.astype("float32").transpose(2, 0, 1))
      inputs.append(
          {"image": image, "height": raw_image.shape[0], "width": raw_image.shape[1]})
    images = detector.model.preprocess_image(inputs)

    # Run Backbone Res1-Res4
    features = detector.model.backbone(images.tensor)

    # Generate proposals with RPN
    proposals, _ = detector.model.proposal_generator(images, features, None)

    # Run RoI head for each proposal (RoI Pooling + Res5)
    proposal_boxes = [x.proposal_boxes for x in proposals]
    features = [features[f] for f in detector.model.roi_heads.in_features]
    box_features = detector.model.roi_heads._shared_roi_transform(
        features, proposal_boxes
    )
    # (sum_proposals, 2048), pooled to 1x1
    feature_pooled = box_features.mean(dim=[2, 3])

    # Predict classes and boxes for each proposal.
    pred_class_logits, pred_proposal_deltas = detector.model.roi_heads.box_predictor(
        feature_pooled)
    rcnn_outputs = FastRCNNOutputs(
        detector.model.roi_heads.box2box_transform,
        pred_class_logits,
        pred_proposal_deltas,
        proposals,
        detector.model.roi_heads.smooth_l1_beta,
    )

    # Fixed-number NMS
    instances_list, ids_list = [], []
    probs_list = rcnn_outputs.predict_probs()
    boxes_list = rcnn_outputs.predict_boxes()
    for probs, boxes, image_size in zip(probs_list, boxes_list, images.image_sizes):
      for nms_thresh in np.arange(0.3, 1.0, 0.1):
        instances, ids = fast_rcnn_inference_single_image(
            boxes, probs, image_size,
            score_thresh=0.2, nms_thresh=nms_thresh, topk_per_image=MAX_BOXES
        )
        if len(ids) >= MIN_BOXES:
          break
      instances_list.append(instances)
      ids_list.append(ids)

    # Post processing for features
    # (sum_proposals, 2048) --> [(p1, 2048), (p2, 2048), ..., (pn, 2048)]
    features_list = feature_pooled.split(rcnn_outputs.num_preds_per_image)
    roi_features_list = []
    for ids, features in zip(ids_list, features_list):
      roi_features_list.append(features[ids].detach())

    # Post processing for bounding boxes (rescale to raw_image)
    raw_instances_list = []
    for instances, input_per_image, image_size in zip(
        instances_list, inputs, images.image_sizes
    ):
      height = input_per_image.get("height", image_size[0])
      width = input_per_image.get("width", image_size[1])
      raw_instances = detector_postprocess(instances, height, width)
      raw_instances_list.append(raw_instances)

    return raw_instances_list, roi_features_list

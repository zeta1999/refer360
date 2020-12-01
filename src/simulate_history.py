usage = '''
Re-run a history of actions of an agent.
Change DATA_PATH and DETECTRON2_YAML with your paths to those files.

argv[1] : json file for the history
argv[2] : 0 or 1 whether to use detectron for demo
argv[3] : degrees between successive FoVs make sure it is equal to the agent's original FoV increment

examples:
PYTHONPATH=.. python simulate_history.py exp-random/samples/1575_randomagent.json 1 15 
PYTHONPATH=.. python simulate_history.py exp-random/samples/2100_randomagent.json 0 15
'''
DATA_PATH = '../py_bottom_up_attention/demo/data/genome/1600-400-20'
DETECTRON2_YAML = '../py_bottom_up_attention/configs/VG-Detection/faster_rcnn_R_101_C4_caffe.yaml'
import cv2
import sys

import panoramic_camera as camera
import json

# import some common detectron2 utilities
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog
from utils import add_overlay
import numpy as np
import os


def get_det2_features(detections):
  boxes = []
  obj_classes = []

  for box, obj_class in zip(detections.pred_boxes, detections.pred_classes):
    box = box.cpu().detach().numpy()
    boxes.append(box)
    obj_class = obj_class.cpu().detach().numpy().tolist()
    obj_classes.append(obj_class)
  return boxes, obj_classes


if __name__ == '__main__':

  if len(sys.argv) != 4:
    print(usage)
    quit(1)
  history = json.load(open(sys.argv[1], 'r'))
  detectron = int(sys.argv[2])
  increment = int(sys.argv[3])
  if detectron:
    data_path = DATA_PATH
    vg_classes = []
    with open(os.path.join(data_path, 'objects_vocab.txt')) as f:
      for object in f.readlines():
        vg_classes.append(object.split(',')[0].lower().strip())

    MetadataCatalog.get("vg").thing_classes = vg_classes
    yaml_file = DETECTRON2_YAML
    cfg = get_cfg()
    cfg.merge_from_file(yaml_file
                        )
    cfg.MODEL.RPN.POST_NMS_TOPK_TEST = 300
    cfg.MODEL.ROI_HEADS.NMS_THRESH_TEST = 0.6
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.6
    # VG Weight
    cfg.MODEL.WEIGHTS = "http://nlp.cs.unc.edu/models/faster_rcnn_from_caffe.pkl"
    predictor = DefaultPredictor(cfg)

  refer = ".".join([" ".join(refexp) for refexp in history['refexps']])
  n_steps = len(history['lng_diffs'])
  image_path = history['pano']

  waldo_position_lng = history['gt_lng']
  waldo_position_lat = history['gt_lat']

  start_lng = history['start_lat']
  start_lat = history['start_lng']

  pred_lng = history['pred_lng']
  pred_lat = history['pred_lat']

  pred_x = history['pred_x']
  pred_y = history['pred_y']

  print("image_path", image_path)
  print(refer)
  print("start:", start_lat, start_lng)
  print("gt:", waldo_position_lat, waldo_position_lng)
  print("pred:", pred_lat, pred_lng)
  print("pred xy:", pred_x, pred_y)
  print('n_steps:', n_steps)

  full_w, full_h = 4552, 2276
  canvas = np.ones((full_h, full_w, 3), dtype='uint8')*255
  obj_canvas = np.ones((full_h, full_w, 3), dtype='uint8')*255

  size = 20

  x = int(full_w * ((waldo_position_lat + 180)/360.0))
  y = int(full_h - full_h *
          ((waldo_position_lng + 90)/180.0))
  print('lat lng:', waldo_position_lat, waldo_position_lng)
  print('x y:', x, y)
  obj_canvas[y-size:y+size, x-size:x+size, 2] = 255.
  obj_canvas[y-size:y+size, x-size:x+size, :2] = 0

  original = cv2.imread(image_path, cv2.IMREAD_COLOR)
  cam = camera.PanoramicCamera()
  cam.load_img(image_path, convert_color=False)

  waldo_img = cv2.resize(cv2.imread(
      '../data/waldo.png', cv2.IMREAD_COLOR), (60, 40), interpolation=cv2.INTER_AREA)

  target_img = cv2.resize(cv2.imread(
      '../data/target.png', cv2.IMREAD_COLOR), (60, 60), interpolation=cv2.INTER_AREA)

  nn = 0

  lng = start_lng
  lat = start_lat
  objects = []
  THRESHOLD = 10
  font = cv2.FONT_HERSHEY_SIMPLEX
  while True:
    cam.look(lat, lng)
    pixel_map = cam.get_map()
    img = cam.get_image()

    lat_map, lng_map = cam.get_pixel_map()
    mapping = np.stack((lat_map, lng_map), axis=2)
    points = []
    poly_transform = np.stack((lng_map.reshape(400*400, 1),
                               lat_map.reshape(400*400, 1)), axis=1).reshape(400*400, 2)
    poly = []
    h, w = mapping.shape[0], mapping.shape[1]

    debug = []
    for ii in range(h):
      poly.append([mapping[ii][0][0], mapping[ii][0][1]])
    debug.append(poly[0])
    debug.append(poly[-1])
    for ii in range(w):
      poly.append([mapping[w-1][ii][0], mapping[w-1][ii][1]])
    debug.append(poly[-1])
    for ii in range(h):
      poly.append([mapping[h-1-ii][w-1][0], mapping[h-1-ii][w-1][1]])
    debug.append(poly[-1])
    for ii in range(w):
      poly.append([mapping[0][w-1-ii][0], mapping[0][w-1-ii][1]])
    debug.append(poly[-1])
    points.append(np.array(poly))

    color = np.uint8(np.random.rand(3) * 255).tolist()
    canvas[lng_map, lat_map, :] = original[lng_map, lat_map, :]
    canvas = cv2.blur(canvas, (3, 3))

    # tform = PiecewiseAffineTransform()
    # tform.estimate(poly_transform, poly_transform)

    # out_rows = original.shape[0]
    # out_cols = original.shape[1]
    # out = warp(original, tform, output_shape=(out_rows, out_cols))

    if detectron:
      detectron_outputs = predictor(img)
      v = Visualizer(img[:, :, :], MetadataCatalog.get("vg"), scale=1.0)

      v = v.draw_instance_predictions(detectron_outputs["instances"].to("cpu"))
      obj_img = cv2.cvtColor(v.get_image()[:, :, ::-1], cv2.COLOR_RGB2BGR)
      boxes, object_types, _ = get_det2_features(
          detectron_outputs["instances"].to("cpu"))

      for b, o in zip(boxes, object_types):
        center_x = int((b[0]+b[2])/2)
        center_y = int((b[1]+b[3])/2)
        o_lat = pixel_map[center_y][center_x][0]
        o_lng = pixel_map[center_y][center_x][1]

        flag = True
        for r in objects:
          d = ((r[1] - o_lng)**2 + (r[0] - o_lat)**2)**0.5
          if d < THRESHOLD and r[2] == o:
            flag = False
        if flag:
          objects.append((o_lat, o_lng, o))
    else:
      obj_img = img
    waldo_coor = cam.get_image_coordinate_for(
        waldo_position_lat, waldo_position_lng)
    if waldo_coor is not None:
      img = add_overlay(img, waldo_img, waldo_coor, maxt_x=60,
                        maxt_y=40, ignore=[76, 112, 71])
    target_coor = cam.get_image_coordinate_for(pred_lat, pred_lng)
    if target_coor is not None:
      img = add_overlay(img, target_img, target_coor, ignore=[255, 255, 255])

    # cv2.putText(img, 'id', (10, 10), font, 0.3, (0, 0, 255), 1)
    for jj, refexp in enumerate(history['refexps']):
      refer = " ".join(refexp)
      cv2.putText(img, refer, (5, (jj+2)*10), font, 0.35, (0, 0, 255), 1)
    if nn >= n_steps:
      cv2.putText(img, 'ACTIONS ARE OVER', (10, 60), font, 0.4, (255, 0, 0), 1)

      pixel_map = cam.get_map()

      curr_lat = pixel_map[pred_y][pred_x][0]
      curr_lng = pixel_map[pred_y][pred_x][1]

    obj_canvas = np.ones((full_h, full_w, 3), dtype='uint8')*255
    cv2.fillPoly(obj_canvas, points, color)
    for o in objects:
      o_lat, o_lng, o_type = o[0], o[1], o[2]
      x = int(full_w * ((o_lat + 180)/360.0))
      y = int(full_h - full_h *
              ((o_lng + 90)/180.0))
      obj_canvas[y-size:y+size, x-size:x+size, 0] = 255.
      obj_canvas[y-size:y+size, x-size:x+size, 1:] = 0
      o_type = vg_classes[o_type]
      cv2.putText(obj_canvas, o_type, (x, y), font, 3, (255, 0, 0), 5)

    resized_canvas = cv2.resize(canvas, (800, 400))
    resized_obj_canvas = cv2.resize(obj_canvas, (800, 400))

    row1 = np.concatenate((img, resized_canvas), axis=1)
    row2 = np.concatenate((obj_img, resized_obj_canvas), axis=1)
    combined = np.concatenate((row1, row2), axis=0)
    cv2.imshow("Use awsd to move c to close or quit", combined)

    key = cv2.waitKey()

    if nn < n_steps:
      lng = lng + history['lng_diffs'][nn]
      lat = lat + history['lat_diffs'][nn]

      nn += 1
    else:
      if key == 100:
        lat = lat + increment
      elif key == 97:
        lat = lat - increment
      elif key == 119:
        lng = lng + increment
      elif key == 115:
        lng = lng - increment
      elif key == 99:
        data = {
            'poly': poly,
            'mapping':  mapping,
            'lat_map': lat_map,
            'lng_map': lng_map,
            'original': original,
            'canvas': canvas
        }
        np.save('/projects2/chrome_downloads/pwa_data.npy', data)
        break

      if lng < -90:
        lng = -90 - (lng + 90)
        lat = lat + 180
      elif lng > 90:
        lng = 90 - (lng - 90)
        lat = lat + 180
#      lng = min(max(-90, lng), 90)
      lat = (lat + 180) % 360 - 180

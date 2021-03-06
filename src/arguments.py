"""
Arguments for train/test
"""
import argparse


def get_train_rl():
  parser = argparse.ArgumentParser(
      description='advantage-actor-critic RL training for localizing Waldo!')
  parser.add_argument('--multi-gpu',
                      action='store_true', help='Use multiple gpu')

  parser.add_argument('--epoch', type=int, default=200,
                      help='# of epochs to train (default: 200)')
  parser.add_argument('--resume', type=str, default='',
                      help='to resume point for backtranslation (default: "")')
  parser.add_argument('--prefix', type=str, default='rl',
                      help='prefix for model files (default: rl)')
  parser.add_argument('--exp-dir', type=str, default='./exp',
                      help='experiment directory (default: ./exp)')
  parser.add_argument('--data-path', type=str, default='../data',
                      help='data path for loading (default: ../data)')

  # Model parameters
  parser.add_argument('--model', type=str, default='lingunet',
                      help='model name concat2conv, rnn2conv, lingunet, visualbert, textonly, visiononly (default: lingunet)')

  parser.add_argument('--n-img-channels', type=int, default=64,
                      help='# of image channels (default: 64)')
  parser.add_argument('--n-layers', type=int, default=2,
                      help='# of layers for models (default: 2)')
  parser.add_argument('--n-hid', type=int, default=128,
                      help='hidden dimension (default: 128)')
  parser.add_argument('--n-obs', type=int, default=10000,
                      help='pre-trained wordvector size (default: 10000)')
  parser.add_argument('--n-head', type=int, default=8,
                      help='# of heads for transformers (default: 8)')
  parser.add_argument('--n-emb', type=int, default=128,
                      help='pre-trained wordvector size (default: 128)')
  parser.add_argument('--cnn-layer', type=int, default=6,
                      help='cnn layer to use (default: 6)')
  parser.add_argument('--dropout', type=float, default=0.25,
                      help='dropout rate (default: 0.25)')
  parser.add_argument('--bidirectional',
                      action='store_true', help='Use bidirectional RNN')
  parser.add_argument('--wordvec-file', type=str, default='../data/glove.840B.300d.txt',
                      help='data path for loading word vectors (default: ../data/glove.840B.300d.txt)')

  parser.add_argument('--memorize', type=int, default=-1,
                      help='memorize first k batches (default: -1)')
  parser.add_argument('--val-freq', type=int, default=1,
                      help='validation frequency for every n epochs (default: 1)')
  parser.add_argument('--clip', type=float, default=5.0,
                      help='gradient clipping (default: 5.0)')
  parser.add_argument('--metric', type=str, default='fov',
                      help='target metric completion|loss|fov|reward (default: fov)')

  parser.add_argument('--gamma', type=float, default=0.99,
                      help='discount factor (default: 0.99)')
  parser.add_argument('--seed', type=int, default=0,
                      help='random seed (default: 0)')
  parser.add_argument('--log-interval', type=int, default=1,
                      help='interval between training status logs (default: 1)')
  parser.add_argument('--max-step', type=int, default=24,
                      help='Max # of steps (default: 24)')
  parser.add_argument('--batch-size', type=int, default=4,
                      help='Batch size (default: 4)')
  parser.add_argument('--lr', type=float, default=0.00001,
                      help='learning rate (default: 0.00001)')
  parser.add_argument('--weight-decay', type=float, default=0.00001,
                      help='L2 regularization (weight decay) term (default: 0.00001)')
  parser.add_argument('--verbose',
                      action='store_true', help='Print to a progressbar or lines in stdout')
  parser.add_argument('--degrees', type=int, default=15,
                      help='degrees in FoV change, default=15')
  parser.add_argument('--use-gpu-camera',
                      action='store_true', help='Use gpu camera')
  parser.add_argument('--use-look-ahead',
                      action='store_true', help='Use look ahead')
  parser.add_argument('--oracle-mode',
                      action='store_true', help='Oracle Mode')
  parser.add_argument('--random-agent',
                      action='store_true', help='Random agent')
  parser.add_argument('--greedy',
                      action='store_true', help='Greedy action prediction')
  parser.add_argument('--debug', type=int, default=0,
                      help='Debug Mode if debug>0, default = 0')

  parser.add_argument('--trn-images', type=str, default='all',
                      help='list of image categories for training separated by comma, options are restaurant, bedroom, living_room, plaza_courtyard, shop, street or all, default=all')
  parser.add_argument('--val-images', type=str, default='all',
                      help='list of image categories for validation separated by comma, options are restaurant, bedroom, living_room, plaza_courtyard, shop, street or all, default=all')
  parser.add_argument('--use-masks',
                      action='store_true', help='Use masks for text embeddings')
  # LXRT Model Config
  # Note: LXRT = L, X, R (three encoders), Transformer
  parser.add_argument('--loadLXMERT', dest='load_lxmert', type=str, default=None,
                      help='Load the pre-trained LXMERT model.')
  parser.add_argument("--llayers", default=9, type=int,
                      help='Number of Language layers')
  parser.add_argument("--xlayers", default=5, type=int,
                      help='Number of CROSS-modality layers.')
  parser.add_argument("--rlayers", default=5, type=int,
                      help='Number of object Relationship layers.')
  parser.add_argument("--fromScratch", dest='from_scratch', action='store_const', default=False, const=True,
                      help='If none of the --load, --loadLXMERT, --loadLXMERTQA is set, '
                      'the model would be trained from scratch. If --fromScratch is'
                      ' not specified, the model would load BERT-pre-trained weights by'
                      ' default. ')
  parser.add_argument('--use-detectron',
                      action='store_true', help='Use detectron for visual input')

  return parser


def get_train_rl_sentence2sentence():
  parser = get_train_rl()
  parser.add_argument('--max-sentence', type=int, default=5,
                      help='max number of sentences, default=5')
  return parser


def get_train_fovpretraining():
  parser = argparse.ArgumentParser(
      description='FoV pretraining for localizing nearby objects!')
  parser.add_argument('--epoch', type=int, default=200,
                      help='# of epochs to train (default: 200)')
  parser.add_argument('--resume', type=str, default='',
                      help='to resume point for backtranslation (default: "")')
  parser.add_argument('--prefix', type=str, default='rl',
                      help='prefix for model files (default: rl)')
  parser.add_argument('--exp-dir', type=str, default='./exp',
                      help='experiment directory (default: ./exp)')
  parser.add_argument('--data-path', type=str, default='../data',
                      help='data path for loading (default: ../data)')

  # Model parameters
  parser.add_argument('--model', type=str, default='hallucinator',
                      help='model name hallucinator|lxmert (default: hallucinator)')

  parser.add_argument('--n-img-channels', type=int, default=64,
                      help='# of image channels (default: 64)')
  parser.add_argument('--n-layers', type=int, default=2,
                      help='# of layers for models (default: 2)')
  parser.add_argument('--n-hid', type=int, default=128,
                      help='hidden dimension (default: 128)')
  parser.add_argument('--n-obs', type=int, default=10000,
                      help='pre-trained wordvector size (default: 10000)')
  parser.add_argument('--n-head', type=int, default=16,
                      help='# of heads for transformers (default: 16)')
  parser.add_argument('--n-emb', type=int, default=128,
                      help='pre-trained wordvector size (default: 128)')
  parser.add_argument('--cnn-layer', type=int, default=6,
                      help='cnn layer to use (default: 6)')
  parser.add_argument('--dropout', type=float, default=0.25,
                      help='dropout rate (default: 0.25)')
  parser.add_argument('--bidirectional',
                      action='store_true', help='Use bidirectional RNN')
  parser.add_argument('--wordvec-file', type=str, default='../data/glove.840B.300d.txt',
                      help='data path for loading word vectors (default: ../data/glove.840B.300d.txt)')

  parser.add_argument('--memorize', type=int, default=-1,
                      help='memorize first k batches (default: -1)')
  parser.add_argument('--val-freq', type=int, default=1,
                      help='validation frequency for every n epochs (default: 1)')
  parser.add_argument('--clip', type=float, default=5.0,
                      help='gradient clipping (default: 5.0)')
  parser.add_argument('--metric', type=str, default='accuracy',
                      help='target metric loss,accuracy (default: accuracy)')

  parser.add_argument('--seed', type=int, default=0,
                      help='random seed (default: 0)')
  parser.add_argument('--log-interval', type=int, default=1,
                      help='interval between training status logs (default: 1)')

  parser.add_argument('--batch-size', type=int, default=64,
                      help='Batch size (default: 64)')
  parser.add_argument('--lr', type=float, default=0.00001,
                      help='learning rate (default: 0.00001)')
  parser.add_argument('--weight-decay', type=float, default=0.00001,
                      help='L2 regularization (weight decay) term (default: 0.00001)')
  parser.add_argument('--verbose',
                      action='store_true', help='Print to a progressbar or lines in stdout')

  parser.add_argument('--debug', type=int, default=0,
                      help='Debug Mode if debug>0, default = 0')

  parser.add_argument('--trn-images', type=str, default='all',
                      help='list of image categories for training separated by comma, options are restaurant, bedroom, living_room, plaza_courtyard, shop, street or all, default=all')

  parser.add_argument('--val-images', type=str, default='all',
                      help='list of image categories for validation separated by comma, options are restaurant, bedroom, living_room, plaza_courtyard, shop, street or all, default=all')
  parser.add_argument('--task', type=str, default='task1',
                      help='name of the task, options are task1, task2 default=task1')

  parser.add_argument('--data-root', type=str, default='../data/fov_pretraining_all',
                      help='load data from data_root path default ../data/fov_pretraining_all')

  parser.add_argument('--obj-dict-file', type=str, default='../data/vg_object_dictionaries.all.json',
                      help='object dictionary file, default=../data/vg_object_dictionaries.all.json')

  parser.add_argument('--direction', type=str, default='canonical',
                      help='direction method used canonical | cartesian | lup | canonical_proximity, default=canonical')

  parser.add_argument('--fov-emb-mode', type=int, default=2,
                      help='Fov embeddings mode 0: dont use it 1:only fov embeddings 2: fov embeddings + image features default=2')
  parser.add_argument(
      '--ignore-list', help='Comma separated list of ground-truth moves to ignore, default=""', default='')

  # LXRT Model Config
  # Note: LXRT = L, X, R (three encoders), Transformer
  parser.add_argument('--loadLXMERT', dest='load_lxmert', type=str, default=None,
                      help='Load the pre-trained LXMERT model.')
  parser.add_argument("--llayers", default=9, type=int,
                      help='Number of Language layers')
  parser.add_argument("--xlayers", default=5, type=int,
                      help='Number of CROSS-modality layers.')
  parser.add_argument("--rlayers", default=5, type=int,
                      help='Number of object Relationship layers.')
  parser.add_argument("--fromScratch", dest='from_scratch', action='store_const', default=False, const=True,
                      help='If none of the --load, --loadLXMERT, --loadLXMERTQA is set, '
                      'the model would be trained from scratch. If --fromScratch is'
                      ' not specified, the model would load BERT-pre-trained weights by'
                      ' default. ')

  return parser

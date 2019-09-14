import os
import time
import string
import itertools
import random
import yaml
import subprocess
import shlex
from collections import defaultdict

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

SEL_ROW = 15
SET_PIN = 11
MODE_PIN = 13

CHAR_KEYS = [''.join(key) for key in itertools.product('ABCDEFGH', '12345678')]
SETTINGS_MAP = dict(zip(CHAR_KEYS, string.ascii_uppercase + string.digits))
SETTINGS_MAP.update({
  'F3': 'ENTER', 'F4': 'ENTER', 'F5': 'ENTER', 'F6': 'ENTER', 
  'H3': 'CANCEL', 'H4': 'CANCEL', 'H5': 'CANCEL', 'H6': 'CANCEL'
})

GAME_DIR = '/home/pi/activiti'

MODE = 'learn'

MATRIX = [
['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8'],
['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8'],
['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8'],
['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8'],
['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8'],
['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8'],
['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8'],
['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8'],
]


CONNS = [8,10,12,16,18,22,24,26,32,36,38,40,37,35,33,31][::-1]

ROW = CONNS[::2]
COL = CONNS[1::2]

NROW = len(ROW)
NCOL = len(COL)

CURRENT_GAME = None
LEARN_HISTORY = defaultdict(set)
PLAY_HISTORY = set()

def setup():
  for item in COL:
    GPIO.setup(item, GPIO.OUT)

  GPIO.setup(SEL_ROW, GPIO.OUT)

  for item in ROW:
    GPIO.setup(item, GPIO.IN, pull_up_down = GPIO.PUD_UP)

  GPIO.setup(SET_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP)
  GPIO.setup(MODE_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP)


def wait_for_key():
  key = None
  while not key:
    key = get_key()
    time.sleep(0.1)

  print('Key: ' + key)
  return key

def get_key():
  key = None
  if GPIO.input(SET_PIN) == 0:
    while GPIO.input(SET_PIN) == 0:
      pass
    
    handle_settings()
    return 'SET'

  if GPIO.input(MODE_PIN) == 0:
    while GPIO.input(MODE_PIN) == 0:
      pass
    handle_mode()
    return 'MODE'

  for col in range(NCOL):  
    GPIO.output(COL[col],0)
  
    for row in range(NROW):  
      if GPIO.input(ROW[row]) == 0:  
        key = MATRIX[row][col]

      while GPIO.input(ROW[row]) == 0:
        pass
  
    GPIO.output(COL[col],1)
  return key

def play_sound(fname):
  print('Playing ' + fname)
  #subprocess.call(shlex.split('mplayer %s' % fname))
  subprocess.call(shlex.split('omxplayer %s' % fname))

def handle_settings():
  """
  Load game config
  """

  global CURRENT_GAME

  play_sound('../assets/settings.wav')

  game_code = ''
  while True:
    key = wait_for_key()
    
    key_val = SETTINGS_MAP.get(key, '')
    if not key_val:
      continue
    
    if key_val == 'ENTER':
      print('Loading game ' + game_code)
      config_file = os.path.join(GAME_DIR, 'outputs', game_code, 'config.yaml')
      if os.path.exists(config_file):
        CURRENT_GAME = yaml.load(open(config_file))
        all_plays = dict()
        for item in CURRENT_GAME['items']:
          all_plays.update({play_item: item for play_item in item['play']})
        CURRENT_GAME['all_plays'] = all_plays
        
        play_sound(get_file_path(CURRENT_GAME['title']))
        MODE = 'learn'
        LEARN_HISTORY.clear()
        PLAY_HISTORY.clear()
        play_sound('../assets/learn.wav')
      else:
        play_sound('../assets/game_not_found.wav')
        game_code = ''
      return

    elif key_val == 'CANCEL':
      game_code = ''
      play_sound('../assets/cancel.wav')
      return
   
    else:
      play_sound('../assets/%s.wav' % key_val)
      game_code += key_val

def get_file_path(fname):
  return os.path.join(GAME_DIR, 'outputs', CURRENT_GAME['code'], fname)
  
def handle_mode():
  global CURRENT_GAME, MODE

  if not CURRENT_GAME:
    return

  MODE = 'play' if MODE == 'learn' else 'learn'
  play_sound('../assets/' + MODE + '.wav')

def learn():
  key = wait_for_key()
  if key in ['SET', 'MODE']:
    return

  key_val = CURRENT_GAME['layout'].get(key, None)
  if not key_val:
    return

  item_indx = key_val - 1
  item = CURRENT_GAME['items'][item_indx]

  options = item['learn']
  print(LEARN_HISTORY[item_indx])
  unplayed = list(set(range(len(options))) - LEARN_HISTORY[item_indx])
  print(unplayed)
  if not unplayed:
    LEARN_HISTORY[item_indx].clear()
    unplayed = list(range(len(options)))
  
  option_indx = unplayed[random.randint(0, len(unplayed)-1)]
  LEARN_HISTORY[item_indx].add(option_indx)
  option = options[option_indx]
  play_sound(get_file_path(option))

def play():
  play_file = CURRENT_GAME.get('play', None)
  if play_file:
    play_file = get_file_path(play_file)
    play_sound(play_file)

  unplayed = list(CURRENT_GAME['all_plays'].keys() - PLAY_HISTORY)
  if not unplayed:
    PLAY_HISTORY.clear()
    unplayed = list(CURRENT_GAME['all_plays'].keys())
 
  option = unplayed[random.randint(0, len(unplayed)-1)]
  item = CURRENT_GAME['all_plays'][option]
  PLAY_HISTORY.add(option)

  play_sound(get_file_path(option))

  key = wait_for_key()
  
  if key in ['SET', 'MODE']:
    return

  key_val = CURRENT_GAME['layout'].get(key, None)
  if not key_val:
    play_sound('../assets/failure.wav')
    return

  selection = CURRENT_GAME['items'][key_val-1]
  if selection == item:
    play_sound('../assets/success.wav')
  else:
    play_sound('../assets/failure.wav')

if __name__ == '__main__':

  try:
    setup()

    while not CURRENT_GAME:
      print('while', CURRENT_GAME)
      handle_settings()

    while True:          
      if MODE == 'learn':
        learn()
      else:
        play()
    
  except KeyboardInterrupt:
    GPIO.cleanup()

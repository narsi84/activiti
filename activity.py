from argparse import ArgumentParser
import random
import shutil
import os
import string
import itertools

from gtts import gTTS
import yaml

ROWS = 'ABCDEFGH'
COLS = '12345678'

def do_tts(item, indir, outfile):
	if item.get('type', 'tts') == 'audio':
		fin = os.path.join(indir, item['src'])
		print('Copying file ', fin)		
		shutil.copyfile(fin, outfile)

	else:
		text = item['src']
		lang = item.get('lang', 'en')

		print('Performing tts for ', outfile)
		tts = gTTS(text, lang=lang)
		tts.save(outfile)
	return os.path.basename(outfile).replace('.mp3', '.wav')

def get_keys(layout):
	tl, br = layout
	r1 = tl[0]; r2 = br[0]
	c1 = tl[1]; c2 = br[1]
	r1_indx = ROWS.index(r1); r2_indx = ROWS.index(r2)
	c1_indx = COLS.index(c1); c2_indx = COLS.index(c2)

	keys = [''.join(item) for item in itertools.product(ROWS[r1_indx:r2_indx+1], COLS[c1_indx:c2_indx+1])]
	return keys

if __name__ == '__main__':

	parser = ArgumentParser()
	parser.add_argument(dest='indir', help='Input directory')
	parser.add_argument('--outdir', dest='outdir', required=False, default='.', help='Output location')
	parser.add_argument('--code', dest='code', required=False, help='Game code', default='')

	args = parser.parse_args()

	yml_file = os.path.join(args.indir, 'config.yaml')
	config = yaml.load(open(yml_file))

	new_config = {}
	if not args.code:
		game_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
	else:
		game_code = args.code
	outdir = os.path.join(args.outdir, game_code)
	os.makedirs(outdir)

	title = config['title']
	outfile = os.path.join(outdir, 'title.mp3')
	new_config['title'] = do_tts(title, args.indir, outfile)
	if 'text' in title:
		new_config['title_text'] = title['text']
	else:
		new_config['title_text'] = title['src'] if title.get('type', 'text') == 'text' else ''

	play = config.get('play', None)
	if play:
		outfile = os.path.join(outdir, 'play.mp3')
		new_config['play'] = do_tts(play, args.indir, outfile)
	new_config['items'] = []
	layout = {''.join(key): 0 for key in itertools.product(ROWS, COLS)}

	for idx, item in enumerate(config['items'], 1):
		new_item = {}
		new_item['id'] = item['id']

		for key in get_keys(item['layout']):
			layout[key] = idx

		new_item['learn'] = [
			do_tts(
				l_item, args.indir, os.path.join(outdir,  '%d_learn_%d.mp3' % (idx, l_idx))			
			) 
			for l_idx, l_item in enumerate(item['learn'], 1)
		]
		new_item['play'] = [
			do_tts(
				p_item, args.indir, os.path.join(outdir,  '%d_play_%d.mp3' % (idx, p_idx))			
			) 
			for p_idx, p_item in enumerate(item['play'], 1)
		]
		new_config['items'].append(new_item)

	new_config['id'] = config['id']
	new_config['code'] = game_code
	new_config['layout'] = layout
	out_yaml = os.path.join(outdir, 'config.yaml')
	yaml.dump(new_config, open(out_yaml, 'w'), default_flow_style=False)

	for r in ROWS:
		print('\t'.join([str(layout[''.join(key)]) for key in itertools.product(r, COLS)]), '\n')

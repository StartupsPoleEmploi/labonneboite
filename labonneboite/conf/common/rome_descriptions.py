# coding: utf8
from labonneboite.common.load_data import load_rome_labels
ROME_DESCRIPTIONS = load_rome_labels()

# import os
# filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'xxxxxxxxxx.csv')
# with open(filename, 'w') as f:
# 	for k in ROME_DESCRIPTIONS:
# 		f.write("%s,%s\n" % (k, ROME_DESCRIPTIONS[k].encode('utf-8')))

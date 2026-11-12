"""Contact sheets from render stills, for a quick look at many moments at once (6 stills per sheet, 2x3).
Run from the film folder:  sheet.py OUT_PREFIX t1,t2,...   -> stills/<OUT_PREFIX>_<k>.jpg"""
import os, sys
from PIL import Image

out, times = sys.argv[1], sys.argv[2].split(',')
for k in range(0, len(times), 6):
    sheet = Image.new('RGB', (1920, 1620), 'white')
    for i, t in enumerate(times[k:k + 6]):
        im = Image.open(os.path.join('stills', 't%s.png' % t.rjust(5, '0'))).convert('RGB').resize((960, 540), Image.LANCZOS)
        sheet.paste(im, ((i % 2) * 960, (i // 2) * 540))
    sheet.save(os.path.join('stills', '%s_%d.jpg' % (out, k // 6)), quality=88)

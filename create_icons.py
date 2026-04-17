from PIL import Image, ImageDraw
import sys

def create_icon(size, filename):
    img = Image.new('RGB', (size, size), color='#06061a')
    d = ImageDraw.Draw(img)
    cx, cy = size//2, size//2
    w, h = int(size*0.8), int(size*0.4)
    d.rounded_rectangle([cx-w//2, cy-h//2, cx+w//2, cy+h//2], radius=int(size*0.05), outline='#facc15', width=int(size*0.05))
    d.line([cx-w//3, cy-h//2, cx-w//3, cy+h//2], fill='#facc15', width=int(size*0.02))
    img.save(filename)

create_icon(192, r'A:\EgyptianLicnesePlateDetector\frontend\icon-192.png')
create_icon(512, r'A:\EgyptianLicnesePlateDetector\frontend\icon-512.png')
print("Icons created!")

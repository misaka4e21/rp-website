#!/usr/bin/python
import os, sys
import Image

# 253x164
final_size = 253, 164
# 618x280
final_size = 618, 280

def cutsize_core(filename, final_size, typename, outpath):
    outfile, ext = os.path.splitext(filename)
    outfile = outpath + outfile.lower() + "-" + typename + ".jpg"
    # Open image initially and resize
    im = Image.open("input/" + filename)
    size = final_size[0], im.height
    im.thumbnail(size, Image.ANTIALIAS)
    # Try again..
    if im.height < final_size[1]:
        im = Image.open("input/" + filename)
        size = im.width, final_size[1]
        im.thumbnail(size, Image.ANTIALIAS)
    im = im.crop((0, 0, final_size[0], final_size[1]))
    im.save(outfile, "JPEG")

def cutsize_thumbnail(filename):
    cutsize_core(filename, (253, 164), "thumbnail", "thumbnail/")
def cutsize_banner(filename):
    cutsize_core(filename, (618, 280), "banner", "banner/")
def cutsize_img(filename):
    cutsize_core(filename, (618, 420), "img", "img/")

def convert(filename):
    outfile, ext = os.path.splitext(filename)
    outfile = "normal/" + outfile.lower() + ".jpg"
    im = Image.open("input/" + filename)
    im.save(outfile, "JPEG")

if __name__ == "__main__":
    try:
        os.makedirs("input")
        os.makedirs("banner")
        os.makedirs("thumbnail")
        os.makedirs("normal")
        os.makedirs("img")
    except OSError as err:
        pass
    for filename in os.listdir("input"):
        cutsize_thumbnail(filename)
        cutsize_banner(filename)
        cutsize_img(filename)
        convert(filename)


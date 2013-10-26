import sys
import hls

def progress(p):
  sys.stdout.write("\r%d%%" % p)
  sys.stdout.flush()

url = "http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8"
hls.download(url, "bipbopall.mp4", progress)

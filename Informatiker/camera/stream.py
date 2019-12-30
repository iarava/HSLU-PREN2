from picamera import PiCamera
import picamera.array
from threading import Thread
import time
from matplotlib import pyplot as plt
import numpy as np

class Stream:
    def __init__(self):
        self.cam = PiCamera()
        self.cam.resolution = (320,240)
        self.cam.exposure_mode = "sports"
        self.cam.framerate = 30
        self.cam.brightness = 60
        #self.cam.contrast = 60
        self.cam.iso = 800
        self.cam.shutter_speed = 500
        #self.cam.hflip = 180
        time.sleep(2)
        self.rawStream = picamera.array.PiRGBArray(self.cam)
        self.stream = self.cam.capture_continuous(self.rawStream, format='bgr', use_video_port=True)
        #print(self.stream.array)
        self.frame = None
        self.stopRecord = False

    def startStreamAsThread(self):
        s = Thread(target=self.updateFrame)
        s.daemon = True
        s.start()
        return self

    def updateFrame(self):
        for i in self.stream:
            self.frame = i.array
            #print(self.frame)
            self.rawStream.truncate(0)
            if(self.stopRecord):
                self.stream.close()
                self.rawStream.close()
                return

    def readImage(self):
        #return latest frame
        return self.frame

#s = Stream()
#s.startStreamAsThread()
#time.sleep(1)
#print(s.frame)
#p = np.array(s.readImage())
#s.stopRecord = True
#print(p)
#plt.imshow(p, interpolation='nearest')
#plt.show()

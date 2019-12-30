import cv2
import time
import queue
from matplotlib import pyplot as plt
from threading import Thread

from camera.stream import Stream
from Bildverarbeitung.Bildverarbeitung import Bildverarbeitung
from sensor.buzer import Buzzer
from sensor.led import Led
from sensor.loadingTof import Tof_Sensor
from gui.app import WebServer

from uart.UARTHandler import UARTHandler


#TODO: uncomment everthing necessary

class Logic:
    def __init__(self):
        self.algorithm = Bildverarbeitung()
        self.uart = UARTHandler()
        self.stream = Stream().startStreamAsThread()
        time.sleep(2)
        self.startSignal = False
        self.detectedNumberArray = None
        self.detectedNumber = None

        self.halteSignal = None
        self.halteSignalRecognized = 0
        self.infoSignal = None

        self.round = 0
        self.papap = 1
        #Positions
        #self.startPos = self.uart.getdst()
        self.startSignalPos = None
        self.distOneRound = None
        self.distAfterRound1 = None

        self.images = queue.Queue()
        self.imgName = 0
        self.loadCount = 0
        self.loadSensor = Tof_Sensor()

    def prepareComponents(self):
        #sensors
        self.led = Led()
        #self.led.turnLedOn()
        self.buzzer = Buzzer()
        #webserver
        #self.webserver = WebServer()
        #web = Thread(target=self.webserver.basic())
        #web.daemon = True
        #web.start()
        for i in range(2):
            print(self.uart.getconnection())

        time.sleep(5)

        self.startRound0()
        #time.sleep(10)
        #self.startRound0()
        #self.startRound1()
        #self.startRound2()
        #self.startRound3()
        #TODO: define shutdownMethod
        self.clearProgrammUp()

    def startRound0(self):
        #self.startSignal = False
        #start Motor
        self.uart.setspeed(1)
        #start Tof measuring
        sens = Thread(target=self.getSensData)
        sens.daemon = True
        sens.start()

        #check if loading is finished
        #print("loadingState: ",self.uart.loadingstate())
        while True:
            if(self.loadCount == 1):
                time.sleep(15)
                break
        self.uart.setspeed(1)
        time.sleep(1)
        self.uart.setspeed(0)
        print("Main: Round0, Loading done")
        #check for roundsignal
        #while True:
        #    if(not(self.startSignal) and self.round == 0):
        #        imgAsArray = self.stream.readImage()
        #        self.startSignal = self.algorithm.isStartSignal(imgAsArray)
        #        print("Startsignal: ")
        #        if(self.papap == 1 and self.startSignal):
        #
        #            self.uart.setspeed(4)
        #            self.papap = 2
        #        elif(self.papap == 2 and self.startSignal):
        #            self.uart.setspeed(6)
        #    elif(self.startSignal):
        #        self.startSignalPos = self.uart.getdst()
        #        #self.round += 1
        #        break

        print("Main: Round0, Roundsignal recognized")

    def startRound1(self):
        print("startRound1")
        self.uart.setspeed(8)
        self.startSignal = False
        while True:
            #TODO: controll this if....
            if(self.round == 1 and ((self.infoSignal is None) or (self.startSignal is None))):
                imgAsArray = self.stream.readImage()
                if(not(self.infoSignal)):
                    digitArray = self.algorithm.getDigitfromImage(imgAsArray)
                    if(digitArray):
                        self.infoSignal = int(digitArray[0])
                        print("Infosignal",self.infoSignal)
                        buz = Thread(target=self.doBuzzer, args=(self.infoSignal,))
                        buz.daemon = True
                        buz.start()
                elif(not(self.startSignal)):
                    self.startSignal = self.algorithm.isStartSignal(imgAsArray)
            else:
                self.distAfterRound1 = self.uart.getdst()
                self.distOneRound = self.distAfterRound1 - self.startSignalPos
                self.round += 1
                break
        print("Main: Round1, Roundsignal and Infosignal recognized")

    def startRound2(self):
        #TODO: setToMax
        self.uart.setspeed(10)
        while ((self.uart.getdst()-self.distAfterRound1) < self.distOneRound):
            time.sleep(0.05)
        self.round += 1
        print("Main: Round2, run the given distance")

    #self.halteSignalRecognized : 0 = not recognized, 1 = first time recognized, 2 = now doesn't recognize anymore
    def startRound3(self):
        #self.uart.setspeed(5)
        while True:
            if(self.round == 3):
                imgAsArray = self.stream.readImage()
                digitArray = self.algorithm.getDigitfromImage(imgAsArray)
                if(digitArray):
                    #TODO: change to self.infoSignal
                    #print(int(digitArray[0]))
                    if(self.infoSignal == int(digitArray[0])):
                        self.halteSignalRecognized = 1
                    else:
                        if(self.halteSignalRecognized == 1):
                            self.halteSignalRecognized = 2
                if(self.halteSignalRecognized == 2):
                    self.uart.setspeed(0)
                    self.round += 1
                    break
        print("Main: Round3, halteSignal recognized and stopped")

    def getSensData(self):
        while True:
            if(self.round == 0):
                range = self.loadSensor.getDistance()
                time.sleep(0.1)
                if(range < 100):
                    #TODO: test for right second
                    self.loadCount = 1
                    time.sleep(1.9)
                    self.uart.setspeed(0)
                    self.uart.startloading()
                    break

    def doBuzzer(self, number):
        for i in range(number):
            self.buzzer.turnBuzOn()
            time.sleep(1)
            self.buzzer.turnBuzOff()
            time.sleep(0.3)

    def clearProgrammUp(self):
        self.led.turnLedOff()
        input("Press Enter to continue...")

    def procedure(self):
        #self.led = Led()
        #self.led.turnLedOn()
        while True:
            if(not(self.startSignal) and self.round == 0):
                imgArray = self.stream.readImage()
                start = int(round(time.time() * 1000))
                self.startSignal = self.algorithm.isStartSignal(imgArray)
                print(self.startSignal)
                #if(digitArray):
                #    print(digitArray)
                #    n = int(digitArray[0])
                #    print("Erkannt Zahl: ",n)
                self.images.put(imgArray)
                mid = int(round(time.time() * 1000))
                print("read: ",mid-start)
                #cv2.imwrite("/home/pi/Group38/camera/images/" + str(self.imgName) +".jpg",imgArray)
                #cv2.imencode("/home/pi/Group38/camera/images/" + str(self.imgName) +".jpg",imgArray)[1].tostring()
                #stop = int(round(time.time() * 1000))
                #print("converted",stop-mid)
                time.sleep(0.01)
                self.imgName += 1
                if(self.imgName == 5):
                    break
            else:
                self.updateRound()
                break
        #self.led.turnLedOff()
    def updateRound(self):
        self.round +=1

    def showImages(self):
        while not(self.images.empty()):
            i = self.images.get()
            #print(i)
            plt.imshow(i, interpolation='nearest')
            plt.show()


l =Logic()
#l.procedure()
l.prepareComponents()
#l.showImages()

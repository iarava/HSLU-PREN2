import time
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Thread
from uart.UARTHandler import UARTHandler

class WebServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'kljgcasiujdnofdhasildgiwdgwq'
        #self.app.config['ENV'] = 'development'
        self.socketio = SocketIO(self.app)
        self.log = logging.getLogger('werkzeug')
        self.log.disabled = True
        self.app.logger.disabled = True

        self.doMeasurement = True
        self.uart = UARTHandler()

    def basic(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')

        self.querys()
        self.socketio.run(self.app, host='0.0.0.0')

    def querys(self):
        @self.socketio.on('checkConnection')
        def checkConnection():
            if(self.uart.getconnection() == 1):
                emit("connectState",True)
            else:
                emit("connectState",False)

        @self.socketio.on('startLoading')
        def start_Loading():
            print("loadingstate begin: ",self.uart.loadingstate())
            self.uart.startloading()
            print("loadingstate doing: ",self.uart.loadingstate())
            print('loading started...')

        @self.socketio.on('start_Motors')
        def start_Motors(data):
            self.uart.setspeed(int(data))

        @self.socketio.on('startMeasurement')
        def startMeasurement():
            thread  = Thread(target=self.showMeasurements)
            self.doMeasurement = True
            thread.daemon = True
            thread.start()

        @self.socketio.on('stopMeasurement')
        def stopMeasurement():
            self.doMeasurement = False

    def showMeasurements(self):
        #s = open("/home/pi/Group38/speed.txt", "w+")
        #d = open("/home/pi/Group38/distance.txt", "w+")
        while True:
            if(self.doMeasurement):
                speed = self.uart.getspeed()
                dist = self.uart.getdst()
                #acc = self.uart.getacc()
                #accx = acc[0]
                #accy = acc[1]
                #speed = 2
                #dist = 200
                data = "Speed: " + str(speed) + ", Distance: " + str(dist)
                #print(data)
                self.socketio.emit("getMeasurementData",data)
                #s.write(speed,"\n")
                #f.write(dist,"\n")
                time.sleep(1)
            else:
            #    s.close()
            #    d.close()
                return
WebServer().basic()

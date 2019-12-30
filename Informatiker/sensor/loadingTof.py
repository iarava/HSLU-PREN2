import adafruit_vl6180x
import board
import busio

class Tof_Sensor:

    def __init__(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self._address = 0x29
        self._sensor = adafruit_vl6180x.VL6180X(self.i2c, self._address)

    def getDistance(self):
        range = self._sensor.range
        #print('Range: {0}mm'.format(range))
        return range

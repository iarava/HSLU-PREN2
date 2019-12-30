import RPi.GPIO as GPIO
import time

class Buzzer:
    """Turn On/Off LED"""

    def __init__(self):
        self.pin = 25
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

    def turnBuzOn(self):
        GPIO.output(self.pin, GPIO.HIGH)
        print("turn Buzzer on")

    def turnBuzOff(self):
        GPIO.output(self.pin, GPIO.LOW)
        print("turn Buzzer off")

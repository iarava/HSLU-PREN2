import RPi.GPIO as GPIO

class Led:
    """Turn On/Off LED"""

    def __init__(self):
        self.pin = 8
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

    def turnLedOn(self):
        GPIO.output(self.pin, GPIO.HIGH)
        print("turn LED on")

    def turnLedOff(self):
        GPIO.output(self.pin, GPIO.LOW)
        print("turn LED off")
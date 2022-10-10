from rad_arduino_proxy import ArduinoProxy
import time
import struct

# Function codes
LASER_TILT_SERVO  = b'\x02' # set position/vel/accel for laser tilt servo
ARDUINO_LED       = b'\x08' # set arduino debug led state: 0x00 = off, 0x01 = on
# predefined commands
led_off    = struct.pack('<cc', ARDUINO_LED, b'\x00')
led_on     = struct.pack('<cc', ARDUINO_LED, b'\x01')
# Create an arduino server server
prox = ArduinoProxy()
# send some packets to arduino with id 1
for idx in range(50):
    prox.send_packets([(1, led_on)])
    time.sleep(0.1)
    prox.send_packets([(1, led_off)])
    time.sleep(0.1)

# shutdown the arduino server
prox.shutdown()

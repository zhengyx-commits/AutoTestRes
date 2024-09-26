#!/usr/bin/python
# coding=UTF-8
import serial
import time

serial1 = serial.Serial('/dev/powerRelay_for_bluetooth1', 9600)
serial0 = serial.Serial('/dev/powerRelay_for_bluetooth2', 9600)
# serial2 = serial.Serial('/dev/tty.usbserial-142330', 9600)

# if serial1.isOpen():
#    print("open success")
# else:
#     print("open failed")


try:
    print("beginning")
    """待机唤醒"""
    serial1.write(b'\xA0\x01\x01\xA2') # 通路
    serial0.write(b'\xA0\x01\x01\xA2') # 通路
    # serial2.write(b'\xA0\x01\x01\xA2') # 通路
    time.sleep(5)
    serial1.write(b'\xA0\x01\x00\xA1') # 断路
    serial0.write(b'\xA0\x01\x00\xA1') # 断路
    # serial2.write(b'\xA0\x01\x00\xA1') # 断路
    time.sleep(1)

    print("done")
    serial1.close()
    serial0.close()
except KeyboardInterrupt:
    serial1.close()
    serial0.close()
    # serial2.close()
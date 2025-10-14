import ucryptolib
cipher = ucryptolib.aes(b"key16byteslong", 1, b"iv16byteslong")

import machine
from machine import Pin, PWM
from utime import sleep

buzzer = PWM(Pin(18))
volume = 50

def DO():
    buzzer.freq(1047)
    buzzer.duty_u16(volume)

def RE():
    buzzer.freq(1175)
    buzzer.duty_u16(volume)

def MI():
    buzzer.freq(1318)
    buzzer.duty_u16(volume)

def FA():
    buzzer.freq(1397)
    buzzer.duty_u16(volume)

def SO():
    buzzer.freq(1568)
    buzzer.duty_u16(volume)

def LA():
    buzzer.freq(1760)
    buzzer.duty_u16(volume)

def SI():
    buzzer.freq(1967)
    buzzer.duty_u16(volume)

def N():
    buzzer.duty_u16(0)

while True:
    MI()
    sleep(0.25)
    MI()
    sleep(0.25)
    MI()
    sleep(0.25)
    DO()
    sleep(0.25)
    MI()
    sleep(0.25)
    SO()
    sleep(0.25)
    SO()
    sleep(0.25)
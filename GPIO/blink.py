import time 
import machine 
led = machine.Pin(16, machine.Pin.OUT) 
button = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_DOWN) 
bp_pressed = 0 

def changerMode(pin):
    global bp_pressed
    if(button.value() == 1): 
        bp_pressed += 1 
        if(bp_pressed == 4): 
            bp_pressed = 1

button.irq(trigger=machine.Pin.IRQ_RISING, handler=changerMode)

while(True):  

    if(bp_pressed == 1): 
        led.value(1) 
        time.sleep(0.5) 
        led.value(0) 
        time.sleep(0.5) 
    
    if(bp_pressed == 2): 
        led.value(1) 
        time.sleep(0.2) 
        led.value(0) 
        time.sleep(0.2) 
    
    if(bp_pressed == 3): 
        led.value(0)

    time.sleep(0.1)
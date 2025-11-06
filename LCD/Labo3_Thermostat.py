#importation des bibliothèques nécessaires
from machine import ADC, Pin, I2C, PWM
from utime import sleep
from dht import *
from lcd1602 import LCD1602

#initialisation des capteurs et actionneurs
i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
lcd = LCD1602(i2c, 2, 16)
ROTARY_ANGLE_SENSOR = ADC(0)
dht = DHT11(18)
Led = machine.Pin(20, machine.Pin.OUT)
buzzer = PWM(Pin(27))

#fonction de mappage du potentiomètre
def mappage(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

#fonction de lecture des capteurs
def lecture_capteurs():
    raw_value = ROTARY_ANGLE_SENSOR.read_u16() #lecture du potentiomètre
    mapped = round(mappage(raw_value, 0, 65535, 15, 35)) #mappage de la valeur lue entre 15 et 35
    dht.measure() #lecture du capteur DHT11
    sleep(1)
    temp = dht.temperature() #récupération de la température
    return mapped, temp

#fonction d'affichage sur l'écran LCD
def lcd_affichage(pot, temp):
    lcd.clear()
    lcd.setCursor(0, 0)
    lcd.print(f"Pot: {pot}")
    lcd.setCursor(0, 1)
    lcd.print(f"Temp: {temp}C")
    
#boucle principale
while True:
    set, ambient = lecture_capteurs() #lecture des capteurs
    lcd_affichage(set, ambient) #affichage sur l'écran LCD
    if set < ambient and ambient < set + 3:
        buzzer.duty_u16(0) #désactivation du buzzer si pas en alarme
        # Clignotement de la LED toutes les 0.5 secondes
        Led.value(1)
        sleep(0.5)    
        Led.value(0)
        sleep(0.5)
    elif (ambient > set) and (ambient > set + 3):
        # Clignotement rapide de la LED
        Led.value(1)
        sleep(0.01)
        Led.value(0)
        sleep(0.01)
        # Activation du buzzer
        buzzer.freq(1318)
        buzzer.duty_u16(1000)
        # Afficher "ALARME" sur l'écran LCD
        lcd.clear()
        lcd.setCursor(0, 0)
        lcd.print("ALARME")
        lcd.setCursor(0, 1)
        
    
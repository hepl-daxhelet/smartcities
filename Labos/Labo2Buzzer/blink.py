from machine import Pin, PWM, ADC
from utime import sleep

buzzer = PWM(Pin(27))
volume = 0
ROTARY_ANGLE_SENSOR = ADC(2)
BP = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_DOWN) 
choix = 0
Led = machine.Pin(18, machine.Pin.OUT)

#Intérruption BP
def changerMusique(pin):
    global choix
    if(BP.value() == 1): 
        choix += 1 
        if(choix == 3): 
            choix = 0

BP.irq(trigger=machine.Pin.IRQ_RISING, handler=changerMusique)


#Définition des différentes notes
# Silence
def N(volume):
    buzzer.duty_u16(0)

# Octave 3
def DO(volume):  buzzer.freq(261); buzzer.duty_u16(volume)
def DOd(volume): buzzer.freq(277); buzzer.duty_u16(volume)  # Do#
def RE(volume):  buzzer.freq(293); buzzer.duty_u16(volume)
def REd(volume): buzzer.freq(311); buzzer.duty_u16(volume)  # Re#
def MI(volume):  buzzer.freq(329); buzzer.duty_u16(volume)
def FA(volume):  buzzer.freq(349); buzzer.duty_u16(volume)
def FAd(volume): buzzer.freq(370); buzzer.duty_u16(volume)  # Fa#
def SO(volume):  buzzer.freq(392); buzzer.duty_u16(volume)
def SOb(volume): buzzer.freq(415); buzzer.duty_u16(volume)  # Sol#
def LA(volume):  buzzer.freq(440); buzzer.duty_u16(volume)
def LAd(volume): buzzer.freq(466); buzzer.duty_u16(volume)  # La#
def SI(volume):  buzzer.freq(493); buzzer.duty_u16(volume)
def SIb(volume): buzzer.freq(466); buzzer.duty_u16(volume)  # Si bémol

# Octave 4
def DO5(volume):  buzzer.freq(523); buzzer.duty_u16(volume)
def DO5d(volume): buzzer.freq(554); buzzer.duty_u16(volume)  # Do#5
def RE5(volume):  buzzer.freq(587); buzzer.duty_u16(volume)
def RE5d(volume): buzzer.freq(622); buzzer.duty_u16(volume)  # Re#5
def MI5(volume):  buzzer.freq(659); buzzer.duty_u16(volume)
def FA5(volume):  buzzer.freq(698); buzzer.duty_u16(volume)
def FA5d(volume): buzzer.freq(740); buzzer.duty_u16(volume)  # Fa#5
def SO5(volume):  buzzer.freq(784); buzzer.duty_u16(volume)
def SO5d(volume): buzzer.freq(830); buzzer.duty_u16(volume)  # Sol#5
def LA5(volume):  buzzer.freq(880); buzzer.duty_u16(volume)
def LA5d(volume): buzzer.freq(932); buzzer.duty_u16(volume)  # La#5
def SI5(volume):  buzzer.freq(988); buzzer.duty_u16(volume)

# Octave 5
def DO6(volume):  buzzer.freq(1047); buzzer.duty_u16(volume)
def DO6d(volume): buzzer.freq(1109); buzzer.duty_u16(volume)  # Do#6
def RE6(volume):  buzzer.freq(1175); buzzer.duty_u16(volume)
def RE6d(volume): buzzer.freq(1245); buzzer.duty_u16(volume)  # Re#6
def MI6(volume):  buzzer.freq(1319); buzzer.duty_u16(volume)
def FA6(volume):  buzzer.freq(1397); buzzer.duty_u16(volume)
def FA6d(volume): buzzer.freq(1480); buzzer.duty_u16(volume)  # Fa#6
def SO6(volume):  buzzer.freq(1568); buzzer.duty_u16(volume)
def SO6d(volume): buzzer.freq(1661); buzzer.duty_u16(volume)  # Sol#6
def LA6(volume):  buzzer.freq(1760); buzzer.duty_u16(volume)
def LA6d(volume): buzzer.freq(1865); buzzer.duty_u16(volume)  # La#6
def SI6(volume):  buzzer.freq(1976); buzzer.duty_u16(volume)

#Musique Mario Bros
def mario_theme():
    #dict => (note, durée)
    sequence = [
        (MI5, 0.25), (MI5, 0.25), (N, 0.25), (MI5, 0.25),
        (N, 0.25), (DO5, 0.25), (MI5, 0.25), (N, 0.25),
        (SO5, 0.5), (N, 0.5), (SO, 0.25),

        (N, 0.25), (DO5, 0.25), (N, 0.25), (SO, 0.25),
        (N, 0.25), (MI, 0.25), (N, 0.25),

        (LA, 0.25), (SI, 0.25), (SIb, 0.25), (LA, 0.25),
        (SO, 0.25), (MI5, 0.25), (SO5, 0.25), (LA5, 0.25),

        (FA5, 0.25), (SO5, 0.25), (N, 0.25), (MI5, 0.25),
        (DO5, 0.25), (RE5, 0.25), (SI, 0.25),

        (DO5, 0.25), (SO, 0.25), (MI, 0.25),
        (LA, 0.25), (SI, 0.25), (SIb, 0.25), (LA, 0.25),
        (SO, 0.25), (MI5, 0.25), (SO5, 0.25), (LA5, 0.25),
        (FA5, 0.25), (SO5, 0.25), (MI5, 0.25), (DO5, 0.25),
        (RE5, 0.25), (SI, 0.25),

        (SO5, 0.25), (FAd, 0.25), (FA5, 0.25), (RE5, 0.25), (MI5, 0.25),
        (SO, 0.25), (LA, 0.25), (DO5, 0.25),
        (LA, 0.25), (DO5, 0.25), (RE5, 0.25),
        (SO5, 0.25), (FAd, 0.25), (FA5, 0.25), (RE5, 0.25), (MI5, 0.25),
        (DO, 0.25), (DO, 0.25), (DO, 0.25),

        (SO5, 0.25), (FAd, 0.25), (FA5, 0.25), (RE5, 0.25), (MI5, 0.25),
        (SO, 0.25), (LA, 0.25), (DO5, 0.25),
        (LA, 0.25), (DO5, 0.25), (RE5, 0.25),
        (RE5, 0.25), (RE5, 0.25), (DO5, 0.25),

        (DO5, 0.25), (DO5, 0.25), (DO5, 0.25),
        (DO5, 0.25), (RE5, 0.25), (MI5, 0.25), (DO5, 0.25), (LA, 0.25), (SO, 0.25),
        (DO5, 0.25), (DO5, 0.25), (DO5, 0.25),
        (DO5, 0.25), (RE5, 0.25), (MI5, 0.25),

        (DO5, 0.25), (DO5, 0.25), (DO5, 0.25),
        (DO5, 0.25), (RE5, 0.25), (MI5, 0.25), (DO5, 0.25), (LA, 0.25), (SO, 0.25),
        (MI5, 0.25), (MI5, 0.25), (MI5, 0.25),
        (DO5, 0.25), (MI5, 0.25), (SO5, 0.25), (SO, 0.5),

        (DO5, 0.25), (SO, 0.25), (MI, 0.25),
        (LA, 0.25), (SI, 0.25), (SIb, 0.25), (LA, 0.25),
        (SO, 0.25), (MI5, 0.25), (SO5, 0.25), (LA5, 0.25),
        (FA5, 0.25), (SO5, 0.25), (MI5, 0.25), (DO5, 0.25),
        (RE5, 0.25), (SI, 0.25),

        (MI5, 0.25), (DO5, 0.25), (SO, 0.25),
        (SO, 0.25), (LA, 0.25), (FA5, 0.25), (FA5, 0.25), (LA, 0.25),
        (SI, 0.25), (LA5, 0.25), (LA5, 0.25), (LA5, 0.25),
        (SO5, 0.25), (FA5, 0.25), (MI5, 0.25), (DO5, 0.25), (LA, 0.25), (SO, 0.25),

        (MI5, 0.25), (DO5, 0.25), (SO, 0.25),
        (SO, 0.25), (LA, 0.25), (FA5, 0.25), (FA5, 0.25), (LA, 0.25),
        (SI, 0.25), (FA5, 0.25), (FA5, 0.25), (FA5, 0.25),
        (MI5, 0.25), (RE5, 0.25), (DO5, 0.25), (SO, 0.25), (MI, 0.25), (DO, 0.25)
    ]

    #Lecture du volume et de la durée pour chaque note + silence entre les notes + clignotement de la led
    for note, dur in sequence:
        volume = ROTARY_ANGLE_SENSOR.read_u16()
        Led.value(1)
        note(volume)
        sleep(dur)
        N(volume)  #silence entre les notes
        Led.value(0)
        sleep(0.05)

#Musique Zelda
def zelda_theme():
    #dict => (note, durée)
    sequence = [
        (MI, 1), (SO, 0.5), (RE, 1), (DO, 0.2), (RE, 0.2), (MI, 1), (SO, 0.5), (RE, 1), (MI, 1), (SO, 0.5), (RE5, 1), (DO5, 0.5), (SO, 0.5), (FA, 0.2), (MI, 0.2), (RE, 1),
        (MI, 1), (SO, 0.5), (RE, 1), (DO, 0.2), (RE, 0.2), (MI, 1), (SO, 0.5), (RE, 1), (MI, 1), (SO, 0.5), (RE5, 1), (DO5, 0.5), (SO5, 1.5),
        (SO5, 0.5), (FA5, 0.2), (MI5, 0.2), (FA5, 0.2), (MI5, 0.2), (DO5, 1), (FA5, 1), (MI5, 0.2), (RE5, 0.2), (MI5, 0.2), (RE5, 0.2), (LA, 1), (SO5, 1), (FA5, 0.2), (MI5, 0.2), (FA5, 0.2), (MI5, 0.2), (DO5, 0.5), (FA5, 0.5), (DO6, 2)
    ]

    #Lecture du volume et de la durée pour chaque note + silence entre les notes + clignotement de la led
    for note, dur in sequence:
        volume = ROTARY_ANGLE_SENSOR.read_u16()
        Led.value(1)
        note(volume)
        sleep(dur)
        N(volume)  #silence entre les notes
        Led.value(0)
        sleep(0.05)

#Ode à la joie
def joy_theme():
    #dict => (note, durée)
    sequence = [
    (SI, 0.5), (SI, 0.5), (DO5, 0.5), (RE5, 0.5), (RE5, 0.5), (DO5, 0.5), (SI, 0.5), (LA, 0.5), (SO, 0.5), (SO, 0.5), (LA, 0.5), (SI, 0.5),
    (SI, 0.5), (LA, 0.125), (LA, 0.75),
    (SI, 0.5), (SI, 0.5), (DO5, 0.5), (RE5, 0.5), (RE5, 0.5), (DO5, 0.5), (SI, 0.5), (LA, 0.5), (SO, 0.5), (SO, 0.5), (LA, 0.5), (SI, 0.5),
    (LA, 0.5), (SO, 0.125), (SO, 0.75),
    (LA, 0.5), (LA, 0.5), (SI, 0.5), (SO, 0.5), (LA, 0.5), (SI, 0.2), (DO5, 0.2), (SI, 0.5), (SO, 0.5), (LA, 0.5), (SI, 0.2), (DO5, 0.2),
    (SI, 0.5), (LA, 0.5), (SO, 0.5), (LA, 0.5),
    (SI, 0.5), (SI, 0.5), (DO5, 0.5), (RE5, 0.5), (RE5, 0.5), (DO5, 0.5), (SI, 0.5), (LA, 0.5), (SO, 0.5), (SO, 0.5), (LA, 0.5), (SI, 0.5),
    (LA, 0.5), (SO, 0.125), (SO, 0.75)
    ]
    
    #Lecture du volume et de la durée pour chaque note + silence entre les notes + clignotement de la led
    for note, dur in sequence:
        volume = ROTARY_ANGLE_SENSOR.read_u16()
        Led.value(1)
        note(volume)
        sleep(dur)
        N(volume)  #silence entre les notes
        Led.value(0)
        sleep(0.05)

#Boucle principale
while True:     #0 = Zelda, 1 = Mario, 3 = Ode à la joie
    if choix == 0:
        zelda_theme()
        sleep(1)
    elif choix == 1:
        mario_theme()
        sleep(1)
    else:
        joy_theme()
        sleep(1)

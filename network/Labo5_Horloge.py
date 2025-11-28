from machine import Pin, PWM
from utime import sleep
import network, time, ntptime

# Configuration Wi-Fi
SSID = "NOM_DU_RESEAU" # Remplacez par le nom de votre réseau Wi-Fi
PASSWORD = "MOT_DE_PASSE" # Remplacez par le mot de passe de votre réseau Wi-Fi

# Configuration du servo-moteur
servo = PWM(Pin(20))
servo.freq(100)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connexion au Wi-Fi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("Connecté au Wi-Fi :", wlan.ifconfig())

def get_local_time(offset=1): # offset en heures par rapport à UTC
    try:
        ntptime.settime()  # Met à jour l'heure du Pico (UTC)
        t = time.localtime(time.time() + offset * 3600)
        return t  # Renvoie un tuple (année, mois, jour, heure, minute, seconde, ...)
    except:
        print("Erreur de récupération de l'heure")
        return None
    
def set_servo_angle(angle):
    # Conversion de l'angle en rapport cyclique
    min_duty = 4000   # pour 0°
    max_duty = 14500   # pour 180°
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty_u16(duty)

# Programme principal
connect_wifi() # Connexion au réseau Wi-Fi

while True:
    current_time = get_local_time(offset=1)  # fuseau horaire Bruxelles (UTC+1)
    if current_time:
        hour = current_time[3]
        #print(hour)
        minute = current_time[4]
        #print(minute)
        angle = (hour % 12) * 15 + (minute / 60) * 15
        #print(angle)
        print(f"Heure : {hour}:{minute:02d} → Angle : {angle:.1f}°")
        set_servo_angle(angle)
    time.sleep(60)  # mise à jour chaque minute

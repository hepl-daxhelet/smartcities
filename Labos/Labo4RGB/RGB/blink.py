from machine import Pin, ADC
import time, utime
from neopixel import NeoPixel
import random

#Affectation des broches
rgb_led = NeoPixel(Pin(18), 1)  # Pin 18 pour la LED RGB
sound_sensor = ADC(1) # Pin A1 pour le capteur sonore

#Variables globales
dernier_changement = 0 # minuterie pour le changement de couleur
intervalles = []  # stocke les intervalles entre plusieurs battements
NB_MESURES = 4 # nombre d'intervalles à garder pour le calcul du BPM

#Fonctions
def couleurAleatoire(): # génère une couleur RGB aléatoire
    
    r = random.randrange(1, 255)
    g = random.randrange(1, 255)
    b = random.randrange(1, 255)
    return (r, g, b)

def ecouterSon(): # détecte si un son dépasse le seuil
    seuil = 34000
    valeur = sound_sensor.read_u16()
    """print("Valeur du capteur sonore :", valeur)"""
    if valeur > seuil:
        return True
    return False

def calculer_BPM(intervals_ms): # calcule le BPM à partir des intervalles en ms
    """Calcule le BPM basé sur la moyenne des intervalles"""
    if len(intervals_ms) < 1:
        return None
    
    moyenne = sum(intervals_ms) / len(intervals_ms)
    bpm = 60000 / moyenne
    return round(bpm)

# Boucle principal
while True:
   now = time.ticks_ms()

   if time.ticks_diff(now, dernier_changement) >= 0 and ecouterSon(): # son détecté et délai écoulé
       rgb_led[0] = couleurAleatoire()
       rgb_led.write()
       """print(sound_sensor.read_u16())"""

       if dernier_changement != 0:
            intervalle = time.ticks_diff(now, dernier_changement)
            intervalles.append(intervalle)

            # garder seulement les X derniers intervalles
            if len(intervalles) > NB_MESURES:
                    intervalles.pop(0)

            bpm = calculer_BPM(intervalles)
            if bpm:
                    print("BPM =", bpm)

       dernier_changement = time.ticks_add(now, 200)
       
   elif time.ticks_diff(now, dernier_changement) >= 200 and not ecouterSon():
         rgb_led[0] = (0, 0, 0)
         rgb_led.write()



         
   

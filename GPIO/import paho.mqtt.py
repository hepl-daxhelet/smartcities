import paho.mqtt.client as mqtt
from PIL import Image
import io

image = bytearray()
expected_size = 0
receiving = False

def on_msg(client, userdata, msg):
    global image, expected_size, receiving

    topic = msg.topic
    payload = msg.payload

    # Début
    if topic == "test/start":
        expected_size = int(payload)
        image = bytearray()
        receiving = True
        print("START =", expected_size)

    # Données JPEG
    elif topic == "test/data" and receiving:
        image.extend(payload)
        print("chunk reçu :", len(payload), "octets")

    # Fin
    elif topic == "test/end":
        receiving = False
        print("END")

        print("Taille reçue =", len(image))
        print("Taille attendue =", expected_size)

        if len(image) == expected_size:
            print("Image complète !")

            # Sauvegarde
            with open("image.jpg", "wb") as f:
                f.write(image)

            # Affichage
            try:
                img = Image.open(io.BytesIO(image))
                img.show()
            except Exception as e:
                print("Erreur affichage :", e)
        else:
            print("❌ Image incomplète")

client = mqtt.Client()
client.connect("192.168.2.26", 1883)
client.subscribe("test/#")
client.on_message = on_msg
client.loop_forever()###

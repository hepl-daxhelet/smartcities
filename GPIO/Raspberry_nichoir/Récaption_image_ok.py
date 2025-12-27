#!/usr/bin/env python3
import os
from datetime import datetime

import paho.mqtt.client as mqtt
import mysql.connector

# -------- CONFIG --------
IMAGES_DIR = "/home/etann/Pictures"

DB_CONFIG = {
    "host": "localhost",
    "user": "birdcam",          # aligné avec le site web
    "password": "birdcam123",   # aligné avec le site web
    "database": "birdcam",
    "autocommit": True,
}

MAX_IMAGES = 50

TOPIC_START = "test/start"
TOPIC_DATA  = "test/data"
TOPIC_END   = "test/end"
TOPIC_BATT  = "birdcam/battery"   # batterie

os.makedirs(IMAGES_DIR, exist_ok=True)

# -------- Variables pour la reconstruction --------
current_buffer = bytearray()
expected_size = 0
receiving = False

# -------- Batterie (dernière valeur reçue) --------
last_battery = None  # ex: 87

# -------- Fonctions DB --------
def db_connect():
    return mysql.connector.connect(**DB_CONFIG)

def save_to_db(filename, path, battery_value):
    conn = db_connect()
    cur = conn.cursor()
    # compatible avec le site: photos(ts, topic, filename, path, battery)
    cur.execute(
        "INSERT INTO photos (ts, topic, filename, path, battery) VALUES (NOW(), %s, %s, %s, %s)",
        (TOPIC_DATA, filename, path, battery_value),
    )
    cur.close()
    conn.close()

def cleanup_old_images():
    """Garde seulement les MAX_IMAGES dernières entrées (et supprime les fichiers associés)."""
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("SELECT id FROM photos ORDER BY id DESC")
    rows = cur.fetchall()
    ids = [r[0] for r in rows]

    if len(ids) > MAX_IMAGES:
        ids_to_delete = ids[MAX_IMAGES:]
        format_ids = ",".join(str(i) for i in ids_to_delete)

        cur.execute(f"SELECT path FROM photos WHERE id IN ({format_ids})")
        for (p,) in cur.fetchall():
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                    print(f"[CLEAN] Fichier supprimé : {p}")
                except Exception as e:
                    print(f"[CLEAN] Erreur suppression {p} : {e}")

        cur.execute(f"DELETE FROM photos WHERE id IN ({format_ids})")
        print(f"[CLEAN] Supprimé {len(ids_to_delete)} images en base.")

    cur.close()
    conn.close()

# -------- Callbacks MQTT --------
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connecté, code : {rc}")
    client.subscribe(TOPIC_START)
    client.subscribe(TOPIC_DATA)
    client.subscribe(TOPIC_END)
    client.subscribe(TOPIC_BATT)
    print("[MQTT] Abonné à test/* + birdcam/battery")

def on_message(client, userdata, msg):
    global current_buffer, expected_size, receiving, last_battery

    topic = msg.topic
    payload = msg.payload

    # --- Batterie ---
    if topic == TOPIC_BATT:
        try:
            s = payload.decode(errors="ignore").strip()
            # garde juste un nombre 0..100 si possible
            digits = "".join(ch for ch in s if ch.isdigit())
            if digits:
                v = int(digits)
                v = max(0, min(100, v))
                last_battery = v
                print(f"[BATT] {last_battery}%")
        except Exception as e:
            print("[BATT] Erreur:", e)
        return

    # --- début d'image ---
    if topic == TOPIC_START:
        try:
            expected_size = int(payload.decode(errors="ignore").strip())
        except ValueError:
            expected_size = 0
        current_buffer = bytearray()
        receiving = True
        print(f"[START] Nouvelle image, taille annoncée : {expected_size} octets")
        return

    # --- chunks ---
    if topic == TOPIC_DATA and receiving:
        current_buffer.extend(payload)
        return

    # --- fin d'image ---
    if topic == TOPIC_END and receiving:
        receiving = False
        got = len(current_buffer)
        print(f"[END] Image terminée ({got}/{expected_size} octets)")

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{ts}.jpg"
        filepath = os.path.join(IMAGES_DIR, filename)

        # Sauvegarde fichier
        try:
            with open(filepath, "wb") as f:
                f.write(current_buffer)
            print(f"[SAVE] Image sauvegardée : {filepath}")
        except Exception as e:
            print(f"[ERROR] Impossible de sauvegarder l'image : {e}")
            current_buffer = bytearray()
            return

        # Sauvegarde en base (avec batterie)
        try:
            save_to_db(filename, filepath, last_battery)
            print(f"[DB] Image enregistrée (battery={last_battery})")
        except Exception as e:
            print(f"[DB] Erreur lors de l'enregistrement : {e}")

        # Nettoyage
        try:
            cleanup_old_images()
        except Exception as e:
            print(f"[CLEAN] Erreur nettoyage : {e}")

        current_buffer = bytearray()

# -------- MAIN --------
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883)

print("En attente d'images MQTT...")
client.loop_forever()

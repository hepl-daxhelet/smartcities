#!/usr/bin/env python3
import os
import glob
import traceback
from flask import Flask, request, redirect, url_for, send_from_directory, Response
import mysql.connector

# =========================================================
# CONFIG
# =========================================================
IMAGES_DIR = "/home/etann/Pictures"

DB_CONFIG = {
    "host": "localhost",
    "user": "birdcam",
    "password": "birdcam123",
    "database": "birdcam",
    "autocommit": True,
}

PORT = 5000

app = Flask(__name__)


# =========================================================
# DB helpers
# =========================================================
def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_photos(limit=50):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT id, ts, topic, filename, path, battery
        FROM photos
        ORDER BY id DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    db.close()
    return rows


# =========================================================
# HTML (intégré dans ce fichier)
# =========================================================
def render_index_html(photos, battery):
    # Dernière image
    last_block = ""
    if photos:
        last = photos[0]
        last_block = f"""
        <div class="card">
            <div class="card-head">
                <div>
                    <div class="title">Dernière image reçue</div>
                    <div class="meta">🕒 {last['ts']} — 📁 {last['filename']} — 🧩 {last['topic']}</div>
                </div>
            </div>
            <a class="bigimg" href="/img/{last['filename']}" target="_blank">
                <img src="/img/{last['filename']}" alt="Dernière image">
            </a>
        </div>
        """
    else:
        last_block = """
        <div class="card">
            <div class="title">Aucune image pour l’instant</div>
            <div class="meta">Dès qu’une photo arrive, elle apparaîtra ici.</div>
        </div>
        """

    # Grille d’historique
    grid_items = []
    for p in photos:
        grid_items.append(f"""
        <div class="thumb">
            <label class="chk">
                <input type="checkbox" name="delete_ids" value="{p['id']}">
                <span>ID {p['id']}</span>
            </label>
            <a href="/img/{p['filename']}" target="_blank">
                <img src="/img/{p['filename']}" alt="{p['filename']}">
            </a>
            <div class="thumb-meta">
                <div class="ts">{p['ts']}</div>
                <div class="fn">{p['filename']}</div>
            </div>
        </div>
        """)

    bat_text = "--"
    if battery is not None:
        bat_text = str(battery)

    html = f"""
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BirdCam</title>
<style>
    body {{
        margin:0;
        font-family: Arial, sans-serif;
        background:#0b0f14;
        color:#e9eef7;
    }}
    header {{
        position: sticky;
        top: 0;
        z-index: 10;
        display:flex;
        align-items:center;
        gap:10px;
        padding:12px 14px;
        background: linear-gradient(90deg,#0b2b63,#0d6b6b);
        box-shadow: 0 10px 25px rgba(0,0,0,.35);
    }}
    .brand {{
        font-weight:900;
        font-size:20px;
        display:flex;
        align-items:center;
        gap:8px;
    }}
    .spacer {{ flex:1; }}
    .battery {{
        padding:6px 12px;
        border-radius:999px;
        background: rgba(255,255,255,0.14);
        border:1px solid rgba(255,255,255,0.15);
        font-weight:800;
    }}
    .btn {{
        cursor:pointer;
        border:none;
        color:#fff;
        background: rgba(0,0,0,0.35);
        padding:9px 12px;
        border-radius:999px;
        font-weight:800;
    }}
    .btn:hover {{ background: rgba(0,0,0,0.5); }}
    .btn.danger {{ background: rgba(185,0,0,0.6); }}
    .btn.danger:hover {{ background: rgba(185,0,0,0.8); }}
    .container {{
        max-width: 1200px;
        margin: 20px auto;
        padding: 0 14px 40px;
    }}
    .card {{
        background: rgba(20,26,40,0.72);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        box-shadow: 0 18px 40px rgba(0,0,0,0.35);
        padding: 16px;
        margin-bottom: 18px;
    }}
    .title {{
        font-size: 20px;
        font-weight: 900;
        margin-bottom: 6px;
    }}
    .meta {{
        font-size: 13px;
        opacity: .85;
    }}
    .bigimg {{
        margin-top: 12px;
        display:block;
        border-radius: 14px;
        overflow:hidden;
        border:1px solid rgba(255,255,255,0.10);
        background: rgba(0,0,0,0.25);
    }}
    .bigimg img {{
        width: 100%;
        display:block;
    }}
    .section-title {{
        font-size: 16px;
        font-weight: 900;
        margin: 18px 0 10px;
        opacity: .95;
    }}
    .grid {{
        display:grid;
        grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
        gap: 12px;
    }}
    .thumb {{
        position:relative;
        overflow:hidden;
        border-radius: 14px;
        background: rgba(20,26,40,0.72);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 10px;
        box-shadow: 0 14px 30px rgba(0,0,0,0.30);
    }}
    .thumb img {{
        width:100%;
        height:140px;
        object-fit: cover;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.10);
        display:block;
    }}
    .thumb-meta {{
        margin-top:8px;
        font-size:13px;
        opacity:.92;
        line-height:1.25;
        word-break: break-word;
    }}
    .thumb-meta .ts {{ font-size:12px; opacity:.8; }}
    .thumb-meta .fn {{ font-size:13px; }}
    .chk {{
        position:absolute;
        top:10px;
        left:10px;
        background: rgba(0,0,0,0.45);
        padding: 5px 8px;
        border-radius: 999px;
        display:flex;
        align-items:center;
        gap:6px;
        font-size:12px;
        border:1px solid rgba(255,255,255,0.12);
    }}
    .chk input {{
        transform: scale(1.2);
        accent-color: #17bebb;
    }}
    form.actions {{
        display:flex;
        gap:10px;
        align-items:center;
        margin:0;
    }}
</style>
</head>
<body>

<header>
    <div class="brand">🐦 BirdCam</div>

    <div class="spacer"></div>

    <!-- Batterie en haut -->
    <div class="battery">🔋 {bat_text}%</div>

    <button class="btn" onclick="location.reload()">🔄 Rafraîchir</button>

    <form class="actions" method="POST" action="/delete_selected" onsubmit="return confirm('Supprimer les images sélectionnées ?');">
        <button class="btn danger" type="submit">🗑 Supprimer sélection</button>
    </form>

    <form class="actions" method="POST" action="/delete_all" onsubmit="return confirm('Tout supprimer ?');">
        <button class="btn danger" type="submit">🗑 Tout supprimer</button>
    </form>
</header>

<div class="container">
    {last_block}

    <div class="section-title">Historique (50 dernières images)</div>

    <form method="POST" action="/delete_selected" onsubmit="return confirm('Supprimer les images sélectionnées ?');">
        <div class="grid">
            {"".join(grid_items)}
        </div>
        <!-- bouton en bas aussi (optionnel) -->
        <div style="margin-top:14px;">
            <button class="btn danger" type="submit">🗑 Supprimer sélection</button>
        </div>
    </form>
</div>

</body>
</html>
"""
    return html


# =========================================================
# Routes
# =========================================================
@app.route("/")
def index():
    try:
        photos = fetch_photos(50)
    except Exception:
        traceback.print_exc()
        photos = []

    # batterie = valeur associée à la photo la plus récente (si stockée dans photos)
    battery = None
    if photos:
        try:
            battery = photos[0].get("battery", None)
        except Exception:
            battery = None

    return Response(render_index_html(photos, battery), mimetype="text/html")


@app.route("/img/<path:filename>")
def img(filename):
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/delete_selected", methods=["POST"])
def delete_selected():
    ids = request.form.getlist("delete_ids")

    if not ids:
        return redirect(url_for("index"))

    try:
        db = get_db()
        cur = db.cursor()

        for img_id in ids:
            cur.execute(
                "SELECT filename FROM photos WHERE id = %s",
                (img_id,)
            )
            row = cur.fetchone()

            if row:
                filename = row[0]
                file_path = os.path.join(IMAGES_DIR, filename)

                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print("Erreur suppression fichier:", e)

                cur.execute("DELETE FROM photos WHERE id = %s", (img_id,))

        db.commit()
        cur.close()
        db.close()

        print("✔ Images sélectionnées supprimées")

    except Exception as e:
        print("❌ ERREUR delete_selected :", e)
        traceback.print_exc()

    return redirect(url_for("index"))



@app.route("/delete_all", methods=["POST"])
def delete_all():
    try:
        # --- 1) SUPPRESSION DES FICHIERS ---
        for f in os.listdir(IMAGES_DIR):
            if f.lower().endswith((".jpg", ".jpeg")):
                try:
                    os.remove(os.path.join(IMAGES_DIR, f))
                except Exception as e:
                    print("Erreur suppression fichier:", e)

        # --- 2) SUPPRESSION BASE DE DONNÉES ---
        db = get_db()
        cur = db.cursor()

        cur.execute("DELETE FROM photos")
        db.commit()

        cur.close()
        db.close()

        print("✔ Toutes les images et références supprimées")

    except Exception as e:
        print("❌ ERREUR delete_all :", e)
        traceback.print_exc()

    return redirect(url_for("index"))


# =========================================================
# Run
# =========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)

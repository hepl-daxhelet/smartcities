#!/usr/bin/env python3
import os
import glob
from datetime import datetime

from flask import (
    Flask,
    request,
    send_from_directory,
    redirect,
    url_for,
    render_template_string,
    jsonify,
)
import mysql.connector

# ---------- CONFIG ----------

IMAGES_DIR = "/home/etann/Pictures"

DB_CONFIG = {
    "host": "localhost",
    "user": "birdcam",
    "password": "birdcam123",
    "database": "birdcam",
}

app = Flask(__name__)


# ---------- ACCÈS BDD ----------

def get_db():
    """Retourne une connexion MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


# ---------- ROUTES ----------


@app.route("/")
def index():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        """
        SELECT id, ts, topic, filename, path
        FROM photos
        ORDER BY id DESC
        LIMIT 50
        """
    )
    photos = cur.fetchall()
    cur.close()
    db.close()

    last_id = photos[0]["id"] if photos else 0

    html = """
    <!doctype html>
    <html lang="fr">
    <head>
        <meta charset="utf-8">
        <title>BirdCam - Dernières images</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            :root {
                --bg-main: #050816;
                --bg-card: #0b1020;
                --bg-chip: #12172b;
                --accent: #3b82f6;
                --accent-soft: rgba(59,130,246,0.15);
                --accent-danger: #ef4444;
                --accent-danger-soft: rgba(239,68,68,0.12);
                --text-main: #e5e7eb;
                --text-sub: #9ca3af;
                --border-subtle: rgba(148,163,184,0.25);
                --shadow-soft: 0 18px 45px rgba(15,23,42,0.8);
                --radius-lg: 18px;
                --radius-pill: 999px;
            }
            * {
                box-sizing: border-box;
            }
            body {
                margin: 0;
                min-height: 100vh;
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text",
                             "Segoe UI", sans-serif;
                background: radial-gradient(circle at top, #0f172a 0, #020617 45%, #000 100%);
                color: var(--text-main);
            }
            .page {
                max-width: 1200px;
                margin: 0 auto;
                padding: 24px 20px 40px;
            }
            header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 16px;
                margin-bottom: 24px;
            }
            .brand {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .brand-icon {
                width: 38px;
                height: 38px;
                border-radius: 12px;
                background: radial-gradient(circle at 30% 20%, #f97316 0, #ec4899 40%, #6366f1 100%);
                display: inline-flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 10px 30px rgba(79,70,229,0.55);
                font-size: 22px;
            }
            .brand-text-title {
                font-weight: 600;
                letter-spacing: 0.03em;
            }
            .brand-text-sub {
                font-size: 12px;
                color: var(--text-sub);
            }

            .toolbar {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .btn {
                border: 1px solid transparent;
                border-radius: var(--radius-pill);
                padding: 7px 16px;
                font-size: 13px;
                font-weight: 500;
                background: rgba(15,23,42,0.9);
                color: var(--text-main);
                display: inline-flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                transition: all 0.15s ease-out;
                text-decoration: none;
                box-shadow: 0 0 0 1px rgba(148,163,184,0.2);
            }
            .btn span.icon {
                font-size: 14px;
            }
            .btn-primary {
                background: linear-gradient(135deg,#3b82f6,#6366f1);
                border-color: transparent;
                box-shadow: 0 14px 30px rgba(37,99,235,0.55);
            }
            .btn-primary:hover {
                filter: brightness(1.08);
                transform: translateY(-1px);
            }
            .btn-danger {
                background: rgba(127,29,29,0.08);
                color: #fecaca;
                border-color: rgba(248,113,113,0.4);
            }
            .btn-danger:hover {
                background: rgba(127,29,29,0.2);
            }
            .btn-ghost {
                background: rgba(15,23,42,0.9);
            }
            .btn-ghost:hover {
                background: rgba(15,23,42,0.7);
            }

            .card {
                background: radial-gradient(circle at top left,#1f2937 0,#020617 55%);
                border-radius: var(--radius-lg);
                border: 1px solid rgba(148,163,184,0.28);
                box-shadow: var(--shadow-soft);
                padding: 18px 18px 14px;
                margin-bottom: 24px;
                position: relative;
                overflow: hidden;
            }
            .card::before {
                content:"";
                position:absolute;
                inset:-40px;
                background: radial-gradient(circle at 0 0,rgba(56,189,248,0.15) 0,transparent 55%);
                opacity:0.9;
                pointer-events:none;
            }
            .card-header {
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:14px;
                position:relative;
                z-index:1;
            }
            .card-title {
                font-size:16px;
                font-weight:550;
            }
            .card-meta {
                font-size:12px;
                color:var(--text-sub);
            }
            .chip {
                display:inline-flex;
                align-items:center;
                gap:6px;
                background:var(--bg-chip);
                border-radius:999px;
                padding:3px 10px;
                font-size:11px;
                border:1px solid rgba(148,163,184,0.35);
            }
            .chip-dot {
                width:7px;
                height:7px;
                border-radius:999px;
                background:#22c55e;
                box-shadow:0 0 0 3px rgba(34,197,94,0.18);
            }

            .latest-preview {
                margin-top:14px;
                border-radius:14px;
                overflow:hidden;
                border:1px solid rgba(15,23,42,0.85);
                background:#020617;
                max-height:380px;
            }
            .latest-preview-inner {
                display:flex;
                justify-content:center;
                align-items:center;
                background:radial-gradient(circle at top,#020617 0,#000 60%);
            }
            .latest-preview img {
                max-width:100%;
                max-height:380px;
                display:block;
            }
            .empty {
                padding:60px 24px 48px;
                text-align:center;
                color:var(--text-sub);
                font-size:14px;
            }

            h2.section-title {
                font-size:15px;
                font-weight:550;
                margin:0 0 10px;
                color:#e5e7eb;
            }
            .section-sub {
                font-size:12px;
                color:var(--text-sub);
                margin-bottom:14px;
            }
            .grid {
                display:grid;
                grid-template-columns:repeat(auto-fill,minmax(210px,1fr));
                gap:14px;
            }
            .thumb-card {
                position:relative;
                border-radius:16px;
                background:var(--bg-card);
                border:1px solid var(--border-subtle);
                overflow:hidden;
                box-shadow:0 16px 30px rgba(15,23,42,0.7);
                transition:all 0.16s ease-out;
            }
            .thumb-card:hover {
                transform:translateY(-3px);
                box-shadow:0 22px 40px rgba(15,23,42,0.9);
                border-color:rgba(96,165,250,0.6);
            }
            .thumb-image-wrap {
                background:#020617;
                border-bottom:1px solid rgba(15,23,42,0.9);
                height:150px;
                display:flex;
                justify-content:center;
                align-items:center;
            }
            .thumb-image-wrap img {
                max-width:100%;
                max-height:150px;
                display:block;
            }
            .thumb-body {
                padding:9px 10px 9px;
                font-size:12px;
            }
            .thumb-filename {
                font-size:12px;
                color:#e5e7eb;
                margin-bottom:4px;
                white-space:nowrap;
                overflow:hidden;
                text-overflow:ellipsis;
            }
            .thumb-meta {
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:8px;
                color:var(--text-sub);
            }
            .thumb-date {
                font-size:11px;
            }
            .thumb-topic {
                font-size:11px;
                padding:2px 7px;
                border-radius:999px;
                background:var(--accent-soft);
                color:#bfdbfe;
            }
            .thumb-select {
                position:absolute;
                top:8px;
                left:8px;
                background:rgba(15,23,42,0.9);
                border-radius:999px;
                padding:3px 7px;
                font-size:11px;
                display:flex;
                align-items:center;
                gap:4px;
                color:var(--text-sub);
            }
            .thumb-select input {
                accent-color:#3b82f6;
            }
            .selection-bar {
                margin-top:10px;
                display:flex;
                justify-content:flex-start;
                gap:10px;
            }
            .btn-small {
                padding:5px 12px;
                font-size:12px;
            }

            @media (max-width:640px){
                header{
                    flex-direction:column;
                    align-items:flex-start;
                }
                .toolbar{
                    align-self:stretch;
                    justify-content:flex-start;
                    flex-wrap:wrap;
                }
            }
        </style>
    </head>
    <body>
        <div class="page">
            <header>
                <div class="brand">
                    <div class="brand-icon">🕊️</div>
                    <div>
                        <div class="brand-text-title">BirdCam</div>
                        <div class="brand-text-sub">Nichoir – ESP32-CAM &amp; Raspberry Pi</div>
                    </div>
                </div>
                <div class="toolbar">
                    <a href="{{ url_for('index') }}" class="btn btn-ghost">
                        <span class="icon">🔄</span>
                        <span>Rafraîchir</span>
                    </a>
                    <form method="post" action="{{ url_for('delete_selected') }}">
                        <button type="submit" class="btn btn-danger">
                            <span class="icon">🗑️</span>
                            <span>Supprimer sélection</span>
                        </button>
                </div>
            </header>

            {% if photos %}
            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="card-title">Dernière image reçue</div>
                        <div class="card-meta">
                            Fichier : {{ photos[0].filename }} — Topic : {{ photos[0].topic }}
                        </div>
                    </div>
                    <div class="chip">
                        <span class="chip-dot"></span>
                        <span>{{ photos[0].ts }}</span>
                    </div>
                </div>
                <div class="latest-preview">
                    <div class="latest-preview-inner">
                        <a href="{{ url_for('serve_image', filename=photos[0].filename) }}" target="_blank">
                            <img src="{{ url_for('serve_image', filename=photos[0].filename) }}" alt="Dernière image">
                        </a>
                    </div>
                </div>
            </div>

            <section>
                <h2 class="section-title">Historique (jusqu'à 50 dernières images)</h2>
                <p class="section-sub">
                    Coche les images à supprimer, puis clique sur <strong>Supprimer sélection</strong>.
                </p>

                <div class="grid">
                    {% for p in photos %}
                    <div class="thumb-card">
                        <label class="thumb-select">
                            <input type="checkbox" name="delete_ids" value="{{ p.id }}">
                            <span>ID {{ p.id }}</span>
                        </label>
                        <div class="thumb-image-wrap">
                            <a href="{{ url_for('serve_image', filename=p.filename) }}" target="_blank">
                                <img src="{{ url_for('serve_image', filename=p.filename) }}" alt="{{ p.filename }}">
                            </a>
                        </div>
                        <div class="thumb-body">
                            <div class="thumb-filename" title="{{ p.filename }}">{{ p.filename }}</div>
                            <div class="thumb-meta">
                                <div class="thumb-date">{{ p.ts }}</div>
                                <div class="thumb-topic">{{ p.topic }}</div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <div class="selection-bar">
                    <button type="submit" class="btn btn-danger btn-small">
                        <span class="icon">🗑️</span>
                        <span>Supprimer sélection</span>
                    </button>
                    </form>
                    <form method="post" action="{{ url_for('delete_all') }}">
                        <button type="submit" class="btn btn-danger btn-small">
                            <span class="icon">🧨</span>
                            <span>Tout supprimer</span>
                        </button>
                    </form>
                </div>
            </section>
            {% else %}
            <div class="card">
                <div class="empty">
                    <p>Aucune image pour l’instant.</p>
                    <p>La page se mettra à jour dès qu’une photo sera reçue.</p>
                </div>
            </div>
            {% endif %}
        </div>

        <script>
            // Auto-mise à jour quand une nouvelle image arrive :
            // on interroge périodiquement /api/last_id, et on ne recharge
            // la page que si l'ID a changé.
            const initialLastId = {{ last_id }};
            async function checkForNewImage() {
                try {
                    const resp = await fetch("/api/last_id");
                    if (!resp.ok) return;
                    const data = await resp.json();
                    if (data.id > initialLastId) {
                        window.location.reload();
                    }
                } catch (e) {
                    // ignore erreurs réseau
                }
            }
            // Vérifie toutes les 5 secondes
            setInterval(checkForNewImage, 5000);
        </script>
    </body>
    </html>
    """

    return render_template_string(html, photos=photos, last_id=last_id)


@app.route("/api/last_id")
def api_last_id():
    """Retourne l'ID de la dernière image, pour l'auto-refresh JS."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM photos")
    (last_id,) = cur.fetchone()
    cur.close()
    db.close()
    return jsonify({"id": int(last_id)})


@app.route("/img/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/delete_all", methods=["POST"])
def delete_all():
    # Supprime les fichiers du disque
    for f in glob.glob(os.path.join(IMAGES_DIR, "*.jpg")):
        try:
            os.remove(f)
        except FileNotFoundError:
            pass

    # Vide la table
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM photos")
    db.commit()
    cur.close()
    db.close()
    return redirect(url_for("index"))


@app.route("/delete_selected", methods=["POST"])
def delete_selected():
    ids = request.form.getlist("delete_ids")
    if not ids:
        return redirect(url_for("index"))

    db = get_db()
    cur = db.cursor()

    # Récupérer chemins pour supprimer les fichiers
    format_ids = ",".join(["%s"] * len(ids))
    cur.execute(f"SELECT path FROM photos WHERE id IN ({format_ids})", ids)
    for (path,) in cur.fetchall():
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    # Supprimer de la base
    cur.execute(f"DELETE FROM photos WHERE id IN ({format_ids})", ids)
    db.commit()
    cur.close()
    db.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

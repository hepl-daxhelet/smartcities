from flask import Flask, render_template_string, send_from_directory, redirect, url_for, request
import os
from datetime import datetime

IMAGES_DIR = "/home/etann/Pictures"

app = Flask(__name__)

TEMPLATE_INDEX = """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>BirdCam</title>
  <style>
    :root { color-scheme: dark; }
    * { box-sizing: border-box; }
    body{
      margin:0;
      background:#020617;
      color:#e5e7eb;
      font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
    }
    header{
      background:radial-gradient(circle at top left,#1d4ed8,#0f766e);
      padding:12px 20px;
      display:flex;
      justify-content:space-between;
      align-items:center;
      box-shadow:0 10px 25px rgba(0,0,0,0.45);
    }
    header h1{
      margin:0;
      font-size:1.3rem;
      display:flex;
      align-items:center;
      gap:8px;
    }
    header h1 span.logo-circle{
      width:26px;height:26px;border-radius:999px;
      background:rgba(15,23,42,0.35);
      display:flex;align-items:center;justify-content:center;
      font-size:1.1rem;
    }
    header .right{
      display:flex;gap:8px;align-items:center;font-size:0.85rem;
    }
    .pill{
      padding:4px 9px;border-radius:999px;
      border:1px solid rgba(226,232,240,0.2);
      background:rgba(15,23,42,0.35);
    }
    .pill span.label{color:#9ca3af;margin-right:4px;}
    .pill span.value{font-weight:500;}
    .btn{
      padding:6px 12px;background:#020617dd;border-radius:999px;
      color:#e5e7eb;border:1px solid #4b556388;text-decoration:none;
      font-size:0.85rem;cursor:pointer;display:inline-flex;
      align-items:center;gap:6px;
    }
    .btn:hover{background:#020617;border-color:#e5e7ebaa;}
    main{padding:18px;max-width:1200px;margin:0 auto 40px;}
    .panel{
      background:rgba(15,23,42,0.95);border-radius:16px;
      padding:14px;border:1px solid #111827;
      box-shadow:0 18px 40px rgba(0,0,0,0.6);
    }
    .panel-header{
      display:flex;justify-content:space-between;align-items:center;
      margin-bottom:8px;font-size:0.9rem;
    }
    .panel-title{font-weight:500;display:flex;align-items:center;gap:6px;}
    .panel-title span.dot{
      width:8px;height:8px;border-radius:999px;
      background:#22c55e;box-shadow:0 0 8px #22c55e99;
    }
    .panel-meta{font-size:0.8rem;color:#9ca3af;}
    .latest-wrapper{text-align:center;margin-top:6px;}
    .latest-wrapper img{
      max-width:100%;max-height:500px;border-radius:12px;
      border:1px solid #1f2937;
    }
    .empty{text-align:center;padding:30px 10px;color:#9ca3af;font-size:0.9rem;}
    .empty span{display:block;margin-top:4px;font-size:0.8rem;}
    hr{border-color:#111827;margin:22px 0;}
    .section-title{
      display:flex;justify-content:space-between;align-items:center;
      font-size:0.95rem;margin-bottom:10px;
    }
    .section-title span.sub{font-size:0.8rem;color:#9ca3af;}
    .grid{
      display:grid;
      grid-template-columns:repeat(auto-fill,minmax(170px,1fr));
      gap:10px;
    }
    .card{
      background:#020617;padding:8px;border-radius:10px;
      border:1px solid #111827;text-align:center;font-size:0.8rem;
      display:flex;flex-direction:column;gap:5px;
      transition:transform 0.09s ease,box-shadow 0.09s ease,border-color 0.09s ease;
    }
    .card:hover{
      transform:translateY(-2px);
      box-shadow:0 16px 32px rgba(0,0,0,0.7);
      border-color:#1d4ed8;
    }
    .card img{
      max-width:100%;max-height:130px;border-radius:8px;
      border:1px solid #0f172a;
    }
    .card small{color:#9ca3af;display:block;}
    .card input[type=checkbox]{margin-bottom:3px;}
    form.delete-form{margin-top:12px;text-align:center;}
    .footer-note{
      margin-top:14px;font-size:0.75rem;color:#6b7280;text-align:center;
    }
  </style>
</head>
<body>

<header>
  <h1>
    <span class="logo-circle">🐦</span>
    <span>BirdCam</span>
  </h1>
  <div class="right">
    <div class="pill">
      <span class="label">Dernière mise à jour :</span>
      <span class="value">
        {% if latest %}{{ latest.ts_str }}{% else %}Aucune image{% endif %}
      </span>
    </div>
    <button class="btn" onclick="location.reload()">
      🔄 Rafraîchir
    </button>
    <a class="btn" href="{{ url_for('delete_all') }}"
       onclick="return confirm('Supprimer TOUTES les images ?')">
      🗑️ Tout supprimer
    </a>
  </div>
</header>

<main>
  <section class="panel">
    {% if latest %}
      <div class="panel-header">
        <div class="panel-title">
          <span class="dot"></span>
          <span>Dernière image reçue</span>
        </div>
        <div class="panel-meta">
          {{ latest.name }}
        </div>
      </div>
      <div class="latest-wrapper">
        <a href="{{ url_for('serve_image', filename=latest.name) }}" target="_blank">
          <img src="{{ url_for('serve_image', filename=latest.name) }}" alt="{{ latest.name }}">
        </a>
      </div>
    {% else %}
      <div class="empty">
        <div>Aucune image reçue pour l’instant.</div>
        <span>Appuie sur “Rafraîchir” après avoir envoyé une photo.</span>
      </div>
    {% endif %}
  </section>

  <hr>

  {% if photos %}
    <section>
      <div class="section-title">
        <div>Historique (jusqu’à 50 images)</div>
        <div class="sub">Coche et supprime ce que tu veux.</div>
      </div>
      <form method="POST" action="{{ url_for('delete_selected') }}" class="delete-form">
        <div class="grid">
          {% for p in photos %}
          <div class="card">
            <input type="checkbox" name="delete_names" value="{{ p.name }}">
            <a href="{{ url_for('serve_image', filename=p.name) }}" target="_blank">
              <img src="{{ url_for('serve_image', filename=p.name) }}" alt="{{ p.name }}">
            </a>
            <div>{{ p.ts_str }}</div>
            <small>{{ p.name }}</small>
          </div>
          {% endfor %}
        </div>
        <button class="btn" type="submit"
                style="margin-top:12px;"
                onclick="return confirm('Supprimer les images sélectionnées ?')">
          🗑️ Supprimer la sélection
        </button>
      </form>
      <div class="footer-note">
        Les images les plus anciennes sont automatiquement supprimées côté Raspberry si tu dépasses 50 fichiers.
      </div>
    </section>
  {% else %}
    <div class="empty">
      <div>Aucune image dans l’historique.</div>
      <span>Quand tu auras pris plusieurs photos, elles apparaîtront ici.</span>
    </div>
  {% endif %}
</main>

</body>
</html>
"""

def list_images():
    """Lit les .jpg du dossier, triés par date (plus récent d'abord)."""
    if not os.path.isdir(IMAGES_DIR):
        return []
    files = [
        f for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith(".jpg")
    ]
    items = []
    for name in files:
        path = os.path.join(IMAGES_DIR, name)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        dt = datetime.fromtimestamp(mtime)
        items.append({
            "name": name,
            "ts": dt,
            "ts_str": dt.strftime("%Y-%m-%d %H:%M:%S"),
        })
    items.sort(key=lambda x: x["ts"], reverse=True)
    # on limite à 50 images max
    return items[:50]

@app.route("/")
def index():
    items = list_images()
    if not items:
        latest = None
        photos = []
    else:
        latest = items[0]
        photos = items[1:]
    return render_template_string(TEMPLATE_INDEX, latest=latest, photos=photos)

@app.route("/img/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

@app.route("/delete_all")
def delete_all():
    if os.path.isdir(IMAGES_DIR):
        for name in os.listdir(IMAGES_DIR):
            if name.lower().endswith(".jpg"):
                path = os.path.join(IMAGES_DIR, name)
                try:
                    os.remove(path)
                except:
                    pass
    return redirect(url_for("index"))

@app.route("/delete_selected", methods=["POST"])
def delete_selected():
    names = request.form.getlist("delete_names")
    if not names:
        return redirect(url_for("index"))
    for name in names:
        path = os.path.join(IMAGES_DIR, name)
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            pass
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

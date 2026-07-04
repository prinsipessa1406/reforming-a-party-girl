#!/usr/bin/env python3
"""
Lokal redigerare för "Reforming a Party Girl".

Kör:  python3 editor.py
Öppnar automatiskt http://localhost:5050 i webbläsaren.

Inget behov av att röra JSON-filer eller Terminal-kommandon för att
lägga till, redigera eller ta bort en historia — allt sker i formuläret.
"""
import json
import os
import re
import subprocess
import threading
import webbrowser
from datetime import date

from flask import Flask, request

import build as site  # återanvänder CATEGORIES, ROOT, etc. från build.py

ROOT = site.ROOT
LOCALES = site.LOCALES
PORT = 5050

app = Flask(__name__)


# ---------- data helpers ----------

def stories_path(locale):
    return os.path.join(ROOT, "content", locale, "stories.json")


def load_stories(locale):
    with open(stories_path(locale), encoding="utf-8") as f:
        return json.load(f)


def save_stories(locale, stories):
    with open(stories_path(locale), "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
        f.write("\n")


def find_index(stories, slug):
    for i, s in enumerate(stories):
        if s["slug"] == slug:
            return i
    return None


def word_count(paragraphs):
    text = " ".join(p[2:] if p.startswith("> ") else p for p in paragraphs)
    return len(text.split())


def read_time_label(paragraphs, locale):
    minutes = max(1, round(word_count(paragraphs) / 200))
    return f"{minutes} min läsning" if locale == "sv" else f"{minutes} min read"


def parse_content(raw_text):
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw_text.strip()) if b.strip()]
    return blocks


def run(cmd):
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (result.stdout or "") + (result.stderr or "")
    return result.returncode, out


# ---------- layout ----------

def page(title, body, flash=""):
    flash_html = f'<div class="flash">{flash}</div>' if flash else ""
    return f"""<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="UTF-8">
<title>{title} — Redigeraren</title>
<style>
  body{{ font-family: -apple-system, sans-serif; background:#faf8f6; color:#18131c; margin:0; }}
  .wrap{{ max-width: 780px; margin: 0 auto; padding: 30px 24px 80px; }}
  h1{{ font-size: 26px; margin: 0 0 6px; }}
  .sub{{ color:#6e6178; margin: 0 0 30px; font-size:14px; }}
  a{{ color:#c9457c; }}
  .flash{{ background:#f8cfe0; padding:12px 16px; border-radius:4px; margin-bottom:24px; font-size:14px; white-space:pre-wrap; }}
  .row{{ display:flex; justify-content:space-between; align-items:center; padding:14px 0; border-bottom:1px solid #eee; gap: 12px; }}
  .row div:first-child{{ flex: 1; }}
  .row .meta{{ color:#6e6178; font-size:13px; }}
  .btn{{ display:inline-block; background:#18131c; color:#fff; padding:10px 18px; border-radius:4px; text-decoration:none; font-size:14px; border:none; cursor:pointer; font-family:inherit; }}
  .btn:hover{{ background:#c9457c; }}
  .btn-secondary{{ background:#fff; color:#18131c; border:1px solid #ccc; }}
  .btn-danger{{ background:#fff; color:#b8461f; border:1px solid #b8461f; }}
  form{{ margin: 0; }}
  fieldset{{ border:1px solid #eee; border-radius:6px; padding:18px; margin: 0 0 20px; }}
  legend{{ font-weight:600; padding: 0 8px; }}
  label{{ display:block; font-size:13px; font-weight:600; margin: 14px 0 4px; }}
  input[type=text], input[type=date], select, textarea{{
    width:100%; padding:9px 10px; font-size:14px; border:1px solid #ccc; border-radius:4px; font-family:inherit; box-sizing:border-box;
  }}
  textarea{{ min-height: 160px; }}
  .help{{ font-size:12px; color:#6e6178; margin-top:4px; }}
  .actions{{ margin-top:28px; display:flex; gap:10px; flex-wrap:wrap; }}
  .top-actions{{ display:flex; gap:10px; margin: 24px 0; flex-wrap:wrap; }}
  .checkbox-row{{ display:flex; align-items:center; gap:8px; margin-top:14px; }}
  .checkbox-row input{{ width:auto; }}
  .checkbox-row label{{ margin:0; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Reforming a Party Girl</h1>
  <p class="sub"><a href="/">← Alla historier</a></p>
  {flash_html}
  {body}
</div>
</body>
</html>"""


# ---------- routes ----------

@app.route("/")
def dashboard():
    stories = load_stories("sv")
    rows = ""
    for s in stories:
        cat = site.category_label("sv", s["category"])
        star = " ★" if s.get("featured") else ""
        rows += f"""<div class="row">
          <div><b>{s['title']}</b>{star}<div class="meta">{cat} · {s['date']} · {s['slug']}</div></div>
          <div><a class="btn btn-secondary" href="/story/edit/{s['slug']}">Redigera</a></div>
        </div>"""

    body = f"""
    <div class="top-actions">
      <a class="btn" href="/story/new">+ Ny historia</a>
      <form action="/build" method="post" style="display:inline"><button class="btn btn-secondary">Bygg om sidan</button></form>
      <form action="/publish" method="post" style="display:inline">
        <button class="btn btn-secondary">Skicka till GitHub</button>
      </form>
    </div>
    {rows}
    """
    return page("Alla historier", body)


def story_form(story=None, slug=None):
    is_new = story is None
    sv = story["sv"] if story else {}
    en = story["en"] if story else {}
    slug_val = slug or ""
    cat_options = "".join(
        f'<option value="{c["key"]}" {"selected" if sv.get("category") == c["key"] else ""}>{c["label"]["sv"]} / {c["label"]["en"]}</option>'
        for c in site.CATEGORIES
    )
    date_val = sv.get("date", date.today().isoformat())
    featured_checked = "checked" if sv.get("featured") else ""

    img_dir = os.path.join(ROOT, "assets", "img")
    existing_images = sorted(os.listdir(img_dir)) if os.path.isdir(img_dir) else []
    img_options = '<option value="">Ingen bild</option>' + "".join(
        f'<option value="{f}" {"selected" if sv.get("image") == f else ""}>{f}</option>' for f in existing_images
    )

    content_sv = "\n\n".join(sv.get("content", []))
    content_en = "\n\n".join(en.get("content", []))

    slug_field = (
        f'<input type="text" value="{slug_val}" disabled style="background:#f5f5f5">'
        f'<input type="hidden" name="slug" value="{slug_val}">'
        if not is_new else
        '<input type="text" name="slug" placeholder="t.ex. min-nya-historia" required pattern="[a-z0-9-]+">'
    )

    delete_btn = (
        f'<form action="/story/delete/{slug_val}" method="post" onsubmit="return confirm(\'Ta bort den här historien helt?\')" style="display:inline">'
        f'<button class="btn btn-danger">Ta bort historia</button></form>'
        if not is_new else ""
    )

    body = f"""
    <form action="/story/save" method="post" enctype="multipart/form-data">
      <fieldset>
        <legend>Grundinfo</legend>
        <label>Slug (unik URL-del, ändras inte efter att sidan skapats)</label>
        {slug_field}
        <label>Kategori</label>
        <select name="category">{cat_options}</select>
        <label>Datum</label>
        <input type="date" name="date" value="{date_val}">
        <div class="checkbox-row">
          <input type="checkbox" name="featured" id="featured" {featured_checked}>
          <label for="featured" style="margin:0">Framhävd (stor ruta överst på startsidan — bara en historia åt gången)</label>
        </div>
        <label>Bild</label>
        <select name="existing_image">{img_options}</select>
        <div class="help">Eller ladda upp en ny bild (sparas i assets/img):</div>
        <input type="file" name="new_image" accept="image/*">
      </fieldset>

      <fieldset>
        <legend>Svenska</legend>
        <label>Titel</label>
        <input type="text" name="title_sv" value="{sv.get('title','')}" required>
        <label>Ingress (kort mening under titeln)</label>
        <input type="text" name="dek_sv" value="{sv.get('dek','')}" required>
        <label>Innehåll</label>
        <textarea name="content_sv" required>{content_sv}</textarea>
        <div class="help">Ett stycke per rad, tom rad mellan styckena. En rad som börjar med "&gt; " blir ett utdraget citat.</div>
      </fieldset>

      <fieldset>
        <legend>English</legend>
        <label>Title</label>
        <input type="text" name="title_en" value="{en.get('title','')}" required>
        <label>Dek</label>
        <input type="text" name="dek_en" value="{en.get('dek','')}" required>
        <label>Content</label>
        <textarea name="content_en" required>{content_en}</textarea>
        <div class="help">One paragraph per block, blank line between paragraphs. A line starting with "&gt; " becomes a pull quote.</div>
      </fieldset>

      <div class="actions">
        <button class="btn" type="submit">Spara och bygg om</button>
        {delete_btn}
      </div>
    </form>
    """
    return body


@app.route("/story/new")
def story_new():
    return page("Ny historia", story_form())


@app.route("/story/edit/<slug>")
def story_edit(slug):
    sv_stories = load_stories("sv")
    en_stories = load_stories("en")
    sv = next((s for s in sv_stories if s["slug"] == slug), None)
    en = next((s for s in en_stories if s["slug"] == slug), None)
    if not sv:
        return page("Hittades inte", f"<p>Ingen historia med slug \"{slug}\" hittades.</p>")
    return page(f"Redigera: {sv['title']}", story_form({"sv": sv, "en": en or {}}, slug=slug))


@app.route("/story/save", methods=["POST"])
def story_save():
    f = request.form
    slug = f["slug"].strip().lower()
    if not re.match(r"^[a-z0-9-]+$", slug):
        return page("Fel", "<p>Slug får bara innehålla små bokstäver, siffror och bindestreck.</p>")

    category = f["category"]
    date_val = f["date"]
    featured = "featured" in f

    image = f.get("existing_image", "")
    upload = request.files.get("new_image")
    if upload and upload.filename:
        img_dir = os.path.join(ROOT, "assets", "img")
        os.makedirs(img_dir, exist_ok=True)
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "-", upload.filename)
        upload.save(os.path.join(img_dir, safe_name))
        image = safe_name

    content_sv = parse_content(f["content_sv"])
    content_en = parse_content(f["content_en"])

    new_sv = {
        "slug": slug,
        **({"image": image} if image else {}),
        "category": category,
        "title": f["title_sv"],
        "dek": f["dek_sv"],
        "date": date_val,
        "readTime": read_time_label(content_sv, "sv"),
        "featured": featured,
        "content": content_sv,
    }
    new_en = {
        "slug": slug,
        **({"image": image} if image else {}),
        "category": category,
        "title": f["title_en"],
        "dek": f["dek_en"],
        "date": date_val,
        "readTime": read_time_label(content_en, "en"),
        "featured": featured,
        "content": content_en,
    }

    for locale, new_story in (("sv", new_sv), ("en", new_en)):
        stories = load_stories(locale)
        idx = find_index(stories, slug)
        if featured:
            for s in stories:
                s["featured"] = False
        if idx is None:
            stories.append(new_story)
        else:
            stories[idx] = new_story
        save_stories(locale, stories)

    code, out = run(["python3", "build.py"])
    flash = "Sparat och sidan ombyggd.\n\n" + out if code == 0 else "Sparat, men bygget misslyckades:\n\n" + out
    return page("Sparat", '<p><a href="/">← Tillbaka till alla historier</a></p>', flash=flash)


@app.route("/story/delete/<slug>", methods=["POST"])
def story_delete(slug):
    for locale in LOCALES:
        stories = load_stories(locale)
        idx = find_index(stories, slug)
        if idx is not None:
            stories.pop(idx)
            save_stories(locale, stories)
    code, out = run(["python3", "build.py"])
    flash = f'Historien "{slug}" borttagen och sidan ombyggd.\n\n' + out
    return page("Borttagen", '<p><a href="/">← Tillbaka till alla historier</a></p>', flash=flash)


@app.route("/build", methods=["POST"])
def build_now():
    code, out = run(["python3", "build.py"])
    flash = out if code == 0 else "Bygget misslyckades:\n\n" + out
    return page("Byggresultat", '<p><a href="/">← Tillbaka</a></p>', flash=flash)


@app.route("/publish", methods=["POST"])
def publish():
    log = []
    code, out = run(["git", "add", "-A"])
    log.append(out)
    code, out = run(["git", "commit", "-m", "Uppdatering via redigeraren"])
    log.append(out)
    if "nothing to commit" in out:
        return page("Inget att skicka", '<p><a href="/">← Tillbaka</a></p>', flash="Inga ändringar att skicka — allt är redan sparat på GitHub.")
    code, out = run(["git", "push"])
    log.append(out)
    ok = code == 0
    flash = ("Skickat till GitHub!\n\n" if ok else "Något gick fel vid push:\n\n") + "\n".join(log)
    return page("Publicerat" if ok else "Fel", '<p><a href="/">← Tillbaka</a></p>', flash=flash)


if __name__ == "__main__":
    url = f"http://localhost:{PORT}"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"Öppnar {url} ...")
    app.run(port=PORT, debug=False)

#!/usr/bin/env python3
"""
Static site generator for "Reforming a Party Girl" — sv (default) + en mirror.

To add a new story: open content/sv/stories.json AND content/en/stories.json,
copy a story object into each with the SAME "slug", translate the fields,
save both. Then re-run:  python3 build.py
That's the whole workflow — no other file needs to change.

Locale routing:
  /                          -> Swedish (default, no prefix)
  /en/                       -> English mirror
Every route (index, about, each story) is built once per locale, with a
relative hreflang link + a manual SV/EN toggle in the nav pointing at its
counterpart, plus a small inline script that redirects on first visit based
on navigator.language (unless the visitor already picked a language).
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
LOCALES = ["sv", "en"]

CONTENT = {}
for loc in LOCALES:
    with open(os.path.join(ROOT, "content", loc, "site.json"), encoding="utf-8") as f:
        site = json.load(f)
    with open(os.path.join(ROOT, "content", loc, "stories.json"), encoding="utf-8") as f:
        stories = json.load(f)
    stories.sort(key=lambda s: s["date"], reverse=True)
    CONTENT[loc] = {"site": site, "stories": stories}

SITE_URL = CONTENT["sv"]["site"]["siteUrl"]

# Canonical category taxonomy — the "key" is the stable, locale-independent
# identifier used in URLs and in each story's "category" field. Only the
# displayed label is translated.
CATEGORIES = [
    {"key": "manifesto", "label": {"sv": "MANIFEST", "en": "MANIFESTO"}},
    {"key": "confessions", "label": {"sv": "BEKÄNNELSER", "en": "CONFESSIONS"}},
    {"key": "reckoning", "label": {"sv": "UPPGÖRELSE", "en": "RECKONING"}},
    {"key": "patterns", "label": {"sv": "MÖNSTER", "en": "PATTERNS"}},
    {"key": "astrology", "label": {"sv": "ASTROLOGI", "en": "ASTROLOGY"}},
]
CATEGORY_LABELS = {c["key"]: c["label"] for c in CATEGORIES}


def category_label(locale, key):
    return CATEGORY_LABELS[key][locale]


def category_relpath(key):
    return f"category/{key}/index.html"


def locale_prefix(locale):
    return "" if locale == "sv" else f"{locale}/"


def page_url(locale, relpath):
    prefix = locale_prefix(locale)
    if relpath == "index.html":
        return f"{SITE_URL}/{prefix}"
    if relpath.endswith("/index.html"):
        return f"{SITE_URL}/{prefix}{relpath[:-len('index.html')]}"
    return f"{SITE_URL}/{prefix}{relpath}"


def root_prefix(locale, relpath):
    """Relative path prefix to get back to the site root from this page."""
    depth = relpath.count("/")
    if locale != "sv":
        depth += 1
    return "../" * depth


def alt_href(locale, relpath):
    """Relative link from this page to its counterpart in the other locale."""
    other = "en" if locale == "sv" else "sv"
    rp = root_prefix(locale, relpath)
    return f"{rp}{'en/' if other == 'en' else ''}{relpath}"


def head_html(title, description, canonical, root, locale, relpath, extra_jsonld=""):
    alt = alt_href(locale, relpath)
    other_url = page_url("en" if locale == "sv" else "sv", relpath)
    lang_attr = locale
    redirect_script = f"""<script>
  (function(){{
    try{{
      var pref = localStorage.getItem('rapg_lang');
      var nav = (navigator.language || navigator.userLanguage || 'en').toLowerCase();
      var wantSv = pref ? pref === 'sv' : nav.indexOf('sv') === 0;
      var isSv = {str(locale == 'sv').lower()};
      if(!pref && wantSv !== isSv){{
        window.location.replace('{alt}');
      }}
    }}catch(e){{}}
  }})();
  </script>"""
    return f"""<meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="author" content="{CONTENT[locale]['site']['authorName']}">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="sv" href="{page_url('sv', relpath)}">
  <link rel="alternate" hreflang="en" href="{page_url('en', relpath)}">
  <link rel="alternate" hreflang="x-default" href="{page_url('sv', relpath)}">
  <link rel="icon" href="data:,">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:locale" content="{'sv_SE' if locale == 'sv' else 'en_US'}">
  <meta property="og:site_name" content="{CONTENT[locale]['site']['siteName']}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <link rel="stylesheet" href="{root}assets/css/style.css">
  {redirect_script}
  {extra_jsonld}"""


def nav_html(root, locale, relpath):
    alt = alt_href(locale, relpath)
    sv_href = "" if locale == "sv" else alt
    en_href = alt if locale == "sv" else ""
    sv_cls = "is-active" if locale == "sv" else ""
    en_cls = "is-active" if locale == "en" else ""
    sv_link = f'<a class="{sv_cls}" href="{root}index.html" onclick="localStorage.setItem(\'rapg_lang\',\'sv\')">SV</a>' if locale == "sv" else f'<a class="{sv_cls}" href="{sv_href}" onclick="localStorage.setItem(\'rapg_lang\',\'sv\')">SV</a>'
    en_link = f'<a class="{en_cls}" href="{en_href}" onclick="localStorage.setItem(\'rapg_lang\',\'en\')">EN</a>' if locale == "sv" else f'<a class="{en_cls}" href="{root}index.html" onclick="localStorage.setItem(\'rapg_lang\',\'en\')">EN</a>'
    return f"""<header class="site">
    <div class="wrap nav">
      <a class="nav__mark" href="{root}index.html">RAMA</a>
      <div class="nav__lang">{sv_link}<span>/</span>{en_link}</div>
    </div>
  </header>"""


def substrip_html(root, locale, active_key=None):
    used_keys = {s["category"] for s in CONTENT[locale]["stories"]}
    links = []
    for c in CATEGORIES:
        if c["key"] not in used_keys:
            continue
        cls = ' class="is-active"' if c["key"] == active_key else ""
        links.append(f'<a{cls} href="{root}{category_relpath(c["key"])}">{c["label"][locale]}</a>')
    return f'<div class="substrip"><div class="wrap substrip__row">{"".join(links)}</div></div>'


def footer_html(root, locale):
    site = CONTENT[locale]["site"]
    ui = site["ui"]
    social = site["social"]
    return f"""<footer class="site">
    <div class="wrap">
      <div class="footer__row">
        <div class="footer__mark">RAMA</div>
        <div class="footer__links">
          <a href="{social.get('instagram','#')}">INSTAGRAM</a>
          <a href="{social.get('tiktok','#')}">TIKTOK</a>
          <a href="{social.get('email','#')}">EMAIL</a>
          <a href="{root}about.html">{ui['aboutOf']}</a>
        </div>
      </div>
      <div class="footer__copy">&copy; 2026 {site['authorName']}. Reforming a Party Girl {"är" if locale == "sv" else "is"} {site['authorName']}{"s" if locale == "sv" else "'s"} {"personliga tidning." if locale == "sv" else "personal magazine."}</div>
    </div>
  </footer>"""


def card_html(story, root, ui, locale, feature=False):
    cls = "card card--feature" if feature else "card"
    arrow = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
    image = f'<img class="card__image card__image--{story["slug"]}" src="{root}assets/img/{story["image"]}" alt="">' if story.get("image") else ""
    return f"""<a class="{cls}" href="{root}stories/{story['slug']}/index.html">
        {image}
        <div class="card__row">
          <span class="card__cat">{category_label(locale, story['category'])}</span>
          <span class="card__dot">&middot;</span>
          <span class="card__meta">{story['readTime']}</span>
        </div>
        <h3 class="card__title">{story['title']}</h3>
        <p class="card__dek">{story['dek']}</p>
        <span class="card__cta">{ui['readStory']} {arrow}</span>
      </a>"""


def paragraphs_html(content):
    out = []
    for p in content:
        if p.startswith("> "):
            out.append(f"<blockquote>{p[2:]}</blockquote>")
        else:
            out.append(f"<p>{p}</p>")
    return "\n      ".join(out)


def person_jsonld(locale):
    site = CONTENT[locale]["site"]
    social = site["social"]
    same_as = [v for k, v in social.items() if v and v != "#" and not v.startswith("mailto:")]
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Person",
        "name": site["authorName"],
        "url": site["siteUrl"],
        "description": site["description"],
        "sameAs": same_as,
    })


def build_index(locale):
    site = CONTENT[locale]["site"]
    stories = CONTENT[locale]["stories"]
    ui = site["ui"]
    relpath = "index.html"
    root = root_prefix(locale, relpath)
    canonical = page_url(locale, relpath)
    title = f'{site["authorName"]} | {site["tagline"]} — {"Bekännelser, kaos och comeback" if locale == "sv" else "Confessions, Chaos & Coming Back"}'
    jsonld = f"""<script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "{site['siteName']}",
    "url": "{site['siteUrl']}",
    "inLanguage": "{locale}",
    "description": "{site['description']}",
    "author": {person_jsonld(locale)}
  }}
  </script>"""

    featured = [s for s in stories if s.get("featured")]
    rest = [s for s in stories if not s.get("featured")]
    cards = "\n      ".join(
        [card_html(s, root, ui, locale, feature=True) for s in featured] + [card_html(s, root, ui, locale) for s in rest]
    )
    html = f"""<!DOCTYPE html>
<html lang="{locale}">
<head>
  {head_html(title, site['description'], canonical, root, locale, relpath, jsonld)}
</head>
<body>
  {nav_html(root, locale, relpath)}
  {substrip_html(root, locale)}
  <main>
    <section class="hero wrap">
      <div class="hero__kicker">{site['heroKicker']}</div>
      <div class="hero__title-wrap">
        <h1>{site['authorName']}</h1>
      </div>
      <p class="hero__tagline">{site['tagline']}</p>
      <p class="hero__sub">{site['manifesto'][0]}</p>
    </section>

    <section class="wrap" id="stories">
      <div class="section-head">
        <h2>{ui['theStories']}</h2>
        <span>{len(stories)} {ui['published']}</span>
      </div>
      <div class="grid">
      {cards}
      </div>
    </section>
  </main>
  {footer_html(root, locale)}
</body>
</html>
"""
    write(os.path.join(ROOT, locale_prefix(locale), "index.html"), html)


def build_category(locale, category_key):
    site = CONTENT[locale]["site"]
    ui = site["ui"]
    label = category_label(locale, category_key)
    stories = [s for s in CONTENT[locale]["stories"] if s["category"] == category_key]
    relpath = category_relpath(category_key)
    root = root_prefix(locale, relpath)
    canonical = page_url(locale, relpath)
    title = f'{label} | {site["authorName"]} — {site["tagline"]}'
    description = f'{label} — {site["description"]}'
    jsonld = f"""<script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "{label}",
    "url": "{canonical}",
    "inLanguage": "{locale}",
    "author": {person_jsonld(locale)}
  }}
  </script>"""

    cards = "\n      ".join(card_html(s, root, ui, locale) for s in stories)
    html = f"""<!DOCTYPE html>
<html lang="{locale}">
<head>
  {head_html(title, description, canonical, root, locale, relpath, jsonld)}
</head>
<body>
  {nav_html(root, locale, relpath)}
  {substrip_html(root, locale, active_key=category_key)}
  <main>
    <section class="wrap" id="stories">
      <div class="section-head section-head--category">
        <h1>{label}</h1>
        <span>{len(stories)} {ui['published']}</span>
      </div>
      <div class="grid">
      {cards}
      </div>
      <a class="back-link" href="{root}index.html#stories">&larr; {ui['backToStories']}</a>
    </section>
  </main>
  {footer_html(root, locale)}
</body>
</html>
"""
    write(os.path.join(ROOT, locale_prefix(locale), "category", category_key, "index.html"), html)


def build_about(locale):
    site = CONTENT[locale]["site"]
    ui = site["ui"]
    relpath = "about.html"
    root = root_prefix(locale, relpath)
    canonical = page_url(locale, relpath)
    title = f'{ui["aboutOf"].title()} — {site["tagline"]}'
    description = site["description"]
    jsonld = f"""<script type="application/ld+json">
  {person_jsonld(locale)}
  </script>"""

    body_paras = "\n      ".join(f"<p>{p}</p>" for p in site["manifesto"])

    html = f"""<!DOCTYPE html>
<html lang="{locale}">
<head>
  {head_html(title, description, canonical, root, locale, relpath, jsonld)}
</head>
<body>
  {nav_html(root, locale, relpath)}
  {substrip_html(root, locale)}
  <main>
    <section class="wrap about">
      <h1>{ui['aboutOf']}</h1>
      <div class="about__body">
        {body_paras}
      </div>
    </section>
  </main>
  {footer_html(root, locale)}
</body>
</html>
"""
    write(os.path.join(ROOT, locale_prefix(locale), "about.html"), html)


def build_story(locale, story):
    site = CONTENT[locale]["site"]
    ui = site["ui"]
    slug = story["slug"]
    relpath = f"stories/{slug}/index.html"
    root = root_prefix(locale, relpath)
    canonical = page_url(locale, relpath)
    title = f'{story["title"]} | {site["authorName"]} — {site["tagline"]}'
    description = story["dek"]
    jsonld = f"""<script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{story['title']}",
    "description": "{story['dek']}",
    "datePublished": "{story['date']}",
    "inLanguage": "{locale}",
    "author": {person_jsonld(locale)}
  }}
  </script>"""

    initials = "".join(w[0] for w in site["authorName"].split()[:2]).upper()

    html = f"""<!DOCTYPE html>
<html lang="{locale}">
<head>
  {head_html(title, description, canonical, root, locale, relpath, jsonld)}
</head>
<body>
  {nav_html(root, locale, relpath)}
  <main>
    <article>
      <div class="wrap article-head">
        <div class="breadcrumb"><a href="{root}index.html">{ui['stories']}</a> &middot; <a href="{root}{category_relpath(story['category'])}">{category_label(locale, story['category'])}</a></div>
        <div class="card__row">
          <a class="card__cat" href="{root}{category_relpath(story['category'])}">{category_label(locale, story['category'])}</a>
          <span class="card__dot">&middot;</span>
          <span class="card__meta">{pretty_date(story['date'], locale)} &middot; {story['readTime']}</span>
        </div>
        <h1>{story['title']}</h1>
        <p class="dek">{story['dek']}</p>
        <div class="byline">
          <div class="byline__avatar">{initials}</div>
          <div class="byline__name">{site['authorName']}</div>
        </div>
      </div>
      {f'<div class="wrap"><img class="article-image article-image--' + story['slug'] + f'" src="{root}assets/img/' + story['image'] + f'" alt="{story["title"]}"></div>' if story.get('image') else ''}
      <div class="article-body">
      {paragraphs_html(story['content'])}
      </div>
      <div class="article-foot">
        <a class="back-link" href="{root}index.html#stories">&larr; {ui['backToStories']}</a>
      </div>
    </article>
  </main>
  {footer_html(root, locale)}
</body>
</html>
"""
    write(os.path.join(ROOT, locale_prefix(locale), "stories", slug, "index.html"), html)


MONTHS_SV = ["", "jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
MONTHS_EN = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def pretty_date(iso, locale):
    y, m, d = iso.split("-")
    if locale == "sv":
        return f"{int(d)} {MONTHS_SV[int(m)]} {y}"
    return f"{MONTHS_EN[int(m)]} {int(d)}, {y}"


def build_sitemap():
    urls = []
    for locale in LOCALES:
        urls.append(page_url(locale, "index.html"))
        urls.append(page_url(locale, "about.html"))
        for s in CONTENT[locale]["stories"]:
            urls.append(page_url(locale, f"stories/{s['slug']}/index.html"))
        for c in CATEGORIES:
            urls.append(page_url(locale, category_relpath(c["key"])))
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'
    write(os.path.join(ROOT, "sitemap.xml"), xml)


def build_robots():
    txt = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    write(os.path.join(ROOT, "robots.txt"), txt)


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    for locale in LOCALES:
        build_index(locale)
        build_about(locale)
        for s in CONTENT[locale]["stories"]:
            build_story(locale, s)
        for c in CATEGORIES:
            build_category(locale, c["key"])
    build_sitemap()
    build_robots()
    total = sum(len(CONTENT[l]["stories"]) for l in LOCALES)
    print(f"\nDone. {total} story pages built across {len(LOCALES)} locales.")

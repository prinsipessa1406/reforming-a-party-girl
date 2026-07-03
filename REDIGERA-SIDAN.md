# Så här redigerar du sidan själv

Du behöver inte kunna programmera. Du behöver bara:

1. **En textredigerare** — TextEdit (finns redan på din Mac) funkar, men [Visual Studio Code](https://code.visualstudio.com) (gratis) är mycket enklare eftersom den förstår filformatet och varnar om du råkar radera ett kommatecken.
2. **Terminal-appen** (finns redan på din Mac, sök på "Terminal" i Spotlight).

Efter ÄNDRING du gör, kör du alltid samma kommando i Terminal för att bygga om sidan:

```
cd ~/reforming-a-party-girl
python3 build.py
```

Det tar en sekund och skriver ut "Done. X story pages built..." när det är klart. Om du vill förhandsgranska innan du är nöjd, öppna `index.html` i mappen genom att dubbelklicka på den — den öppnas i webbläsaren.

---

## Ändra text som redan finns

All text bor i fyra filer:

- `content/sv/site.json` — namnet, taglinen, manifestot på svenska
- `content/sv/stories.json` — alla historier på svenska
- `content/en/site.json` — samma sak på engelska
- `content/en/stories.json` — alla historier på engelska

Öppna filen, hitta texten (den ligger mellan citattecken `" "`), ändra den, spara. Kör sen `python3 build.py`.

**Viktigt:** ändra bara texten INUTI citattecknen, rör inte kommatecken, citattecken eller klamrar `{ }` `[ ]` — de håller ihop filens struktur. Om du är osäker, fråga mig så kollar jag igenom innan du bygger om.

---

## Lägga till en ny historia

1. Öppna `content/sv/stories.json`.
2. Kopiera ett helt befintligt historia-block (allt mellan en `{` och matchande `}`).
3. Klistra in det som ett nytt block i listan (kom ihåg kommatecken mellan blocken).
4. Ändra:
   - `"slug"` — en unik kort URL-vänlig identifierare, t.ex. `"min-nya-historia"` (bara små bokstäver och bindestreck, inga mellanslag eller åäö)
   - `"category"` — måste vara en av de befintliga kategori-nycklarna: `manifesto`, `confessions`, `reckoning`, `patterns`, `astrology` (gemener, exakt så). Det är den rosa raden högst upp som filtrerar på den.
   - `"title"`, `"dek"`, `"date"`, `"readTime"`, `"content"` (en lista av stycken — en rad som börjar med `"> "` blir ett utdraget citat)
5. Gör exakt samma sak i `content/en/stories.json` med **samma `"slug"`** och **samma `"category"`-nyckel**, men engelsk text i övrigt, så hänger språkversionerna ihop.
6. Kör `python3 build.py`.

En ny sida skapas automatiskt på `stories/din-slug/` — inget annat behöver ändras.

### Lägga till en helt ny kategori

Öppna `build.py`, hitta listan `CATEGORIES` nära toppen, och lägg till en rad i samma format:

```
{"key": "min-nya-kategori", "label": {"sv": "SVENSK TEXT", "en": "ENGLISH TEXT"}},
```

Kör `python3 build.py` — en ny sida på `category/min-nya-kategori/` skapas automatiskt och dyker upp i den rosa raden.

---

## Byta eller lägga till en bild

1. Lägg bildfilen (jpg eller png) i mappen `assets/img/`.
2. I stories.json, lägg till (eller ändra) raden `"image": "filnamn.jpg",` i historian du vill koppla bilden till.
3. Kör `python3 build.py`.

Om en bild verkar felbeskuren (visar fel del av bilden), säg till mig vad som är fel så justerar jag beskärningen i `assets/css/style.css` — det är en detalj jag gärna hjälper till med.

---

## Ändra färger

Högst upp i `assets/css/style.css` finns en lista med färger, t.ex.:

```
--pink: #c9457c;
--ink: #18131c;
```

Byt ut hex-koden (t.ex. `#c9457c`) mot en annan, spara, kör `python3 build.py`. Samma färg används överallt den nämns, så en ändring uppdaterar hela sidan konsekvent.

---

## Vad du INTE behöver röra

Filen `build.py` är "motorn" som sätter ihop allt — den behöver du aldrig öppna för vanliga ändringar (text, bilder, färger). Om du vill ändra själva layouten (t.ex. flytta var saker står på sidan) är det bättre att fråga mig, eller en utvecklare, eftersom ett litet misstag där kan göra att hela sidan slutar bygga.

---

## Spara ändringar i Git / GitHub

Sidan ligger i ett Git-repo kopplat till `github.com/prinsipessa1406/reforming-a-party-girl`. Varje gång du gjort en ändring och kört `python3 build.py`, spara och skicka upp den så här i Terminal:

```
cd ~/reforming-a-party-girl
git add -A
git commit -m "kort beskrivning av vad du ändrade"
git push
```

Första gången du pushar på en ny dator kan Terminalen be dig logga in på GitHub (webbläsare öppnas, eller så ber den om användarnamn + ett Personal Access Token — inte ditt vanliga lösenord, skapa ett på [github.com/settings/tokens](https://github.com/settings/tokens) med "repo"-rutan ikryssad). Efter första gången kommer den ihåg det.

---

## Publicera sidan på riktigt (en egen webbadress)

Just nu syns sidan bara om man öppnar filerna lokalt eller tittar på GitHub-repot — inte som en riktig webbsida ännu. När du är redo att göra den synlig på internet finns två enkla vägar:

- **Netlify Drop** (netlify.com/drop) — dra hela mappen `reforming-a-party-girl` dit, ingen installation behövs, du får en länk på några sekunder.
- **Koppla GitHub-repot till Netlify eller Vercel** — då byggs sidan om automatiskt varje gång du pushar. Lite mer initial uppsättning, men smidigare i längden.

Säg till om du vill ha hjälp med endera, eller om du vill koppla ett eget domännamn (t.ex. ramabenkhalifa.com).

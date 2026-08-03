import json
import os
import requests
from io import BytesIO
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
PAGE_ID = os.environ["PAGE_ID"]

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf"
FONT_PATH = "Bangers-Regular.ttf"

# Heure locale (Madagascar, UTC+3) -> catégorie à publier
CALENDRIER = {
    8: "citations",
    10: "trivia",
    12: "citations",
    14: "folklore",
    16: "comparatif",
    18: "trivia",
    20: "portraits",
    22: "citations",
    0: "retrospectives",
    2: "folklore",
    4: "citations",
    6: "trivia",
}

PREFIXES = {
    "citations": "🔥📖",
    "trivia": "🧐✨",
    "folklore": "🌙👹",
    "comparatif": "⚖️📺",
    "portraits": "🖋️👤",
    "retrospectives": "⏳📚",
}


def categorie_actuelle():
    heure_locale = (datetime.now(timezone.utc) + timedelta(hours=3)).hour
    heure_creneau = min(CALENDRIER.keys(), key=lambda h: abs(h - heure_locale))
    return CALENDRIER[heure_creneau]


def charger_contenu(categorie):
    with open(f"contenu/{categorie}.json", "r", encoding="utf-8") as f:
        return json.load(f)


def charger_memoire():
    if os.path.exists("memoire_publications.json"):
        with open("memoire_publications.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def sauvegarder_memoire(memoire):
    with open("memoire_publications.json", "w", encoding="utf-8") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=2)


def choisir_entree(entrees, memoire, categorie):
    deja_utilisees = memoire.get(categorie, [])
    non_utilisees = [e for e in entrees if e["id"] not in deja_utilisees]
    if not non_utilisees:
        deja_utilisees = []
        non_utilisees = entrees
    memoire[categorie] = deja_utilisees
    return non_utilisees[0]


def recuperer_image_anilist(titre_manga):
    query = """
    query ($search: String) {
      Media(search: $search, type: MANGA) {
        coverImage { extraLarge }
      }
    }
    """
    reponse = requests.post(
        "https://graphql.anilist.co",
        json={"query": query, "variables": {"search": titre_manga}}
    )
    data = reponse.json()
    media = data.get("data", {}).get("Media")
    if media is None:
        return None
    return media["coverImage"]["extraLarge"]


def telecharger_police():
    if not os.path.exists(FONT_PATH):
        reponse = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(reponse.content)


def creer_image_stylee(image_url, titre_manga):
    telecharger_police()
    reponse = requests.get(image_url)
    image = Image.open(BytesIO(reponse.content)).convert("RGB")

    dessin = ImageDraw.Draw(image)
    taille_police = int(image.width / 10)
    police = ImageFont.truetype(FONT_PATH, taille_police)
    texte = titre_manga.upper()

    boite = dessin.textbbox((0, 0), texte, font=police)
    largeur_texte = boite[2] - boite[0]
    x = (image.width - largeur_texte) / 2
    y = image.height - taille_police * 1.8

    contour = 3
    for dx in range(-contour, contour + 1):
        for dy in range(-contour, contour + 1):
            dessin.text((x + dx, y + dy), texte, font=police, fill="black")
    dessin.text((x, y), texte, font=police, fill="white")

    sortie = BytesIO()
    image.save(sortie, format="JPEG")
    sortie.seek(0)
    return sortie


def styliser_titre(texte):
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    stylise = "𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅"
    table = str.maketrans(normal, stylise)
    return texte.translate(table)


def publier(categorie, entree):
    image_url = recuperer_image_anilist(entree["manga"])
    if image_url is None:
        print(f"Aucune image trouvée pour {entree['manga']}, publication annulée.")
        return {"error": "image non trouvee"}

    image_stylee = creer_image_stylee(image_url, entree["manga"])
    titre_stylise = styliser_titre(entree["manga"])
    prefixe = PREFIXES.get(categorie, "✨")

    legende = f"{prefixe} {titre_stylise}\n\n{entree['texte']}\n\n#{entree['manga'].replace(' ', '')} #manga #anime"

    url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"
    fichiers = {"source": ("image.jpg", image_stylee, "image/jpeg")}
    data = {"caption": legende, "access_token": PAGE_ACCESS_TOKEN}
    reponse = requests.post(url, data=data, files=fichiers)
    return reponse.json()


if __name__ == "__main__":
    categorie = categorie_actuelle()
    print(f"Catégorie choisie pour ce créneau : {categorie}")

    contenu = charger_contenu(categorie)
    memoire = charger_memoire()
    entree = choisir_entree(contenu, memoire, categorie)

    resultat = publier(categorie, entree)
    print("Résultat Facebook:", resultat)

    if "error" not in resultat:
        memoire.setdefault(categorie, []).append(entree["id"])
        sauvegarder_memoire(memoire)

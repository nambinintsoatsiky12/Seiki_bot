import json
import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
PAGE_ID = os.environ["PAGE_ID"]

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf"
FONT_PATH = "Bangers-Regular.ttf"


def charger_citations():
    with open("contenu/citations.json", "r", encoding="utf-8") as f:
        return json.load(f)


def charger_memoire():
    if os.path.exists("memoire_publications.json"):
        with open("memoire_publications.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {"citations_utilisees": []}


def sauvegarder_memoire(memoire):
    with open("memoire_publications.json", "w", encoding="utf-8") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=2)


def choisir_citation(citations, memoire):
    non_utilisees = [c for c in citations if c["id"] not in memoire["citations_utilisees"]]
    if not non_utilisees:
        memoire["citations_utilisees"] = []
        non_utilisees = citations
    return non_utilisees[0]


def recuperer_image_anilist(titre_manga):
    query = """
    query ($search: String) {
      Media(search: $search, type: MANGA) {
        coverImage {
          extraLarge
        }
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

    # Centrer le texte en bas de l'image, avec un contour noir pour la lisibilité
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


def publier_sur_facebook(citation):
    image_url = recuperer_image_anilist(citation["manga"])
    if image_url is None:
        print(f"Aucune image trouvée pour {citation['manga']}, publication annulée pour cette fois.")
        return {"error": "image non trouvee"}

    image_stylee = creer_image_stylee(image_url, citation["manga"])

    legende = f"🔥📖 {citation['texte']}\n\n⚔️ #{citation['manga'].replace(' ', '')} #manga #anime"

    url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"
    fichiers = {"source": ("image.jpg", image_stylee, "image/jpeg")}
    data = {
        "caption": legende,
        "access_token": PAGE_ACCESS_TOKEN
    }
    reponse = requests.post(url, data=data, files=fichiers)
    return reponse.json()


if __name__ == "__main__":
    citations = charger_citations()
    memoire = charger_memoire()
    citation = choisir_citation(citations, memoire)

    resultat = publier_sur_facebook(citation)
    print("Résultat Facebook:", resultat)

    if "error" not in resultat:
        memoire["citations_utilisees"].append(citation["id"])
        sauvegarder_memoire(memoire)

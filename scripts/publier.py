import json
import os
import random
import re
import requests
from io import BytesIO
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
PAGE_ID = os.environ["PAGE_ID"]

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf"
FONT_PATH = "Bangers-Regular.ttf"

CALENDRIER = {
    8: "citations", 10: "trivia", 12: "citations", 14: "folklore",
    16: "comparatif", 18: "trivia", 20: "portraits", 22: "citations",
    0: "retrospectives", 2: "folklore", 4: "citations", 6: "trivia",
}

PREFIXES = {
    "citations": "🔥📖", "trivia": "🧐✨", "folklore": "✴️🔥",
    "comparatif": "⚖️📺", "portraits": "🖋️👤", "retrospectives": "⏳📚",
}

ACCROCHES = [
    "🚨 ARRÊTE DE SCROLLER 🚨", "😱 ATTENDS VOIR ÇA 😱",
    "🔥 ÇA VA TE MARQUER 🔥", "👀 REGARDE ÇA DE PRÈS 👀", "⚡ ON EN PARLE ⚡",
]

EMOJIS_FIN = ["🔥", "😤", "💯", "🥷", "⚔️", "😭", "👑", "🎌"]

EMOJIS_PARAGRAPHE = ["💥", "😨", "🤯", "😮‍💨", "👊", "🩸", "⚡", "🖤"]

NORMAL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
ITALIQUE = "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫"
GRAS = "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"

TABLE_ITALIQUE = str.maketrans(NORMAL, ITALIQUE)
TABLE_GRAS = str.maketrans(NORMAL, GRAS)

TABLE_TITRE = str.maketrans(
    NORMAL,
    "𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅0123456789"
)

MOTS_A_IGNORER = {
    "cette", "avec", "pour", "dans", "leur", "leurs", "elle", "aussi",
    "mais", "plus", "être", "avoir", "tout", "tous", "toute", "toutes",
    "comme", "entre", "sans", "encore", "depuis", "avant", "après",
    "cette", "parce", "alors",
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
      Media(search: $search, type: MANGA, isAdult: false) {
        isAdult
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
    if media is None or media.get("isAdult"):
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
    return texte.translate(TABLE_TITRE)


def italiser(texte):
    return texte.translate(TABLE_ITALIQUE)


def mettre_en_gras(mot):
    return mot.translate(TABLE_GRAS)


def styliser_paragraphe(paragraphe):
    mots = paragraphe.split(" ")
    mots_candidats = [
        i for i, m in enumerate(mots)
        if len(re.sub(r"[^\wéèêàâçùûîï]", "", m)) >= 7
        and m.lower().strip(",.!?»«") not in MOTS_A_IGNORER
    ]
    nb_a_marquer = min(2, len(mots_candidats))
    a_marquer = set(random.sample(mots_candidats, nb_a_marquer)) if nb_a_marquer else set()

    resultat = []
    for i, mot in enumerate(mots):
        if i in a_marquer:
            propre = mot.strip(",.!?»«")
            resultat.append(f"#{mettre_en_gras(propre.upper())}")
        else:
            resultat.append(italiser(mot))

    emoji = random.choice(EMOJIS_PARAGRAPHE)
    return emoji + " " + " ".join(resultat)


def styliser_texte_complet(texte):
    paragraphes = texte.split("\n\n")
    return "\n\n".join(styliser_paragraphe(p) for p in paragraphes if p.strip())


def publier(categorie, entree):
    image_url = recuperer_image_anilist(entree["manga"])
    if image_url is None:
        print(f"Aucune image trouvée (ou contenu adulte détecté) pour {entree['manga']}, publication annulée.")
        return {"error": "image non trouvee ou contenu inapproprie"}

    image_stylee = creer_image_stylee(image_url, entree["manga"])
    titre_stylise = styliser_titre(entree["manga"])
    prefixe = PREFIXES.get(categorie, "✨")
    accroche = random.choice(ACCROCHES)
    emoji_fin = random.choice(EMOJIS_FIN)
    corps_stylise = styliser_texte_complet(entree["texte"])

    legende = (
        f"{accroche}\n\n"
        f"{prefixe} {titre_stylise}\n\n"
        f"{corps_stylise}\n\n"
        f"{emoji_fin} #{entree['manga'].replace(' ', '')} #manga #anime {emoji_fin}"
    )

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

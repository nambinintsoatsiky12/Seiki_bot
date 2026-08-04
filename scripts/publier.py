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
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf"
FONT_PATH = "Bangers-Regular.ttf"

CALENDRIER = {
    8: "citations", 10: "trivia", 12: "citations", 14: "folklore",
    16: "comparatif", 18: "trivia", 20: "portraits", 22: "citations",
    0: "retrospectives", 2: "folklore", 4: "citations", 6: "trivia",
}
PREFIXES = {
    "citations": "🔥📖", "trivia": "🧐✨", "folklore": "🌙👹",
    "comparatif": "⚖️📺", "portraits": "🖋️👤", "retrospectives": "⏳📚",
}
ANGLES = {
    "citations": "une citation marquante du manga, avec son contexte et pourquoi elle frappe",
    "trivia": "une anecdote peu connue sur ce manga ou son auteur",
    "folklore": "un lien entre ce manga et le folklore/les légendes japonaises",
    "comparatif": "une différence notable entre le manga et son adaptation anime",
    "portraits": "un fait marquant sur le mangaka qui a créé cette œuvre",
    "retrospectives": "un regard en arrière sur l'impact de ce manga dans le temps",
}
ACCROCHES = [
    "🚨 ARRÊTE DE SCROLLER 🚨",
    "😱 ATTENDS VOIR ÇA 😱",
    "🔥 ÇA VA TE MARQUER 🔥",
    "👀 REGARDE ÇA DE PRÈS 👀",
    "⚡ ON EN PARLE ⚡",
]
EMOJIS_FIN = ["🔥", "😤", "💯", "🥷", "⚔️", "😭", "👑", "🎌"]
EMOJIS_PARAGRAPHE = ["💥", "😨", "🤯", "😮‍💨", "👊", "🩸", "⚡", "🖤"]

NORMAL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
ITALIQUE = "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫"
GRAS = "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
ACCROCHE_STYLE = "𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕0123456789"
TITRE_STYLE = "𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅0123456789"

TABLE_ITALIQUE = str.maketrans(NORMAL, ITALIQUE)
TABLE_GRAS = str.maketrans(NORMAL, GRAS)
TABLE_ACCROCHE = str.maketrans(NORMAL, ACCROCHE_STYLE)
TABLE_TITRE = str.maketrans(NORMAL, TITRE_STYLE)

MOTS_A_IGNORER = {"cette","avec","pour","dans","leur","leurs","elle","aussi","mais","plus","être","avoir","tout","tous","toute","toutes","comme","entre","sans","encore","depuis","avant","après","parce","alors"}


def categorie_actuelle():
    h = (datetime.now(timezone.utc) + timedelta(hours=3)).hour
    return CALENDRIER[min(CALENDRIER.keys(), key=lambda x: abs(x - h))]


def charger_contenu(categorie):
    with open(f"contenu/{categorie}.json", "r", encoding="utf-8") as f:
        return json.load(f)


def charger_memoire():
    if os.path.exists("memoire_publications.json"):
        with open("memoire_publications.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def sauvegarder_memoire(m):
    with open("memoire_publications.json", "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def choisir_entree(entrees, memoire, categorie):
    utilisees = memoire.get(categorie, [])
    dispo = [e for e in entrees if e["id"] not in utilisees]
    if not dispo:
        utilisees = []
        dispo = entrees
    memoire[categorie] = utilisees
    return random.choice(dispo)


def generer_texte_gemini(manga, categorie, texte_secours):
    angle = ANGLES.get(categorie, "un fait intéressant sur ce manga")
    prompt = (
        f"Tu es le community manager d'une page Facebook manga/surnaturel appelée 'La piraterie'. "
        f"Écris un post Facebook de 3 à 5 courts paragraphes sur le manga '{manga}', autour de : {angle}. "
        f"Ton chaleureux, fan de manga, accessible. Termine par une question qui invite au commentaire. "
        f"Ne mets aucun emoji (ils seront ajoutés séparément). Pas de titre, juste le texte."
    )
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return texte_secours


def recuperer_image_anilist(titre_manga):
    query = """
    query ($search: String) {
      Media(search: $search, type: MANGA, isAdult: false) {
        isAdult
        coverImage { extraLarge }
      }
    }
    """
    r = requests.post("https://graphql.anilist.co", json={"query": query, "variables": {"search": titre_manga}})
    media = r.json().get("data", {}).get("Media")
    if media is None or media.get("isAdult"):
        return None
    return media["coverImage"]["extraLarge"]


def telecharger_police():
    if not os.path.exists(FONT_PATH):
        r = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)


def creer_image_stylee(image_url, titre_manga):
    telecharger_police()
    r = requests.get(image_url)
    image = Image.open(BytesIO(r.content)).convert("RGB")
    dessin = ImageDraw.Draw(image)
    taille = int(image.width / 10)
    police = ImageFont.truetype(FONT_PATH, taille)
    texte = titre_manga.upper()
    boite = dessin.textbbox((0, 0), texte, font=police)
    x = (image.width - (boite[2] - boite[0])) / 2
    y = image.height - taille * 1.8
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            dessin.text((x + dx, y + dy), texte, font=police, fill="black")
    dessin.text((x, y), texte, font=police, fill="white")
    sortie = BytesIO()
    image.save(sortie, format="JPEG")
    sortie.seek(0)
    return sortie


def styliser_paragraphe(p):
    mots = p.split(" ")
    candidats = [i for i, m in enumerate(mots) if len(re.sub(r"[^\wéèêàâçùûîï]", "", m)) >= 7 and m.lower().strip(",.!?»«") not in MOTS_A_IGNORER]
    marques = set(random.sample(candidats, min(2, len(candidats)))) if candidats else set()
    out = []
    for i, m in enumerate(mots):
        if i in marques:
            propre = m.strip(",.!?»«")
            out.append(f"#{propre.upper().translate(TABLE_GRAS)}")
        else:
            out.append(m.translate(TABLE_ITALIQUE))
    return random.choice(EMOJIS_PARAGRAPHE) + " " + " ".join(out)


def styliser_texte(texte):
    return "\n\n".join(styliser_paragraphe(p) for p in texte.split("\n\n") if p.strip())


def publier(categorie, entree):
    image_url = recuperer_image_anilist(entree["manga"])
    if image_url is None:
        print(f"Pas d'image valide pour {entree['manga']}, annulé.")
        return {"error": "image non trouvee"}

    texte_brut = generer_texte_gemini(entree["manga"], categorie, entree["texte"])
    corps = styliser_texte(texte_brut)
    image_stylee = creer_image_stylee(image_url, entree["manga"])
    titre = entree["manga"].upper().translate(TABLE_TITRE)
    accroche = random.choice(ACCROCHES).translate(TABLE_ACCROCHE)
    legende = f"{accroche}\n\n{PREFIXES.get(categorie,'✨')} {titre}\n\n{corps}\n\n{random.choice(EMOJIS_FIN)} #{entree['manga'].replace(' ','')} #manga #anime"

    r = requests.post(
        f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos",
        data={"caption": legende, "access_token": PAGE_ACCESS_TOKEN},
        files={"source": ("image.jpg", image_stylee, "image/jpeg")}
    )
    return r.json()


if __name__ == "__main__":
    categorie = categorie_actuelle()
    contenu = charger_contenu(categorie)
    memoire = charger_memoire()
    entree = choisir_entree(contenu, memoire, categorie)
    resultat = publier(categorie, entree)
    print("Résultat:", resultat)
    if "error" not in resultat:
        memoire.setdefault(categorie, []).append(entree["id"])
        sauvegarder_memoire(memoire)

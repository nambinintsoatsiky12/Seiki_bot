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

MANGAS_CELEBRES = [
    "One Piece", "Naruto", "Attack on Titan", "Demon Slayer", "Jujutsu Kaisen",
    "Death Note", "My Hero Academia", "Fullmetal Alchemist", "Dragon Ball",
    "Bleach", "Hunter x Hunter", "Tokyo Ghoul", "Chainsaw Man", "Spy x Family",
    "One Punch Man", "Black Clover", "Fairy Tail", "Sword Art Online",
    "Tokyo Revengers", "Vinland Saga", "Jojo's Bizarre Adventure",
    "Mob Psycho 100", "The Promised Neverland", "Haikyuu", "Blue Lock",
    "Solo Leveling", "Berserk", "Vagabond", "Slam Dunk", "Rurouni Kenshin",
]

SUJETS_FAITS = [
    "le cerveau humain", "le corps humain", "les animaux marins", "les insectes",
    "l'espace et l'univers", "les océans", "l'histoire ancienne", "la psychologie humaine",
    "les records animaliers", "le sommeil et les rêves", "la nature extrême", "le règne animal","À propos de Google",
]

CALENDRIER = {
    8: "citations", 10: "faits", 12: "citations", 14: "folklore",
    16: "comparatif", 18: "faits", 20: "portraits", 22: "citations",
    0: "retrospectives", 2: "faits", 4: "trivia", 6: "faits",
}
PREFIXES = {
    "citations": "🔥📖", "trivia": "🧐✨", "folklore": "🌙👹",
    "comparatif": "⚖️📺", "portraits": "🖋️👤", "retrospectives": "⏳📚",
    "faits": "🤯🌍",
}
ANGLES = {
    "citations": (
        "Commence OBLIGATOIREMENT par une réplique culte de l'anime entre guillemets français, "
        "sur sa propre ligne, suivie d'un saut de ligne. Ensuite explique le contexte et pourquoi "
        "cette phrase marque les fans."
    ),
    "trivia": (
        "Commence OBLIGATOIREMENT par '🔥Le saviez-vous ?🔥' suivi d'une anecdote peu connue "
        "sur cet anime, son studio, ou sa production."
    ),
    "folklore": (
        "Explique un lien concret entre cet anime et une légende, un yōkai, ou une croyance "
        "du folklore japonais traditionnel."
    ),
    "comparatif": (
        "Compare une scène ou un choix précis entre l'anime et son manga d'origine "
        "(si un manga existe), en expliquant ce qui change et pourquoi."
    ),
    "portraits": (
        "Commence OBLIGATOIREMENT par le nom du studio d'animation ou du réalisateur, "
        "puis raconte un fait marquant sur leur travail sur cet anime."
    ),
    "retrospectives": (
        "Commence OBLIGATOIREMENT par une phrase du type 'Retour sur...' et regarde en arrière "
        "sur l'impact ou l'héritage de cet anime dans le temps."
    ),
    "faits": (
        "Commence OBLIGATOIREMENT par 'Le savais-tu ?' suivi d'un fait vrai, vérifiable et "
        "fascinant sur ce sujet précis. Développe avec du contexte scientifique ou historique "
        "réel, en 3 à 5 paragraphes complets. Ne parle JAMAIS de personnes réelles identifiables, "
        "de violence, de torture, ou de théories non vérifiées — reste sur des faits factuels "
        "et positifs (science, nature, corps humain, histoire, espace)."
    ),
}
ACCROCHES = ["🚨 ARRÊTE DE SCROLLER 🚨", "😱 ATTENDS VOIR ÇA 😱", "🔥 ÇA VA TE MARQUER 🔥", "👀 REGARDE ÇA DE PRÈS 👀", "⚡ ON EN PARLE ⚡", "💎 PÉPITE MÉCONNUE 💎"]
EMOJIS_FIN = ["🔥", "😤", "💯", "🥷", "⚔️", "😭", "👑", "🎌"]
EMOJIS_PARAGRAPHE = ["💥", "😨", "🤯", "😮‍💨", "👊", "🩸", "⚡", "🖤"]

NORMAL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
ITALIQUE = "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫"
GRAS = "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
ACCROCHE_STYLE = "𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕0123456789"
TITRE_STYLE = "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"
TABLE_ITALIQUE = str.maketrans(NORMAL, ITALIQUE)
TABLE_GRAS = str.maketrans(NORMAL, GRAS)
TABLE_ACCROCHE = str.maketrans(NORMAL, ACCROCHE_STYLE)
TABLE_TITRE = str.maketrans(NORMAL, TITRE_STYLE)
MOTS_A_IGNORER = {"cette","avec","pour","dans","leur","leurs","elle","aussi","mais","plus","être","avoir","tout","tous","toute","toutes","comme","entre","sans","encore","depuis","avant","après","parce","alors"}


def categorie_actuelle():
    h = (datetime.now(timezone.utc) + timedelta(hours=3)).hour
    return CALENDRIER[min(CALENDRIER.keys(), key=lambda x: abs(x - h))]


def charger_memoire():
    if os.path.exists("memoire_publications.json"):
        with open("memoire_publications.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {"mangas_recents": [], "derniere_publication": None}


def sauvegarder_memoire(m):
    with open("memoire_publications.json", "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def piocher_manga(deja_utilises):
    if random.random() < 0.60:
        dispo = [m for m in MANGAS_CELEBRES if m not in deja_utilises]
        return random.choice(dispo) if dispo else random.choice(MANGAS_CELEBRES)

    if random.random() < 0.7:
        query = """
        query ($page: Int) { Page(page: $page, perPage: 30) {
          media(type: MANGA, sort: POPULARITY_DESC, isAdult: false) { title { romaji english } }
        }}"""
        variables = {"page": random.randint(6, 100)}
    else:
        query = """
        query { Page(page: 1, perPage: 30) {
          media(type: MANGA, sort: TRENDING_DESC, isAdult: false) { title { romaji english } }
        }}"""
        variables = {}

    resp = requests.post("https://graphql.anilist.co", json={"query": query, "variables": variables})
    resultats = resp.json().get("data", {}).get("Page", {}).get("media", [])
    noms = [(m["title"]["english"] or m["title"]["romaji"]) for m in resultats if m["title"]["romaji"] or m["title"]["english"]]
    noms_dispo = [n for n in noms if n not in deja_utilises]
    if not noms_dispo:
        return random.choice(MANGAS_CELEBRES)
    return random.choice(noms_dispo)


def piocher_image_pour_faits(sujet):
    requetes = {
        "le cerveau humain": "human brain anatomy",
        "le corps humain": "human anatomy",
        "les animaux marins": "marine animal ocean",
        "les insectes": "insect macro photography",
        "l'espace et l'univers": "galaxy nebula space",
        "les océans": "deep sea ocean",
        "l'histoire ancienne": "ancient artifact archaeology",
        "la psychologie humaine": "human mind brain",
        "les records animaliers": "wild animal",
        "le sommeil et les rêves": "night sky stars",
        "la nature extrême": "extreme nature landscape",
        "le règne animal": "wildlife animal",
    }
    terme = requetes.get(sujet, "nature")

    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{terme} filetype:bitmap",
        "gsrlimit": 15,
        "gsrnamespace": 6,
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": 1080,
        "format": "json",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        pages = r.json().get("query", {}).get("pages", {})
        candidats = []
        for page in pages.values():
            infos = page.get("imageinfo", [])
            if infos and infos[0].get("thumburl", "").lower().endswith((".jpg", ".jpeg", ".png")):
                candidats.append(infos[0]["thumburl"])
        if candidats:
            return random.choice(candidats)
    except Exception:
        pass

    return None


def generer_texte_gemini(sujet, categorie):
    consigne = ANGLES.get(categorie, "un fait intéressant")
    prompt = (
        f"Tu es le community manager d'une page Facebook manga/surnaturel appelée 'La piraterie'. "
        f"Écris un post Facebook de 3 à 5 courts paragraphes sur '{sujet}'. "
        f"CONSIGNE DE FORMAT STRICTE À RESPECTER : {consigne}\n"
        f"Si tu ne connais pas bien ce sujet précis, reste factuel et prudent, n'invente jamais de fausses infos. "
        f"Ton chaleureux, accessible. Termine par une question qui invite au commentaire. "
        f"Ne mets aucun emoji (ils seront ajoutés séparément). Pas de titre, juste le texte."
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
    data = r.json()
    if "candidates" not in data:
        print("Réponse brute Gemini (échec):", data)
        return (
            f"Découvrez ou redécouvrez {sujet}, un sujet qui mérite clairement le détour. "
            f"Une pépite à suivre de près.\n\n"
            f"Et vous, vous connaissiez déjà ça ? Dites-le en commentaire !"
        )
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


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


def creer_image_stylee(image_url, titre):
    telecharger_police()
    r = requests.get(image_url)
    image = Image.open(BytesIO(r.content)).convert("RGB")

    largeur_cible = 1080
    if image.width < largeur_cible:
        ratio = largeur_cible / image.width
        nouvelle_taille = (largeur_cible, int(image.height * ratio))
        image = image.resize(nouvelle_taille, Image.LANCZOS)

    dessin = ImageDraw.Draw(image)
    taille = int(image.width / 10)
    police = ImageFont.truetype(FONT_PATH, taille)
    texte = titre.upper()
    boite = dessin.textbbox((0, 0), texte, font=police)
    x = (image.width - (boite[2] - boite[0])) / 2
    y = image.height - taille * 1.8
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            dessin.text((x + dx, y + dy), texte, font=police, fill="black")
    dessin.text((x, y), texte, font=police, fill="white")
    sortie = BytesIO()
    image.save(sortie, format="JPEG", quality=95)
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


def publier(categorie, sujet):
    if categorie == "faits":
        image_url = piocher_image_pour_faits(sujet)
        titre_affiche = sujet.capitalize()
        if image_url is None:
            return {"error": "image non trouvee"}
    else:
        image_url = recuperer_image_anilist(sujet)
        titre_affiche = sujet
        if image_url is None:
            return {"error": "image non trouvee"}

    image_stylee = creer_image_stylee(image_url, titre_affiche)
    texte_brut = generer_texte_gemini(sujet, categorie)
    corps = styliser_texte(texte_brut)
    titre = titre_affiche.upper().translate(TABLE_TITRE)
    accroche = random.choice(ACCROCHES).translate(TABLE_ACCROCHE)
    hashtag_sujet = titre_affiche.replace(" ", "").replace("'", "")
    legende = f"{accroche}\n\n{PREFIXES.get(categorie,'✨')} {titre}\n\n{corps}\n\n{random.choice(EMOJIS_FIN)} #{hashtag_sujet} #manga #anime"

    r = requests.post(
        f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos",
        data={"caption": legende, "access_token": PAGE_ACCESS_TOKEN},
        files={"source": ("image.jpg", image_stylee, "image/jpeg")}
    )
    return r.json()


if __name__ == "__main__":
    memoire = charger_memoire()
    categorie = categorie_actuelle()
    deja_utilises = memoire.get("mangas_recents", [])
    sujet_retenu = None
    resultat = {"error": "aucune tentative"}

    for _ in range(4):
        if categorie == "faits":
            dispo = [s for s in SUJETS_FAITS if s not in deja_utilises] or SUJETS_FAITS
            candidat = random.choice(dispo)
        else:
            candidat = piocher_manga(deja_utilises)

        if candidat is None:
            continue
        resultat = publier(categorie, candidat)
        if "error" not in resultat:
            sujet_retenu = candidat
            break
        print(f"Échec pour {candidat} ({resultat.get('error')}), nouvel essai...")

    print(f"Catégorie : {categorie} | Sujet retenu : {sujet_retenu}")
    print("Résultat:", resultat)

    if sujet_retenu and "error" not in resultat:
        deja_utilises.append(sujet_retenu)
        memoire["mangas_recents"] = deja_utilises[-150:]
        memoire["derniere_publication"] = datetime.now(timezone.utc).isoformat()
        sauvegarder_memoire(memoire)

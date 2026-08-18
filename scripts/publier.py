import json
import os
import random
import re
import requests
from io import BytesIO
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
import unicodedata

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
    "les records animaliers", "le sommeil et les rêves", "la nature extrême", "le règne animal",
    "les secrets de Google", "les coulisses du web",
]

# Nouvelles catégories
CATEGORIES_MANGA = ["citations", "trivia", "folklore", "comparatif", "portraits", "retrospectives"]
CATEGORIES_NON_MANGA = ["faits", "tristes", "chanceux"]

PREFIXES = {
    "citations": "🔥📖", "trivia": "🧐✨", "folklore": "🌙👹",
    "comparatif": "⚖️📺", "portraits": "🖋️👤", "retrospectives": "⏳📚",
    "faits": "🤯🌍", "tristes": "😢💔", "chanceux": "🍀✨"
}

ANGLES = {
    "citations": (
        "Commence OBLIGATOIREMENT par une réplique culte de l'anime entre guillemets français, "
        "sur sa propre ligne, suivie d'un saut de ligne. Ensuite explique le contexte et pourquoi "
        "cette phrase marque les fans."
    ),
    "trivia": (
        "Commence OBLIGATOIREMENT par 'Le saviez-vous ?' suivi d'une anecdote peu connue "
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
        "fascinant sur ce sujet précis. Développe avec du contexte scientifique, historique ou "
        "technologique réel, en 3 à 5 paragraphes complets. Ne parle JAMAIS de personnes réelles "
        "identifiables, de violence, ou de théories non vérifiées — reste sur des faits factuels "
        "et positifs (science, nature, corps humain, histoire, espace, web, technologie)."
    ),
    "tristes": (
        "Raconte une histoire vraie triste et marquante de l'histoire mondiale (par exemple un événement "
        "historique émouvant, une catastrophe naturelle, un destin tragique). Sois factuel, respectueux, "
        "sans détails graphiques. Termine par une réflexion ou une question qui invite au commentaire."
    ),
    "chanceux": (
        "Raconte une histoire vraie incroyable de chance ou de coïncidence (survivant miraculeux, gagnant "
        "de loterie improbable, sauvetage impossible). Reste factuel et cite des sources si possible. "
        "Termine par une question qui invite au commentaire."
    ),
}

ACCROCHES = ["🚨 ARRÊTE DE SCROLLER 🚨", "😱 ATTENDS VOIR ÇA 😱", "🔥 ÇA VA TE MARQUER 🔥", "👀 REGARDE ÇA DE PRÈS 👀", "⚡ ON EN PARLE ⚡", "💎 PÉPITE MÉCONNUE 💎"]
EMOJIS_FIN = ["🔥", "😤", "💯", "🥷", "⚔️", "😭", "👑", "🎌"]
EMOJIS_PARAGRAPHE = ["💥", "😨", "🤯", "😮‍💨", "👊", "🩸", "⚡", "🖤"]
EMOJIS_PARAGRAPHE_FAITS = ["✨", "🌍", "🔬", "🧠", "🌿", "📚", "💡", "🌐"]
# Emojis pour les nouvelles catégories
EMOJIS_PARAGRAPHE_TRISTES = ["😢", "💔", "🕊️", "🌧️", "🥀", "📜"]
EMOJIS_PARAGRAPHE_CHANCEUX = ["🍀", "✨", "🌟", "🙌", "💫", "🎉"]

NORMAL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
ITALIQUE = "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫"
GRAS = "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘺𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
ACCROCHE_STYLE = "𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕0123456789"
TITRE_STYLE = "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"
TABLE_ITALIQUE = str.maketrans(NORMAL, ITALIQUE)
TABLE_GRAS = str.maketrans(NORMAL, GRAS)
TABLE_ACCROCHE = str.maketrans(NORMAL, ACCROCHE_STYLE)
TABLE_TITRE = str.maketrans(NORMAL, TITRE_STYLE)
MOTS_A_IGNORER = {"cette","avec","pour","dans","leur","leurs","elle","aussi","mais","plus","être","avoir","tout","tous","toute","toutes","comme","entre","sans","encore","depuis","avant","après","parce","alors"}


def sans_accents(texte):
    """Enlève les accents pour éviter les problèmes de mapping."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texte)
        if unicodedata.category(c) != 'Mn'
    )


def charger_memoire():
    """Charge la mémoire en s'assurant que toutes les clés existent."""
    if os.path.exists("memoire_publications.json"):
        with open("memoire_publications.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    # Initialisation des champs par défaut
    data.setdefault("mangas_recents", [])
    data.setdefault("faits_recents", [])
    data.setdefault("tristes_recents", [])
    data.setdefault("chanceux_recents", [])
    data.setdefault("derniere_publication", None)
    data.setdefault("compteur_manga_jour", {"date": "", "count": 0})
    return data


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

    try:
        resp = requests.post("https://graphql.anilist.co", json={"query": query, "variables": variables}, timeout=15)
        resp.raise_for_status()
        resultats = resp.json().get("data", {}).get("Page", {}).get("media", [])
        noms = [(m["title"]["english"] or m["title"]["romaji"]) for m in resultats if m["title"]["romaji"] or m["title"]["english"]]
        noms_dispo = [n for n in noms if n not in deja_utilises]
        if not noms_dispo:
            return random.choice(MANGAS_CELEBRES)
        return random.choice(noms_dispo)
    except requests.exceptions.RequestException as e:
        print("Erreur réseau AniList (piocher_manga):", e)
        return random.choice(MANGAS_CELEBRES)


def piocher_image_pour_faits(sujet):
    """Recherche une image sur Wikimedia Commons pour les sujets factuels."""
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
        "les secrets de Google": "Google data center technology",
        "les coulisses du web": "internet infrastructure server room",
    }
    terme = requetes.get(sujet, "nature")

    headers = {
        "User-Agent": "LaPiraterieBot/1.0 (contact: ton-email@example.com)"
    }
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": terme,
        "gsrlimit": 20,
        "gsrnamespace": 6,
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": 1080,
        "format": "json",
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        candidats = []
        for page in pages.values():
            infos = page.get("imageinfo", [])
            if infos:
                image_url = infos[0].get("thumburl") or infos[0].get("url")
                if image_url and image_url.lower().endswith((".jpg", ".jpeg", ".png")):
                    candidats.append(image_url)
        if candidats:
            return random.choice(candidats)
        else:
            print(f"Aucune image trouvée pour {sujet} sur Wikimedia Commons.")
            return None
    except Exception as e:
        print(f"Erreur Wikimedia pour {sujet}: {e}")
        return None


def piocher_image_pour_histoires(categorie):
    """Recherche une image pour les catégories tristes/chanceux."""
    if categorie == "tristes":
        termes = ["sad historical event", "old shipwreck", "tragic monument"]
    else:  # chanceux
        termes = ["lucky clover", "lucky charm", "fortune"]
    headers = {
        "User-Agent": "LaPiraterieBot/1.0 (contact: ton-email@example.com)"
    }
    url = "https://commons.wikimedia.org/w/api.php"
    for terme in termes:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": terme,
            "gsrlimit": 10,
            "gsrnamespace": 6,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 1080,
            "format": "json",
        }
        try:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            candidats = []
            for page in pages.values():
                infos = page.get("imageinfo", [])
                if infos:
                    image_url = infos[0].get("thumburl") or infos[0].get("url")
                    if image_url and image_url.lower().endswith((".jpg", ".jpeg", ".png")):
                        candidats.append(image_url)
            if candidats:
                return random.choice(candidats)
        except Exception as e:
            print(f"Erreur Wikimedia pour {categorie} ({terme}): {e}")
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
    texte_secours = (
        f"Découvrez ou redécouvrez {sujet}, un sujet qui mérite clairement le détour. "
        f"Une pépite à suivre de près.\n\n"
        f"Et vous, vous connaissiez déjà ça ? Dites-le en commentaire !"
    )
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            print("Réponse Gemini inattendue :", data)
            return texte_secours
    except requests.exceptions.Timeout:
        print("Timeout Gemini")
        return texte_secours
    except requests.exceptions.RequestException as e:
        print(f"Erreur réseau Gemini : {e}")
        return texte_secours
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Erreur parsing Gemini : {e}")
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
    try:
        r = requests.post("https://graphql.anilist.co", json={"query": query, "variables": {"search": titre_manga}}, timeout=15)
        r.raise_for_status()
        media = r.json().get("data", {}).get("Media")
        if media is None or media.get("isAdult"):
            return None
        return media["coverImage"]["extraLarge"]
    except requests.exceptions.RequestException as e:
        print("Erreur réseau AniList (image):", e)
        return None


def telecharger_police():
    if not os.path.exists(FONT_PATH):
        try:
            r = requests.get(FONT_URL, timeout=15)
            r.raise_for_status()
            with open(FONT_PATH, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"Erreur téléchargement police : {e}")


def creer_image_stylee(image_url, titre):
    """Crée une image stylisée avec le titre. Si image_url est None, génère un fond dégradé."""
    telecharger_police()
    if image_url is None:
        largeur = 1080
        hauteur = 1080
        image = Image.new("RGB", (largeur, hauteur))
        pixels = image.load()
        for y in range(hauteur):
            for x in range(largeur):
                r = int(30 + (80 - 30) * (x / largeur))
                g = int(30 + (50 - 30) * (y / hauteur))
                b = int(60 + (120 - 60) * ((x + y) / (largeur + hauteur)))
                pixels[x, y] = (r, g, b)
    else:
        try:
            r = requests.get(image_url, timeout=15)
            r.raise_for_status()
            image = Image.open(BytesIO(r.content)).convert("RGB")
        except Exception as e:
            print(f"Erreur récupération image : {e}, utilisation fond par défaut")
            image = Image.new("RGB", (1080, 1080), color=(40, 40, 80))

    largeur_cible = 1080
    if image.width < largeur_cible:
        ratio = largeur_cible / image.width
        nouvelle_taille = (largeur_cible, int(image.height * ratio))
        image = image.resize(nouvelle_taille, Image.LANCZOS)

    dessin = ImageDraw.Draw(image)
    texte = titre.upper()
    texte_sans_accents = sans_accents(texte)
    taille = int(image.width / 8)
    police = None
    while taille > 20:
        try:
            police = ImageFont.truetype(FONT_PATH, taille)
        except:
            police = ImageFont.load_default()
            break
        bbox = dessin.textbbox((0, 0), texte_sans_accents, font=police)
        largeur_texte = bbox[2] - bbox[0]
        if largeur_texte <= image.width * 0.9:
            break
        taille -= 5

    bbox = dessin.textbbox((0, 0), texte_sans_accents, font=police)
    x = (image.width - (bbox[2] - bbox[0])) / 2
    y = image.height - taille * 2.0

    for dx in range(-3, 4):
        for dy in range(-3, 4):
            dessin.text((x + dx, y + dy), texte_sans_accents, font=police, fill="black")
    dessin.text((x, y), texte_sans_accents, font=police, fill="white")

    sortie = BytesIO()
    image.save(sortie, format="JPEG", quality=95)
    sortie.seek(0)
    return sortie


def styliser_paragraphe(p, categorie):
    mots = p.split(" ")
    candidats = [i for i, m in enumerate(mots) if len(re.sub(r"[^\wéèêàâçùûîï]", "", m)) >= 7 and m.lower().strip(",.!?»«") not in MOTS_A_IGNORER]
    marques = set(random.sample(candidats, min(2, len(candidats)))) if candidats else set()
    out = []
    for i, m in enumerate(mots):
        mot_sans_accents = sans_accents(m)
        if i in marques:
            propre = mot_sans_accents.strip(",.!?»«")
            out.append(f"#{propre.upper().translate(TABLE_GRAS)}")
        else:
            out.append(mot_sans_accents.translate(TABLE_ITALIQUE))
    # Choix de l'emoji selon la catégorie
    if categorie == "faits":
        emoji = random.choice(EMOJIS_PARAGRAPHE_FAITS)
    elif categorie == "tristes":
        emoji = random.choice(EMOJIS_PARAGRAPHE_TRISTES)
    elif categorie == "chanceux":
        emoji = random.choice(EMOJIS_PARAGRAPHE_CHANCEUX)
    else:
        emoji = random.choice(EMOJIS_PARAGRAPHE)
    return emoji + " " + " ".join(out)


def styliser_texte(texte, categorie):
    return "\n\n".join(styliser_paragraphe(p, categorie) for p in texte.split("\n\n") if p.strip())


def choisir_categorie(memoire):
    """Détermine la catégorie à publier selon l'heure et la limite quotidienne de mangas."""
    now = datetime.now(timezone.utc) + timedelta(hours=3)  # Heure de Paris
    heure = now.hour
    date_aujourdhui = now.strftime("%Y-%m-%d")

    # Initialiser le compteur manga du jour
    compteur = memoire.get("compteur_manga_jour", {"date": "", "count": 0})
    if compteur.get("date") != date_aujourdhui:
        compteur = {"date": date_aujourdhui, "count": 0}
        memoire["compteur_manga_jour"] = compteur

    # Définir une rotation horaire (mais on va d'abord vérifier la limite manga)
    # Ancienne logique : on choisit une catégorie selon l'heure
    # On la garde comme base, mais si c'est un manga et que le quota est atteint, on bascule
    if 6 <= heure < 10:
        categorie_base = "faits"
    elif 10 <= heure < 12:
        categorie_base = "citations"
    elif 12 <= heure < 14:
        categorie_base = "faits"
    elif 14 <= heure < 16:
        categorie_base = "folklore"
    elif 16 <= heure < 18:
        categorie_base = "comparatif"
    elif 18 <= heure < 20:
        categorie_base = "faits"
    elif 20 <= heure < 22:
        categorie_base = "portraits"
    elif 22 <= heure < 24:
        categorie_base = "citations"
    else:  # 0h - 6h
        categorie_base = "retrospectives"

    # Si la catégorie de base est un manga et que le quota est atteint, on choisit une non-manga
    if categorie_base in CATEGORIES_MANGA:
        if compteur["count"] >= 3:
            print(f"Quota manga atteint ({compteur['count']}/3), bascule vers catégorie non-manga.")
            # On choisit aléatoirement parmi les non-manga (on peut pondérer si besoin)
            categorie_choisie = random.choice(CATEGORIES_NON_MANGA)
        else:
            categorie_choisie = categorie_base
    else:
        categorie_choisie = categorie_base

    return categorie_choisie


def publier(categorie, sujet):
    """Prépare et publie le contenu sur Facebook."""
    if categorie == "faits":
        image_url = piocher_image_pour_faits(sujet)
        titre_affiche = sujet.capitalize()
    elif categorie in ["tristes", "chanceux"]:
        image_url = piocher_image_pour_histoires(categorie)
        titre_affiche = categorie.capitalize()  # ou un titre plus descriptif
    else:
        image_url = recuperer_image_anilist(sujet)
        titre_affiche = sujet
        if image_url is None:
            return {"error": "image non trouvee"}

    try:
        image_stylee = creer_image_stylee(image_url, titre_affiche)
    except Exception as e:
        print("Erreur création image:", e)
        return {"error": "creation image echouee"}

    texte_brut = generer_texte_gemini(sujet, categorie)
    corps = styliser_texte(texte_brut, categorie)
    titre = titre_affiche.upper().translate(TABLE_TITRE)
    accroche = random.choice(ACCROCHES).translate(TABLE_ACCROCHE)
    hashtag_sujet = titre_affiche.replace(" ", "").replace("'", "")
    legende = f"{accroche}\n\n{PREFIXES.get(categorie,'✨')} {titre}\n\n{corps}\n\n{random.choice(EMOJIS_FIN)} #{hashtag_sujet} #manga #anime"

    try:
        r = requests.post(
            f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos",
            data={"caption": legende, "access_token": PAGE_ACCESS_TOKEN},
            files={"source": ("image.jpg", image_stylee, "image/jpeg")},
            timeout=30
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print("Erreur réseau Facebook:", e)
        return {"error": "publication facebook echouee"}


if __name__ == "__main__":
    memoire = charger_memoire()
    categorie = choisir_categorie(memoire)

    # Sélection de la liste de sujets déjà utilisés selon la catégorie
    if categorie == "faits":
        deja_utilises = memoire.get("faits_recents", [])
    elif categorie == "tristes":
        deja_utilises = memoire.get("tristes_recents", [])
    elif categorie == "chanceux":
        deja_utilises = memoire.get("chanceux_recents", [])
    else:
        deja_utilises = memoire.get("mangas_recents", [])

    sujet_retenu = None
    resultat = {"error": "aucune tentative"}

    for _ in range(4):
        if categorie == "faits":
            dispo = [s for s in SUJETS_FAITS if s not in deja_utilises] or SUJETS_FAITS
            candidat = random.choice(dispo)
        elif categorie == "tristes":
            # Pas de liste prédéfinie, on demande à Gemini de choisir une histoire
            candidat = "une histoire vraie triste du monde"  # le sujet sera traité par Gemini
        elif categorie == "chanceux":
            candidat = "une histoire vraie de chance incroyable"
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
        # Mise à jour de la mémoire selon la catégorie
        if categorie == "faits":
            memoire.setdefault("faits_recents", []).append(sujet_retenu)
            memoire["faits_recents"] = memoire["faits_recents"][-150:]
        elif categorie == "tristes":
            memoire.setdefault("tristes_recents", []).append(sujet_retenu)
            memoire["tristes_recents"] = memoire["tristes_recents"][-150:]
        elif categorie == "chanceux":
            memoire.setdefault("chanceux_recents", []).append(sujet_retenu)
            memoire["chanceux_recents"] = memoire["chanceux_recents"][-150:]
        else:
            memoire.setdefault("mangas_recents", []).append(sujet_retenu)
            memoire["mangas_recents"] = memoire["mangas_recents"][-150:]
            # Incrémenter le compteur manga du jour
            compteur = memoire.get("compteur_manga_jour", {"date": "", "count": 0})
            today = (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%Y-%m-%d")
            if compteur.get("date") != today:
                compteur = {"date": today, "count": 0}
            compteur["count"] += 1
            memoire["compteur_manga_jour"] = compteur

        memoire["derniere_publication"] = datetime.now(timezone.utc).isoformat()
        sauvegarder_memoire(memoire)

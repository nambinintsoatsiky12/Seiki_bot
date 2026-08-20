import json
import os
import random
import re
import unicodedata
import requests
from io import BytesIO
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
PAGE_ID = os.environ["PAGE_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]

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

DOMAINES = [
    "anime_manga", "sciences", "espace", "corps_humain", "animaux",
    "histoire", "technologie", "cultures_du_monde", "archeologie",
    "phenomenes_naturels", "inventions", "exploration", "langues", "web",
]

ACCROCHES = ["🚨 ARRÊTE DE SCROLLER 🚨", "😱 ATTENDS VOIR ÇA 😱", "🔥 ÇA VA TE MARQUER 🔥", "👀 REGARDE ÇA DE PRÈS 👀", "⚡ ON EN PARLE ⚡", "💎 PÉPITE MÉCONNUE 💎"]
EMOJIS_FIN = ["🔥", "😤", "💯", "🥷", "⚔️", "😭", "👑", "🎌", "🌌"]
EMOJIS_PARAGRAPHE = ["💥", "😨", "🤯", "😮‍💨", "👊", "🩸", "⚡", "🖤", "✨", "🌍", "🔬", "💡"]

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


def sans_accents(texte):
    return ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')


def charger_memoire():
    if os.path.exists("memoire_publications.json"):
        with open("memoire_publications.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("sujets_recents", [])
            return data
    return {"sujets_recents": [], "derniere_publication": None}


def sauvegarder_memoire(m):
    with open("memoire_publications.json", "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def piocher_manga(deja_utilises):
    if random.random() < 0.6:
        dispo = [m for m in MANGAS_CELEBRES if m not in deja_utilises]
        return random.choice(dispo) if dispo else random.choice(MANGAS_CELEBRES)
    try:
        query = """
        query ($page: Int) { Page(page: $page, perPage: 30) {
          media(type: MANGA, sort: POPULARITY_DESC, isAdult: false) { title { romaji english } }
        }}"""
        resp = requests.post("https://graphql.anilist.co", json={"query": query, "variables": {"page": random.randint(6, 100)}}, timeout=15)
        resultats = resp.json().get("data", {}).get("Page", {}).get("media", [])
        noms = [(m["title"]["english"] or m["title"]["romaji"]) for m in resultats if m["title"]["romaji"] or m["title"]["english"]]
        dispo = [n for n in noms if n not in deja_utilises]
        return random.choice(dispo) if dispo else random.choice(MANGAS_CELEBRES)
    except requests.exceptions.RequestException as e:
        print("Erreur AniList (piocher_manga):", e)
        return random.choice(MANGAS_CELEBRES)


def recuperer_image_anilist(titre_manga):
    query = """
    query ($search: String) {
      Media(search: $search, type: MANGA, isAdult: false) { isAdult coverImage { extraLarge } }
    }"""
    try:
        r = requests.post("https://graphql.anilist.co", json={"query": query, "variables": {"search": titre_manga}}, timeout=15)
        media = r.json().get("data", {}).get("Media")
        if media is None or media.get("isAdult"):
            print(f"AniList : aucune image trouvée pour '{titre_manga}'")
            return None
        return media["coverImage"]["extraLarge"]
    except requests.exceptions.RequestException as e:
        print("Erreur AniList (image):", e)
        return None


def chercher_image_pexels(mot_cle):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": mot_cle, "per_page": 15, "orientation": "square"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        photos = r.json().get("photos", [])
        if not photos:
            print(f"Pexels : aucune image pour '{mot_cle}'")
            return None
        photo = random.choice(photos)
        return photo["src"]["large"]
    except requests.exceptions.RequestException as e:
        print("Erreur Pexels:", e)
        return None


def demander_sujet_et_texte_gemini(domaine, deja_utilises):
    consignes_domaine = {
        "sciences": "une découverte ou un fait scientifique réel et fascinant",
        "espace": "un fait vérifié sur l'espace, les étoiles, les planètes ou l'univers",
        "corps_humain": "un fait surprenant et vrai sur le corps humain ou le cerveau",
        "animaux": "un fait ou record incroyable mais vrai sur un animal précis",
        "histoire": "un événement historique réel et marquant (sans détails violents graphiques)",
        "technologie": "une info fascinante sur la technologie, l'IA, ou une invention",
        "cultures_du_monde": "une tradition ou coutume réelle et fascinante d'une culture du monde",
        "archeologie": "une découverte archéologique réelle et intrigante",
        "phenomenes_naturels": "un phénomène naturel extrême et réel (volcans, séismes, météo...)",
        "inventions": "l'histoire vraie d'une invention qui a changé le monde",
        "exploration": "un fait vrai sur une grande expédition ou exploration réelle",
        "langues": "un fait fascinant et vrai sur une langue ou l'origine d'un mot",
        "web": "un fait vrai et peu connu sur Internet, Google, ou les coulisses du web",
    }
    consigne = consignes_domaine.get(domaine, "un fait vrai et fascinant")
    eviter = ", ".join(deja_utilises[-20:]) if deja_utilises else "aucun"

    prompt = (
        f"Tu es le community manager de la page Facebook 'La piraterie — Omniverses', qui couvre absolument "
        f"tout ce qui est fascinant dans l'univers réel : sciences, histoire, culture, technologie, nature, mystères. "
        f"Choisis {consigne}. Évite ces sujets déjà utilisés récemment : {eviter}.\n\n"
        f"Réponds UNIQUEMENT en JSON valide, sans texte autour, avec ce format exact :\n"
        f'{{"sujet": "nom court du sujet en français (3-6 mots)", '
        f'"mot_cle_image": "UN SEUL mot-clé anglais simple et concret désignant un objet/lieu/être vivant photographiable (pas de mots abstraits ni de combinaisons bizarres)", '
        f'"texte": "le post Facebook complet en français, 3 à 5 paragraphes, qui commence par \'Le savais-tu ?\' '
        f'et se termine par une question qui invite au commentaire. Reste factuel, vérifié, jamais inventé. '
        f'Ne parle jamais de personnes réelles vivantes en détail, ni de violence, torture ou tragédies précises. '
        f'Pas d\'emoji dans le texte."}}'
    )
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
        r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        data = r.json()
        if "candidates" not in data:
            print("Réponse brute Gemini (échec):", data)
            return None
        brut = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        brut = re.sub(r"^```json\s*|\s*```$", "", brut.strip())
        resultat = json.loads(brut)
        if all(k in resultat for k in ("sujet", "mot_cle_image", "texte")):
            return resultat
        return None
    except requests.exceptions.RequestException as e:
        print("Erreur réseau Gemini:", e)
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print("Erreur parsing Gemini:", e)
        return None


def telecharger_police():
    if not os.path.exists(FONT_PATH):
        try:
            r = requests.get(FONT_URL, timeout=15)
            with open(FONT_PATH, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print("Erreur téléchargement police:", e)


def creer_image_stylee(image_url, titre):
    telecharger_police()
    r = requests.get(image_url, timeout=15)
    image = Image.open(BytesIO(r.content)).convert("RGB")

    largeur_cible = 1080
    if image.width < largeur_cible:
        ratio = largeur_cible / image.width
        image = image.resize((largeur_cible, int(image.height * ratio)), Image.LANCZOS)

    dessin = ImageDraw.Draw(image)
    texte = sans_accents(titre.upper())
    taille = int(image.width / 8)
    police = ImageFont.truetype(FONT_PATH, taille)
    while taille > 20:
        police = ImageFont.truetype(FONT_PATH, taille)
        boite = dessin.textbbox((0, 0), texte, font=police)
        if (boite[2] - boite[0]) <= image.width * 0.9:
            break
        taille -= 5

    boite = dessin.textbbox((0, 0), texte, font=police)
    x = (image.width - (boite[2] - boite[0])) / 2
    y = image.height - taille * 2.0
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
        m2 = sans_accents(m)
        if i in marques:
            out.append(f"#{m2.strip(',.!?»«').upper().translate(TABLE_GRAS)}")
        else:
            out.append(m2.translate(TABLE_ITALIQUE))
    return random.choice(EMOJIS_PARAGRAPHE) + " " + " ".join(out)


def styliser_texte(texte):
    return "\n\n".join(styliser_paragraphe(p) for p in texte.split("\n\n") if p.strip())


def publier_manga(deja_utilises):
    manga = piocher_manga(deja_utilises)
    image_url = recuperer_image_anilist(manga)
    if image_url is None:
        return manga, {"error": "image non trouvee"}

    prompt = (
        f"Tu es le community manager de la page Facebook 'La piraterie — Omniverses'. "
        f"Écris un post de 3 à 5 paragraphes sur l'anime/manga '{manga}' : commence par une réplique culte "
        f"entre guillemets français sur sa propre ligne, puis explique le contexte. Termine par une question. "
        f"Reste factuel si tu ne connais pas bien ce titre. Pas d'emoji dans le texte."
    )
    texte_secours = f"Découvrez ou redécouvrez {manga}, une œuvre qui mérite le détour.\n\nVous connaissez ? Dites-le en commentaire !"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
        r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        data = r.json()
        texte_brut = data["candidates"][0]["content"]["parts"][0]["text"].strip() if "candidates" in data else texte_secours
    except Exception as e:
        print("Erreur Gemini manga:", e)
        texte_brut = texte_secours

    return manga, finaliser_et_publier(manga, image_url, texte_brut)


def publier_fait(deja_utilises, domaine):
    resultat_gemini = demander_sujet_et_texte_gemini(domaine, deja_utilises)
    if resultat_gemini is None:
        return None, {"error": "gemini indisponible"}

    sujet = resultat_gemini["sujet"]
    if sujet in deja_utilises:
        return None, {"error": "sujet deja utilise"}

    image_url = chercher_image_pexels(resultat_gemini["mot_cle_image"])
    if image_url is None:
        image_url = chercher_image_pexels("nature landscape")
    if image_url is None:
        return None, {"error": "image non trouvee"}

    return sujet, finaliser_et_publier(sujet, image_url, resultat_gemini["texte"])


def finaliser_et_publier(titre_affiche, image_url, texte_brut):
    try:
        image_stylee = creer_image_stylee(image_url, titre_affiche)
    except Exception as e:
        print("Erreur création image:", e)
        return {"error": "creation image echouee"}

    corps = styliser_texte(texte_brut)
    titre = titre_affiche.upper().translate(TABLE_TITRE)
    accroche = random.choice(ACCROCHES).translate(TABLE_ACCROCHE)
    hashtag = re.sub(r"[^\w]", "", titre_affiche)
    legende = f"{accroche}\n\n🌌 OMNIVERSES 🌌\n\n{titre}\n\n{corps}\n\n{random.choice(EMOJIS_FIN)} #{hashtag} #omniverses #savaistu"

    try:
        r = requests.post(
            f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos",
            data={"caption": legende, "access_token": PAGE_ACCESS_TOKEN},
            files={"source": ("image.jpg", image_stylee, "image/jpeg")},
            timeout=30,
        )
        return r.json()
    except requests.exceptions.RequestException as e:
        print("Erreur réseau Facebook:", e)
        return {"error": "publication facebook echouee"}


if __name__ == "__main__":
    memoire = charger_memoire()
    deja_utilises = memoire.get("sujets_recents", [])

    sujet_retenu = None
    resultat = {"error": "aucune tentative"}

    for _ in range(4):
        domaine = random.choice(DOMAINES)
        print(f"Domaine tiré : {domaine}")
        if domaine == "anime_manga":
            candidat, resultat = publier_manga(deja_utilises)
        else:
            candidat, resultat = publier_fait(deja_utilises, domaine)

        if candidat and "error" not in resultat:
            sujet_retenu = candidat
            break
        print(f"Échec ({resultat.get('error')}), nouvel essai...")

    print(f"Sujet retenu : {sujet_retenu}")
    print("Résultat:", resultat)

    if sujet_retenu and "error" not in resultat:
        deja_utilises.append(sujet_retenu)
        memoire["sujets_recents"] = deja_utilises[-150:]
        memoire["derniere_publication"] = datetime.now(timezone.utc).isoformat()
        sauvegarder_memoire(memoire)

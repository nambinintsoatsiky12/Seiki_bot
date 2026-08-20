import json
import os
import random
import re
import subprocess
import time
import unicodedata
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS

PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
PAGE_ID = os.environ["PAGE_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf"
FONT_PATH = "Bangers-Regular.ttf"
NB_IMAGES = 5

MANGAS_CELEBRES = [
    "One Piece", "Naruto", "Attack on Titan", "Demon Slayer", "Jujutsu Kaisen",
    "Death Note", "My Hero Academia", "Fullmetal Alchemist", "Dragon Ball",
    "Bleach", "Hunter x Hunter", "Tokyo Ghoul", "Chainsaw Man", "Spy x Family",
]

DOMAINES_FAITS = [
    "sciences", "espace", "corps_humain", "animaux", "histoire", "technologie",
    "cultures_du_monde", "archeologie", "phenomenes_naturels", "inventions",
]

CONSIGNES_DOMAINE = {
    "sciences": "une découverte scientifique réelle et fascinante",
    "espace": "un fait vérifié sur l'espace ou l'univers",
    "corps_humain": "un fait surprenant et vrai sur le corps humain",
    "animaux": "un fait ou record incroyable mais vrai sur un animal",
    "histoire": "un événement historique réel et marquant",
    "technologie": "une info fascinante sur la technologie ou l'IA",
    "cultures_du_monde": "une tradition réelle et fascinante d'une culture du monde",
    "archeologie": "une découverte archéologique réelle et intrigante",
    "phenomenes_naturels": "un phénomène naturel extrême et réel",
    "inventions": "l'histoire vraie d'une invention qui a changé le monde",
}


def sans_accents(texte):
    return ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')


def choisir_sujet():
    if random.random() < 1 / 14:
        return "anime_manga", random.choice(MANGAS_CELEBRES)
    return random.choice(DOMAINES_FAITS), None


def recuperer_image_anilist(titre_manga):
    query = """
    query ($search: String) {
      Media(search: $search, type: MANGA, isAdult: false) { isAdult coverImage { extraLarge } }
    }"""
    try:
        r = requests.post("https://graphql.anilist.co", json={"query": query, "variables": {"search": titre_manga}}, timeout=15)
        media = r.json().get("data", {}).get("Media")
        if media is None or media.get("isAdult"):
            return None
        return media["coverImage"]["extraLarge"]
    except requests.exceptions.RequestException as e:
        print("Erreur AniList:", e)
        return None


def chercher_images_pexels(mot_cle, nombre):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": mot_cle, "per_page": 20, "orientation": "portrait"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        photos = r.json().get("photos", [])
        random.shuffle(photos)
        return [p["src"]["portrait"] for p in photos[:nombre]]
    except requests.exceptions.RequestException as e:
        print("Erreur Pexels:", e)
        return []


def demander_contenu_gemini(domaine):
    consigne = CONSIGNES_DOMAINE.get(domaine, "un fait vrai et fascinant")
    prompt = (
        f"Tu es le community manager de 'La piraterie — Omniverses'. Choisis {consigne}.\n"
        f"Réponds UNIQUEMENT en JSON valide, sans texte autour :\n"
        f'{{"sujet": "nom court en français (3-6 mots)", '
        f'"mot_cle_image": "UN SEUL mot-clé anglais simple et concret photographiable", '
        f'"narration": "un texte de narration en français, environ 100 à 130 mots, dynamique et captivant, '
        f'à lire à voix haute pour un Reel vidéo, qui explique ce fait de façon claire et termine par une phrase '
        f'd\'accroche du type invite à suivre la page ou à commenter"}}'
    )
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
        r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        data = r.json()
        if "candidates" not in data:
            print("Réponse brute Gemini (échec):", data)
            return None
        brut = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        brut = re.sub(r"^```json\s*|\s*```$", "", brut)
        resultat = json.loads(brut)
        if all(k in resultat for k in ("sujet", "mot_cle_image", "narration")):
            return resultat
        return None
    except Exception as e:
        print("Erreur Gemini:", e)
        return None


def telecharger_police():
    if not os.path.exists(FONT_PATH):
        r = requests.get(FONT_URL, timeout=15)
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)


def preparer_frame(image_url, index, titre=None):
    telecharger_police()
    r = requests.get(image_url, timeout=15)
    image = Image.open(BytesIO(r.content)).convert("RGB")

    cible_w, cible_h = 1080, 1920
    ratio = max(cible_w / image.width, cible_h / image.height)
    image = image.resize((int(image.width * ratio), int(image.height * ratio)))
    gauche = (image.width - cible_w) / 2
    haut = (image.height - cible_h) / 2
    image = image.crop((gauche, haut, gauche + cible_w, haut + cible_h))

    if titre:
        dessin = ImageDraw.Draw(image)
        texte = sans_accents(titre.upper())
        taille = 90
        police = ImageFont.truetype(FONT_PATH, taille)
        while taille > 30:
            police = ImageFont.truetype(FONT_PATH, taille)
            boite = dessin.textbbox((0, 0), texte, font=police)
            if (boite[2] - boite[0]) <= cible_w * 0.9:
                break
            taille -= 5
        boite = dessin.textbbox((0, 0), texte, font=police)
        x = (cible_w - (boite[2] - boite[0])) / 2
        y = cible_h - 300
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                dessin.text((x + dx, y + dy), texte, font=police, fill="black")
        dessin.text((x, y), texte, font=police, fill="white")

    chemin = f"frame_{index}.jpg"
    image.save(chemin, quality=95)
    return chemin


def creer_narration_audio(texte):
    tts = gTTS(text=texte, lang="fr")
    tts.save("narration.mp3")
    resultat = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "narration.mp3"],
        capture_output=True, text=True
    )
    try:
        return float(resultat.stdout.strip())
    except ValueError:
        return 20.0


def creer_video(chemins_images, duree_totale):
    duree_par_image = max(duree_totale / len(chemins_images), 2.0)
    with open("liste_images.txt", "w") as f:
        for chemin in chemins_images:
            f.write(f"file '{chemin}'\nduration {duree_par_image}\n")
        f.write(f"file '{chemins_images[-1]}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "liste_images.txt",
        "-i", "narration.mp3", "-vf", "scale=1080:1920,format=yuv420p",
        "-r", "25", "-c:v", "libx264", "-c:a", "aac", "-shortest",
        "-movflags", "+faststart", "reel.mp4"
    ], check=True, capture_output=True, text=True)


def publier_reel(legende):
    r = requests.post(
        f"https://graph.facebook.com/v21.0/{PAGE_ID}/video_reels",
        data={"upload_phase": "start", "access_token": PAGE_ACCESS_TOKEN}, timeout=30
    )
    depart = r.json()
    print("Résultat démarrage upload:", depart)
    if "video_id" not in depart or "upload_url" not in depart:
        return {"error": "echec demarrage upload", "detail": depart}

    video_id, upload_url = depart["video_id"], depart["upload_url"]
    with open("reel.mp4", "rb") as f:
        contenu = f.read()
    print(f"Taille vidéo : {len(contenu)} octets")

    r2 = requests.post(
        upload_url, headers={"Authorization": f"OAuth {PAGE_ACCESS_TOKEN}", "file_offset": "0"},
        data=contenu, timeout=90
    )
    print("Résultat upload binaire:", r2.status_code, r2.text[:500])

    etat_final = None
    for _ in range(15):
        time.sleep(5)
        statut = requests.get(
            f"https://graph.facebook.com/v21.0/{video_id}",
            params={"fields": "status", "access_token": PAGE_ACCESS_TOKEN}, timeout=15
        ).json()
        etat_final = statut.get("status", {}).get("video_status")
        print("Statut vidéo:", statut)
        if etat_final == "ready":
            break

    if etat_final != "ready":
        return {"error": "video jamais prete", "dernier_statut": etat_final}

    r3 = requests.post(
        f"https://graph.facebook.com/v21.0/{PAGE_ID}/video_reels",
        data={"upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED",
              "description": legende, "access_token": PAGE_ACCESS_TOKEN}, timeout=30
    )
    resultat_final = r3.json()
    print("Résultat publication finale:", resultat_final)
    return resultat_final


if __name__ == "__main__":
    domaine, manga_direct = choisir_sujet()
    print(f"Domaine choisi : {domaine}")

    if domaine == "anime_manga":
        titre = manga_direct
        image_url = recuperer_image_anilist(titre)
        images_urls = [image_url] * NB_IMAGES if image_url else []
        narration = f"On parle de {titre} aujourd'hui, une œuvre incontournable de l'univers manga et anime. Suivez la page pour découvrir encore plus de contenu sur cet univers passionnant !"
        legende = f"🔥 {titre} — vous en pensez quoi ? 👇"
    else:
        infos = demander_contenu_gemini(domaine)
        if infos is None:
            print("Gemini indisponible, arrêt.")
            exit()
        titre = infos["sujet"]
        images_urls = chercher_images_pexels(infos["mot_cle_image"], NB_IMAGES)
        narration = infos["narration"]
        legende = f"🌌 {titre} — le saviez-vous ? Dites-le en commentaire 👇"

    if not images_urls:
        print("Aucune image trouvée, Reel annulé.")
    else:
        try:
            duree = creer_narration_audio(narration)
            chemins = [preparer_frame(u, i, titre if i == 0 else None) for i, u in enumerate(images_urls)]
            creer_video(chemins, duree)
            resultat = publier_reel(legende)
            print("Résultat final:", resultat)
        except subprocess.CalledProcessError as e:
            print("Erreur ffmpeg:", e.stderr[-2000:] if e.stderr else str(e))
        except Exception as e:
            print("Erreur inattendue:", e)

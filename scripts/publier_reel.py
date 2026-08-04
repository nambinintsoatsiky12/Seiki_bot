import json
import os
import random
import subprocess
import time
from datetime import date
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont

PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
PAGE_ID = os.environ["PAGE_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf"
FONT_PATH = "Bangers-Regular.ttf"


def manga_de_la_semaine():
    with open("contenu/rotation_reels.json", "r", encoding="utf-8") as f:
        liste = json.load(f)
    semaine = date.today().isocalendar()[1]
    return liste[semaine % len(liste)]


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


def creer_image_verticale(image_url, manga):
    telecharger_police()
    r = requests.get(image_url)
    image = Image.open(BytesIO(r.content)).convert("RGB")

    cible_w, cible_h = 1080, 1920
    ratio = max(cible_w / image.width, cible_h / image.height)
    nouvelle_taille = (int(image.width * ratio), int(image.height * ratio))
    image = image.resize(nouvelle_taille)
    gauche = (image.width - cible_w) / 2
    haut = (image.height - cible_h) / 2
    image = image.crop((gauche, haut, gauche + cible_w, haut + cible_h))

    dessin = ImageDraw.Draw(image)
    police = ImageFont.truetype(FONT_PATH, 90)
    texte = manga.upper()
    boite = dessin.textbbox((0, 0), texte, font=police)
    x = (cible_w - (boite[2] - boite[0])) / 2
    y = cible_h - 300
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            dessin.text((x + dx, y + dy), texte, font=police, fill="black")
    dessin.text((x, y), texte, font=police, fill="white")

    image.save("frame.jpg", quality=95)


def generer_texte_reel(manga):
    prompt = (
        f"Tu es le community manager d'une page Facebook manga/surnaturel. "
        f"Écris une légende COURTE et percutante (2-3 phrases max) pour un Reel vidéo mettant en avant le manga '{manga}'. "
        f"Ton fan, énergique. Termine par une question courte. Ajoute 2-3 emojis pertinents. Pas de hashtags."
    )
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return f"On parle de {manga} aujourd'hui 🔥 Vous en pensez quoi ? 👇"

def creer_video():
    commande = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", "frame.jpg",
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0015,1.15)':d=200:s=1080x1920:fps=25",
        "-t", "8",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        "-movflags", "+faststart",
        "reel.mp4"
    ]
    subprocess.run(commande, check=True)

def publier_reel(manga, legende):
    taille = os.path.getsize("reel.mp4")
    
    # 1. Start (Initialisation)
    r = requests.post(
        f"https://graph.facebook.com/v21.0/{PAGE_ID}/video_reels",
        data={"upload_phase": "start", "access_token": PAGE_ACCESS_TOKEN}
    )
    depart = r.json()
    video_id = depart.get("video_id")
    upload_url = depart.get("upload_url")
    
    if not video_id or not upload_url:
        print("Erreur initialisation Facebook:", depart)
        return depart

    # 2. Upload de la vidéo
    taille = os.path.getsize("reel.mp4")
    
    with open("reel.mp4", "rb") as f:
        contenu = f.read()
        
    r2 = requests.post(
        upload_url,
        headers={
            "Authorization": f"OAuth {PAGE_ACCESS_TOKEN}",
            "offset": "0",
            "file_size": str(taille)
        },
        data=contenu
    )
    print("Résultat upload:", r2.json())
    # Pause de 15 secondes pour laisser le temps à Meta de traiter le fichier
    print("Attente du traitement vidéo par Meta...")
    time.sleep(15)
    
# 3. Finish (Publication)
    r3 = requests.post(
        f"https://graph.facebook.com/v21.0/{PAGE_ID}/video_reels",
        params={"access_token": PAGE_ACCESS_TOKEN},
        data={
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "published": "true",
            "description": legende
        }
    )
    
    reponse = r3.json()
    print("REPONSE DE META :", reponse) # <-- Regarde cette ligne dans les logs !
    
    if "error" in reponse:
        raise Exception(f"Meta a refusé le Reel : {reponse['error']}")
        
    return reponse
if __name__ == "__main__":
    manga = manga_de_la_semaine()
    print("Manga de la semaine :", manga)

    image_url = recuperer_image_anilist(manga)
    if image_url is None:
        print("Image introuvable, Reel annulé.")
    else:
        creer_image_verticale(image_url, manga)
        creer_video()
        legende = generer_texte_reel(manga)
        resultat = publier_reel(manga, legende)
        print("Résultat final:", resultat)

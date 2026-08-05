import os
import random
import subprocess
from gTTS import gTTS
from PIL import Image, ImageDraw, ImageFont

# --- BASE DE DONNÉES DES HISTOIRES (Format 50 secondes) ---
MANGAS = [
    {
        "titre": "ONE PIECE",
        "histoire": (
            "Gol D. Roger, le Roi des Pirates, a exécuté le plus grand coup de l'histoire en léguant son trésor ultime, "
            "le One Piece, à quiconque le trouvera. Vingt ans plus tard, Monkey D. Luffy, un jeune homme au corps d'élastique "
            "ayant mangé le fruit du démon, prend la mer à bord d'une barque. Son objectif est simple mais monumental : "
            "rassembler un équipage légendaire, traverser la ligne de Grand Line et devenir le nouveau Roi des Pirates !"
        ),
        "couleur_fond": "#0f2027"
    },
    {
        "titre": "SOLO LEVELING",
        "histoire": (
            "Dans un monde menacé par des monstres issus de portes interdimensionnelles, Sung Jinwoo est connu comme le chasseur "
            "le plus faible de toute l'humanité. Incapable de financer les soins de sa mère, il continue de risquer sa vie dans des donjons. "
            "Mais lors d'une mission de routine qui tourne au massacre dans un donjon double, Jinwoo frôle la mort et débloque "
            "un système d'interface secret qui fait de lui le seul joueur capable de monter de niveau sans aucune limite."
        ),
        "couleur_fond": "#141e30"
    },
    {
        "titre": "NARUTO",
        "histoire": (
            "Orphelin rejeté et craint par tout le village de Konoha à cause du démon renard à neuf queues scellé en lui, "
            "Naruto Uzumaki a grandi dans la solitude absolue. Mais au lieu de sombrer dans la haine, il s'est fixé le défi "
            "le plus ambitieux de sa vie : devenir le Hokage, le leader ultime de son village, afin de forcer tout le monde "
            "à reconnaître enfin sa véritable valeur."
        ),
        "couleur_fond": "#45a247"
    }
]

def creer_video():
    manga = random.choice(MANGAS)
    print(f"Création de l'histoire pour : {manga['titre']}")

    # 1. Génération de l'audio long (Voix IA en français)
    audio_file = "voix.mp3"
    tts = gTTS(text=manga["histoire"], lang='fr', slow=False)
    tts.save(audio_file)

    # 2. Obtenir la durée exacte de l'audio avec ffprobe
    cmd_duration = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_file
    ]
    duration = float(subprocess.check_output(cmd_duration).decode('utf-8').strip())
    print(f"Durée de l'histoire : {duration:.1f} secondes")

    # 3. Génération des images du diaporama
    image_files = []
    textes = [manga['titre'], "L'HISTOIRE", "LE DESTIN", "ABONNE-TOI !"]
    
    for i, txt in enumerate(textes):
        img = Image.new('RGB', (1080, 1920), color=manga['couleur_fond'])
        draw = ImageDraw.Draw(img)
        draw.text((540, 960), txt, fill="white", anchor="mm")
        
        filename = f"frame_{i}.png"
        img.save(filename)
        image_files.append(filename)

    # Calcul du temps par image pour couvrir toute la durée de la voix
    time_per_img = duration / len(textes)

    # 4. Assemblage FFmpeg (Vidéo 9:16 + Voix IA synchronisée)
    cmd_ffmpeg = [
        "ffmpeg", "-y",
        "-framerate", f"1/{time_per_img}",
        "-i", "frame_%d.png",
        "-i", audio_file,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        "reel.mp4"
    ]
    
    print("Assemblage du Reel en cours...")
    subprocess.run(cmd_ffmpeg, check=True)

    # Nettoyage
    os.remove(audio_file)
    for f in image_files:
        os.remove(f)

if __name__ == "__main__":
    creer_video()

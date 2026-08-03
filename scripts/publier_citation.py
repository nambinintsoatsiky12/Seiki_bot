import json
import os
import requests

PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
PAGE_ID = os.environ["PAGE_ID"]

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
    
def publier_sur_facebook(citation):
    image_url = recuperer_image_anilist(citation["manga"])
    if image_url is None:
        print(f"Aucune image trouvée pour {citation['manga']}, publication annulée pour cette fois.")
        return {"error": "image non trouvee"}

    url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"
    data = {
        "url": image_url,
        "caption": citation["texte"],
        "access_token": PAGE_ACCESS_TOKEN
    }
    reponse = requests.post(url, data=data)
    return reponse.json()
    
if __name__ == "__main__":
    citations = charger_citations()
    memoire = charger_memoire()
    citation = choisir_citation(citations, memoire)

    resultat = publier_sur_facebook(citation)
    print("Résultat Facebook:", resultat)

    memoire["citations_utilisees"].append(citation["id"])
    sauvegarder_memoire(memoire)

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer les credentials depuis les variables d'environnement
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Initialisation du client Supabase
supabase: Client = create_client(url, key)

# Récupérer les données de la table articles où is_recommandation est True, en sélectionnant uniquement le lien
response = supabase.table("articles").select("link").eq("is_recommandation", True).execute()

# Afficher la réponse pour vérification
print("Réponse de Supabase :", response.data)

# Lire le contenu existant du fichier pour éviter les doublons
existing_values = set()
try:
    with open("links.txt", "r") as file:
        existing_values = set(line.strip() for line in file if line.strip())
except FileNotFoundError:
    pass  # Si le fichier n'existe pas, on commence avec un ensemble vide

# Écrire dans le fichier en mode ajout
with open("links.txt", "a") as file:
    for item in response.data:
        link = item.get("link")
        if link and link not in existing_values:
            file.write(f"{link}\n")
            existing_values.add(link)

print("Les liens des articles avec is_recommandation (True) uniques ont été ajoutés à links.txt")
# main.py
import os
import requests
import re
from auth import login
from scraper import get_disciplines, get_article_urls, get_soup
from parser import parse_article

# Configuration
BASE_URL = "https://www.evidencealerts.com"
START_URL = f"{BASE_URL}/HitParade/StellarHighestRated?discipline=user"
OUTPUT_DIR = "articles"

# Remplace par tes identifiants
EMAIL = "jperrama@gmail.com"
PASSWORD = "JE-po1906"

def clean_discipline_name(name):
    """Nettoie le nom de la discipline pour en faire un nom de dossier valide."""
    cleaned_name = re.sub(r'[\/\-\s]+', '-', name.strip())
    cleaned_name = re.sub(r'[^a-zA-Z0-9\-]', '', cleaned_name)
    return cleaned_name

def main():
    # Créer le dossier principal de sortie s'il n'existe pas
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Initialiser la session
    session = requests.Session()

    # Connexion
    if not login(session, EMAIL, PASSWORD, START_URL):
        return

    # Récupérer les disciplines
    disciplines = get_disciplines(session, START_URL)
    print("Disciplines trouvées :")
    for value, name in disciplines:
        print(f"  - {name} ({value})")

    # Parcourir chaque discipline
    for disc_value, disc_name in disciplines:
        print(f"\nTraitement de la discipline : {disc_name}")
        
        # Créer un sous-dossier avec le nom nettoyé de la discipline
        cleaned_disc_name = clean_discipline_name(disc_name)
        discipline_dir = os.path.join(OUTPUT_DIR, cleaned_disc_name)
        if not os.path.exists(discipline_dir):
            os.makedirs(discipline_dir)

        # Récupérer les URLs des articles
        article_urls = get_article_urls(session, disc_value)
        print(f"  {len(article_urls)} article(s) trouvé(s).")

        for article_id, article_url in article_urls:
            print(f"    Récupération de : {article_url}")
            soup = get_soup(session, article_url)

            # Vérifier si redirection vers login
            if "Please sign in" in soup.text:
                print("      Session expirée, tentative de reconnexion...")
                if not login(session, EMAIL, PASSWORD, article_url):
                    print("      Échec de la reconnexion, article ignoré.")
                    continue
                soup = get_soup(session, article_url)

            # Parser l'article
            article_data = parse_article(soup)

            # Sauvegarder dans un fichier dans le sous-dossier de la discipline
            filename = os.path.join(discipline_dir, f"{article_id}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=== Lien PubMed ===\n")
                f.write(article_data["pubmed_link"] + "\n\n")
                f.write("=== Métadonnées ===\n")
                f.write(article_data["metadata"] + "\n\n")
                f.write("=== Abstract ===\n")
                f.write(article_data["abstract"])
            print(f"      Sauvegardé dans {filename}")

if __name__ == "__main__":
    main()
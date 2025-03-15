import os
import requests
import re
import argparse
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

# Disciplines ciblées (valeurs correspondant aux disciplines avec <6 articles)
TARGET_DISCIPLINE_VALUES = [
    "270",  # Surgery - Ophthalmology (Ophtalmologie)
    "296",  # Special Interest - Pain -- Physician (Médecine de la douleur)
    "272",  # Surgery - Thoracic (Chirurgie thoracique)
    "21",   # --Neurology (Neurologie)
    "266",  # Surgery - Gastrointestinal (Chirurgie digestive)
    "262",  # Surgery - Orthopaedics (Chirurgie orthopédique)
    "23",   # --Physical Medicine and Rehabilitation (Médecine physique et réadaptation)
    "24",   # --Respirology/Pulmonology (Pneumologie)
    "275",  # Surgery - Cardiac (Chirurgie cardiaque)
    "274",  # Surgery - Urology (Urologie)
    "273",  # Surgery - Vascular (Chirurgie vasculaire)
    "25",   # --Rheumatology (Rhumatologie)
    "268",  # Surgery - Neurosurgery (Neurochirurgie)
    "276",  # Surgery - Ear Nose Throat (Chirurgie ORL)
    "263",  # Occupational and Environmental Health (Médecine du Travail)
    "253",  # Pediatrics (General) (Pédiatrie)
    "13",   # --Genetics (Génétique)
    "19"    # --Intensivist/Critical Care (Anesthésie - Réanimation)
]

def clean_discipline_name(name):
    """Nettoie le nom de la discipline pour en faire un nom de dossier valide."""
    cleaned_name = re.sub(r'[\/\-\s]+', '-', name.strip())
    cleaned_name = re.sub(r'[^a-zA-Z0-9\-]', '', cleaned_name)
    return cleaned_name

def main():
    # Ajouter un argument pour cibler uniquement les disciplines spécifiques
    parser = argparse.ArgumentParser(description="Scraper pour Evidence Alerts")
    parser.add_argument("--targeted", action="store_true", help="Scrape uniquement les disciplines ciblées (<6 articles)")
    args = parser.parse_args()

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

    # Filtrer les disciplines si l'option --targeted est activée
    if args.targeted:
        disciplines = [(value, name) for value, name in disciplines if value in TARGET_DISCIPLINE_VALUES]
        if not disciplines:
            print("Aucune discipline cible trouvée.")
            return
        print("\nMode ciblé activé. Disciplines à traiter :")
        for value, name in disciplines:
            print(f"  - {name} ({value})")
    else:
        print("\nMode complet activé : traitement de toutes les disciplines.")

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
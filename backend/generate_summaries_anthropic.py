import os
import argparse
import re
from datetime import datetime
from dotenv import load_dotenv
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging
import time

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d’environnement
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Configuration
INPUT_DIR = "articles"
OUTPUT_DIR = "syntheses"
MODEL_NAME = "claude-3-7-sonnet-20250219"

# Initialiser le client Anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Semaphore pour limiter les requêtes à l’API (réduit à 8 pour ralentir)
semaphore = threading.Semaphore(8)

def read_article_file(filepath):
    """Lit un fichier .txt et retourne le lien PubMed, les métadonnées, l'abstract, la date et le journal."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        pubmed_start = content.find("=== Lien PubMed ===")
        metadata_start = content.find("=== Métadonnées ===")
        abstract_start = content.find("=== Abstract ===")
        
        if pubmed_start == -1 or metadata_start == -1 or abstract_start == -1:
            logger.warning(f"Fichier {filepath} ignoré : balises manquantes.")
            return None, None, None, None, None
        
        pubmed_link = content[pubmed_start + len("=== Lien PubMed ===\n"):metadata_start].strip()
        metadata = content[metadata_start + len("=== Métadonnées ===\n"):abstract_start].strip()
        abstract = content[abstract_start + len("=== Abstract ===\n"):].strip()
        
        if abstract.strip().upper() == "N/A":
            logger.warning(f"Fichier {filepath} ignoré : abstract N/A.")
            return None, None, None, None, None
        
        pub_date = extract_publication_date(metadata)
        journal = extract_journal(metadata)
        
        return pubmed_link, metadata, abstract, pub_date, journal
    except Exception as e:
        logger.error(f"Erreur lecture fichier {filepath}: {e}")
        return None, None, None, None, None

def extract_publication_date(metadata):
    """Extract the publication date from metadata using Anthropic."""
    with semaphore:
        prompt = (
            "Extract the publication date from the following metadata. "
            "Look for a date in the format 'Month Day, Year' or 'Year Month Day' (e.g., 'Epub 2024 Feb 23' or '2024 Mar 7'). "
            "If 'Epub' is present, use the date following it; otherwise, use the first date in the citation. "
            "Return the date as a string in the format 'YYYY-MM-DD'. "
            "If no date is found, return '1970-01-01'. "
            f"Metadata:\n{metadata}"
        )
        
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=50,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        time.sleep(0.5)  # Pause de 0.5 seconde pour ralentir
        date_str = response.content[0].text.strip()
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            date_str = '1970-01-01'
        
        return date_str

def extract_journal(metadata):
    """Extract the journal name from metadata using Anthropic."""
    with semaphore:
        prompt = (
            "Extract the journal name from the following metadata. "
            "Look for the journal name (e.g., 'Lancet', 'JAMA', 'Am J Emerg Med') typically following the author list and before the DOI or publication details. "
            "Return the journal name as a string. If no journal is found, return 'Inconnu'. "
            "Metadata:\n{metadata}"
        )
        
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=50,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        time.sleep(0.5)  # Pause de 0.5 seconde pour ralentir
        journal = response.content[0].text.strip()
        return journal if journal else 'Inconnu'

def translate_to_french(text):
    """Traduit un texte en français avec Claude."""
    with semaphore:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=2000,
            temperature=0.5,
            system="Tu es un traducteur médical expert en français.",
            messages=[{"role": "user", "content": f"Traduis ce texte en français de manière claire et précise :\n{text}"}]
        )
        time.sleep(0.5)  # Pause de 0.5 seconde pour ralentir
        return response.content[0].text

def generate_summary(metadata, abstract_fr, journal):
    """Génère une synthèse avec une section dédiée pour la revue."""
    with semaphore:
        prompt = (
            "Transforme cet article scientifique en une synthèse concise en français (100-150 mots) pour médecins. "
            "Ton : clair, factuel, clinique. Structure obligatoire : 📝 Titre, 📌 Contexte & Problématique, 🧪 Méthodologie, "
            "📊 Résultats clés, 🩺 Impact clinique, ## Revue, 📖 Référence. Chaque section doit être brève. "
            "Sous la section ## Revue, indique uniquement le nom de la revue : '{journal}'. "
            "Pour la section 📖 Référence, inclut les détails de la citation (année, volume, pages, DOI) sans inclure les auteurs ou la revue (car elle est déjà dans ## Revue). "
            "Mets en avant les résultats principaux et implications pratiques. "
            "Explique toutes les abréviations au moins une fois (terme complet entre parenthèses). "
            "Utilise uniquement les informations de l’input. "
            f"Article :\n{metadata}\n{abstract_fr}"
        ).format(journal=journal)
        
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=2000,
            temperature=0.5,
            system="Tu es un assistant médical francophone.",
            messages=[{"role": "user", "content": prompt}]
        )
        time.sleep(0.5)  # Pause de 0.5 seconde pour ralentir
        return response.content[0].text

def is_summary_valid(summary):
    """Vérifie si la synthèse respecte la structure et est en français."""
    required_sections = ["📝", "📌", "🧪", "📊", "🩺", "## Revue", "📖"]
    has_all_sections = all(section in summary for section in required_sections)
    is_french = any(word in summary.lower() for word in ["contexte", "méthodologie", "résultats", "impact", "référence"])
    return has_all_sections and is_french

def process_article(filepath, discipline_folder):
    """Traite un seul article et génère une synthèse, sauf si elle existe déjà."""
    if not os.path.exists(filepath):
        logger.info(f"Fichier source {filepath} inexistant.")
        return

    output_path = os.path.join(OUTPUT_DIR, discipline_folder, os.path.basename(filepath))
    
    # Vérifier si le fichier de synthèse existe déjà
    if os.path.exists(output_path):
        logger.info(f"Synthèse {output_path} existe déjà, fichier ignoré.")
        return

    logger.info(f"Traitement : {filepath}")
    
    pubmed_link, metadata, abstract, pub_date, journal = read_article_file(filepath)
    if not (pubmed_link and metadata and abstract):
        logger.warning(f"Fichier {filepath} ignoré : données invalides.")
        return

    logger.info(f"  Traduction de l’abstract pour {filepath}...")
    abstract_fr = translate_to_french(abstract)
    
    logger.info(f"  Génération de la synthèse pour {filepath}...")
    summary = generate_summary(metadata, abstract_fr, journal)
    
    if not is_summary_valid(summary):
        logger.warning(f"Correction nécessaire pour {filepath}...")
        with semaphore:
            correction_prompt = (
                "Corrige cette synthèse pour inclure toutes les sections : "
                "📝 Titre, 📌 Contexte & Problématique, 🧪 Méthodologie, 📊 Résultats clés, 🩺 Impact clinique, ## Revue, 📖 Référence. "
                "Reste concis (100-150 mots), en français. "
                "Sous la section ## Revue, indique uniquement le nom de la revue : '{journal}'. "
                "Pour la section 📖 Référence, inclut les détails de la citation (année, volume, pages, DOI) sans inclure les auteurs ou la revue. "
                "Synthèse initiale :\n{summary}"
            ).format(journal=journal, summary=summary)
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=2000,
                temperature=0.5,
                messages=[{"role": "user", "content": correction_prompt}]
            )
            time.sleep(0.5)  # Pause de 0.5 seconde pour ralentir
            summary = response.content[0].text
    
    summary = f"Date de publication : {pub_date}\n\n{summary}\n🔗 Lien PubMed : {pubmed_link}"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)
    logger.info(f"  Sauvegardée : {output_path}")

def process_articles(test_mode=False):
    """Traite les articles en parallèle, mais plus lentement pour réduire les coûts."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logger.info(f"Dossier {OUTPUT_DIR} créé.")

    all_files = []
    for discipline_folder in os.listdir(INPUT_DIR):
        discipline_path = os.path.join(INPUT_DIR, discipline_folder)
        if os.path.isdir(discipline_path):
            files = [os.path.join(discipline_path, f) for f in os.listdir(discipline_path) if f.endswith(".txt")]
            all_files.extend([(discipline_folder, f) for f in files])
            logger.info(f"Trouvé {len(files)} fichiers dans {discipline_folder}")

    if not all_files:
        logger.error("Aucun fichier .txt trouvé dans les dossiers d'articles.")
        return

    if test_mode:
        logger.info("Mode test activé : traitement de 5 articles.")
        files_to_process = [
            ("Internal-Medicine-or-see-subspecialties-below", os.path.join(INPUT_DIR, "Internal-Medicine-or-see-subspecialties-below", "112347.txt")),
            ("FM-GP-Mental-Health", os.path.join(INPUT_DIR, "FM-GP-Mental-Health", "115334.txt")),
            ("FM-GP-Mental-Health", os.path.join(INPUT_DIR, "FM-GP-Mental-Health", "114493.txt")),
            ("FM-GP-Mental-Health", os.path.join(INPUT_DIR, "FM-GP-Mental-Health", "114620.txt")),
            ("Respirology-Pulmonology", os.path.join(INPUT_DIR, "Respirology-Pulmonology", "112480.txt"))
        ]
    else:
        logger.info("Mode complet activé : traitement de tous les articles.")
        files_to_process = all_files

    # Process in parallel avec moins de workers pour ralentir
    max_workers = 8  # Réduit de 16 à 8 pour moins de pression sur l’API
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_article, filepath, discipline): (filepath, discipline) for discipline, filepath in files_to_process}
        for future in as_completed(future_to_file):
            filepath, _ = future_to_file[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Erreur sur {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Générer des synthèses d’articles.")
    parser.add_argument("--test", action="store_true", help="Mode test : 5 articles.")
    args = parser.parse_args()
    process_articles(test_mode=args.test)

if __name__ == "__main__":
    main()
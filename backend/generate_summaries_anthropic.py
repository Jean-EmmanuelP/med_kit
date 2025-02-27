import os
import time
import argparse
from dotenv import load_dotenv
import anthropic

# Charger les variables d’environnement
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Configuration
INPUT_DIR = "articles"
OUTPUT_DIR = "syntheses"
MODEL_NAME = "claude-3-7-sonnet-20250219"  # Modèle Claude performant

# Initialiser le client Anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def read_article_file(filepath):
    """Lit un fichier .txt et retourne le lien PubMed, les métadonnées et l'abstract."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    pubmed_start = content.find("=== Lien PubMed ===")
    metadata_start = content.find("=== Métadonnées ===")
    abstract_start = content.find("=== Abstract ===")
    
    if pubmed_start == -1 or metadata_start == -1 or abstract_start == -1:
        return None, None, None
    
    pubmed_link = content[pubmed_start + len("=== Lien PubMed ===\n"):metadata_start].strip()
    metadata = content[metadata_start + len("=== Métadonnées ===\n"):abstract_start].strip()
    abstract = content[abstract_start + len("=== Abstract ===\n"):].strip()
    
    if abstract.strip().upper() == "N/A":
        return None, None, None
    
    return pubmed_link, metadata, abstract

def translate_to_french(text):
    """Traduit un texte en français avec Claude, en utilisant des termes médicaux."""
    response = client.messages.create(
        model=MODEL_NAME,
        max_token=2000,
        temperature=0.5,
        system="Tu es un traducteur médical expert en français.",
        messages=[{"role": "user", "content": f"Traduis ce texte en français de manière claire et précise, en utilisant des termes médicaux appropriés. Ne modifie pas le contenu, juste la langue. Base-toi uniquement sur le texte fourni :\n{text}"}]
    )
    return response.content[0].text

def generate_summary(metadata, abstract_fr):
    """Génère une synthèse concise et factuelle avec Claude."""
    prompt = (
        "Transforme cet article scientifique en une synthèse concise en français (100-150 mots) pour médecins et chirurgiens. "
        "Ton : clair, factuel, clinique. Structure obligatoire : 📝 Titre, 📌 Contexte & Problématique, 🧪 Méthodologie, "
        "📊 Résultats clés, 🩺 Impact clinique, 📖 Référence (style Vancouver). "
        "Chaque section doit être brève, avec des phrases courtes. Mets en avant les résultats principaux (chiffres clés) "
        "et les implications pratiques. Utilise uniquement les informations de l’input, sans ajouter de données externes. "
        f"Article :\n{metadata}\n{abstract_fr}"
    )
    response = client.messages.create(
        model=MODEL_NAME,
        max_token=2000,
        temperature=0.5,
        system="Tu es un assistant médical pour médecins francophones.",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def is_summary_valid(summary):
    """Vérifie si la synthèse respecte la structure et est en français."""
    required_sections = ["📝", "📌", "🧪", "📊", "🩺", "📖"]
    has_all_sections = all(section in summary for section in required_sections)
    is_french = any(word in summary.lower() for word in ["contexte", "méthodologie", "résultats", "impact", "référence"])
    return has_all_sections and is_french

def process_articles(test_mode=False):
    """Traite les articles : 5 en mode test, tous sinon."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if test_mode:
        print("Mode test activé : traitement de 5 articles.")
        files_to_process = [
            ("Internal-Medicine-or-see-subspecialties-below", os.path.join(INPUT_DIR, "Internal-Medicine-or-see-subspecialties-below", "112347.txt")),
            ("FM-GP-Mental-Health", os.path.join(INPUT_DIR, "FM-GP-Mental-Health", "115334.txt")),
            ("FM-GP-Mental-Health", os.path.join(INPUT_DIR, "FM-GP-Mental-Health", "114493.txt")),
            ("FM-GP-Mental-Health", os.path.join(INPUT_DIR, "FM-GP-Mental-Health", "114620.txt")),
            ("-Respirology-Pulmonology", os.path.join(INPUT_DIR, "-Respirology-Pulmonology", "112480.txt"))
        ]
    else:
        print("Mode complet activé : traitement de tous les articles.")
        all_files = []
        for discipline_folder in os.listdir(INPUT_DIR):
            discipline_path = os.path.join(INPUT_DIR, discipline_folder)
            if os.path.isdir(discipline_path):
                for article_file in os.listdir(discipline_path):
                    if article_file.endswith(".txt"):
                        all_files.append((discipline_folder, os.path.join(discipline_path, article_file)))
        files_to_process = all_files

    for discipline_folder, filepath in files_to_process:
        if not os.path.exists(filepath):
            print(f"Fichier introuvable : {filepath}, ignoré.")
            continue
        
        print(f"  Traitement : {filepath}")
        pubmed_link, metadata, abstract = read_article_file(filepath)
        
        if pubmed_link and metadata and abstract:
            print(f"    Traduction de l’abstract...")
            abstract_fr = translate_to_french(abstract)
            time.sleep(10)
            
            print(f"    Génération de la synthèse : {os.path.basename(filepath)}")
            summary = generate_summary(metadata, abstract_fr)
            
            if not is_summary_valid(summary):
                print(f"    Correction de la synthèse...")
                correction_prompt = (
                    "Corrige cette synthèse pour inclure toutes les sections : "
                    "📝 Titre, 📌 Contexte & Problématique, 🧪 Méthodologie, 📊 Résultats clés, 🩺 Impact clinique, 📖 Référence. "
                    "Reste concis (100-150 mots), en français, et base-toi uniquement sur l’input. Synthèse initiale :\n"
                    f"{summary}"
                )
                response = client.messages.create(
                    model=MODEL_NAME,
                    temperature=0.5,
                    messages=[{"role": "user", "content": correction_prompt}]
                )
                summary = response.content[0].text
            
            summary += f"\n🔗 Lien PubMed : {pubmed_link}"
            
            output_discipline_dir = os.path.join(OUTPUT_DIR, discipline_folder)
            if not os.path.exists(output_discipline_dir):
                os.makedirs(output_discipline_dir)
            
            output_filename = os.path.join(output_discipline_dir, os.path.basename(filepath))
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"    Sauvegardée : {output_filename}")
            time.sleep(60)
        else:
            print(f"    Ignoré (abstract N/A ou erreur) : {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Générer des synthèses d’articles.")
    parser.add_argument("--test", action="store_true", help="Mode test : 5 articles.")
    args = parser.parse_args()
    process_articles(test_mode=args.test)

if __name__ == "__main__":
    main()
import os
import re
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d’environnement
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialiser le client Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Dossier contenant les synthèses
SYNTHESES_DIR = "syntheses"

# Charger les disciplines depuis la table disciplines
response = supabase.table("disciplines").select("id, name").execute()
DISCIPLINE_NAME_TO_ID = {item["name"]: item["id"] for item in response.data}

# Mapping des sous-catégories aux disciplines principales
DISCIPLINE_MAPPING = {
    "Allergy-and-Immunology": ["Allergie et immunologie"],
    "Cardiology": ["Cardiologie"],
    "Dermatology": ["Dermatologie"],
    "Endocrine": ["Endocrinologie-Diabétologie-Nutrition"],
    "Gastroenterology": ["Hépato-Gastroentérologie"],
    "Genetics": ["Génétique"],
    "Geriatrics": ["Gériatrie"],
    "Hematology": ["Hématologie"],
    "Hemostasis-and-Thrombosis": ["Hématologie"],
    "Infectious-Disease": ["Maladies infectieuses"],
    "Intensivist-Critical-Care": ["Anesthésie - Réanimation"],
    "Nephrology": ["Néphrologie"],
    "Neurology": ["Neurologie"],
    "Oncology-Breast": ["Oncologie"],
    "Oncology-Gastrointestinal": ["Oncologie"],
    "Oncology-General": ["Oncologie"],
    "Oncology-Genitourinary": ["Oncologie"],
    "Oncology-Gynecology": ["Oncologie"],
    "Oncology-Hematology": ["Oncologie"],
    "Oncology-Lung": ["Oncologie"],
    "Oncology-Palliative-and-Supportive-Care": ["Oncologie"],
    "Oncology-Pediatric": ["Oncologie", "Pédiatrie"],
    "Physical-Medicine-and-Rehabilitation": ["Médecine physique et réadaptation"],
    "Respirology-Pulmonology": ["Pneumologie"],
    "Rheumatology": ["Rhumatologie"],
    "Tropical-and-Travel-Medicine": ["Maladies infectieuses"],
    "Emergency-Medicine": ["Urgences"],
    "Family-Medicine-FM-General-Practice-GP": ["Médecine Générale"],
    "FM-GP-Anesthesia": ["Anesthésie - Réanimation"],
    "FM-GP-Mental-Health": ["Psychiatrie"],
    "FM-GP-Obstetrics": ["Gynécologie-obstétrique"],
    "General-Internal-Medicine-Primary-CareUS": ["Médecine Interne"],
    "Hospital-Doctor-Hospitalists": ["Médecine Interne"],
    "Internal-Medicine-or-see-subspecialties-below": ["Médecine Interne"],
    "Occupational-and-Environmental-Health": ["Médecine du Travail"],
    "Public-Health": ["Santé Publique"],
    "Surgery-Ophthalmology": ["Ophtalmologie"],
    "Special-Interest-Pain-Physician": ["Médecine de la douleur"],
    "Surgery-Thoracic": ["Chirurgie thoracique"],
    "Surgery-Gastrointestinal": ["Chirurgie digestive"],
    "Surgery-Orthopaedics": ["Chirurgie orthopédique"],
    "Surgery-Cardiac": ["Chirurgie cardiaque"],
    "Surgery-Urology": ["Urologie"],
    "Surgery-Vascular": ["Chirurgie vasculaire"],
    "Surgery-Neurosurgery": ["Neurochirurgie"],
    "Surgery-Ear-Nose-Throat": ["Chirurgie ORL"],
    "Pediatrics-General": ["Pédiatrie"],
    "Anesthesiology": ["Anesthésie - Réanimation"],
    "Gynecology": ["Gynécologie-obstétrique"],
    "Obstetrics": ["Gynécologie-obstétrique"],
    "Pediatric-Emergency-Medicine": ["Pédiatrie", "Urgences"],
    "Pediatric-Hospital-Medicine": ["Pédiatrie"],
    "Pediatric-Neonatology": ["Pédiatrie"],
    "Psychiatry": ["Psychiatrie"],
    "Surgery-Colorectal": ["Chirurgie digestive"],
    "Surgery-Plastic": ["Chirurgie plastique"],
    "Surgery-Head-and-Neck": ["Chirurgie ORL"],
    "Special-Interest-Obesity-Physician": ["Endocrinologie-Diabétologie-Nutrition"],
    "Special-Interest-Obesity-Surgeon": ["Chirurgie digestive"]
}

def parse_synthesis_file(filepath):
    """Parse un fichier .txt de synthèse et retourne les champs nécessaires."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract publication date
    date_match = re.match(r"Date de publication : (\d{4}-\d{2}-\d{2})", content)
    published_at = (date_match.group(1) + "T00:00:00+00:00") if date_match else "1970-01-01T00:00:00+00:00"
    
    # Extract title
    title_match = re.search(r"# 📝 (.*?)(?=\n\s*##)", content, re.DOTALL)
    title = title_match.group(1).strip() if title_match else "Titre inconnu"
    
    # Extract content (from ## 📌 Contexte & Problématique to before ## Revue)
    content_start = content.find("## 📌 Contexte & Problématique")
    content_end = content.find("## Revue")
    content_text = content[content_start:content_end].strip() if content_start != -1 and content_end != -1 else content
    
    # Extract journal from the ## Revue section
    journal = "Inconnu"
    revue_start = content.find("## Revue")
    if revue_start != -1:
        revue_end = content.find("\n##", revue_start + 1)  # Find the next section
        if revue_end == -1:
            revue_end = content.find("\n🔗", revue_start)  # Fallback to end of content
        journal_text = content[revue_start + len("## Revue\n"):revue_end].strip()
        journal = journal_text if journal_text else "Inconnu"
    
    # Extract PubMed link
    link_match = re.search(r"🔗 Lien PubMed : (https://[^\s]+)", content)
    pubmed_link = link_match.group(1).strip() if link_match else None
    
    # Extract discipline
    relative_path = os.path.relpath(filepath, SYNTHESES_DIR)
    backend_discipline = os.path.dirname(relative_path)
    
    # Vérifier si le nom commence par un tiret et retirer le tiret si présent
    if backend_discipline.startswith('-'):
        backend_discipline_cleaned = backend_discipline[1:]  # Retire le tiret
        print(f"Dossier avec tiret détecté : {backend_discipline} -> {backend_discipline_cleaned}")
    else:
        backend_discipline_cleaned = backend_discipline
    
    frontend_discipline_names = DISCIPLINE_MAPPING.get(backend_discipline_cleaned, ["Unknown"])
    frontend_discipline_ids = [DISCIPLINE_NAME_TO_ID.get(name) for name in frontend_discipline_names if DISCIPLINE_NAME_TO_ID.get(name)]
    
    if not frontend_discipline_ids:
        print(f"Avertissement : Aucune discipline trouvée pour {backend_discipline_cleaned} (original: {backend_discipline})")
    
    return {
        "title": title,
        "content": content_text,
        "published_at": published_at,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "link": pubmed_link,
        "journal": journal,
        "discipline_ids": frontend_discipline_ids
    }

def insert_article_to_db(article_data):
    """Insère un article dans la table articles."""
    try:
        response = supabase.table("articles").insert({
            "title": article_data["title"],
            "content": article_data["content"],
            "published_at": article_data["published_at"],
            "created_at": article_data["created_at"],
            "link": article_data["link"],
            "journal": article_data["journal"]
        }).execute()
        
        if response.data:
            print(f"Article inséré avec succès : {article_data['title']}")
            article_id = response.data[0]["id"]
            for discipline_id in article_data["discipline_ids"]:
                response_discipline = supabase.table("article_disciplines").insert({
                    "article_id": article_id,
                    "discipline_id": discipline_id
                }).execute()
                if response_discipline.data:
                    print(f"Discipline associée : ID {discipline_id}")
                else:
                    print(f"Erreur association discipline : {response_discipline.error}")
        else:
            print(f"Erreur insertion : {response.error}")
    except Exception as e:
        print(f"Exception : {e}")

def populate_articles():
    """Parcourt et insère les synthèses dans la base de données."""
    for root, dirs, files in os.walk(SYNTHESES_DIR):
        for file in files:
            if file.endswith(".txt"):
                filepath = os.path.join(root, file)
                print(f"Processing file: {filepath}")
                article_data = parse_synthesis_file(filepath)
                insert_article_to_db(article_data)

def main():
    print("Starting population of articles table...")
    populate_articles()
    print("Population complete.")

if __name__ == "__main__":
    main()
import os
import re
from datetime import datetime, timezone  # Ajout de l'importation de timezone
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d’environnement
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")  # e.g., https://etxelhjnqbrgwuitltyk.supabase.co
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Your Supabase anon or service role key

# Initialiser le client Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Dossier contenant les synthèses
SYNTHESES_DIR = "syntheses"

# Charger les disciplines depuis la table disciplines et créer un mapping name -> id
response = supabase.table("disciplines").select("id, name").execute()
DISCIPLINE_NAME_TO_ID = {item["name"]: item["id"] for item in response.data}

# Mapping des sous-catégories (dossiers) aux disciplines principales (en français)
# Chaque sous-catégorie est associée à une ou plusieurs disciplines, et nous utilisons DISCIPLINE_NAME_TO_ID pour obtenir les IDs
DISCIPLINE_MAPPING = {
    "-Allergy-and-Immunology": ["Allergie et immunologie"],
    "-Cardiology": ["Cardiologie"],
    "-Dermatology": ["Dermatologie"],
    "-Endocrine": ["Endocrinologie-Diabétologie-Nutrition"],
    "-Gastroenterology": ["Hépato-Gastroentérologie"],
    "-Genetics": ["Génétique"],
    "-Geriatrics": ["Gériatrie"],
    "-Hematology": ["Hématologie"],
    "-Hemostasis-and-Thrombosis": ["Hématologie"],
    "-Infectious-Disease": ["Maladies infectieuses"],
    "-Intensivist-Critical-Care": ["Anesthésie - Réanimation"],
    "-Nephrology": ["Néphrologie"],
    "-Neurology": ["Neurologie"],
    "-Oncology-Breast": ["Oncologie"],
    "-Oncology-Gastrointestinal": ["Oncologie"],
    "-Oncology-General": ["Oncologie"],
    "-Oncology-Genitourinary": ["Oncologie"],
    "-Oncology-Gynecology": ["Oncologie"],
    "-Oncology-Hematology": ["Oncologie"],
    "-Oncology-Lung": ["Oncologie"],
    "-Oncology-Palliative-and-Supportive-Care": ["Oncologie"],
    "-Oncology-Pediatric": ["Oncologie", "Pédiatrie"],
    "-Physical-Medicine-and-Rehabilitation": ["Médecine physique et réadaptation"],
    "-Respirology-Pulmonology": ["Pneumologie"],
    "-Rheumatology": ["Rhumatologie"],
    "-Tropical-and-Travel-Medicine": ["Maladies infectieuses"],
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
    # Ignorer les dossiers non pertinents
    "My-disciplines": ["Unknown"]
}

def parse_synthesis_file(filepath):
    """Parse un fichier .txt de synthèse et retourne les champs nécessaires pour la table articles."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract publication date
    date_match = re.match(r"Date de publication : (\d{4}-\d{2}-\d{2})", content)
    if date_match:
        published_at = date_match.group(1) + "T00:00:00+00:00"  # Format timestampz
    else:
        published_at = "1970-01-01T00:00:00+00:00"  # Default if not found
    
    # Extract title (remove "# 📝" and emoji, allow for multiple newlines before next section)
    title_match = re.search(r"# 📝 (.*?)(?=\n\s*##)", content, re.DOTALL)
    title = title_match.group(1).strip() if title_match else "Titre inconnu"
    
    # Extract content (everything from "📌 Contexte & Problématique" until "🔗 Lien PubMed")
    content_start = content.find("## 📌 Contexte & Problématique")
    content_end = content.find("🔗 Lien PubMed")
    if content_start != -1 and content_end != -1:
        content_text = content[content_start:content_end].strip()
    else:
        content_text = content  # Fallback to full content if structure not found
    
    # Extract author (first author before comma in "Référence" section)
    ref_start = content.find("## 📖 Référence")
    if ref_start != -1:
        ref_end = content.find("\n", ref_start)
        ref_line = content[ref_start + len("## 📖 Référence\n"):ref_end].strip()
        author_match = re.match(r"^[^,]+", ref_line)
        author = author_match.group(0).strip() if author_match else "Unknown"
    else:
        author = "Unknown"
    
    # Extract PubMed link
    link_match = re.search(r"🔗 Lien PubMed : (https://[^\s]+)", content)
    pubmed_link = link_match.group(1).strip() if link_match else None
    
    # Extract discipline from the filepath (subdirectory name under syntheses)
    relative_path = os.path.relpath(filepath, SYNTHESES_DIR)
    backend_discipline = os.path.dirname(relative_path)  # Gets the subdirectory name (e.g., "FM-GP-Mental-Health")
    
    # Map backend discipline to frontend disciplines (can be multiple)
    frontend_discipline_names = DISCIPLINE_MAPPING.get(backend_discipline, ["Unknown"])
    
    # Convert discipline names to discipline IDs
    frontend_discipline_ids = []
    for name in frontend_discipline_names:
        discipline_id = DISCIPLINE_NAME_TO_ID.get(name)
        if discipline_id:
            frontend_discipline_ids.append(discipline_id)
        else:
            print(f"Discipline '{name}' non trouvée dans la table disciplines. Ignorée.")
    
    return {
        "title": title,
        "content": content_text,
        "author": author,
        "published_at": published_at,
        "created_at": datetime.now(timezone.utc).isoformat(),  # Correction de l'avertissement de dépréciation
        "link": pubmed_link,  # Can be None if no link is found
        "discipline_ids": frontend_discipline_ids  # List of discipline IDs
    }

def insert_article_to_db(article_data):
    """Insère un article dans la table articles de Supabase et met à jour article_disciplines."""
    try:
        # Insérer l'article dans la table articles
        response = supabase.table("articles").insert({
            "title": article_data["title"],
            "content": article_data["content"],
            "author": article_data["author"],
            "published_at": article_data["published_at"],
            "created_at": article_data["created_at"],
            "link": article_data["link"]
        }).execute()
        
        if response.data:
            print(f"Article inséré avec succès : {article_data['title']}")
            # Récupérer l'ID de l'article inséré
            article_id = response.data[0]["id"]
            
            # Insérer une entrée dans article_disciplines pour chaque discipline ID associée
            for discipline_id in article_data["discipline_ids"]:
                response_discipline = supabase.table("article_disciplines").insert({
                    "article_id": article_id,
                    "discipline_id": discipline_id
                }).execute()
                
                if response_discipline.data:
                    print(f"Discipline associée avec succès : ID {discipline_id} (article_id: {article_id})")
                else:
                    print(f"Erreur lors de l'association de la discipline ID {discipline_id}")
                    print(response_discipline.error)
        else:
            print(f"Erreur lors de l'insertion de l'article : {article_data['title']}")
            print(response.error)
    except Exception as e:
        print(f"Exception lors de l'insertion de l'article : {article_data['title']}")
        print(e)

def populate_articles():
    """Parcourt tous les fichiers .txt dans le dossier syntheses et les insère dans la table articles."""
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
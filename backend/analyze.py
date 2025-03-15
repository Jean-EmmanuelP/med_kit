import os
from collections import defaultdict

# Dossier contenant les synthèses
SYNTHESES_DIR = "syntheses"

def analyze_syntheses_directory():
    """Analyse le dossier syntheses et retourne le nombre de fichiers .txt par dossier."""
    file_counts = defaultdict(int)
    
    # Parcourir le dossier syntheses
    for root, dirs, files in os.walk(SYNTHESES_DIR):
        # Calculer le chemin relatif par rapport à SYNTHESES_DIR
        relative_path = os.path.relpath(root, SYNTHESES_DIR)
        # Si on est à la racine (SYNTHESES_DIR), ignorer
        if relative_path == ".":
            continue
        
        # Compter les fichiers .txt dans ce dossier
        txt_files = [f for f in files if f.endswith(".txt")]
        file_count = len(txt_files)
        file_counts[relative_path] = file_count
        print(f"Dossier : {relative_path}, Nombre de fichiers .txt : {file_count}")

    return file_counts

def main():
    print("Analyse du dossier syntheses...")
    file_counts = analyze_syntheses_directory()
    
    # Afficher un résumé
    total_files = sum(file_counts.values())
    print("\nRésumé :")
    print(f"Total des fichiers .txt : {total_files}")
    print("Détail par dossier :")
    for discipline, count in file_counts.items():
        print(f"- {discipline}: {count} fichier(s)")

    # Sauvegarder les données dans un fichier JSON pour vous (facultatif)
    import json
    with open("syntheses_analysis.json", "w", encoding="utf-8") as f:
        json.dump(dict(file_counts), f, ensure_ascii=False, indent=2)
    print("Données sauvegardées dans 'syntheses_analysis.json'")

if __name__ == "__main__":
    main()
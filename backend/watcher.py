import os
import time
import logging

# Configurer le logging pour afficher les mises à jour
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration des dossiers
INPUT_DIR = "articles"
OUTPUT_DIR = "syntheses"

def count_txt_files(directory):
    """Compte le nombre de fichiers .txt dans un dossier et ses sous-dossiers."""
    total = 0
    for root, _, files in os.walk(directory):
        total += len([f for f in files if f.endswith(".txt")])
    return total

def create_progress_bar(percentage):
    """Crée une barre de progression visuelle de 0% à 100%."""
    bar_length = 50  # Longueur de la barre en caractères
    filled_length = int(bar_length * percentage / 100)
    bar = '█' * filled_length + ' ' * (bar_length - filled_length)
    return f"[{bar}] {percentage:.2f}%"

def monitor_progress():
    """Surveille la progression avec une barre de 0% à 100% et le nombre de fichiers."""
    # Compter le nombre total de fichiers dans articles une seule fois
    total_articles = count_txt_files(INPUT_DIR)
    if total_articles == 0:
        logger.error(f"Aucun fichier .txt trouvé dans {INPUT_DIR}. Arrêt du script.")
        return
    
    logger.info(f"Nombre total d'articles à traiter : {total_articles}")
    
    # Boucle de surveillance
    while True:
        current_syntheses = count_txt_files(OUTPUT_DIR)
        percentage = (current_syntheses / total_articles) * 100 if total_articles > 0 else 0
        progress_bar = create_progress_bar(percentage)
        
        # Afficher la barre de progression et le détail des fichiers
        logger.info(f"Progression : {progress_bar}")
        logger.info(f"Fichiers : {current_syntheses}/{total_articles} synthèses générées")
        
        # Vérifier si le traitement est terminé
        if current_syntheses >= total_articles:
            logger.info("Traitement terminé : le nombre de synthèses égale le nombre d'articles.")
            break
        
        # Attendre 20 secondes avant la prochaine vérification (comme dans ton exemple)
        time.sleep(20)

def main():
    """Point d'entrée du script."""
    logger.info("Démarrage de la surveillance des synthèses...")
    monitor_progress()

if __name__ == "__main__":
    main()
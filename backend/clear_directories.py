import shutil
import os

# Dossiers à vider
dirs_to_clear = ["articles", "syntheses"]

for dir_path in dirs_to_clear:
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)  # Supprime le dossier et tout son contenu
        os.makedirs(dir_path)    # Recrée le dossier vide
        print(f"Cleared and recreated directory: {dir_path}")
    else:
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")
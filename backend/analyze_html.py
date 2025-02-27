# analyze_html.py
import requests
from bs4 import BeautifulSoup
from auth import login

# Configuration
BASE_URL = "https://www.evidencealerts.com"
LOGIN_URL = f"{BASE_URL}/Account/Login"
TARGET_URL = "https://www.evidencealerts.com/HitParade/StellarHighestRated/114176?discipline=272"  # Exemple à analyser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36"
}

# Remplace par tes identifiants
EMAIL = "ton_email@example.com"
PASSWORD = "ton_mot_de_passe"

def get_soup(session, url):
    """Télécharge une page et retourne un objet BeautifulSoup."""
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def analyze_page():
    """Récupère et sauvegarde le HTML d'une page pour analyse."""
    session = requests.Session()
    
    # Connexion
    if not login(session, EMAIL, PASSWORD, TARGET_URL):
        print("Échec de la connexion, abandon.")
        return
    
    # Récupérer la page
    soup = get_soup(session, TARGET_URL)
    
    # Sauvegarder le HTML brut
    with open("article_114176.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    print(f"HTML sauvegardé dans 'article_114176.html'.")

if __name__ == "__main__":
    analyze_page()
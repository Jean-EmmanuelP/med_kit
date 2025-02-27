# auth.py
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.evidencealerts.com"
LOGIN_URL = f"{BASE_URL}/Account/Login"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36"
}

def login(session, email, password, target_url):
    """Effectue la connexion et retourne True si réussie."""
    response = session.get(LOGIN_URL, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_token = soup.find("input", {"name": "__RequestVerificationToken"})["value"]

    login_data = {
        "__RequestVerificationToken": csrf_token,
        "Email": email,
        "Password": password,
        "RememberMe": "false",
        "ReturnUrl": target_url
    }

    login_response = session.post(LOGIN_URL, headers=HEADERS, data=login_data)
    login_response.raise_for_status()

    if "Please sign in" not in login_response.text:
        print("Connexion réussie.")
        return True
    else:
        print("Échec de la connexion.")
        return False
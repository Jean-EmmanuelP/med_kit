# scraper.py
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.evidencealerts.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36"
}

def get_soup(session, url):
    """Télécharge une page et retourne un objet BeautifulSoup."""
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def get_disciplines(session, start_url):
    """Récupère la liste des disciplines depuis la page initiale."""
    soup = get_soup(session, start_url)
    select = soup.find("select", {"id": "Disciplines"})
    disciplines = []
    if select:
        for option in select.find_all("option"):
            value = option.get("value")
            name = option.get_text(strip=True)
            disciplines.append((value, name))
    else:
        disciplines.append(("user", "My discipline(s)"))
    return disciplines

def get_article_urls(session, discipline_value):
    """Récupère les URLs des articles pour une discipline donnée."""
    page_url = f"{BASE_URL}/HitParade/StellarHighestRated?discipline={discipline_value}"
    soup = get_soup(session, page_url)
    article_rows = soup.find_all("tr", id=lambda x: x and x.startswith("Article"))
    article_urls = []
    for row in article_rows:
        link = row.find("a")
        if link and link.get("href"):
            article_url = BASE_URL + link.get("href")
            article_id = row.get("id").replace("Article", "")
            article_urls.append((article_id, article_url))
    return article_urls
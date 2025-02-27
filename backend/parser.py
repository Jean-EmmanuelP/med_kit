# parser.py
from bs4 import BeautifulSoup
import re

def extract_pubmed_link(soup, doi):
    """Extrait ou construit le lien PubMed à partir du HTML et du DOI."""
    # Chercher le lien "View on PubMed"
    pubmed_link_tag = soup.find("a", class_="text-primary article-record-button", string=lambda x: x and "View on PubMed" in x)
    if pubmed_link_tag and pubmed_link_tag.get("href"):
        # Si un lien redirigé est trouvé, on pourrait tenter de le résoudre, mais ici on préfère le DOI
        pass  # Pour l'instant, on ignore le lien redirigé car il n'est pas direct

    # Construire un lien PubMed avec le DOI (plus fiable)
    if doi:
        # Extraire le DOI des métadonnées (ex. "doi: 10.1016/j.jtha.2024.02.019")
        doi_match = re.search(r"doi: (10\.\d{4,}/[^\s]+)", doi)
        if doi_match:
            doi_value = doi_match.group(1)
            return f"https://pubmed.ncbi.nlm.nih.gov/?term={doi_value}"
    return "Lien PubMed non disponible"

def parse_article(soup):
    """Extrait le lien PubMed, les métadonnées et l'abstract d'une page d'article."""
    # Métadonnées
    metadata_div = soup.select_one("#ArticleRecord .panel.panel-default .panel-body div:first-child")
    metadata = metadata_div.get_text(separator="\n", strip=True) if metadata_div else "Métadonnées non trouvées"

    # Extraire le lien PubMed (avant les métadonnées dans le fichier)
    pubmed_link = extract_pubmed_link(soup, metadata)

    # Abstract
    abstract_panel = soup.find("div", class_="panel panel-default", recursive=True)
    while abstract_panel:
        heading = abstract_panel.find("div", class_="panel-heading")
        if heading and "Abstract" in heading.get_text(strip=True):
            abstract_body = abstract_panel.find("div", class_="panel-body")
            abstract = abstract_body.get_text(separator="\n", strip=True) if abstract_body else "Abstract non trouvé dans le panneau"
            break
        abstract_panel = abstract_panel.find_next("div", class_="panel panel-default")
    else:
        abstract = "Abstract non trouvé"

    return {
        "pubmed_link": pubmed_link,
        "metadata": metadata,
        "abstract": abstract
    }
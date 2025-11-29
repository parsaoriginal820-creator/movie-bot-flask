import cloudscraper
from bs4 import BeautifulSoup
import re
import requests

scraper = cloudscraper.create_scraper()

def search_psarips(query):
    try:
        url = f"https://psarips.eu/?s={query.replace(' ', '+')}"
        r = scraper.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        for item in soup.find_all('article')[:10]:
            a = item.find('h2').find('a') if item.find('h2') else None
            if a:
                results.append({
                    "title": a.text.strip(),
                    "link": a['href']
                })
        return results
    except:
        return []

def get_links_from_page(url):
    try:
        r = scraper.get(url, timeout=15)
        text = r.text
        patterns = [
            r'(https?://[^\s\'\"<>]+uptostream\.com/[^\s\'\"<>]+)',
            r'(https?://[^\s\'\"<>]+filemoon\.sx/[^\s\'\"<>]+)',
            r'(https?://[^\s\'\"<>]+streamtape\.com/[^\s\'\"<>]+)',
        ]
        links = []
        for pattern in patterns:
            found = re.findall(pattern, text)
            links.extend(found)
        return list(set([l for l in links if any(q in l.lower() for q in ["1080", "720", "web", "bluray"])]))[:6]
    except:
        return []

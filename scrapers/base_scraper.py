import requests
from bs4 import BeautifulSoup
import time

class BaseScraper:
    BASE_URL = "https://adatbank.mlsz.hu/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MLSZ-Scraper/1.0 (University Project; Budapest; borcsiczkypatrik@gmail.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'hu-HU,hu;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        })

    def get_soup(self, url: str, delay: float = 4.0, max_retries: int = 3) -> BeautifulSoup:
        """Letölti és feldolgozza a HTML-t retry-vel"""
        full_url = url if url.startswith("http") else self.BASE_URL + url
        
        for attempt in range(max_retries):
            try:
                time.sleep(delay)
                resp = self.session.get(full_url, timeout=30)
                resp.raise_for_status()
                resp.encoding = 'utf-8'
                return BeautifulSoup(resp.text, "html.parser")
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = delay * (attempt + 1)
                    print(f"Próbálkozás {attempt + 1}/{max_retries} sikertelen, várok {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Minden {max_retries} próbálkozás sikertelen: {e}")
                    raise
        
        raise Exception("Elértük a maximális próbálkozások számát")
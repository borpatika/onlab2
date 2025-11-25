from datetime import date, datetime
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import json
from scrapers.base_scraper import BaseScraper
from llm.injury_detector import LLMInjuryDetector
from database.db_operations import create_injury_article

class NSOArticleScraper(BaseScraper):
    """Nemzeti Sport cikkek scrapelésére szolgáló osztály"""

    
    BASE_URL = "https://www.nemzetisport.hu/"

    def __init__(self):
        super().__init__()
        # NSO-specifikus header beállítások
        self.session.headers.update({
            'User-Agent': 'NSO-Scraper/1.0 (University Project; Budapest; borcsiczkypatrik@gmail.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'hu-HU,hu;q=0.9,en;q=0.8',
            'Referer': 'https://www.nemzetisport.hu/',
        })

    def scrape_article(self, url: str, delay: float = 4.0, max_retries: int = 3) -> Optional[Dict[str, str]]:
        """
        NSO cikk adatainak kinyerése
        
        Args:
            url: A cikk URL-je
            delay: Várakozási idő kérések között
            max_retries: Maximális újrapróbálkozások száma
            
        Returns:
            Dictionary a cikk adataival vagy None hiba esetén
        """
        try:
            soup = self.get_soup(url, delay, max_retries)
            
            title = self._extract_title(soup)
            article_text = self._extract_article_text(soup)
            lead = self._extract_lead(soup)
            publish_date = self._extract_publish_date(soup)
            
            return {
                'title': title,
                'lead': lead,
                'text': article_text,
                'publish_date': publish_date,
                'url': url,
                'source': 'Nemzeti Sport'
            }
            
        except Exception as e:
            print(f"Hiba a cikk scrapelése közben ({url}): {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Cikk címének kinyerése"""
        title = soup.find('h1', class_='article-header-title')
        if title and title.get_text().strip():
            return title.get_text().strip()
        
        return "Cím nem található"

    def _extract_lead(self, soup: BeautifulSoup) -> str:
        """Cikk lead (bevezető) szövegének kinyerése"""
        lead = soup.find('div', class_='lead')
        if lead and lead.get_text().strip():
            return lead.get_text().strip()
        
        return ""

    def _extract_article_text(self, soup: BeautifulSoup) -> str:
        """Cikk fő szövegének kinyerése"""
        article_parts = []
        content_containers = []
        
        # Keresés class alapján
        content_containers.extend(soup.find_all('div', class_='block-content'))
        content_containers.extend(soup.find_all('div', class_='article-content'))
        content_containers.extend(soup.find_all('div', class_='article-body'))
        content_containers.extend(soup.find_all('div', class_=lambda x: x and 'content' in x))
        content_containers.extend(soup.find_all('nso-wysiwyg-box'))
        
        for container in content_containers:
            # Paragraph-ok kinyerése a tartalomból
            paragraphs = container.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 30:  # Csak értelmes hosszú szövegeket
                    article_parts.append(text)
        
        # Ha nem találtunk elegendő tartalmat, próbáljuk meg az összes paragraph-ot
        if len(article_parts) < 3:
            all_paragraphs = soup.find_all('p')
            for p in all_paragraphs:
                text = p.get_text().strip()
                if len(text) > 50:  # Csak hosszabb bekezdéseket
                    article_parts.append(text)
        
        return "\n\n".join(article_parts)

    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """Közzététel dátumának kinyerése"""
        date = soup.find('div', class_='article-header-date')
        if date and date.get_text().strip():
            return date.get_text().strip()
    
        return "Dátum nem található"

    def scrape_multiple_articles(self, urls: list, delay: float = 4.0) -> list:
        """
        Több cikk scrapelése egyszerre
        
        Args:
            urls: Cikk URL-ek listája
            delay: Várakozás URL-ek között
            
        Returns:
            Cikk adatok listája
        """
        articles = []
        
        for i, url in enumerate(urls):
            print(f"Cikk scrapelése ({i+1}/{len(urls)}): {url}")
            
            article_data = self.scrape_article(url, delay)
            if article_data:
                articles.append(article_data)
        
        return articles

    def get_article_links_from_rovat(self, rovat_url: str = "rovat/labdarugo-nb-i", delay: float = 3.0) -> List[str]:
        """
        Kinyeri az összes cikk linkjét a megadott rovat oldaláról
        
        Args:
            rovat_url: A rovat URL-je (alapértelmezetten labdarúgó NB I)
            delay: Várakozási idő
            
        Returns:
            Cikk URL-ek listája
        """
        try:
            # Teljes URL összeállítása
            full_url = self.BASE_URL + rovat_url if not rovat_url.startswith("http") else rovat_url
            
            print(f"Oldal letöltése: {full_url}")
            soup = self.get_soup(full_url, delay)
            
            article_links = []
            
            # 1. Keresés nso-article-card elemekben
            article_cards = soup.find_all('nso-article-card')
            print(f"Talált nso-article-card elemek: {len(article_cards)}")
            
            for card in article_cards:
                link = self._extract_link_from_card(card)
                if link and link not in article_links:
                    article_links.append(link)
            
            # 2. Keresés app-category-article-list elemben
            article_list = soup.find('app-category-article-list')
            if article_list:
                links_in_list = article_list.find_all('a', href=True)
                for link_elem in links_in_list:
                    href = link_elem['href']
                    if self._is_valid_article_link(href) and href not in article_links:
                        article_links.append(href)
            
            print(f"Összesen talált cikk link: {len(article_links)}")
            
            # Duplikátumok eltávolítása és teljes URL-ek készítése
            unique_links = list(set(article_links))
            full_links = [self._make_full_url(link) for link in unique_links]
            
            return full_links
            
        except Exception as e:
            print(f"Hiba a rovat oldal feldolgozása közben: {e}")
            return []

    def _extract_link_from_card(self, card) -> str:
        """Link kinyerése nso-article-card elemből"""
        try:
            # Keresés nso-article-card-link-wrapper-ben
            link_wrapper = card.find('nso-article-card-link-wrapper')
            if link_wrapper:
                link_elem = link_wrapper.find('a', href=True)
                if link_elem:
                    return link_elem['href']
            
            # Keresés közvetlenül a card-ban
            link_elem = card.find('a', href=True)
            if link_elem:
                return link_elem['href']
                
        except Exception as e:
            print(f"Hiba link kinyerése közben: {e}")
        
        return ""

    def _is_valid_article_link(self, href: str) -> bool:
        """Ellenőrzi, hogy a link érvényes cikk link-e"""
        if not href:
            return False
        
        # Kizárjuk ezeket
        excluded_patterns = [
            '/rovat/',
            '/hirlevel/',
            '/szerzo/',
            '/video/',
            '/galeria/',
            '#',
            'javascript:',
            'mailto:',
            'tel:'
        ]
        
        # Kell tartalmaznia ezeket a mintákat
        required_patterns = [
            '/labdarugo-nb-i/'
        ]
        
        # Kizárások ellenőrzése
        for pattern in excluded_patterns:
            if pattern in href:
                return False
        
        # Kötelező minták ellenőrzése
        for pattern in required_patterns:
            if pattern in href:
                return True
        
        return False

    def _make_full_url(self, link: str) -> str:
        """Relatív URL-ből teljes URL készítése"""
        if link.startswith('http'):
            return link
        elif link.startswith('/'):
            return self.BASE_URL + link[1:]
        else:
            return self.BASE_URL + link

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Egyszerű változat csak NSO formátumra"""
        if not date_str or date_str == "Dátum nem található":
            return None
        try:
            date_part = date_str.split(' ')[0].rstrip('.')
            return datetime.strptime(date_part, '%Y.%m.%d').date()
        except:
            return None

    def scrape_and_save_to_db(self):
        llm_detector = LLMInjuryDetector()

        # 1. Összes cikk link lekérése a rovatról
        print("Cikk linkek gyűjtése a rovatról...")
        article_urls = self.get_article_links_from_rovat("rovat/labdarugo-nb-i")
        if not article_urls:
            print("Nem sikerült cikk linkeket gyűjteni!")
            return
        
        # 2. Összes cikk scrapelése
        print("Cikkek letöltése...")
        all_articles = self.scrape_multiple_articles(article_urls, delay=4.0)
        
        if not all_articles:
            print("Nem sikerült letölteni a cikkeket!")
            return
        
        # 3. Cikkek feldolgozása LLM-mel
        injury_articles = []  # Cikkek, amikben sérülés van
        no_injury_articles = []  # Cikkek, amikben nincs sérülés
        error_articles = []  # Cikkek, amik nem dolgozhatók fel
        
        for i, article_data in enumerate(all_articles, 1):
            print(f"\n[{i}/{len(all_articles)}] Cikk feldolgozása: {article_data['title']}")
            print(f"URL: {article_data['url']}")
            
            # Összeállítjuk a teljes szöveget a címből, leadből és fő szövegből
            full_text = f"{article_data['title']}\n\n{article_data['lead']}\n\n{article_data['text']}"
            
            # Prompt építése
            prompt = llm_detector.build_prompt_from_article(full_text)
            
            # LLM lekérdezés
            print("LLM válasz várható...")
            llm_result = llm_detector.query_ollama(prompt)
            
            if llm_result:
                # Eredmények értelmezése
                try:
                    pattern = r'\{[^{}]*\}'
                    match = re.search(pattern, llm_result, re.DOTALL)
                    if match:
                        json_str = match.group()
                        result_data = json.loads(json_str)
                    
                        # Boolean érték kezelése - többféle formátumot kezeljünk
                        is_injured = result_data.get('is_injured', False)
                        
                        # Többféle boolean érték kezelése
                        if isinstance(is_injured, bool):
                            has_injury = is_injured
                        elif isinstance(is_injured, str):
                            has_injury = is_injured.lower().strip() in ['true', 'igen', 'yes', '1', 'i']
                        else:
                            has_injury = False
                        
                        if has_injury:
                            print("SÉRÜLÉS ÉSZLELVE!")
                            article_data['injury_data'] = result_data
                            injury_articles.append(article_data)
                            
                            # Részletes információk
                            print(f"   Játékos: {result_data.get('player_name', 'N/A')}")
                            print(f"   Csapat: {result_data.get('team', 'N/A')}")
                            print(f"   Sérülés: {result_data.get('injury_description', 'N/A')}")
                            print(f"   Felépülés: {result_data.get('recovery_time', 'N/A')}")
                            
                        else:
                            print("Nincs sérülés a cikkben")
                            article_data['injury_data'] = result_data
                            no_injury_articles.append(article_data)
                            
                except json.JSONDecodeError as e:
                    print(f"Az LLM válasz nem JSON formátumú: {e}")
                    print(f"Kapott válasz: {llm_result}")
                    # Manuális elemzés, ha nem JSON a válasz
                    if 'is_injured' in llm_result and 'true' in llm_result.lower():
                        print("SÉRÜLÉS ÉSZLELVE (manuális elemzés)")
                        injury_articles.append(article_data)
                    else:
                        print("Nincs sérülés a cikkben (manuális elemzés)")
                        no_injury_articles.append(article_data)
                except Exception as e:
                    print(f"Hiba az eredmény feldolgozásában: {e}")
                    error_articles.append(article_data)
            else:
                print("Hiba: Nem sikerült kapni választ az LLM-től")
                error_articles.append(article_data)
            
        for i, article in enumerate(injury_articles, 1):
            injury_data = article.get('injury_data', {})
            print(f"\n{i}. {article['title']}")
            
            injury_id = create_injury_article(
                url=article['url'],
                player_name=injury_data.get('player_name'),
                team_name=injury_data.get('team'),
                title=article.get('title'),
                published_date=self._parse_date(article.get('publish_date')),
                injury_type=injury_data.get('injury_description'),
                duration=injury_data.get('recovery_time')
            )
            print(injury_id)

if __name__ == "__main__":
    nso_scraper = NSOArticleScraper()
    nso_scraper.scrape_and_save_to_db()
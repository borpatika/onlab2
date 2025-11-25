from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from database.db_operations import (
    create_team, 
    create_player, 
    link_player_to_team,
    get_team_by_name,
    get_player_by_name_and_team_name
)


class TeamAndPlayersScraper(BaseScraper):
    """MLSZ Adatbank scraper NB1 csapatokhoz és játékosokhoz"""
    
    def __init__(self, season: str = "2024/2025", league_id: int = 31362):
        super().__init__()
        self.season = season
        self.league_id = league_id
    
    def scrape_all_teams(self, season: int = 65, round: int = 11) -> List[Dict]:
        """
        Összeszedi az összes csapat alapadatait az NB1-ből.
        
        Args:
            season: Évad ID (65 = 2024/2025)
            round: Forduló szám
            
        Returns:
            Lista dictekkel: [{"name": str, "url": str}, ...]
        """
        url = f"club/{season}/0/{self.league_id}/{round}/307004.html"  # DVSC oldal (de tartalmazza az összes csapatot)
        soup = self.get_soup(url)
        
        teams = []
        seen = set()
        
        # class="league_teams"-ben vannak a csapatok
        league_teams_div = soup.find("div", class_="league_teams")
        
        if not league_teams_div:
            print("Nincs league_teams div")
            return teams
        
        # Minden <a> tag egy csapat
        for team_link in league_teams_div.find_all("a", class_="league-team"):
            team_url = team_link.get("href")
            team_name = team_link.find("span").text.strip() if team_link.find("span") else ""
            
            if team_name not in seen:
                teams.append({
                    "name": team_name,
                    "url": team_url
                })
            seen.add(team_name)
            
            print(f"Csapat megtalálva: {team_name}")
        
        return teams
    
    def scrape_team_details(self, team_url: str) -> Dict:
        """
        Egy csapat részletes adatainak lekérése.
        
        Args:
            team_url: Csapat oldal URL (pl: https://adatbank.mlsz.hu/club/65/0/31362/11/307004.html)
            
        Returns:
            Dict: {"name": str, "address": str, "website": str, "players": List[Dict]}
        """
        soup = self.get_soup(team_url)

        # Csapat alapadatok - class="team_data"
        team_data = {}
        team_data_div = soup.find("div", class_="team_data")
        
        if team_data_div:
            # Név
            title = soup.find("h1", class_="container_title")
            team_data["name"] = title.text.strip() if title else ""
            
            # Cím
            address_div = team_data_div.find("div", class_="detail address")
            if address_div:
                address_data = address_div.find("div", class_="datas")
                team_data["address"] = address_data.text.strip() if address_data else ""
            
            # Weboldal
            web_div = team_data_div.find_all("div", class_="detail phone")
            for web in web_div:
                if web and "Web" in web.text:
                    web_link = web.find("a")
                    team_data["website"] = web_link.get("href") if web_link else ""
                else:
                    team_data["website"] = ""
        
        # Játékosok listája
        team_data["players"] = self._scrape_players_from_team_page(soup)
        
        return team_data
    
    def _scrape_players_from_team_page(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Játékosok kinyerése a csapat oldaláról.
        
        Args:
            soup: BeautifulSoup object a csapat oldaláról
            
        Returns:
            Lista: [{"name": str, "url": str, "birth_date": date}, ...]
        """
        players = []
        
        # class="content playersTab jatekos_panel inactive_panel"
        players_div = soup.find("div", id="jatekos_panel")

        if not players_div:
            return players
        
        # Táblázatban vannak a játékosok
        tbody = players_div.find("tbody", id="teamPlayers")
        if not tbody:
            return players

        for row in tbody.find_all("tr"):
            player_link = row.find("a")
            if not player_link:
                continue
            
            player_name = player_link.find("span", class_="playerName")
            player_url = player_link.get("href")
            
            birth_date = None
            if player_url:
                player_soup = self.get_soup(player_url)

                birth_td_label = player_soup.find("td", string="Születési idő")
                if birth_td_label:
                    birth_td = birth_td_label.find_next_sibling("td")
                    if birth_td:
                        birth_date = birth_td.text.strip()
            
            players.append({
                "name": player_name.text.strip() if player_name else "",
                "url": player_url,
                "birth_date": self._parse_date(birth_date)
            })
        
        return players
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Dátum string parser (pl: "1986. 12. 23.")
        
        Args:
            date_str: Dátum formátum: "YYYY. MM. DD."
            
        Returns:
            datetime object vagy None
        """
        try:
            cleaned = date_str.replace(".", "").replace(" ", "")
            return datetime.strptime(cleaned, "%Y%m%d").date()
        except:
            return None
    
    def save_teams_to_db(self):
        """
        Összeszedi az összes csapatot és menti az adatbázisba.
        """
        print("Csapatok letöltése...")
        teams_list = self.scrape_all_teams()
        
        for team_info in teams_list:
            print(f"\nFeldolgozás: {team_info['name']}")
            
            # Részletes adatok lekérése
            team_details = self.scrape_team_details(team_info["url"])
            
            # Csapat mentése
            team_id = get_team_by_name(team_details["name"])
            if not team_id:
                team_id = create_team(
                    name=team_details["name"],
                    address=team_details.get("address", ""),
                    website=team_details.get("website", "")
                )
                print(f"Csapat létrehozva: {team_details['name']} (ID: {team_id})")
            else:
                print(f"Csapat már létezik: {team_details['name']}")
            
            # Játékosok mentése
            for player_info in team_details["players"]:
                player_name = player_info["name"]
                birth_date = player_info.get("birth_date")
                
                existing_player = get_player_by_name_and_team_name(player_name, team_details["name"])
                
                if not existing_player:
                    player_id = create_player(
                        name=player_name,
                        birth_date=birth_date
                    )
                    print(f"Játékos létrehozva: {player_name}")
                    # Kapcsolat létrehozása
                    link_player_to_team(player_id, team_id)
                else:
                    print(f"Játékos már létezik: {player_name}")
                
        
        print("\nMinden csapat és játékos mentve az adatbázisba!")


# Használat
if __name__ == "__main__":
    scraper = TeamAndPlayersScraper()
    scraper.save_teams_to_db()
    
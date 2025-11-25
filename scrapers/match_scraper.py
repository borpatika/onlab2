from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from database.db_operations import (
    create_match,
    create_match_event,
    get_match_by_teams_date_and_round,
    get_player_by_name_and_team_name,
    get_team_by_name,
    create_or_update_player_stats
)

class MatchAndMatchEventScraper(BaseScraper):
    """Scraper az MLSZ adatbankból a meccsek és meccsesemények kinyerésére."""
    
    BASE_URL = "https://adatbank.mlsz.hu/league/65/0/31362/{}.html"

    def scrape_round(self, round_number: int) -> List[Dict]:
        """Egy adott forduló összes meccsének lekérése."""
        print(f"{round_number}. forduló letöltése...")
        url = self.BASE_URL.format(round_number)
        soup = self.get_soup(url)

        matches = []

        # A team-sorsolas boxon belül keresünk minden .schedule divet
        team_sorsolas_div = soup.find("div", class_="schedule_box")
        if not team_sorsolas_div:
            print("Nem található schedule_box ezen az oldalon.")
            return matches

        for match_div in team_sorsolas_div.find_all("div", class_="schedule"):
            result_div = match_div.find("div", class_="result-cont")
            if result_div:
                a_tag = result_div.find("a")
                match_url = a_tag["href"] if a_tag else ""
                if match_url == "":
                    break

            match_data = self._parse_match_from_div(match_div)
            if match_data:
                matches.append(match_data)

        return matches


    def _parse_match_from_div(self, div: BeautifulSoup) -> Optional[Dict]:
        """Egyetlen meccs adatainak kinyerése a listázó oldalról."""
        try:
            # Csapatnevek
            home_team_tag = div.find("div", class_="home_team")
            away_team_tag = div.find("div", class_="away_team")
            home_team = home_team_tag.get_text(strip=True) if home_team_tag else ""
            away_team = away_team_tag.get_text(strip=True) if away_team_tag else ""

            # Eredmény és meccs link
            result_div = div.find("div", class_="result-cont")
            result = ""
            match_url = ""
            if result_div:
                span = result_div.find("span", class_="schedule-points")
                result = span.get_text(strip=True) if span else ""
                a_tag = result_div.find("a")
                match_url = a_tag["href"] if a_tag else ""
                print(match_url)

            # Dátum + idő
            date_div = div.find("div", class_="team_sorsolas_date")
            date_text = date_div.get_text(strip=True) if date_div else ""

            # Stadion
            arena_div = div.find("div", class_="team_sorsolas_arena")
            arena = arena_div.get_text(strip=True) if arena_div else ""

            # Meccsdátum konvertálása
            match_date = self._parse_date(date_text)

            match_details = self.scrape_match_events(match_url)

            return {
                "home_team": home_team,
                "away_team": away_team,
                "home_score": result.split(" - ")[0],
                "away_score": result.split(" - ")[1],
                "arena": arena,
                "date": match_date,
                "url": match_url,
                "referee": match_details["referee"],
                "events": match_details["events"],
                "player_stats": match_details["player_stats"]
            }

        except Exception as e:
            print(f"Hiba egy meccs feldolgozásakor: {e}")
            return None


    def scrape_match_events(self, match_url: str) -> Dict:
        """Meccsesemények és játékos statisztikák lekérése a meccs részletes oldaláról."""
        if not match_url:
            return {"referee": None, "events": [], "player_stats": {}}

        soup = self.get_soup(match_url)
        events = []
        referee_name = None
        player_stats = {"home": {}, "away": {}}

        # Játékvezető kinyerése
        info_wrapper = soup.find("div", class_="team_info_wrapper")
        if info_wrapper:
            for detail in info_wrapper.find_all("div", class_="detail"):
                label_div = detail.find("div", class_="dataname")
                value_div = detail.find("div", class_="datas") or detail.find("div", class_="name datas")
                if not label_div or not value_div:
                    continue
                label = label_div.get_text(strip=True)
                value = value_div.get_text(strip=True)
                if "Játékvezető" in label and "Tartalék" not in label:
                    referee_name = value
                    break

        # Csapatok adatainak feldolgozása
        match_teams_div = soup.find("div", class_="match_teams_players")
        if match_teams_div:
            # Hazai csapat feldolgozása
            left_team_div = match_teams_div.find("div", id="left_team")
            if left_team_div:
                self._process_team_players(left_team_div, "home", events, player_stats["home"])

            # Vendég csapat feldolgozása
            right_team_div = match_teams_div.find("div", id="right_team")
            if right_team_div:
                self._process_team_players(right_team_div, "away", events, player_stats["away"])

        return {
            "referee": referee_name,
            "events": events,
            "player_stats": player_stats
        }

    def _process_team_players(self, team_div: BeautifulSoup, team_side: str, events: List, player_stats: Dict):
        """Egy csapat játékosainak feldolgozása."""
        
        # Kezdő játékosok
        main_table = team_div.find("table")
        if main_table:
            for row in main_table.find_all("tr", class_="template-tr-selectable"):
                self._process_player_row(row, team_side, events, player_stats, is_starter=True)
        
        # Cserék
        replacement_table = team_div.find("table", class_="replacement")
        if replacement_table:
            for row in replacement_table.find_all("tr", class_="template-tr-selectable"):
                self._process_player_row(row, team_side, events, player_stats, is_starter=False)

    def _process_player_row(self, row: BeautifulSoup, team_side: str, events: List, player_stats: Dict, is_starter: bool):
        """Egy játékos sor feldolgozása."""
        try:
            # Játékos nevének kinyerése
            name_td = row.find("td", class_="match_players_name")
            if not name_td:
                return
                
            player_links = name_td.find_all("a")
            if not player_links:
                return
                
            player_name = player_links[0].get_text(strip=True)
            if not player_name:
                return

            # Kártyák és események cellája
            cards_td = row.find("td", class_="match_players_cards")
            
            # Játszott percek számítása
            minutes_played = self._calculate_minutes_played(cards_td, is_starter)
            
            # Statisztika inicializálása
            stats = {
                "minutes_played": minutes_played,
                "goals": 0,
                "own_goals": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "is_starter": is_starter
            }

            # Események feldolgozása
            if cards_td:
                for span in cards_td.find_all("span"):
                    style = span.get("style", "")
                    minute_text = span.get_text(strip=True).replace("'", "")
                    minute = ''.join(filter(str.isdigit, minute_text))
                    
                    if not minute:
                        continue
                    
                    # Esemény típusának meghatározása
                    if "event_goal.png" in style or "event_penalty_goal.png" in style:
                        event_type = "goal"
                        stats["goals"] += 1
                        events.append({
                            "minute": minute,
                            "player": player_name,
                            "type": event_type,
                            "team_side": team_side
                        })
                        
                    elif "event_own_goal.png" in style:
                        event_type = "own_goal"
                        stats["own_goals"] += 1
                        events.append({
                            "minute": minute,
                            "player": player_name,
                            "type": event_type,
                            "team_side": team_side
                        })

                    elif "event_yellowcard.png" in style:
                        event_type = "yellow_card"
                        stats["yellow_cards"] += 1
                        events.append({
                            "minute": minute,
                            "player": player_name,
                            "type": event_type,
                            "team_side": team_side
                        })
                        
                    elif "event_redcard.png" in style:
                        event_type = "red_card"
                        stats["red_cards"] += 1
                        events.append({
                            "minute": minute,
                            "player": player_name,
                            "type": event_type,
                            "team_side": team_side
                        })
                        
                    elif "event_swap.png" in style:
                        event_type = "substitution"
                        events.append({
                            "minute": minute,
                            "player": player_name,
                            "type": event_type,
                            "team_side": team_side,
                            "is_sub_in": not is_starter  # Ha csere, akkor bejött, ha kezdő, akkor kiment
                        })

            # Statisztika mentése
            player_stats[player_name] = stats
            
        except Exception as e:
            print(f"Hiba játékos feldolgozásakor: {e}")

    def _calculate_minutes_played(self, cards_td: BeautifulSoup, is_starter: bool) -> int:
        """Játszott percek számítása."""
        if not cards_td:
            return 90 if is_starter else 0
        
        # Csere események keresése
        substitution_spans = []
        for span in cards_td.find_all("span"):
            style = span.get("style", "")
            if "event_swap.png" in style:
                minute_text = span.get_text(strip=True).replace("'", "")
                minute = ''.join(filter(str.isdigit, minute_text))
                if minute:
                    substitution_spans.append(int(minute))
        
        if not substitution_spans:
            return 90 if is_starter else 0
        
        if is_starter:
            # Kezdő játékos: kicserélték, annyi percet játszott
            return min(substitution_spans)
        else:
            # Csere játékos: bekerült, 90 - bekerülési perc
            substitution_time = min(substitution_spans)
            return 90 - substitution_time

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Formátum: '2025. 07. 25.20:00' - returns string in 'YYYY-MM-DD' format"""
        try:
            normalized = date_str.replace('. ', '.')
            date_only = normalized[:10]
            date_obj = datetime.strptime(date_only, "%Y.%m.%d").date()
            return date_obj.isoformat()
        except Exception as e:
            print(f"Dátum parse hiba: '{date_str}' - {e}")
            return None


    def save_matches_to_db(self):
        for round_number in range(1, 34):
            matches = self.scrape_round(round_number)
            for m in matches:
                home_team_name = m["home_team"]
                away_team_name = m["away_team"]

                home_team_id = get_team_by_name(home_team_name)
                away_team_id = get_team_by_name(away_team_name)

                if home_team_id is None or away_team_id is None:
                    print(f"Csapat nem található: {home_team_name} vagy {away_team_name}")
                    continue

                existing_match = get_match_by_teams_date_and_round(
                    home_team_id=home_team_id,
                    away_team_id=away_team_id, 
                    date=m["date"],
                    round_num=round_number
                )
                
                if existing_match:
                    print(f"Meccs már létezik: {home_team_name} - {away_team_name}")
                    continue

                match_id = create_match(
                    season="2024/2025",
                    round_num=round_number,
                    date=m["date"],
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    home_score=m["home_score"],
                    away_score=m["away_score"], 
                    stadium=m["arena"],
                    referee=m["referee"]
                )
                print(f"Meccs mentve: {home_team_name} - {away_team_name}")

                for e in m["events"]:
                    team_name = home_team_name if e["team_side"] == "home" else away_team_name
                    team_id = get_team_by_name(team_name)
                    player_id = get_player_by_name_and_team_name(e["player"], team_name)

                    if not player_id:
                        print(f"Játékos nem található: {e['player']} ({team_name})")
                        continue

                    create_match_event(
                        match_id=match_id,
                        event_type=e["type"],
                        minute=e["minute"],
                        player_id=player_id,
                        team_id=team_id,
                    )
                    print(f"Esemény: {e['minute']}' {e['player']} ({e['type']})")

                self._save_player_stats_for_match(m, home_team_name, away_team_name, match_id)


    def _save_player_stats_for_match(self, match_data: Dict, home_team_name: str, away_team_name: str, match_id: int):
        """Játékos statisztikák mentése egy meccshez."""
        print(f"Játékos statisztikák mentése...")
        
        # Hazai csapat statisztikái
        for player_name, stats in match_data["player_stats"]["home"].items():
            self._save_single_player_stats(player_name, home_team_name, stats, match_id)
        
        # Vendég csapat statisztikái
        for player_name, stats in match_data["player_stats"]["away"].items():
            self._save_single_player_stats(player_name, away_team_name, stats, match_id)


    def _save_single_player_stats(self, player_name: str, team_name: str, stats: Dict, match_id: int):
        """Egy játékos statisztikáinak mentése."""
        try:
            player_id = get_player_by_name_and_team_name(player_name, team_name)
            if not player_id:
                print(f"Játékos nem található statisztikához: {player_name} ({team_name})")
                return
            
            team_id = get_team_by_name(team_name)
            if not team_id:
                print(f"Csapat nem található: {team_name}")
                return
                
            matches_played = 1
            goals = stats.get("goals", 0)
            own_goals = stats.get("own_goals", 0)
            yellow_cards = stats.get("yellow_cards", 0) 
            red_cards = stats.get("red_cards", 0)
            minutes_played = stats.get("minutes_played", 0)
            
            create_or_update_player_stats(
                player_id=player_id,
                team_id=team_id,
                matches_played=matches_played,
                goals=goals,
                own_goals=own_goals,
                yellow_cards=yellow_cards,
                red_cards=red_cards,
                minutes_played=minutes_played
            )
            
            print(f"Statisztika mentve: {player_name} - +{goals}gól, +{own_goals}öngól, +{minutes_played}perc, +{yellow_cards}sárga, +{red_cards}piros")
            
        except Exception as e:
            print(f"Hiba a statisztika mentésénél ({player_name}): {e}")

if __name__ == "__main__":
    scraper = MatchAndMatchEventScraper()
    scraper.save_matches_to_db()
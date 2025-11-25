from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from database.db_operations import (
    create_or_update_standing,
    get_team_by_name,
)

class StandingScraper(BaseScraper):
    """Scraper az MLSZ adatbankból a tabella adatainak kinyerésére."""

    BASE_URL = "https://adatbank.mlsz.hu/league/65/0/31362/{}.html"

    def scrape_round(self, round_number: int) -> List[Dict]:
        """Egy adott forduló tabellájának lekérése."""
        print(f"{round_number}. forduló tabellájának letöltése...")
        url = self.BASE_URL.format(round_number)
        soup = self.get_soup(url)

        standings = []

        team_sorsolas_div = soup.find("div", class_="schedule_box")
        if not team_sorsolas_div:
            print("Nem található schedule_box ezen az oldalon.")
            return standings

        # Megnézzük az első meccs eredményét
        first_match_div = team_sorsolas_div.find("div", class_="schedule")
        if first_match_div:
            result_div = first_match_div.find("div", class_="result-cont")
            if result_div:
                a_tag = result_div.find("a")
                match_url = a_tag["href"] if a_tag else ""
                # Ha nincs match_url, akkor még nincs eredmény -> nincs tabella frissítés, mert a forduló még nem lett lejátszva
                if match_url == "":
                    print(f"{round_number}. forduló még nem játszották le, tabella nem frissült")
                    return standings
            else:
                print(f"{round_number}. forduló még nem játszották le (nincs result-div)")
                return standings
        else:
            print(f"{round_number}. forduló még nem játszották le (nincs match-div)")
            return standings

        # A team_tabella div-en belül keresünk
        team_tabella_div = soup.find("div", class_="team_tabella")
        if not team_tabella_div:
            print("Nem található team_tabella ezen az oldalon.")
            return standings

        # A fő tabella panel
        tabella_panel = team_tabella_div.find("div", id="tabella_panel")
        if not tabella_panel:
            print("Nem található tabella_panel.")
            return standings

        # Tábla sorok feldolgozása
        table_body = tabella_panel.find("tbody", id="tableContent")
        if not table_body:
            print("Nem található tableContent tbody.")
            return standings

        for row in table_body.find_all("tr", class_="template-tr-selectable"):
            standing_data = self._parse_standing_row(row, round_number)
            if standing_data:
                standings.append(standing_data)

        return standings

    def _parse_standing_row(self, row: BeautifulSoup, round_number: int) -> Optional[Dict]:
        """Egyetlen tabella sor feldolgozása."""
        try:
            # Pozíció
            position_td = row.find("td")
            position = position_td.get_text(strip=True) if position_td else ""

            # Csapat neve
            tds = row.find_all("td")
            team_name = ""
            if len(tds) > 2:
                team_name = tds[2].get_text(strip=True)
                team_name = team_name.replace('\u00a0', ' ')
                team_name = ' '.join(team_name.split())

            # Statisztikai adatok
            # Mérkőzések száma (4. td)
            matches_played = tds[3].get_text(strip=True) if len(tds) > 3 else "0"

            # Győzelmek (5. td)
            wins = tds[4].get_text(strip=True) if len(tds) > 4 else "0"

            # Döntetlenek (6. td)
            draws = tds[5].get_text(strip=True) if len(tds) > 5 else "0"

            # Vereségek (7. td)
            losses = tds[6].get_text(strip=True) if len(tds) > 6 else "0"

            # Lőtt gólok (8. td)
            goals_for = tds[7].get_text(strip=True) if len(tds) > 7 else "0"

            # Kapott gólok (9. td)
            goals_against = tds[8].get_text(strip=True) if len(tds) > 8 else "0"

            # Gólkülönbség (10. td)
            goal_difference = "0"
            if len(tds) > 9:
                gk_td = row.find("td", class_="remove700")
                if gk_td:
                    goal_difference = gk_td.get_text(strip=True)

            # Pontok (11. td)
            points = tds[10].get_text(strip=True) if len(tds) > 10 else "0"

            return {
                "round_number": round_number,
                "position": int(position) if position.isdigit() else 0,
                "team_name": team_name,
                "matches_played": int(matches_played) if matches_played.isdigit() else 0,
                "wins": int(wins) if wins.isdigit() else 0,
                "draws": int(draws) if draws.isdigit() else 0,
                "losses": int(losses) if losses.isdigit() else 0,
                "goals_for": int(goals_for) if goals_for.isdigit() else 0,
                "goals_against": int(goals_against) if goals_against.isdigit() else 0,
                "goal_difference": int(goal_difference) if goal_difference.lstrip('-').isdigit() else 0,
                "points": int(points) if points.isdigit() else 0,
            }

        except Exception as e:
            print(f"Hiba egy tabella sor feldolgozásakor: {e}")
            return None

    def scrape_all_rounds(self) -> Dict[int, List[Dict]]:
        """Az összes forduló tabellájának lekérése."""
        all_standings = {}

        for round_number in range(1, 34):  # 33 forduló az NB1-ben
            standings = self.scrape_round(round_number)
            if standings:
                all_standings[round_number] = standings
                print(f"{round_number}. forduló tabellája sikeresen letöltve ({len(standings)} csapat)")
            else:
                print(f"{round_number}. forduló még nincs lejátszva")
                break

        return all_standings

    def save_standings_to_db(self):
        """Az összes forduló tabellájának letöltése és adatbázisba mentése."""
        all_standings = self.scrape_all_rounds()

        for round_number, standings in all_standings.items():
            for standing in standings:
                team_id = get_team_by_name(str(standing.get('team_name')))
                print(f"TEAM ID: {team_id}")

                if team_id:
                    create_or_update_standing(
                        season="2025/26",
                        team_id=team_id,
                        round_num=round_number,
                        position=standing["position"],
                        matches_played=standing["matches_played"],
                        wins=standing["wins"],
                        draws=standing["draws"],
                        losses=standing["losses"],
                        goals_for=standing["goals_for"],
                        goals_against=standing["goals_against"],
                        goal_difference=standing["goal_difference"],
                        points=standing["points"]
                    )
                    print(f"Tabella mentve: {standing['position']}. {standing['team_name']} ({standing['points']} pont)")
                else:
                    print(f"Csapat nem található: {standing['team_name']}")


if __name__ == "__main__":
    scraper = StandingScraper()
    scraper.save_standings_to_db()
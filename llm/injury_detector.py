import os
import requests

class LLMInjuryDetector:
    def __init__(self, model_name="llama3:latest", ollama_url=None):
        self.model_name = model_name
        self.ollama_url = ollama_url or os.getenv('OLLAMA_URL', 'http://ollama:11434/api/generate')

    def query_ollama(self, prompt: str) -> str:
        """
        Lekéri az Ollama-tól a választ a prompt alapján.
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            print(f"Hiba történt az Ollama lekérdezése során: {e}")
            return ""


    def build_prompt_from_article(self, article_text: str) -> str:
        """
        Felépít egy elemző promptot az adott cikk szövegéből.
        Törekszik arra, hogy a válasz csak egy parse-olható JSON dict legyen a kívánt adatokkal.
        """
        prompt = f"""
            Olvasd el az alábbi sporthír cikket:

            ---
            {article_text}
            ---

            Feladatod:
            1. Állapítsd meg, hogy írnak-e a cikkben egy játékos sérüléséről.
            2. Ha igen:
            - Add meg a játékos nevét.
            - Írd le, milyen sérülést szenvedett.
            - Add meg, mennyi időre jósolják a felépülést (ha le van írva).
            - Ha szerepel a cikkben, add meg a játékos csapatát is. Ha nincs említve, hagyd üresen.
            3. Ha nem írják le konkrétan a felépülés idejét:
            - Adj becslést arra, mennyi idő lehet a felépülés.
            4. A választ kizárólag egy JSON objektum formájában add vissza az alábbi struktúrában, minden egyéb szöveg nélkül:

            {{
            "is_injured": true/false,
            "player_name": "...",
            "team": "...",
            "injury_description": "...",
            "recovery_time": "...",
            "comment": "..."
            }}

            Ne adj hozzá semmilyen magyarázatot vagy szöveget, csak a JSON-t! Ha nincs pontos info valamiről, például csapatról, csak egy "" legyen az értéke. És a válaszodban ne ismételd meg a cikk szövegét, csak a kért információkat add meg!
            Az alábbi csapatok játszanak az NB1-ben: DVSC, DVTK, ETO FC, Ferencvárosi TC, Kisvárda Master Good, Kolorcity Kazincbarcika SC, MTK Budapest, Nyíregyháza Spartacus FC, Paksi FC, Puskás Akadémia FC, Újpest FC, ZTE FC.
            """
        return prompt


# Példa használat:
if __name__ == "__main__":
    scraper = LLMInjuryDetector()

    test_cikk_szoveg = """
    A hétvégén újabb izgalmas mérkőzéseket láthattak a szurkolók az NB I-ben...
    Kis Tibor egy szerencsétlen ütközés során a bokájához kapott, várhatóan 2 hét a felépülése.
    """

    prompt = scraper.build_prompt_from_article(test_cikk_szoveg)
    result = scraper.query_ollama(prompt)
    print(result)

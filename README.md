# MLSZ Webscraper – NB I Adatgyűjtő Rendszer

Ez a projekt automatizált scraping rendszert biztosít az MLSZ adatbank és a Nemzeti Sport oldalakról.  
A rendszer begyűjti és adatbázisban tárolja a csapatok, játékosok, mérkőzések, tabellaadatok és sérüléses hírek adatait.

---

## Indítás

A projekt gyökerében futtasd:

docker-compose up -d --build

Ez elindítja:

- PostgreSQL adatbázist
- Ollama LLM szervert
- Scraper szolgáltatást (cron időzítéssel)

---

## Leállítás

Konténerek leállítása:

docker-compose down

Konténerek + volume-ok törlése (adatbázis is törlődik):

docker-compose down -v

---

## Adatbázis ellenőrzése

Belépés a PostgreSQL konténerbe:

docker exec -it mlsz-postgres psql -U mlsz_user -d mlsz_db

Táblák listázása:

\dt

A teams tábla megtekintése:

SELECT * FROM teams;

Rekordszám ellenőrzése:

SELECT COUNT(*) FROM teams;

Kilépés:

\q

Egyszerűbben:

docker exec -it mlsz-postgres psql -U mlsz_user -d mlsz_db -c "SELECT * FROM teams;"

docker exec -it mlsz-postgres psql -U mlsz_user -d mlsz_db -c "SELECT COUNT(*) FROM teams;"

---

## Logok megtekintése

A scraper logjai a logs/ mappába kerülnek.

Host gépről:

tail -f logs/scraper.log

Konténeren belül:

docker exec -it mlsz-scraper bash  
tail -f /var/log/scraper.log

---

## Cron feladatok

A scraper konténerben a cron ütemezetten futtatja a scrapereket:

- Vasárnap 01:00 – meccsek
- Vasárnap 02:00 – tabella
- Minden második nap 03:00 – cikkek

--

## Megjegyzés

A rendszer egy RTX 5070 Ti GPU-val és 32 GB RAM-mal lett tesztelve.
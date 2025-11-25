#!/bin/bash
set -e

echo "MLSZ Scraper Container elindítása..."

# Várakozás az adatbázis elérhetőségére
echo "Adatbázis kapcsolat ellenőrzése..."
while ! pg_isready -h postgres -p 5432 -U mlsz_user > /dev/null 2>&1; do
  echo "Adatbázis még nem elérhető, várakozás..."
  sleep 2
done
echo "Adatbázis elérhető"

# Várakozás az Ollama elérhetőségére
echo "Ollama kapcsolat ellenőrzése..."
while ! curl -f http://ollama:11434/api/tags > /dev/null 2>&1; do
  echo "Ollama még nem elérhető, várakozás..."
  sleep 5
done
echo "Ollama elérhető"

# Ollama model betöltése (háttérben, ne blokkolja)
echo "Ollama model betöltése (háttérben)..."
curl -X POST http://ollama:11434/api/pull -d '{"name": "llama3:latest"}' > /dev/null 2>&1 &

# Cron szolgáltatás indítása
echo "Cron indítása..."
service cron start

# Log fájlok létrehozása
touch /var/log/scraper.log
touch /var/log/cron.log

# Kezdeti scraperek futtatása
if [ "$RUN_INITIAL_SCRAPERS" = "true" ]; then
    echo "TELJES RENDSZER SETUP INDÍTÁSA..."
    cd /app && python main.py --setup >> /var/log/scraper.log 2>&1
    echo "TELJES RENDSZER SETUP BEFEJEZVE" >> /var/log/scraper.log
fi

echo "Container készen áll"
echo "Logok követése:"
echo "- tail -f /var/log/scraper.log"
echo "- tail -f /var/log/cron.log"

# Container életben tartása
tail -f /var/log/scraper.log /var/log/cron.log
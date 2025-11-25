FROM python:3.11-slim

WORKDIR /app

# Rendszer függőségek
RUN apt-get update && apt-get install -y \
    cron \
    postgresql-client \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Python függőségek
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Alkalmazás másolása
COPY . .

# Sorvége karakterek javítása Windows -> Linux
RUN dos2unix /app/crontab && \
    dos2unix /app/docker-entrypoint.sh

# Cron beállítása
COPY crontab /etc/cron.d/mlsz-scraper
RUN chmod 0644 /etc/cron.d/mlsz-scraper \
    && crontab /etc/cron.d/mlsz-scraper

# Log könyvtár
RUN mkdir -p /var/log

# Kezdő szkript
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
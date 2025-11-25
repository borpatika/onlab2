#!/usr/bin/env python3
"""
MLSZ Scraper Main Workflow
Futtatás: python main.py [options]
"""

import argparse
import sys
import logging

from scrapers.team_scraper import TeamAndPlayersScraper
from scrapers.match_scraper import MatchAndMatchEventScraper
from scrapers.standing_scraper import StandingScraper
from scrapers.nso_scraper import NSOArticleScraper
from database.database import init_db, drop_db

# Logging beállítás
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log')
    ]
)

def init_database():
    """Adatbázis inicializálása"""
    logging.info("Adatbázis inicializálása...")
    init_db()
    logging.info("Adatbázis kész")

def reset_database():
    """Adatbázis teljes resetelése"""
    logging.warning("ADATBÁZIS TÖRLÉSE...")
    drop_db()
    logging.info("Adatbázis újrainicializálása...")
    init_db()
    logging.info("Adatbázis resetelve")

def run_teams():
    """Csapatok és játékosok scrapelése"""
    logging.info("Csapatok és játékosok scrapelése...")
    scraper = TeamAndPlayersScraper()
    scraper.save_teams_to_db()
    logging.info("Csapatok és játékosok mentve")

def run_matches():
    """Meccsek és események scrapelése"""
    logging.info("Meccsek és események scrapelése...")
    scraper = MatchAndMatchEventScraper()
    scraper.save_matches_to_db()
    logging.info("Meccsek és események mentve")

def run_standings():
    """Tabella scrapelése"""
    logging.info("Tabella scrapelése...")
    scraper = StandingScraper()
    scraper.save_standings_to_db()
    logging.info("Tabella mentve")

def run_articles():
    """Cikkek scrapelése"""
    logging.info("Cikkek scrapelése...")
    scraper = NSOArticleScraper()
    scraper.scrape_and_save_to_db()
    logging.info("Cikkek mentve")

def run_all():
    """Összes scraper futtatása"""
    logging.info("ÖSSZES SCRAPER INDÍTÁSA")
    
    run_teams()
    run_matches() 
    run_standings()
    run_articles()
    
    logging.info("ÖSSZES SCRAPER BEFEJEZVE")

def run_complete_setup():
    """Teljes setup: adatbázis + összes scraper"""
    logging.info("TELJES RENDSZER SETUP INDÍTÁSA")
    init_database()
    run_all()
    logging.info("TELJES RENDSZER SETUP BEFEJEZVE")

def main():
    parser = argparse.ArgumentParser(description='MLSZ Scraper Suite')
    
    # Fő opciók
    parser.add_argument('--teams', action='store_true', help='Csapatok scrapelése')
    parser.add_argument('--matches', action='store_true', help='Meccsek scrapelése')
    parser.add_argument('--standings', action='store_true', help='Tabella scrapelése')
    parser.add_argument('--articles', action='store_true', help='Cikkek scrapelése')
    parser.add_argument('--all', action='store_true', help='Összes scraper futtatása')
    
    # Adatbázis opciók
    parser.add_argument('--init-db', action='store_true', help='Adatbázis inicializálása')
    parser.add_argument('--reset-db', action='store_true', help='Adatbázis teljes resetelése')
    parser.add_argument('--setup', action='store_true', help='Teljes setup: adatbázis + összes scraper')
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    try:
        if args.reset_db:
            reset_database()
            return
            
        if args.init_db:
            init_database()
            if not any([args.teams, args.matches, args.standings, args.articles, args.all, args.setup]):
                return
        
        # Setup - adatbázis + összes scraper
        if args.setup:
            run_complete_setup()
            return
            
        # Scraperek
        if args.all:
            run_all()
        else:
            if args.teams:
                run_teams()
            if args.matches:
                run_matches()
            if args.standings:
                run_standings()
            if args.articles:
                run_articles()
                
    except Exception as e:
        logging.error(f"Hiba történt: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
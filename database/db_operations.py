from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from .models import Team, Player, TeamPlayer, Match, MatchEvent, Standing, PlayerStats, InjuryArticle
from .database import get_db_session


# ============== TEAM OPERATIONS ==============

def create_team(name, address=None, website=None):
    """Create a new team"""
    with get_db_session() as session:
        existing = session.query(Team).filter_by(name=name).first()
        if existing:
            print(f"Csapat már létezik: {name} (ID: {existing.team_id})")
            return None
        
        team = Team(name=name, address=address, website=website)
        session.add(team)
        session.flush()
        return team.team_id


def get_team_by_name(name):
    """Get team ID by name (case-insensitive, trimmed)"""
    with get_db_session() as session:
        normalized_name = name.upper().strip()

        team = session.query(Team).filter(
            func.upper(func.trim(Team.name)) == normalized_name
        ).first()
        
        return team.team_id if team else None


def get_all_teams():
    """Get all teams"""
    with get_db_session() as session:
        return session.query(Team).all()


# ============== PLAYER OPERATIONS ==============

def create_player(name, birth_date=None, is_injured=False):
    """Create a new player"""
    with get_db_session() as session:
        player = Player(name=name, birth_date=birth_date, is_injured=is_injured)
        session.add(player)
        session.flush()
        return player.player_id


def get_player_by_name_and_team_name(player_name, team_name):
    """Get player ID by name and team name (case-insensitive)"""
    with get_db_session() as session:
        player = session.query(Player)\
            .join(TeamPlayer)\
            .join(Team)\
            .filter(func.upper(Player.name) == func.upper(player_name))\
            .filter(func.upper(Team.name) == func.upper(team_name))\
            .first()
        return player.player_id if player else None


def update_player_injury_status(player_id, is_injured):
    """Update player injury status"""
    with get_db_session() as session:
        player = session.query(Player).filter_by(player_id=player_id).first()
        if player:
            player.is_injured = is_injured
            return True
        return False


def get_injured_players():
    """Get all injured players"""
    with get_db_session() as session:
        return session.query(Player).filter_by(is_injured=True).all()
    

def get_players_by_team_name(team_name):
    """Get all players for a team by team name"""
    with get_db_session() as session:
        return session.query(Player)\
            .join(TeamPlayer)\
            .join(Team)\
            .filter(Team.name == team_name)\
            .all()


# ============== TEAM-PLAYER OPERATIONS ==============

def link_player_to_team(player_id, team_id):
    """Link a player to a team"""
    with get_db_session() as session:
        # Check if link already exists
        existing = session.query(TeamPlayer).filter_by(
            player_id=player_id, team_id=team_id
        ).first()
        if not existing:
            team_player = TeamPlayer(player_id=player_id, team_id=team_id)
            session.add(team_player)
            return True
        return False


def get_players_by_team(team_id):
    """Get all players for a team"""
    with get_db_session() as session:
        return session.query(Player).join(TeamPlayer).filter(
            TeamPlayer.team_id == team_id
        ).all()


# ============== MATCH OPERATIONS ==============

def create_match(season, round_num, date, home_team_id, away_team_id, 
                 home_score=None, away_score=None, stadium=None, referee=None):
    """Create a new match"""
    with get_db_session() as session:
        match = Match(
            season=season,
            round=round_num,
            date=date,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_score=home_score,
            away_score=away_score,
            stadium=stadium,
            referee=referee
        )
        session.add(match)
        session.flush()
        return match.match_id


def get_matches_by_round(season, round_num):
    """Get all matches for a specific round"""
    with get_db_session() as session:
        return session.query(Match).filter_by(season=season, round=round_num).all()
    

def get_match_by_teams_date_and_round(home_team_id: int, away_team_id: int, date: str, round_num: int):
    """Get match by team IDs, date and round (duplicate check)"""
    with get_db_session() as session:
        return session.query(Match)\
            .filter_by(
                date=date,
                round=round_num,
                home_team_id=home_team_id,
                away_team_id=away_team_id
            )\
            .first()


# ============== MATCH EVENT OPERATIONS ==============

def create_match_event(match_id, event_type, minute, player_id=None, team_id=None):
    """Create a match event"""
    with get_db_session() as session:
        event = MatchEvent(
            match_id=match_id,
            event_type=event_type,
            minute=minute,
            player_id=player_id,
            team_id=team_id
        )
        session.add(event)
        return True


# ============== STANDING OPERATIONS ==============

def create_or_update_standing(season, round_num, team_id, matches_played, wins, 
                               draws, losses, goals_for, goals_against, goal_difference, points, position):
    """Create or update team standing"""
    with get_db_session() as session:
        standing = session.query(Standing).filter_by(
            season=season, round=round_num, team_id=team_id
        ).first()
        
        if standing:
            # Update existing
            standing.matches_played = matches_played
            standing.wins = wins
            standing.draws = draws
            standing.losses = losses
            standing.goals_for = goals_for
            standing.goals_against = goals_against
            standing.goal_difference = goal_difference
            standing.points = points
            standing.position = position
        else:
            # Create new
            standing = Standing(
                season=season,
                round=round_num,
                team_id=team_id,
                matches_played=matches_played,
                wins=wins,
                draws=draws,
                losses=losses,
                goals_for=goals_for,
                goals_against=goals_against,
                goal_difference = goal_difference,
                points=points,
                position=position
            )
            session.add(standing)


def get_standings(season, round_num):
    """Get standings for a specific round"""
    with get_db_session() as session:
        return session.query(Standing).filter_by(
            season=season, round=round_num
        ).order_by(Standing.position).all()


# ============== PLAYER STATS OPERATIONS ==============

def create_or_update_player_stats(player_id, team_id, matches_played, goals, own_goals, 
                                   yellow_cards, red_cards, minutes_played):
    """Create or update player statistics"""
    with get_db_session() as session:
        stat = session.query(PlayerStats).filter_by(
            player_id=player_id, team_id=team_id
        ).first()
        
        if stat:
            # Update existing
            stat.matches_played = stat.matches_played + matches_played
            stat.goals = stat.goals + goals
            stat.own_goals = stat.own_goals + own_goals
            stat.yellow_cards = stat.yellow_cards + yellow_cards
            stat.red_cards = stat.red_cards + red_cards
            stat.minutes_played = stat.minutes_played + minutes_played
        else:
            # Create new
            stat = PlayerStats(
                player_id=player_id,
                team_id=team_id,
                matches_played=matches_played,
                goals=goals,
                own_goals=own_goals,
                yellow_cards=yellow_cards,
                red_cards=red_cards,
                minutes_played=minutes_played
            )
            session.add(stat)


# ============== INJURY ARTICLE OPERATIONS ==============

def create_injury_article(url, player_name=None, team_name=None, title=None, published_date=None, injury_type=None, duration=None):
    """Create a new injury article (returns None if URL already exists)"""
    with get_db_session() as session:
        try:
            # Check if URL already exists
            existing = session.query(InjuryArticle).filter_by(url=url).first()
            if existing:
                return None
            
            player_id = None
            
            # Normalize names to uppercase
            if player_name is not None and team_name is not None:
                player_name_upper = player_name.upper().strip()
                team_name_upper = team_name.upper().strip()
                
                # Find player by name and team
                player_id = get_player_by_name_and_team_name(player_name_upper, team_name_upper)

                if not player_id and ' ' in player_name_upper:
                    name_parts = player_name_upper.split()
                    if len(name_parts) == 2:
                        reversed_name = f"{name_parts[1]} {name_parts[0]}"
                        player_id = get_player_by_name_and_team_name(reversed_name, team_name_upper)
                
            player_id = player_id if player_id else None
            
            # Determine if manual check is needed
            needs_manual_check = player_id is None
            
            injury_article = InjuryArticle(
                player_id=player_id,
                url=url,
                title=title,
                published_date=published_date,
                injury_type=injury_type,
                injury_start=published_date,
                duration=duration,
                needs_manual_check=needs_manual_check
            )
            session.add(injury_article)
            session.flush()

            if player_id:
                update_player_injury_status(player_id, True)
            
            print(f"Cikk mentve (ID: {injury_article.id}), "
                  f"Manuális ellenőrzés szükséges: {needs_manual_check}")
            
            return injury_article.id
        except IntegrityError:
            return None


def get_injury_article_by_url(url):
    """Get injury article by URL"""
    with get_db_session() as session:
        return session.query(InjuryArticle).filter_by(url=url).first()


def update_injury_article(injury_article_id, **kwargs):
    """Update an existing injury article"""
    with get_db_session() as session:
        injury_article = session.query(InjuryArticle).filter_by(id=injury_article_id).first()
        if injury_article:
            for key, value in kwargs.items():
                if hasattr(injury_article, key):
                    setattr(injury_article, key, value)
            return True
        return False


def get_injuries_for_player(player_id):
    """Get all injury records for a player"""
    with get_db_session() as session:
        return session.query(InjuryArticle).filter(
            InjuryArticle.player_id == player_id
        ).all()

from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone


Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    
    team_id = Column(Integer, primary_key=True)
    name = Column(String(100))
    address = Column(String(70))
    website = Column(String(255))
    
    # Relationships
    home_matches = relationship('Match', foreign_keys='Match.home_team_id', back_populates='home_team')
    away_matches = relationship('Match', foreign_keys='Match.away_team_id', back_populates='away_team')
    team_players = relationship('TeamPlayer', back_populates='team')
    standings = relationship('Standing', back_populates='team')
    player_stats = relationship('PlayerStats', back_populates='team')
    match_events = relationship('MatchEvent', back_populates='team')
    
    def __repr__(self):
        return f"<Team(name={self.name})>"


class Player(Base):
    __tablename__ = 'players'
    
    player_id = Column(Integer, primary_key=True)
    name = Column(String(100))
    birth_date = Column(Date)
    is_injured = Column(Boolean, default=False)
    
    # Relationships
    team_players = relationship('TeamPlayer', back_populates='player')
    match_events = relationship('MatchEvent', back_populates='player')
    player_stats = relationship('PlayerStats', back_populates='player')
    injury_articles = relationship('InjuryArticle', back_populates='player')
    
    def __repr__(self):
        return f"<Player(name={self.name}, injured={self.is_injured})>"


class TeamPlayer(Base):
    __tablename__ = 'team_players'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.team_id'))
    player_id = Column(Integer, ForeignKey('players.player_id'))
    
    # Relationships
    team = relationship('Team', back_populates='team_players')
    player = relationship('Player', back_populates='team_players')
    
    def __repr__(self):
        return f"<TeamPlayer(team_id={self.team_id}, player_id={self.player_id})>"


class Match(Base):
    __tablename__ = 'matches'
    
    match_id = Column(Integer, primary_key=True)
    season = Column(String(20))
    round = Column(Integer)
    date = Column(Date)
    home_team_id = Column(Integer, ForeignKey('teams.team_id'))
    away_team_id = Column(Integer, ForeignKey('teams.team_id'))
    home_score = Column(Integer)
    away_score = Column(Integer)
    stadium = Column(String(100))
    referee = Column(String(100))
    
    # Relationships
    home_team = relationship('Team', foreign_keys=[home_team_id], back_populates='home_matches')
    away_team = relationship('Team', foreign_keys=[away_team_id], back_populates='away_matches')
    match_events = relationship('MatchEvent', back_populates='match')
    
    def __repr__(self):
        return f"<Match(round={self.round}, date={self.date})>"


class MatchEvent(Base):
    __tablename__ = 'match_events'
    
    event_id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.match_id'))
    event_type = Column(String(30))
    minute = Column(Integer)
    player_id = Column(Integer, ForeignKey('players.player_id'))
    team_id = Column(Integer, ForeignKey('teams.team_id'))
    
    # Relationships
    match = relationship('Match', back_populates='match_events')
    player = relationship('Player', back_populates='match_events')
    team = relationship('Team', back_populates='match_events')
    
    def __repr__(self):
        return f"<MatchEvent(type={self.event_type}, minute={self.minute})>"


class Standing(Base):
    __tablename__ = 'standings'
    
    id = Column(Integer, primary_key=True)
    season = Column(String(20))
    round = Column(Integer)
    team_id = Column(Integer, ForeignKey('teams.team_id'))
    matches_played = Column(Integer)
    wins = Column(Integer)
    draws = Column(Integer)
    losses = Column(Integer)
    goals_for = Column(Integer)
    goals_against = Column(Integer)
    goal_difference = Column(Integer)
    points = Column(Integer)
    position = Column(Integer)
    
    # Relationships
    team = relationship('Team', back_populates='standings')
    
    def __repr__(self):
        return f"<Standing(team_id={self.team_id}, position={self.position}, points={self.points})>"


class PlayerStats(Base):
    __tablename__ = 'player_stats'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.player_id'))
    team_id = Column(Integer, ForeignKey('teams.team_id'))
    matches_played = Column(Integer)
    goals = Column(Integer)
    own_goals = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    minutes_played = Column(Integer)
    
    # Relationships
    player = relationship('Player', back_populates='player_stats')
    team = relationship('Team', back_populates='player_stats')
    
    def __repr__(self):
        return f"<PlayerStats(player_id={self.player_id}, goals={self.goals})>"


class InjuryArticle(Base):
    __tablename__ = 'injury_articles'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.player_id'))
    url = Column(String(500), unique=True, nullable=False)
    title = Column(String(300))
    published_date = Column(Date)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    injury_type = Column(String(100))
    injury_start = Column(Date)
    duration = Column(String(100))
    needs_manual_check = Column(Boolean, default=True)
    
    # Relationships
    player = relationship('Player', back_populates='injury_articles')
    
    def __repr__(self):
        return (
            f"<InjuryArticle(player_id={self.player_id}, "
            f"injury_type={self.injury_type}, "
            f"start={self.injury_start}, duration={self.duration}, "
            f"needs_manual_check={self.needs_manual_check})>"
        )
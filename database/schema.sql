CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    address VARCHAR(70),
    website VARCHAR(255)
);

CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    birth_date DATE,
    is_injured BOOLEAN DEFAULT FALSE
);

CREATE TABLE team_players (
    id SERIAL PRIMARY KEY,
    team_id INT REFERENCES teams(team_id),
    player_id INT REFERENCES players(player_id)
);

CREATE TABLE matches (
    match_id SERIAL PRIMARY KEY,
    season VARCHAR(20),
    round INT,
    date DATE,
    home_team_id INT REFERENCES teams(team_id),
    away_team_id INT REFERENCES teams(team_id),
    home_score INT,
    away_score INT,
    stadium VARCHAR(100),
    referee VARCHAR(100)
);

CREATE TABLE match_events (
    event_id SERIAL PRIMARY KEY,
    match_id INT REFERENCES matches(match_id),
    event_type VARCHAR(30),
    minute INT,
    player_id INT REFERENCES players(player_id),
    team_id INT REFERENCES teams(team_id)
);

CREATE TABLE standings (
    id SERIAL PRIMARY KEY,
    season VARCHAR(20),
    round INT,
    team_id INT REFERENCES teams(team_id),
    matches_played INT,
    wins INT,
    draws INT,
    losses INT,
    goals_for INT,
    goals_against INT,
    goal_difference INT,
    points INT,
    position INT
);

CREATE TABLE player_stats (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(player_id),
    team_id INT REFERENCES teams(team_id),
    matches_played INT,
    goals INT,
    own_goals INT,
    yellow_cards INT,
    red_cards INT,
    minutes_played INT
);

CREATE TABLE injury_articles (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(player_id),
    url VARCHAR(500) UNIQUE NOT NULL,
    title VARCHAR(300),
    published_date DATE,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    injury_type VARCHAR(100),
    injury_start DATE,
    duration VARCHAR(100),
    needs_manual_check BOOLEAN DEFAULT TRUE
);

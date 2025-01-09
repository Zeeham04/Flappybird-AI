-- Create the database
CREATE DATABASE flappy_ai;

-- Use the database
USE flappy_ai;

-- Table for overall AI performance by generation
CREATE TABLE ai_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    generation INT NOT NULL,
    average_fitness FLOAT NOT NULL,
    max_fitness FLOAT NOT NULL,
    games_played INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for game sessions played by the AI
CREATE TABLE game_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    generation INT NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    total_score FLOAT NOT NULL,
    pipes_passed INT NOT NULL,
    duration_seconds FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generation) REFERENCES ai_performance(generation)
);

-- Table for AI actions taken during gameplay
CREATE TABLE actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    action_type ENUM('FLAP', 'NO_FLAP') NOT NULL,
    bird_y FLOAT NOT NULL,
    pipe_distance FLOAT NOT NULL,
    pipe_gap FLOAT NOT NULL,
    score_before_action FLOAT NOT NULL,
    survived BOOLEAN NOT NULL,
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id)
);

-- Table for pipes encountered during the game
CREATE TABLE pipes_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    pipe_position_x FLOAT NOT NULL,
    pipe_gap_top_y FLOAT NOT NULL,
    pipe_gap_bottom_y FLOAT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id)
);

# Flappy Bird AI: Human vs AI

This project is an AI-powered version of the classic game **Flappy Bird**. It allows you to compete in two modes: play as a human or let an AI trained using **NEAT (NeuroEvolution of Augmenting Topologies)** learn and dominate the game. The AI also leverages historical game data stored in a database to improve its decision-making.

---

## Features

### Gameplay
- **Human Mode**: Navigate the bird through pipes by pressing the spacebar. Avoid obstacles and achieve the highest score!
- **AI Mode**: Watch the AI evolve and learn to pass pipes more efficiently through a neural network and historical game analysis.

### AI Mechanics
- **NEAT Algorithm**: The AI uses a feedforward neural network trained via NEAT for evolving smarter gameplay.
- **Historical Learning**: The AI adapts using historical scenarios retrieved from a database to refine its actions.

### Database Integration
- Stores game sessions, scores, and pipe data.
- Tracks AI performance metrics like generation fitness and survival data.
- Provides recommendations for the AI based on successful and fatal past actions.

---

## Files and Components

### Code
- `flappy_AI.py`: The main script containing game logic, AI training, and historical learning integration.
- `config.txt`: Configuration file for the NEAT algorithm, defining mutation rates, population size, and other settings.
- `connection.py`: Handles database connections and queries.
- `Flappy_Base.sql`: SQL schema for the database storing game and AI performance data.

### Assets
- `bird.png`: The bird sprite used in the game.
- `pipe.png`: Graphics for the top and bottom pipes.
- `background.png`: Background image for the game environment.

---

## Setup

### Prerequisites
- Python 3.7 or higher
- MySQL or a compatible database server
- Required Python libraries:
  - `pygame`
  - `neat-python`
  - `pymysql`
  - `numpy`
  - `mysql-connector-python`

### Installation Steps
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd flappy-bird-ai


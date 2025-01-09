import random
import pygame
import neat
import os
import sys
import mysql.connector
from datetime import datetime
import uuid
import numpy as np
from collections import defaultdict

# Add to DatabaseManager class
class DatabaseManager:

    def get_successful_actions(self, min_score=50):
        """Retrieve successful actions from previous games"""
        if not self.cursor:
            return []
        try:
            query = """
                SELECT a.bird_y, a.pipe_distance, a.pipe_gap, a.action_type
                FROM actions a
                JOIN game_sessions g ON a.session_id = g.session_id
                WHERE g.total_score >= %s
                AND a.survived = TRUE
                ORDER BY g.total_score DESC
                LIMIT 1000
            """
            self.cursor.execute(query, (min_score,))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error retrieving successful actions: {err}")
            return []

    def get_best_generation_genome(self):
        """Retrieve the genome configuration from the best performing generation"""
        if not self.cursor:
            return None
        try:
            query = """
                SELECT generation, max_fitness
                FROM ai_performance
                ORDER BY max_fitness DESC
                LIMIT 1
            """
            self.cursor.execute(query)
            return self.cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Error retrieving best genome: {err}")
            return None

    def get_fatal_scenarios(self):
        """Retrieve scenarios that commonly led to bird death"""
        if not self.cursor:
            return []
        try:
            query = """
                SELECT bird_y, pipe_distance, pipe_gap, action_type
                FROM actions
                WHERE survived = FALSE
                ORDER BY score_before_action DESC
                LIMIT 1000
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error retrieving fatal scenarios: {err}")
            return []

# Add HistoricalLearning class
class HistoricalLearning:
    def __init__(self, db_manager):
        self.db = db_manager
        self.successful_patterns = defaultdict(int)
        self.fatal_patterns = defaultdict(int)
        self.load_historical_data()

    def load_historical_data(self):
        """Load and process historical game data"""
        # Load successful actions
        successful_actions = self.db.get_successful_actions()
        for bird_y, pipe_distance, pipe_gap, action_type in successful_actions:
            key = self._discretize_state(bird_y, pipe_distance, pipe_gap)
            self.successful_patterns[key] += 1 if action_type == 'FLAP' else -1

        # Load fatal scenarios
        fatal_scenarios = self.db.get_fatal_scenarios()
        for bird_y, pipe_distance, pipe_gap, action_type in fatal_scenarios:
            key = self._discretize_state(bird_y, pipe_distance, pipe_gap)
            self.fatal_patterns[key] += 1 if action_type == 'FLAP' else -1

    def _discretize_state(self, bird_y, pipe_distance, pipe_gap):
        """Convert continuous state values to discrete buckets"""
        # Discretize values into buckets for pattern matching
        y_bucket = int(bird_y / 50)  # Every 50 pixels
        dist_bucket = int(pipe_distance / 100)  # Every 100 pixels
        gap_bucket = int(pipe_gap / 50)  # Every 50 pixels
        return (y_bucket, dist_bucket, gap_bucket)

    def get_recommendation(self, bird_y, pipe_distance, pipe_gap):
        """Get action recommendation based on historical data"""
        key = self._discretize_state(bird_y, pipe_distance, pipe_gap)
        
        # Check if this scenario was fatal in the past
        if self.fatal_patterns[key] != 0:
            # Recommend opposite of what led to death
            return self.fatal_patterns[key] < 0
        
        # Use successful patterns if available
        if self.successful_patterns[key] != 0:
            return self.successful_patterns[key] > 0
        
        # No historical data for this scenario
        return None

# Modify Bird class to include historical learning
class Bird:
    def __init__(self, session_id=None, historical_learning=None):
        # [Previous attributes remain the same]
        self.historical_learning = historical_learning  # Add historical learning
        self.session_id = session_id
        self.pipes_passed = 0

# Modify ai_game function to use historical learning
def ai_game(genomes, config):
    global GEN
    GEN += 1

    # Initialize database and historical learning
    db = DatabaseManager()
    historical_learning = HistoricalLearning(db)
    db.start_generation(GEN)

    birds = []
    nets = []
    ge = []
    pipes = []
    start_time = pygame.time.get_ticks()

    # Create birds with historical learning capability
    for _, genome in genomes:
        session_id = db.start_game_session(GEN)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        genome.fitness = 0
        nets.append(net)
        birds.append(Bird(session_id, historical_learning))
        ge.append(genome)

    while True:
        # [Previous event handling code remains the same]

        # Update birds with historical learning
        alive_birds = 0
        for i, bird in enumerate(birds):
            if not bird.dead:
                nearest_pipe = pipes[0] if pipes else None
                pipe_distance = nearest_pipe.bottom_pipe_rect.x - bird.bird_rect.x if nearest_pipe else BG_WIDTH
                pipe_gap = nearest_pipe.top_pipe_rect.bottom if nearest_pipe else 0

                # Get AI decision
                output = nets[i].activate([bird.bird_rect.y, pipe_distance])
                should_jump = output[0] > 0.5

                # Get recommendation from historical data
                historical_recommendation = bird.historical_learning.get_recommendation(
                    bird.bird_rect.y, pipe_distance, pipe_gap
                )

                # Combine AI decision with historical learning
                if historical_recommendation is not None:
                    # Use historical recommendation with 30% probability
                    if random.random() < 0.3:
                        should_jump = historical_recommendation
                        # Reward following historical success patterns
                        ge[i].fitness += 0.1

                

    

# Add database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'flappy_ai'
}

# Add DatabaseManager class
class DatabaseManager:
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("Database connection successful!")
        except mysql.connector.Error as err:
            print(f"Database connection failed: {err}")
            self.conn = None
            self.cursor = None

    def start_generation(self, generation):
        if not self.cursor:
            return
        try:
            query = """INSERT INTO ai_performance (generation, average_fitness, max_fitness, games_played)
                      VALUES (%s, 0, 0, 0)"""
            self.cursor.execute(query, (generation,))
            self.conn.commit()
        except mysql.connector.Error as err:
            print(f"Error starting generation: {err}")

    def start_game_session(self, generation):
        if not self.cursor:
            return None
        try:
            session_id = str(uuid.uuid4())
            query = """INSERT INTO game_sessions (generation, session_id, total_score, pipes_passed, duration_seconds)
                      VALUES (%s, %s, 0, 0, 0)"""
            self.cursor.execute(query, (generation, session_id))
            self.conn.commit()
            return session_id
        except mysql.connector.Error as err:
            print(f"Error starting game session: {err}")
            return None

    def record_action(self, session_id, action_type, bird_y, pipe_distance, pipe_gap, score, survived):
        if not self.cursor or not session_id:
            return
        try:
            query = """INSERT INTO actions (session_id, action_type, bird_y, pipe_distance, pipe_gap, 
                      score_before_action, survived)
                      VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            self.cursor.execute(query, (session_id, action_type, bird_y, pipe_distance, pipe_gap, score, survived))
            self.conn.commit()
        except mysql.connector.Error as err:
            print(f"Error recording action: {err}")

    def record_pipe(self, session_id, x, top_y, bottom_y):
        if not self.cursor or not session_id:
            return
        try:
            query = """INSERT INTO pipes_data (session_id, pipe_position_x, pipe_gap_top_y, pipe_gap_bottom_y)
                      VALUES (%s, %s, %s, %s)"""
            self.cursor.execute(query, (session_id, x, top_y, bottom_y))
            self.conn.commit()
        except mysql.connector.Error as err:
            print(f"Error recording pipe: {err}")

    def update_game_session(self, session_id, score, pipes_passed, duration):
        if not self.cursor or not session_id:
            return
        try:
            query = """UPDATE game_sessions 
                      SET total_score = %s, pipes_passed = %s, duration_seconds = %s 
                      WHERE session_id = %s"""
            self.cursor.execute(query, (score, pipes_passed, duration, session_id))
            self.conn.commit()
        except mysql.connector.Error as err:
            print(f"Error updating game session: {err}")

    def update_generation_stats(self, generation, avg_fitness, max_fitness, games_played):
        if not self.cursor:
            return
        try:
            query = """UPDATE ai_performance 
                      SET average_fitness = %s, max_fitness = %s, games_played = %s 
                      WHERE generation = %s"""
            self.cursor.execute(query, (avg_fitness, max_fitness, games_played, generation))
            self.conn.commit()
        except mysql.connector.Error as err:
            print(f"Error updating generation stats: {err}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

# Modify Bird class to include session tracking
class Bird:
    def __init__(self, session_id=None):
        self.bird_rect = BIRD_IMG.get_rect(center=(BG_WIDTH // 4, BG_HEIGHT // 2))
        self.dead = False
        self.score = 0
        self.velocity = 0
        self.flap_cooldown = 0
        self.session_id = session_id  # Add session_id
        self.pipes_passed = 0  # Add pipes_passed counter

# Modify ai_game function to include data collection
def ai_game(genomes, config):
    global GEN
    GEN += 1

    # Initialize database connection
    db = DatabaseManager()
    db.start_generation(GEN)

    birds = []
    nets = []
    ge = []
    pipes = []
    start_time = pygame.time.get_ticks()

    # Create birds with session IDs
    for _, genome in genomes:
        session_id = db.start_game_session(GEN)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        genome.fitness = 0
        nets.append(net)
        birds.append(Bird(session_id))
        ge.append(genome)

    while True:
        # [Previous event handling code remains the same]

        # Record pipe data
        for pipe in pipes:
            if not hasattr(pipe, 'recorded') or not pipe.recorded:
                for bird in birds:
                    if not bird.dead:
                        db.record_pipe(bird.session_id, 
                                     pipe.bottom_pipe_rect.x,
                                     pipe.top_pipe_rect.bottom,
                                     pipe.bottom_pipe_rect.top)
                pipe.recorded = True

        # Update birds and record actions
        alive_birds = 0
        for i, bird in enumerate(birds):
            if not bird.dead:
                # Get nearest pipe for AI input
                nearest_pipe = pipes[0] if pipes else None
                pipe_distance = nearest_pipe.bottom_pipe_rect.x - bird.bird_rect.x if nearest_pipe else BG_WIDTH
                pipe_gap = nearest_pipe.top_pipe_rect.bottom if nearest_pipe else 0

                # Get AI decision and record action
                output = nets[i].activate([bird.bird_rect.y, pipe_distance])
                should_jump = output[0] > 0.5
                
                db.record_action(bird.session_id,
                               'FLAP' if should_jump else 'NO_FLAP',
                               bird.bird_rect.y,
                               pipe_distance,
                               pipe_gap,
                               bird.score,
                               True)

                # Move bird
                bird.move(jump=should_jump)
                bird.score += SCORE_INCREASE
                ge[i].fitness += SCORE_INCREASE

                # Update score when passing pipes
                if nearest_pipe and not nearest_pipe.passed and nearest_pipe.bottom_pipe_rect.right < bird.bird_rect.left:
                    bird.pipes_passed += 1
                    nearest_pipe.passed = True

                if bird.collision(pipes):
                    duration = (pygame.time.get_ticks() - start_time) / 1000
                    db.update_game_session(bird.session_id, bird.score, bird.pipes_passed, duration)
                    bird.dead = True
                else:
                    alive_birds += 1

        if alive_birds == 0:
            # Calculate and record final generation statistics
            fitnesses = [g.fitness for g in ge]
            avg_fitness = sum(fitnesses) / len(fitnesses) if fitnesses else 0
            max_fitness = max(fitnesses) if fitnesses else 0
            db.update_generation_stats(GEN, avg_fitness, max_fitness, len(birds))
            db.close()
            return
# Initialize Pygame
pygame.init()

# Load images and assets
BG = pygame.image.load("assets/background.png")
BG_WIDTH, BG_HEIGHT = BG.get_size()
WN = pygame.display.set_mode((BG_WIDTH, BG_HEIGHT))
pygame.display.set_caption("Flappy Bird: AI vs Human")

# Game constants
CLOCK = pygame.time.Clock()
RED = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FPS = 60
GRAVITY = 0.5  # Reduced gravity for smoother falling
JUMP_SPEED = -8  # Added jump speed for more controlled jumps
MAX_FALL_SPEED = 10  # Added maximum fall speed
GAP_PIPE = 150
PIPE_EVENT = pygame.USEREVENT
pygame.time.set_timer(PIPE_EVENT, 1500)  # Increased time between pipes
FONT = pygame.font.SysFont("comicsans", 30)
STATS_FONT = pygame.font.SysFont("comicsans", 24)
SCORE_INCREASE = 0.1

# Bird settings
BIRD_IMG = pygame.image.load("assets/bird.png")
BIRD_SIZE = (40, 26)
BIRD_IMG = pygame.transform.scale(BIRD_IMG, BIRD_SIZE)

# Pipe settings
PIPE_BOTTOM_IMG = pygame.image.load("assets/pipe.png")
PIPE_TOP_IMG = pygame.transform.flip(PIPE_BOTTOM_IMG, False, True)
PIPE_BOTTOM_HEIGHTS = [90, 122, 154, 186, 218, 250]
PIPE_SPEED = 3  # Added constant for pipe speed

# Global variables
GEN = 0
HUMAN_MODE = False

class Pipe:
    def __init__(self, height):
        bottom_midtop = (BG_WIDTH, BG_HEIGHT - height)
        top_midbottom = (BG_WIDTH, BG_HEIGHT - height - GAP_PIPE)
        self.bottom_pipe_rect = PIPE_BOTTOM_IMG.get_rect(midtop=bottom_midtop)
        self.top_pipe_rect = PIPE_TOP_IMG.get_rect(midbottom=top_midbottom)
        self.passed = False  # Track if bird has passed this pipe

    def move(self):
        self.bottom_pipe_rect.x -= PIPE_SPEED
        self.top_pipe_rect.x -= PIPE_SPEED

    def display(self):
        WN.blit(PIPE_BOTTOM_IMG, self.bottom_pipe_rect)
        WN.blit(PIPE_TOP_IMG, self.top_pipe_rect)

class Bird:
    def __init__(self):
        self.bird_rect = BIRD_IMG.get_rect(center=(BG_WIDTH // 4, BG_HEIGHT // 2))  # Changed initial position
        self.dead = False
        self.score = 0
        self.velocity = 0  # Added velocity for smooth movement
        self.flap_cooldown = 0  # Prevents rapid flapping

    def move(self, jump=False):
        if jump and self.flap_cooldown <= 0:
            self.velocity = JUMP_SPEED
            self.flap_cooldown = 10  # Set cooldown frames
        
        # Apply gravity and update position
        self.velocity = min(self.velocity + GRAVITY, MAX_FALL_SPEED)
        self.bird_rect.centery += self.velocity
        
        # Update flap cooldown
        if self.flap_cooldown > 0:
            self.flap_cooldown -= 1

    def collision(self, pipes):
        for pipe in pipes:
            if self.bird_rect.colliderect(pipe.bottom_pipe_rect) or \
               self.bird_rect.colliderect(pipe.top_pipe_rect):
                return True
        if self.bird_rect.midbottom[1] >= BG_HEIGHT or self.bird_rect.midtop[1] < 0:
            return True
        return False

    def draw_lines(self, pipes):
        # Draw red lines to nearest pipes
        if pipes:
            nearest_pipe = pipes[0]
            pygame.draw.line(WN, RED, self.bird_rect.center, nearest_pipe.top_pipe_rect.midbottom, 2)
            pygame.draw.line(WN, RED, self.bird_rect.center, nearest_pipe.bottom_pipe_rect.midtop, 2)

def menu():
    while True:
        WN.blit(BG, (0, 0))
        title = FONT.render("Flappy Bird: AI vs Human", True, BLACK)
        human_button = FONT.render("1. Human Mode", True, BLACK)
        ai_button = FONT.render("2. AI Mode", True, BLACK)
        quit_button = FONT.render("3. Quit", True, BLACK)
        instructions = STATS_FONT.render("Press SPACE to flap!", True, BLACK)

        WN.blit(title, (BG_WIDTH // 2 - title.get_width() // 2, BG_HEIGHT // 4))
        WN.blit(human_button, (BG_WIDTH // 2 - human_button.get_width() // 2, BG_HEIGHT // 2 - 50))
        WN.blit(ai_button, (BG_WIDTH // 2 - ai_button.get_width() // 2, BG_HEIGHT // 2))
        WN.blit(quit_button, (BG_WIDTH // 2 - quit_button.get_width() // 2, BG_HEIGHT // 2 + 50))
        WN.blit(instructions, (BG_WIDTH // 2 - instructions.get_width() // 2, BG_HEIGHT // 2 + 100))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "HUMAN"
                if event.key == pygame.K_2:
                    return "AI"
                if event.key == pygame.K_3:
                    pygame.quit()
                    sys.exit()

def human_game():
    bird = Bird()
    pipes = []
    score = 0
    start_time = pygame.time.get_ticks()
    game_started = False  # Track if game has started

    while True:
        # Handle events
        jump = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == PIPE_EVENT and game_started:
                height = random.choice(PIPE_BOTTOM_HEIGHTS)
                pipes.append(Pipe(height))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                jump = True
                if not game_started:
                    game_started = True

        # Draw background
        WN.blit(BG, (0, 0))

        if not game_started:
            # Display "Press SPACE to start" message
            start_text = FONT.render("Press SPACE to start!", True, BLACK)
            WN.blit(start_text, (BG_WIDTH // 2 - start_text.get_width() // 2, BG_HEIGHT // 2))
        else:
            # Game logic
            # Move and display pipes
            for pipe in pipes:
                pipe.move()
                pipe.display()
                # Check for score increase
                if not pipe.passed and pipe.bottom_pipe_rect.right < bird.bird_rect.left:
                    score += 1
                    pipe.passed = True

            # Remove off-screen pipes
            pipes = [pipe for pipe in pipes if pipe.bottom_pipe_rect.right > 0]

        # Update and display bird
        bird.move(jump)
        WN.blit(BIRD_IMG, bird.bird_rect)

        # Draw lines to pipes
        bird.draw_lines(pipes)

        # Check for collision only if game has started
        if game_started and bird.collision(pipes):
            game_over_text = FONT.render(f"Game Over! Score: {score}", True, BLACK)
            WN.blit(game_over_text, (BG_WIDTH // 2 - game_over_text.get_width() // 2, BG_HEIGHT // 2))
            pygame.display.update()
            pygame.time.wait(2000)  # Wait 2 seconds before returning
            return  # Return to the menu

        # Display score
        score_text = FONT.render(f"Score: {score}", True, BLACK)
        WN.blit(score_text, (10, 10))

        pygame.display.update()
        CLOCK.tick(FPS)

def ai_game(genomes, config):
    global GEN
    GEN += 1

    birds = []
    nets = []
    ge = []
    pipes = []
    start_time = pygame.time.get_ticks()

    for _, genome in genomes[:20]:  # Increased to 20 birds
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        genome.fitness = 0
        nets.append(net)
        birds.append(Bird())
        ge.append(genome)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == PIPE_EVENT:
                height = random.choice(PIPE_BOTTOM_HEIGHTS)
                pipes.append(Pipe(height))

        WN.blit(BG, (0, 0))

        # Move pipes and remove off-screen pipes
        if pipes:
            for pipe in pipes:
                pipe.move()
                pipe.display()
            pipes = [pipe for pipe in pipes if pipe.bottom_pipe_rect.x > -100]

        # Update birds
        alive_birds = 0
        for i, bird in enumerate(birds):
            if not bird.dead:
                if pipes:
                    output = nets[i].activate([bird.bird_rect.y, pipes[0].top_pipe_rect.x, bird.bird_rect.y - (pipes[0].bottom_pipe_rect.top - GAP_PIPE / 2)])
                else:
                    output = nets[i].activate([bird.bird_rect.y, BG_WIDTH, 0])

                bird.move(jump=output[0] > 0.5)
                bird.score += SCORE_INCREASE
                ge[i].fitness += SCORE_INCREASE
                WN.blit(BIRD_IMG, bird.bird_rect)

                # Draw lines to pipes
                bird.draw_lines(pipes)

                if bird.collision(pipes):
                    bird.dead = True
                else:
                    alive_birds += 1

        if alive_birds == 0:
            return

        elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
        stats = [f"Generation: {GEN}", f"Alive Birds: {alive_birds}", f"Time: {elapsed_time}s"]
        for idx, stat in enumerate(stats):
            text = FONT.render(stat, True, BLACK)
            WN.blit(text, (10, 10 + idx * 30))

        pygame.display.update()
        CLOCK.tick(FPS)


def run():
    while True:
        mode = menu()

        if mode == "HUMAN":
            human_game()
        elif mode == "AI":
            config_path = os.path.join(os.path.dirname(__file__), "config.txt")
            config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                      neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                      config_path)
            population = neat.Population(config)
            population.run(ai_game, 20)

if __name__ == "__main__":
    run()

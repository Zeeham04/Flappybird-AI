import random
import pygame
import neat
import os
import sys

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

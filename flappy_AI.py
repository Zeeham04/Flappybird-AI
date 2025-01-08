# Import required libraries
import random  # Used for generating random pipe heights
import pygame  # Used for creating the game visuals and mechanics
import neat    # Used for implementing the neural network and evolution logic

# Initialize the Pygame library
pygame.init()

# Game constants
CLOCK = pygame.time.Clock()  # Clock object to control the frame rate
RED = (255, 0, 0)            # Color used for drawing distance lines (RGB format)
BLACK = (0, 0, 0)            # Color used for text
FPS = 60                     # Frames per second

# Window dimensions and setup
WN_WIDTH = 400               # Width of the game window
WN_HEIGHT = 500              # Height of the game window
WN = pygame.display.set_mode((WN_WIDTH, WN_HEIGHT))  # Set up the display window
pygame.display.set_caption("AI Plays Flappy Bird")   # Set the window title

# Load images and assets
BG = pygame.image.load("assets/bird_bg.png")  # Background image
BIRD_IMG = pygame.image.load("assets/bird.png")  # Bird image
BIRD_SIZE = (40, 26)                           # Dimensions for the bird
BIRD_IMG = pygame.transform.scale(BIRD_IMG, BIRD_SIZE)  # Resize bird image
GRAVITY = 4                                    # Gravity constant affecting the bird's fall
JUMP = 30                                      # Vertical jump height for the bird

# Pipe settings
PIPE_X0 = 400  # Initial x-coordinate of pipes
PIPE_BOTTOM_IMG = pygame.image.load("assets/pipe.png")  # Bottom pipe image
PIPE_TOP_IMG = pygame.transform.flip(PIPE_BOTTOM_IMG, False, True)  # Flipped image for the top pipe
PIPE_BOTTOM_HEIGHTS = [90, 122, 154, 186, 218, 250]  # Possible heights for bottom pipes
GAP_PIPE = 150  # Gap between the top and bottom pipes
PIPE_EVENT = pygame.USEREVENT  # Custom event for pipe generation
pygame.time.set_timer(PIPE_EVENT, 1000)  # Set the timer to trigger the event every second
FONT = pygame.font.SysFont("comicsans", 30)  # Font for displaying text
SCORE_INCREASE = 0.01  # Score increment for surviving birds
GEN = 0  # Counter for tracking generations

# Pipe class to represent each pipe pair
class Pipe:
    def __init__(self, height):
        # Bottom pipe positioning
        bottom_midtop = (PIPE_X0, WN_HEIGHT - height)
        # Top pipe positioning
        top_midbottom = (PIPE_X0, WN_HEIGHT - height - GAP_PIPE)
        # Rectangles representing the pipe hitboxes
        self.bottom_pipe_rect = PIPE_BOTTOM_IMG.get_rect(midtop=bottom_midtop)
        self.top_pipe_rect = PIPE_TOP_IMG.get_rect(midbottom=top_midbottom)

    def display_pipe(self):
        # Draw both the bottom and top pipes on the screen
        WN.blit(PIPE_BOTTOM_IMG, self.bottom_pipe_rect)
        WN.blit(PIPE_TOP_IMG, self.top_pipe_rect)

# Bird class to represent each bird
class Bird:
    def __init__(self):
        self.bird_rect = BIRD_IMG.get_rect(center=(WN_WIDTH // 2, WN_HEIGHT // 2))  # Initialize bird position
        self.dead = False  # Flag to indicate if the bird is dead
        self.score = 0     # Bird's score

    def collision(self, pipes):
        # Check for collision with any pipe or boundaries
        for pipe in pipes:
            if self.bird_rect.colliderect(pipe.bottom_pipe_rect) or \
               self.bird_rect.colliderect(pipe.top_pipe_rect):
                return True
        # Check for collision with the top or bottom of the screen
        if self.bird_rect.midbottom[1] >= WN_HEIGHT or self.bird_rect.midtop[1] < 0:
            return True
        return False

    def find_nearest_pipes(self, pipes):
        # Find the nearest pipes (top and bottom) in front of the bird
        nearest_pipe_top = None
        nearest_pipe_bottom = None
        min_distance = WN_WIDTH
        for pipe in pipes:
            curr_distance = pipe.bottom_pipe_rect.topright[0] - self.bird_rect.topleft[0]
            if curr_distance < 0:
                continue  # Skip pipes already behind the bird
            elif curr_distance <= min_distance:
                min_distance = curr_distance
                nearest_pipe_bottom = pipe.bottom_pipe_rect
                nearest_pipe_top = pipe.top_pipe_rect
        return nearest_pipe_top, nearest_pipe_bottom

    def get_distances(self, top_pipe, bottom_pipe):
        # Calculate distances to the nearest pipes
        distance = [WN_WIDTH] * 3
        distance[0] = top_pipe.centerx - self.bird_rect.centerx  # Horizontal distance
        distance[1] = self.bird_rect.topleft[1] - top_pipe.bottomright[1]  # Vertical distance to top pipe
        distance[2] = bottom_pipe.topright[1] - self.bird_rect.bottomright[1]  # Vertical distance to bottom pipe
        return distance

    def draw_lines(self, top_pipe, bottom_pipe):
        # Draw lines to visualize distances to the nearest pipes
        pygame.draw.line(WN, RED, self.bird_rect.midright, top_pipe.midbottom, 5)
        pygame.draw.line(WN, RED, self.bird_rect.midright, bottom_pipe.midtop, 5)

# Game loop that controls one generation
def game_loop(genomes, config):
    global GEN
    GEN += 1  # Increment generation counter

    # Initialize birds, networks, and genomes
    birds = []
    nets = []
    ge = []  # Genomes list

    pipe_list = []  # List to store pipes

    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)  # Create neural network
        genome.fitness = 0  # Initialize fitness score
        nets.append(net)
        birds.append(Bird())
        ge.append(genome)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == PIPE_EVENT:  # Triggered every second to generate pipes
                bottom_height = random.choice(PIPE_BOTTOM_HEIGHTS)
                pipe_list.append(Pipe(bottom_height))

        # Draw background
        WN.blit(BG, (0, 0))
        remove_pipes = []  # List of pipes to remove

        # Update pipe positions and display them
        for pipe in pipe_list:
            pipe.top_pipe_rect.x -= 3  # Move pipes left
            pipe.bottom_pipe_rect.x -= 3
            pipe.display_pipe()

            if pipe.top_pipe_rect.x < -100:  # Remove pipes out of the screen
                remove_pipes.append(pipe)

        for r in remove_pipes:
            pipe_list.remove(r)

        alive_birds = 0
        max_score = 0

        # Process each bird
        for i, bird in enumerate(birds):
            if not bird.dead:
                bird.bird_rect.centery += GRAVITY  # Apply gravity
                bird.score += SCORE_INCREASE  # Increment score
                alive_birds += 1
                max_score = max(max_score, bird.score)
                ge[i].fitness += bird.score  # Update fitness based on score

                WN.blit(BIRD_IMG, bird.bird_rect)  # Draw the bird
                bird.dead = bird.collision(pipe_list)  # Check for collisions

                # Find the nearest pipes and get distances
                nearest_pipes = bird.find_nearest_pipes(pipe_list)
                if nearest_pipes[0]:
                    distances = bird.get_distances(nearest_pipes[0], nearest_pipes[1])
                    bird.draw_lines(nearest_pipes[0], nearest_pipes[1])
                else:
                    distances = [WN_WIDTH] * 3

                # Neural network prediction
                output = nets[i].activate(distances)
                max_ind = output.index(max(output))  # Find the action with the highest probability
                if max_ind == 0:  # If the network decides to jump
                    bird.bird_rect.centery -= JUMP

        if alive_birds == 0:  # End generation if all birds are dead
            return

        # Display generation stats
        msg = f"Gen: {GEN} Birds Alive: {alive_birds} Score: {int(max_score)}"
        text = FONT.render(msg, True, BLACK)
        WN.blit(text, (40, 20))
        pygame.display.update()
        CLOCK.tick(FPS)  # Control frame rate

# Run the NEAT algorithm
neat_config = neat.config.Config(
    neat.DefaultGenome, neat.DefaultReproduction,
    neat.DefaultSpeciesSet, neat.DefaultStagnation, "config.txt"
)
population = neat.Population(neat_config)  # Initialize NEAT population
stats = neat.StatisticsReporter()  # Add a statistics reporter
population.add_reporter(stats)
population.run(game_loop, 50)  # Run for 50 generations

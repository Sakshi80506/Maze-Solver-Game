import pygame
import random
import time
from pygame import mixer
import heapq # For path finding
pygame.init()
mixer.init()
CELL_SIZE = 20
WIDTH, HEIGHT = 1200, 700
FPS = 60
TIMER_LIMIT = 75
COIN_SCORE = 10
OBSTACLE_PENALTY = 5 # Score penalty when hitting an obstacle
OBSTACLE_COUNT = {
 "easy": 3,
 "medium": 5,
 "hard": 8
}
OBSTACLE_SPEED = {
 "easy": 2, # Cells per second
 "medium": 3,
 "hard": 4
}
DEADLY_OBSTACLE_CHANCE = 0.3 # 30% chance for an obstacle to be deadly
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Solver 3D")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("arial", 36)
SMALL_FONT = pygame.font.SysFont("arial", 24)
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (150, 150, 150)
BLUE, RED, GREEN, YELLOW = (0, 100, 255), (255, 60, 60), (0, 200, 0), (255, 255, 0)
PURPLE = (150, 0, 150) # Color for normal obstacles
DARK_RED = (180, 0, 0) # Color for deadly obstacles
LIGHT_BLUE = (173, 216, 230) # Color for path hints
try:
 player_img = pygame.transform.scale(pygame.image.load("player.png"), (CELL_SIZE, CELL_SIZE))
 coin_img = pygame.transform.scale(pygame.image.load("coin.png"), (CELL_SIZE, CELL_SIZE))
except pygame.error:
 # Create fallback images if files aren't found
 player_img = pygame.Surface((CELL_SIZE, CELL_SIZE))
 player_img.fill(BLUE)
 coin_img = pygame.Surface((CELL_SIZE, CELL_SIZE))
 coin_img.fill(YELLOW)
 print("Warning: Image files not found. Using placeholder graphics.")
class Obstacle:
 def __init__(self, maze, deadly=False):
 self.maze = maze
 self.deadly = deadly
 self.color = DARK_RED if deadly else PURPLE
 self.position = self.find_valid_position()
 self.direction = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
 self.move_timer = 0
 self.move_interval = random.uniform(0.3, 0.8) # Time between moves
 self.position_float = [float(self.position[0]), float(self.position[1])]
 def find_valid_position(self):
 rows, cols = len(self.maze), len(self.maze[0])
 while True:
 r, c = random.randint(1, rows - 2), random.randint(1, cols - 2)
 if self.maze[r][c] == 0:
 # Make sure it's not at player start or goal
 if not ((r == 0 and c == 0) or (r == rows - 1 and c == cols - 1)):
 return [r, c]
 def update(self, dt, speed_factor):
 self.move_timer += dt
 if self.move_timer >= self.move_interval:
 self.move_timer = 0
 self.choose_direction()
 # Smooth movement
 dr, dc = self.direction
 move_amount = dt * speed_factor
 # Update floating point position
 new_r = self.position_float[0] + dr * move_amount
 new_c = self.position_float[1] + dc * move_amount
 # Check if new position would be valid
 int_r, int_c = int(new_r), int(new_c)
 if (0 <= int_r < len(self.maze) and 0 <= int_c < len(self.maze[0]) and self.maze[int_r][int_c] == 0):
 self.position_float = [new_r, new_c]
 self.position = [int_r, int_c]
 else:
 # Hit a wall, choose new direction
 self.choose_direction()
 def choose_direction(self):
 r, c = self.position
 possible_directions = []
 # Check all four directions
 for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
 new_r, new_c = r + dr, c + dc
 if (0 <= new_r < len(self.maze) and 0 <= new_c < len(self.maze[0]) and self.maze[new_r][new_c] == 0):
 possible_directions.append((dr, dc))
 # If there are valid directions, choose one
 if possible_directions:
 self.direction = random.choice(possible_directions)
 else:
 # Fallback if somehow trapped
 self.direction = (0, 0)
 def draw(self):
 x, y = self.position[1] * CELL_SIZE, self.position[0] * CELL_SIZE
 pygame.draw.rect(screen, self.color, (x, y, CELL_SIZE, CELL_SIZE))
 if self.deadly:
 # Draw an X for deadly obstacles
 pygame.draw.line(screen, BLACK, (x, y), (x + CELL_SIZE, y + CELL_SIZE), 2)
 pygame.draw.line(screen, BLACK, (x + CELL_SIZE, y), (x, y + CELL_SIZE), 2)
 else:
 # Draw a circle for non-deadly obstacles
 pygame.draw.circle(screen, BLACK, (x + CELL_SIZE // 2, y + CELL_SIZE // 2), CELL_SIZE // 3, 2)
def generate_maze_with_multiple_paths(rows, cols):
 # Initialize maze with walls
 maze = [[1 for _ in range(cols)] for _ in range(rows)]
 # Create main path using DFS
 visited = [[False] * cols for _ in range(rows)]
 def get_neighbors(r, c):
 neighbors = []
 if r > 1: neighbors.append((r - 2, c))
 if r < rows - 2: neighbors.append((r + 2, c))
 if c > 1: neighbors.append((r, c - 2))
 if c < cols - 2: neighbors.append((r, c + 2))
 return neighbors
 def visit(r, c):
 visited[r][c] = True
 maze[r][c] = 0
 neighbors = get_neighbors(r, c)
 random.shuffle(neighbors)
 for nr, nc in neighbors:
 if not visited[nr][nc]:
 maze[(r + nr) // 2][(c + nc) // 2] = 0
 visit(nr, nc)
 # Generate main path
 visit(0, 0)
 # Add additional paths and loops
 for _ in range(rows * cols // 15): # Number of additional paths proportional to maze size
 r, c = random.randint(1, rows - 2), random.randint(1, cols - 2)
 if maze[r][c] == 0: # Start from an existing path
 # Try to connect to another part of the path
 directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
 random.shuffle(directions)
 for dr, dc in directions:
 nr, nc = r + dr * 2, c + dc * 2
 if (0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 0 and
 maze[r + dr][c + dc] == 1): # If wall between two paths
 maze[r + dr][c + dc] = 0 # Create a passage
 break
 # Ensure the start and goal are open
 maze[0][0] = maze[rows - 1][cols - 1] = 0
 return maze
def find_paths(maze, start, goal):
 """Find multiple paths from start to goal using A* algorithm"""
 rows, cols = len(maze), len(maze[0])
 def heuristic(p1, p2):
 # Manhattan distance
 return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
 # Get all possible paths
 paths = []
 # Find first path (shortest)
 open_set = [(heuristic(start, goal), 0, start, [])]
 visited = set()
 while open_set and len(paths) < 3: # Limit to 3 paths for performance
 _, cost, current, path = heapq.heappop(open_set)
 if current == goal:
 paths.append(path + [current])
 # Mark this path as "visited" to find alternative paths
 for pos in path:
 visited.add(tuple(pos))
 continue
 if tuple(current) in visited:
 continue
 visited.add(tuple(current))
 # Add current position to path
 new_path = path + [current]
 # Check all four directions
 for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
 r, c = current
 nr, nc = r + dr, c + dc
 if (0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 0 and tuple([nr, nc]) not in visited):
 new_cost = cost + 1
 priority = new_cost + heuristic([nr, nc], goal)
 heapq.heappush(open_set, (priority, new_cost, [nr, nc], new_path))
 return paths
def place_coins(maze, start, goal, max_coins=20):
 rows, cols = len(maze), len(maze[0])
 coins = []
 path_cells = [(r, c) for r in range(rows) for c in range(cols) if maze[r][c] == 0]
 path_cells = [p for p in path_cells if p != tuple(start) and p != tuple(goal)]
 for _ in range(min(max_coins, len(path_cells))):
 pos = random.choice(path_cells)
 path_cells.remove(pos)
 coins.append(pos)
 return coins
def create_obstacles(maze, difficulty, rows, cols):
 count = OBSTACLE_COUNT[difficulty]
 obstacles = []
 for _ in range(count):
 is_deadly = random.random() < DEADLY_OBSTACLE_CHANCE
 obstacle = Obstacle(maze, deadly=is_deadly)
 obstacles.append(obstacle)
 return obstacles
def draw_maze(maze, player_pos, goal_pos, coins, obstacles, paths=None):
 for r, row in enumerate(maze):
 for c, cell in enumerate(row):
 x, y = c * CELL_SIZE, r * CELL_SIZE
 rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
 if cell == 1:
 pygame.draw.rect(screen, GRAY, rect)
 pygame.draw.line(screen, BLACK, (x, y), (x + CELL_SIZE, y), 1)
 pygame.draw.line(screen, BLACK, (x, y), (x, y + CELL_SIZE), 1)
 else:
 pygame.draw.rect(screen, WHITE, rect)
 # Draw paths if provided (for AI hint)
 if paths:
 colors = [(173, 216, 230), (144, 238, 144), (255, 182, 193)] # Different colors for different paths
 for i, path in enumerate(paths):
 color = colors[i % len(colors)]
 for r, c in path:
 if [r, c] != player_pos and [r, c] != goal_pos:
 x, y = c * CELL_SIZE, r * CELL_SIZE
 rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
 pygame.draw.rect(screen, color, rect)
 pygame.draw.rect(screen, color, rect, 1)
 maze_width = len(maze[0]) * CELL_SIZE
 maze_height = len(maze) * CELL_SIZE
 pygame.draw.rect(screen, BLACK, (0, 0, maze_width, maze_height), 4)
 gx, gy = goal_pos[1] * CELL_SIZE, goal_pos[0] * CELL_SIZE
 pygame.draw.rect(screen, (144, 238, 144), (gx, gy, CELL_SIZE, CELL_SIZE))
 pygame.draw.rect(screen, GREEN, (gx, gy, CELL_SIZE, CELL_SIZE), 2)
 for r, c in coins:
 screen.blit(coin_img, (c * CELL_SIZE, r * CELL_SIZE))
 for obstacle in obstacles:
 obstacle.draw()
 screen.blit(player_img, (player_pos[1] * CELL_SIZE, player_pos[0] * CELL_SIZE))
def show_score(score):
 """Display the score on a separate screen"""
 screen.fill(WHITE)
 # Display score with larger font and centered
 title = FONT.render("YOUR SCORE", True, BLACK)
 score_text = FONT.render(str(score), True, BLUE)
 # Position elements
 screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
 screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
 # Back button
 back_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
 pygame.draw.rect(screen, BLUE, back_btn, border_radius=8)
 screen.blit(FONT.render("Back", True, WHITE), (back_btn.x + 60, back_btn.y + 5))
 pygame.display.flip()
 while True:
 for e in pygame.event.get():
 if e.type == pygame.QUIT:
 pygame.quit()
 exit()
 if e.type == pygame.MOUSEBUTTONDOWN:
 if back_btn.collidepoint(e.pos):
 return
def game_over_screen(win, final_score, ai_used):
 screen.fill(WHITE)
 if win:
 msg = FONT.render("You Win!", True, GREEN)
 else:
 msg = FONT.render("Game Over!", True, RED)
 screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 3))
 score_text = FONT.render(f"Final Score: {final_score}", True, BLACK)
 screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
 if ai_used:
 hint_text = SMALL_FONT.render("(AI Help was used)", True, GRAY)
 screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT // 2 + 50))
 view_score_btn = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 200, 300, 50)
 home_btn = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 130, 300, 50)
 pygame.draw.rect(screen, YELLOW, view_score_btn, border_radius=8)
 pygame.draw.rect(screen, GRAY, home_btn, border_radius=8)
 screen.blit(FONT.render("View Score", True, BLACK),
 (view_score_btn.x + 75, view_score_btn.y + 5))
 screen.blit(FONT.render("Back Home", True, WHITE),
 (home_btn.x + 75, home_btn.y + 5))
 pygame.display.flip()
 while True:
 for e in pygame.event.get():
 if e.type == pygame.QUIT:
 pygame.quit()
 exit()
 if e.type == pygame.MOUSEBUTTONDOWN:
 if view_score_btn.collidepoint(e.pos):
 show_score(final_score)
 # Redraw the game over screen when returning from show_score
 screen.fill(WHITE)
 screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 3))
 screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
 if ai_used:
 screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT // 2 + 50))
 pygame.draw.rect(screen, YELLOW, view_score_btn, border_radius=8)
 pygame.draw.rect(screen, GRAY, home_btn, border_radius=8)
 screen.blit(FONT.render("View Score", True, BLACK),
 (view_score_btn.x + 75, view_score_btn.y + 5))
 screen.blit(FONT.render("Back Home", True, WHITE),
 (home_btn.x + 75, home_btn.y + 5))
 pygame.display.flip()
 continue
 if home_btn.collidepoint(e.pos):
 return
def start_game(rows, cols, difficulty):
 # Initialize score locally for this game session
 current_score = 0 # This is the player's score for the current game
 maze = generate_maze_with_multiple_paths(rows, cols)
 player = [0, 0]
 goal = [rows - 1, cols - 1]
 coins = place_coins(maze, player, goal)
 obstacles = create_obstacles(maze, difficulty, rows, cols)
 speed_factor = OBSTACLE_SPEED[difficulty]
 start_time = time.time()
 last_frame_time = start_time
 move_count = 0
 ai_used = False
 game_active = True
 player_hit_cooldown = 0 # Cooldown after being hit by an obstacle
 showing_paths = False
 paths = None
 while game_active:
 current_time = time.time()
 dt = current_time - last_frame_time
 last_frame_time = current_time
 screen.fill(WHITE)
 draw_maze(maze, player, goal, coins, obstacles, paths if showing_paths else None)
 pygame.draw.rect(screen, (245, 245, 245), (WIDTH - 200, 0, 200, HEIGHT))
 time_left = max(0, TIMER_LIMIT - int(current_time - start_time))
 screen.blit(SMALL_FONT.render(f"Time: {time_left}s", True, BLACK), (WIDTH - 180, 30))
 screen.blit(SMALL_FONT.render(f"Moves: {move_count}", True, BLACK), (WIDTH - 180, 70))
 screen.blit(SMALL_FONT.render(f"Score: {current_score}", True, BLACK), (WIDTH - 180, 110))
 help_btn = pygame.Rect(WIDTH - 160, 160, 140, 40)
 pygame.draw.rect(screen, BLUE, help_btn, border_radius=8)
 screen.blit(SMALL_FONT.render("Help", True, WHITE), (help_btn.x + 30, help_btn.y + 10))
 quit_btn = pygame.Rect(WIDTH - 160, 220, 140, 40)
 pygame.draw.rect(screen, RED, quit_btn, border_radius=8)
 screen.blit(SMALL_FONT.render("Exit Game", True, WHITE), (quit_btn.x + 45, quit_btn.y + 10))
 restart_btn = pygame.Rect(WIDTH - 160, 280, 140, 40)
 pygame.draw.rect(screen, GREEN, restart_btn, border_radius=8)
 screen.blit(SMALL_FONT.render("New Game", True, WHITE), (restart_btn.x + 35, restart_btn.y + 10))
 pygame.display.flip()
 # Update obstacles
 for obstacle in obstacles:
 obstacle.update(dt, speed_factor)
 # Check for collision with player
 if obstacle.position == player and player_hit_cooldown <= 0:
 if obstacle.deadly:
 game_active = False
 game_over_screen(False, current_score, ai_used)
 return
 else:
 current_score = max(0, current_score - OBSTACLE_PENALTY)
 player_hit_cooldown = 1 # 1 second cooldown
 # Update cooldown
 if player_hit_cooldown > 0:
 player_hit_cooldown -= dt
 if time_left == 0:
 game_active = False
 game_over_screen(False, current_score, ai_used)
 return
 if player == goal:
 game_active = False
 game_over_screen(True, current_score, ai_used)
 return
 for e in pygame.event.get():
 if e.type == pygame.QUIT:
 pygame.quit()
 exit()
 if e.type == pygame.MOUSEBUTTONDOWN:
 if help_btn.collidepoint(e.pos):
 ai_used = True
 showing_paths = not showing_paths
 if showing_paths and paths is None:
 paths = find_paths(maze, player, goal)
 if quit_btn.collidepoint(e.pos):
 return
 if restart_btn.collidepoint(e.pos):
 start_game(rows, cols, difficulty)
 return
 if e.type == pygame.KEYDOWN:
 r, c = player
 new_r, new_c = r, c
 if e.key == pygame.K_UP and r > 0 and maze[r - 1][c] == 0:
 new_r -= 1
 if e.key == pygame.K_DOWN and r < rows - 1 and maze[r + 1][c] == 0:
 new_r += 1
 if e.key == pygame.K_LEFT and c > 0 and maze[r][c - 1] == 0:
 new_c -= 1
 if e.key == pygame.K_RIGHT and c < cols - 1 and maze[r][c + 1] == 0:
 new_c += 1
 if [new_r, new_c] != player:
 player = [new_r, new_c]
 move_count += 1
 # Reset paths when player moves
 paths = None
 showing_paths = False
 if (new_r, new_c) in coins:
 coins.remove((new_r, new_c))
 current_score += COIN_SCORE
 clock.tick(FPS)
def home_screen():
 while True:
 screen.fill(WHITE)
 title = FONT.render("Maze Solver Game", True, BLACK)
 screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
 easy_btn = pygame.Rect(WIDTH // 2 - 100, 200, 200, 50)
 medium_btn = pygame.Rect(WIDTH // 2 - 100, 270, 200, 50)
 hard_btn = pygame.Rect(WIDTH // 2 - 100, 340, 200, 50)
 quit_btn = pygame.Rect(WIDTH // 2 - 100, 410, 200, 50)
 pygame.draw.rect(screen, GREEN, easy_btn)
 pygame.draw.rect(screen, BLUE, medium_btn)
 pygame.draw.rect(screen, (255, 165, 0), hard_btn)
 pygame.draw.rect(screen, RED, quit_btn)
 screen.blit(SMALL_FONT.render("Easy", True, WHITE), (easy_btn.x + 70, easy_btn.y + 10))
 screen.blit(SMALL_FONT.render("Medium", True, WHITE), (medium_btn.x + 55, medium_btn.y + 10))
 screen.blit(SMALL_FONT.render("Hard", True, WHITE), (hard_btn.x + 70, hard_btn.y + 10))
 screen.blit(SMALL_FONT.render("Quit", True, WHITE), (quit_btn.x + 70, quit_btn.y + 10))
 pygame.display.flip()
 for e in pygame.event.get():
 if e.type == pygame.QUIT:
 pygame.quit()
 exit()
 if e.type == pygame.MOUSEBUTTONDOWN:
 if easy_btn.collidepoint(e.pos):
 start_game(21, 21, "easy")
 if medium_btn.collidepoint(e.pos):
 start_game(29, 29, "medium")
 if hard_btn.collidepoint(e.pos):
 start_game(35, 35, "hard") # Changed from 45x45 to 35x35 for hard difficulty
 if quit_btn.collidepoint(e.pos):
 pygame.quit()
 exit()
home_screen()

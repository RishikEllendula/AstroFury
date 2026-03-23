import pygame
import random
import math
import sys
import os

# ── Initialize ──────────────────────────────────────────────────────────────
pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AstroFury")

clock = pygame.time.Clock()
FPS = 60

# ── Assets ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_img(name, size):
    path = os.path.join(BASE_DIR, name)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, size)

player_img   = load_img("player.png",     (64, 64))
enemy_img    = load_img("enemy.png",      (48, 48))
bullet_img   = load_img("bullet.png",     (16, 32))
background_img = load_img("background.png", (WIDTH, HEIGHT))

# ── Fonts ─────────────────────────────────────────────────────────────────────
font       = pygame.font.Font(None, 36)
big_font   = pygame.font.Font(None, 80)
small_font = pygame.font.Font(None, 28)

# ── Colors ────────────────────────────────────────────────────────────────────
WHITE  = (255, 255, 255)
RED    = (255,  60,  60)
YELLOW = (255, 220,  50)
GRAY   = (180, 180, 180)
BLACK  = (  0,   0,   0)
CYAN   = ( 80, 220, 255)

# ── High Score ────────────────────────────────────────────────────────────────
SCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")

def load_high_score():
    try:
        with open(SCORE_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0

def save_high_score(score):
    with open(SCORE_FILE, "w") as f:
        f.write(str(score))

# ── Helper: centered text ─────────────────────────────────────────────────────
def draw_text(text, fnt, color, x, y, center=True):
    surf = fnt.render(text, True, color)
    rect = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
    screen.blit(surf, rect)

# ── Scrolling Background ──────────────────────────────────────────────────────
bg_y1 = 0
bg_y2 = -HEIGHT   # second copy stacked above

def update_background(speed=1):
    global bg_y1, bg_y2
    bg_y1 += speed
    bg_y2 += speed
    if bg_y1 >= HEIGHT:
        bg_y1 = -HEIGHT
    if bg_y2 >= HEIGHT:
        bg_y2 = -HEIGHT
    screen.blit(background_img, (0, bg_y1))
    screen.blit(background_img, (0, bg_y2))

# ── Enemy factory ─────────────────────────────────────────────────────────────
NUM_ENEMIES   = 6
BASE_SPEED_X  = 1.5

def make_enemies(count=NUM_ENEMIES, speed_x=BASE_SPEED_X):
    return [
        {
            "x":       random.randint(0, WIDTH - 48),
            "y":       random.randint(50, 150),
            "speed_x": speed_x * random.choice([-1, 1]),
            "speed_y": 22,
        }
        for _ in range(count)
    ]

# ── Draw HUD (lives + score + level + high score) ────────────────────────────
HEART = "♥"

def draw_hud(score, lives, level, high_score):
    # Score
    draw_text(f"Score: {score}", font, WHITE, 10, 10, center=False)
    # Level
    draw_text(f"Level: {level}", font, YELLOW, WIDTH // 2, 10, center=False)
    # High score
    draw_text(f"Best: {high_score}", font, CYAN, WIDTH - 130, 10, center=False)
    # Lives as hearts
    hearts = HEART * lives
    draw_text(hearts, font, RED, WIDTH - 10 - font.size(hearts)[0], 10, center=False)

# ─────────────────────────────────────────────────────────────────────────────
# SCREENS
# ─────────────────────────────────────────────────────────────────────────────

def menu_screen(high_score):
    """Blocking menu loop. Returns True to start, False to quit."""
    while True:
        update_background(speed=1)
        draw_text("ASTROFURY", big_font, YELLOW, WIDTH // 2, HEIGHT // 2 - 120)
        draw_text("SPACE  →  Shoot", small_font, WHITE,  WIDTH // 2, HEIGHT // 2 - 20)
        draw_text("← →  →  Move",   small_font, WHITE,  WIDTH // 2, HEIGHT // 2 + 20)
        draw_text("Press  ENTER  to  Play", font, CYAN, WIDTH // 2, HEIGHT // 2 + 80)
        draw_text(f"High Score: {high_score}", small_font, GRAY, WIDTH // 2, HEIGHT // 2 + 130)
        pygame.display.update()
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True

def game_over_screen(score, high_score):
    """Show game-over for 4 s or until ENTER/ESC pressed. Returns True=retry, False=quit."""
    deadline = pygame.time.get_ticks() + 4000
    while True:
        remaining = max(0, (deadline - pygame.time.get_ticks()) // 1000)
        update_background(speed=1)
        draw_text("GAME  OVER",       big_font,   RED,   WIDTH // 2, HEIGHT // 2 - 110)
        draw_text(f"Score: {score}",  font,       WHITE, WIDTH // 2, HEIGHT // 2 - 20)
        draw_text(f"Best:  {high_score}", font,   CYAN,  WIDTH // 2, HEIGHT // 2 + 25)
        draw_text("ENTER → Play Again   ESC → Quit", small_font, GRAY,
                  WIDTH // 2, HEIGHT // 2 + 85)
        draw_text(f"Auto-closing in {remaining}s…", small_font, GRAY,
                  WIDTH // 2, HEIGHT // 2 + 120)
        pygame.display.update()
        clock.tick(FPS)
        if pygame.time.get_ticks() >= deadline:
            return False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False

# ─────────────────────────────────────────────────────────────────────────────
# MAIN GAME FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def run_game():
    global bg_y1, bg_y2

    # Reset scrolling background
    bg_y1 = 0
    bg_y2 = -HEIGHT

    # State
    player_x    = WIDTH // 2 - 32
    player_y    = HEIGHT - 100
    player_speed = 5
    lives        = 3
    score        = 0
    level        = 1
    kills_for_next_level = 5

    bullet_x     = 0
    bullet_y     = player_y
    bullet_speed = 12
    bullet_state = "ready"

    current_speed = BASE_SPEED_X
    enemies = make_enemies(speed_x=current_speed)

    # Invincibility frames after taking a hit (prevents instant death)
    invincible_until = 0

    running = True
    while running:
        clock.tick(FPS)
        now = pygame.time.get_ticks()

        # ── Draw background
        update_background(speed=1 + level * 0.3)

        # ── Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # ── Player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_RIGHT]:
            player_x += player_speed
        if keys[pygame.K_SPACE] and bullet_state == "ready":
            bullet_x     = player_x
            bullet_y     = player_y
            bullet_state = "fire"

        # Clamp player
        player_x = max(0, min(player_x, WIDTH - 64))

        # ── Bullet
        if bullet_state == "fire":
            bullet_y -= bullet_speed
            screen.blit(bullet_img, (bullet_x + 24, bullet_y))
        if bullet_y <= 0:
            bullet_y     = player_y
            bullet_state = "ready"

        # ── Enemies
        for e in enemies:
            e["x"] += e["speed_x"]
            if e["x"] <= 0 or e["x"] >= WIDTH - 48:
                e["speed_x"] *= -1
                e["y"]       += e["speed_y"]

            # Bullet collision
            if bullet_state == "fire":
                dist = math.hypot(e["x"] - bullet_x, e["y"] - bullet_y)
                if dist < 30:
                    bullet_y     = player_y
                    bullet_state = "ready"
                    score        += 1
                    kills_for_next_level -= 1
                    e["x"] = random.randint(0, WIDTH - 48)
                    e["y"] = random.randint(50, 150)

                    # Level up every 5 kills
                    if kills_for_next_level <= 0:
                        level               += 1
                        kills_for_next_level = 5 + level * 2
                        current_speed       += 0.5
                        # Speed up existing enemies
                        for en in enemies:
                            en["speed_x"] = math.copysign(current_speed, en["speed_x"])

            # Player collision (only if not invincible)
            if now > invincible_until:
                dist = math.hypot(e["x"] - player_x, e["y"] - player_y)
                if dist < 40:
                    lives           -= 1
                    invincible_until = now + 2000   # 2 s grace
                    e["x"] = random.randint(0, WIDTH - 48)
                    e["y"] = random.randint(50, 150)
                    if lives <= 0:
                        running = False

            screen.blit(enemy_img, (e["x"], e["y"]))

        # ── Player (flicker when invincible)
        show_player = True
        if now < invincible_until:
            show_player = (now // 150) % 2 == 0   # flicker every 150 ms
        if show_player:
            screen.blit(player_img, (player_x, player_y))

        # ── HUD
        draw_hud(score, lives, level, load_high_score())

        pygame.display.update()

    return score

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def main():
    high_score = load_high_score()
    menu_screen(high_score)

    while True:
        score      = run_game()
        high_score = load_high_score()

        if score > high_score:
            high_score = score
            save_high_score(high_score)

        play_again = game_over_screen(score, high_score)
        if not play_again:
            break

    pygame.quit()
    print(f"Thanks for playing AstroFury! Final score: {score}")
    sys.exit()


if __name__ == "__main__":
    main()

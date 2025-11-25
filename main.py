import os
import sys
import pygame
import random
import math
from player import Player
from enemy import Enemy
from bullet import Bullet

# ---------------------------
# Asset path util (no arquivo extra)
# ---------------------------
def asset_path(filename):
    """
    Retorna caminho correto para assets:
    - quando empacotado pelo PyInstaller -> usa sys._MEIPASS
    - quando roda em .py -> usa o diretório do arquivo main.py
    """
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)

# ---------------------------
# Safe loaders
# ---------------------------
def safe_load_image(path, convert_alpha=True):
    full = asset_path(path)
    try:
        img = pygame.image.load(full)
        return img.convert_alpha() if convert_alpha else img.convert()
    except Exception as e:
        print(f"[WARN] Falha ao carregar imagem '{path}': {e} (tentado: {full})")
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 128))
        return surf

def safe_load_sound(path):
    full = asset_path(path)
    try:
        return pygame.mixer.Sound(full)
    except Exception as e:
        print(f"[WARN] Falha ao carregar som '{path}': {e} (tentado: {full})")
        class Silent:
            def play(self, *a, **k): pass
            def set_volume(self, *a, **k): pass
        return Silent()

# ---------------------------
# Inicialização Pygame
# ---------------------------
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Top Down Shooter")

clock = pygame.time.Clock()
FPS = 60

# ---------------------------
# Constantes / Configurações
# ---------------------------
PLAYER_SIZE = 50
PLAYER_SPEED = 5
PLAYER_START_LIFE = 3

ENEMY_SIZE = 40
ENEMY_SPEED_INIT = 1.0

BULLET_SIZE = 10
BULLET_SPEED = 10

BOX_SIZE = 50
OBSTACLES_COUNT = 10

MAX_SHOTS = 10
RELOAD_TIME_MS = 2000

ENEMIES_TO_SPAWN_INIT = 20
MAX_WAVES = 4

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

font = pygame.font.SysFont(None, 36)
game_over_font = pygame.font.SysFont(None, 72)

# ---------------------------
# Assets (usando loaders seguros)
# ---------------------------
heart_img = safe_load_image("assets/heartDisplayFull.png")
heart_img = pygame.transform.scale(heart_img, (32, 32))

background = safe_load_image("assets/background.png", convert_alpha=False)
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

player_img = safe_load_image("assets/soldier1_gun.png")
player_img = pygame.transform.scale(player_img, (PLAYER_SIZE, PLAYER_SIZE))

player_reload_img = safe_load_image("assets/soldier1_reload.png")
player_reload_img = pygame.transform.scale(player_reload_img, (PLAYER_SIZE, PLAYER_SIZE))

box_img = safe_load_image("assets/tile_129.png")
box_img = pygame.transform.scale(box_img, (BOX_SIZE, BOX_SIZE))

zombie_hold_img = safe_load_image("assets/zoimbie1_hold.png")
zombie_hold_img = pygame.transform.scale(zombie_hold_img, (ENEMY_SIZE, ENEMY_SIZE))
zombie_stand_img = safe_load_image("assets/zoimbie1_stand.png")
zombie_stand_img = pygame.transform.scale(zombie_stand_img, (ENEMY_SIZE, ENEMY_SIZE))

pistol_sound = safe_load_sound("assets/pistol-shot.mp3")
pistol_reloading = safe_load_sound("assets/gun-reload.mp3")
background_zombie = safe_load_sound("assets/zombie.mp3")
game_over_sound = safe_load_sound("assets/game-over.mp3")
game_win_sound = safe_load_sound("assets/you-win-sequence.mp3")

# volumes
try:
    pistol_sound.set_volume(0.1)
    pistol_reloading.set_volume(0.5)
    background_zombie.set_volume(0.08)
    game_over_sound.set_volume(0.7)
    game_win_sound.set_volume(0.7)
except Exception:
    pass

# ---------------------------
# Estado do jogo
# ---------------------------
player_size = PLAYER_SIZE
player_speed = PLAYER_SPEED

enemy_size = ENEMY_SIZE
enemy_speed = ENEMY_SPEED_INIT

bullet_size = BULLET_SIZE
bullet_speed = BULLET_SPEED

enemies = []
bullets = []
obstacles = []

kill_count = 0
wave = 1
enemies_to_spawn = ENEMIES_TO_SPAWN_INIT
game_win = False
game_over = False

played_game_win = False
played_game_over = False

zombie_switch_time = 3000
last_zombie_switch = pygame.time.get_ticks()
zombie_current_img = zombie_hold_img

shots_fired = 0
reloading = False
reload_start = 0
reload_sound_played = False

# tocar ambiência (se disponível)
try:
    background_zombie.play(-1)
except Exception:
    pass

# ---------------------------
# Funções utilitárias do jogo
# ---------------------------
def spawn_obstacles(num=OBSTACLES_COUNT):
    obstacles.clear()
    for _ in range(num):
        attempts = 0
        while True:
            attempts += 1
            if attempts > 200:
                break
            x = random.randint(0, WIDTH - BOX_SIZE)
            y = random.randint(0, HEIGHT - BOX_SIZE)
            new_box = pygame.Rect(x, y, BOX_SIZE, BOX_SIZE)
            player_rect = pygame.Rect(WIDTH // 2, HEIGHT // 2, PLAYER_SIZE, PLAYER_SIZE)
            if not new_box.colliderect(player_rect) and not any(new_box.colliderect(o) for o in obstacles):
                obstacles.append(new_box)
                break

def init_enemies():
    enemies.clear()
    attempts = 0
    spawned = 0
    while spawned < enemies_to_spawn and attempts < enemies_to_spawn * 10:
        e = Enemy.spawn(enemy_size, enemy_speed, WIDTH, HEIGHT, enemies)
        attempts += 1
        if e:
            enemies.append(e)
            spawned += 1

def reset_game():
    global game_over, game_win, player, bullets, enemies, kill_count
    global shots_fired, reloading, reload_sound_played
    global last_zombie_switch, zombie_current_img
    global wave, enemy_speed, enemies_to_spawn
    global played_game_over, played_game_win

    game_over = False
    game_win = False

    # recriar player
    player = Player(WIDTH // 2, HEIGHT // 2, PLAYER_SIZE, PLAYER_SPEED)

    bullets.clear()
    enemies.clear()
    kill_count = 0
    shots_fired = 0
    reloading = False
    reload_sound_played = False

    last_zombie_switch = pygame.time.get_ticks()
    zombie_current_img = zombie_hold_img

    # reset das waves
    wave = 1
    enemy_speed = ENEMY_SPEED_INIT
    enemies_to_spawn = ENEMIES_TO_SPAWN_INIT

    played_game_over = False
    played_game_win = False

    spawn_obstacles(OBSTACLES_COUNT)
    init_enemies()


# cria o player e o mapa inicial
player = Player(WIDTH // 2, HEIGHT // 2, PLAYER_SIZE, PLAYER_SPEED)
spawn_obstacles(OBSTACLES_COUNT)
init_enemies()

# ---------------------------
# Eventos / Loop principal (separado por funções)
# ---------------------------
def handle_events():
    global running, shots_fired, reloading, reload_start, reload_sound_played, game_over, game_win
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and not game_over and not game_win:
            if not reloading:
                if shots_fired < MAX_SHOTS:
                    try:
                        pistol_sound.play()
                    except Exception:
                        pass
                    mx, my = pygame.mouse.get_pos()
                    bullets.append(Bullet(player.centerx, player.centery, mx, my, bullet_size, bullet_speed))
                    shots_fired += 1
                if shots_fired >= MAX_SHOTS:
                    reloading = True
                    reload_start = pygame.time.get_ticks()
                    reload_sound_played = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and (game_over or game_win):
                reset_game()

    return True

def update(dt):
    global reloading, shots_fired, reload_sound_played, last_zombie_switch, zombie_current_img
    global game_over, kill_count, wave, enemies_to_spawn, enemy_speed, game_win, played_game_over, played_game_win

    if reloading:
        if not reload_sound_played:
            try:
                pistol_reloading.play()
            except Exception:
                pass
            reload_sound_played = True
        if pygame.time.get_ticks() - reload_start >= RELOAD_TIME_MS:
            shots_fired = 0
            reloading = False
            reload_sound_played = False

    current_time = pygame.time.get_ticks()
    if current_time - last_zombie_switch >= zombie_switch_time:
        zombie_current_img = zombie_stand_img if zombie_current_img == zombie_hold_img else zombie_hold_img
        last_zombie_switch = current_time

    if not game_over and not game_win:
        player.handle_input(WIDTH, HEIGHT)
        player.move_and_collide(obstacles, WIDTH, HEIGHT)
        player.update_invincible()

        # inimigos se movendo
        for enemy in enemies[:]:
            enemy.move_towards_player(player, enemies, obstacles)
            if player.colliderect(enemy):
                player.take_damage()
                if getattr(player, "life", None) is not None:
                    if player.life <= 0:
                        game_over = True
                else:
                    game_over = True
                # remove o inimigo que bateu no player
                if enemy in enemies:
                    enemies.remove(enemy)

        # balas
        for bullet in bullets[:]:
            bullet.move()
            if bullet.offscreen(WIDTH, HEIGHT):
                if bullet in bullets: bullets.remove(bullet)
                continue

            for enemy in enemies[:]:
                if bullet.rect.colliderect(enemy):
                    if bullet in bullets: bullets.remove(bullet)
                    died = False
                    if hasattr(enemy, "hit_react"):
                        try:
                            died = enemy.hit_react(bullet.rect.x, bullet.rect.y)
                        except Exception:
                            died = True
                    else:
                        died = True

                    if died and enemy in enemies:
                        enemies.remove(enemy)
                        kill_count += 1
                    break

        # waves
        if len(enemies) == 0:
            wave += 1
            if wave > MAX_WAVES:
                game_win = True
            else:
                enemies_to_spawn = int(5 + (wave * 7))
                enemy_speed += 0.20
                init_enemies()

def draw():
    global played_game_win, played_game_over
    screen.blit(background, (0, 0))

    for box in obstacles:
        screen.blit(box_img, (box.x, box.y))

    mx, my = pygame.mouse.get_pos()
    dx = mx - player.centerx
    dy = my - player.centery
    angle = math.degrees(math.atan2(-dy, dx))
    current_player_img = player_reload_img if reloading else player_img
    rotated_img = pygame.transform.rotate(current_player_img, angle)
    rotated_rect = rotated_img.get_rect(center=(player.centerx, player.centery))
    screen.blit(rotated_img, rotated_rect)

    for enemy in enemies[:]:
        dx = player.centerx - enemy.centerx
        dy = player.centery - enemy.centery
        angle = math.degrees(math.atan2(-dy, dx))
        rotated_zombie = pygame.transform.rotate(zombie_current_img, angle)
        rotated_rect = rotated_zombie.get_rect(center=(enemy.centerx, enemy.centery))
        screen.blit(rotated_zombie, rotated_rect)

    for bullet in bullets:
        try:
            pygame.draw.rect(screen, YELLOW, bullet.rect)
        except Exception:
            pass

    if reloading:
        reload_text = font.render("Recarregando...", True, RED)
        screen.blit(reload_text, (WIDTH // 2 - reload_text.get_width() // 2, 10))

    life_count = getattr(player, "life", PLAYER_START_LIFE)
    for i in range(life_count):
        screen.blit(heart_img, (10 + i * 35, 10))

    wave_text = font.render(f"Wave: {wave}", True, BLACK)
    screen.blit(wave_text, (10, 90))
    kills_text = font.render(f"Inimigos mortos: {kill_count}", True, BLACK)
    screen.blit(kills_text, (10, 50))

    if len(enemies) == 0 and not (game_win or game_over):
        next_wave_text = font.render("Next Wave!", True, RED)
        screen.blit(next_wave_text, (WIDTH // 2 - next_wave_text.get_width() // 2, HEIGHT // 2 - 150))

    if game_win:
        if not played_game_win:
            try:
                game_win_sound.play()
            except Exception:
                pass
            played_game_win = True
        win_text = game_over_font.render("VOCÊ VENCEU!", True, BLUE)
        info_text = font.render(f"Inimigos mortos: {kill_count} - Vidas perdidas: {PLAYER_START_LIFE - getattr(player, 'life', 0)}", True, BLACK)
        restart_text = font.render("Pressione R para reiniciar", True, BLACK)
        screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2 - 60))
        screen.blit(info_text, (WIDTH // 2 - info_text.get_width() // 2, HEIGHT // 2))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))

    if game_over:
        if not played_game_over:
            try:
                game_over_sound.play()
            except Exception:
                pass
        played_game_over = True
        go_text = game_over_font.render("GAME OVER", True, RED)
        info_text = font.render(f"Inimigos mortos: {kill_count} - Pressione R para reiniciar", True, BLACK)
        screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(info_text, (WIDTH // 2 - info_text.get_width() // 2, HEIGHT // 2 + 20))

# ---------------------------
# Main loop
# ---------------------------
running = True
while running:
    dt = clock.tick(FPS)
    running = handle_events()
    update(dt)
    draw()
    pygame.display.flip()

pygame.quit()

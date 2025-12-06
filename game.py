import pygame
import os

pygame.init()

# --- КОНСТАНТЫ И НАСТРОЙКИ ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 920
FPS = 60
FONT_COLOR = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Slime Cave: The Challenge")
clock = pygame.time.Clock()

# Шрифты (используем стандартный системный шрифт)
font_ui = pygame.font.SysFont('arial', 32, bold=True)
font_big = pygame.font.SysFont('arial', 72, bold=True)

# --- ЗАГРУЗКА РЕСУРСОВ ---
base_path = os.path.dirname(__file__)
assets_dir = os.path.join(base_path, 'assets')
sound_dir = os.path.join(base_path, 'sounds')

# Изображения
try:
    bg_img = pygame.image.load(os.path.join(assets_dir, "bg.png")).convert()
    bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    
    player_img = pygame.image.load(os.path.join(assets_dir, "player.png")).convert_alpha()
    player_img = pygame.transform.scale(player_img, (64, 80))
    
    enemy_base = pygame.image.load(os.path.join(assets_dir, "enemy.png")).convert_alpha()
    enemy_img_right = pygame.transform.scale(enemy_base, (64, 80))
    enemy_img_left = pygame.transform.flip(enemy_img_right, True, False)
    
    # Лестница теперь выступает как "Стена испытаний" по центру
    wall_img = pygame.image.load(os.path.join(assets_dir, "ladder.png")).convert_alpha()
    wall_img = pygame.transform.scale(wall_img, (100, 400))
except Exception as e:
    print(f"Ошибка загрузки изображений: {e}")
    pygame.quit()
    exit()

# Звуки
pygame.mixer.music.load(os.path.join(sound_dir, 'фон.mp3'))
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)

sound_plop = pygame.mixer.Sound(os.path.join(sound_dir, 'slime-movement_my185dn_.mp3'))
sound_plop.set_volume(0.4)

# Проверка необязательных звуков
try:
    sound_climb = pygame.mixer.Sound(os.path.join(sound_dir, 'звуклестницы.mp3'))
    sound_climb.set_volume(0.3)
except:
    sound_climb = None

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ИГРЫ ---
game_state = "MENU" # Варианты: MENU, PLAYING, GAMEOVER, WIN
score = 0
lives = 3
invincible_timer = 0 # Время неуязвимости после удара

# --- ИГРОК ---
player_rect = player_img.get_rect(center=(200, 800))
player_vel_y = 0
speed = 5
gravity = 0.5
jump_force = -12
on_ground = False
on_wall = False

# --- СТЕНА (ПРЕПЯТСТВИЕ) ---
wall_rect = wall_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200))

# --- ВРАГИ ---
# Создаем список врагов с параметрами
enemies = []

def spawn_enemies():
    global enemies
    enemies = [
        # Враг 1 (быстрый)
        {'rect': enemy_img_right.get_rect(center=(800, 800)), 'speed': 4, 'dir': -1, 'img': enemy_img_left, 'alive': True},
        # Враг 2 (медленный)
        {'rect': enemy_img_right.get_rect(center=(1100, 800)), 'speed': 2, 'dir': 1, 'img': enemy_img_right, 'alive': True},
        # Враг 3 (на платформе/воздухе)
        {'rect': enemy_img_right.get_rect(center=(600, 500)), 'speed': 3, 'dir': 1, 'img': enemy_img_right, 'alive': True}
    ]

spawn_enemies()

# --- ФУНКЦИИ ---

def draw_text(text, font, color, x, y, center=False):
    img = font.render(text, True, color)
    if center:
        rect = img.get_rect(center=(x, y))
        screen.blit(img, rect)
    else:
        screen.blit(img, (x, y))

def reset_game():
    global score, lives, player_rect, player_vel_y, game_state, invincible_timer
    score = 0
    lives = 3
    player_rect.center = (100, 800)
    player_vel_y = 0
    invincible_timer = 0
    spawn_enemies()
    game_state = "PLAYING"

# --- ГЛАВНЫЙ ЦИКЛ ---
running = True
climb_sound_playing = False

while running:
    # 1. ОБРАБОТКА СОБЫТИЙ
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            
            # Управление состояниями
            if game_state == "MENU" and event.key == pygame.K_SPACE:
                reset_game()
            elif (game_state == "GAMEOVER" or game_state == "WIN") and event.key == pygame.K_r:
                reset_game()

    keys = pygame.key.get_pressed()

    # 2. ОТРИСОВКА ФОНА (всегда)
    screen.blit(bg_img, (0, 0))
    screen.blit(wall_img, wall_rect)

    # 3. ЛОГИКА ПО СОСТОЯНИЯМ
    
    # --- МЕНЮ ---
    if game_state == "MENU":
        # Затемнение фона
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0,0,0))
        screen.blit(overlay, (0,0))
        
        draw_text("SLIME CAVE ADVENTURE", font_big, GREEN, SCREEN_WIDTH//2, 300, center=True)
        draw_text("Цель: Набери 100 очков", font_ui, (200, 200, 200), SCREEN_WIDTH//2, 400, center=True)
        draw_text("Управление: WASD - Движение | W - Прыжок", font_ui, (200, 200, 200), SCREEN_WIDTH//2, 450, center=True)
        draw_text("[НАЖМИ ПРОБЕЛ ЧТОБЫ НАЧАТЬ]", font_ui, (255, 255, 255), SCREEN_WIDTH//2, 600, center=True)

    # --- ИГРА ---
    elif game_state == "PLAYING":
        
        # -- Движение игрока --
        dx = 0
        if keys[pygame.K_a]: dx = -speed
        if keys[pygame.K_d]: dx = speed
        
        player_rect.x += dx
        
        # Ограничение экрана
        if player_rect.left < 0: player_rect.left = 0
        if player_rect.right > SCREEN_WIDTH: player_rect.right = SCREEN_WIDTH

        # -- Физика и Стены --
        # Проверка касания стены
        on_wall = player_rect.colliderect(wall_rect)
        
        # Прыжок / Плюханье
        if keys[pygame.K_w]:
            if on_ground:
                player_vel_y = jump_force
                on_ground = False
                sound_plop.play()
            elif on_wall:
                player_vel_y = -3 # Ползти вверх
                if sound_climb and not climb_sound_playing:
                    sound_climb.play(-1)
                    climb_sound_playing = True
        
        # Логика гравитации
        if on_wall:
            if not keys[pygame.K_w]: # Если не ползем вверх, медленно сползаем
                player_vel_y = 1
                if climb_sound_playing and sound_climb:
                    sound_climb.stop()
                    climb_sound_playing = False
        else:
            player_vel_y += gravity
            if climb_sound_playing and sound_climb:
                sound_climb.stop()
                climb_sound_playing = False
        
        player_rect.y += player_vel_y

        # Пол/Земля
        if player_rect.bottom >= SCREEN_HEIGHT:
            player_rect.bottom = SCREEN_HEIGHT
            player_vel_y = 0
            on_ground = True
        else:
            on_ground = False

        # -- Враги --
        active_enemies = 0
        for e in enemies:
            if not e['alive']:
                continue
            
            active_enemies += 1
            
            # Движение врага
            e['rect'].x += e['speed'] * e['dir']
            
            # Отскок от стен экрана и центральной стены
            if e['rect'].left <= 0 or e['rect'].right >= SCREEN_WIDTH or e['rect'].colliderect(wall_rect):
                e['dir'] *= -1
                e['img'] = enemy_img_right if e['dir'] > 0 else enemy_img_left
            
            # Гравитация для врагов (если они в воздухе)
            if e['rect'].bottom < SCREEN_HEIGHT:
                e['rect'].y += 2
            else:
                e['rect'].bottom = SCREEN_HEIGHT

            # Отрисовка врага
            screen.blit(e['img'], e['rect'])

            # -- Столкновения с игроком --
            if player_rect.colliderect(e['rect']):
                # 1. Убийство врага (Прыжок сверху)
                # Условие: Игрок падает вниз и находится выше центра врага
                if player_vel_y > 0 and player_rect.bottom < e['rect'].centery + 20:
                    e['alive'] = False
                    player_vel_y = jump_force / 1.5 # Отскок
                    score += 10
                    sound_plop.play()
                
                # 2. Получение урона
                elif invincible_timer == 0:
                    lives -= 1
                    invincible_timer = 90 # 1.5 секунды неуязвимости (при 60 FPS)
                    # Отталкивание игрока
                    if player_rect.x < e['rect'].x:
                        player_rect.x -= 50
                    else:
                        player_rect.x += 50
                    player_vel_y = -5
                    
                    if lives <= 0:
                        game_state = "GAMEOVER"

        # Возрождение врагов (чтобы игра не кончалась)
        if active_enemies == 0:
            spawn_enemies()

        # Проверка победы
        if score >= 100:
            game_state = "WIN"

        # -- Отрисовка Игрока --
        # Мигание если неуязвим
        if invincible_timer > 0:
            invincible_timer -= 1
            if invincible_timer % 10 < 5: # Мигает каждые 5 кадров
                screen.blit(player_img, player_rect)
        else:
            screen.blit(player_img, player_rect)

        # -- UI (Интерфейс) --
        # Рисуем подложку для текста
        pygame.draw.rect(screen, (0, 0, 0), (10, 10, 200, 80))
        draw_text(f"СЧЕТ: {score}/100", font_ui, (255, 215, 0), 20, 20)
        draw_text(f"ЖИЗНИ: {lives}", font_ui, RED, 20, 55)

    # --- КОНЕЦ ИГРЫ ---
    elif game_state == "GAMEOVER":
        draw_text("ИГРА ОКОНЧЕНА", font_big, RED, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50, center=True)
        draw_text(f"Финальный счет: {score}", font_ui, (255, 255, 255), SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20, center=True)
        draw_text("Нажми R для рестарта", font_ui, (200, 200, 200), SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70, center=True)

    # --- ПОБЕДА ---
    elif game_state == "WIN":
        draw_text("ТЫ ПОБЕДИЛ!", font_big, GREEN, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50, center=True)
        draw_text(f"Счет: {score}", font_ui, (255, 255, 255), SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20, center=True)
        draw_text("Нажми R чтобы играть снова", font_ui, (200, 200, 200), SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70, center=True)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
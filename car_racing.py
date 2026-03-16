"""
=============================================================
  TURBO SPRINT - Python Car Racing Game
  Optimized for i3 processor + 8GB RAM
  Uses: pygame (lightweight, CPU-friendly)
=============================================================
"""

import pygame
import random
import sys
import math
import os

# ─── INIT ────────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

# ─── CONSTANTS ───────────────────────────────────────────
SCREEN_W, SCREEN_H = 800, 600
FPS = 60
ROAD_W = 400
ROAD_LEFT = (SCREEN_W - ROAD_W) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_W
LANE_W = ROAD_W // 4

# ─── COLORS ──────────────────────────────────────────────
C_BG         = (15,  15,  25)
C_ROAD       = (40,  42,  54)
C_ROAD_EDGE  = (60,  62,  74)
C_LANE_MARK  = (220, 200, 80)
C_GRASS_L    = (20,  80,  20)
C_GRASS_R    = (20,  80,  20)
C_WHITE      = (255, 255, 255)
C_RED        = (220,  50,  50)
C_GREEN      = (50,  200,  80)
C_YELLOW     = (255, 215,   0)
C_CYAN       = (0,   220, 220)
C_ORANGE     = (255, 140,   0)
C_GRAY       = (130, 130, 140)
C_DARK_GRAY  = (60,  60,  70)
C_PLAYER_CAR = (30,  144, 255)
C_HUD_BG     = (0,   0,   0, 160)
C_NEON_BLUE  = (0,   200, 255)
C_NEON_PINK  = (255,  50, 180)


# ─── SIMPLE SOUND GENERATOR ──────────────────────────────
def make_beep(freq=440, duration=0.1, volume=0.3):
    """Generate a simple beep sound without external files."""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = bytearray(n_samples)
    for i in range(n_samples):
        t = i / sample_rate
        val = int(127 + 127 * volume * math.sin(2 * math.pi * freq * t))
        buf[i] = val
    sound = pygame.mixer.Sound(buffer=bytes(buf))
    return sound

try:
    SND_ENGINE  = make_beep(80,  0.05, 0.1)
    SND_CRASH   = make_beep(120, 0.3,  0.4)
    SND_SCORE   = make_beep(880, 0.15, 0.3)
    SND_POWERUP = make_beep(660, 0.2,  0.3)
    sounds_ok = True
except Exception:
    sounds_ok = False


# ─── FONT HELPER ─────────────────────────────────────────
def load_font(size, bold=False):
    try:
        return pygame.font.SysFont("consolas", size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


# ─── DRAW HELPERS ────────────────────────────────────────
def draw_rounded_rect(surf, color, rect, radius=8, alpha=255):
    if alpha < 255:
        s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color[:3], alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
        surf.blit(s, (rect[0], rect[1]))
    else:
        pygame.draw.rect(surf, color, rect, border_radius=radius)


def draw_car(surf, x, y, w, h, color, is_player=False):
    """Draw a stylised top-down car."""
    # Body
    body_rect = pygame.Rect(x - w//2, y - h//2, w, h)
    draw_rounded_rect(surf, color, body_rect, radius=6)

    # Windshield
    ws_w, ws_h = int(w * 0.65), int(h * 0.22)
    ws_x = x - ws_w // 2
    ws_y = y - h // 2 + int(h * 0.08) if is_player else y + h // 2 - int(h * 0.30)
    pygame.draw.rect(surf, (180, 220, 255), (ws_x, ws_y, ws_w, ws_h), border_radius=3)

    # Tail lights / headlights
    light_w, light_h = int(w * 0.20), int(h * 0.10)
    light_y = y + h // 2 - light_h - 2 if is_player else y - h // 2 + 2
    light_color = (255, 60, 60) if is_player else (255, 220, 80)
    pygame.draw.rect(surf, light_color, (x - w // 2 + 2, light_y, light_w, light_h), border_radius=2)
    pygame.draw.rect(surf, light_color, (x + w // 2 - light_w - 2, light_y, light_w, light_h), border_radius=2)

    # Wheels
    wheel_w, wheel_h = int(w * 0.22), int(h * 0.18)
    for wx in [x - w // 2 - wheel_w + 2, x + w // 2 - 2]:
        for wy in [y - h // 2 + int(h * 0.12), y + h // 2 - int(h * 0.12) - wheel_h]:
            pygame.draw.rect(surf, C_DARK_GRAY, (wx, wy, wheel_w, wheel_h), border_radius=3)

    # Roof shine
    pygame.draw.line(surf, (*[min(255, c + 60) for c in color[:3]],),
                     (x - w//4, y - h//4), (x + w//4, y - h//4), 2)


# ─── PARTICLE SYSTEM ─────────────────────────────────────
class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size')

    def __init__(self, x, y, color):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.max_life = self.life = random.randint(20, 45)
        self.color = color
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= 1

    def draw(self, surf):
        alpha = int(255 * self.life / self.max_life)
        r = max(1, int(self.size * self.life / self.max_life))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=12):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update_draw(self, surf):
        alive = []
        for p in self.particles:
            p.update()
            if p.life > 0:
                p.draw(surf)
                alive.append(p)
        self.particles = alive


# ─── ROAD DASHES ─────────────────────────────────────────
class RoadDash:
    DASH_H = 40
    GAP_H  = 30
    CYCLE  = DASH_H + GAP_H

    def __init__(self, lane, y):
        self.lane = lane   # 0-2  (between lanes)
        self.y = y

    def update(self, speed):
        self.y += speed
        if self.y > SCREEN_H + self.DASH_H:
            self.y -= (SCREEN_H + self.CYCLE + self.DASH_H)

    def draw(self, surf):
        x = ROAD_LEFT + (self.lane + 1) * LANE_W
        pygame.draw.rect(surf, C_LANE_MARK, (x - 2, int(self.y), 4, self.DASH_H))


# ─── OBSTACLE CAR ────────────────────────────────────────
class ObstacleCar:
    COLORS = [(200, 50, 50), (50, 180, 50), (200, 130, 50),
              (160, 60, 200), (50, 180, 180), (220, 90, 90)]
    CAR_W, CAR_H = 44, 72

    def __init__(self, speed_base):
        self.lane = random.randint(0, 3)
        self.x = ROAD_LEFT + self.lane * LANE_W + LANE_W // 2
        self.y = -self.CAR_H - random.randint(0, 200)
        self.speed = random.uniform(speed_base * 0.3, speed_base * 0.7)
        self.color = random.choice(self.COLORS)

    def update(self, road_speed):
        self.y += road_speed - self.speed

    def draw(self, surf):
        draw_car(surf, int(self.x), int(self.y), self.CAR_W, self.CAR_H, self.color)

    @property
    def rect(self):
        return pygame.Rect(self.x - self.CAR_W//2 + 4,
                           self.y - self.CAR_H//2 + 4,
                           self.CAR_W - 8, self.CAR_H - 8)


# ─── POWER-UP ─────────────────────────────────────────────
class PowerUp:
    TYPES = {
        'shield':  (C_CYAN,   '🛡', 'SHIELD!',  5),
        'boost':   (C_YELLOW, '⚡', 'BOOST!',   4),
        'points':  (C_GREEN,  '★', '+500 PTS', 0),
    }
    SIZE = 28

    def __init__(self, road_speed):
        kind = random.choice(list(self.TYPES.keys()))
        self.kind = kind
        self.color, self.icon, self.label, self.duration = self.TYPES[kind]
        self.lane = random.randint(0, 3)
        self.x = ROAD_LEFT + self.lane * LANE_W + LANE_W // 2
        self.y = -self.SIZE - random.randint(50, 300)
        self.speed = road_speed
        self.pulse = 0

    def update(self, road_speed):
        self.y += road_speed
        self.pulse = (self.pulse + 3) % 360

    def draw(self, surf):
        pulse_r = self.SIZE + int(4 * math.sin(math.radians(self.pulse)))
        glow = pygame.Surface((pulse_r * 2 + 8, pulse_r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color[:3], 60),
                           (pulse_r + 4, pulse_r + 4), pulse_r + 4)
        surf.blit(glow, (int(self.x) - pulse_r - 4, int(self.y) - pulse_r - 4))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.SIZE)
        pygame.draw.circle(surf, C_WHITE, (int(self.x), int(self.y)), self.SIZE, 2)
        fnt = load_font(18, bold=True)
        txt = fnt.render(self.icon, True, C_WHITE)
        surf.blit(txt, txt.get_rect(center=(int(self.x), int(self.y))))

    @property
    def rect(self):
        return pygame.Rect(self.x - self.SIZE, self.y - self.SIZE,
                           self.SIZE * 2, self.SIZE * 2)


# ─── FLOATING TEXT ───────────────────────────────────────
class FloatText:
    def __init__(self, x, y, text, color=C_WHITE):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.life = 60
        self.font = load_font(22, bold=True)

    def update(self):
        self.y -= 1.2
        self.life -= 1

    def draw(self, surf):
        alpha = min(255, int(255 * self.life / 30))
        txt = self.font.render(self.text, True, self.color)
        txt.set_alpha(alpha)
        surf.blit(txt, txt.get_rect(center=(int(self.x), int(self.y))))


# ─── PLAYER ──────────────────────────────────────────────
class Player:
    CAR_W, CAR_H = 48, 78
    MOVE_SPEED = 5
    MAX_X = ROAD_RIGHT - CAR_W // 2 - 4
    MIN_X = ROAD_LEFT  + CAR_W // 2 + 4

    def __init__(self):
        self.x = SCREEN_W // 2
        self.y = SCREEN_H - 120
        self.shield = 0
        self.boost  = 0
        self.lives  = 3
        self.invincible = 0  # frames of invincibility after hit
        self.tilt = 0  # visual tilt when turning

    def handle_input(self, keys):
        dx = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx =  1
        self.tilt += (dx * 4 - self.tilt) * 0.2
        speed = self.MOVE_SPEED * (1.6 if self.boost > 0 else 1.0)
        self.x += dx * speed
        self.x = max(self.MIN_X, min(self.MAX_X, self.x))

    def update(self):
        if self.shield > 0:    self.shield -= 1
        if self.boost  > 0:    self.boost  -= 1
        if self.invincible > 0: self.invincible -= 1

    def draw(self, surf):
        if self.invincible > 0 and (self.invincible // 4) % 2 == 0:
            return  # Blink when invincible
        # Shield aura
        if self.shield > 0:
            s = pygame.Surface((self.CAR_W + 30, self.CAR_H + 30), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 220, 255, 80),
                                (0, 0, self.CAR_W + 30, self.CAR_H + 30))
            surf.blit(s, (int(self.x) - (self.CAR_W + 30)//2,
                          int(self.y) - (self.CAR_H + 30)//2))
        draw_car(surf, int(self.x), int(self.y), self.CAR_W, self.CAR_H,
                 C_PLAYER_CAR, is_player=True)

    @property
    def rect(self):
        return pygame.Rect(self.x - self.CAR_W//2 + 6,
                           self.y - self.CAR_H//2 + 6,
                           self.CAR_W - 12, self.CAR_H - 12)


# ─── HUD ─────────────────────────────────────────────────
def draw_hud(surf, score, speed, lives, distance, player, hi_score):
    fnt_big  = load_font(28, bold=True)
    fnt_med  = load_font(18, bold=True)
    fnt_sm   = load_font(14)

    # Top bar background
    draw_rounded_rect(surf, (0, 0, 0), (0, 0, SCREEN_W, 50), radius=0, alpha=180)

    # Score
    sc_txt = fnt_big.render(f"SCORE  {score:07d}", True, C_NEON_BLUE)
    surf.blit(sc_txt, (20, 10))

    # Hi-score
    hi_txt = fnt_sm.render(f"BEST {hi_score:07d}", True, C_GRAY)
    surf.blit(hi_txt, (20, 40))

    # Speed
    spd_txt = fnt_big.render(f"{int(speed * 6):3d} km/h", True, C_YELLOW)
    surf.blit(spd_txt, (SCREEN_W // 2 - spd_txt.get_width() // 2, 10))

    # Distance
    dist_txt = fnt_sm.render(f"{distance:.0f} m", True, C_GRAY)
    surf.blit(dist_txt, (SCREEN_W // 2 - dist_txt.get_width() // 2, 38))

    # Lives
    for i in range(3):
        color = C_RED if i < lives else C_DARK_GRAY
        px = SCREEN_W - 30 - i * 28
        pygame.draw.polygon(surf, color, [
            (px, 12), (px-9, 22), (px-9, 32), (px, 28),
            (px+9, 32), (px+9, 22)
        ])

    # Active power-up indicators
    py = 58
    if player.shield > 0:
        bar_w = int(80 * player.shield / (60 * 5))
        draw_rounded_rect(surf, C_DARK_GRAY, (10, py, 82, 14), radius=4)
        draw_rounded_rect(surf, C_CYAN, (10, py, bar_w, 14), radius=4)
        surf.blit(fnt_sm.render("SHIELD", True, C_CYAN), (96, py))
        py += 18
    if player.boost > 0:
        bar_w = int(80 * player.boost / (60 * 4))
        draw_rounded_rect(surf, C_DARK_GRAY, (10, py, 82, 14), radius=4)
        draw_rounded_rect(surf, C_YELLOW, (10, py, bar_w, 14), radius=4)
        surf.blit(fnt_sm.render("BOOST", True, C_YELLOW), (96, py))


# ─── BACKGROUND (stars / buildings) ──────────────────────
class Background:
    def __init__(self):
        self.stars = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H),
                       random.randint(1, 3)) for _ in range(60)]
        self.buildings_l = self._gen_buildings(side='left')
        self.buildings_r = self._gen_buildings(side='right')
        self.bg_y = 0

    def _gen_buildings(self, side):
        buildings = []
        x = 0 if side == 'left' else ROAD_RIGHT
        while x < (ROAD_LEFT if side == 'left' else SCREEN_W):
            w = random.randint(30, 60)
            h = random.randint(60, 200)
            buildings.append({'x': x, 'w': w, 'h': h,
                               'color': (random.randint(30, 60),
                                         random.randint(30, 60),
                                         random.randint(50, 80))})
            x += w + random.randint(5, 20)
        return buildings

    def draw(self, surf):
        surf.fill(C_BG)
        for (x, y, r) in self.stars:
            pygame.draw.circle(surf, (200, 200, 220), (x, y), r)

        # Grass / side strips
        pygame.draw.rect(surf, C_GRASS_L, (0, 0, ROAD_LEFT, SCREEN_H))
        pygame.draw.rect(surf, C_GRASS_R, (ROAD_RIGHT, 0, SCREEN_W - ROAD_RIGHT, SCREEN_H))

        # Buildings
        for b in self.buildings_l:
            pygame.draw.rect(surf, b['color'],
                             (b['x'], SCREEN_H - b['h'], b['w'], b['h']))
        for b in self.buildings_r:
            pygame.draw.rect(surf, b['color'],
                             (b['x'], SCREEN_H - b['h'], b['w'], b['h']))

        # Road
        pygame.draw.rect(surf, C_ROAD, (ROAD_LEFT, 0, ROAD_W, SCREEN_H))
        # Road edge lines
        pygame.draw.rect(surf, C_WHITE, (ROAD_LEFT, 0, 4, SCREEN_H))
        pygame.draw.rect(surf, C_WHITE, (ROAD_RIGHT - 4, 0, 4, SCREEN_H))


# ─── SCREENS ─────────────────────────────────────────────
def draw_title_screen(surf):
    surf.fill(C_BG)
    fnt_title = load_font(72, bold=True)
    fnt_sub    = load_font(24)
    fnt_info   = load_font(18)

    title = fnt_title.render("TURBO SPRINT", True, C_NEON_BLUE)
    surf.blit(title, title.get_rect(center=(SCREEN_W//2, 160)))

    sub = fnt_sub.render("Python Car Racing", True, C_NEON_PINK)
    surf.blit(sub, sub.get_rect(center=(SCREEN_W//2, 230)))

    # Controls box
    draw_rounded_rect(surf, C_DARK_GRAY, (200, 280, 400, 160), radius=10)
    controls = [
        ("←  /  A", "Move Left"),
        ("→  /  D", "Move Right"),
        ("ESC",      "Pause / Quit"),
    ]
    y = 300
    for key, action in controls:
        k_txt = fnt_info.render(key, True, C_YELLOW)
        a_txt = fnt_info.render(action, True, C_WHITE)
        surf.blit(k_txt, (230, y))
        surf.blit(a_txt, (370, y))
        y += 30

    # Avoid cars hint
    hint = fnt_info.render("Collect power-ups  •  Dodge traffic  •  Survive!", True, C_GRAY)
    surf.blit(hint, hint.get_rect(center=(SCREEN_W//2, 470)))

    press = fnt_sub.render("PRESS  ENTER  TO  START", True, C_GREEN)
    surf.blit(press, press.get_rect(center=(SCREEN_W//2, 540)))


def draw_pause_screen(surf):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    fnt = load_font(56, bold=True)
    msg = fnt.render("PAUSED", True, C_WHITE)
    surf.blit(msg, msg.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 30)))
    sm = load_font(22)
    hint = sm.render("Press P or ESC to resume", True, C_GRAY)
    surf.blit(hint, hint.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 40)))


def draw_game_over(surf, score, hi_score):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surf.blit(overlay, (0, 0))
    fnt_big = load_font(64, bold=True)
    fnt_med = load_font(28)
    fnt_sm  = load_font(20)

    go = fnt_big.render("GAME OVER", True, C_RED)
    surf.blit(go, go.get_rect(center=(SCREEN_W//2, 180)))

    sc = fnt_med.render(f"Score: {score:,}", True, C_WHITE)
    surf.blit(sc, sc.get_rect(center=(SCREEN_W//2, 280)))

    hi = fnt_med.render(f"Best:  {hi_score:,}", True, C_YELLOW)
    surf.blit(hi, hi.get_rect(center=(SCREEN_W//2, 330)))

    if score >= hi_score:
        new = fnt_sm.render("🏆  NEW HIGH SCORE!  🏆", True, C_YELLOW)
        surf.blit(new, new.get_rect(center=(SCREEN_W//2, 390)))

    again = fnt_med.render("ENTER = Play Again     ESC = Quit", True, C_GREEN)
    surf.blit(again, again.get_rect(center=(SCREEN_W//2, 470)))


# ─── DIFFICULTY CURVE ─────────────────────────────────────
def calc_difficulty(distance):
    """Returns (road_speed, spawn_interval) based on distance traveled."""
    level = min(int(distance / 800), 10)
    road_speed = 5 + level * 0.8
    spawn_interval = max(40, 120 - level * 7)
    return road_speed, spawn_interval


# ─── MAIN GAME LOOP ──────────────────────────────────────
def run_game(screen, clock, hi_score):
    bg     = Background()
    player = Player()
    parts  = ParticleSystem()
    floats = []

    obstacles  = []
    powerups   = []
    dashes     = []

    # Pre-populate lane dashes
    for lane in range(3):
        y = 0
        while y < SCREEN_H:
            dashes.append(RoadDash(lane, y))
            y += RoadDash.CYCLE

    score      = 0
    distance   = 0.0
    spawn_timer = 0
    pu_timer    = 0
    pu_interval = 300
    game_over  = False
    paused     = False
    frame      = 0

    while True:
        dt = clock.tick(FPS)
        frame += 1

        # ── EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p) and not game_over:
                    paused = not paused
                if event.key == pygame.K_RETURN:
                    if game_over:
                        return score  # restart handled by main()
                if event.key == pygame.K_ESCAPE and game_over:
                    pygame.quit(); sys.exit()

        if paused:
            draw_pause_screen(screen)
            pygame.display.flip()
            continue

        if game_over:
            draw_game_over(screen, score, hi_score)
            pygame.display.flip()
            continue

        # ── DIFFICULTY
        road_speed, spawn_interval = calc_difficulty(distance)
        if player.boost > 0:
            road_speed *= 1.5

        # ── UPDATE
        player.handle_input(pygame.key.get_pressed())
        player.update()
        distance += road_speed * 0.05

        # Score: time + distance
        if frame % 10 == 0:
            score += int(road_speed * 2)

        # Dashes
        for d in dashes:
            d.update(road_speed)

        # Obstacles
        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            obstacles.append(ObstacleCar(road_speed))

        alive_obs = []
        for obs in obstacles:
            obs.update(road_speed)
            if obs.y < SCREEN_H + 100:
                alive_obs.append(obs)
                # Collision
                if player.invincible == 0 and player.rect.colliderect(obs.rect):
                    if player.shield > 0:
                        player.shield = 0
                        player.invincible = 90
                        parts.emit(int(player.x), int(player.y), C_CYAN, 20)
                        floats.append(FloatText(player.x, player.y - 40,
                                                "SHIELD BLOCKED!", C_CYAN))
                        if sounds_ok: SND_CRASH.play()
                    else:
                        player.lives -= 1
                        player.invincible = 120
                        parts.emit(int(player.x), int(player.y), C_RED, 25)
                        floats.append(FloatText(player.x, player.y - 40,
                                                f"LIVES: {player.lives}", C_RED))
                        if sounds_ok: SND_CRASH.play()
                        if player.lives <= 0:
                            game_over = True
                            hi_score = max(hi_score, score)
            else:
                score += 10  # passed a car
        obstacles = alive_obs

        # Power-ups
        pu_timer += 1
        if pu_timer >= pu_interval:
            pu_timer = 0
            powerups.append(PowerUp(road_speed))

        alive_pu = []
        for pu in powerups:
            pu.update(road_speed)
            if pu.y < SCREEN_H + 60:
                alive_pu.append(pu)
                if player.rect.colliderect(pu.rect):
                    if pu.kind == 'shield':
                        player.shield = 60 * pu.duration
                    elif pu.kind == 'boost':
                        player.boost = 60 * pu.duration
                    elif pu.kind == 'points':
                        score += 500
                    parts.emit(int(pu.x), int(pu.y), pu.color, 18)
                    floats.append(FloatText(pu.x, pu.y - 30, pu.label, pu.color))
                    if sounds_ok: SND_POWERUP.play()
                    alive_pu.remove(pu)
        powerups = alive_pu

        # Float texts
        floats = [ft for ft in floats if ft.life > 0]
        for ft in floats:
            ft.update()

        # Engine exhaust particles (throttle)
        if frame % 4 == 0:
            parts.emit(int(player.x), int(player.y) + 36, C_DARK_GRAY, 2)

        # ── DRAW
        bg.draw(screen)
        for d in dashes:
            d.draw(screen)
        for obs in obstacles:
            obs.draw(screen)
        for pu in powerups:
            pu.draw(screen)
        player.draw(screen)
        parts.update_draw(screen)
        for ft in floats:
            ft.draw(screen)

        draw_hud(screen, score, road_speed, player.lives, distance, player, hi_score)

        pygame.display.flip()

    return score


# ─── MAIN ENTRY POINT ────────────────────────────────────
def main():
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("TURBO SPRINT – Python Car Racing")
    clock = pygame.time.Clock()
    hi_score = 0

    # Title screen
    while True:
        screen.fill(C_BG)
        draw_title_screen(screen)
        pygame.display.flip()
        clock.tick(30)
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        waiting = False
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

        final_score = run_game(screen, clock, hi_score)
        hi_score = max(hi_score, final_score)


if __name__ == "__main__":
    main()

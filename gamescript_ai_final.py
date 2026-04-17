"""
GameScript AI — Text to 2D Platformer (Python + Pygame)
Uses Claude API to parse game descriptions into varied game configs.
"""

import pygame
import sys
import json
import math
import random
import os
import threading
import anthropic

# ── CONSTANTS ────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1100, 620
PANEL_W = 340
GAME_W  = SCREEN_W - PANEL_W
GAME_H  = SCREEN_H

FPS = 60

# Colours
C_BG        = (13,  27,  42)
C_PANEL_BG  = (13,  27,  42)
C_BORDER    = (27,  47,  69)
C_ACCENT    = (0,  200, 255)
C_TEXT      = (255, 255, 255)
C_SUBTEXT   = (82,  96, 112)
C_INPUT_BG  = (21,  34,  51)
C_GAME_BG1  = (10,  22,  40)
C_GAME_BG2  = (13,  32,  64)
C_PLAT_TOP  = (61, 122,  61)
C_PLAT_BOT  = (26,  58,  26)
C_WIN       = (16, 185, 129)
C_LOSE      = (239, 68,  68)
C_YELLOW    = (245,158, 11)
C_GREEN     = (16, 185, 129)

GRAVITY = 0.55
JUMP_VEL = -13
PLAYER_SPEED = 4.5
BULLET_SPEED = 9

EXAMPLES = [
    "A blue hero jumps on platforms, collects golden coins, avoids red enemies. Collect all coins to win!",
    "A green spaceship shoots red robots falling from the sky. Shoot all enemies to win.",
    "A purple warrior runs and jumps on platforms. Avoid spikes and enemies and survive for 30 seconds.",
    "A yellow ninja collects magic crystals on floating platforms while dodging orange ghosts.",
    "A cyan robot shoots blue lasers at pink aliens on a space station. Defeat all aliens to win.",
]


# ── CLAUDE NLP ───────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a game-design parser. Given a text description of a 2D platformer game, extract the game configuration as JSON. 

Return ONLY valid JSON — no markdown, no explanation — matching this exact schema:
{
  "hero": {
    "name": "string (e.g. Hero, Ninja, Spaceship)",
    "color": "#RRGGBB"
  },
  "enemies": [
    {"name": "string", "color": "#RRGGBB", "speed": float (0.8-2.5), "count": int (2-6)}
  ],
  "collectibles": [
    {"name": "string", "color": "#RRGGBB", "count": int (4-12)}
  ],
  "mechanics": ["jump", "shoot", "avoid"],
  "winCondition": "collect" | "survive" | "reach_goal" | "defeat_all",
  "surviveDuration": int (seconds, only if winCondition is survive, e.g. 30),
  "gameType": "platformer" | "shooter" | "survival",
  "bgColor1": "#RRGGBB (top sky color)",
  "bgColor2": "#RRGGBB (bottom sky color)",
  "platformColor": "#RRGGBB",
  "platformCount": int (4-8),
  "title": "string (short evocative game title)"
}

Rules:
- Extract colors literally from the description (blue hero → #3B82F6, red enemy → #EF4444, golden coins → #F59E0B, etc.)
- If no color is specified for an element, pick something thematically fitting
- "mechanics" list must include "jump" for platformers, "shoot" only if shooting is described
- Match winCondition to the described objective precisely
- Make bgColor1/bgColor2 match the game's mood (space = dark blues, forest = dark greens, etc.)
- Vary platformCount, enemy count, speed, and collectible count based on difficulty implied in the description
- DO NOT return any text outside the JSON object
"""

def parse_with_claude(description: str) -> dict | None:
    """Call Claude API to parse the description. Returns config dict or None on error."""
    try:
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": description}]
        )
        raw = message.content[0].text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"[Claude API error] {e}")
        return None


# ── UTILITIES ────────────────────────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def draw_rounded_rect(surf, color, rect, radius=6, border_color=None, border_w=1):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(surf, border_color, rect, border_w, border_radius=radius)

def wrap_text(text, font, max_width):
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if font.size(test)[0] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


# ── GAME ENTITIES ─────────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.color = color
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -1)
        self.life = 1.0
        self.size = random.uniform(3, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 0.04

    def draw(self, surf, offset_x):
        if self.life <= 0:
            return
        alpha = int(self.life * 255)
        s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
        surf.blit(s, (int(self.x - offset_x - self.size), int(self.y - self.size)))


class Player:
    W, H = 24, 36

    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.on_ground = False
        self.facing_right = True
        self.jump_cd = 0
        self.color = color

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def draw(self, surf, offset_x, hurt_flash):
        x = int(self.x - offset_x)
        y = int(self.y)
        if hurt_flash:
            return  # flicker
        c = self.color
        # Body
        pygame.draw.rect(surf, c, (x+2, y+int(self.H*0.38), self.W-4, int(self.H*0.62)), border_radius=4)
        # Head
        pygame.draw.circle(surf, c, (x+self.W//2, y+int(self.H*0.28)), int(self.H*0.28))
        # Eye
        eye_x = x + int(self.W*0.65) if self.facing_right else x + int(self.W*0.2)
        pygame.draw.circle(surf, (255,255,255), (eye_x, y+int(self.H*0.25)), 3)
        dx = 1 if self.facing_right else -1
        pygame.draw.circle(surf, (0,0,0), (eye_x+dx, y+int(self.H*0.25)), 2)


class Enemy:
    W, H = 24, 28

    def __init__(self, x, y, plat, speed, color):
        self.x, self.y = float(x), float(y)
        self.vx = speed
        self.plat = plat
        self.alive = True
        self.color = color

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self):
        self.x += self.vx
        if self.x < self.plat['x'] or self.x + self.W > self.plat['x'] + self.plat['w']:
            self.vx *= -1

    def draw(self, surf, offset_x):
        if not self.alive:
            return
        x = int(self.x - offset_x)
        y = int(self.y)
        c = self.color
        pygame.draw.rect(surf, c, (x, y, self.W, int(self.H*0.65)), border_radius=4)
        pygame.draw.circle(surf, c, (x+self.W//2, y+int(self.H*0.25)), int(self.H*0.28))
        # X eyes
        for side in [-1, 1]:
            ex = x + self.W//2 + side*5
            ey = y + int(self.H*0.22)
            pygame.draw.line(surf, (255,255,255), (ex-3, ey-3), (ex+3, ey+3), 2)
            pygame.draw.line(surf, (255,255,255), (ex+3, ey-3), (ex-3, ey+3), 2)


class Collectible:
    SIZE = 8

    def __init__(self, x, y, color, idx):
        self.x, self.y = float(x), float(y)
        self.color = color
        self.collected = False
        self.bob_offset = idx * 0.5

    def rect(self):
        return pygame.Rect(int(self.x)-self.SIZE, int(self.y)-self.SIZE, self.SIZE*2, self.SIZE*2)

    def draw(self, surf, offset_x, time):
        if self.collected:
            return
        bob = math.sin(time * 0.05 + self.bob_offset) * 3
        x = int(self.x - offset_x)
        y = int(self.y + bob)
        pygame.draw.circle(surf, self.color, (x, y), self.SIZE)
        pygame.draw.circle(surf, (255,255,255,128), (x-3, y-3), 3)


class Bullet:
    def __init__(self, x, y, vx):
        self.x, self.y = float(x), float(y)
        self.vx = vx
        self.alive = True

    def update(self, game_w):
        self.x += self.vx
        if self.x < 0 or self.x > game_w + 2000:
            self.alive = False

    def draw(self, surf, offset_x):
        pygame.draw.circle(surf, C_ACCENT, (int(self.x - offset_x), int(self.y)), 4)


# ── GAME ENGINE ───────────────────────────────────────────────────────────────

class PlatformerGame:
    def __init__(self, cfg: dict, surface_w: int, surface_h: int):
        self.cfg = cfg
        self.W = surface_w
        self.H = surface_h
        self.state = "playing"  # playing, win, lose
        self.time = 0
        self.score = 0
        self.health = 3
        self.lives = 3
        self.invincible = 0
        self.shoot_cd = 0
        self.jump_cd = 0
        self.particles = []
        self.bullets = []
        self.camera_x = 0.0

        hero_color = hex_to_rgb(cfg["hero"].get("color", "#3B82F6"))
        enemy_cfg  = cfg["enemies"][0] if cfg["enemies"] else {}
        enemy_color = hex_to_rgb(enemy_cfg.get("color", "#EF4444"))
        enemy_speed = float(enemy_cfg.get("speed", 1.2))
        collect_cfg = cfg["collectibles"][0] if cfg["collectibles"] else {}
        collect_color = hex_to_rgb(collect_cfg.get("color", "#F59E0B"))
        collect_count = int(collect_cfg.get("count", 8))

        self.hero_color    = hero_color
        self.enemy_color   = enemy_color
        self.collect_color = collect_color
        self.can_shoot     = "shoot" in cfg.get("mechanics", [])
        self.win_type      = cfg.get("winCondition", "collect")
        self.survive_ticks = int(cfg.get("surviveDuration", 30)) * FPS
        self.plat_color    = hex_to_rgb(cfg.get("platformColor", "#2D5A2D"))

        self.bg1 = hex_to_rgb(cfg.get("bgColor1", "#0A1628"))
        self.bg2 = hex_to_rgb(cfg.get("bgColor2", "#0D2040"))

        # Build platforms
        PLAT_H = 16
        n_plats = int(cfg.get("platformCount", 6))
        ground_y = self.H - 40
        self.platforms = [{"x": 0, "y": ground_y, "w": self.W * 3, "h": 40}]  # ground

        # Max jump height: v^2 / (2*g) = 13^2 / (2*0.55) ≈ 153px
        # Keep platforms within 110px vertical steps so player can always reach them
        MAX_JUMP_H = 110
        PLAT_W_MIN, PLAT_W_MAX = 100, 160
        HORIZ_GAP = 180  # horizontal spacing between platforms

        prev_y = ground_y
        prev_x = 0
        for i in range(n_plats):
            plat_w = random.randint(PLAT_W_MIN, PLAT_W_MAX)
            step_up = random.randint(60, MAX_JUMP_H - 10)
            new_y = prev_y - step_up
            # Clamp: don't go above HUD bar (44px) + margin, don't go below ground
            new_y = max(80, min(ground_y - 60, new_y))
            new_x = prev_x + HORIZ_GAP + random.randint(-20, 40)
            self.platforms.append({
                "x": new_x, "y": new_y,
                "w": plat_w, "h": PLAT_H
            })
            prev_y = new_y
            prev_x = new_x

        # Build collectibles
        self.collectibles = []
        plats_for_items = self.platforms[1:]
        for i in range(collect_count):
            p = plats_for_items[i % len(plats_for_items)]
            margin = 16
            safe_w = max(1, p["w"] - margin * 2)
            cx = p["x"] + margin + (i * 23) % safe_w
            cy = p["y"] - 24
            self.collectibles.append(Collectible(cx, cy, collect_color, i))

        # Build enemies
        enemy_count = int(enemy_cfg.get("count", 4))
        self.enemies = []
        for i in range(min(enemy_count, len(plats_for_items))):
            p = plats_for_items[i % len(plats_for_items)]
            spd = enemy_speed * (1 if i % 2 == 0 else -1)
            e = Enemy(p["x"] + 10, p["y"] - 28, p, spd, enemy_color)
            e.start_x = p["x"] + 10
            e.start_y = p["y"] - 28
            self.enemies.append(e)

        # Goal flag — place on last platform so it's always reachable
        self.goal = None
        if self.win_type == "reach_goal":
            last_p = self.platforms[-1]
            gx = last_p["x"] + last_p["w"] // 2 - 10
            gy = last_p["y"] - 60
            self.goal = pygame.Rect(gx, gy, 20, 60)

        # Player — spawn just above the ground
        self.player = Player(60, ground_y - Player.H - 2, hero_color)

    def _collide_platform(self, obj_rect, vy):
        on_ground = False
        for p in self.platforms:
            pr = pygame.Rect(p["x"], p["y"], p["w"], p["h"])
            if obj_rect.colliderect(pr):
                if vy >= 0 and obj_rect.bottom - vy <= pr.top + 12:
                    return pr.top, True
        return None, False

    def update(self, keys):
        if self.state != "playing":
            return

        self.time += 1
        if self.invincible > 0:
            self.invincible -= 1
        if self.shoot_cd > 0:
            self.shoot_cd -= 1

        pl = self.player
        pl.vx = 0
        if keys.get(pygame.K_LEFT) or keys.get(pygame.K_a):
            pl.vx = -PLAYER_SPEED
            pl.facing_right = False
        if keys.get(pygame.K_RIGHT) or keys.get(pygame.K_d):
            pl.vx = PLAYER_SPEED
            pl.facing_right = True
        if (keys.get(pygame.K_UP) or keys.get(pygame.K_w) or keys.get(pygame.K_SPACE)):
            if pl.on_ground and pl.jump_cd <= 0:
                pl.vy = JUMP_VEL
                pl.jump_cd = 6
        if self.can_shoot and keys.get(pygame.K_z) and self.shoot_cd <= 0:
            bx = pl.x + (pl.W if pl.facing_right else 0)
            bvx = BULLET_SPEED if pl.facing_right else -BULLET_SPEED
            self.bullets.append(Bullet(bx, pl.y + 14, bvx))
            self.shoot_cd = 18

        if pl.jump_cd > 0:
            pl.jump_cd -= 1

        # Physics
        pl.vy += GRAVITY
        pl.x += pl.vx
        pl.y += pl.vy
        pl.x = max(0, min(self.W * 3 - pl.W, pl.x))

        # Platform collision
        pr = pl.rect()
        pl.on_ground = False
        for p in self.platforms:
            plr = pygame.Rect(p["x"], p["y"], p["w"], p["h"])
            if pr.colliderect(plr) and pl.vy >= 0 and pr.bottom - pl.vy <= plr.top + 12:
                pl.y = p["y"] - pl.H
                pl.vy = 0
                pl.on_ground = True
                break

        if pl.y > self.H + 50:
            self.health = 0

        # Camera
        self.camera_x = max(0, pl.x - self.W * 0.35)

        # Enemies
        for e in self.enemies:
            if not e.alive:
                continue
            e.update()
            # Bullet hits
            for b in self.bullets:
                if b.alive and e.rect().colliderect(pygame.Rect(int(b.x), int(b.y), 8, 8)):
                    e.alive = False
                    b.alive = False
                    self._spawn_particles(e.x + 12, e.y + 14, self.enemy_color)
                    self.score += 10
            # Player collision
            if self.invincible <= 0 and pl.rect().colliderect(e.rect()):
                if pl.vy > 0 and pl.y + pl.H < e.y + e.H * 0.5:
                    e.alive = False
                    self._spawn_particles(e.x + 12, e.y + 14, self.enemy_color)
                    self.score += 10
                    pl.vy = -8
                else:
                    self.health -= 1
                    self.invincible = 90
                    self._spawn_particles(pl.x + 12, pl.y + 18, self.hero_color)

        # Bullets OOB
        self.bullets = [b for b in self.bullets if b.alive]
        for b in self.bullets:
            b.update(self.W * 3)
        self.bullets = [b for b in self.bullets if b.alive]

        # Collectibles
        for c in self.collectibles:
            if not c.collected and pl.rect().colliderect(c.rect()):
                c.collected = True
                self.score += 20
                self._spawn_particles(c.x, c.y, self.collect_color, 6)

        # Win / lose checks
        if self.win_type == "collect" and all(c.collected for c in self.collectibles):
            self.state = "win"
        elif self.win_type == "reach_goal" and self.goal and pl.rect().colliderect(self.goal):
            self.state = "win"
        elif self.win_type == "survive" and self.time >= self.survive_ticks:
            self.state = "win"
        elif self.win_type == "defeat_all" and all(not e.alive for e in self.enemies):
            self.state = "win"

        if self.health <= 0:
            self.lives -= 1
            if self.lives <= 0:
                self.state = "lose"
            else:
                self._reset_player()

        # Particles
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def _spawn_particles(self, x, y, color, n=8):
        for _ in range(n):
            self.particles.append(Particle(x, y, color))

    def _reset_player(self):
        pl = self.player
        ground_y = self.H - 40
        pl.x, pl.y = 60.0, float(ground_y - pl.H - 2)
        pl.vx = pl.vy = 0.0
        self.health = 3
        self.invincible = 90

    def reset(self):
        for e in self.enemies:
            e.alive = True
            e.x = float(e.start_x)
            e.y = float(e.start_y)
            e.vx = abs(e.vx) if e.vx >= 0 else e.vx  # restore direction
        for c in self.collectibles:
            c.collected = False
        self.bullets.clear()
        self.particles.clear()
        self.score = 0
        self.health = 3
        self.lives = 3
        self.state = "playing"
        self.time = 0
        self.camera_x = 0
        self._reset_player()

    def draw(self, surf):
        ox = int(self.camera_x)

        # Sky gradient (manual)
        for y in range(self.H):
            t = y / self.H
            c = lerp_color(self.bg1, self.bg2, t)
            pygame.draw.line(surf, c, (0, y), (self.W, y))

        # Stars
        for i in range(40):
            sx = int((i * 173 + self.time * 0.02) % self.W)
            sy = int((i * 97) % (self.H * 0.6))
            surf.set_at((sx, sy), (200, 200, 200))

        # Platforms
        for p in self.platforms:
            px = p["x"] - ox
            if px + p["w"] < 0 or px > self.W:
                continue
            pc = self.plat_color
            dark = tuple(max(0, c - 30) for c in pc)
            pygame.draw.rect(surf, dark, (px, p["y"], p["w"], p["h"]))
            pygame.draw.rect(surf, pc, (px, p["y"], p["w"], 4))

        # Goal
        if self.goal:
            pygame.draw.rect(surf, C_YELLOW, (self.goal.x - ox, self.goal.y, self.goal.w, self.goal.h))
            flag_pts = [
                (self.goal.x - ox + self.goal.w, self.goal.y),
                (self.goal.x - ox + self.goal.w + 20, self.goal.y + 10),
                (self.goal.x - ox + self.goal.w, self.goal.y + 20),
            ]
            pygame.draw.polygon(surf, C_GREEN, flag_pts)

        # Collectibles
        for c in self.collectibles:
            c.draw(surf, ox, self.time)

        # Enemies
        for e in self.enemies:
            e.draw(surf, ox)

        # Bullets
        for b in self.bullets:
            b.draw(surf, ox)

        # Player (with hurt flash)
        hurt_flash = self.invincible > 0 and (self.time // 4) % 2 == 0
        self.player.draw(surf, ox, hurt_flash)

        # Particles
        for p in self.particles:
            p.draw(surf, ox)

        # HUD overlays on canvas
        if self.win_type == "survive":
            remaining = max(0, self.survive_ticks - self.time) // FPS
            txt = pygame.font.SysFont("segoeui", 20, bold=True).render(f"{remaining}s", True, C_ACCENT)
            surf.blit(txt, (self.W - 60, 15))
        if self.win_type == "collect":
            left = sum(1 for c in self.collectibles if not c.collected)
            txt = pygame.font.SysFont("segoeui", 14).render(f"Collect: {left} left", True, self.collect_color)
            surf.blit(txt, (10, 15))


# ── UI / APP ──────────────────────────────────────────────────────────────────

class TextInput:
    def __init__(self, rect, font, placeholder=""):
        self.rect = rect
        self.font = font
        self.placeholder = placeholder
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_TAB):
                self.text += event.unicode

    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer > 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, surf):
        border = C_ACCENT if self.active else C_BORDER
        draw_rounded_rect(surf, C_INPUT_BG, self.rect, 8, border)
        # Word-wrap
        lines = wrap_text(self.text or "", self.font, self.rect.w - 20)
        if not self.text:
            lines = wrap_text(self.placeholder, self.font, self.rect.w - 20)
            color = C_SUBTEXT
        else:
            color = C_TEXT
        for i, line in enumerate(lines[:6]):
            s = self.font.render(line, True, color)
            surf.blit(s, (self.rect.x + 10, self.rect.y + 10 + i * 18))
        # Cursor
        if self.active and self.cursor_visible:
            cx = self.rect.x + 10 + (self.font.size(lines[-1] if lines else "")[0] if self.text else 0)
            cy = self.rect.y + 10 + min(5, len(lines) - 1) * 18
            pygame.draw.line(surf, C_ACCENT, (cx, cy), (cx, cy + 16), 2)


class Button:
    def __init__(self, rect, label, color=C_ACCENT, text_color=C_BG, font=None):
        self.rect = rect
        self.label = label
        self.color = color
        self.text_color = text_color
        self.font = font
        self.hovered = False
        self.disabled = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and not self.disabled:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surf):
        f = self.font or pygame.font.SysFont("segoeui", 14, bold=True)
        if self.disabled:
            c = C_BORDER
            tc = C_SUBTEXT
        elif self.hovered:
            c = tuple(max(0, x - 30) for x in self.color)
            tc = self.text_color
        else:
            c = self.color
            tc = self.text_color
        draw_rounded_rect(surf, c, self.rect, 8)
        txt = f.render(self.label, True, tc)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("GameScript AI — Text to 2D Game")
        self.clock = pygame.time.Clock()

        # Fonts
        self.f_title  = pygame.font.SysFont("segoeui", 22, bold=True)
        self.f_label  = pygame.font.SysFont("segoeui", 11, bold=True)
        self.f_small  = pygame.font.SysFont("segoeui", 11)
        self.f_input  = pygame.font.SysFont("segoeui", 13)
        self.f_hud    = pygame.font.SysFont("segoeui", 20, bold=True)
        self.f_hud_sm = pygame.font.SysFont("segoeui", 10)
        self.f_overlay= pygame.font.SysFont("segoeui", 32, bold=True)
        self.f_ctrl   = pygame.font.SysFont("consolas", 11)

        # UI state
        self.text_input = TextInput(
            pygame.Rect(12, 90, PANEL_W - 24, 130),
            self.f_input,
            "Example: A blue hero jumps on platforms, collects golden coins, avoids red enemies."
        )
        self.gen_btn = Button(pygame.Rect(12, 234, PANEL_W - 24, 44), "▶  Generate Game")
        self.example_btns = [
            Button(pygame.Rect(12, 296 + i*28, PANEL_W - 24, 24),
                   ex[:52] + ("…" if len(ex) > 52 else ""),
                   C_INPUT_BG, (168, 196, 216), self.f_small)
            for i, ex in enumerate(EXAMPLES)
        ]

        # Game surface
        self.game_surf = pygame.Surface((GAME_W, GAME_H))
        self.game = None
        self.game_cfg = None

        # App state
        self.generating = False
        self.gen_error = ""
        self.nlp_log = "Claude NLP engine ready."
        self.parse_info = {}
        self.keys_held = {}

    def _start_generation(self):
        desc = self.text_input.text.strip()
        if not desc:
            self.gen_error = "Please enter a game description."
            return
        self.generating = True
        self.gen_btn.disabled = True
        self.gen_btn.label = "Analysing…"
        self.gen_error = ""
        self.nlp_log = "Sending to Claude API…"
        self.parse_info = {}

        def worker():
            cfg = parse_with_claude(desc)
            if cfg is None:
                cfg = self._fallback_parse(desc)
                self.nlp_log = "Claude unavailable — used local fallback parser."
            else:
                self.nlp_log = f"Claude parsed: {cfg.get('title', 'Game')} | win={cfg.get('winCondition')} | type={cfg.get('gameType')}"
            self.game_cfg = cfg
            self.parse_info = cfg
            self.game = PlatformerGame(cfg, GAME_W, GAME_H)
            self.gen_btn.disabled = False
            self.gen_btn.label = "▶  Regenerate"
            self.generating = False

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _fallback_parse(self, text: str) -> dict:
        """Simple keyword fallback if API is unavailable."""
        t = text.lower()
        hero_color = "#3B82F6"
        for col, hex_ in [("red","#EF4444"),("blue","#3B82F6"),("green","#10B981"),
                           ("yellow","#F59E0B"),("purple","#8B5CF6"),("cyan","#06B6D4"),
                           ("orange","#F97316"),("pink","#EC4899")]:
            if col in t:
                hero_color = hex_; break
        win = "collect"
        if any(w in t for w in ["survive","survival"]): win = "survive"
        elif any(w in t for w in ["flag","reach","goal","portal"]): win = "reach_goal"
        elif any(w in t for w in ["defeat","shoot all","kill all"]): win = "defeat_all"
        mechanics = ["jump"]
        if any(w in t for w in ["shoot","laser","fire","bullet"]): mechanics.append("shoot")
        return {
            "hero": {"name": "Hero", "color": hero_color},
            "enemies": [{"name": "Enemy", "color": "#EF4444", "speed": 1.2, "count": 4}],
            "collectibles": [{"name": "coin", "color": "#F59E0B", "count": 8}],
            "mechanics": mechanics,
            "winCondition": win,
            "surviveDuration": 30,
            "gameType": "platformer",
            "bgColor1": "#0A1628",
            "bgColor2": "#0D2040",
            "platformColor": "#2D5A2D",
            "platformCount": 6,
            "title": "Adventure"
        }

    def _draw_panel(self):
        surf = self.screen
        # Panel background
        pygame.draw.rect(surf, C_PANEL_BG, (0, 0, PANEL_W, SCREEN_H))
        pygame.draw.line(surf, C_BORDER, (PANEL_W, 0), (PANEL_W, SCREEN_H), 1)

        # Logo
        pygame.draw.line(surf, C_BORDER, (0, 56), (PANEL_W, 56), 1)
        t1 = self.f_title.render("Game", True, C_TEXT)
        t2 = self.f_title.render("Script", True, C_ACCENT)
        t3 = self.f_title.render(" AI", True, C_TEXT)
        surf.blit(t1, (14, 14))
        surf.blit(t2, (14 + t1.get_width(), 14))
        surf.blit(t3, (14 + t1.get_width() + t2.get_width(), 14))
        sub = self.f_small.render("Text Description → Playable 2D Game", True, C_SUBTEXT)
        surf.blit(sub, (14, 38))

        # Label
        lbl = self.f_label.render("DESCRIBE YOUR GAME", True, (168, 196, 216))
        surf.blit(lbl, (12, 72))

        # Text input
        self.text_input.update()
        self.text_input.draw(surf)

        # Generate button
        self.gen_btn.draw(surf)

        # Error
        if self.gen_error:
            err = self.f_small.render(self.gen_error, True, C_LOSE)
            surf.blit(err, (12, 282))

        # Examples label
        ex_lbl = self.f_small.render("Try an example:", True, C_SUBTEXT)
        surf.blit(ex_lbl, (12, 284))
        for btn in self.example_btns:
            btn.draw(surf)

        # Parse info
        if self.parse_info:
            py = 450
            pygame.draw.rect(surf, C_INPUT_BG, (12, py, PANEL_W - 24, 130), border_radius=8)
            pygame.draw.rect(surf, C_BORDER, (12, py, PANEL_W - 24, 130), 1, border_radius=8)
            hdr = self.f_label.render("NLP ANALYSIS", True, C_ACCENT)
            surf.blit(hdr, (20, py + 8))
            rows = [
                ("Hero",     self.parse_info.get("hero", {}).get("name", "?")),
                ("Type",     self.parse_info.get("gameType", "?")),
                ("Win",      self.parse_info.get("winCondition", "?")),
                ("Enemies",  ", ".join(e.get("name","?") for e in self.parse_info.get("enemies",[]))),
                ("Collect",  ", ".join(c.get("name","?") for c in self.parse_info.get("collectibles",[]))),
            ]
            for i, (k, v) in enumerate(rows):
                ky = self.f_small.render(k, True, C_SUBTEXT)
                vl = self.f_small.render(str(v)[:28], True, (168, 196, 216))
                surf.blit(ky, (20, py + 24 + i*20))
                surf.blit(vl, (PANEL_W - 24 - vl.get_width() - 8, py + 24 + i*20))

        # NLP log bar
        pygame.draw.rect(surf, (10, 20, 31), (0, SCREEN_H - 28, PANEL_W, 28))
        pygame.draw.line(surf, C_BORDER, (0, SCREEN_H - 28), (PANEL_W, SCREEN_H - 28), 1)
        log_txt = self.f_ctrl.render(self.nlp_log[:55], True, C_SUBTEXT)
        surf.blit(log_txt, (8, SCREEN_H - 20))

    def _draw_game_area(self):
        surf = self.screen
        gx = PANEL_W

        if self.game is None:
            # Start screen
            self.game_surf.fill(C_GAME_BG1)
            pygame.draw.rect(surf, C_GAME_BG1, (gx, 0, GAME_W, GAME_H))
            msg1 = self.f_overlay.render("🎮  Ready to Generate", True, C_TEXT)
            msg2 = self.f_input.render("Write a game description on the left and click Generate.", True, C_SUBTEXT)
            surf.blit(msg1, msg1.get_rect(center=(gx + GAME_W//2, GAME_H//2 - 30)))
            surf.blit(msg2, msg2.get_rect(center=(gx + GAME_W//2, GAME_H//2 + 20)))
            return

        # Draw game
        self.game_surf.fill((0, 0, 0))
        self.game.draw(self.game_surf)
        surf.blit(self.game_surf, (gx, 0))

        # HUD bar
        hud_h = 44
        pygame.draw.rect(surf, C_BG, (gx, 0, GAME_W, hud_h))
        pygame.draw.line(surf, C_BORDER, (gx, hud_h), (gx + GAME_W, hud_h), 1)
        title_txt = self.f_input.render(self.game_cfg.get("title", "Adventure"), True, C_TEXT)
        surf.blit(title_txt, (gx + 10, 14))

        for i, (val, lbl, col) in enumerate([
            (self.game.score, "SCORE", C_ACCENT),
            (self.game.health, "HEALTH", C_GREEN),
            (self.game.lives, "LIVES", C_LOSE),
        ]):
            rx = gx + GAME_W - 200 + i * 68
            v = self.f_hud.render(str(val), True, col)
            l = self.f_hud_sm.render(lbl, True, C_SUBTEXT)
            surf.blit(v, v.get_rect(centerx=rx + 24, centery=16))
            surf.blit(l, l.get_rect(centerx=rx + 24, centery=34))

        # Overlay for win/lose (draw over game)
        if self.game.state == "win":
            s = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
            s.fill((5, 13, 21, 210))
            surf.blit(s, (gx, 0))
            t1 = self.f_overlay.render("🏆  You Win!", True, C_WIN)
            t2 = self.f_input.render(f"Score: {self.game.score}  — Press R to play again", True, (168,196,216))
            surf.blit(t1, t1.get_rect(center=(gx + GAME_W//2, GAME_H//2 - 20)))
            surf.blit(t2, t2.get_rect(center=(gx + GAME_W//2, GAME_H//2 + 30)))
        elif self.game.state == "lose":
            s = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
            s.fill((5, 13, 21, 210))
            surf.blit(s, (gx, 0))
            t1 = self.f_overlay.render("💀  Game Over", True, C_LOSE)
            t2 = self.f_input.render(f"Score: {self.game.score}  — Press R to try again", True, (168,196,216))
            surf.blit(t1, t1.get_rect(center=(gx + GAME_W//2, GAME_H//2 - 20)))
            surf.blit(t2, t2.get_rect(center=(gx + GAME_W//2, GAME_H//2 + 30)))
        elif self.generating:
            s = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
            s.fill((5, 13, 21, 170))
            surf.blit(s, (gx, 0))
            dots = "." * (1 + (pygame.time.get_ticks() // 400) % 3)
            t = self.f_overlay.render(f"Generating{dots}", True, C_ACCENT)
            surf.blit(t, t.get_rect(center=(gx + GAME_W//2, GAME_H//2)))

        # Controls bar
        ctrl_y = GAME_H - 28
        pygame.draw.rect(surf, C_BG, (gx, ctrl_y, GAME_W, 28))
        pygame.draw.line(surf, C_BORDER, (gx, ctrl_y), (gx + GAME_W, ctrl_y), 1)
        controls = [("← →", "Move"), ("↑/Space", "Jump"), ("Z", "Shoot"), ("R", "Restart")]
        cx = gx + 10
        for key, desc in controls:
            k = self.f_ctrl.render(key, True, (168, 196, 216))
            pygame.draw.rect(surf, C_INPUT_BG, (cx-2, ctrl_y+5, k.get_width()+8, 18), border_radius=3)
            surf.blit(k, (cx+2, ctrl_y + 7))
            cx += k.get_width() + 14
            d = self.f_small.render(desc, True, C_SUBTEXT)
            surf.blit(d, (cx - 4, ctrl_y + 8))
            cx += d.get_width() + 20

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    break

                self.text_input.handle_event(event)

                if self.gen_btn.handle_event(event):
                    self._start_generation()

                for i, btn in enumerate(self.example_btns):
                    if btn.handle_event(event):
                        self.text_input.text = EXAMPLES[i]

                if event.type == pygame.KEYDOWN:
                    self.keys_held[event.key] = True
                    if event.key == pygame.K_r and self.game:
                        self.game.reset()
                if event.type == pygame.KEYUP:
                    self.keys_held[event.key] = False

            # Update game
            if self.game and self.game.state == "playing":
                self.game.update(self.keys_held)

            # Draw
            self.screen.fill(C_BG)
            self._draw_panel()
            self._draw_game_area()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠  ANTHROPIC_API_KEY not set — will use local fallback parser.")
        print("   Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
    App().run()

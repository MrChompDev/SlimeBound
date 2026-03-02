"""
Strange Places: Slimebound  —  Day 1 + Day 2  (v3)
Fixes: reliable platform physics, pixel font, full-screen background, 5 levels
"""

import pygame, math, os

# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
SW, SH      = 1920, 1080
FPS         = 60
TITLE       = "Strange Places: Slimebound"
GRAVITY     = 0.65
JUMP_FORCE  = -16
MOVE_SPEED  = 5
GROUND_Y    = SH - 100

PISTOL_SPD  = 20 ; PISTOL_CD  = 18
HUSH_SPD    = 10 ; HUSH_CD    = 42

# Palette
C_BG          = ( 22,  14,  40)
C_GROUND      = ( 48,  34,  68)
C_PLAT        = ( 65,  50,  90)
C_PLAT_TOP    = (110,  85, 150)
C_BTN_S_OFF   = ( 50, 170,  70)   # small / pistol
C_BTN_S_ON    = (120, 255, 130)
C_BTN_L_OFF   = (190,  80,  20)   # large / hush
C_BTN_L_ON    = (255, 200,  50)
C_WHITE       = (255, 255, 255)
C_DOOR        = ( 75,  55, 115)
C_DOOR_EDGE   = (150, 120, 200)
C_CRACK       = (110,  75,  45)
C_MP          = ( 80, 120, 175)
C_MP_EDGE     = (150, 195, 255)
C_PORTAL      = ( 60, 220, 255)
C_PORTAL_DARK = ( 20,  80, 120)

ASSET_DIR = os.path.join(os.path.dirname(__file__), "Assets")
PATHS = {
    "slime"       : os.path.join(ASSET_DIR, "Character", "Slime.png"),
    "pistol"      : os.path.join(ASSET_DIR, "Guns",      "Pistol.png"),
    "hush"        : os.path.join(ASSET_DIR, "Guns",      "Hush_Puppy.png"),
    "bullet"      : os.path.join(ASSET_DIR, "Guns",      "Bullet.png"),
    "bg"          : os.path.join(ASSET_DIR, "Tiles",     "Background.png"),
    "tile"        : os.path.join(ASSET_DIR, "Tiles",     "Tile_01.png"),
    "btn_pistol"  : os.path.join(ASSET_DIR, "Tiles",     "Button_Pistol.png"),
    "btn_hush"    : os.path.join(ASSET_DIR, "Tiles",     "Button_Hush.png"),
    "door"        : os.path.join(ASSET_DIR, "Tiles",     "Door.png"),
    # Menu
    "menu_bg"     : os.path.join(ASSET_DIR, "Menu",      "MenuBG.png"),
    "btn_play"    : os.path.join(ASSET_DIR, "Menu",      "Play_Button.png"),
    "btn_settings": os.path.join(ASSET_DIR, "Menu",      "Settings_Button.png"),
    "btn_exit"    : os.path.join(ASSET_DIR, "Menu",      "Exit_Button.png"),
    # Settings
    "settings_bg" : os.path.join(ASSET_DIR, "Settings",   "SettingsBG.png"),
    "music_on"    : os.path.join(ASSET_DIR, "Settings",   "Music_Button_On.png"),
    "music_off"   : os.path.join(ASSET_DIR, "Settings",   "Music_Button_Off.png"),
    "sfx_on"      : os.path.join(ASSET_DIR, "Settings",   "SFX_Button_On.png"),
    "sfx_off"     : os.path.join(ASSET_DIR, "Settings",   "SFX_Button_Off.png"),
    # Music
    "ost_main"    : os.path.join(ASSET_DIR, "SFX\\Music", "MainOST.mp3"),
    "ost_settings": os.path.join(ASSET_DIR, "SFX\\Music", "SettingsOST.mp3"),
}

# Global image store — populated in main() before any level is built
IMGS: dict = {}


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def load_img(path, size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if size: img = pygame.transform.smoothscale(img, size)
        return img, True
    except Exception:
        w, h = size or (48, 48)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((180, 60, 180, 160))
        return s, False

def pf(size):
    """Pixel font — pygame's built-in bitmap font."""
    return pygame.font.Font(None, size)

def draw_9slice(surf, rect, col, edge_col, radius=5):
    pygame.draw.rect(surf, col,      rect, border_radius=radius)
    pygame.draw.rect(surf, edge_col, rect, 2, border_radius=radius)


_current_track = None   # track which file is already loaded

def play_music(path, loops=-1, volume=0.7):
    """Load and play a music track — no-op if it's already playing."""
    global _current_track
    if _current_track == path:
        return   # already playing, don't restart
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops)
        _current_track = path
    except Exception as e:
        print(f"[Music] Could not load {path}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  BULLET
# ═══════════════════════════════════════════════════════════════════════════════
class Bullet(pygame.sprite.Sprite):
    SZ = {"pistol": (13, 13), "hush": (23, 23)}

    def __init__(self, x, y, angle, img, kind):
        super().__init__()
        self.kind = kind
        spd       = PISTOL_SPD if kind == "pistol" else HUSH_SPD
        sz        = self.SZ[kind]
        self.image = pygame.transform.smoothscale(img, sz).copy()
        if kind == "hush":
            t = pygame.Surface(sz, pygame.SRCALPHA); t.fill((255,110,0,150))
            self.image.blit(t, (0,0))
        self.rect         = self.image.get_rect(center=(x, y))
        self.pos          = pygame.math.Vector2(x, y)
        self.vel          = pygame.math.Vector2(math.cos(angle)*spd, math.sin(angle)*spd)
        self.bounces_left = 1 if kind == "pistol" else 0

    def update(self):
        self.pos += self.vel
        self.rect.center = round(self.pos.x), round(self.pos.y)
        if self.bounces_left and (self.pos.x <= 0 or self.pos.x >= SW):
            self.vel.x *= -1; self.bounces_left -= 1
        if not (-80 < self.pos.x < SW+80 and -80 < self.pos.y < SH+80):
            self.kill()


# ═══════════════════════════════════════════════════════════════════════════════
#  BUTTONS
# ═══════════════════════════════════════════════════════════════════════════════
class Button:
    ACCEPTS = None
    def __init__(self, x, y, w, h, label=""):
        self.rect   = pygame.Rect(x, y, w, h)
        self.active = False
        self._flash = 0
        self.label  = label
        self.linked = []

    def link(self, *objs): self.linked.extend(objs); return self

    def try_hit(self, b):
        if b.kind != self.ACCEPTS: return False
        if not self.rect.colliderect(b.rect): return False
        if not self.active:
            self.active = True; self._flash = 22
            for o in self.linked: o.trigger()
        b.kill(); return True

    def update(self):
        if self._flash > 0: self._flash -= 1

    def draw(self, surf, font): pass


class SmallButton(Button):
    """Pistol only — tiny precise target. Hush bounces off."""
    ACCEPTS = "pistol"
    R = 20
    def __init__(self, cx, cy, label=""):
        super().__init__(cx-self.R, cy-self.R, self.R*2, self.R*2, label)
        self.cx, self.cy = cx, cy

    def try_hit(self, b):
        if b.kind == "hush" and b.rect.colliderect(self.rect):
            b.vel *= -0.5; b.kill(); return False
        return super().try_hit(b)

    def draw(self, surf, font):
        cx, cy = self.cx, self.cy
        r      = self.R + (5 if self._flash else 0)
        # Use sprite if available, else draw circle fallback
        img = IMGS.get("btn_pistol")
        if img:
            size = r * 2
            scaled = pygame.transform.smoothscale(img, (size, size))
            if self.active:
                bright = scaled.copy()
                bright.fill((80, 255, 80, 60), special_flags=pygame.BLEND_RGBA_ADD)
                scaled = bright
            surf.blit(scaled, scaled.get_rect(center=(cx, cy)))
        else:
            col = C_BTN_S_ON if self.active else C_BTN_S_OFF
            pygame.draw.circle(surf, col,     (cx, cy), r)
            pygame.draw.circle(surf, C_WHITE, (cx, cy), r, 2)
            pygame.draw.circle(surf, C_WHITE, (cx, cy), 5)
        t = font.render(self.label or "PISTOL", True, (180, 255, 180))
        surf.blit(t, t.get_rect(centerx=cx, bottom=cy - r - 4))


class LargeButton(Button):
    """Hush only — heavy switch. Pistol shatters."""
    ACCEPTS = "hush"
    def __init__(self, x, y, w=72, h=48, label=""):
        super().__init__(x, y, w, h, label)

    def try_hit(self, b):
        if b.kind == "pistol" and b.rect.colliderect(self.rect):
            b.kill(); return False
        return super().try_hit(b)

    def draw(self, surf, font):
        r   = self.rect.inflate(10, 8) if self._flash else self.rect
        img = IMGS.get("btn_hush")
        if img:
            scaled = pygame.transform.smoothscale(img, (r.w, r.h))
            if self.active:
                bright = scaled.copy()
                bright.fill((255, 200, 0, 60), special_flags=pygame.BLEND_RGBA_ADD)
                scaled = bright
            surf.blit(scaled, r.topleft)
        else:
            col = C_BTN_L_ON if self.active else C_BTN_L_OFF
            pygame.draw.rect(surf, col,     r, border_radius=6)
            pygame.draw.rect(surf, C_WHITE, r, 3, border_radius=6)
            inn = r.inflate(-14, -10)
            pygame.draw.rect(surf, tuple(min(c+28,255) for c in col), inn, border_radius=4)
        t = font.render(self.label or "HUSH", True, (255, 225, 170))
        surf.blit(t, t.get_rect(centerx=r.centerx, bottom=r.top - 4))


# ═══════════════════════════════════════════════════════════════════════════════
#  WORLD OBJECTS
# ═══════════════════════════════════════════════════════════════════════════════
class Door:
    """
    Solid wall from screen top down to ground — player can NEVER jump over it.
    The collision shrinks upward as the door opens (slides into the ceiling).
    Door.png is tiled vertically to fill the visible panel.
    """
    SPEED = 8

    def __init__(self, x, y, w, h):
        # x, w  = horizontal position/size
        # y, h  = where the VISIBLE door panel sits (used for initial layout only)
        # Collision ALWAYS covers from y=0 to ground — player can't jump over
        self.x         = x
        self.w         = w
        self._open     = False
        self._slide    = 0          # how many px the door has slid UP into ceiling
        self._full_h   = GROUND_Y   # full collision height = ceiling → ground

    @property
    def rect(self):
        """Solid collision rect — ceiling down to current door bottom."""
        remaining = max(0, self._full_h - self._slide)
        return pygame.Rect(self.x, 0, self.w, remaining)

    def trigger(self): self._open = True

    def update(self):
        if self._open and self._slide < self._full_h:
            self._slide = min(self._slide + self.SPEED, self._full_h)

    def draw(self, surf, font):
        remaining = self._full_h - self._slide
        if remaining <= 0:
            return

        door_img = IMGS.get("door")
        if door_img:
            # Tile at NATIVE size — no scaling, just like platform tiles
            tile_w, tile_h = door_img.get_size()
            # Tile from top-left, covering the door width and visible height
            y = 0
            while y < remaining:
                x = self.x
                while x < self.x + self.w:
                    clip_w = min(tile_w, self.x + self.w - x)
                    clip_h = min(tile_h, remaining - y)
                    surf.blit(door_img, (x, y),
                              area=pygame.Rect(0, 0, clip_w, clip_h))
                    x += tile_w
                y += tile_h
        else:
            draw_rect = pygame.Rect(self.x, 0, self.w, remaining)
            pygame.draw.rect(surf, C_DOOR,      draw_rect, border_radius=4)
            pygame.draw.rect(surf, C_DOOR_EDGE, draw_rect, 3, border_radius=4)


class MovingPlatform:
    def __init__(self, x, y, w, h, ex, ey, speed=2):
        self.rect    = pygame.Rect(x, y, w, h)
        self.start   = pygame.math.Vector2(x, y)
        self.end     = pygame.math.Vector2(ex, ey)
        self.pos     = pygame.math.Vector2(x, y)
        self._moving = False; self._at_end = False
        self.speed   = speed
    def trigger(self): self._moving = True
    def update(self):
        if not self._moving: return
        target = self.end if not self._at_end else self.start
        d = target - self.pos
        if d.length() <= self.speed:
            self.pos = target.copy(); self._moving = False; self._at_end = not self._at_end
        else:
            self.pos += d.normalize() * self.speed
        self.rect.topleft = round(self.pos.x), round(self.pos.y)
    def draw(self, surf):
        pygame.draw.rect(surf, C_MP,      self.rect, border_radius=5)
        pygame.draw.rect(surf, C_MP_EDGE, self.rect, 2, border_radius=5)
        mx, my = self.rect.centerx, self.rect.centery
        pygame.draw.polygon(surf, C_MP_EDGE, [(mx-10,my+4),(mx,my-5),(mx+10,my+4)])


class CrackedBlock:
    def __init__(self, x, y, w=64, h=64):
        self.rect  = pygame.Rect(x, y, w, h)
        self.alive = True; self._shake = 0
    def try_hit(self, b):
        if not self.alive or not b.rect.colliderect(self.rect): return False
        if b.kind == "hush":   self.alive = False; b.kill(); return True
        b.vel.x *= -1; self._shake = 8; return False
    def update(self):
        if self._shake > 0: self._shake -= 1
    def draw(self, surf, font):
        if not self.alive: return
        sh = (2 if self._shake%2==0 else -2) if self._shake else 0
        r  = self.rect.move(sh, 0)
        pygame.draw.rect(surf, C_CRACK,        r, border_radius=3)
        pygame.draw.rect(surf, (55,35,20),     r, 2,  border_radius=3)
        cx, cy = r.centerx, r.centery
        pygame.draw.lines(surf,(40,25,12),False,
                          [(cx,r.top),(cx-9,cy-6),(cx+5,cy),(cx-7,r.bottom)],2)
        pygame.draw.line(surf,(40,25,12),(r.left+12,cy-12),(r.right-12,cy+12),2)
        t = font.render("HUSH", True, (195,155,95))
        surf.blit(t, t.get_rect(center=(cx,cy)))


class Portal:
    """Exit portal — glows when all buttons in the level are active."""
    def __init__(self, cx, cy, r=36):
        self.cx = cx; self.cy = cy; self.r = r
        self._pulse = 0.0
    def is_open(self, buttons):
        return all(b.active for b in buttons) if buttons else True
    def touches(self, slime_rect):
        dx = slime_rect.centerx - self.cx
        dy = slime_rect.centery - self.cy
        return math.hypot(dx, dy) < self.r + 10
    def update(self): self._pulse = (self._pulse + 0.07) % (2*math.pi)
    def draw(self, surf, buttons, font):
        opened = self.is_open(buttons)
        glow_r = self.r + int(6 * math.sin(self._pulse))
        col    = C_PORTAL if opened else (80, 80, 100)
        dark   = C_PORTAL_DARK if opened else (30, 30, 50)
        for i in range(4, 0, -1):
            alpha_surf = pygame.Surface((glow_r*2+20, glow_r*2+20), pygame.SRCALPHA)
            ar = glow_r + i*5
            pygame.draw.circle(alpha_surf, (*col, 25), (ar+10, ar+10), ar)
            surf.blit(alpha_surf, (self.cx-ar-10, self.cy-ar-10))
        pygame.draw.circle(surf, dark, (self.cx, self.cy), glow_r)
        pygame.draw.circle(surf, col,  (self.cx, self.cy), glow_r, 3)
        inner = int(glow_r * 0.55)
        pygame.draw.circle(surf, col, (self.cx, self.cy), inner)
        label = "EXIT" if opened else "LOCKED"
        t = font.render(label, True, col)
        surf.blit(t, t.get_rect(centerx=self.cx, top=self.cy + glow_r + 6))


# ═══════════════════════════════════════════════════════════════════════════════
#  SLIME  — reliable physics using prev-position tracking
# ═══════════════════════════════════════════════════════════════════════════════
class Slime:
    BW, BH = 62, 62

    def __init__(self, x, y, images):
        self.images       = images
        self.pos          = pygame.math.Vector2(x, y)
        self.vel          = pygame.math.Vector2(0, 0)
        self.on_ground    = False
        self._was_falling = False
        self._sq_timer    = 0
        self._sq_dur      = 10
        self.gun          = "pistol"
        self._cd          = 0
        self.rect         = pygame.Rect(0, 0, self.BW, self.BH)
        self.rect.center  = round(x), round(y)

    def reset(self, x, y):
        self.pos.update(x, y); self.vel.update(0, 0)
        self.on_ground = False; self._was_falling = False

    # ── squash/stretch ────────────────────────────────────
    def _squash(self):  self._sq_timer =  self._sq_dur
    def _stretch(self): self._sq_timer = -self._sq_dur

    def _scale(self):
        if self._sq_timer > 0:
            t = self._sq_timer / self._sq_dur
            return 1+.30*t, 1-.28*t
        if self._sq_timer < 0:
            t = -self._sq_timer / self._sq_dur
            return 1-.18*t, 1+.35*t
        return 1.0, 1.0

    # ── input ─────────────────────────────────────────────
    def handle_input(self, keys):
        self.vel.x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.vel.x = -MOVE_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.vel.x =  MOVE_SPEED
        if (keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vel.y = JUMP_FORCE; self.on_ground = False; self._stretch()
        if keys[pygame.K_1]: self.gun = "pistol"
        if keys[pygame.K_2]: self.gun = "hush"

    # ── physics  (prev-pos tracking for reliable landing) ─
    def apply_gravity(self, solids):
        self.vel.y += GRAVITY

        # ── horizontal pass ───────────────────────────────
        prev_x = self.rect.x
        self.pos.x += self.vel.x
        self.rect.centerx = round(self.pos.x)
        for s in solids:
            if self.rect.colliderect(s):
                if self.vel.x > 0:
                    self.rect.right  = s.left; self.vel.x = 0
                elif self.vel.x < 0:
                    self.rect.left   = s.right; self.vel.x = 0
                self.pos.x = self.rect.centerx

        # ── vertical pass ─────────────────────────────────
        old_bottom = self.rect.bottom
        old_top    = self.rect.top
        self.pos.y += self.vel.y
        self.rect.centery = round(self.pos.y)

        self.on_ground = False
        for s in solids:
            if not self.rect.colliderect(s):
                continue
            if self.vel.y > 0 and old_bottom <= s.top + 4:
                # land on top
                self.rect.bottom = s.top
                self.vel.y       = 0
                self.on_ground   = True
                if self._was_falling: self._squash()
                self._was_falling = False
            elif self.vel.y < 0 and old_top >= s.bottom - 4:
                # hit ceiling
                self.rect.top = s.bottom
                self.vel.y    = 0
            self.pos.y = self.rect.centery

        if not self.on_ground and self.vel.y > 2:
            self._was_falling = True

        # clamp to ground strip
        if self.rect.bottom > GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.pos.y       = self.rect.centery
            self.vel.y       = 0
            self.on_ground   = True
            if self._was_falling: self._squash()
            self._was_falling = False

        self.rect.center = round(self.pos.x), round(self.pos.y)

    # ── shoot ─────────────────────────────────────────────
    def shoot(self, mpos, grp, img):
        if self._cd > 0: return False
        self._cd = PISTOL_CD if self.gun == "pistol" else HUSH_CD
        dx = mpos[0]-self.rect.centerx; dy = mpos[1]-self.rect.centery
        grp.add(Bullet(self.rect.centerx, self.rect.centery,
                       math.atan2(dy,dx), img, self.gun))
        return True

    def tick(self):
        if self._cd > 0: self._cd -= 1
        if self._sq_timer > 0: self._sq_timer -= 1
        elif self._sq_timer < 0: self._sq_timer += 1

    # ── draw ──────────────────────────────────────────────
    def draw(self, surf, mpos):
        sx, sy = self._scale()
        w = max(4, round(self.BW*sx)); h = max(4, round(self.BH*sy))
        scaled = pygame.transform.smoothscale(self.images["slime"], (w,h))
        surf.blit(scaled, scaled.get_rect(center=self.rect.center))

        gi   = self.images["pistol" if self.gun=="pistol" else "hush"]
        dx   = mpos[0]-self.rect.centerx; dy = mpos[1]-self.rect.centery
        ang  = math.degrees(math.atan2(dy,dx))
        gs   = gi if -90<ang<90 else pygame.transform.flip(gi,False,True)
        rg   = pygame.transform.rotate(gs, -ang)
        dist = 30
        surf.blit(rg, rg.get_rect(center=(
            self.rect.centerx + math.cos(math.radians(ang))*dist,
            self.rect.centery + math.sin(math.radians(ang))*dist)))


# ═══════════════════════════════════════════════════════════════════════════════
#  LEVEL DEFINITIONS
#  Each function returns (title, subtitle, static_rects, moving_platforms,
#                         doors, buttons, cracked_blocks, portal, spawn_xy)
# ═══════════════════════════════════════════════════════════════════════════════
GY = GROUND_Y

def level_1():
    """The Threshold — learn movement and shooting a button."""
    plats = [
        pygame.Rect(350, GY-180, 200, 20),
        pygame.Rect(700, GY-260, 200, 20),
        pygame.Rect(1050,GY-180, 200, 20),
    ]
    door  = Door(920, GY-280, 55, 280)
    btn   = SmallButton(500, GY-205, "PISTOL")
    btn.link(door)
    portal = Portal(1250, GY-50)
    return ("LEVEL 1", "THE THRESHOLD",
            plats, [], [door], [btn], [], portal, (120, GY-80), None, 15,
            "Initialization complete.")


def level_2():
    """Backwards Forest I — hush lifts you over a wall."""
    plats = [
        pygame.Rect(200, GY-150, 250, 20),
        pygame.Rect(560, GY-280, 180, 20),
        pygame.Rect(820, GY-200, 250, 20),
        pygame.Rect(1150,GY-320, 200, 20),
        pygame.Rect(1450,GY-200, 200, 20),
    ]
    door_a = Door(510, GY-300, 55, 300)
    door_b = Door(1110,GY-340, 55, 340)

    mp_a = MovingPlatform(390, GY-60, 130, 20, 390, GY-260)

    btn_p  = SmallButton(300, GY-175, "PISTOL")
    btn_h  = LargeButton(600, GY-330, label="HUSH")
    btn_p2 = SmallButton(920, GY-225, "PISTOL")

    btn_p.link(door_a)
    btn_h.link(mp_a)
    btn_p2.link(door_b)

    portal = Portal(1580, GY-50)
    return ("LEVEL 2", "BACKWARDS FOREST I",
            plats, [mp_a], [door_a, door_b], [btn_p, btn_h, btn_p2], [], portal,
            (120, GY-80), None, 20,
            "Specimen 13 responding.")


def level_3():
    """Backwards Forest II — sequence: shoot in correct order."""
    plats = [
        pygame.Rect(250, GY-150, 220, 20),
        pygame.Rect(550, GY-260, 180, 20),
        pygame.Rect(820, GY-360, 180, 20),
        pygame.Rect(1080,GY-260, 220, 20),
        pygame.Rect(1380,GY-180, 220, 20),
    ]

    # Three doors, each opened by a button in sequence
    door_a = Door(490,  GY-280, 55, 280)
    door_b = Door(770,  GY-380, 55, 380)
    door_c = Door(1040, GY-280, 55, 280)

    btn1 = SmallButton(380, GY-175, "1ST")
    btn2 = SmallButton(680, GY-285, "2ND")
    btn3 = SmallButton(960, GY-385, "3RD")

    # Each button only opens next door if previous is active
    # Simplified: chain each door with its button directly
    btn1.link(door_a)
    btn2.link(door_b)
    btn3.link(door_c)

    portal = Portal(1560, GY-50)

    # Riddle text stored in level meta
    riddle = '"Forward I fall, backward I rise."'
    return ("LEVEL 3", "BACKWARDS FOREST II",
            plats, [], [door_a, door_b, door_c], [btn1, btn2, btn3], [], portal,
            (120, GY-80), riddle, 18,
            "Containment breach logged.")


def level_4():
    """Glass Desert I — light crystal sequence (three pistol buttons in order)."""
    plats = [
        pygame.Rect(200, GY-120, 250, 20),
        pygame.Rect(500, GY-220, 200, 20),
        pygame.Rect(760, GY-340, 200, 20),
        pygame.Rect(1030,GY-220, 220, 20),
        pygame.Rect(1340,GY-340, 200, 20),
        pygame.Rect(1620,GY-220, 200, 20),
    ]

    door_1 = Door(460,  GY-240, 40, 240)
    door_2 = Door(720,  GY-360, 40, 360)
    door_3 = Door(990,  GY-240, 40, 240)
    door_4 = Door(1300, GY-360, 40, 360)

    # Crystal buttons — precision shots needed
    c1 = SmallButton(310,  GY-145, "CRYSTAL")
    c2 = SmallButton(610,  GY-245, "CRYSTAL")
    c3 = SmallButton(870,  GY-365, "CRYSTAL")
    c4 = SmallButton(1140, GY-245, "CRYSTAL")

    c1.link(door_1); c2.link(door_2); c3.link(door_3); c4.link(door_4)

    # Heavy gate needs hush
    gate = Door(1580, GY-440, 55, 440)
    hbtn = LargeButton(1440, GY-370, label="HUSH GATE")
    hbtn.link(gate)

    portal = Portal(1820, GY-50)
    return ("LEVEL 4", "GLASS DESERT I",
            plats, [], [door_1, door_2, door_3, door_4, gate],
            [c1, c2, c3, c4, hbtn], [], portal, (120, GY-80), None, 20,
            "Structural decay at 72%.")


def level_5():
    """Glass Desert II — dual guns, cracked walls, lifts, combo finale."""
    plats = [
        pygame.Rect(200, GY-150, 220, 20),
        pygame.Rect(520, GY-260, 180, 20),
        pygame.Rect(800, GY-380, 180, 20),
        pygame.Rect(1060,GY-260, 220, 20),
        pygame.Rect(1380,GY-380, 200, 20),
        pygame.Rect(1660,GY-260, 220, 20),
    ]

    # Cracked wall blocking progress
    crack_wall = [
        CrackedBlock(770, GY-64,  64, 64),
        CrackedBlock(770, GY-128, 64, 64),
        CrackedBlock(770, GY-192, 64, 64),
        CrackedBlock(770, GY-256, 64, 64),
        CrackedBlock(770, GY-320, 64, 64),
        CrackedBlock(770, GY-384, 64, 64),
    ]

    door_a = Door(480,  GY-280, 50, 280)
    door_b = Door(1020, GY-280, 50, 280)
    door_c = Door(1640, GY-480, 50, 480)

    mp_a = MovingPlatform(650, GY-60, 140, 20, 650, GY-370, speed=3)
    mp_b = MovingPlatform(1200,GY-60, 140, 20, 1400,GY-60,  speed=3)

    btn_p1 = SmallButton(320,  GY-175, "PISTOL")
    btn_h1 = LargeButton(555,  GY-310, label="HUSH")
    btn_p2 = SmallButton(900,  GY-405, "PISTOL")
    btn_h2 = LargeButton(1100, GY-310, label="HUSH")
    btn_p3 = SmallButton(1490, GY-405, "PISTOL")
    btn_h3 = LargeButton(1700, GY-310, label="HUSH GATE")

    btn_p1.link(door_a)
    btn_h1.link(mp_a)
    btn_p2.link(door_b)
    btn_h2.link(mp_b)
    btn_p3.link(door_c)
    btn_h3.link(door_c)

    portal = Portal(1840, GY-50)
    return ("LEVEL 5", "GLASS DESERT II",
            plats, [mp_a, mp_b], [door_a, door_b, door_c],
            [btn_p1, btn_h1, btn_p2, btn_h2, btn_p3, btn_h3],
            crack_wall, portal, (120, GY-80), None, 25,
            "External stone growth detected.")


LEVELS = [level_1, level_2, level_3, level_4, level_5]


# ═══════════════════════════════════════════════════════════════════════════════
#  LEVEL LOADER
# ═══════════════════════════════════════════════════════════════════════════════
def load_level(idx):
    data = LEVELS[idx]()
    # All levels return 12 fields: title, sub, plats, mps, doors, btns,
    #                              cracks, portal, spawn, riddle, ammo, lore
    title, sub, plats, mps, doors, btns, cracks, portal, spawn, riddle, ammo, lore = data
    return {
        "title": title, "sub": sub,
        "plats": plats, "mps": mps, "doors": doors,
        "btns": btns, "cracks": cracks,
        "portal": portal, "spawn": spawn,
        "riddle": riddle,
        "ammo": ammo,
        "lore": lore,
    }


def get_solids(lv):
    s = list(lv["plats"])
    for mp in lv["mps"]:  s.append(mp.rect)
    for d  in lv["doors"]:
        if d.rect.h > 4: s.append(d.rect)
    return s


# ═══════════════════════════════════════════════════════════════════════════════
#  HUD  — right-side panel, all positions computed top→bottom, no overlap
# ═══════════════════════════════════════════════════════════════════════════════
def draw_hud(surf, slime, lv_idx, ammo, ammo_max, font_b, font_s):
    SLOT    = 90
    PAD     = 10
    PANEL_W = SLOT + 40
    PANEL_X = SW - PANEL_W - 10
    INNER_X = PANEL_X + 10          # left edge of content inside panel
    CX      = PANEL_X + PANEL_W//2  # centre x of panel

    # ── Level label (top centre, outside panel) ───────────
    lvtxt = font_b.render(f"LEVEL {lv_idx+1}/{len(LEVELS)}", True, (200, 200, 255))
    surf.blit(lvtxt, lvtxt.get_rect(centerx=SW//2, top=14))

    # ── Compute all content heights first ────────────────
    # We'll measure and position each block, then draw the panel behind them.

    font_big_ammo = pygame.font.Font(None, 68)

    pip_total  = min(ammo_max, 20)
    pip_r      = 5
    pip_gap    = 4
    pip_cols   = 5
    pip_rows   = math.ceil(pip_total / pip_cols)
    pip_block_h = pip_rows * (pip_r*2 + pip_gap)

    hint_lines = [("WASD", "Move+Jump"), ("LMB", "Shoot"),
                  ("1/2",  "Switch"),    ("R",   "Restart")]

    # Heights of each section (with gaps)
    GAP       = 8
    SLOT_ROWS = 2
    h_slots   = SLOT_ROWS * SLOT + (SLOT_ROWS - 1) * (font_s.get_height() + 6) + GAP*2
    h_ammo_lbl = font_b.get_height()
    h_ammo_num = font_big_ammo.size("00")[1]
    h_pips     = pip_block_h + GAP
    h_divider  = 2 + GAP
    h_hints    = len(hint_lines) * (font_s.get_height() + 3)
    PANEL_PAD  = 12

    panel_h = PANEL_PAD + h_slots + GAP + h_ammo_lbl + GAP + h_ammo_num + GAP + h_pips + h_divider + h_hints + PANEL_PAD
    START_Y = 56

    # ── Draw panel background ─────────────────────────────
    panel = pygame.Surface((PANEL_W, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 160),       (0, 0, PANEL_W, panel_h), border_radius=12)
    pygame.draw.rect(panel, (80, 60, 110, 200),   (0, 0, PANEL_W, panel_h), 2, border_radius=12)
    surf.blit(panel, (PANEL_X, START_Y))

    # ── Gun slots ─────────────────────────────────────────
    guns = [
        ("pistol", "1", "PISTOL",     IMGS.get("pistol"), C_BTN_S_ON),
        ("hush",   "2", "HUSH PUPPY", IMGS.get("hush"),   C_BTN_L_ON),
    ]
    cursor_y = START_Y + PANEL_PAD

    for (key, hotkey, name, gun_img, active_col) in guns:
        sx     = INNER_X + 10
        active = slime.gun == key

        # Slot box
        slot_surf = pygame.Surface((SLOT, SLOT), pygame.SRCALPHA)
        if active:
            pygame.draw.rect(slot_surf, (*active_col, 55),  (0,0,SLOT,SLOT), border_radius=8)
            pygame.draw.rect(slot_surf, (*active_col, 230), (0,0,SLOT,SLOT), 3, border_radius=8)
        else:
            pygame.draw.rect(slot_surf, (35, 26, 50, 200),  (0,0,SLOT,SLOT), border_radius=8)
            pygame.draw.rect(slot_surf, (65, 50, 85, 160),  (0,0,SLOT,SLOT), 2, border_radius=8)
        surf.blit(slot_surf, (sx, cursor_y))

        # Gun image centred in slot
        if gun_img:
            iw, ih  = gun_img.get_size()
            max_dim = SLOT - PAD * 2
            scale   = min(max_dim / iw, max_dim / ih)
            sw_, sh_ = max(1, round(iw*scale)), max(1, round(ih*scale))
            scaled  = pygame.transform.smoothscale(gun_img, (sw_, sh_))
            surf.blit(scaled, (sx + (SLOT-sw_)//2, cursor_y + (SLOT-sh_)//2))

        # Hotkey badge top-left
        badge = pygame.Surface((20, 20), pygame.SRCALPHA)
        badge.fill((0, 0, 0, 180))
        surf.blit(badge, (sx + 3, cursor_y + 3))
        hk = font_s.render(hotkey, True, active_col if active else (120, 110, 140))
        surf.blit(hk, (sx + 5, cursor_y + 3))

        # Active arrow to the left of slot
        if active:
            ax = sx - 12
            ay = cursor_y + SLOT//2
            pygame.draw.polygon(surf, active_col, [(ax,ay-6),(ax+9,ay),(ax,ay+6)])

        # Gun name below slot
        col    = active_col if active else (80, 70, 100)
        name_t = font_s.render(name, True, col)
        surf.blit(name_t, name_t.get_rect(centerx=sx + SLOT//2, top=cursor_y + SLOT + 2))

        cursor_y += SLOT + font_s.get_height() + 6 + GAP

    # ── Divider ───────────────────────────────────────────
    cursor_y += GAP // 2
    pygame.draw.line(surf, (80, 60, 110), (PANEL_X + 8, cursor_y), (PANEL_X + PANEL_W - 8, cursor_y), 1)
    cursor_y += GAP

    # ── AMMO label ───────────────────────────────────────
    ammo_col = (100, 255, 140) if ammo > ammo_max * 0.4 else \
               (255, 220,  60) if ammo > ammo_max * 0.15 else (255, 80, 80)
    lbl = font_b.render("AMMO", True, (170, 160, 205))
    surf.blit(lbl, lbl.get_rect(centerx=CX, top=cursor_y))
    cursor_y += lbl.get_height() + GAP

    # ── Ammo number ──────────────────────────────────────
    num_t = font_big_ammo.render(str(ammo), True, ammo_col)
    surf.blit(num_t, num_t.get_rect(centerx=CX, top=cursor_y))
    cursor_y += num_t.get_height() + GAP

    # ── Pip grid ─────────────────────────────────────────
    pip_ox = PANEL_X + (PANEL_W - pip_cols*(pip_r*2 + pip_gap) + pip_gap) // 2
    for i in range(pip_total):
        filled = i < ammo        # left-to-right: filled = remaining ammo
        pcol   = ammo_col if filled else (45, 35, 60)
        row    = i // pip_cols
        col_i  = i % pip_cols
        px     = pip_ox + col_i * (pip_r*2 + pip_gap) + pip_r
        py     = cursor_y + row * (pip_r*2 + pip_gap) + pip_r
        pygame.draw.circle(surf, pcol, (px, py), pip_r)
    cursor_y += pip_block_h + GAP

    # ── Divider ───────────────────────────────────────────
    pygame.draw.line(surf, (80, 60, 110), (PANEL_X + 8, cursor_y), (PANEL_X + PANEL_W - 8, cursor_y), 1)
    cursor_y += GAP

    # ── Hints ────────────────────────────────────────────
    for key_str, desc in hint_lines:
        kt = font_s.render(key_str, True, (150, 145, 200))
        dt = font_s.render(desc,    True, ( 90,  85, 130))
        surf.blit(kt, (INNER_X,                       cursor_y))
        surf.blit(dt, (INNER_X + kt.get_width() + 6,  cursor_y))
        cursor_y += font_s.get_height() + 3


# ═══════════════════════════════════════════════════════════════════════════════
#  TITLE CARD
# ═══════════════════════════════════════════════════════════════════════════════
def draw_title_card(surf, lv, timer, font_big, font_med, font_s):
    # timer counts DOWN from 120 → 0
    if timer > 80:
        alpha = int((120 - timer) / 40 * 255)
    elif timer > 40:
        alpha = 255
    else:
        alpha = int(timer / 40 * 255)
    alpha = max(0, min(255, alpha))
    if alpha <= 0: return

    overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, min(255, int(alpha * 0.65))))
    surf.blit(overlay, (0, 0))

    def fade_blit(text_surf, center):
        ts = text_surf.copy(); ts.set_alpha(alpha)
        surf.blit(ts, ts.get_rect(center=center))

    # Level title  (e.g. "LEVEL 1")
    fade_blit(font_big.render(lv["title"], True, C_PORTAL),        (SW//2, SH//2 - 80))
    # Sub-title    (e.g. "THE THRESHOLD")
    fade_blit(font_med.render(lv["sub"],   True, (220, 200, 255)), (SW//2, SH//2 - 10))
    # Lore leak    (cryptic one-liner, cyan-tinted, smaller)
    if lv.get("lore"):
        lore_font = pygame.font.Font(None, 38)
        fade_blit(lore_font.render(lv["lore"], True, (140, 230, 220)), (SW//2, SH//2 + 55))
    # Riddle       (optional extra puzzle hint)
    if lv.get("riddle"):
        fade_blit(font_s.render(lv["riddle"], True, (180, 220, 255)), (SW//2, SH//2 + 100))


# ═══════════════════════════════════════════════════════════════════════════════
#  ENDING SEQUENCE
# ═══════════════════════════════════════════════════════════════════════════════
def run_ending(screen, clock):
    """Play the ending cutscene. Returns when complete."""
    SW2, SH2 = screen.get_size()

    # Fade out music gracefully over 2 seconds
    pygame.mixer.music.fadeout(2000)
    global _current_track
    _current_track = None
    font_big  = pygame.font.Font(None, 96)
    font_med  = pygame.font.Font(None, 58)
    font_sml  = pygame.font.Font(None, 38)

    # Sequence of (text, colour, y_offset_from_centre, start_frame, hold_frames)
    BEATS = [
        # Act 1 — the door opens
        ("The door opens.",              (200, 200, 255), -60,   0,  160),
        ("Light floods in.",             (255, 255, 220),  10,  80,  160),
        # Act 2 — something is wrong
        ("But the light is wrong.",      (200, 100, 100), -40, 220,  160),
        # Act 3 — the line
        ('"Every place is strange',      (140, 230, 220), -30, 380,  140),
        ("to something.\"",              (140, 230, 220),  30, 400,  160),
        # Act 4 — pause then you are ready
        ("You are ready.",               (60,  220, 255),   0, 600,  200),
        # Act 5 — twist
        ("Phase Two.",                   (255,  80,  80),   0, 900,  300),
    ]

    TOTAL_FRAMES = 1260   # ~21 seconds at 60 fps

    frame = 0
    zoom  = 1.0

    while frame < TOTAL_FRAMES:
        clock.tick(FPS)
        frame += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                return   # any key skips

        # Slowly zoom out during phase-two reveal (frames 900+)
        if frame > 900:
            zoom = max(0.6, 1.0 - (frame - 900) / 1200)

        # Background — deep black with subtle vignette
        screen.fill((5, 3, 12))

        # Draw each text beat with its own fade
        for (text, col, y_off, start, hold) in BEATS:
            rel = frame - start
            if rel < 0:
                continue
            if rel < 40:
                a = int(rel / 40 * 255)
            elif rel < hold:
                a = 255
            else:
                a = max(0, int(255 - (rel - hold) / 40 * 255))
            if a <= 0:
                continue

            # Choose font size by which act we're in
            if text in ("Phase Two.",):
                fnt = font_big
            elif text.startswith('"') or "strange" in text or "wrong" in text:
                fnt = font_med
            else:
                fnt = font_sml

            rendered = fnt.render(text, True, col)
            rendered.set_alpha(a)
            cx = int(SW2 // 2 + (SW2 // 2) * (zoom - 1))
            cy = SW2 // 2   # unused, kept for reference
            pos = rendered.get_rect(center=(SW2 // 2, SH2 // 2 + y_off))
            screen.blit(rendered, pos)

        # "Phase Two." — add red border flash
        if frame > 900:
            t = frame - 900
            intensity = min(200, int(t * 0.6))
            pygame.draw.rect(screen, (intensity, 0, 0), (0, 0, SW2, SH2), 10)

        pygame.display.flip()

    # Hard fade to black
    fade = pygame.Surface((SW2, SH2))
    fade.fill((0, 0, 0))
    for a in range(0, 256, 4):
        fade.set_alpha(a)
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)


# ═══════════════════════════════════════════════════════════════════════════════
#  MENU SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
def run_menu(screen, clock, menu_imgs):
    """Show the main menu. Returns 'play', 'settings', or 'exit'."""
    SW2, SH2 = screen.get_size()

    play_music(PATHS["ost_main"])

    bg_img       = menu_imgs.get("menu_bg")
    play_img     = menu_imgs.get("btn_play")
    settings_img = menu_imgs.get("btn_settings")
    exit_img     = menu_imgs.get("btn_exit")

    # Background scaled once
    bg_scaled = pygame.transform.smoothscale(bg_img, (SW2, SH2)) if bg_img else None

    # From the reference: buttons are on the RIGHT side, stacked vertically
    # roughly the top-right quadrant. Using proportional coords from the reference image.
    BTN_W = int(SW2 * 0.28)   # button width
    BTN_H = int(SH2 * 0.115)  # button height
    BTN_X = int(SW2 * 0.675)  # left edge of buttons

    btn_play_rect     = pygame.Rect(BTN_X, int(SH2 * 0.19),  BTN_W, BTN_H)
    btn_settings_rect = pygame.Rect(BTN_X, int(SH2 * 0.345), BTN_W, BTN_H)
    btn_exit_rect     = pygame.Rect(BTN_X, int(SH2 * 0.49),  BTN_W, BTN_H)

    def prescale(img):
        return pygame.transform.smoothscale(img, (BTN_W, BTN_H)) if img else None

    play_s     = prescale(play_img)
    settings_s = prescale(settings_img)
    exit_s     = prescale(exit_img)

    def draw_btn(img_s, rect, hover):
        if img_s:
            if hover:
                lit = img_s.copy()
                lit.fill((30, 30, 30, 0), special_flags=pygame.BLEND_RGB_ADD)
                screen.blit(lit, rect.topleft)
            else:
                screen.blit(img_s, rect.topleft)
        else:
            col = (80, 80, 220) if hover else (50, 50, 180)
            pygame.draw.rect(screen, col, rect, border_radius=14)

    while True:
        clock.tick(FPS)
        mpos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "exit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_play_rect.collidepoint(mpos):     return "play"
                if btn_settings_rect.collidepoint(mpos): return "settings"
                if btn_exit_rect.collidepoint(mpos):     return "exit"

        # Draw background
        if bg_scaled:
            screen.blit(bg_scaled, (0, 0))
        else:
            screen.fill((30, 20, 50))

        # Draw buttons
        draw_btn(play_s,     btn_play_rect,     btn_play_rect.collidepoint(mpos))
        draw_btn(settings_s, btn_settings_rect, btn_settings_rect.collidepoint(mpos))
        draw_btn(exit_s,     btn_exit_rect,     btn_exit_rect.collidepoint(mpos))

        pygame.display.flip()


# ═══════════════════════════════════════════════════════════════════════════════
#  SETTINGS SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
def run_settings(screen, clock, settings_imgs, music_on, sfx_on):
    """Show the settings screen. Returns (music_on, sfx_on) when closed."""
    SW2, SH2 = screen.get_size()

    # Switch to settings music
    if music_on:
        play_music(PATHS["ost_settings"])

    bg_img        = settings_imgs.get("settings_bg")
    music_on_img  = settings_imgs.get("music_on")
    music_off_img = settings_imgs.get("music_off")
    sfx_on_img    = settings_imgs.get("sfx_on")
    sfx_off_img   = settings_imgs.get("sfx_off")

    # Background scaled once
    bg_scaled = pygame.transform.smoothscale(bg_img, (SW2, SH2)) if bg_img else None

    # From the reference: Music button upper-right, SFX below it, BACK below that
    BTN_W = int(SW2 * 0.28)
    BTN_H = int(SH2 * 0.115)
    BTN_X = int(SW2 * 0.675)

    music_rect = pygame.Rect(BTN_X, int(SH2 * 0.14),  BTN_W, BTN_H)
    sfx_rect   = pygame.Rect(BTN_X, int(SH2 * 0.295), BTN_W, BTN_H)
    back_rect  = pygame.Rect(BTN_X, int(SH2 * 0.43),  BTN_W, BTN_H)

    font_b = pygame.font.Font(None, 58)

    def prescale(img):
        return pygame.transform.smoothscale(img, (BTN_W, BTN_H)) if img else None

    mus_on_s  = prescale(music_on_img)
    mus_off_s = prescale(music_off_img)
    sfx_on_s  = prescale(sfx_on_img)
    sfx_off_s = prescale(sfx_off_img)

    def draw_toggle(on_s, off_s, rect, state, hover, fallback_label):
        img = on_s if state else off_s
        if img:
            if hover:
                lit = img.copy()
                lit.fill((25, 25, 25, 0), special_flags=pygame.BLEND_RGB_ADD)
                screen.blit(lit, rect.topleft)
            else:
                screen.blit(img, rect.topleft)
        else:
            col = (110, 30, 180) if state else (60, 60, 80)
            if hover: col = tuple(min(255, c + 25) for c in col)
            pygame.draw.rect(screen, col, rect, border_radius=14)
            pygame.draw.rect(screen, (180, 140, 255), rect, 3, border_radius=14)
            txt = font_b.render(f"{fallback_label}: {'ON' if state else 'OFF'}", True, (240, 210, 255))
            screen.blit(txt, txt.get_rect(center=rect.center))

    while True:
        clock.tick(FPS)
        mpos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return music_on, sfx_on
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if music_on:
                    play_music(PATHS["ost_main"])
                return music_on, sfx_on
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if music_rect.collidepoint(mpos):
                    music_on = not music_on
                    if music_on:
                        play_music(PATHS["ost_settings"])
                    else:
                        pygame.mixer.music.stop()
                        _current_track = None
                if sfx_rect.collidepoint(mpos):
                    sfx_on = not sfx_on
                if back_rect.collidepoint(mpos):
                    # Restore main OST when returning to menu
                    if music_on:
                        play_music(PATHS["ost_main"])
                    return music_on, sfx_on

        # Draw background only
        if bg_scaled:
            screen.blit(bg_scaled, (0, 0))
        else:
            screen.fill((30, 20, 50))

        # Draw toggle buttons
        draw_toggle(mus_on_s, mus_off_s, music_rect, music_on, music_rect.collidepoint(mpos), "MUSIC")
        draw_toggle(sfx_on_s, sfx_off_s, sfx_rect,   sfx_on,   sfx_rect.collidepoint(mpos),   "SFX")

        # BACK button
        hover_back = back_rect.collidepoint(mpos)
        back_col   = (75, 55, 130) if hover_back else (50, 35, 95)
        pygame.draw.rect(screen, back_col, back_rect, border_radius=14)
        pygame.draw.rect(screen, (160, 130, 220), back_rect, 3, border_radius=14)
        bt = font_b.render("BACK", True, (220, 200, 255))
        screen.blit(bt, bt.get_rect(center=back_rect.center))

        pygame.display.flip()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SW, SH))
    clock  = pygame.time.Clock()

    # Pixel fonts
    font_big = pygame.font.Font(None, 96)
    font_med = pygame.font.Font(None, 62)
    font_b   = pygame.font.Font(None, 34)
    font_s   = pygame.font.Font(None, 26)

    # ── Load game assets ──────────────────────────────────
    slime_img,  _     = load_img(PATHS["slime"],      (62, 62))
    pistol_img, _     = load_img(PATHS["pistol"],     (40, 22))
    hush_img,   _     = load_img(PATHS["hush"],       (48, 24))
    bullet_img, _     = load_img(PATHS["bullet"],     (14, 14))
    bg_img,     bg_ok = load_img(PATHS["bg"],         (SW, SH))
    tile_img,   ti_ok = load_img(PATHS["tile"],       (64, 64))
    btn_p_img,  _     = load_img(PATHS["btn_pistol"], (48, 48))
    btn_h_img,  _     = load_img(PATHS["btn_hush"],   (48, 48))
    door_img,   _     = load_img(PATHS["door"])

    IMGS.update({
        "slime"     : slime_img,
        "pistol"    : pistol_img,
        "hush"      : hush_img,
        "bullet"    : bullet_img,
        "btn_pistol": btn_p_img,
        "btn_hush"  : btn_h_img,
        "door"      : door_img,
    })
    images = {"slime": slime_img, "pistol": pistol_img, "hush": hush_img}

    # ── Load menu / settings assets ───────────────────────
    def _li(key, size=None):
        img, _ = load_img(PATHS[key], size)
        return img

    menu_imgs = {
        "menu_bg"     : _li("menu_bg",      (SW, SH)),
        "btn_play"    : _li("btn_play"),
        "btn_settings": _li("btn_settings"),
        "btn_exit"    : _li("btn_exit"),
    }
    settings_imgs = {
        "settings_bg" : _li("settings_bg",  (SW, SH)),
        "music_on"    : _li("music_on"),
        "music_off"   : _li("music_off"),
        "sfx_on"      : _li("sfx_on"),
        "sfx_off"     : _li("sfx_off"),
    }

    # ── Settings state ─────────────────────────────────────
    music_on = True
    sfx_on   = True

    # ── Menu loop ─────────────────────────────────────────
    while True:
        result = run_menu(screen, clock, menu_imgs)

        if result == "exit":
            pygame.quit()
            return

        if result == "settings":
            music_on, sfx_on = run_settings(screen, clock, settings_imgs, music_on, sfx_on)
            continue   # go back to menu

        # result == "play" — fall through to game
        break

    # Ensure main OST is playing for gameplay
    if music_on:
        play_music(PATHS["ost_main"])

    # ── Game state ─────────────────────────────────────────
    lv_idx     = 0
    lv         = load_level(lv_idx)
    bullets    = pygame.sprite.Group()
    slime      = Slime(*lv["spawn"], images)
    card_timer = 120
    ammo       = lv["ammo"]
    ammo_max   = ammo
    game_over  = False     # True when player runs out of ammo with portal still locked

    def restart_level():
        nonlocal lv, ammo, ammo_max, game_over, card_timer
        lv         = load_level(lv_idx)
        slime.reset(*lv["spawn"])
        bullets.empty()
        ammo      = lv["ammo"]
        ammo_max  = ammo
        game_over = False
        card_timer = 120

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Return to main menu
                    running = False
                    main()
                    return
                if event.key == pygame.K_r:
                    restart_level()
            if not game_over:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if ammo > 0:
                        if slime.shoot(pygame.mouse.get_pos(), bullets, bullet_img):
                            ammo -= 1
                            # Check immediately: out of ammo + portal still locked = lose
                            if ammo == 0 and not lv["portal"].is_open(lv["btns"]):
                                game_over = True

        keys = pygame.key.get_pressed()
        mpos = pygame.mouse.get_pos()

        # ── Update (skip all gameplay when game over) ──────
        if not game_over:
            if card_timer <= 0:
                slime.handle_input(keys)
            slime.apply_gravity(get_solids(lv))
            slime.tick()
            bullets.update()

            for mp in lv["mps"]:    mp.update()
            for d  in lv["doors"]:  d.update()
            for b  in lv["btns"]:   b.update()
            for cb in lv["cracks"]: cb.update()
            lv["portal"].update()

            # Bullet collisions
            for blt in list(bullets):
                for btn in lv["btns"]:   btn.try_hit(blt)
                for cb  in lv["cracks"]: cb.try_hit(blt)

            # Portal check
            if (lv["portal"].is_open(lv["btns"]) and
                    lv["portal"].touches(slime.rect)):
                if lv_idx == len(LEVELS) - 1:
                    # Last level — play ending then return to menu
                    run_ending(screen, clock)
                    running = False
                else:
                    lv_idx     = lv_idx + 1
                    lv         = load_level(lv_idx)
                    slime.reset(*lv["spawn"])
                    bullets.empty()
                    ammo       = lv["ammo"]; ammo_max = ammo
                    game_over  = False; card_timer = 120

            if card_timer > 0: card_timer -= 1

        # ── Draw ──────────────────────────────────────────
        # Background — always full screen fill first
        screen.fill(C_BG)
        if bg_ok:
            screen.blit(bg_img, (0, 0))   # already scaled to SW×SH

        # Ground strip
        pygame.draw.rect(screen, C_GROUND, (0, GROUND_Y, SW, SH-GROUND_Y))
        pygame.draw.line(screen, C_PLAT_TOP, (0, GROUND_Y), (SW, GROUND_Y), 3)

        # Static platforms
        for pr in lv["plats"]:
            if ti_ok:
                for tx in range(pr.left, pr.right, 64):
                    screen.blit(tile_img, (tx, pr.top-8))
            else:
                pygame.draw.rect(screen, C_PLAT, pr, border_radius=4)
                pygame.draw.rect(screen, C_PLAT_TOP, pr, 2, border_radius=4)

        # World objects
        for mp in lv["mps"]:    mp.draw(screen)
        for d  in lv["doors"]:  d.draw(screen, font_s)
        for cb in lv["cracks"]: cb.draw(screen, font_s)
        for b  in lv["btns"]:   b.draw(screen, font_s)
        lv["portal"].draw(screen, lv["btns"], font_s)

        # Bullets + Slime
        bullets.draw(screen)
        slime.draw(screen, mpos)

        # HUD
        draw_hud(screen, slime, lv_idx, ammo, ammo_max, font_b, font_s)

        # Title card
        if card_timer > 0:
            draw_title_card(screen, lv, card_timer, font_big, font_med, font_s)

        # ── GAME OVER overlay ─────────────────────────────
        if game_over:
            dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 170))
            screen.blit(dim, (0, 0))

            # Red flash border
            pygame.draw.rect(screen, (180, 30, 30), (0, 0, SW, SH), 8)

            # "OUT OF AMMO!" heading
            t1 = font_big.render("OUT OF AMMO!", True, (255, 70, 70))
            screen.blit(t1, t1.get_rect(center=(SW//2, SH//2 - 70)))

            # Sub message
            t2 = font_med.render("You needed more precision.", True, (220, 180, 180))
            screen.blit(t2, t2.get_rect(center=(SW//2, SH//2 + 10)))

            # Pulsing restart prompt
            pulse = int(200 + 55 * math.sin(pygame.time.get_ticks() * 0.005))
            t3 = font_b.render("Press  R  to try again", True, (pulse, pulse, pulse))
            screen.blit(t3, t3.get_rect(center=(SW//2, SH//2 + 80)))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
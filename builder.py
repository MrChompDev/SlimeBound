"""
SlimeBound Level Builder
Save/load levels as JSON, export as Python code for main.py
All assets loaded, full feature support
"""

import json
import sys
from pathlib import Path
import pygame


# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
SW, SH      = 1920, 1080
FPS         = 60
GROUND_Y    = SH - 100
GRID        = 20

ROOT        = Path(__file__).resolve().parent
LEVELS_DIR  = ROOT / "Levels"
ASSETS_DIR  = ROOT / "Assets"

LEVELS_DIR.mkdir(parents=True, exist_ok=True)

TOOLS = [
    "platform",      # 1
    "door",          # 2
    "small_button",  # 3
    "large_button",  # 4
    "crack",         # 5
    "moving_plat",   # 6
    "spawn",         # 7
    "portal",        # 8
    "link",          # 9
]

# Colors
C_BG          = ( 22,  14,  40)
C_GROUND      = ( 48,  34,  68)
C_PLAT        = ( 65,  50,  90)
C_PLAT_TOP    = (110,  85, 150)
C_GRID        = ( 34,  34,  46)
C_PORTAL      = ( 60, 220, 255)


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def snap(v):
    return int(round(v / GRID) * GRID)


def rect_from_points(a, b):
    x1, y1 = a
    x2, y2 = b
    x = min(x1, x2)
    y = min(y1, y2)
    w = max(GRID, abs(x2 - x1))
    h = max(GRID, abs(y2 - y1))
    return [x, y, w, h]


def load_img(path, size=None):
    try:
        img = pygame.image.load(str(path)).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#  LEVEL BUILDER
# ═══════════════════════════════════════════════════════════════════════════════
class LevelBuilder:
    def __init__(self, out_name="level_custom.json"):
        pygame.init()
        self.screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("SlimeBound Level Builder")
        self.clock  = pygame.time.Clock()
        self.font_b = pygame.font.Font(None, 28)
        self.font_s = pygame.font.Font(None, 22)

        # ── Load all assets ────────────────────────────────────
        self.slime_img    = load_img(ASSETS_DIR / "Character" / "Slime.png", (60, 60))
        self.pistol_img   = load_img(ASSETS_DIR / "Guns" / "Pistol.png")
        self.hush_img     = load_img(ASSETS_DIR / "Guns" / "Hush_Puppy.png")
        self.bullet_img   = load_img(ASSETS_DIR / "Guns" / "Bullet.png")
        self.tile_img     = load_img(ASSETS_DIR / "Tiles" / "Tile_01.png", (64, 64))
        self.bg_img       = load_img(ASSETS_DIR / "Tiles" / "Background.png", (SW, SH))
        self.btn_p_img    = load_img(ASSETS_DIR / "Tiles" / "Button_Pistol.png")
        self.btn_h_img    = load_img(ASSETS_DIR / "Tiles" / "Button_Hush.png")
        self.door_img     = load_img(ASSETS_DIR / "Tiles" / "Door.png")

        self.out_name     = out_name
        self.tool_idx     = 0
        self.drag_start   = None
        self.drag_current = None
        self.pending_mp   = None
        self.pending_link_btn = None

        self.next_door_id = 1
        self.next_mp_id   = 1
        self.current_level_num = 1  # Track which numbered level we're viewing

        self.level = self.new_level_data()

    def new_level_data(self):
        return {
            "title": "CUSTOM LEVEL",
            "sub": "BUILDER",
            "ammo": 20,
            "riddle": None,
            "spawn": [120, GROUND_Y - 80],
            "plats": [],
            "moving_platforms": [],
            "doors": [],
            "buttons": [],
            "cracks": [],
            "portal": {"x": 1750, "y": GROUND_Y - 50, "r": 36},
        }

    @property
    def tool(self):
        return TOOLS[self.tool_idx]

    def cycle_tool(self, delta):
        self.tool_idx = (self.tool_idx + delta) % len(TOOLS)
        self.cancel_drag()

    def set_tool(self, idx):
        self.tool_idx = max(0, min(idx, len(TOOLS) - 1))
        self.cancel_drag()

    def cancel_drag(self):
        self.drag_start = None
        self.drag_current = None

    # ── SAVE / LOAD ────────────────────────────────────────────
    def save(self):
        # Save to numbered level if editing one, otherwise use out_name
        if self.current_level_num and self.current_level_num > 0:
            filename = f"level{self.current_level_num}.json"
        else:
            filename = self.out_name
            
        path = LEVELS_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.level, f, indent=2)
        print(f"✓ Saved JSON: {path}")

    def export_python(self):
        """Export as Python code that can be pasted into main.py"""
        # Use numbered filename if editing a numbered level
        if self.current_level_num and self.current_level_num > 0:
            py_name = f"level{self.current_level_num}.py"
        else:
            py_name = self.out_name.replace(".json", ".py")
            
        path = LEVELS_DIR / py_name

        code = self.generate_python_function()
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"✓ Exported Python: {path}")
        print("  Copy the function into main.py LEVELS list!")

    def generate_python_function(self):
        """Convert current level to a Python function matching main.py format"""
        lv = self.level
        func_name = lv["title"].lower().replace(" ", "_")
        title = lv["title"]
        sub   = lv["sub"]
        riddle = lv.get("riddle")
        ammo   = lv.get("ammo", 20)
        sx, sy = lv["spawn"]

        lines = [
            f'def {func_name}():',
            f'    """Generated from builder: {title}"""',
            f'    plats = [',
        ]

        for p in lv["plats"]:
            lines.append(f'        pygame.Rect({p[0]}, {p[1]}, {p[2]}, {p[3]}),')
        lines.append('    ]')
        lines.append('')

        # Doors
        if lv["doors"]:
            for d in lv["doors"]:
                did = d["id"]
                lines.append(f'    {did} = Door({d["x"]}, {d["y"]}, {d["w"]}, {d["h"]})')
            lines.append('')

        # Moving platforms
        if lv["moving_platforms"]:
            for mp in lv["moving_platforms"]:
                mid = mp["id"]
                spd = mp.get("speed", 2)
                lines.append(f'    {mid} = MovingPlatform({mp["x"]}, {mp["y"]}, {mp["w"]}, {mp["h"]}, {mp["ex"]}, {mp["ey"]}, speed={spd})')
            lines.append('')

        # Cracked blocks
        if lv["cracks"]:
            lines.append('    crack_wall = [')
            for c in lv["cracks"]:
                lines.append(f'        CrackedBlock({c["x"]}, {c["y"]}, {c["w"]}, {c["h"]}),')
            lines.append('    ]')
            lines.append('')
        else:
            lines.append('    crack_wall = []')
            lines.append('')

        # Buttons
        if lv["buttons"]:
            for i, b in enumerate(lv["buttons"]):
                if b["type"] == "small":
                    lines.append(f'    btn{i+1} = SmallButton({b["x"]}, {b["y"]}, "{b.get("label", "PISTOL")}")')
                else:
                    w = b.get("w", 72)
                    h = b.get("h", 48)
                    lines.append(f'    btn{i+1} = LargeButton({b["x"]}, {b["y"]}, w={w}, h={h}, label="{b.get("label", "HUSH")}")')

            lines.append('')

            # Links
            for i, b in enumerate(lv["buttons"]):
                if b.get("links"):
                    targets = ', '.join(b["links"])
                    lines.append(f'    btn{i+1}.link({targets})')
            lines.append('')

        # Portal
        px = lv["portal"]["x"]
        py = lv["portal"]["y"]
        pr = lv["portal"].get("r", 36)
        lines.append(f'    portal = Portal({px}, {py}, r={pr})')
        lines.append('')

        # Return statement
        door_list = '[' + ', '.join([d["id"] for d in lv["doors"]]) + ']' if lv["doors"] else '[]'
        mp_list   = '[' + ', '.join([mp["id"] for mp in lv["moving_platforms"]]) + ']' if lv["moving_platforms"] else '[]'
        btn_list  = '[' + ', '.join([f'btn{i+1}' for i in range(len(lv["buttons"]))]) + ']' if lv["buttons"] else '[]'

        riddle_str = f'"{riddle}"' if riddle else 'None'

        lines.append(f'    return ("{title}", "{sub}",')
        lines.append(f'            plats, {mp_list}, {door_list},')
        lines.append(f'            {btn_list}, crack_wall, portal,')
        lines.append(f'            ({sx}, {sy}), {riddle_str}, {ammo})')

        return '\n'.join(lines)

    def load(self, file_name):
        """Load a level from JSON file"""
        path = LEVELS_DIR / file_name
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        required = ["plats", "moving_platforms", "doors", "buttons", "cracks", "portal", "spawn"]
        for key in required:
            if key not in data:
                raise ValueError(f"Invalid level file: missing '{key}'")

        self.level = data
        self.next_door_id = max([0] + [
            int(d.get("id", "door_0").split("_")[-1])
            for d in self.level["doors"] if str(d.get("id", "")).startswith("door_")
        ]) + 1
        self.next_mp_id = max([0] + [
            int(m.get("id", "mp_0").split("_")[-1])
            for m in self.level["moving_platforms"] if str(m.get("id", "")).startswith("mp_")
        ]) + 1
        
        # Extract level number from filename if in format level{N}.json
        if file_name.startswith("level") and file_name.endswith(".json"):
            try:
                self.current_level_num = int(file_name[5:-5])
            except ValueError:
                pass

    def load_level_by_number(self, level_num):
        """Load a specific numbered level"""
        file_name = f"level{level_num}.json"
        try:
            self.load(file_name)
            print(f"✓ Loaded: {file_name}")
            return True
        except FileNotFoundError:
            print(f"✗ Level {level_num} not found")
            return False
        except Exception as ex:
            print(f"✗ Load failed: {ex}")
            return False

    # ── MOUSE HANDLERS ─────────────────────────────────────────
    def handle_mouse_down(self, pos, button):
        x, y = snap(pos[0]), snap(pos[1])

        if button == 1:  # Left click
            # If pending moving platform endpoint, set it
            if self.pending_mp is not None:
                self.pending_mp["ex"] = x
                self.pending_mp["ey"] = y
                self.level["moving_platforms"].append(self.pending_mp)
                self.pending_mp = None
                return
            self.on_left_down(x, y)

        elif button == 3:  # Right click = erase
            self.erase_at(x, y)

    def on_left_down(self, x, y):
        # Drag-based tools
        if self.tool in {"platform", "door", "crack", "moving_plat"}:
            self.drag_start = (x, y)
            self.drag_current = (x, y)
            return

        # Single-click tools
        if self.tool == "small_button":
            self.level["buttons"].append({
                "type": "small", "x": x, "y": y,
                "label": "PISTOL", "links": []
            })
            return

        if self.tool == "large_button":
            self.level["buttons"].append({
                "type": "large", "x": x, "y": y,
                "w": 72, "h": 48, "label": "HUSH", "links": []
            })
            return

        if self.tool == "spawn":
            self.level["spawn"] = [x, y]
            return

        if self.tool == "portal":
            self.level["portal"]["x"] = x
            self.level["portal"]["y"] = y
            return

        if self.tool == "link":
            # Click button to start linking
            btn = self.find_button_at(x, y)
            if btn is not None:
                self.pending_link_btn = btn
                return
            # Click target to link to active button
            target_id = self.find_target_id_at(x, y)
            if target_id and self.pending_link_btn is not None:
                links = self.pending_link_btn.setdefault("links", [])
                if target_id not in links:
                    links.append(target_id)

    def handle_mouse_up(self, pos, button):
        if button != 1 or self.drag_start is None:
            return

        x, y = snap(pos[0]), snap(pos[1])
        r = rect_from_points(self.drag_start, (x, y))

        if self.tool == "platform":
            self.level["plats"].append(r)

        elif self.tool == "door":
            self.level["doors"].append({
                "id": f"door_{self.next_door_id}",
                "x": r[0], "y": r[1], "w": r[2], "h": r[3]
            })
            self.next_door_id += 1

        elif self.tool == "crack":
            self.level["cracks"].append({
                "x": r[0], "y": r[1], "w": r[2], "h": r[3]
            })

        elif self.tool == "moving_plat":
            self.pending_mp = {
                "id": f"mp_{self.next_mp_id}",
                "x": r[0], "y": r[1], "w": r[2], "h": r[3],
                "ex": r[0], "ey": r[1],  # temp, will be set on next click
                "speed": 2
            }
            self.next_mp_id += 1

        self.drag_start = None
        self.drag_current = None

    def handle_mouse_motion(self, pos):
        if self.drag_start is not None:
            self.drag_current = (snap(pos[0]), snap(pos[1]))

    # ── KEYBOARD ───────────────────────────────────────────────
    def handle_key(self, event):
        # Tool selection 1-9
        if pygame.K_1 <= event.key <= pygame.K_9:
            idx = event.key - pygame.K_1
            if idx < len(TOOLS):
                self.set_tool(idx)

        elif event.key == pygame.K_q:
            self.cycle_tool(-1)
        elif event.key == pygame.K_e:
            self.cycle_tool(1)

        elif event.key == pygame.K_s:
            self.save()

        elif event.key == pygame.K_p:
            self.export_python()

        elif event.key == pygame.K_n:
            self.level = self.new_level_data()
            self.pending_mp = None
            self.pending_link_btn = None
            print("✓ New level")

        elif event.key == pygame.K_l:
            # Load next numbered level
            self.load_level_by_number(self.current_level_num + 1)
            
        elif event.key == pygame.K_LEFT:
            # Load previous numbered level
            if self.current_level_num > 1:
                self.load_level_by_number(self.current_level_num - 1)
                
        elif event.key == pygame.K_RIGHT:
            # Load next numbered level
            self.load_level_by_number(self.current_level_num + 1)

        elif event.key == pygame.K_LEFTBRACKET:
            self.level["ammo"] = max(1, self.level["ammo"] - 1)

        elif event.key == pygame.K_RIGHTBRACKET:
            self.level["ammo"] += 1

        elif event.key == pygame.K_t:
            # Edit title
            print("Enter new title (current:", self.level["title"], ")")

        elif event.key == pygame.K_BACKSPACE:
            if self.level["buttons"]:
                self.level["buttons"].pop()

        elif event.key == pygame.K_ESCAPE:
            self.pending_link_btn = None
            self.pending_mp = None
            self.cancel_drag()

    # ── FIND HELPERS ───────────────────────────────────────────
    def find_button_at(self, x, y):
        p = pygame.Vector2(x, y)
        for btn in self.level["buttons"]:
            if btn["type"] == "small":
                if p.distance_to((btn["x"], btn["y"])) <= 24:
                    return btn
            else:
                r = pygame.Rect(btn["x"], btn["y"], btn.get("w", 72), btn.get("h", 48))
                if r.collidepoint(x, y):
                    return btn
        return None

    def find_target_id_at(self, x, y):
        for d in self.level["doors"]:
            r = pygame.Rect(d["x"], d["y"], d["w"], d["h"])
            if r.collidepoint(x, y):
                return d["id"]
        for mp in self.level["moving_platforms"]:
            r = pygame.Rect(mp["x"], mp["y"], mp["w"], mp["h"])
            if r.collidepoint(x, y):
                return mp["id"]
        return None

    # ── ERASE ──────────────────────────────────────────────────
    def erase_at(self, x, y):
        pt = (x, y)
        self.level["plats"] = [r for r in self.level["plats"]
                               if not pygame.Rect(*r).collidepoint(pt)]

        self.level["cracks"] = [c for c in self.level["cracks"]
                                if not pygame.Rect(c["x"], c["y"], c["w"], c["h"]).collidepoint(pt)]

        self.level["doors"] = [d for d in self.level["doors"]
                               if not pygame.Rect(d["x"], d["y"], d["w"], d["h"]).collidepoint(pt)]

        self.level["moving_platforms"] = [
            mp for mp in self.level["moving_platforms"]
            if not pygame.Rect(mp["x"], mp["y"], mp["w"], mp["h"]).collidepoint(pt)
        ]

        keep_btns = []
        for btn in self.level["buttons"]:
            if btn["type"] == "small":
                if pygame.Vector2(btn["x"], btn["y"]).distance_to(pt) <= 24:
                    continue
            else:
                if pygame.Rect(btn["x"], btn["y"], btn.get("w", 72), btn.get("h", 48)).collidepoint(pt):
                    continue
            keep_btns.append(btn)
        self.level["buttons"] = keep_btns

    # ── DRAW ───────────────────────────────────────────────────
    def draw_tiled_rect(self, rect):
        if not self.tile_img:
            pygame.draw.rect(self.screen, C_PLAT, rect)
            return
        tw, th = self.tile_img.get_size()
        for yy in range(rect.top, rect.bottom, th):
            for xx in range(rect.left, rect.right, tw):
                self.screen.blit(self.tile_img, (xx, yy))

    def draw(self):
        # Background
        if self.bg_img:
            self.screen.blit(self.bg_img, (0, 0))
        else:
            self.screen.fill(C_BG)

        # Grid
        for x in range(0, SW, GRID):
            pygame.draw.line(self.screen, C_GRID, (x, 0), (x, SH))
        for y in range(0, SH, GRID):
            pygame.draw.line(self.screen, C_GRID, (0, y), (SW, y))

        # Ground strip
        pygame.draw.rect(self.screen, C_GROUND, (0, GROUND_Y, SW, SH - GROUND_Y))
        pygame.draw.line(self.screen, C_PLAT_TOP, (0, GROUND_Y), (SW, GROUND_Y), 3)

        # Platforms
        for r in self.level["plats"]:
            rr = pygame.Rect(*r)
            self.draw_tiled_rect(rr)
            pygame.draw.rect(self.screen, (120, 180, 220), rr, 1)

        # Doors
        for d in self.level["doors"]:
            rr = pygame.Rect(d["x"], d["y"], d["w"], d["h"])
            if self.door_img:
                # Tile door image at native size
                tw, th = self.door_img.get_size()
                for yy in range(rr.top, rr.bottom, th):
                    for xx in range(rr.left, rr.right, tw):
                        cw = min(tw, rr.right - xx)
                        ch = min(th, rr.bottom - yy)
                        self.screen.blit(self.door_img, (xx, yy),
                                        area=pygame.Rect(0, 0, cw, ch))
            else:
                pygame.draw.rect(self.screen, (120, 80, 140), rr)
            pygame.draw.rect(self.screen, (200, 180, 220), rr, 2)
            idt = self.font_s.render(d["id"], True, (255, 255, 255))
            self.screen.blit(idt, (rr.x + 4, rr.y + 4))

        # Cracked blocks
        for c in self.level["cracks"]:
            rr = pygame.Rect(c["x"], c["y"], c["w"], c["h"])
            pygame.draw.rect(self.screen, (120, 80, 50), rr)
            pygame.draw.line(self.screen, (60, 40, 25), rr.topleft, rr.bottomright, 2)
            pygame.draw.line(self.screen, (60, 40, 25), rr.topright, rr.bottomleft, 2)

        # Moving platforms
        for mp in self.level["moving_platforms"]:
            rr = pygame.Rect(mp["x"], mp["y"], mp["w"], mp["h"])
            pygame.draw.rect(self.screen, (80, 120, 175), rr, border_radius=5)
            pygame.draw.rect(self.screen, (150, 195, 255), rr, 2, border_radius=5)
            # Arrow to endpoint
            pygame.draw.line(self.screen, (100, 255, 255), rr.center, (mp["ex"], mp["ey"]), 2)
            pygame.draw.circle(self.screen, (100, 255, 255), (mp["ex"], mp["ey"]), 6)
            idt = self.font_s.render(mp["id"], True, (255, 255, 255))
            self.screen.blit(idt, (rr.x + 4, rr.y + 4))

        # Buttons
        for b in self.level["buttons"]:
            if b["type"] == "small":
                if self.btn_p_img:
                    sz = 44
                    im = pygame.transform.smoothscale(self.btn_p_img, (sz, sz))
                    self.screen.blit(im, im.get_rect(center=(b["x"], b["y"])))
                else:
                    pygame.draw.circle(self.screen, (80, 200, 100), (b["x"], b["y"]), 22)
                bpos = (b["x"], b["y"])
            else:
                rr = pygame.Rect(b["x"], b["y"], b.get("w", 72), b.get("h", 48))
                if self.btn_h_img:
                    im = pygame.transform.smoothscale(self.btn_h_img, (rr.w, rr.h))
                    self.screen.blit(im, rr.topleft)
                else:
                    pygame.draw.rect(self.screen, (220, 120, 60), rr, border_radius=6)
                bpos = rr.center

            # Draw link lines
            if b.get("links"):
                for target in b["links"]:
                    obj = next((d for d in self.level["doors"] if d["id"] == target), None)
                    if obj is None:
                        obj = next((m for m in self.level["moving_platforms"] if m["id"] == target), None)
                    if obj is not None:
                        tpos = (obj["x"] + obj["w"] // 2, obj["y"] + obj["h"] // 2)
                        pygame.draw.line(self.screen, (245, 230, 120), bpos, tpos, 2)

        # Active link button highlight
        if self.pending_link_btn is not None:
            bx = self.pending_link_btn["x"]
            by = self.pending_link_btn["y"]
            pygame.draw.circle(self.screen, (255, 255, 120), (bx, by), 30, 3)

        # Spawn
        spawn = self.level["spawn"]
        if self.slime_img:
            self.screen.blit(self.slime_img, self.slime_img.get_rect(center=(spawn[0], spawn[1])))
        else:
            pygame.draw.circle(self.screen, (120, 220, 120), (spawn[0], spawn[1]), 12, 2)

        # Portal
        portal = self.level["portal"]
        px, py, pr = portal["x"], portal["y"], portal.get("r", 36)
        for i in range(3, 0, -1):
            glow_r = pr + i * 4
            alpha_surf = pygame.Surface((glow_r * 2 + 20, glow_r * 2 + 20), pygame.SRCALPHA)
            pygame.draw.circle(alpha_surf, (*C_PORTAL, 30), (glow_r + 10, glow_r + 10), glow_r)
            self.screen.blit(alpha_surf, (px - glow_r - 10, py - glow_r - 10))
        pygame.draw.circle(self.screen, C_PORTAL, (px, py), pr, 3)
        lbl = self.font_s.render("PORTAL", True, C_PORTAL)
        self.screen.blit(lbl, lbl.get_rect(centerx=px, top=py + pr + 4))

        # Drag preview
        if self.drag_start and self.drag_current:
            rr = rect_from_points(self.drag_start, self.drag_current)
            pygame.draw.rect(self.screen, (230, 230, 90), rr, 2)

        # Pending moving platform message
        if self.pending_mp is not None:
            msg = self.font_b.render("Click endpoint for moving platform", True, (255, 255, 100))
            self.screen.blit(msg, (12, 60))

        # ── HUD ────────────────────────────────────────────────
        tool_str = " | ".join([f"{i+1}:{t}" for i, t in enumerate(TOOLS)])
        ui1 = f"Editing: Level {self.current_level_num}  |  Tool: {self.tool}  |  Q/E cycle  |  S save  |  P export Python  |  [ ] ammo({self.level['ammo']})"
        ui2 = f"Tools: {tool_str}"
        ui3 = "L: load next level  |  ←→: prev/next level  |  N: new level  |  Left click: place  |  Right click: erase"

        self.screen.blit(self.font_b.render(ui1, True, (240, 240, 240)), (12, 10))
        self.screen.blit(self.font_s.render(ui2, True, (210, 210, 210)), (12, 36))
        self.screen.blit(self.font_s.render(ui3, True, (190, 190, 200)), (12, 58))

        # Level info
        info = f'"{self.level["title"]}" / "{self.level["sub"]}" | Ammo: {self.level["ammo"]} | Spawn: {self.level["spawn"]}'
        self.screen.blit(self.font_s.render(info, True, (180, 180, 220)), (12, SH - 30))

        pygame.display.flip()

    # ── RUN ────────────────────────────────────────────────────
    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not (self.pending_link_btn or self.pending_mp or self.drag_start):
                        running = False
                    else:
                        self.handle_key(event)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_down(event.pos, event.button)

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_mouse_up(event.pos, event.button)

                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)

            self.draw()

        pygame.quit()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    out_name = sys.argv[1] if len(sys.argv) > 1 else "level_custom.json"
    if not out_name.lower().endswith(".json"):
        out_name += ".json"
    LevelBuilder(out_name).run()


if __name__ == "__main__":
    main()
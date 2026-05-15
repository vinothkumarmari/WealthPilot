"""Day 1 Instagram Post — Attractive UI with cartoon characters (Inflation Reality)."""
from PIL import Image, ImageDraw, ImageFont
import os, math

OUT = os.path.join(os.path.dirname(__file__), "app", "static", "insta_posts")
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1080

# Colors
PURPLE_DARK = (74, 0, 224)
PURPLE = (108, 92, 231)
PURPLE_LIGHT = (180, 160, 255)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
NEAR_WHITE = (245, 242, 255)
DARK = (18, 8, 42)
RED = (231, 76, 60)
ORANGE = (243, 156, 18)
GREEN = (46, 204, 113)
SKIN = (255, 218, 185)
SKIN_DARK = (230, 190, 155)
HAIR_DARK = (50, 30, 20)
BLUE_SHIRT = (52, 152, 219)
PINK = (255, 105, 180)

def get_font(size, bold=False):
    paths = (["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"] if bold
             else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"])
    for f in paths:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def gradient_bg(draw, w, h, c1, c2):
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def draw_centered_text(draw, y, text, font, fill=WHITE, w=W):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, y), text, font=font, fill=fill)

def draw_star(draw, cx, cy, size, fill):
    """5-point star."""
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = size if i % 2 == 0 else size * 0.4
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=fill)

def draw_rupee_coin(draw, cx, cy, r, glow=False):
    """Draw a ₹ coin."""
    if glow:
        for g in range(4, 0, -1):
            draw.ellipse([cx-r-g*3, cy-r-g*3, cx+r+g*3, cy+r+g*3],
                         fill=(255, 215, 0, 8))
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=GOLD, outline=(218, 165, 0), width=2)
    draw.ellipse([cx-r+4, cy-r+4, cx+r-4, cy+r-4], fill=None, outline=(255, 235, 100), width=1)
    f = get_font(int(r * 1.2), bold=True)
    bbox = draw.textbbox((0, 0), "₹", font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 3), "₹", font=f, fill=(150, 100, 0))

def draw_cartoon_person(draw, cx, cy, scale=1.0, expression="worried", shirt_color=BLUE_SHIRT, facing_right=True):
    """Draw a cute cartoon person."""
    s = scale
    # Body
    body_w, body_h = int(50 * s), int(60 * s)
    draw.rounded_rectangle([cx - body_w, cy, cx + body_w, cy + body_h],
                           radius=int(15 * s), fill=shirt_color)
    # Neck
    draw.rectangle([cx - int(10*s), cy - int(10*s), cx + int(10*s), cy + int(5*s)], fill=SKIN)
    # Head
    head_r = int(38 * s)
    hcy = cy - int(35 * s)
    draw.ellipse([cx - head_r, hcy - head_r, cx + head_r, hcy + head_r], fill=SKIN)
    # Hair
    draw.pieslice([cx - head_r - 2, hcy - head_r - 5, cx + head_r + 2, hcy + int(5*s)],
                  180, 0, fill=HAIR_DARK)
    # Eyes
    eye_off = int(14 * s)
    eye_y = hcy - int(5 * s)
    eye_r = int(6 * s)
    # White of eyes
    draw.ellipse([cx - eye_off - eye_r, eye_y - eye_r, cx - eye_off + eye_r, eye_y + eye_r], fill=WHITE)
    draw.ellipse([cx + eye_off - eye_r, eye_y - eye_r, cx + eye_off + eye_r, eye_y + eye_r], fill=WHITE)
    # Pupils
    pr = int(3 * s)
    if expression == "worried":
        draw.ellipse([cx - eye_off - pr, eye_y - pr + 1, cx - eye_off + pr, eye_y + pr + 1], fill=(40, 30, 20))
        draw.ellipse([cx + eye_off - pr, eye_y - pr + 1, cx + eye_off + pr, eye_y + pr + 1], fill=(40, 30, 20))
        # Worried eyebrows (angled)
        draw.line([(cx - eye_off - eye_r, eye_y - eye_r - int(6*s)),
                   (cx - eye_off + eye_r + 2, eye_y - eye_r - int(2*s))],
                  fill=HAIR_DARK, width=int(3*s))
        draw.line([(cx + eye_off - eye_r - 2, eye_y - eye_r - int(2*s)),
                   (cx + eye_off + eye_r, eye_y - eye_r - int(6*s))],
                  fill=HAIR_DARK, width=int(3*s))
        # Worried mouth (wavy/frown)
        mouth_y = hcy + int(15 * s)
        draw.arc([cx - int(12*s), mouth_y - int(5*s), cx + int(12*s), mouth_y + int(12*s)],
                 200, 340, fill=(180, 80, 60), width=int(3*s))
    elif expression == "shocked":
        # Big eyes
        draw.ellipse([cx - eye_off - pr - 1, eye_y - pr - 1, cx - eye_off + pr + 1, eye_y + pr + 1], fill=(40, 30, 20))
        draw.ellipse([cx + eye_off - pr - 1, eye_y - pr - 1, cx + eye_off + pr + 1, eye_y + pr + 1], fill=(40, 30, 20))
        # Raised eyebrows
        draw.arc([cx - eye_off - eye_r - 2, eye_y - eye_r - int(12*s),
                  cx - eye_off + eye_r + 2, eye_y - eye_r + int(2*s)],
                 200, 340, fill=HAIR_DARK, width=int(3*s))
        draw.arc([cx + eye_off - eye_r - 2, eye_y - eye_r - int(12*s),
                  cx + eye_off + eye_r + 2, eye_y - eye_r + int(2*s)],
                 200, 340, fill=HAIR_DARK, width=int(3*s))
        # Open mouth
        mouth_y = hcy + int(16 * s)
        draw.ellipse([cx - int(8*s), mouth_y, cx + int(8*s), mouth_y + int(14*s)],
                     fill=(180, 60, 50), outline=(150, 40, 30), width=1)
    elif expression == "happy":
        draw.ellipse([cx - eye_off - pr, eye_y - pr, cx - eye_off + pr, eye_y + pr], fill=(40, 30, 20))
        draw.ellipse([cx + eye_off - pr, eye_y - pr, cx + eye_off + pr, eye_y + pr], fill=(40, 30, 20))
        mouth_y = hcy + int(12 * s)
        draw.arc([cx - int(14*s), mouth_y - int(8*s), cx + int(14*s), mouth_y + int(8*s)],
                 10, 170, fill=(180, 80, 60), width=int(3*s))

    # Arms
    arm_y = cy + int(15 * s)
    if expression == "worried":
        # Hands on head gesture
        draw.line([(cx - body_w, arm_y), (cx - body_w - int(25*s), arm_y - int(30*s))],
                  fill=shirt_color, width=int(12*s))
        draw.line([(cx + body_w, arm_y), (cx + body_w + int(25*s), arm_y - int(30*s))],
                  fill=shirt_color, width=int(12*s))
        # Hands
        draw.ellipse([cx - body_w - int(32*s), arm_y - int(40*s),
                      cx - body_w - int(18*s), arm_y - int(26*s)], fill=SKIN)
        draw.ellipse([cx + body_w + int(18*s), arm_y - int(40*s),
                      cx + body_w + int(32*s), arm_y - int(26*s)], fill=SKIN)
    elif expression == "shocked":
        # Arms spread out
        draw.line([(cx - body_w, arm_y), (cx - body_w - int(35*s), arm_y + int(10*s))],
                  fill=shirt_color, width=int(12*s))
        draw.line([(cx + body_w, arm_y), (cx + body_w + int(35*s), arm_y + int(10*s))],
                  fill=shirt_color, width=int(12*s))
        draw.ellipse([cx - body_w - int(42*s), arm_y + int(3*s),
                      cx - body_w - int(28*s), arm_y + int(17*s)], fill=SKIN)
        draw.ellipse([cx + body_w + int(28*s), arm_y + int(3*s),
                      cx + body_w + int(42*s), arm_y + int(17*s)], fill=SKIN)

    # Legs
    leg_y = cy + body_h
    draw.rounded_rectangle([cx - int(25*s), leg_y, cx - int(5*s), leg_y + int(35*s)],
                           radius=int(8*s), fill=(60, 60, 80))
    draw.rounded_rectangle([cx + int(5*s), leg_y, cx + int(25*s), leg_y + int(35*s)],
                           radius=int(8*s), fill=(60, 60, 80))

def draw_flying_rupees(draw, coins):
    """Draw rupee coins scattered around."""
    for cx, cy, r in coins:
        draw_rupee_coin(draw, cx, cy, r)

def draw_arrow_up(draw, x, y, size, color):
    """Upward arrow for price rise."""
    draw.polygon([
        (x, y - size), (x + size * 0.7, y + size * 0.3),
        (x + size * 0.25, y + size * 0.3), (x + size * 0.25, y + size),
        (x - size * 0.25, y + size), (x - size * 0.25, y + size * 0.3),
        (x - size * 0.7, y + size * 0.3)
    ], fill=color)

def draw_receipt(draw, x, y, w, h, items):
    """Draw a receipt/bill."""
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=WHITE, outline=(200, 200, 200))
    # Zigzag bottom
    for i in range(0, w, 12):
        draw.polygon([(x + i, y + h), (x + i + 6, y + h + 8), (x + i + 12, y + h)], fill=WHITE)
    # Title
    draw.text((x + 15, y + 8), "BILL", font=get_font(16, bold=True), fill=(80, 80, 80))
    draw.line([(x + 10, y + 30), (x + w - 10, y + 30)], fill=(200, 200, 200), width=1)
    # Items
    for i, (name, price) in enumerate(items):
        iy = y + 36 + i * 20
        draw.text((x + 12, iy), name, font=get_font(13), fill=(100, 100, 100))
        draw.text((x + w - 55, iy), price, font=get_font(13, bold=True), fill=RED)

def draw_speech_bubble(draw, x, y, w, h, text, font, fill_bg=(255, 255, 255), fill_text=(40, 30, 60), tail="left"):
    """Speech bubble with tail."""
    draw.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=fill_bg)
    if tail == "left":
        draw.polygon([(x + 20, y + h), (x + 10, y + h + 18), (x + 40, y + h)], fill=fill_bg)
    elif tail == "right":
        draw.polygon([(x + w - 40, y + h), (x + w - 10, y + h + 18), (x + w - 20, y + h)], fill=fill_bg)
    # Text centered
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((x + (w - tw) // 2, y + (h - (bbox[3] - bbox[1])) // 2), text, font=font, fill=fill_text)

def draw_grocery_cart(draw, x, y, s=1.0):
    """Simple shopping cart icon."""
    # Cart body
    draw.rounded_rectangle([x, y, x + int(55*s), y + int(35*s)], radius=int(6*s),
                           fill=(200, 200, 220), outline=(150, 150, 170), width=2)
    # Handle
    draw.arc([x + int(40*s), y - int(20*s), x + int(70*s), y + int(10*s)],
             180, 0, fill=(150, 150, 170), width=int(3*s))
    # Wheels
    draw.ellipse([x + int(8*s), y + int(35*s), x + int(18*s), y + int(45*s)], fill=(100, 100, 120))
    draw.ellipse([x + int(38*s), y + int(35*s), x + int(48*s), y + int(45*s)], fill=(100, 100, 120))
    # Items in cart (small colored rectangles)
    draw.rectangle([x + int(5*s), y + int(5*s), x + int(18*s), y + int(20*s)], fill=(46, 204, 113))
    draw.rectangle([x + int(20*s), y + int(8*s), x + int(33*s), y + int(22*s)], fill=ORANGE)
    draw.rectangle([x + int(35*s), y + int(5*s), x + int(50*s), y + int(18*s)], fill=RED)

def draw_house(draw, x, y, s=1.0):
    """Simple house icon."""
    # Roof
    draw.polygon([(x + int(30*s), y), (x - int(5*s), y + int(30*s)),
                  (x + int(65*s), y + int(30*s))], fill=(180, 80, 60))
    # Body
    draw.rectangle([x + int(5*s), y + int(30*s), x + int(55*s), y + int(60*s)],
                   fill=(220, 200, 170))
    # Door
    draw.rectangle([x + int(20*s), y + int(38*s), x + int(38*s), y + int(60*s)],
                   fill=(120, 70, 40))
    # Window
    draw.rectangle([x + int(42*s), y + int(36*s), x + int(52*s), y + int(48*s)],
                   fill=(180, 220, 255), outline=(150, 150, 170))

def draw_gas_pump(draw, x, y, s=1.0):
    """Simple petrol pump icon."""
    # Body
    draw.rounded_rectangle([x, y + int(10*s), x + int(35*s), y + int(55*s)],
                           radius=int(5*s), fill=(80, 80, 100))
    # Screen
    draw.rectangle([x + int(5*s), y + int(15*s), x + int(30*s), y + int(30*s)], fill=(200, 255, 200))
    # Nozzle
    draw.line([(x + int(35*s), y + int(20*s)), (x + int(50*s), y + int(10*s))],
              fill=(80, 80, 100), width=int(4*s))
    draw.ellipse([x + int(46*s), y + int(5*s), x + int(54*s), y + int(15*s)], fill=(60, 60, 80))
    # Base
    draw.rectangle([x - int(3*s), y + int(55*s), x + int(38*s), y + int(60*s)], fill=(60, 60, 80))


def generate_day1():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)

    # === BACKGROUND ===
    # Rich gradient: dark purple → deep navy
    for y in range(H):
        t = y / H
        r = int(30 + t * (12 - 30))
        g = int(10 + t * (5 - 10))
        b = int(60 + t * (40 - 60))
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Subtle diagonal stripes for texture
    for i in range(-H, W + H, 80):
        draw.line([(i, 0), (i + H, H)], fill=(255, 255, 255, 3), width=1)

    # Glowing circles in corners (decorative)
    for cx, cy, cr, alpha in [(120, 120, 180, 6), (W - 100, H - 150, 200, 5),
                               (W - 200, 200, 120, 4), (200, H - 100, 150, 5)]:
        for g in range(cr, 0, -3):
            draw.ellipse([cx - g, cy - g, cx + g, cy + g], fill=(108, 92, 231, alpha))

    # === TOP SECTION: Warning banner ===
    draw_rounded_rect(draw, (40, 30, W - 40, 85), 16, fill=(231, 76, 60, 40), outline=RED, width=2)
    # Warning triangles drawn manually instead of emoji
    draw.polygon([(115, 42), (105, 60), (125, 60)], fill=GOLD)
    draw.text((112, 44), "!", font=get_font(14, bold=True), fill=RED)
    draw.polygon([(W - 115, 42), (W - 125, 60), (W - 105, 60)], fill=GOLD)
    draw.text((W - 118, 44), "!", font=get_font(14, bold=True), fill=RED)
    draw_centered_text(draw, 40, "INFLATION  -  THE SILENT THIEF", get_font(30, bold=True), fill=WHITE)

    # === MAIN TITLE ===
    draw_centered_text(draw, 105, "At ~6% inflation/year", get_font(38, bold=True), fill=WHITE)
    draw_centered_text(draw, 160, "Prices nearly DOUBLE", get_font(50, bold=True), fill=GOLD)
    draw_centered_text(draw, 220, "every 12 years", get_font(38, bold=True), fill=WHITE)

    # === CARTOON CHARACTER — worried person on LEFT ===
    draw_cartoon_person(draw, 160, 330, scale=1.4, expression="worried", shirt_color=BLUE_SHIRT)

    # Speech bubble from worried person
    draw_speech_bubble(draw, 50, 260, 220, 55,
                       "Why is everything costly?", get_font(18, bold=True),
                       fill_bg=(255, 255, 255, 220), fill_text=(180, 50, 40), tail="left")

    # === CARTOON CHARACTER — shocked person on RIGHT ===
    draw_cartoon_person(draw, W - 170, 330, scale=1.3, expression="shocked", shirt_color=PINK)

    # Speech bubble from shocked person
    draw_speech_bubble(draw, W - 310, 260, 240, 55,
                       "Same salary, more bills!", get_font(18, bold=True),
                       fill_bg=(255, 230, 230), fill_text=(180, 50, 40), tail="right")

    # === FLYING RUPEE COINS (scattered around characters) ===
    coins = [(100, 495, 14), (250, 310, 10), (W - 100, 495, 14),
             (W - 250, 320, 11), (W // 2 - 60, 315, 12), (W // 2 + 70, 330, 10),
             (80, 370, 8), (W - 80, 390, 9)]
    draw_flying_rupees(draw, coins)

    # === SMALL ICONS between characters ===
    draw_grocery_cart(draw, W // 2 - 28, 360, s=0.9)
    draw_house(draw, W // 2 - 30, 420, s=0.7)
    draw_gas_pump(draw, W // 2 - 18, 485, s=0.7)

    # Red up arrows near icons
    draw_arrow_up(draw, W // 2 + 50, 365, 12, RED)
    draw_arrow_up(draw, W // 2 + 50, 430, 12, RED)
    draw_arrow_up(draw, W // 2 + 45, 495, 12, RED)

    # === INFLATION BY CATEGORY (CPI-based ranges) ===
    table_y = 555

    # Table header
    draw_rounded_rect(draw, (55, table_y, W - 55, table_y + 50), 12, fill=PURPLE)
    draw.text((90, table_y + 10), "Category", font=get_font(24, bold=True), fill=WHITE)
    draw.text((480, table_y + 10), "Avg. Annual Inflation", font=get_font(24, bold=True), fill=WHITE)

    # CPI-sourced category data (RBI official ranges)
    # Using colored dot icons instead of emojis (Pillow can't render emojis)
    items = [
        ("Food & Beverages", "6 - 10%", ORANGE, (46, 204, 113)),
        ("Housing & Rent", "4 - 6%", ORANGE, (52, 152, 219)),
        ("Fuel & Transport", "5 - 12%", RED, (243, 156, 18)),
        ("Health & Medical", "6 - 8%", RED, (231, 76, 60)),
        ("Education", "8 - 12%", RED, (155, 89, 182)),
        ("Overall CPI", "~5 - 6%", ORANGE, GOLD),
    ]

    # Category icons drawn as small shapes
    def draw_category_icon(draw, x, y, index):
        """Draw a small icon for each category."""
        s = 0.45
        if index == 0:  # Food - small bowl
            draw.arc([x, y+2, x+22, y+20], 180, 0, fill=(46, 204, 113), width=3)
            draw.line([(x, y+12), (x+22, y+12)], fill=(46, 204, 113), width=2)
        elif index == 1:  # Housing - small house
            draw.polygon([(x+11, y), (x, y+12), (x+22, y+12)], fill=(52, 152, 219))
            draw.rectangle([x+3, y+12, x+19, y+22], fill=(52, 152, 219))
            draw.rectangle([x+8, y+14, x+14, y+22], fill=(30, 100, 170))
        elif index == 2:  # Fuel - droplet
            draw.polygon([(x+11, y), (x+2, y+14), (x+20, y+14)], fill=ORANGE)
            draw.ellipse([x+2, y+10, x+20, y+22], fill=ORANGE)
        elif index == 3:  # Health - cross
            draw.rectangle([x+7, y+1, x+15, y+21], fill=RED)
            draw.rectangle([x+1, y+7, x+21, y+15], fill=RED)
        elif index == 4:  # Education - book
            draw.rectangle([x+2, y+3, x+20, y+20], fill=(155, 89, 182))
            draw.line([(x+11, y+3), (x+11, y+20)], fill=(130, 60, 160), width=2)
            draw.rectangle([x+4, y+5, x+10, y+8], fill=(200, 180, 230))
        elif index == 5:  # Overall - chart
            draw.rectangle([x+1, y+14, x+6, y+22], fill=GOLD)
            draw.rectangle([x+8, y+8, x+13, y+22], fill=GOLD)
            draw.rectangle([x+15, y+3, x+20, y+22], fill=GOLD)

    for i, (item, rate, badge_color, dot_color) in enumerate(items):
        ry = table_y + 55 + i * 54
        row_fill = (35, 18, 70) if i % 2 == 0 else (45, 25, 80)
        is_last = (i == len(items) - 1)
        outline_c = GOLD if is_last else (108, 92, 231)
        draw_rounded_rect(draw, (55, ry, W - 55, ry + 50), 8, fill=row_fill,
                          outline=outline_c, width=2 if is_last else 1)

        # Category icon
        draw_category_icon(draw, 78, ry + 14, i)

        # Label text
        draw.text((110, ry + 12), item, font=get_font(22), fill=WHITE)

        # Rate badge
        draw_rounded_rect(draw, (620, ry + 8, 790, ry + 42), 14, fill=badge_color)
        bbox = draw.textbbox((0, 0), rate, font=get_font(20, bold=True))
        tw = bbox[2] - bbox[0]
        draw.text((620 + (170 - tw) // 2, ry + 13), rate, font=get_font(20, bold=True), fill=WHITE)

        # Up arrow
        draw_arrow_up(draw, 600, ry + 24, 8, badge_color)

    # === BOTTOM INSIGHT BOX ===
    box_y = table_y + 55 + 6 * 54 + 10
    draw_rounded_rect(draw, (60, box_y, W - 60, box_y + 80), 16,
                      fill=(255, 215, 0, 15), outline=GOLD, width=2)
    # Lightbulb icon drawn manually
    lb_x, lb_y = 100, box_y + 10
    draw.ellipse([lb_x, lb_y, lb_x + 18, lb_y + 18], fill=GOLD)
    draw.rectangle([lb_x + 5, lb_y + 16, lb_x + 13, lb_y + 24], fill=GOLD)
    draw_centered_text(draw, box_y + 6, "If you don't track & budget today", get_font(26, bold=True), fill=GOLD)
    draw_centered_text(draw, box_y + 40, "inflation will eat your savings silently", get_font(24), fill=NEAR_WHITE)

    # === SOURCE & DISCLAIMER (small, transparent) ===
    draw_centered_text(draw, box_y + 88, "Based on RBI CPI data trends  •  Ranges are approximate", get_font(16), fill=(150, 140, 180))

    # === BOTTOM BAR ===
    draw_rounded_rect(draw, (0, H - 55, W, H), 0, fill=GOLD)
    draw_centered_text(draw, H - 50, "mywealthpilot.in", get_font(28, bold=True), fill=DARK)

    # === Decorative stars ===
    for sx, sy, ss in [(90, 510, 6), (W - 80, 520, 5), (W // 2 - 120, 510, 4),
                        (W // 2 + 130, 525, 5), (50, 200, 4), (W - 60, 210, 3)]:
        draw_star(draw, sx, sy, ss, (255, 255, 255, 60))

    img.save(os.path.join(OUT, "day1_inflation_cartoon.png"), quality=95)
    print(f"Day 1 post saved to: {os.path.join(OUT, 'day1_inflation_cartoon.png')}")

if __name__ == "__main__":
    generate_day1()

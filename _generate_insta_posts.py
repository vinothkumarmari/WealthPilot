"""Generate 5 Instagram posts (1080x1080) for MyWealthPilot launch."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.join(os.path.dirname(__file__), "app", "static", "insta_posts")
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1080

# Brand colors
PURPLE_DARK = (74, 0, 224)
PURPLE = (108, 92, 231)
PURPLE_LIGHT = (142, 45, 226)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
NEAR_WHITE = (240, 237, 255)
DARK_BG = (20, 10, 50)

def gradient_bg(draw, w, h, color1, color2):
    """Draw vertical gradient."""
    for y in range(h):
        r = int(color1[0] + (color2[0] - color1[0]) * y / h)
        g = int(color1[1] + (color2[1] - color1[1]) * y / h)
        b = int(color1[2] + (color2[2] - color1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

def diagonal_gradient(draw, w, h, color1, color2):
    """Draw diagonal gradient."""
    for y in range(h):
        for x in range(0, w, 2):
            t = (x / w * 0.5 + y / h * 0.5)
            r = int(color1[0] + (color2[0] - color1[0]) * t)
            g = int(color1[1] + (color2[1] - color1[1]) * t)
            b = int(color1[2] + (color2[2] - color1[2]) * t)
            draw.line([(x, y), (x + 1, y)], fill=(r, g, b))

def get_font(size, bold=False):
    """Try to load a nice font, fallback to default."""
    font_names = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    if bold:
        font_names = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]
    for f in font_names:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def draw_centered_text(draw, y, text, font, fill=WHITE, w=W):
    """Draw horizontally centered text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, y), text, font=font, fill=fill)

def draw_shield(draw, cx, cy, size, fill_color=(255, 255, 255, 230)):
    """Draw a shield shape."""
    s = size
    points = [
        (cx, cy - s),           # top
        (cx + s * 0.75, cy - s * 0.55),  # top right
        (cx + s * 0.75, cy + s * 0.1),   # mid right
        (cx, cy + s),                     # bottom
        (cx - s * 0.75, cy + s * 0.1),   # mid left
        (cx - s * 0.75, cy - s * 0.55),  # top left
    ]
    draw.polygon(points, fill=fill_color)

# ==========================================
# POST 1: Launch Announcement
# ==========================================
def post1_launch():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, PURPLE_DARK, DARK_BG)

    # Decorative circles
    draw.ellipse([W - 300, -100, W + 100, 300], fill=None, outline=(108, 92, 231, 40), width=2)
    draw.ellipse([-150, H - 350, 250, H + 50], fill=None, outline=(108, 92, 231, 40), width=2)

    # Top badge
    font_sm = get_font(28)
    font_md = get_font(40, bold=True)
    font_lg = get_font(72, bold=True)
    font_xl = get_font(100, bold=True)
    font_rupee = get_font(180, bold=True)
    font_tag = get_font(24)

    # "INTRODUCING" tag
    draw_rounded_rect(draw, (W // 2 - 140, 120, W // 2 + 140, 165), 20, fill=GOLD)
    draw_centered_text(draw, 127, "INTRODUCING", get_font(26, bold=True), fill=DARK_BG)

    # App name
    draw_centered_text(draw, 200, "Wealth", font_xl, fill=WHITE)
    draw_centered_text(draw, 300, "Pilot", font_xl, fill=GOLD)

    # Shield with rupee
    draw_shield(draw, W // 2, 530, 120, fill_color=(255, 255, 255, 50))
    draw.polygon([
        (W // 2, 410), (W // 2 + 90, 465), (W // 2 + 90, 555),
        (W // 2, 650), (W // 2 - 90, 555), (W // 2 - 90, 465)
    ], fill=(255, 255, 255, 30), outline=(255, 255, 255, 80))
    draw_centered_text(draw, 480, "₹", font_rupee, fill=GOLD)

    # Tagline
    draw_centered_text(draw, 700, "Your Personal Finance", font_md, fill=WHITE)
    draw_centered_text(draw, 755, "Co-Pilot", font_md, fill=GOLD)

    # Bottom features
    features = ["Track", "Budget", "Save", "Grow"]
    start_x = 140
    spacing = 220
    for i, feat in enumerate(features):
        x = start_x + i * spacing
        draw_rounded_rect(draw, (x - 60, 860, x + 60, 905), 20, fill=(255, 255, 255, 25), outline=(255, 255, 255, 60))
        draw_centered_text(draw, 867, feat, get_font(28, bold=True), fill=WHITE, w=x * 2)

    # Bottom bar
    draw_rounded_rect(draw, (0, H - 60, W, H), 0, fill=GOLD)
    draw_centered_text(draw, H - 55, "mywealthpilot.in", get_font(30, bold=True), fill=DARK_BG)

    img.save(os.path.join(OUT, "post1_launch.png"), quality=95)
    print("Post 1: Launch announcement created")

# ==========================================
# POST 2: Problem Post — "Where does your ₹ go?"
# ==========================================
def post2_problem():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, (30, 15, 60), PURPLE_DARK)

    font_lg = get_font(68, bold=True)
    font_md = get_font(38, bold=True)
    font_sm = get_font(30)
    font_emoji = get_font(80)

    # Big question
    draw_centered_text(draw, 100, "🤔", font_emoji)
    draw_centered_text(draw, 220, "Where does", font_lg, fill=WHITE)
    draw_centered_text(draw, 300, "your ₹ go?", font_lg, fill=GOLD)

    # Stats boxes
    stats = [
        ("72%", "Indians don't track\ntheir expenses"),
        ("₹15K", "Average monthly\nspending wasted"),
        ("3 out of 5", "Have no monthly\nbudget plan"),
    ]
    y_start = 440
    for i, (num, desc) in enumerate(stats):
        y = y_start + i * 155
        draw_rounded_rect(draw, (100, y, W - 100, y + 135), 16, fill=(255, 255, 255, 15), outline=(108, 92, 231, 100), width=2)
        draw.text((150, y + 20), num, font=get_font(46, bold=True), fill=GOLD)
        lines = desc.split('\n')
        for j, line in enumerate(lines):
            draw.text((420, y + 20 + j * 35), line, font=get_font(28), fill=NEAR_WHITE)

    # Bottom CTA
    draw_rounded_rect(draw, (W // 2 - 220, 920, W // 2 + 220, 980), 30, fill=GOLD)
    draw_centered_text(draw, 932, "Start Tracking Free →", get_font(32, bold=True), fill=DARK_BG)

    draw_centered_text(draw, H - 45, "mywealthpilot.in", get_font(24), fill=(180, 170, 210))

    img.save(os.path.join(OUT, "post2_problem.png"), quality=95)
    print("Post 2: Problem post created")

# ==========================================
# POST 3: Feature Showcase — Core Features
# ==========================================
def post3_features():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, PURPLE_DARK, (20, 5, 55))

    font_lg = get_font(56, bold=True)
    font_md = get_font(32, bold=True)
    font_sm = get_font(26)

    # Header
    draw_centered_text(draw, 60, "Everything you need", font_lg, fill=WHITE)
    draw_centered_text(draw, 130, "in ONE app", font_lg, fill=GOLD)

    # Feature cards (2x3 grid)
    features = [
        ("💰", "Expense\nTracker", "Track every ₹"),
        ("📊", "Smart\nBudgets", "Plan monthly"),
        ("📈", "Price\nTracker", "Compare prices"),
        ("🏦", "Investment\nTracker", "Grow wealth"),
        ("📋", "Tax Guide\n& ITR", "File smarter"),
        ("🛡️", "Secure\n& Private", "Your data, safe"),
    ]

    cols, rows = 2, 3
    card_w, card_h = 410, 200
    gap_x, gap_y = 40, 30
    start_x = (W - cols * card_w - (cols - 1) * gap_x) // 2
    start_y = 230

    for i, (emoji, title, sub) in enumerate(features):
        col = i % cols
        row = i // cols
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)

        draw_rounded_rect(draw, (x, y, x + card_w, y + card_h), 16,
                          fill=(255, 255, 255, 12), outline=(108, 92, 231, 80), width=2)

        draw.text((x + 25, y + 25), emoji, font=get_font(44))
        lines = title.split('\n')
        for j, line in enumerate(lines):
            draw.text((x + 85, y + 20 + j * 34), line, font=get_font(30, bold=True), fill=WHITE)
        draw.text((x + 85, y + card_h - 55), sub, font=get_font(24), fill=(200, 195, 230))

    # Bottom
    draw_rounded_rect(draw, (0, H - 80, W, H), 0, fill=GOLD)
    draw_centered_text(draw, H - 72, "🆓 100% Free to Start  ·  mywealthpilot.in", get_font(30, bold=True), fill=DARK_BG)

    img.save(os.path.join(OUT, "post3_features.png"), quality=95)
    print("Post 3: Feature showcase created")

# ==========================================
# POST 4: Made in India + Trust
# ==========================================
def post4_india():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)

    # Saffron-white-green subtle gradient with purple overlay
    for y in range(H):
        if y < H // 3:
            t = y / (H // 3)
            r = int(255 - t * (255 - 74))
            g = int(153 - t * (153 - 0))
            b = int(51 - t * (51 - 224))
        elif y < 2 * H // 3:
            r, g, b = 74, 0, 224
        else:
            t = (y - 2 * H // 3) / (H // 3)
            r = int(74 + t * (19 - 74))
            g = int(0 + t * (136 - 0))
            b = int(224 + t * (8 - 224))
        # Blend with dark purple
        r = int(r * 0.3 + 20 * 0.7)
        g = int(g * 0.3 + 10 * 0.7)
        b = int(b * 0.3 + 50 * 0.7)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    font_lg = get_font(64, bold=True)
    font_md = get_font(36, bold=True)
    font_sm = get_font(28)

    # Flag emoji + text
    draw_centered_text(draw, 100, "🇮🇳", get_font(100))
    draw_centered_text(draw, 240, "Proudly Made", font_lg, fill=WHITE)
    draw_centered_text(draw, 320, "in India", font_lg, fill=GOLD)

    # Trust points
    points = [
        "🔒  Your data stays on secure servers",
        "🆓  Free — no hidden charges",
        "📱  Works on any device, any browser",
        "🌐  Available in Tamil, Hindi, Telugu",
        "⚡  No app install needed — just open & use",
        "💳  Razorpay-secured payments",
    ]

    y = 450
    for point in points:
        draw_rounded_rect(draw, (120, y, W - 120, y + 60), 12,
                          fill=(255, 255, 255, 10))
        draw.text((150, y + 12), point, font=get_font(28), fill=NEAR_WHITE)
        y += 75

    # Bottom
    draw_rounded_rect(draw, (W // 2 - 200, 940, W // 2 + 200, 995), 30, fill=GOLD)
    draw_centered_text(draw, 952, "Try It Free Today", get_font(32, bold=True), fill=DARK_BG)
    draw_centered_text(draw, H - 40, "mywealthpilot.in", get_font(22), fill=(180, 170, 210))

    img.save(os.path.join(OUT, "post4_india.png"), quality=95)
    print("Post 4: Made in India created")

# ==========================================
# POST 5: CTA — "Your first step"
# ==========================================
def post5_cta():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, DARK_BG, PURPLE_DARK)

    font_xl = get_font(72, bold=True)
    font_lg = get_font(50, bold=True)
    font_md = get_font(34, bold=True)
    font_sm = get_font(28)

    # Top
    draw_centered_text(draw, 80, "Your wealth", font_xl, fill=WHITE)
    draw_centered_text(draw, 165, "journey starts", font_xl, fill=WHITE)
    draw_centered_text(draw, 250, "with one step", font_xl, fill=GOLD)

    # Steps
    steps = [
        ("1", "Sign Up Free", "30 seconds, no credit card"),
        ("2", "Add Your First Expense", "Track where ₹ goes"),
        ("3", "Set a Budget", "Plan your monthly spending"),
        ("4", "Watch Your Wealth Grow", "Insights & reports in real-time"),
    ]

    y = 390
    for num, title, sub in steps:
        # Number circle
        cx = 160
        draw.ellipse([cx - 28, y - 2, cx + 28, y + 54], fill=GOLD)
        draw_centered_text(draw, y + 5, num, get_font(32, bold=True), fill=DARK_BG, w=cx * 2)

        # Text
        draw.text((220, y), title, font=get_font(34, bold=True), fill=WHITE)
        draw.text((220, y + 42), sub, font=get_font(24), fill=(180, 175, 210))

        # Connector line
        if num != "4":
            draw.line([(cx, y + 56), (cx, y + 105)], fill=(108, 92, 231, 60), width=2)

        y += 120

    # Big CTA button
    draw_rounded_rect(draw, (180, 900, W - 180, 975), 40, fill=GOLD)
    draw_centered_text(draw, 918, "Start Free Now →", get_font(38, bold=True), fill=DARK_BG)

    draw_centered_text(draw, H - 40, "mywealthpilot.in", get_font(24), fill=(180, 170, 210))

    img.save(os.path.join(OUT, "post5_cta.png"), quality=95)
    print("Post 5: CTA post created")

# Generate all
if __name__ == "__main__":
    post1_launch()
    post2_problem()
    post3_features()
    post4_india()
    post5_cta()
    print(f"\nAll 5 posts saved to: {OUT}")

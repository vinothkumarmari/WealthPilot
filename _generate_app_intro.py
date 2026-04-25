"""MyWealthPilot App Intro Post — Instagram (1080x1080)."""
from PIL import Image, ImageDraw, ImageFont
import os, math

OUT = os.path.join(os.path.dirname(__file__), "app", "static", "insta_posts")
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1080

PURPLE_DARK = (74, 0, 224)
PURPLE = (108, 92, 231)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
NEAR_WHITE = (245, 242, 255)
DARK = (18, 8, 42)
GREEN = (46, 204, 113)
LIGHT_PURPLE = (200, 190, 240)

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

def draw_shield_logo(draw, cx, cy, size):
    """Draw the MyWealthPilot shield logo."""
    s = size
    # Shield
    draw.polygon([
        (cx, cy - s), (cx + s * 0.75, cy - s * 0.55),
        (cx + s * 0.75, cy + s * 0.1), (cx, cy + s),
        (cx - s * 0.75, cy + s * 0.1), (cx - s * 0.75, cy - s * 0.55)
    ], fill=(255, 255, 255, 40), outline=(255, 255, 255, 100))
    # Rupee inside
    f = get_font(int(s * 1.1), bold=True)
    bbox = draw.textbbox((0, 0), "₹", font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - int(s * 0.15)), "₹", font=f, fill=GOLD)

def draw_compass_ring(draw, cx, cy, r):
    """Subtle compass ring with ticks."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=None,
                 outline=(255, 255, 255, 20), width=2)
    draw.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], fill=None,
                 outline=(255, 255, 255, 12), width=1)
    # Ticks
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        x1 = cx + int((r - 5) * math.cos(rad))
        y1 = cy + int((r - 5) * math.sin(rad))
        x2 = cx + int((r + 5) * math.cos(rad))
        y2 = cy + int((r + 5) * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 40), width=2)

def draw_feature_card(draw, x, y, w, h, icon_func, title, subtitle):
    """Draw a feature card with icon, title, subtitle."""
    draw_rounded_rect(draw, (x, y, x + w, y + h), 14,
                      fill=(30, 15, 60), outline=(108, 92, 231), width=1)
    icon_func(draw, x + 20, y + 20)
    draw.text((x + 55, y + 10), title, font=get_font(22, bold=True), fill=WHITE)
    draw.text((x + 55, y + 38), subtitle, font=get_font(17), fill=LIGHT_PURPLE)

# Feature icon drawers
def icon_expense(draw, x, y):
    """Coin stack icon."""
    for i in range(3):
        oy = y + i * 6
        draw.ellipse([x, oy, x + 24, oy + 10], fill=GOLD, outline=(200, 170, 0))

def icon_budget(draw, x, y):
    """Bar chart icon."""
    draw.rectangle([x, y + 14, x + 7, y + 24], fill=GREEN)
    draw.rectangle([x + 9, y + 6, x + 16, y + 24], fill=(52, 152, 219))
    draw.rectangle([x + 18, y, x + 25, y + 24], fill=PURPLE)

def icon_price(draw, x, y):
    """Tag icon."""
    draw.rounded_rectangle([x, y + 2, x + 24, y + 22], radius=4, fill=(243, 156, 18))
    draw.ellipse([x + 3, y + 6, x + 9, y + 12], fill=WHITE)

def icon_tax(draw, x, y):
    """Document icon."""
    draw.rounded_rectangle([x + 2, y, x + 22, y + 24], radius=3, fill=(52, 152, 219))
    draw.line([(x + 7, y + 8), (x + 18, y + 8)], fill=WHITE, width=1)
    draw.line([(x + 7, y + 13), (x + 18, y + 13)], fill=WHITE, width=1)
    draw.line([(x + 7, y + 18), (x + 15, y + 18)], fill=WHITE, width=1)

def icon_report(draw, x, y):
    """Line chart icon."""
    draw.line([(x, y + 20), (x + 8, y + 10), (x + 16, y + 16), (x + 24, y + 2)],
              fill=GREEN, width=2)
    draw.ellipse([x + 22, y, x + 26, y + 5], fill=GREEN)

def icon_language(draw, x, y):
    """Globe icon."""
    draw.ellipse([x, y, x + 24, y + 24], fill=None, outline=(155, 89, 182), width=2)
    draw.line([(x + 12, y), (x + 12, y + 24)], fill=(155, 89, 182), width=1)
    draw.line([(x, y + 12), (x + 24, y + 12)], fill=(155, 89, 182), width=1)
    draw.arc([x - 4, y, x + 16, y + 24], 270, 90, fill=(155, 89, 182), width=1)


def generate_intro():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)

    # Background gradient
    gradient_bg(draw, W, H, PURPLE_DARK, DARK)

    # Decorative elements
    draw_compass_ring(draw, W // 2, 240, 140)
    draw_compass_ring(draw, W // 2, 240, 110)

    # Decorative corner glows
    for cx, cy, cr in [(0, 0, 200), (W, H, 250), (W, 0, 150)]:
        for g in range(cr, 0, -4):
            draw.ellipse([cx - g, cy - g, cx + g, cy + g], fill=(108, 92, 231, 3))

    # === TOP: "Meet" badge ===
    draw_rounded_rect(draw, (W // 2 - 80, 50, W // 2 + 80, 88), 20, fill=GOLD)
    draw_centered_text(draw, 57, "MEET", get_font(24, bold=True), fill=DARK)

    # === LOGO ===
    draw_shield_logo(draw, W // 2, 230, 80)

    # === APP NAME ===
    draw_centered_text(draw, 340, "myWealth", get_font(72, bold=True), fill=WHITE)
    draw_centered_text(draw, 415, "Pilot", get_font(72, bold=True), fill=GOLD)

    # === TAGLINE ===
    draw_centered_text(draw, 505, "Your Personal Finance Co-Pilot", get_font(28), fill=LIGHT_PURPLE)

    # === DIVIDER ===
    draw.line([(W // 2 - 100, 555), (W // 2 + 100, 555)], fill=GOLD, width=2)

    # === FEATURE CARDS (2 columns x 3 rows) ===
    card_w = 440
    card_h = 65
    gap_x = 30
    gap_y = 15
    start_x = (W - 2 * card_w - gap_x) // 2
    start_y = 580

    features = [
        (icon_expense, "Expense Tracker", "Track every rupee"),
        (icon_budget, "Smart Budgets", "Plan monthly spending"),
        (icon_price, "Price Tracker", "Compare across platforms"),
        (icon_tax, "Tax & ITR Guide", "File smarter"),
        (icon_report, "Reports & Insights", "Know your money flow"),
        (icon_language, "Multi-Language", "Tamil, Hindi, Telugu"),
    ]

    for i, (icon_fn, title, sub) in enumerate(features):
        col = i % 2
        row = i // 2
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        draw_feature_card(draw, x, y, card_w, card_h, icon_fn, title, sub)

    # === FREE BADGE ===
    badge_y = start_y + 3 * (card_h + gap_y) + 10
    draw_rounded_rect(draw, (W // 2 - 220, badge_y, W // 2 + 220, badge_y + 50), 25,
                      fill=(30, 60, 40), outline=GREEN, width=2)
    draw_centered_text(draw, badge_y + 10, "100% Free to Start  |  No Hidden Charges",
                       get_font(22, bold=True), fill=GREEN)

    # === MADE IN INDIA ===
    india_y = badge_y + 65
    draw_centered_text(draw, india_y, "Made in India  |  Works on Any Device",
                       get_font(22), fill=LIGHT_PURPLE)

    # === BOTTOM BAR ===
    draw_rounded_rect(draw, (0, H - 55, W, H), 0, fill=GOLD)
    draw_centered_text(draw, H - 50, "mywealthpilot.in", get_font(28, bold=True), fill=DARK)

    img.save(os.path.join(OUT, "app_intro.png"), quality=95)
    print(f"App intro post saved to: {os.path.join(OUT, 'app_intro.png')}")

if __name__ == "__main__":
    generate_intro()

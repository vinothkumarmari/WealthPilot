"""
MyWealthPilot - Promotional Video Generator
Generates an MP4 ad video for social media (1080x1920 portrait / 1080x1080 square)
"""

from moviepy import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import math

# --- Config ---
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "mywealthpilot_ad.mp4")
WIDTH, HEIGHT = 1080, 1920  # Instagram Story / Reel format
FPS = 30
DURATION_PER_SLIDE = 4  # seconds

# Colors
BG_DARK = (26, 26, 46)       # #1a1a2e
ACCENT = (108, 92, 231)      # #6C5CE7
ACCENT_LIGHT = (162, 155, 254)  # #A29BFE
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
GREEN = (46, 213, 115)
LIGHT_BG = (240, 242, 245)

def get_font(size, bold=False):
    """Get a font - tries system fonts"""
    font_names = [
        "C:/Windows/Fonts/segoeui.ttf" if not bold else "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arial.ttf" if not bold else "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibri.ttf" if not bold else "C:/Windows/Fonts/calibrib.ttf",
    ]
    for fn in font_names:
        if os.path.exists(fn):
            return ImageFont.truetype(fn, size)
    return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)

def draw_gradient_bg(draw, width, height, color1, color2):
    for y in range(height):
        ratio = y / height
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

def draw_centered_text(draw, y, text, font, fill=WHITE):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (WIDTH - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)

def draw_icon_circle(draw, cx, cy, radius, color):
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)

def create_slide_intro():
    """Slide 1: Brand intro"""
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, WIDTH, HEIGHT, (20, 20, 50), BG_DARK)

    # Decorative circles
    draw.ellipse([WIDTH - 200, -100, WIDTH + 100, 200], fill=(108, 92, 231, 40), outline=None)
    draw.ellipse([-100, HEIGHT - 300, 200, HEIGHT - 100], fill=(108, 92, 231, 40))

    # Wallet icon circle
    draw_icon_circle(draw, WIDTH // 2, 600, 80, ACCENT)
    font_icon = get_font(60, bold=True)
    draw_centered_text(draw, 580, "W", font_icon, WHITE)

    # Brand name
    font_brand = get_font(72, bold=True)
    font_brand_accent = get_font(72, bold=True)
    bbox1 = draw.textbbox((0, 0), "Wealth", font=font_brand)
    bbox2 = draw.textbbox((0, 0), "Pilot", font=font_brand_accent)
    tw = (bbox1[2] - bbox1[0]) + (bbox2[2] - bbox2[0])
    x = (WIDTH - tw) // 2
    draw.text((x, 750), "Wealth", font=font_brand, fill=WHITE)
    draw.text((x + bbox1[2] - bbox1[0], 750), "Pilot", font=font_brand_accent, fill=ACCENT_LIGHT)

    # Tagline
    font_tag = get_font(32)
    draw_centered_text(draw, 850, "Your Personal Finance Co-Pilot", font_tag, ACCENT_LIGHT)

    # Subtitle
    font_sub = get_font(36, bold=True)
    draw_centered_text(draw, 1000, "All-in-One Finance Manager", font_sub, WHITE)
    font_sub2 = get_font(30)
    draw_centered_text(draw, 1060, "Built for India", font_sub2, GOLD)

    # URL
    font_url = get_font(34, bold=True)
    draw_rounded_rect(draw, (WIDTH // 2 - 220, 1200, WIDTH // 2 + 220, 1270), 35, ACCENT)
    draw_centered_text(draw, 1215, "mywealthpilot.in", font_url, WHITE)

    return np.array(img)

def create_slide_problem():
    """Slide 2: Problem statement"""
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, WIDTH, HEIGHT, BG_DARK, (15, 15, 35))

    font_big = get_font(52, bold=True)
    font_med = get_font(36)

    draw_centered_text(draw, 400, "Where does your", font_big, WHITE)
    draw_centered_text(draw, 470, "money go every month?", font_big, WHITE)

    # Emoji-style items
    items = [
        "📒  Spreadsheets?",
        "📱  Notes app?",
        "🤷  Guesswork?",
        "😰  No idea?",
    ]
    font_item = get_font(38)
    y = 650
    for item in items:
        draw_centered_text(draw, y, item, font_item, (200, 200, 220))
        y += 80

    font_cta = get_font(44, bold=True)
    draw_centered_text(draw, 1100, "There's a better way.", font_cta, ACCENT_LIGHT)

    return np.array(img)

def create_slide_features1():
    """Slide 3: Core features"""
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, WIDTH, HEIGHT, (15, 15, 35), BG_DARK)

    font_title = get_font(46, bold=True)
    draw_centered_text(draw, 250, "Everything You Need", font_title, WHITE)

    features = [
        ("💵", "Income & Expense Tracking"),
        ("📊", "SIP & Investment Monitor"),
        ("🏆", "Live Gold & Silver Rates"),
        ("🎯", "Financial Goals & Budget"),
        ("🏥", "Insurance & Policy Manager"),
        ("🏦", "Loan & EMI Tracker"),
        ("🧮", "Financial Calculators"),
        ("🤖", "AI-Powered Suggestions"),
    ]

    font_feat = get_font(30)
    font_emoji = get_font(34)
    y = 420
    for emoji, text in features:
        # Feature card background
        draw_rounded_rect(draw, (80, y - 10, WIDTH - 80, y + 65), 12, (40, 40, 70))
        draw.text((110, y + 8), emoji, font=font_emoji, fill=WHITE)
        draw.text((170, y + 12), text, font=font_feat, fill=WHITE)
        y += 95

    return np.array(img)

def create_slide_features2():
    """Slide 4: Premium features"""
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, WIDTH, HEIGHT, BG_DARK, (20, 15, 45))

    font_title = get_font(46, bold=True)
    draw_centered_text(draw, 250, "Premium Features", font_title, GOLD)

    features = [
        ("👨‍👩‍👧", "Family Finance Dashboard"),
        ("📈", "Custom Reports & Analytics"),
        ("🏛️", "Govt Schemes & Budget Info"),
        ("📋", "Tax Planning & ITR Guide"),
        ("🔮", "Future Planner 2040+"),
        ("💡", "AI Playbooks"),
        ("🛡️", "Insurance Analyzer"),
        ("👴", "Retirement Planner"),
    ]

    font_feat = get_font(30)
    font_emoji = get_font(34)
    y = 420
    for emoji, text in features:
        draw_rounded_rect(draw, (80, y - 10, WIDTH - 80, y + 65), 12, (50, 40, 80))
        draw.text((110, y + 8), emoji, font=font_emoji, fill=WHITE)
        draw.text((170, y + 12), text, font=font_feat, fill=WHITE)
        y += 95

    return np.array(img)

def create_slide_pricing():
    """Slide 5: Pricing"""
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, WIDTH, HEIGHT, (15, 15, 35), BG_DARK)

    font_title = get_font(48, bold=True)
    draw_centered_text(draw, 300, "Simple Pricing", font_title, WHITE)

    # Free plan
    draw_rounded_rect(draw, (100, 480, WIDTH - 100, 700), 20, (40, 40, 70))
    font_plan = get_font(36, bold=True)
    font_price = get_font(56, bold=True)
    font_desc = get_font(26)
    draw_centered_text(draw, 500, "FREE", font_plan, GREEN)
    draw_centered_text(draw, 555, "₹0", font_price, GREEN)
    draw_centered_text(draw, 635, "Core features • No credit card", font_desc, (180, 180, 200))

    # Pro plan
    draw_rounded_rect(draw, (100, 750, WIDTH - 100, 980), 20, ACCENT)
    draw_centered_text(draw, 770, "PRO", font_plan, WHITE)
    draw_centered_text(draw, 825, "₹99/month", font_price, WHITE)
    draw_centered_text(draw, 910, "All features • Priority support", font_desc, (220, 220, 240))

    # Family plan
    draw_rounded_rect(draw, (100, 1030, WIDTH - 100, 1260), 20, (80, 60, 180))
    draw_centered_text(draw, 1050, "FAMILY", font_plan, GOLD)
    draw_centered_text(draw, 1105, "₹199/month", font_price, GOLD)
    draw_centered_text(draw, 1190, "Everything + Family dashboard", font_desc, (220, 220, 240))

    return np.array(img)

def create_slide_languages():
    """Slide 6: Languages & platforms"""
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, WIDTH, HEIGHT, BG_DARK, (20, 20, 50))

    font_title = get_font(46, bold=True)
    draw_centered_text(draw, 350, "Available in 4 Languages", font_title, WHITE)

    langs = ["English", "தமிழ்", "हिन्दी", "తెలుగు"]
    font_lang = get_font(44, bold=True)
    y = 550
    for lang in langs:
        draw_rounded_rect(draw, (200, y - 5, WIDTH - 200, y + 65), 15, (50, 45, 85))
        draw_centered_text(draw, y + 5, lang, font_lang, WHITE)
        y += 100

    font_feat = get_font(32)
    y = 1050
    extras = ["🌙  Dark Mode", "📱  Mobile Friendly", "🔒  Secure & Private"]
    for text in extras:
        draw_centered_text(draw, y, text, font_feat, ACCENT_LIGHT)
        y += 70

    return np.array(img)

def create_slide_cta():
    """Slide 7: Call to action"""
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, WIDTH, HEIGHT, (20, 15, 50), BG_DARK)

    # Decorative
    draw.ellipse([WIDTH // 2 - 250, 200, WIDTH // 2 + 250, 700], fill=(108, 92, 231, 30))

    font_big = get_font(56, bold=True)
    font_med = get_font(40, bold=True)
    font_url = get_font(42, bold=True)

    draw_centered_text(draw, 500, "Start Your", font_big, WHITE)
    draw_centered_text(draw, 580, "Financial Journey", font_big, WHITE)
    draw_centered_text(draw, 660, "Today", font_big, ACCENT_LIGHT)

    draw_centered_text(draw, 820, "FREE to Start", font_med, GREEN)
    draw_centered_text(draw, 880, "No Credit Card Required", get_font(30), (180, 180, 200))

    # CTA button
    draw_rounded_rect(draw, (WIDTH // 2 - 280, 1000, WIDTH // 2 + 280, 1090), 45, ACCENT)
    draw_centered_text(draw, 1020, "mywealthpilot.in", font_url, WHITE)

    # Made in India
    font_small = get_font(30)
    draw_centered_text(draw, 1180, "Made in India 🇮🇳", font_small, GOLD)

    # Brand
    font_brand = get_font(36, bold=True)
    draw_centered_text(draw, 1350, "MyWealthPilot", font_brand, ACCENT_LIGHT)

    return np.array(img)

def add_fade_transition(clip, fade_duration=0.5):
    """Add fade in and fade out to a clip"""
    return clip.with_effects([
        vfx.FadeIn(fade_duration),
        vfx.FadeOut(fade_duration),
    ])

def generate_video():
    print("🎬 Generating MyWealthPilot promo video...")

    slides = [
        ("Intro", create_slide_intro),
        ("Problem", create_slide_problem),
        ("Features 1", create_slide_features1),
        ("Features 2", create_slide_features2),
        ("Pricing", create_slide_pricing),
        ("Languages", create_slide_languages),
        ("CTA", create_slide_cta),
    ]

    clips = []
    for i, (name, slide_func) in enumerate(slides):
        print(f"  Creating slide {i + 1}/{len(slides)}: {name}")
        frame = slide_func()
        clip = ImageClip(frame, duration=DURATION_PER_SLIDE)
        clip = add_fade_transition(clip, 0.5)
        clips.append(clip)

    print("  Compositing video...")
    final = concatenate_videoclips(clips, method="compose")

    print(f"  Writing {OUTPUT_FILE}...")
    final.write_videofile(
        OUTPUT_FILE,
        fps=FPS,
        codec='libx264',
        audio=False,
        preset='medium',
        threads=4,
    )

    final.close()
    for c in clips:
        c.close()

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"\n✅ Video saved: {OUTPUT_FILE}")
    print(f"📐 Resolution: {WIDTH}x{HEIGHT}")
    print(f"⏱️  Duration: {len(slides) * DURATION_PER_SLIDE}s")
    print(f"📦 Size: {size_mb:.1f} MB")

if __name__ == '__main__':
    generate_video()

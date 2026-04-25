"""Generate 5 Pre-Launch Instagram Posts (1080x1080) — Financial Awareness & Motivation."""
from PIL import Image, ImageDraw, ImageFont
import os, math

OUT = os.path.join(os.path.dirname(__file__), "app", "static", "insta_posts")
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1080

# Brand colors
PURPLE_DARK = (74, 0, 224)
PURPLE = (108, 92, 231)
PURPLE_LIGHT = (142, 45, 226)
GOLD = (255, 215, 0)
GOLD_DARK = (255, 165, 0)
WHITE = (255, 255, 255)
NEAR_WHITE = (240, 237, 255)
DARK_BG = (20, 10, 50)
RED = (231, 76, 60)
RED_DARK = (192, 57, 43)
GREEN = (46, 204, 113)
GREEN_DARK = (39, 174, 96)
ORANGE = (243, 156, 18)
LIGHT_PURPLE = (200, 190, 240)

def gradient_bg(draw, w, h, c1, c2):
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

def get_font(size, bold=False):
    paths_bold = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]
    paths_reg = ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    for f in (paths_bold if bold else paths_reg):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def draw_centered_text(draw, y, text, font, fill=WHITE, w=W):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, y), text, font=font, fill=fill)

def draw_bar(draw, x, y, bar_w, bar_h, fill_color, label_top, label_bottom, font_val, font_label):
    """Draw a vertical bar with labels."""
    draw.rounded_rectangle([x, y, x + bar_w, y + bar_h], radius=8, fill=fill_color)
    # Value on top
    bbox = draw.textbbox((0, 0), label_top, font=font_val)
    tw = bbox[2] - bbox[0]
    draw.text((x + (bar_w - tw) // 2, y - 40), label_top, font=font_val, fill=fill_color)
    # Label below
    bbox2 = draw.textbbox((0, 0), label_bottom, font=font_label)
    tw2 = bbox2[2] - bbox2[0]
    draw.text((x + (bar_w - tw2) // 2, y + bar_h + 10), label_bottom, font=font_label, fill=LIGHT_PURPLE)

def draw_rising_arrow(draw, x, y, size, color):
    """Draw an upward arrow indicating rise."""
    draw.polygon([
        (x, y - size),
        (x + size * 0.6, y),
        (x + size * 0.2, y),
        (x + size * 0.2, y + size),
        (x - size * 0.2, y + size),
        (x - size * 0.2, y),
        (x - size * 0.6, y),
    ], fill=color)


# ==========================================
# POST 1: INFLATION REALITY — "₹100 in 2015 vs 2026"
# ==========================================
def post1_inflation():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, (40, 10, 20), (20, 5, 40))

    # Red warning accent at top
    for y in range(6):
        draw.line([(0, y), (W, y)], fill=RED)

    f_xl = get_font(60, bold=True)
    f_lg = get_font(48, bold=True)
    f_md = get_font(34, bold=True)
    f_sm = get_font(26)
    f_val = get_font(38, bold=True)
    f_label = get_font(22)

    # Header
    draw_centered_text(draw, 40, "⚠️  INFLATION REALITY", f_xl, fill=RED)
    draw_centered_text(draw, 120, "What ₹100 could buy in 2015", f_md, fill=WHITE)
    draw_centered_text(draw, 165, "vs what it buys in 2026", f_md, fill=GOLD)

    # Price comparison cards
    items = [
        ("🍚 Rice (1kg)", "₹32", "₹58", "+81%"),
        ("🥛 Milk (1L)", "₹42", "₹72", "+71%"),
        ("⛽ Petrol (1L)", "₹63", "₹105", "+67%"),
        ("🏠 Rent (avg)", "₹8K", "₹16K", "+100%"),
        ("🎓 School Fee", "₹30K", "₹75K", "+150%"),
        ("🏥 Health Ins.", "₹5K", "₹14K", "+180%"),
    ]

    y_start = 240
    card_h = 100
    gap = 15

    for i, (item, old_p, new_p, pct) in enumerate(items):
        y = y_start + i * (card_h + gap)
        # Card background
        draw_rounded_rect(draw, (60, y, W - 60, y + card_h), 14,
                          fill=(255, 255, 255, 8), outline=(231, 76, 60, 60), width=1)

        # Item name
        draw.text((90, y + 12), item, font=get_font(28, bold=True), fill=WHITE)

        # Old price
        draw.text((90, y + 52), old_p, font=get_font(26), fill=(150, 150, 150))

        # Arrow
        draw.text((340, y + 45), "→", font=get_font(30, bold=True), fill=ORANGE)

        # New price
        draw.text((400, y + 50), new_p, font=get_font(28, bold=True), fill=WHITE)

        # Percentage badge
        pct_color = RED
        draw_rounded_rect(draw, (W - 200, y + 30, W - 90, y + 72), 18, fill=RED)
        bbox = draw.textbbox((0, 0), pct, font=get_font(24, bold=True))
        tw = bbox[2] - bbox[0]
        draw.text((W - 200 + (110 - tw) // 2, y + 37), pct, font=get_font(24, bold=True), fill=WHITE)

    # Bottom message
    y_bot = y_start + 6 * (card_h + gap) + 10
    draw_rounded_rect(draw, (60, y_bot, W - 60, y_bot + 75), 14, fill=(255, 215, 0, 20), outline=GOLD, width=2)
    draw_centered_text(draw, y_bot + 8, "Your salary grew 30%.", get_font(28, bold=True), fill=GOLD)
    draw_centered_text(draw, y_bot + 42, "Prices grew 80-180%. Are you tracking this?", get_font(22), fill=NEAR_WHITE)

    # Bottom bar
    draw_rounded_rect(draw, (0, H - 50, W, H), 0, fill=(40, 10, 20))
    draw_centered_text(draw, H - 44, "Follow for more financial insights  •  @mywealthpilot.in", get_font(22), fill=LIGHT_PURPLE)

    img.save(os.path.join(OUT, "pre1_inflation.png"), quality=95)
    print("Pre-Post 1: Inflation Reality created")


# ==========================================
# POST 2: SALARY vs EXPENSES — "The Gap Nobody Talks About"
# ==========================================
def post2_salary_gap():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, DARK_BG, (15, 5, 45))

    f_xl = get_font(54, bold=True)
    f_lg = get_font(42, bold=True)
    f_md = get_font(32, bold=True)
    f_sm = get_font(26)

    # Header
    draw_centered_text(draw, 50, "The Gap Nobody", f_xl, fill=WHITE)
    draw_centered_text(draw, 115, "Talks About 📉", f_xl, fill=RED)

    # Subtitle
    draw_centered_text(draw, 200, "Average Indian Salary vs Expenses (Monthly)", get_font(26), fill=LIGHT_PURPLE)

    # Bar chart area
    bar_base_y = 700  # bottom of bars
    bar_w = 120
    bar_max_h = 380

    # Salary bar (green) — ₹35K
    sal_h = int(bar_max_h * 0.55)
    sal_x = 200
    draw.rounded_rectangle([sal_x, bar_base_y - sal_h, sal_x + bar_w, bar_base_y], radius=10, fill=GREEN)
    draw_centered_text(draw, bar_base_y - sal_h - 50, "₹35K", get_font(36, bold=True), fill=GREEN, w=sal_x * 2 + bar_w)
    draw_centered_text(draw, bar_base_y + 15, "Salary", get_font(24, bold=True), fill=WHITE, w=sal_x * 2 + bar_w)

    # Expenses bar (red) — ₹32K
    exp_h = int(bar_max_h * 0.50)
    exp_x = 440
    draw.rounded_rectangle([exp_x, bar_base_y - exp_h, exp_x + bar_w, bar_base_y], radius=10, fill=RED)
    draw_centered_text(draw, bar_base_y - exp_h - 50, "₹32K", get_font(36, bold=True), fill=RED, w=exp_x * 2 + bar_w)
    draw_centered_text(draw, bar_base_y + 15, "Expenses", get_font(24, bold=True), fill=WHITE, w=exp_x * 2 + bar_w)

    # Savings bar (gold) — ₹3K
    sav_h = int(bar_max_h * 0.06)
    sav_x = 680
    draw.rounded_rectangle([sav_x, bar_base_y - sav_h, sav_x + bar_w, bar_base_y], radius=6, fill=GOLD)
    draw_centered_text(draw, bar_base_y - sav_h - 50, "₹3K", get_font(36, bold=True), fill=GOLD, w=sav_x * 2 + bar_w)
    draw_centered_text(draw, bar_base_y + 15, "Savings", get_font(24, bold=True), fill=WHITE, w=sav_x * 2 + bar_w)

    # Gap indicator — dotted arrow between salary and expense
    gap_y = bar_base_y - sal_h + 30
    draw_rounded_rect(draw, (sal_x + bar_w + 20, gap_y, exp_x - 20, gap_y + 40), 8, fill=(255, 255, 255, 10), outline=ORANGE, width=2)
    draw_centered_text(draw, gap_y + 5, "Only 8.5%", get_font(22, bold=True), fill=ORANGE, w=sal_x + bar_w + 20 + (exp_x - 20 - sal_x - bar_w - 20))

    # Shocking stat below chart
    draw_rounded_rect(draw, (80, 770, W - 80, 850), 14, fill=(231, 76, 60, 25), outline=RED, width=2)
    draw_centered_text(draw, 780, "91.5% of salary → GONE every month", get_font(30, bold=True), fill=RED)
    draw_centered_text(draw, 818, "Without tracking, you'll never know where", get_font(22), fill=NEAR_WHITE)

    # Bottom insight
    draw_rounded_rect(draw, (100, 880, W - 100, 960), 14, fill=(46, 204, 113, 20), outline=GREEN, width=2)
    draw_centered_text(draw, 893, "What if you saved just ₹5K more?", get_font(28, bold=True), fill=GREEN)
    draw_centered_text(draw, 928, "₹5K/month × 10 years = ₹10.5L (with 12% returns)", get_font(22), fill=NEAR_WHITE)

    # Bottom
    draw_centered_text(draw, H - 45, "Follow for more  •  @mywealthpilot.in", get_font(22), fill=LIGHT_PURPLE)

    img.save(os.path.join(OUT, "pre2_salary_gap.png"), quality=95)
    print("Pre-Post 2: Salary vs Expenses Gap created")


# ==========================================
# POST 3: WHERE YOUR ₹ ACTUALLY GOES — Pie chart breakdown
# ==========================================
def post3_spending_breakdown():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, (25, 8, 48), DARK_BG)

    f_xl = get_font(52, bold=True)
    f_md = get_font(30, bold=True)
    f_sm = get_font(26)

    # Header
    draw_centered_text(draw, 45, "Where Your ₹ Actually", f_xl, fill=WHITE)
    draw_centered_text(draw, 108, "Goes Every Month 💸", f_xl, fill=GOLD)

    # Pie chart (draw as colored arc segments)
    cx, cy, radius = W // 2, 380, 170
    segments = [
        (30, "Rent/EMI", RED, "30%"),
        (22, "Food & Grocery", ORANGE, "22%"),
        (15, "Transport", PURPLE, "15%"),
        (12, "Bills & Recharge", (52, 152, 219), "12%"),
        (10, "Shopping", PURPLE_LIGHT, "10%"),
        (5, "Entertainment", (155, 89, 182), "5%"),
        (6, "Savings", GREEN, "6%"),
    ]

    start_angle = -90
    for pct, label, color, pct_str in segments:
        end_angle = start_angle + (pct / 100) * 360
        draw.pieslice([cx - radius, cy - radius, cx + radius, cy + radius],
                      start_angle, end_angle, fill=color, outline=(15, 5, 40), width=2)
        start_angle = end_angle

    # Center circle for donut effect
    draw.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=DARK_BG)
    draw_centered_text(draw, cy - 22, "₹35K", get_font(30, bold=True), fill=GOLD)
    draw_centered_text(draw, cy + 12, "/month", get_font(18), fill=LIGHT_PURPLE)

    # Legend cards
    y_start = 590
    col1_x, col2_x = 60, W // 2 + 20

    for i, (pct, label, color, pct_str) in enumerate(segments):
        col = i % 2
        row = i // 2
        x = col1_x if col == 0 else col2_x
        y = y_start + row * 72

        # Color dot
        draw.ellipse([x, y + 8, x + 24, y + 32], fill=color)
        # Label
        draw.text((x + 35, y + 4), label, font=get_font(24, bold=True), fill=WHITE)
        # Percentage
        draw.text((x + 35, y + 32), pct_str, font=get_font(20), fill=LIGHT_PURPLE)

    # Shock stat
    draw_rounded_rect(draw, (80, 870, W - 80, 950), 14, fill=(231, 76, 60, 20), outline=RED, width=2)
    draw_centered_text(draw, 880, "Only 6% goes to Savings 😱", get_font(32, bold=True), fill=RED)
    draw_centered_text(draw, 920, "94% of your hard-earned money disappears", get_font(22), fill=NEAR_WHITE)

    # Bottom
    draw_rounded_rect(draw, (80, 970, W - 80, 1025), 14, fill=(255, 215, 0, 15))
    draw_centered_text(draw, 980, "Track every ₹ — Know exactly where it goes", get_font(26, bold=True), fill=GOLD)
    draw_centered_text(draw, H - 40, "@mywealthpilot.in", get_font(22), fill=LIGHT_PURPLE)

    img.save(os.path.join(OUT, "pre3_spending.png"), quality=95)
    print("Pre-Post 3: Spending Breakdown created")


# ==========================================
# POST 4: COST OF NOT SAVING — "₹500/day = ₹1.8 Crore"
# ==========================================
def post4_cost_of_not_saving():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, (10, 15, 40), (30, 5, 55))

    f_xl = get_font(54, bold=True)
    f_lg = get_font(44, bold=True)
    f_md = get_font(32, bold=True)
    f_sm = get_font(26)

    # Header
    draw_centered_text(draw, 50, "What If You Saved", f_xl, fill=WHITE)
    draw_centered_text(draw, 115, "Just ₹500/Day? 🤔", f_xl, fill=GOLD)

    # Subtitle
    draw_centered_text(draw, 195, "₹500 = one chai + snack you skip daily", get_font(26), fill=LIGHT_PURPLE)

    # Timeline cards
    timeline = [
        ("1 Month", "₹15,000", "Saved", GREEN),
        ("1 Year", "₹1,82,500", "Saved", GREEN),
        ("5 Years", "₹12.4 Lakh", "@ 12% returns", GOLD),
        ("10 Years", "₹34.8 Lakh", "@ 12% returns", GOLD),
        ("20 Years", "₹1.5 Crore", "@ 12% returns", GOLD),
        ("25 Years", "₹2.67 Crore", "@ 12% returns", (255, 215, 0)),
    ]

    y = 260
    for i, (period, amount, note, color) in enumerate(timeline):
        # Card
        card_fill = (255, 255, 255, 8) if i < 4 else (255, 215, 0, 20)
        card_outline = color if i >= 4 else (108, 92, 231, 60)
        draw_rounded_rect(draw, (100, y, W - 100, y + 90), 14,
                          fill=card_fill, outline=card_outline, width=2 if i >= 4 else 1)

        # Timeline dot + line
        dot_cx = 145
        draw.ellipse([dot_cx - 10, y + 32, dot_cx + 10, y + 52], fill=color)
        if i < len(timeline) - 1:
            draw.line([(dot_cx, y + 54), (dot_cx, y + 100)], fill=(108, 92, 231, 40), width=2)

        # Period
        draw.text((175, y + 14), period, font=get_font(28, bold=True), fill=WHITE)
        draw.text((175, y + 50), note, font=get_font(20), fill=LIGHT_PURPLE)

        # Amount (right-aligned)
        bbox = draw.textbbox((0, 0), amount, font=get_font(34, bold=True))
        tw = bbox[2] - bbox[0]
        draw.text((W - 140 - tw, y + 25), amount, font=get_font(34, bold=True), fill=color)

        y += 105

    # Big emphasis box
    draw_rounded_rect(draw, (80, 910, W - 80, 1000), 16, fill=(255, 215, 0, 15), outline=GOLD, width=3)
    draw_centered_text(draw, 920, "₹500/day → ₹2.67 CRORE", get_font(38, bold=True), fill=GOLD)
    draw_centered_text(draw, 965, "The cost of NOT saving is a fortune lost", get_font(24), fill=NEAR_WHITE)

    # Bottom
    draw_centered_text(draw, H - 42, "Start tracking today  •  @mywealthpilot.in", get_font(22), fill=LIGHT_PURPLE)

    img.save(os.path.join(OUT, "pre4_saving_power.png"), quality=95)
    print("Pre-Post 4: Cost of Not Saving created")


# ==========================================
# POST 5: MOTIVATIONAL — "Take Control" (teaser before launch)
# ==========================================
def post5_take_control():
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, PURPLE_DARK, DARK_BG)

    f_xl = get_font(62, bold=True)
    f_lg = get_font(46, bold=True)
    f_md = get_font(34, bold=True)
    f_sm = get_font(28)
    f_quote = get_font(40, bold=True)

    # Decorative compass ring
    cx, cy = W // 2, 300
    for r, alpha in [(200, 15), (180, 10), (160, 8)]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=None,
                     outline=(255, 255, 255, alpha), width=1)

    # Compass ticks
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        x1 = cx + int(195 * math.cos(rad))
        y1 = cy + int(195 * math.sin(rad))
        x2 = cx + int(205 * math.cos(rad))
        y2 = cy + int(205 * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 40), width=2)

    # Shield silhouette in center
    draw.polygon([
        (cx, cy - 100), (cx + 75, cy - 55), (cx + 75, cy + 10),
        (cx, cy + 100), (cx - 75, cy + 10), (cx - 75, cy - 55)
    ], fill=(255, 255, 255, 12), outline=(255, 255, 255, 30))

    # Bold rupee in shield
    draw_centered_text(draw, cy - 32, "₹", get_font(90, bold=True), fill=GOLD)

    # Quote section
    draw_centered_text(draw, 530, '"Do not save what is left', f_quote, fill=WHITE)
    draw_centered_text(draw, 580, 'after spending,', f_quote, fill=WHITE)
    draw_centered_text(draw, 640, 'Spend what is left', f_quote, fill=GOLD)
    draw_centered_text(draw, 690, 'after saving."', f_quote, fill=GOLD)
    draw_centered_text(draw, 750, "— Warren Buffett", get_font(26), fill=LIGHT_PURPLE)

    # Take control message
    draw_rounded_rect(draw, (120, 820, W - 120, 900), 16, fill=(255, 255, 255, 10), outline=GOLD, width=2)
    draw_centered_text(draw, 833, "It's time to take control", get_font(34, bold=True), fill=WHITE)
    draw_centered_text(draw, 870, "of every ₹ you earn", get_font(28), fill=GOLD)

    # Teaser
    draw_rounded_rect(draw, (W // 2 - 220, 930, W // 2 + 220, 990), 30, fill=GOLD)
    draw_centered_text(draw, 942, "Something is coming... 🚀", get_font(32, bold=True), fill=DARK_BG)

    # Bottom
    draw_centered_text(draw, H - 42, "Stay tuned  •  @mywealthpilot.in", get_font(22), fill=LIGHT_PURPLE)

    img.save(os.path.join(OUT, "pre5_take_control.png"), quality=95)
    print("Pre-Post 5: Take Control / Teaser created")


if __name__ == "__main__":
    post1_inflation()
    post2_salary_gap()
    post3_spending_breakdown()
    post4_cost_of_not_saving()
    post5_take_control()
    print(f"\nAll 5 pre-launch posts saved to: {OUT}")

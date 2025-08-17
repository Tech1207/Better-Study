import pygame, json, os, time

# ----------------------------
# Config
# ----------------------------
CONFIG_FILE = "debugstats_config.json"
JSON_FILE = "Questions.json"

default_config = {
    "WINDOW_WIDTH": 1200,
    "WINDOW_HEIGHT": 800,
    "FONT_SIZE": 20,
    "COLUMN_COUNT": 3,
    "ROW_PADDING": 10,
    "COLUMN_PADDING": 50,
    "REFRESH_INTERVAL": 1,  # seconds for JSON reload
    "SCROLL_SPEED": 20
}

# Load or create config
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
else:
    config = default_config
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

WIDTH = config.get("WINDOW_WIDTH", 1200)
HEIGHT = config.get("WINDOW_HEIGHT", 800)
FONT_SIZE = config.get("FONT_SIZE", 20)
COLUMN_COUNT = config.get("COLUMN_COUNT", 3)
ROW_PADDING = config.get("ROW_PADDING", 10)
COLUMN_PADDING = config.get("COLUMN_PADDING", 50)
REFRESH_INTERVAL = config.get("REFRESH_INTERVAL", 1)
SCROLL_SPEED = config.get("SCROLL_SPEED", 20)

# ----------------------------
# Pygame Setup
# ----------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Quiz Debug Stats")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", FONT_SIZE)
BLACK, WHITE, GREY, DARK_GREY = (0,0,0), (255,255,255), (200,200,200), (150,150,150)

# ----------------------------
# Variables
# ----------------------------
scroll_offset = 0
scrollbar_rect = None
scrollbar_dragging = False
drag_start_y = 0
scroll_start_offset = 0
last_mod_time = 0
last_reload_time = 0
QuestionsAnswers = {}

# ----------------------------
# Helpers
# ----------------------------
def load_questions():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Cache wrapped lines
        column_width = (WIDTH - COLUMN_PADDING*(COLUMN_COUNT+1)) // COLUMN_COUNT
        for q, d in data.items():
            d['wrapped_lines'] = wrap_text(q, font, column_width)
        return data
    return {}

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    return lines

def draw_stats(data, scroll_offset):
    screen.fill(WHITE)
    questions = list(data.keys())

    column_width = (WIDTH - COLUMN_PADDING*(COLUMN_COUNT+1)) // COLUMN_COUNT
    col_x_positions = [COLUMN_PADDING + i*(column_width+COLUMN_PADDING) for i in range(COLUMN_COUNT)]
    column_heights = [ROW_PADDING for _ in range(COLUMN_COUNT)]
    line_height = FONT_SIZE + 2

    max_height = 0

    for question in questions:
        col = column_heights.index(min(column_heights))
        x = col_x_positions[col]
        y = column_heights[col] - scroll_offset

        wrapped_lines = data[question]['wrapped_lines']

        # Draw question
        for i, line in enumerate(wrapped_lines):
            screen.blit(font.render(line, True, BLACK), (x, y + i*line_height))

        # Draw stats
        stats = data[question].get("stats", {})
        stat_text = f"R:{stats.get('right',0)} W:{stats.get('wrong',0)} Seen:{stats.get('times_seen',0)}"
        screen.blit(font.render(stat_text, True, BLACK), (x, y + len(wrapped_lines)*line_height + 2))

        # Update column height
        column_heights[col] += (len(wrapped_lines)+1)*line_height + ROW_PADDING
        max_height = max(max_height, column_heights[col])

    # Draw scrollbar
    global scrollbar_rect
    if max_height > HEIGHT:
        bar_height = HEIGHT * HEIGHT / max_height
        bar_y = scroll_offset * HEIGHT / max_height
        bar_width = 15
        bar_x = WIDTH - bar_width - 5
        scrollbar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, GREY, scrollbar_rect)
    else:
        scrollbar_rect = None

    return max_height

# ----------------------------
# Main Loop
# ----------------------------
QuestionsAnswers = load_questions()
if os.path.exists(JSON_FILE):
    last_mod_time = os.path.getmtime(JSON_FILE)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            # Re-wrap questions
            for q, d in QuestionsAnswers.items():
                d['wrapped_lines'] = wrap_text(q, font, (WIDTH - COLUMN_PADDING*(COLUMN_COUNT+1)) // COLUMN_COUNT)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # scroll up
                scroll_offset = max(0, scroll_offset - SCROLL_SPEED)
            elif event.button == 5:  # scroll down
                scroll_offset += SCROLL_SPEED
            elif event.button == 1:  # left click
                if scrollbar_rect and scrollbar_rect.collidepoint(event.pos):
                    scrollbar_dragging = True
                    drag_start_y = event.pos[1]
                    scroll_start_offset = scroll_offset
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                scrollbar_dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if scrollbar_dragging and scrollbar_rect:
                bar_max_offset = HEIGHT - scrollbar_rect.height
                delta_y = event.pos[1] - drag_start_y
                proportion = delta_y / bar_max_offset
                max_scroll = max_height - HEIGHT
                scroll_offset = min(max(max_scroll * proportion + scroll_start_offset, 0), max_scroll)

    # Reload JSON periodically
    if time.time() - last_reload_time > REFRESH_INTERVAL:
        if os.path.exists(JSON_FILE):
            mod_time = os.path.getmtime(JSON_FILE)
            if mod_time != last_mod_time:
                QuestionsAnswers = load_questions()
                last_mod_time = mod_time
        last_reload_time = time.time()

    # Draw stats
    max_height = draw_stats(QuestionsAnswers, scroll_offset)

    # Clamp scroll
    if max_height > HEIGHT:
        scroll_offset = min(scroll_offset, max_height - HEIGHT)
    else:
        scroll_offset = 0

    pygame.display.flip()
    clock.tick(60)
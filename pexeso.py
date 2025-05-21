import asyncio
import platform
import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Window settings
width, height = 1200, 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pexeso")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
DARK_GRAY = (100, 100, 100)
BLUE = (100, 150, 200)
HOVER_BLUE = (120, 180, 240)
YELLOW = (240, 200, 100)
HOVER_YELLOW = (255, 220, 120)
PASTEL_PURPLE = (180, 150, 200)
PASTEL_PINK = (220, 160, 180)
GLOW_COLOR = (255, 255, 255, 50)  # Semi-transparent white for glow

# Fonts
try:
    title_font = pygame.font.SysFont("arial,helvetica,sans", 90, bold=True)
    button_font = pygame.font.SysFont("arial,helvetica,sans", 36, bold=True)
    info_font = pygame.font.SysFont("arial,helvetica,sans", 30)
except:
    title_font = pygame.font.SysFont(None, 90)
    button_font = pygame.font.SysFont(None, 36)
    info_font = pygame.font.SysFont(None, 30)

# Difficulty settings with text-based cards
difficulties = {
    "easy": {"rows": 4, "cols": 2, "values": ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D']},
    "medium": {"rows": 4, "cols": 4, "values": ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D', 'E', 'E', 'F', 'F', 'G', 'G', 'H', 'H']},
    "hard": {"rows": 6, "cols": 4, "values": ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D', 'E', 'E', 'F', 'F', 'G', 'G', 'H', 'H', 'I', 'I', 'J', 'J', 'K', 'K', 'L', 'L']}
}

# Menu buttons
buttons = [
    {"text": "1 Hráč", "y": 200, "mode": "single", "color": GRAY},
    {"text": "2 Hráči", "y": 280, "mode": "multi", "color": GRAY},
    {"text": "Ľahká", "y": 380, "difficulty": "easy", "color": GRAY},
    {"text": "Stredná", "y": 460, "difficulty": "medium", "color": GRAY},
    {"text": "Ťažká", "y": 540, "difficulty": "hard", "color": GRAY},
    {"text": "Štart", "y": 640, "action": "start", "color": YELLOW},
    {"text": "Koniec", "y": 720, "action": "exit", "color": YELLOW}
]

# Precompute background gradient
background_surface = pygame.Surface((width, height), pygame.SRCALPHA)
for r in range(max(width, height), 0, -5):
    alpha = r / max(width, height)
    color = (
        int(PASTEL_PURPLE[0] * alpha + PASTEL_PINK[0] * (1 - alpha)),
        int(PASTEL_PURPLE[1] * alpha + PASTEL_PINK[1] * (1 - alpha)),
        int(PASTEL_PURPLE[2] * alpha + PASTEL_PINK[2] * (1 - alpha))
    )
    pygame.draw.circle(background_surface, color, (width // 2, height // 2), r)

# Cache text surfaces
title_surface = title_font.render("Pexeso", True, WHITE)
title_shadow = title_font.render("Pexeso", True, DARK_GRAY)
title_rect = title_surface.get_rect(center=(width // 2, 100))
button_surfaces = {btn["text"]: button_font.render(btn["text"], True, WHITE) for btn in buttons}
restart_surface = button_font.render("Reštart", True, WHITE)
menu_surface = button_font.render("Menu", True, WHITE)

def init_game(difficulty_settings):
    rows, cols = difficulty_settings["rows"], difficulty_settings["cols"]
    values = difficulty_settings["values"].copy()
    random.shuffle(values)
    cards = [{'value': values[i], 'revealed': False, 'matched': False, 'flip_progress': 0.0} for i in range(rows * cols)]
    card_size = 120
    card_margin = 15
    grid_width = cols * (card_size + card_margin) - card_margin
    grid_height = rows * (card_size + card_margin) - card_margin
    grid_x = (width - grid_width) // 2
    grid_y = (height - grid_height) // 2
    return cards, rows, cols, card_size, card_margin, grid_x, grid_y

async def main():
    # Game variables
    menu = True
    difficulty = None
    game_mode = "multi"  # Default to multiplayer
    cards = []
    rows, cols = 0, 0
    card_size, card_margin = 0, 15
    grid_x, grid_y = 0, 0
    first_card, second_card = None, None
    waiting, wait_time, wait_start = False, 1000, 0
    player1_score, player2_score = 0, 0
    player1_moves, player2_moves = 0, 0
    current_player = 1
    matches_found = 0
    game_over = False
    game_initialized = False
    start_time = 0
    pulse_time = 0
    FPS = 60
    clock = pygame.time.Clock()

    # Cache card surfaces
    card_surfaces = {chr(i): info_font.render(chr(i), True, WHITE) for i in range(65, 91)}  # A-Z

    while True:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pulse_time += 0.1
        pulse_scale = 1 + 0.05 * math.sin(pulse_time)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if menu:
                    for button in buttons:
                        text_rect = button_surfaces[button["text"]].get_rect(center=(width // 2, button["y"]))
                        button_rect = text_rect.inflate(60, 40)
                        if button_rect.collidepoint(mouse_x, mouse_y):
                            if button.get("mode"):
                                game_mode = button["mode"]
                                for btn in buttons:
                                    if btn.get("mode"):
                                        btn["color"] = HOVER_YELLOW if btn["mode"] == game_mode else GRAY
                            elif button.get("difficulty"):
                                difficulty = button["difficulty"]
                                for btn in buttons:
                                    if btn.get("difficulty"):
                                        btn["color"] = HOVER_YELLOW if btn["difficulty"] == difficulty else GRAY
                            elif button["action"] == "start" and difficulty:
                                menu = False
                                cards, rows, cols, card_size, card_margin, grid_x, grid_y = init_game(difficulties[difficulty])
                                game_initialized = True
                                player1_score, player2_score = 0, 0
                                player1_moves, player2_moves = 0, 0
                                matches_found = 0
                                current_player = 1
                                start_time = pygame.time.get_ticks()
                            elif button["action"] == "exit":
                                return
                elif not waiting and not game_over and game_initialized:
                    for i in range(rows):
                        for j in range(cols):
                            card_index = i * cols + j
                            card = cards[card_index]
                            if card['matched'] or card['revealed']:
                                continue
                            x = grid_x + j * (card_size + card_margin)
                            y = grid_y + i * (card_size + card_margin)
                            if x <= mouse_x <= x + card_size and y <= mouse_y <= y + card_size:
                                card['revealed'] = True
                                card['flip_progress'] = 1.0
                                if first_card is None:
                                    first_card = card_index
                                elif second_card is None and first_card != card_index:
                                    second_card = card_index
                                    player1_moves += 1
                                    if cards[first_card]['value'] == cards[second_card]['value']:
                                        cards[first_card]['matched'] = True
                                        cards[second_card]['matched'] = True
                                        matches_found += 1
                                        player1_score += 1
                                        first_card, second_card = None, None
                                    else:
                                        waiting = True
                                        wait_start = pygame.time.get_ticks()
                                        if game_mode == "multi":
                                            current_player = 3 - current_player
                                            if current_player == 2:
                                                player2_moves += 1
                elif game_over:
                    restart_rect = restart_surface.get_rect(center=(width // 2, height // 2 + 100))
                    menu_rect = menu_surface.get_rect(center=(width // 2, height // 2 + 200))
                    if restart_rect.collidepoint(mouse_x, mouse_y):
                        cards, rows, cols, card_size, card_margin, grid_x, grid_y = init_game(difficulties[difficulty])
                        player1_score, player2_score = 0, 0
                        player1_moves, player2_moves = 0, 0
                        current_player = 1
                        matches_found = 0
                        game_over = False
                        first_card, second_card = None, None
                        waiting = False
                        game_initialized = True
                        start_time = pygame.time.get_ticks()
                    elif menu_rect.collidepoint(mouse_x, mouse_y):
                        menu = True
                        difficulty = None
                        game_mode = "multi"
                        game_initialized = False
                        cards = []
                        player1_score, player2_score = 0, 0
                        player1_moves, player2_moves = 0, 0
                        matches_found = 0
                        game_over = False
                        current_player = 1
                        start_time = 0
                        for btn in buttons:
                            btn["color"] = GRAY if btn.get("mode") or btn.get("difficulty") else YELLOW

        # Hover effect
        hover_button = None
        restart_hover = False
        menu_hover = False
        if menu:
            for button in buttons:
                text_rect = button_surfaces[button["text"]].get_rect(center=(width // 2, button["y"]))
                button_rect = text_rect.inflate(60, 40)
                if button_rect.collidepoint(mouse_x, mouse_y):
                    hover_button = button["text"]
                    if button.get("action") in ["start", "exit"]:
                        button["color"] = HOVER_YELLOW
                    elif button.get("mode") != game_mode or button.get("difficulty") != difficulty:
                        button["color"] = HOVER_BLUE
        else:
            restart_rect = restart_surface.get_rect(center=(width // 2, height // 2 + 100))
            menu_rect = menu_surface.get_rect(center=(width // 2, height // 2 + 200))
            restart_hover = restart_rect.collidepoint(mouse_x, mouse_y)
            menu_hover = menu_rect.collidepoint(mouse_x, mouse_y)

        # Card flip animation
        for card in cards:
            if card['revealed'] and card['flip_progress'] > 0:
                card['flip_progress'] = max(0, card['flip_progress'] - 0.15)
            elif not card['revealed'] and card['flip_progress'] < 1:
                card['flip_progress'] = min(1, card['flip_progress'] + 0.15)

        # Check waiting
        if waiting and pygame.time.get_ticks() - wait_start > wait_time:
            cards[first_card]['revealed'] = False
            cards[second_card]['revealed'] = False
            first_card, second_card = None, None
            waiting = False

        # Check win condition
        if game_initialized and matches_found == len(cards) // 2 and not game_over:
            game_over = True

        # Rendering
        screen.blit(background_surface, (0, 0))

        if menu:
            screen.blit(title_shadow, (title_rect.x + 5, title_rect.y + 5))
            screen.blit(title_surface, title_rect)
            for button in buttons:
                text = button_surfaces[button["text"]]
                text_rect = text.get_rect(center=(width // 2, button["y"]))
                button_rect = text_rect.inflate(60 * pulse_scale, 40 * pulse_scale)
                if hover_button == button["text"]:
                    pygame.draw.rect(screen, GLOW_COLOR, button_rect.inflate(10, 10), 4, border_radius=15)
                pygame.draw.rect(screen, DARK_GRAY, (button_rect.left + 5, button_rect.top + 5, button_rect.width, button_rect.height), border_radius=15)
                pygame.draw.rect(screen, button["color"], button_rect, border_radius=15)
                screen.blit(text, text_rect)
        else:
            for i in range(rows):
                for j in range(cols):
                    card_index = i * cols + j
                    card = cards[card_index]
                    x = grid_x + j * (card_size + card_margin)
                    y = grid_y + i * (card_size + card_margin)
                    scale = 1 - 0.3 * abs(math.cos(math.pi * card['flip_progress']))
                    surface = pygame.Surface((card_size, card_size), pygame.SRCALPHA)
                    card_color = (
                        int(BLACK[0] * card['flip_progress'] + BLUE[0] * (1 - card['flip_progress'])),
                        int(BLACK[1] * card['flip_progress'] + BLUE[1] * (1 - card['flip_progress'])),
                        int(BLACK[2] * card['flip_progress'] + BLUE[2] * (1 - card['flip_progress']))
                    )
                    pygame.draw.rect(surface, card_color if not card['matched'] else GRAY, (0, 0, card_size, card_size), border_radius=10)
                    if card['flip_progress'] <= 0.5 and not card['matched']:
                        text = card_surfaces.get(card['value'], info_font.render(card['value'], True, WHITE))
                        text_rect = text.get_rect(center=(card_size // 2, card_size // 2))
                        surface.blit(text, text_rect)
                    scaled_surface = pygame.transform.smoothscale(surface, (int(card_size * scale), int(card_size * scale)))
                    screen.blit(scaled_surface, (x + (card_size - scaled_surface.get_width()) // 2, y + (card_size - scaled_surface.get_height()) // 2))

            # Info display
            elapsed_time = (pygame.time.get_ticks() - start_time) // 1000 if game_initialized else 0
            info_texts = [
                f"Hráč {current_player} na rade" if game_mode == "multi" else "Hráč 1 na rade",
                f"Hráč 1: {player1_score} (Ťahy: {player1_moves})",
                f"Hráč 2: {player2_score} (Ťahy: {player2_moves})" if game_mode == "multi" else ""
            ]
            info_surface = pygame.Surface((310, 120 if game_mode == "single" else 160), pygame.SRCALPHA)
            for r in range(200, 0, -5):
                alpha = r / 200
                color = (
                    int(PASTEL_PURPLE[0] * alpha + PASTEL_PINK[0] * (1 - alpha)),
                    int(PASTEL_PURPLE[1] * alpha + PASTEL_PINK[1] * (1 - alpha)),
                    int(PASTEL_PURPLE[2] * alpha + PASTEL_PINK[2] * (1 - alpha))
                )
                pygame.draw.circle(info_surface, color, (155, 80), r)
            screen.blit(info_surface, (5, 5))
            for i, text in enumerate(info_texts):
                if text:
                    rendered = info_font.render(text, True, WHITE)
                    screen.blit(rendered, (10, 10 + i * 40))
            time_text = info_font.render(f"Čas: {elapsed_time}s", True, WHITE)
            screen.blit(time_text, (10, 10 + (2 if game_mode == "single" else 3) * 40))

            if game_over:
                winner = "Hráč 1" if game_mode == "single" or player1_score > player2_score else "Hráč 2" if player2_score > player1_score else "Remíza"
                text = title_font.render(f"Výhra! {winner}", True, WHITE)
                text_rect = text.get_rect(center=(width // 2, height // 2))
                pygame.draw.rect(screen, YELLOW, text_rect.inflate(50, 30), border_radius=15)
                screen.blit(text, text_rect)
                for text, y, hover, surface in [
                    ("Reštart", height // 2 + 100, restart_hover, restart_surface),
                    ("Menu", height // 2 + 200, menu_hover, menu_surface)
                ]:
                    text_rect = surface.get_rect(center=(width // 2, y))
                    button_rect = text_rect.inflate(60 * pulse_scale, 40 * pulse_scale)
                    if hover:
                        pygame.draw.rect(screen, GLOW_COLOR, button_rect.inflate(10, 10), 4, border_radius=15)
                    pygame.draw.rect(screen, DARK_GRAY, (button_rect.left + 5, button_rect.top + 5, button_rect.width, button_rect.height), border_radius=15)
                    pygame.draw.rect(screen, HOVER_YELLOW if hover else YELLOW, button_rect, border_radius=15)
                    screen.blit(surface, text_rect)

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    asyncio.run(main())
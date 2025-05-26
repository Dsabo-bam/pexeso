import asyncio
import platform
import pygame
import random
import math

# -----------------------
# Inicializácia Pygame + Mixer
# -----------------------
pygame.init()
pygame.mixer.init()

# -----------------------
# Načítanie zvukov
# -----------------------
# Vyžaduje priečinok `sounds/` v rovnakej zložke ako tento skript:
# sounds/
#   ├─ background.mp3
#   ├─ flip.wav
#   ├─ game_over.wav
#   ├─ button_click.wav      ← nový efekt pre klik na tlačidlo
#   └─ match.wav             ← nový efekt pre správny pár
pygame.mixer.music.load("sounds/background.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

flip_sound       = pygame.mixer.Sound("sounds/flip.wav")
game_over_sound = pygame.mixer.Sound("sounds/game_over.wav")
button_sound     = pygame.mixer.Sound("sounds/button_click.wav")
match_sound      = pygame.mixer.Sound("sounds/match.wav")
for s in (flip_sound, game_over_sound, button_sound, match_sound):
    s.set_volume(0.5)

# -----------------------
# Nastavenie okna
# -----------------------
width, height = 1200, 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pexeso")

# -----------------------
# Farby
# -----------------------
WHITE         = (255, 255, 255)
BLACK         = (0,   0,   0)
GRAY          = (180, 180, 180)
DARK_GRAY     = (100, 100, 100)
BLUE          = (100, 150, 200)
YELLOW        = (240, 200, 100)
PASTEL_PURPLE = (180, 150, 200)
PASTEL_PINK   = (220, 160, 180)
GREEN         = (100, 200, 150)
RED           = (200, 100, 100)

# -----------------------
# Nastavenia (Settings)
# -----------------------
settings_data = {
    "background_color": None,  # None = gradient
    "sound": True,             # zap/vyp
    "volume": 0.5,             # 0.0–1.0
}

# -----------------------
# Kontrastné schémy pre každé pozadie
# -----------------------
color_schemes = {
    None:        {"card_back": BLUE,         "card_front": BLACK, "button": YELLOW},
    GRAY:        {"card_back": PASTEL_PURPLE,"card_front": BLACK, "button": BLUE},
    BLUE:        {"card_back": DARK_GRAY,    "card_front": WHITE, "button": YELLOW},
    PASTEL_PINK: {"card_back": GREEN,        "card_front": BLACK, "button": RED},
}

# -----------------------
# Možnosti farieb pozadia
# -----------------------
bg_options = [
    ("Predvolené", None),
    ("Sivá",       GRAY),
    ("Modrá",      BLUE),
    ("Ružová",     PASTEL_PINK),
]

# -----------------------
# Fonty
# -----------------------
try:
    title_font    = pygame.font.SysFont("arial,helvetica,sans", 90, bold=True)
    subtitle_font = pygame.font.SysFont("arial,helvetica,sans", 60, bold=True)
    button_font   = pygame.font.SysFont("arial,helvetica,sans", 36, bold=True)
    info_font     = pygame.font.SysFont("arial,helvetica,sans", 30)
except:
    title_font    = pygame.font.SysFont(None, 90)
    subtitle_font = pygame.font.SysFont(None, 60)
    button_font   = pygame.font.SysFont(None, 36)
    info_font     = pygame.font.SysFont(None, 30)

# -----------------------
# Gradient pozadia
# -----------------------
def draw_gradient():
    bg = pygame.Surface((width, height), pygame.SRCALPHA)
    for r in range(max(width, height), 0, -5):
        a = r / max(width, height)
        col = (
            int(PASTEL_PURPLE[0]*a + PASTEL_PINK[0]*(1-a)),
            int(PASTEL_PURPLE[1]*a + PASTEL_PINK[1]*(1-a)),
            int(PASTEL_PURPLE[2]*a + PASTEL_PINK[2]*(1-a))
        )
        pygame.draw.circle(bg, col, (width//2, height//2), r)
    screen.blit(bg, (0, 0))

# -----------------------
# Výber obtiažnosti
# -----------------------
difficulties = {
    "easy":   {"rows": 4, "cols": 2, "values": list("AABBCCDD")},
    "medium": {"rows": 4, "cols": 4, "values": list("AABBCCDDEEFFGGHH")},
    "hard":   {"rows": 6, "cols": 4, "values": list("AABBCCDDEEFFGGHHIIJJKKLL")},
}
def init_game(settings):
    rows, cols = settings["rows"], settings["cols"]
    vals = settings["values"].copy()
    random.shuffle(vals)
    cards = [{
        "value": vals[i],
        "revealed": False,
        "matched": False,
        "flip_progress": 0.0
    } for i in range(rows * cols)]
    size, margin = 120, 15
    grid_w = cols * (size + margin) - margin
    grid_h = rows * (size + margin) - margin
    gx = (width - grid_w) // 2
    gy = (height - grid_h) // 2
    return cards, rows, cols, size, margin, gx, gy

# -----------------------
# Pred-render písmená
# -----------------------
card_surfs = {chr(i): info_font.render(chr(i), True, WHITE) for i in range(65, 91)}

# -----------------------
# Kreslenie tlačidla
# -----------------------
def draw_button(text, color, center=None, corner=None, inflate=(200,50), pulse=1.0):
    surf = button_font.render(text, True, WHITE)
    rect = surf.get_rect(bottomright=corner) if corner else surf.get_rect(center=center)
    btn = rect.inflate(inflate[0]*pulse, inflate[1]*pulse)
    pygame.draw.rect(screen, DARK_GRAY, (btn.left+5, btn.top+5, btn.width, btn.height), border_radius=15)
    pygame.draw.rect(screen, color, btn, border_radius=15)
    screen.blit(surf, rect)
    return btn

# -----------------------
# Titulok + Nastavenia ikona
# -----------------------
title_surf   = title_font.render("Pexeso", True, WHITE)
title_shadow = title_font.render("Pexeso", True, DARK_GRAY)
title_rect   = title_surf.get_rect(center=(width//2, 100))

settings_circle_center = (100, 100)
settings_circle_radius = 30
settings_label    = subtitle_font.render("Nastavenia", True, WHITE)
settings_label_sh = subtitle_font.render("Nastavenia", True, DARK_GRAY)

# -----------------------
# Hlavná slučka
# -----------------------
async def main():
    state = "main"  # main, submenu, game, settings
    game_mode = difficulty = None

    cards = []; rows = cols = 0
    size = margin = 0; gx = gy = 0
    first = second = None
    waiting = False; wait_ms = 1000; wait_start = 0
    p1_score = p2_score = p1_moves = p2_moves = 0
    current = 1; matches = 0
    game_over = False; winner = ""
    game_started = False; start_time = 0

    FPS = 144
    clock = pygame.time.Clock()
    pulse_time = 0

    # Rect-y tlačidiel
    start_btn = play_btn = None
    player_btns = diff_btns = []
    bg_option_btns = []; sound_btn = back_btn = None
    menu_during_btn = None

    while True:
        mx, my = pygame.mouse.get_pos()
        pulse_time += 0.1
        pulse = 1 + 0.05 * math.sin(pulse_time)

        # Slider pre hlasitosť
        slider_x = width//2 - 150
        slider_y = 220 + len(bg_options)*80 + 80
        slider_w = 300; slider_h = 5; knob_r = 10
        slider_rect = pygame.Rect(slider_x, slider_y, slider_w, slider_h)
        slider_area = slider_rect.inflate(knob_r*2, knob_r*2)

        # vyber schémy
        scheme = color_schemes[settings_data["background_color"]]
        card_back_col  = scheme["card_back"]
        card_front_col = scheme["card_front"]
        btn_col        = scheme["button"]

        # --- EVENT LOOP ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            # ťahom myšou na slider
            if state == "settings" and event.type == pygame.MOUSEMOTION and event.buttons[0]:
                if slider_area.collidepoint(event.pos):
                    rel = (event.pos[0] - slider_x)/slider_w
                    settings_data["volume"] = max(0, min(1, rel))
                    for s in (flip_sound, game_over_sound, button_sound, match_sound):
                        s.set_volume(settings_data["volume"])
                    pygame.mixer.music.set_volume(settings_data["volume"])

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Nastavenia ikona (len mimo hry)
                if state != "game":
                    dx = mx - settings_circle_center[0]
                    dy = my - settings_circle_center[1]
                    rect_txt = settings_label.get_rect(midleft=(
                        settings_circle_center[0]+settings_circle_radius+10,
                        settings_circle_center[1]
                    ))
                    if math.hypot(dx, dy) <= settings_circle_radius or rect_txt.collidepoint(mx, my):
                        if settings_data["sound"]: button_sound.play()
                        state = "settings"
                        continue

                # MENU počas hry
                if state == "game" and menu_during_btn and menu_during_btn.collidepoint(mx, my):
                    if settings_data["sound"]: button_sound.play()
                    state = "main"
                    game_mode = difficulty = None
                    game_started = False
                    continue

                # Main → Submenu
                if state == "main" and start_btn and start_btn.collidepoint(mx, my):
                    if settings_data["sound"]: button_sound.play()
                    state = "submenu"

                # Submenu → Game
                elif state == "submenu":
                    for i, btn in enumerate(player_btns):
                        if btn.collidepoint(mx, my):
                            if settings_data["sound"]: button_sound.play()
                            game_mode = ["single", "multi"][i]
                    for i, btn in enumerate(diff_btns):
                        if btn.collidepoint(mx, my):
                            if settings_data["sound"]: button_sound.play()
                            difficulty = ["easy", "medium", "hard"][i]
                    if play_btn and play_btn.collidepoint(mx, my) and game_mode and difficulty:
                        if settings_data["sound"]: button_sound.play()
                        cards, rows, cols, size, margin, gx, gy = init_game(difficulties[difficulty])
                        p1_score = p2_score = p1_moves = p2_moves = 0
                        current = 1; matches = 0
                        first = second = None
                        waiting = False; game_over = False
                        game_started = True; start_time = pygame.time.get_ticks()
                        state = "game"

                # Settings → Main
                elif state == "settings":
                    if sound_btn and sound_btn.collidepoint(mx, my):
                        settings_data["sound"] = not settings_data["sound"]
                        if settings_data["sound"]:
                            pygame.mixer.music.unpause()
                        else:
                            pygame.mixer.music.pause()
                        if settings_data["sound"]: button_sound.play()
                    if slider_area.collidepoint(mx, my):
                        rel = (mx - slider_x)/slider_w
                        settings_data["volume"] = max(0, min(1, rel))
                        for s in (flip_sound, game_over_sound, button_sound, match_sound):
                            s.set_volume(settings_data["volume"])
                        pygame.mixer.music.set_volume(settings_data["volume"])
                    for i, btn in enumerate(bg_option_btns):
                        if btn.collidepoint(mx, my):
                            if settings_data["sound"]: button_sound.play()
                            settings_data["background_color"] = bg_options[i][1]
                    if back_btn and back_btn.collidepoint(mx, my):
                        if settings_data["sound"]: button_sound.play()
                        state = "main"
                        game_mode = difficulty = None

                # Hra – klik na kartu
                elif state == "game" and game_started and not waiting and not game_over:
                    for i in range(rows):
                        for j in range(cols):
                            idx = i*cols + j
                            c   = cards[idx]
                            if c["matched"] or c["revealed"]:
                                continue
                            x = gx + j*(size+margin)
                            y = gy + i*(size+margin)
                            if x <= mx <= x+size and y <= my <= y+size:
                                c["revealed"] = True
                                c["flip_progress"] = 1.0
                                if settings_data["sound"]: flip_sound.play()
                                if first is None:
                                    first = idx
                                elif second is None and first != idx:
                                    second = idx
                                    if game_mode=="multi":
                                        if current==1: p1_moves+=1
                                        else:          p2_moves+=1
                                    else:
                                        p1_moves+=1
                                    if cards[first]["value"]==cards[second]["value"]:
                                        cards[first]["matched"]=cards[second]["matched"]=True
                                        matches += 1
                                        if settings_data["sound"]: match_sound.play()
                                        if game_mode=="multi":
                                            if current==1: p1_score+=1
                                            else:          p2_score+=1
                                        else:
                                            p1_score+=1
                                        first=second=None
                                    else:
                                        waiting=True
                                        wait_start=pygame.time.get_ticks()
                                        if game_mode=="multi":
                                            current=3-current

        # Skrytie nesprávnych
        if waiting and pygame.time.get_ticks()-wait_start>wait_ms:
            cards[first]["revealed"]=False
            cards[second]["revealed"]=False
            first=second=None
            waiting=False

        # Animácia flip
        for c in cards:
            if c["revealed"] and c["flip_progress"]>0:
                c["flip_progress"]=max(0,c["flip_progress"]-0.15)
            elif not c["revealed"] and c["flip_progress"]<1:
                c["flip_progress"]=min(1,c["flip_progress"]+0.15)

        # Koniec hry
        if game_started and matches==len(cards)//2 and not game_over:
            game_over=True
            if settings_data["sound"]: game_over_sound.play()
            if game_mode=="multi":
                if p1_score>p2_score:   winner="Víťaz: Hráč 1"
                elif p2_score>p1_score: winner="Víťaz: Hráč 2"
                else:                    winner="Remíza"
            else:
                winner=f"Získané páry: {p1_score}"

        # --- VYKRESĽOVANIE ---
        if settings_data["background_color"]:
            screen.fill(settings_data["background_color"])
        else:
            draw_gradient()

        if state!="game":
            pygame.draw.circle(screen, btn_col, settings_circle_center, settings_circle_radius)
            pygame.draw.circle(screen, DARK_GRAY,
                               (settings_circle_center[0]+3, settings_circle_center[1]+3),
                               settings_circle_radius)
            screen.blit(settings_label_sh,(
                settings_circle_center[0]+settings_circle_radius+10+3,
                settings_circle_center[1]-settings_label.get_height()/2+3))
            screen.blit(settings_label,(
                settings_circle_center[0]+settings_circle_radius+10,
                settings_circle_center[1]-settings_label.get_height()/2))

        if state=="main":
            screen.blit(title_shadow,(title_rect.x+5,title_rect.y+5))
            screen.blit(title_surf,title_rect)
            start_btn=draw_button("Štart",btn_col,center=(width//2,height//2),inflate=(200,50),pulse=pulse)

        elif state=="submenu":
            screen.blit(title_shadow,(title_rect.x+5,title_rect.y+5))
            screen.blit(title_surf,title_rect)
            sub1=subtitle_font.render("POČET HRÁČOV",True,WHITE)
            sub1s=subtitle_font.render("POČET HRÁČOV",True,DARK_GRAY)
            r1=sub1.get_rect(center=(width//2,250))
            screen.blit(sub1s,(r1.x+3,r1.y+3));screen.blit(sub1,r1)
            sub2=subtitle_font.render("OBTIAŽNOSŤ",True,WHITE)
            sub2s=subtitle_font.render("OBTIAŽNOSŤ",True,DARK_GRAY)
            r2=sub2.get_rect(center=(width//2,450))
            screen.blit(sub2s,(r2.x+3,r2.y+3));screen.blit(sub2,r2)
            player_btns=[]
            for i,txt in enumerate(["1 Hráč","2 Hráči"]):
                x=width//2+(i*200-100)
                col=btn_col if game_mode==["single","multi"][i] else DARK_GRAY
                btn=draw_button(txt,col,center=(x,350),inflate=(150,50))
                player_btns.append(btn)
            diff_btns=[]
            for i,txt in enumerate(["Ľahká","Stredná","Ťažká"]):
                x=width//2+(i*200-200)
                col=btn_col if difficulty==["easy","medium","hard"][i] else DARK_GRAY
                btn=draw_button(txt,col,center=(x,530),inflate=(150,50))
                diff_btns.append(btn)
            play_btn=draw_button("HRAŤ",btn_col,center=(width//2,700),inflate=(150,50),pulse=pulse)

        elif state=="settings":
            screen.blit(title_shadow,(title_rect.x+5,title_rect.y+5))
            screen.blit(title_surf,title_rect)
            hdr=subtitle_font.render("NASTAVENIA",True,WHITE)
            screen.blit(hdr,(width//2-hdr.get_width()//2,180))
            bg_option_btns=[]
            for i,(label,color_val) in enumerate(bg_options):
                y=220+i*80
                col=color_val if color_val is not None else DARK_GRAY
                btn=draw_button(label,col,center=(width//2,y),inflate=(300,60))
                bg_option_btns.append(btn)
            sound_text="Zvuk: Zapnutý" if settings_data["sound"] else "Zvuk: Vypnutý"
            sound_btn=draw_button(sound_text,btn_col,center=(width//2,220+len(bg_options)*80),inflate=(300,60))
            # slider
            pygame.draw.rect(screen,WHITE,slider_rect)
            knob_x=slider_x+settings_data["volume"]*slider_w
            knob_y=slider_y+slider_h//2
            pygame.draw.circle(screen,btn_col,(int(knob_x),knob_y),knob_r)
            back_btn=draw_button("Späť",btn_col,center=(width//2,height-100),inflate=(200,50))

        else:  # game
            for i in range(rows):
                for j in range(cols):
                    idx=i*cols+j; c=cards[idx]
                    x=gx+j*(size+margin); y=gy+i*(size+margin)
                    t=c["flip_progress"]
                    scale=1-0.3*abs(math.cos(math.pi*t))
                    surf=pygame.Surface((size,size),pygame.SRCALPHA)
                    fb,bb=card_front_col,card_back_col
                    col=(int(fb[0]*t+bb[0]*(1-t)),int(fb[1]*t+bb[1]*(1-t)),int(fb[2]*t+bb[2]*(1-t)))
                    draw_col=GRAY if c["matched"] else col
                    pygame.draw.rect(surf,draw_col,(0,0,size,size),border_radius=10)
                    if t<=0.5 and not c["matched"]:
                        txt=card_surfs[c["value"]]; tr=txt.get_rect(center=(size//2,size//2))
                        surf.blit(txt,tr)
                    scaled=pygame.transform.smoothscale(surf,(int(size*scale),int(size*scale)))
                    screen.blit(scaled,(
                        x+(size-scaled.get_width())//2,
                        y+(size-scaled.get_height())//2))
            elapsed=(pygame.time.get_ticks()-start_time)//1000
            screen.blit(info_font.render(f"Hráč {current} na rade",True,WHITE),(10,10))
            screen.blit(info_font.render(f"Hráč 1: {p1_score} (Ťahy: {p1_moves})",True,WHITE),(10,50))
            if game_mode=="multi":
                screen.blit(info_font.render(f"Hráč 2: {p2_score} (Ťahy: {p2_moves})",True,WHITE),(10,90))
                screen.blit(info_font.render(f"Čas: {elapsed}s",True,WHITE),(10,130))
            else:
                screen.blit(info_font.render(f"Čas: {elapsed}s",True,WHITE),(10,90))
            if game_over:
                msg_surf=title_font.render(winner,True,WHITE)
                msg_rect=msg_surf.get_rect(center=(width//2,height//2-50))
                pygame.draw.rect(screen,btn_col,msg_rect.inflate(50,30),border_radius=15)
                screen.blit(msg_surf,msg_rect)
            menu_during_btn=draw_button("MENU",btn_col,corner=(width-20,height-20),inflate=(20,20),pulse=1.0)

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(1/ FPS)

if platform.system()=="Emscripten":
    asyncio.ensure_future(main())
else:
    asyncio.run(main())

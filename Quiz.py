import pygame, random, json, sys, time, ctypes

# ----------------------------
# High-DPI awareness
# ----------------------------
try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
except: pass

# ----------------------------
# Config
# ----------------------------
CONFIG_FILE = "config.json"
JSON_FILE = "Questions.json"

def load_config():
    with open(CONFIG_FILE,"r",encoding="utf-8") as f:
        return json.load(f)
def save_config(cfg):
    with open(CONFIG_FILE,"w",encoding="utf-8") as f:
        json.dump(cfg,f,indent=4)

config = load_config()
SHOW_SCROLLBAR = config.get("SHOW_SCROLLBAR", True)
ENABLE_SKIP_BUTTON = config.get("ENABLE_SKIP_BUTTON", True)
NEXT_DELAY = config.get("NEXT_DELAY", 2)
scroll_offset = config.get("SCROLL_OFFSET",0)
dragging_scroll = config.get("DRAG_SCROLLBAR",False)
manual_question_font = config.get("MANUAL_QUESTION_FONT",None)
manual_answer_font = config.get("MANUAL_ANSWER_FONT",None)
manual_ui_font = config.get("MANUAL_UI_FONT",None)

# ----------------------------
# Load / Save Questions
# ----------------------------
def load_questions():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for q in data:
        if "stats" not in data[q]:
            data[q]["stats"] = {"right":0,"wrong":0,"times_seen":0}
        else:
            for key in ["right","wrong","times_seen"]:
                if key not in data[q]["stats"]:
                    data[q]["stats"][key]=0
    return data

def save_questions(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data,f,indent=4,ensure_ascii=False)

QuestionsAnswers = load_questions()

# ----------------------------
# Pygame Setup
# ----------------------------
pygame.init()
WIDTH, HEIGHT = 1280,720
screen = pygame.display.set_mode((WIDTH,HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Quiz Game")
WHITE, BLACK, GRAY, GREEN, RED, SCROLL_COLOR = (255,255,255),(0,0,0),(200,200,200),(100,200,100),(200,100,100),(150,150,150)

# ----------------------------
# Wrapping functions
# ----------------------------
def render_wrapped_text_in_box(text, font, color, box_width):
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= box_width-10:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    surfaces=[]
    total_height=0
    for line in lines:
        surf = font.render(line, True, color)
        surfaces.append(surf)
        total_height += surf.get_height()
    return surfaces, total_height

def render_wrapped_text(text, font, color, max_width):
    words = text.split(' ')
    lines=[]
    current_line=""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0]<=max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    surfaces=[]
    y_offset=0
    for line in lines:
        surf = font.render(line, True, color)
        surfaces.append((surf, y_offset))
        y_offset += surf.get_height()+5
    return surfaces

# ----------------------------
# Fonts
# ----------------------------
def get_question_font(width):
    size = max(24, int(width*0.04))
    if manual_question_font is not None: size = manual_question_font
    return pygame.font.SysFont("arial", size, bold=True)
def get_answer_font(height):
    size = max(20,int(height*0.035))
    if manual_answer_font is not None: size = manual_answer_font
    return size
def get_ui_font(height):
    size = max(16,int(height*0.025))
    if manual_ui_font is not None: size = manual_ui_font
    return size

# ----------------------------
# Answer boxes
# ----------------------------
def create_answer_boxes(answers,width,height,question_height):
    boxes=[]
    box_width = int(width*0.8)
    gap=int(height*0.03)
    start_y=int(height*0.05)+question_height+gap
    y=start_y
    for ans in answers:
        ans_font = pygame.font.SysFont("arial", get_answer_font(height))
        wrapped_surfs,total_height = render_wrapped_text_in_box(ans, ans_font, BLACK, box_width)
        box_height = total_height + int(height*0.02)
        rect = pygame.Rect((width-box_width)//2, y, box_width, box_height)
        boxes.append((rect, ans, ans_font))
        y += box_height+gap
    return boxes

# ----------------------------
# Question selection
# ----------------------------
mode="Arcade"
def get_random_question():
    global QuestionsAnswers
    if mode=="Arcade":
        question = random.choice(list(QuestionsAnswers.keys()))
    else:
        questions=list(QuestionsAnswers.keys())
        weights=[]
        for q in questions:
            stats = QuestionsAnswers[q]["stats"]
            right = stats["right"] if stats["right"]>0 else 1
            wrong = stats["wrong"] if stats["wrong"]>0 else 1
            weights.append(wrong/right)
        question=random.choices(questions,weights=weights,k=1)[0]
    data = QuestionsAnswers[question]
    data["stats"]["times_seen"] += 1
    save_questions(QuestionsAnswers)
    answers = data["correct"] + data["wrong"]
    random.shuffle(answers)
    return question,answers,data["correct"]

# ----------------------------
# Buttons
# ----------------------------
def create_buttons(width,height):
    question_buttons = {"Q+":pygame.Rect(int(width*0.05),height-80,int(width*0.05),30),
                        "Q-":pygame.Rect(int(width*0.12),height-80,int(width*0.05),30),
                        "QDefault":pygame.Rect(int(width*0.2),height-80,int(width*0.1),30)}
    answer_buttons = {"A+":pygame.Rect(int(width*0.35),height-80,int(width*0.05),30),
                      "A-":pygame.Rect(int(width*0.42),height-80,int(width*0.05),30),
                      "ADefault":pygame.Rect(int(width*0.49),height-80,int(width*0.1),30)}
    ui_buttons = {"U+":pygame.Rect(int(width*0.65),height-80,int(width*0.05),30),
                  "U-":pygame.Rect(int(width*0.72),height-80,int(width*0.05),30),
                  "UDefault":pygame.Rect(int(width*0.79),height-80,int(width*0.1),30)}
    mode_buttons = {"Practice":pygame.Rect(int(width*0.05),height-40,int(width*0.1),30),
                    "Arcade":pygame.Rect(int(width*0.17),height-40,int(width*0.1),30)}
    skip_button = pygame.Rect(width-120,height-40,100,30)
    return question_buttons,answer_buttons,ui_buttons,mode_buttons,skip_button

# ----------------------------
# Initialize first question
# ----------------------------
question,answers,correct_answers = get_random_question()
font_q = get_question_font(WIDTH)
wrapped_surfaces = render_wrapped_text(question,font_q,BLACK,WIDTH-100)
question_height = sum([surf.get_height()+5 for surf,_ in wrapped_surfaces])
boxes=create_answer_boxes(answers,WIDTH,HEIGHT,question_height)
selected=None
show_feedback=False
feedback_start=0
feedback_type=None
chosen_answer=None

question_buttons,answer_buttons,ui_buttons,buttons_mode,skip_button = create_buttons(WIDTH,HEIGHT)

# ----------------------------
# Scroll helpers
# ----------------------------
def calculate_total_height():
    question_height = sum([surf.get_height()+5 for surf,_ in wrapped_surfaces])
    answer_height = sum([rect.height+int(HEIGHT*0.03) for rect,_,_ in boxes])
    return int(HEIGHT*0.05)+question_height+int(HEIGHT*0.03)+answer_height+100

def draw_scrollbar(total_height):
    if not SHOW_SCROLLBAR or total_height<=HEIGHT: return None
    bar_height = max(int(HEIGHT*HEIGHT/total_height),20)
    scroll_range = total_height - HEIGHT
    bar_y = int(-scroll_offset*(HEIGHT-bar_height)/scroll_range)
    bar_rect = pygame.Rect(WIDTH-15, bar_y,10,bar_height)
    pygame.draw.rect(screen, SCROLL_COLOR, bar_rect, border_radius=5)
    return bar_rect

# ----------------------------
# Main loop
# ----------------------------
running=True
while running:
    screen.fill(WHITE)
    WIDTH,HEIGHT = screen.get_size()
    question_buttons,answer_buttons,ui_buttons,buttons_mode,skip_button = create_buttons(WIDTH,HEIGHT)
    font_q = get_question_font(WIDTH)
    wrapped_surfaces = render_wrapped_text(question,font_q,BLACK,WIDTH-100)
    question_height = sum([surf.get_height()+5 for surf,_ in wrapped_surfaces])
    boxes=create_answer_boxes(answers,WIDTH,HEIGHT,question_height)
    total_height_content = calculate_total_height()
    scrollbar_rect = draw_scrollbar(total_height_content)

    # Feedback
    if show_feedback:
        font_feedback = pygame.font.SysFont("arial", max(40,int(min(WIDTH,HEIGHT)*0.08)),bold=True)
        if feedback_type=="correct":
            screen.fill(GREEN)
            msg=font_feedback.render("Correct! []~(￣▽￣)~*",True,BLACK)
            screen.blit(msg,(WIDTH//2-msg.get_width()//2, HEIGHT//2-msg.get_height()//2))
            if time.time()-feedback_start>NEXT_DELAY:
                show_feedback=False
                question,answers,correct_answers=get_random_question()
                boxes=create_answer_boxes(answers,WIDTH,HEIGHT,question_height)
                selected=None
        elif feedback_type=="wrong":
            screen.fill(RED)
            msg=font_feedback.render("Wrong",True,BLACK)
            screen.blit(msg,(WIDTH//2-msg.get_width()//2, HEIGHT//5))
            small_font = pygame.font.SysFont("arial", max(20,int(HEIGHT*0.03)))
            screen.blit(small_font.render(f"You chose: {chosen_answer}", True, BLACK),(50,HEIGHT//2))
            screen.blit(small_font.render("Correct: "+", ".join(correct_answers), True, BLACK),(50,HEIGHT//2+40))
    else:
        y_start=int(HEIGHT*0.05)+scroll_offset
        for surf,offset in wrapped_surfaces:
            screen.blit(surf,(50,y_start+offset))
        for rect, ans, ans_font in boxes:
            rect_scroll = rect.move(0,scroll_offset)
            pygame.draw.rect(screen,GRAY,rect_scroll,border_radius=10)
            wrapped_surfs,total_height = render_wrapped_text_in_box(ans,ans_font,BLACK,rect.width)
            y_offset = rect_scroll.top + (rect.height - total_height)//2
            for surf in wrapped_surfs:
                screen.blit(surf,(rect_scroll.left+5,y_offset))
                y_offset += surf.get_height()
        if config.get("SHOW_STATS_INFO", True):
                stats = QuestionsAnswers[question]["stats"]
                screen.blit(pygame.font.SysFont("arial",20).render(
                    f"Right: {stats['right']} | Wrong: {stats['wrong']} | Seen: {stats['times_seen']}", True, BLACK
                ), (50, HEIGHT-120))
        ui_font = pygame.font.SysFont("arial", get_ui_font(HEIGHT))
        # Draw buttons
        for label, rect in question_buttons.items():
            pygame.draw.rect(screen,GRAY,rect,border_radius=5)
            screen.blit(ui_font.render(label, True, BLACK),(rect.centerx-ui_font.size(label)[0]//2,rect.centery-ui_font.size(label)[1]//2))
        for label, rect in answer_buttons.items():
            pygame.draw.rect(screen,GRAY,rect,border_radius=5)
            screen.blit(ui_font.render(label, True, BLACK),(rect.centerx-ui_font.size(label)[0]//2,rect.centery-ui_font.size(label)[1]//2))
        for label, rect in ui_buttons.items():
            pygame.draw.rect(screen,GRAY,rect,border_radius=5)
            screen.blit(ui_font.render(label, True, BLACK),(rect.centerx-ui_font.size(label)[0]//2,rect.centery-ui_font.size(label)[1]//2))
        for label, rect in buttons_mode.items():
            pygame.draw.rect(screen,GREEN if mode==label else GRAY,rect,border_radius=5)
            screen.blit(ui_font.render(label, True, BLACK),(rect.centerx-ui_font.size(label)[0]//2,rect.centery-ui_font.size(label)[1]//2))
        if ENABLE_SKIP_BUTTON:
            pygame.draw.rect(screen,GRAY,skip_button,border_radius=5)
            screen.blit(ui_font.render("Skip", True, BLACK),(skip_button.centerx-ui_font.size("Skip")[0]//2, skip_button.centery-ui_font.size("Skip")[1]//2))

    pygame.display.flip()

    # ----------------------------
    # Event handling
    # ----------------------------
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            save_questions(QuestionsAnswers)
            config["SCROLL_OFFSET"]=scroll_offset
            config["DRAG_SCROLLBAR"]=dragging_scroll
            config["MANUAL_QUESTION_FONT"]=manual_question_font
            config["MANUAL_ANSWER_FONT"]=manual_answer_font
            config["MANUAL_UI_FONT"]=manual_ui_font
            save_config(config)
            running=False
            sys.exit()
        elif event.type==pygame.VIDEORESIZE:
            WIDTH,HEIGHT = event.w,event.h
            screen=pygame.display.set_mode((WIDTH,HEIGHT),pygame.RESIZABLE)
        elif event.type==pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if event.button == 1:
                clicked_ui = False

                # Scrollbar dragging
                if SHOW_SCROLLBAR and scrollbar_rect and scrollbar_rect.collidepoint(pos):
                    dragging_scroll = True
                    config["DRAG_SCROLLBAR"] = True
                    save_config(config)
                    continue

                # Question/Answer/UI font buttons
                for label, rect in question_buttons.items():
                    if rect.collidepoint(pos):
                        clicked_ui = True
                        if label=="Q+": manual_question_font = 24 if manual_question_font is None else manual_question_font+2
                        elif label=="Q-": manual_question_font = 24 if manual_question_font is None else max(8,manual_question_font-2)
                        elif label=="QDefault": manual_question_font=None

                for label, rect in answer_buttons.items():
                    if rect.collidepoint(pos):
                        clicked_ui = True
                        if label=="A+": manual_answer_font = 20 if manual_answer_font is None else manual_answer_font+2
                        elif label=="A-": manual_answer_font = 20 if manual_answer_font is None else max(8,manual_answer_font-2)
                        elif label=="ADefault": manual_answer_font=None

                for label, rect in ui_buttons.items():
                    if rect.collidepoint(pos):
                        clicked_ui = True
                        if label=="U+": manual_ui_font = 16 if manual_ui_font is None else manual_ui_font+2
                        elif label=="U-": manual_ui_font = 16 if manual_ui_font is None else max(8,manual_ui_font-2)
                        elif label=="UDefault": manual_ui_font=None

                for label, rect in buttons_mode.items():
                    if rect.collidepoint(pos):
                        clicked_ui = True
                        mode = label
                        question, answers, correct_answers = get_random_question()
                        boxes = create_answer_boxes(answers, WIDTH, HEIGHT, question_height)
                        selected = None

                # ----------------------
                # Skip button handled separately
                # ----------------------
                if ENABLE_SKIP_BUTTON and skip_button.collidepoint(pos):
                    question, answers, correct_answers = get_random_question()
                    boxes = create_answer_boxes(answers, WIDTH, HEIGHT, question_height)
                    selected = None
                    show_feedback = False
                    # Do NOT set clicked_ui=True here; skip button should always respond 
                # Answer selection
                if not clicked_ui:
                    if show_feedback:
                        show_feedback=False
                        question,answers,correct_answers=get_random_question()
                        boxes=create_answer_boxes(answers,WIDTH,HEIGHT,question_height)
                        selected=None
                    else:
                        for rect, ans, ans_font in boxes:
                            rect_scroll = rect.move(0, scroll_offset)
                            if rect_scroll.collidepoint(pos):
                                selected=ans
                                chosen_answer=ans
                                if ans in correct_answers:
                                    feedback_type="correct"
                                    feedback_start=time.time()
                                    QuestionsAnswers[question]["stats"]["right"]+=1
                                else:
                                    feedback_type="wrong"
                                    QuestionsAnswers[question]["stats"]["wrong"]+=1
                                save_questions(QuestionsAnswers)
                                show_feedback=True
            elif event.button==4:
                if total_height_content>HEIGHT: scroll_offset = min(scroll_offset+40,0)
            elif event.button==5:
                if total_height_content>HEIGHT: scroll_offset = max(scroll_offset-40, min(0, HEIGHT-total_height_content))
        elif event.type==pygame.MOUSEBUTTONUP:
            if event.button==1 and dragging_scroll: dragging_scroll=False; config["DRAG_SCROLLBAR"]=False; save_config(config)
        elif event.type==pygame.MOUSEMOTION:
            if dragging_scroll and SHOW_SCROLLBAR and scrollbar_rect:
                y = event.pos[1]-10
                scroll_range=total_height_content-HEIGHT
                bar_max=HEIGHT-scrollbar_rect.height
                scroll_offset=-int(y*scroll_range/bar_max)

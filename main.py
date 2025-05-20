# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import pygame
import random
import sqlite3
import time
import cv2
import numpy as np
from datetime import datetime
from twilio.rest import Client
import os
import math

pygame.init()

# Inițializare ecran
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Culori
WHITE = (255, 255, 255)
PINK = (255, 105, 180)
BLACK = (0, 0, 0)
BLUE = (0, 191, 255)

# Imagini
background_img = pygame.image.load("background1.jpg")
background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
bird_img = pygame.image.load("bird.png")
bird_img = pygame.transform.scale(bird_img, (40, 30))
menu_img = pygame.image.load("menu.png")
menu_img = pygame.transform.scale(menu_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
img_img = pygame.image.load("img.png")
img_img = pygame.transform.scale(img_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Fonturi
font = pygame.font.Font(None, 40)
score_font = pygame.font.Font(None, 30)
bonus_font = pygame.font.Font(None, 36)

# Inițializare ceas
clock = pygame.time.Clock()

# Twilio WhatsApp
account_sid = 'AC864af3ad607edde33015baf42c453dcc'
auth_token = 'b43a7372e4adf912d1f1862933588c4a'
client = Client(account_sid, auth_token)
twilio_whatsapp_number = 'whatsapp:‪+14155238886‬'
your_whatsapp_number = 'whatsapp:‪+40771167158‬'

# Bird inițializare
bird_x = 50
bird_y = SCREEN_HEIGHT // 2
bird_velocity = 0
gravity = 0.8
flap_strength = -10
max_velocity = 12

# Țevi
pipe_width = 60
initial_pipe_gap = 150
pipe_gap = initial_pipe_gap
pipes = []
pipe_speed = 3
level = 1
difficulty_factor = 5
min_pipe_gap = 60

# Variabile pentru detecția mâinii
last_hand_y = None
last_flap_time = 0
flap_visual_power = 0
flap_cooldown = 0.2  # Ajustat pentru control fluid
flap_threshold = 10  # Ajustat pentru detecție mai precisă

# Variabile pentru bonus
bonus_active = False
bonus_start_time = 0
bonus_duration = 3
particles = []

# Camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
camera_height = 480

# Verificăm camera
if not cap.isOpened():
    print("CRITIC: Camera nu poate fi deschisă (index 0)! Încercăm index 1...")
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("CRITIC: Nici index 1 nu funcționează! Verifică dacă camera e conectată.")
        print("Pași: 1. Conectează camera. 2. Verifică în Device Manager. 3. Încearcă alt index (ex. 2).")
        pygame.quit()
        exit()
else:
    print("Camera deschisă cu succes.")

# Testăm fluxul camerei
print("Testăm fluxul camerei timp de 5 secunde. Mișcă mâna în fața camerei.")
start_test = time.time()
while time.time() - start_test < 5:
    ret, frame = cap.read()
    if not ret:
        print("CRITIC: Nu se poate citi cadrul! Camera e defectă sau ocupată.")
        cap.release()
        pygame.quit()
        exit()
    cv2.imshow("Test Camera", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()
print("Test cameră încheiat. Dacă nu ai văzut imaginea, camera nu funcționează.")

# Clasă pentru particulele de artificii
class Particle:
    def _init_(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(3, 6)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.5, 1.5)
        self.start_time = time.time()
        self.color = random.choice([PINK, BLUE])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        elapsed = time.time() - self.start_time
        self.life -= elapsed / 60
        self.start_time = time.time()
        return self.life > 0

    def draw(self, screen):
        if self.life > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

# Funcție pentru crearea exploziei de artificii
def create_fireworks():
    global particles
    particles = []
    num_particles = 50
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2
    for _ in range(num_particles):
        particles.append(Particle(center_x, center_y))

# Funcția pentru detectarea mișcării mâinii
def detect_hand_movement(cap):
    try:
        if not cap.isOpened():
            print("DEBUG: Camera nu este deschisă.")
            return None, None
        ret, frame = cap.read()
        if not ret:
            print("DEBUG: Nu se poate citi cadrul de la cameră.")
            return None, None
        frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Interval HSV optimizat pentru detecția pielii
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            print("DEBUG: Niciun contur detectat.")
            return None, frame
        max_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(max_contour)
        min_contour_area = 1000  # Ajustat pentru detecție mai robustă
        if area < min_contour_area:
            print(f"DEBUG: Contur prea mic: {area}")
            return None, frame
        M = cv2.moments(max_contour)
        if M["m00"] == 0:
            print("DEBUG: Momentul conturului este zero.")
            return None, frame
        cY = int(M["m01"] / M["m00"])
        cv2.drawContours(frame, [max_contour], -1, (0, 255, 0), 2)
        cv2.circle(frame, (int(M["m10"] / M["m00"]), cY), 5, (0, 0, 255), -1)
        print(f"DEBUG: Mână detectată: y={cY}, area={area}")
        return cY, frame
    except Exception as e:
        print(f"DEBUG: Eroare în detect_hand_movement: {e}")
        return None, frame

# Ecran de calibrare
def calibrate_gestures(cap):
    calibrating = True
    start_time = time.time()
    font = pygame.font.Font(None, 30)
    last_hand_y = None
    flap_count = 0
    while calibrating and time.time() - start_time < 15:
        screen.fill(BLACK)
        text = font.render("Mișcă mâna sus-jos rapid sau apasă SPACE. Apasă Q să începi.", True, WHITE)
        screen.blit(text, (20, 20))
        hand_y, frame = detect_hand_movement(cap)
        status = "Mână nedetectată"
        flap_detected = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cv2.destroyAllWindows()
                cap.release()
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    calibrating = False
                elif event.key == pygame.K_SPACE:
                    flap_count += 1
                    status = "Zbor detectat prin SPACE!"
                    flap_detected = True
                    print("DEBUG: SPACE detectat în calibrare")
        if hand_y is not None and not flap_detected:
            status = f"Mână detectată: y={hand_y}"
            if last_hand_y is not None and abs(hand_y - last_hand_y) > flap_threshold:
                status += " | Zbor detectat prin mână!"
                flap_count += 1
                print(f"DEBUG: Zbor detectat prin mână în calibrare: displacement={abs(hand_y - last_hand_y)}")
        screen.blit(font.render(status, True, PINK), (20, 60))
        screen.blit(font.render(f"Flaps detectate: {flap_count}", True, PINK), (20, 100))
        if frame is not None:
            cv2.imshow("Calibrare Camera", frame)
        last_hand_y = hand_y
        pygame.display.update()
        clock.tick(60)
    cv2.destroyAllWindows()
    print(f"Calibrare încheiată. Flaps detectate: {flap_count}")
    return True

# Baza de date
def create_database():
    try:
        conn = sqlite3.connect("flappybird.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS high_scores (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT,
                     score INTEGER,
                     date TEXT,
                     time INTEGER)''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Eroare la crearea bazei de date: {e}")
    finally:
        conn.close()

def create_player_stats_table():
    try:
        conn = sqlite3.connect("flappybird.db")
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS player_stats")
        c.execute('''CREATE TABLE IF NOT EXISTS player_stats (
                     name TEXT PRIMARY KEY,
                     games_played INTEGER,
                     total_score INTEGER,
                     best_score INTEGER)''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Eroare la crearea tabelului player_stats: {e}")
    finally:
        conn.close()

create_database()
create_player_stats_table()

def save_high_score(name, score, time_spent):
    try:
        conn = sqlite3.connect("flappybird.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Salvăm: name={name}, score={score}, date={now}, time={time_spent}")
        c.execute("INSERT INTO high_scores (name, score, date, time) VALUES (?, ?, ?, ?)",
                  (name, score, now, time_spent))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Eroare la salvarea scorului: {e}")
    finally:
        conn.close()

def update_player_stats(name, score):
    try:
        conn = sqlite3.connect("flappybird.db")
        c = conn.cursor()
        c.execute("SELECT * FROM player_stats WHERE name = ?", (name,))
        result = c.fetchone()
        if result:
            games_played = result[1] + 1
            total_score = result[2] + score
            best_score = max(result[3], score)
            c.execute('''UPDATE player_stats 
                         SET games_played = ?, total_score = ?, best_score = ? 
                         WHERE name = ?''', (games_played, total_score, best_score, name))
        else:
            c.execute("INSERT INTO player_stats (name, games_played, total_score, best_score) VALUES (?, ?, ?, ?)",
                      (name, 1, score, score))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Eroare la actualizarea statisticilor: {e}")
    finally:
        conn.close()

def display_high_scores():
    try:
        conn = sqlite3.connect("flappybird.db")
        c = conn.cursor()
        c.execute("SELECT name, score, date, time FROM high_scores ORDER BY score DESC LIMIT 5")
        top_scores = c.fetchall()
        print("\n🏆 Top 5 scoruri:")
        for i, (name, score, date, duration) in enumerate(top_scores):
            print(f"{i + 1}. {name} - {score} puncte - {date} - {duration} secunde")
    except sqlite3.Error as e:
        print(f"Eroare la afișarea scorurilor: {e}")
    finally:
        conn.close()

def display_all_players_stats():
    try:
        conn = sqlite3.connect("flappybird.db")
        c = conn.cursor()
        c.execute("SELECT name, games_played, total_score, best_score FROM player_stats")
        players = c.fetchall()
        if players:
            print("📊 Statistici pentru toți jucătorii:")
            for player in players:
                print(f"{player[0]}: Jocuri jucate: {player[1]}, Scor total: {player[2]}, Cel mai bun scor: {player[3]}")
        else:
            print("Nu există statistici pentru niciun jucător.")
    except sqlite3.Error as e:
        print(f"Eroare la afișarea statisticilor: {e}")
    finally:
        conn.close()

def get_player_name():
    name = ""
    font = pygame.font.Font(None, 40)
    active = True
    input_box_width = 300
    input_box_height = 40
    input_rect = pygame.Rect(0, 0, input_box_width, input_box_height)
    input_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
    while active:
        screen.blit(menu_img, (0, 0))
        title_text = font.render("Scrie-ți numele și apasă Enter:", True, PINK)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(title_text, title_rect)
        pygame.draw.rect(screen, PINK, input_rect, 2)
        name_surface = font.render(name, True, WHITE)
        name_rect = name_surface.get_rect(center=input_rect.center)
        screen.blit(name_surface, name_rect)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                cap.release()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip() != "":
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 12:
                    name += event.unicode
    return name.strip()

def select_difficulty():
    global initial_pipe_gap, pipe_speed, difficulty_factor
    font = pygame.font.Font(None, 40)
    selecting = True
    while selecting:
        screen.blit(menu_img, (0, 0))
        screen.blit(font.render("1. Ușor", True, PINK), (150, 200))
        screen.blit(font.render("2. Mediu", True, PINK), (150, 250))
        screen.blit(font.render("3. Greu", True, PINK), (150, 300))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                cap.release()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    initial_pipe_gap = 150
                    pipe_speed = 3
                    difficulty_factor = 5
                    selecting = False
                elif event.key == pygame.K_2:
                    initial_pipe_gap = 120
                    pipe_speed = 4
                    difficulty_factor = 7
                    selecting = False
                elif event.key == pygame.K_3:
                    initial_pipe_gap = 100
                    pipe_speed = 5
                    difficulty_factor = 10
                    selecting = False

def create_pipe():
    pipe_height = random.randint(100, 400)
    pipes.append([SCREEN_WIDTH, pipe_height])

def save_last_played():
    try:
        with open("last_played.txt", "w") as f:
            f.write(str(time.time()))
    except Exception as e:
        print(f"Eroare la salvarea timpului de joc: {e}")

def check_last_played(name, score):
    if not os.path.exists("last_played.txt"):
        print("Fișierul last_played.txt nu există. Se creează acum.")
        save_last_played()
        return
    try:
        with open("last_played.txt", "r") as f:
            last_time = float(f.read())
        now = time.time()
        time_passed = now - last_time
        if time_passed >= 300:
            print("Au trecut mai mult de 5 minute. Notificările WhatsApp sunt dezactivate temporar.")
        else:
            print(f"Mai sunt {int((300 - time_passed) // 60)} minute până la notificare.")
    except Exception as e:
        print(f"Eroare la verificarea timpului de joc: {e}")
        save_last_played()

def send_whatsapp_message(name, score, message_type="game_over"):
    print(f"Notificările WhatsApp sunt dezactivate temporar din cauza limitei de 9 mesaje/zi.")
    print(f"Mesaj neexpediat ({message_type}): {name}, scor: {score}")

def ask_play_again():
    font = pygame.font.Font(None, 36)
    asking = True
    while asking:
        screen.blit(img_img, (0, 0))
        text1 = font.render("Apasă Enter pentru a juca din nou,", True, PINK)
        text2 = font.render("sau X pentru a ieși.", True, PINK)
        screen.blit(text1, (40, 250))
        screen.blit(text2, (100, 290))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
                if event.key == pygame.K_x:
                    return False

def show_highscores_screen():
    font = pygame.font.Font(None, 24)
    try:
        conn = sqlite3.connect("flappybird.db")
        c = conn.cursor()
        c.execute("SELECT name, score, date, time FROM high_scores ORDER BY score DESC LIMIT 5")
        top_scores = c.fetchall()
        showing = True
        while showing:
            screen.fill(WHITE)
            title = font.render("🏆 Top 5 Scoruri", True, PINK)
            screen.blit(title, (100, 50))
            for idx, (name, score, date, time_spent) in enumerate(top_scores):
                line1 = font.render(f"{idx + 1}. {name}: {score} pct", True, BLACK)
                screen.blit(line1, (30, 100 + idx * 60))
                line2 = font.render(f"{date}, {time_spent} sec", True, BLACK)
                screen.blit(line2, (30, 120 + idx * 60))
            screen.blit(font.render("Apasă SPACE pentru meniu", True, PINK), (50, 450))
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    showing = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    showing = False
    except sqlite3.Error as e:
        print(f"Eroare la afișarea scorurilor: {e}")
    finally:
        conn.close()

player_name = get_player_name()
select_difficulty()
pipe_gap = initial_pipe_gap
last_bonus_score = -10

# Rulăm calibrarea
if not calibrate_gestures(cap):
    pygame.quit()
    cap.release()
    exit()

while True:
    check_last_played(player_name, 0)
    bird_x = 50
    bird_y = SCREEN_HEIGHT // 2
    bird_velocity = 0
    pipes = []
    create_pipe()
    score = 0
    level = 1
    pipe_gap = initial_pipe_gap
    start_time = time.time()
    running = True
    last_hand_y = None
    bonus_active = False
    particles = []
    last_bonus_score = -10
    last_flap_time = 0
    control_status = "Fără input"

    while running:
        screen.blit(background_img, (0, 0))
        current_time = time.time()
        flap_triggered = False

        # Verificăm evenimentele (inclusiv tasta Space)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and current_time - last_flap_time > flap_cooldown:
                    bird_velocity = flap_strength
                    flap_visual_power = abs(flap_strength)
                    last_flap_time = current_time
                    flap_triggered = True
                    control_status = "Zbor: SPACE"
                    print(f"DEBUG: Zbor declanșat prin SPACE! velocity={bird_velocity}")

        # Detectăm poziția mâinii
        hand_y, frame = detect_hand_movement(cap)

        # Aplicăm gravitația în fiecare cadru
        bird_velocity += gravity
        print(f"DEBUG: Gravitație aplicată: velocity={bird_velocity}, bird_y={bird_y}")

        # Verificăm detecția mâinii dacă nu a fost declanșat zborul prin Space
        if not flap_triggered and hand_y is not None:
            if last_hand_y is not None and current_time - last_flap_time > flap_cooldown:
                displacement = abs(hand_y - last_hand_y)
                if displacement > flap_threshold:
                    flap_power = min(displacement * 0.4, abs(flap_strength))
                    bird_velocity = -flap_power
                    flap_visual_power = flap_power
                    last_flap_time = current_time
                    control_status = f"Zbor: Mână (disp={displacement:.2f})"
                    print(f"DEBUG: Zbor detectat prin mână! displacement={displacement:.2f}, power={flap_power:.2f}, velocity={bird_velocity}")

        last_hand_y = hand_y

        # Limităm viteza păsării
        bird_velocity = max(-max_velocity, min(max_velocity, bird_velocity))

        # Actualizăm poziția păsării
        bird_y += bird_velocity
        bird_y = max(0, min(bird_y, SCREEN_HEIGHT - 30))
        print(f"DEBUG: Poziție pasăre actualizată: bird_y={bird_y}")

        screen.blit(bird_img, (bird_x, bird_y))

        # Afișăm informații pentru debugging și instrucțiuni
        status = "Mână nedetectată" if hand_y is None else f"Hand Y: {hand_y:.1f}"
        screen.blit(score_font.render(status, True, WHITE), (10, 40))
        screen.blit(score_font.render("Apasă SPACE sau mișcă mâna pentru a zbura", True, WHITE), (10, 70))
        screen.blit(score_font.render(control_status, True, WHITE), (10, 100))

        # Afișăm fereastra camerei în timpul jocului pentru debugging
        if frame is not None:
            cv2.imshow("Camera Joc", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False

        for pipe in pipes[:]:
            pipe[0] -= pipe_speed
            pygame.draw.rect(screen, PINK, (pipe[0], 0, pipe_width, pipe[1]))
            pygame.draw.rect(screen, PINK, (pipe[0], pipe[1] + pipe_gap, pipe_width, SCREEN_HEIGHT))
            if (bird_x < pipe[0] + pipe_width and bird_x + 40 > pipe[0] and
                    (bird_y < pipe[1] or bird_y + 30 > pipe[1] + pipe_gap)):
                running = False
            if pipe[0] < -pipe_width:
                pipes.remove(pipe)
                create_pipe()
                score += 1
                if score % 10 == 0 and score != last_bonus_score:
                    bonus_active = True
                    bonus_start_time = time.time()
                    last_bonus_score = score
                    create_fireworks()
                if score % 5 == 0:
                    level += 1
                    pipe_gap = max(min_pipe_gap, pipe_gap - difficulty_factor)
                    print(f"Nivel: {level}, Pipe gap: {pipe_gap}")

        # Gestionăm efectul de bonus
        if bonus_active:
            particles = [p for p in particles if p.update()]
            for particle in particles:
                particle.draw(screen)
            bonus_text = bonus_font.render("Well Done! Keep Going!", True, PINK)
            bonus_rect = bonus_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(bonus_text, bonus_rect)
            if time.time() - bonus_start_time > bonus_duration:
                bonus_active = False
                particles = []

        screen.blit(score_font.render(f"Scor: {score}  Nivel: {level}", True, WHITE), (10, 10))

        # HUD pentru puterea gestului
        hud_bar_width = int(flap_visual_power * 10)
        hud_bar_width = min(hud_bar_width, 100)
        pygame.draw.rect(screen, BLUE, (SCREEN_WIDTH - 120, 10, hud_bar_width, 15))
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 120, 10, 100, 15), 2)

        pygame.display.update()
        clock.tick(60)

    end_time = time.time()
    time_spent = int(end_time - start_time)
    save_high_score(player_name, score, time_spent)
    update_player_stats(player_name, score)
    send_whatsapp_message(player_name, score, message_type="game_over")
    save_last_played()

    cv2.destroyAllWindows()  # Închidem fereastra camerei la sfârșitul jocului
    show_highscores_screen()
    if not ask_play_again():
        break

pygame.quit()
cap.release()
cv2.destroyAllWindows()
exit()
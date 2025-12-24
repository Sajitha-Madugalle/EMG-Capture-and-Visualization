import pygame
import os
import random
import sys
import socket
import struct
import threading
import collections
import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi, iirnotch, lfilter, lfilter_zi

# --- EMG CONFIGURATION ---
DEFAULT_PORT = 8888
SAMPLE_RATE = 25000.0   # 25 kSPS
VOLTAGE_REF = 1.65
ADC_MAX_VAL = 512.0
EMG_THRESHOLD = 0.3    # Default threshold (Adjustable)
JUMP_COOLDOWN = 200     # ms

# --- GAME CONFIGURATION ---
# Initial size
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SIGNAL_HEIGHT = 200
GAME_HEIGHT = SCREEN_HEIGHT - SIGNAL_HEIGHT

GRAVITY = 0.25
BIRD_JUMP = -6
PIPE_SPEED = 3
PIPE_GAP = 150
PIPE_FREQUENCY = 1500

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
PIPE_GREEN = (34, 139, 34)
BIRD_YELLOW = (255, 215, 0)
RED = (255, 0, 0)
PLOT_BG = (20, 20, 20)
PLOT_LINE = (0, 255, 0)
THRESH_LINE = (255, 255, 0)

class EMGHandler:
    def __init__(self, port=DEFAULT_PORT):
        self.port = port
        self.running = False
        self.current_envelope = 0.0
        self.lock = threading.Lock()
        
        # Filtering State
        self.notch_coeffs = []
        self.notch_zis = []
        self.init_notch_filters()
        
        self.bp_sos = None
        self.bp_zi = None
        self.init_bandpass_filter()
        
        self.lp_sos = None
        self.lp_zi = None
        self.init_lowpass_filter()

    def init_notch_filters(self):
        freqs = [50.0, 100.0, 150.0]
        quality_factor = 30.0
        for f in freqs:
            b, a = iirnotch(f, quality_factor, fs=SAMPLE_RATE)
            self.notch_coeffs.append((b, a))
            zi = lfilter_zi(b, a)
            self.notch_zis.append(zi)

    def init_bandpass_filter(self):
        low = 25.0
        high = 150.0
        nyquist = SAMPLE_RATE / 2.0
        # 4th order butterworth bandpass
        self.bp_sos = butter(4, [low/nyquist, high/nyquist], btype='bandpass', output='sos')
        self.bp_zi = sosfilt_zi(self.bp_sos)

    def init_lowpass_filter(self):
        cutoff = 5.0 # 5Hz envelope
        nyquist = SAMPLE_RATE / 2.0
        self.lp_sos = butter(2, cutoff/nyquist, btype='low', output='sos')
        self.lp_zi = sosfilt_zi(self.lp_sos)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', self.port))
        sock.settimeout(1.0)
        
        print(f"Listening for EMG on port {self.port}...")

        while self.running:
            try:
                data, _ = sock.recvfrom(4096)
                
                # Decode
                num_samples = len(data) // 2
                fmt = '<' + 'h' * num_samples
                values = struct.unpack(fmt, data)
                chunk = np.array(values, dtype=float)

                # 1. Notch Filter
                for i in range(len(self.notch_coeffs)):
                    b, a = self.notch_coeffs[i]
                    chunk, self.notch_zis[i] = lfilter(b, a, chunk, zi=self.notch_zis[i])

                # 2. Bandpass Filter
                if self.bp_sos is not None:
                    chunk, self.bp_zi = sosfilt(self.bp_sos, chunk, zi=self.bp_zi)

                # Convert to Voltage
                voltage_chunk = chunk * (VOLTAGE_REF / ADC_MAX_VAL)

                # 3. Envelope Detection (Rectify + Lowpass)
                rectified = np.abs(voltage_chunk)
                envelope_chunk, self.lp_zi = sosfilt(self.lp_sos, rectified, zi=self.lp_zi)

                # Update current max envelope in this chunk
                if len(envelope_chunk) > 0:
                    current_max = np.max(envelope_chunk)
                    with self.lock:
                        self.current_envelope = current_max

            except socket.timeout:
                continue
            except Exception as e:
                print(f"EMG Error: {e}")
        
        sock.close()

    def get_envelope(self):
        with self.lock:
            return self.current_envelope

class Bird:
    def __init__(self, game_height):
        self.x = 100
        self.y = game_height // 2
        self.velocity = 0
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Load Sprite
        try:
            image_path = os.path.join(os.path.dirname(__file__), "flappy_bird.png")
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except FileNotFoundError:
            print("Warning: flappy_bird.png not found, using fallback rect.")
            self.image = None

    def jump(self):
        self.velocity = BIRD_JUMP

    def move(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.y = int(self.y)

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.rect(screen, BIRD_YELLOW, self.rect)

class Pipe:
    def __init__(self, screen_width, game_height):
        self.x = screen_width
        self.width = 70
        # Constrain pipe height to current GAME_HEIGHT
        self.height = random.randint(50, max(50, game_height - PIPE_GAP - 50))
        self.passed = False
        self.game_height = game_height # Store for recalc if needed
        self.top_rect = pygame.Rect(self.x, 0, self.width, self.height)
        self.bottom_rect = pygame.Rect(self.x, self.height + PIPE_GAP, self.width, game_height - (self.height + PIPE_GAP))

    def move(self):
        self.x -= PIPE_SPEED
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

    def draw(self, screen):
        pygame.draw.rect(screen, PIPE_GREEN, self.top_rect)
        pygame.draw.rect(screen, PIPE_GREEN, self.bottom_rect)
        pygame.draw.rect(screen, BLACK, self.top_rect, 2)
        pygame.draw.rect(screen, BLACK, self.bottom_rect, 2)

    def collide(self, bird):
        return self.top_rect.colliderect(bird.rect) or self.bottom_rect.colliderect(bird.rect)

def draw_text(screen, text, size, x, y, color=BLACK):
    font = pygame.font.SysFont(None, size)
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def main():
    global SCREEN_WIDTH, SCREEN_HEIGHT, GAME_HEIGHT, SIGNAL_HEIGHT

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption('Flappy Bird EMG')
    clock = pygame.time.Clock()

    # Start EMG Handler
    emg_handler = EMGHandler()
    emg_handler.start()

    bird = Bird(GAME_HEIGHT)
    pipes = []
    score = 0
    font = pygame.font.SysFont(None, 40)
    
    last_pipe_time = pygame.time.get_ticks()
    last_jump_time = 0
    running = True
    game_active = True
    
    # Gain Variable
    emg_gain = 14.0
    
    # Signal Plot Buffer
    plot_buffer = collections.deque([0.0] * SCREEN_WIDTH, maxlen=SCREEN_WIDTH)

    # Main Loop
    while running:
        clock.tick(60)
        
        # --- DRAW BACKGROUNDS ---
        # Game Area
        pygame.draw.rect(screen, SKY_BLUE, (0, 0, SCREEN_WIDTH, GAME_HEIGHT))
        # Signal Area
        pygame.draw.rect(screen, PLOT_BG, (0, GAME_HEIGHT, SCREEN_WIDTH, SIGNAL_HEIGHT))
        
        current_time = pygame.time.get_ticks()
        envelope = emg_handler.get_envelope()

        # Input Handling
        
        # 1. Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # RESIZE EVENT
            if event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                if SCREEN_HEIGHT < 300: SCREEN_HEIGHT = 300
                if SCREEN_WIDTH < 300: SCREEN_WIDTH = 300
                
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                
                # Recalculate Layout
                # Keep fixed signal height unless window starts getting too small
                if SCREEN_HEIGHT < 400:
                    SIGNAL_HEIGHT = 100
                else:
                    SIGNAL_HEIGHT = 200
                    
                GAME_HEIGHT = SCREEN_HEIGHT - SIGNAL_HEIGHT
                
                # Resize Plot Buffer (preserve old data if possible)
                new_buffer = collections.deque(list(plot_buffer), maxlen=SCREEN_WIDTH)
                plot_buffer = new_buffer
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    last_jump_time = 0 # Allow instant jump
                    bird.jump() # Direct jump
                if event.key == pygame.K_r and not game_active:
                     # Reset game
                    bird = Bird(GAME_HEIGHT)
                    pipes = []
                    score = 0
                    game_active = True
                    last_pipe_time = current_time
                # --- GAIN CONTROL ---
                if event.key == pygame.K_UP:
                    emg_gain += 0.5
                if event.key == pygame.K_DOWN:
                    emg_gain = max(0.1, emg_gain - 0.5)

        # 2. EMG Input
        # Apply Gain
        scaled_envelope = envelope * emg_gain
        plot_buffer.append(scaled_envelope)
        
        if scaled_envelope > EMG_THRESHOLD:
            if current_time - last_jump_time > JUMP_COOLDOWN:
                if game_active:
                    bird.jump()
                last_jump_time = current_time

        if game_active:
            # Bird
            bird.move()
            bird.draw(screen)

            # Pipes
            if current_time - last_pipe_time > PIPE_FREQUENCY:
                pipes.append(Pipe(SCREEN_WIDTH, GAME_HEIGHT))
                last_pipe_time = current_time

            pipes_to_remove = []
            for pipe in pipes:
                pipe.move()
                pipe.draw(screen)
                if pipe.collide(bird):
                    game_active = False
                if pipe.x + pipe.width < bird.x and not pipe.passed:
                    pipe.passed = True
                    score += 1
                if pipe.x < -pipe.width:
                    pipes_to_remove.append(pipe)
            for pipe in pipes_to_remove:
                pipes.remove(pipe)

            # Ground/Ceiling
            if bird.y >= GAME_HEIGHT - bird.height or bird.y < 0:
                game_active = False

            # Score
            score_surface = font.render(str(score), True, WHITE)
            screen.blit(score_surface, (SCREEN_WIDTH // 2, 50))
            
        else:
            # Game Over
            draw_text(screen, "Game Over", 80, SCREEN_WIDTH//2 - 150, GAME_HEIGHT//2 - 50)
            draw_text(screen, f"Score: {score}", 60, SCREEN_WIDTH//2 - 80, GAME_HEIGHT//2 + 20)
            draw_text(screen, "Press 'R' to Restart", 40, SCREEN_WIDTH//2 - 120, GAME_HEIGHT//2 + 80)

        # --- DRAW SIGNAL PLOT ---
        # 1. Points
        points = []
        
        
        for x, val in enumerate(plot_buffer):
            # Scale val to fit in SIGNAL_HEIGHT (0 to 2V approx range covers most)
            # Origin is bottom-left of plot area: (x, SCREEN_HEIGHT)
            # Subtract value: (x, SCREEN_HEIGHT - (val * scale))
            plot_y = SCREEN_HEIGHT - min(int(val * 100), SIGNAL_HEIGHT - 10) 
            points.append((x, plot_y))
            
        if len(points) > 1:
            pygame.draw.lines(screen, PLOT_LINE, False, points, 2)
            
        # 2. Threshold Line
        thresh_h = min(int(EMG_THRESHOLD * 100), SIGNAL_HEIGHT - 10)
        thresh_y = SCREEN_HEIGHT - thresh_h
        pygame.draw.line(screen, THRESH_LINE, (0, thresh_y), (SCREEN_WIDTH, thresh_y), 2)
        
        # 3. Text Info
        draw_text(screen, f"EMG: {scaled_envelope:.2f}V", 25, 10, GAME_HEIGHT + 10, color=WHITE)
        draw_text(screen, f"Gain: x{emg_gain:.1f}", 25, 10, GAME_HEIGHT + 35, color=WHITE)
        draw_text(screen, "Threshold", 18, SCREEN_WIDTH - 80, thresh_y - 20, color=THRESH_LINE)

        pygame.display.flip()

    emg_handler.running = False
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
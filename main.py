import pygame
import random
import time
import sys
import math
import socket
import threading
import os

# --- Android-Specific Setup ---
IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ

if IS_ANDROID:
    from jnius import autoclass
    def get_multicast_lock():
        """Android needs an explicit lock to hear UDP Broadcasts."""
        try:
            Context = autoclass('android.content.Context')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            wifi = activity.getSystemService(Context.WIFI_SERVICE)
            multicast_lock = wifi.createMulticastLock("fakermip_lock")
            multicast_lock.acquire()
            print("Android Multicast Lock Acquired")
        except Exception as e:
            print(f"Could not acquire Multicast Lock: {e}")
    get_multicast_lock()

# --- Configuration ---
# Desktop defaults
WINDOW_WIDTH = 700 
WINDOW_HEIGHT = 600 

NORMAL_IMAGE_PATH = 'fakeMIP-normal.png' 
DANCE_IMAGE_PATH = 'fakeMIP-dancing.png' 

# Sound Categories
DANCE_SOUNDS = ['MiPDance_1.wav', 'MiPDance_2.wav'] 
IDLE_SOUNDS = ['MiP_yapping2self.wav', 'MiP_hahahamip.wav', 'MiP_yippee.wav', 'MiP_mip1.wav', 'MiP_mip3.wav']
STARTUP_SOUND = 'MiP_mipthenoh.wav'
POWER_DOWN_SOUND = 'MiP_powerdown.wav'
SAD_SOUNDS = ['MiP_ohno.wav', 'MiP_aww.wav']

# Networking Setup
UDP_PORT = 2014 
BROADCAST_IP = "255.255.255.255"

# --- HUMAN-READABLE IDENTITY ---
NAMES = ['Jarold', 'Carl', 'Timothy', 'Bartholomew', 'Garry', 'Sprocket', 'Rusty', 'Zippy']
MY_NAME = f"MiP_{random.choice(NAMES)}_{random.randint(100, 999)}"

# Frequency Tweaks
CHANCE_TO_DANCE = 0.001 
DANCE_COOLDOWN_SECONDS = 30 

# Global flags for network communication
network_trigger = False
network_sad_trigger = False

def network_listener():
    """Listens for other MiPs dancing or leaving."""
    global network_trigger, network_sad_trigger
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to empty string to listen on all available interfaces
    sock.bind(('', UDP_PORT))
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode()
            sender_name, command = message.split(":")
            
            if sender_name != MY_NAME:
                if command == "DANCE":
                    print(f"{MY_NAME} heard {sender_name} dancing! Joining in 1 second...")
                    time.sleep(1)
                    network_trigger = True
                elif command == "POWER_OFF":
                    print(f"{MY_NAME} heard {sender_name} leave. So sad...")
                    network_sad_trigger = True
        except:
            pass

def send_signal(command):
    """Broadcasts a command (DANCE or POWER_OFF)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f"{MY_NAME}:{command}"
        sock.sendto(message.encode(), (BROADCAST_IP, UDP_PORT))
        sock.close()
    except Exception as e:
        print(f"Network error: {e}")

def main():
    global network_trigger, network_sad_trigger
    pygame.init()
    pygame.mixer.init()

    # Handling Screen Size: PC vs Android
    if IS_ANDROID:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        current_w, current_h = screen.get_size()
    else:
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        current_w, current_h = WINDOW_WIDTH, WINDOW_HEIGHT

    pygame.display.set_caption(f"FakerMiP - {MY_NAME}") 

    # Start network thread
    threading.Thread(target=network_listener, daemon=True).start()

    try:
        # Load and scale images based on current screen size
        raw_normal = pygame.image.load(NORMAL_IMAGE_PATH).convert_alpha()
        normal_img = pygame.transform.scale(raw_normal, (current_w, current_h)) 
        raw_dance = pygame.image.load(DANCE_IMAGE_PATH).convert_alpha()
        base_dance_img = pygame.transform.scale(raw_dance, (current_w, current_h)) 
        
        # Load Sounds
        dance_sfx = [pygame.mixer.Sound(s) for s in DANCE_SOUNDS] 
        idle_sfx = [pygame.mixer.Sound(s) for s in IDLE_SOUNDS]
        startup_sfx = pygame.mixer.Sound(STARTUP_SOUND)
        powerdown_sfx = pygame.mixer.Sound(POWER_DOWN_SOUND)
        sad_sfx = [pygame.mixer.Sound(s) for s in SAD_SOUNDS]
    except pygame.error as e:
        print(f"Error loading files: {e}")
        return

    startup_sfx.play()
    running = True
    is_dancing = False
    clock = pygame.time.Clock()
    last_idle_time = time.time()
    next_idle_delay = random.uniform(1, 20)
    last_dance_finish_time = 0 

    try:
        while running:
            current_time = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Input Handling: Space for PC, Screen Tap for Android
                is_input_trigger = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    is_input_trigger = True
                elif event.type == pygame.MOUSEBUTTONDOWN: # Tapping screen
                    is_input_trigger = True

                if is_input_trigger and not is_dancing:
                    is_dancing = True
                    send_signal("DANCE")

            # Respond to network dance
            if network_trigger and not is_dancing:
                is_dancing = True
                network_trigger = False

            # Respond to network departure
            if network_sad_trigger:
                if not pygame.mixer.get_busy():
                    random.choice(sad_sfx).play()
                    network_sad_trigger = False
                else:
                    network_sad_trigger = False

            if not is_dancing:
                screen.fill((0, 0, 0))
                # Breathing animation
                idle_pitch = 1.0 + (math.sin(current_time * 2) * 0.02)
                h_now = int(current_h * idle_pitch)
                idle_img = pygame.transform.scale(normal_img, (current_w, h_now))
                idle_rect = idle_img.get_rect(center=(current_w//2, current_h//2))
                screen.blit(idle_img, idle_rect.topleft)
                
                # Idle SFX
                if current_time - last_idle_time > next_idle_delay:
                    if not pygame.mixer.get_busy():
                        random.choice(idle_sfx).play()
                        last_idle_time = current_time
                        next_idle_delay = random.uniform(1, 20)

                # Random Dance with Cooldown
                if current_time - last_dance_finish_time > DANCE_COOLDOWN_SECONDS:
                    if random.random() < CHANCE_TO_DANCE:
                        is_dancing = True
                        send_signal("DANCE")
            
            if is_dancing:
                network_trigger = False 
                selected_sound = random.choice(dance_sfx) 
                channel = selected_sound.play(loops=2) 
                start_time = time.time()
                
                while channel.get_busy():
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            channel.stop()
                            running = False
                            break
                    if not running: break
                    
                    t = (time.time() - start_time) * 8
                    w_factor = 0.9 + (math.sin(t) * 0.1) 
                    h_factor = 0.95 + (math.cos(t * 1.2) * 0.05)
                    roll = math.sin(t * 0.8) * 5 
                    
                    scaled = pygame.transform.scale(base_dance_img, (int(current_w * w_factor), int(current_h * h_factor)))
                    final = pygame.transform.rotate(scaled, roll)
                    rect = final.get_rect(center=(current_w//2 + (math.sin(t) * 15), current_h//2))

                    screen.fill((0, 0, 0))
                    screen.blit(final, rect.topleft)
                    pygame.display.flip()
                    clock.tick(60)
                
                if running:
                    if random.random() < 0.3: random.choice(sad_sfx).play()
                    screen.fill((0, 0, 0))
                    screen.blit(normal_img, (0, 0))
                    pygame.display.flip()
                    time.sleep(2) 
                    last_dance_finish_time = time.time()
                    last_idle_time = time.time()
                    next_idle_delay = random.uniform(1, 20)
                    is_dancing = False

            pygame.display.flip()
            clock.tick(60) 

    except KeyboardInterrupt:
        pass 
    
    # Send POWER_OFF before shutting down
    send_signal("POWER_OFF")
    
    print("Powering down...")
    screen.fill((0, 0, 0)); screen.blit(normal_img, (0, 0)); pygame.display.flip()
    pd_channel = powerdown_sfx.play()
    while pd_channel.get_busy(): pygame.time.delay(100)
    pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import HandLandmarkerOptions
import numpy as np
import random
import math
import time
import sys
import urllib.request
import os
import colorsys

# ─── Model Setup ─────────────────────────────────────────────────────────────
MODEL_PATH = "hand_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

if not os.path.exists(MODEL_PATH):
    print("📥 Downloading hand landmarker model (~9MB)...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("✅ Model downloaded!")

# ─── Camera ──────────────────────────────────────────────────────────────────
def open_camera():
    for idx in [0, 1]:
        for backend in [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]:
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"✅ Camera opened (index={idx})")
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    return cap
                cap.release()
    print("\n❌ Could not open camera.")
    print("   → System Settings → Privacy & Security → Camera → enable Terminal")
    sys.exit(1)

# ─── Detector ────────────────────────────────────────────────────────────────
base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
options = HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
    running_mode=vision.RunningMode.VIDEO
)
detector = vision.HandLandmarker.create_from_options(options)

# ─── Constants ───────────────────────────────────────────────────────────────
CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]

# Finger groups: thumb, index, middle, ring, pinky
FINGER_GROUPS = {
    'thumb':  [(0,1),(1,2),(2,3),(3,4)],
    'index':  [(0,5),(5,6),(6,7),(7,8)],
    'middle': [(0,9),(9,10),(10,11),(11,12)],
    'ring':   [(0,13),(13,14),(14,15),(15,16)],
    'pinky':  [(0,17),(17,18),(18,19),(19,20)],
    'palm':   [(5,9),(9,13),(13,17)],
}

FINGERTIPS = [4, 8, 12, 16, 20]
FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# ─── Premium Color Palette ───────────────────────────────────────────────────
# Each finger gets its own gradient color scheme (HSL-based)
def hsl_to_bgr(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h/360, l, s)
    return (int(b*255), int(g*255), int(r*255))

FINGER_COLORS = {
    'thumb':  [hsl_to_bgr(30, 1.0, 0.6),  hsl_to_bgr(45, 1.0, 0.7)],   # Warm amber
    'index':  [hsl_to_bgr(170, 1.0, 0.5),  hsl_to_bgr(190, 1.0, 0.65)], # Cyan/Teal
    'middle': [hsl_to_bgr(270, 0.9, 0.6),  hsl_to_bgr(290, 1.0, 0.7)],  # Purple
    'ring':   [hsl_to_bgr(340, 1.0, 0.55), hsl_to_bgr(0, 1.0, 0.65)],   # Rose/Red
    'pinky':  [hsl_to_bgr(100, 0.9, 0.5),  hsl_to_bgr(130, 1.0, 0.6)],  # Green
    'palm':   [hsl_to_bgr(210, 0.8, 0.5),  hsl_to_bgr(230, 0.9, 0.6)],  # Blue
}

ACCENT_CYAN   = hsl_to_bgr(185, 1.0, 0.55)
ACCENT_PURPLE = hsl_to_bgr(270, 0.9, 0.6)
ACCENT_AMBER  = hsl_to_bgr(40, 1.0, 0.6)
ACCENT_ROSE   = hsl_to_bgr(345, 1.0, 0.6)
ACCENT_GREEN  = hsl_to_bgr(150, 0.9, 0.5)
TEXT_PRIMARY   = (240, 240, 245)
TEXT_SECONDARY = (160, 165, 175)
TEXT_DIM       = (90, 95, 105)
PANEL_BG       = (20, 20, 25)

GESTURE_EMOJI = {
    "FIST": "✊",
    "OPEN HAND": "🖐️",
    "PEACE": "✌️",
    "POINTING": "☝️",
    "PINKY": "🤙",
    "THUMBS UP": "👍",
}

# ─── Particle System ─────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color, size_range=(1,4), speed_range=(1.0,4.5)):
        self.x, self.y = float(x), float(y)
        angle = random.uniform(0, 2*math.pi)
        speed = random.uniform(*speed_range)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.03, 0.08)
        self.size = random.randint(*size_range)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.06
        self.vx *= 0.98
        self.life -= self.decay

    def draw(self, canvas):
        if self.life <= 0:
            return
        alpha = self.life ** 1.5  # Non-linear fade for smoother disappearance
        c = tuple(int(ch * alpha) for ch in self.color)
        px, py = int(self.x), int(self.y)
        if 0 <= px < canvas.shape[1] and 0 <= py < canvas.shape[0]:
            cv2.circle(canvas, (px, py), self.size, c, -1)
            # Soft glow around particle
            if self.size > 2:
                glow_c = tuple(int(ch * alpha * 0.3) for ch in self.color)
                cv2.circle(canvas, (px, py), self.size + 3, glow_c, -1)

particles = []
TRAIL_LEN = 18
trails = {i: [] for i in range(10)}

# ─── Smooth value tracker ────────────────────────────────────────────────────
class SmoothValue:
    def __init__(self, initial=0, smoothing=0.15):
        self.value = initial
        self.target = initial
        self.smoothing = smoothing

    def update(self, target):
        self.target = target
        self.value += (self.target - self.value) * self.smoothing
        return self.value

smooth_fps = SmoothValue(0, 0.1)

# ─── Drawing Helpers ─────────────────────────────────────────────────────────
def lerp_color(c1, c2, t):
    """Linearly interpolate between two BGR colors."""
    t = max(0, min(1, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

def glow_line(canvas, p1, p2, color, t=2, glow_layers=4):
    """Draw a line with layered glow effect."""
    for i in range(glow_layers, 0, -1):
        alpha = (i / glow_layers) * 0.5
        fade = tuple(int(c * alpha) for c in color)
        cv2.line(canvas, p1, p2, fade, t + i * 3, cv2.LINE_AA)
    cv2.line(canvas, p1, p2, color, t, cv2.LINE_AA)
    # Bright core
    core = tuple(min(255, int(c * 1.3)) for c in color)
    cv2.line(canvas, p1, p2, core, max(1, t - 1), cv2.LINE_AA)

def glow_circle(canvas, center, r, color, pulse=0):
    """Draw a circle with pulsating glow."""
    pr = r + int(pulse * 3)
    for i in range(5, 0, -1):
        alpha = (i / 5) * 0.4
        fade = tuple(int(c * alpha) for c in color)
        cv2.circle(canvas, center, pr + i * 3, fade, 2, cv2.LINE_AA)
    cv2.circle(canvas, center, pr, color, -1, cv2.LINE_AA)
    # White highlight dot
    cv2.circle(canvas, (center[0]-2, center[1]-2), max(1, pr//3), (255,255,255), -1, cv2.LINE_AA)

def draw_rounded_rect(img, pt1, pt2, color, radius=12, thickness=-1, alpha=0.7):
    """Draw a rounded rectangle with optional transparency."""
    overlay = img.copy()
    x1, y1 = pt1
    x2, y2 = pt2
    # Draw filled rounded rect using multiple shapes
    cv2.rectangle(overlay, (x1+radius, y1), (x2-radius, y2), color, thickness)
    cv2.rectangle(overlay, (x1, y1+radius), (x2, y2-radius), color, thickness)
    cv2.circle(overlay, (x1+radius, y1+radius), radius, color, thickness)
    cv2.circle(overlay, (x2-radius, y1+radius), radius, color, thickness)
    cv2.circle(overlay, (x1+radius, y2-radius), radius, color, thickness)
    cv2.circle(overlay, (x2-radius, y2-radius), radius, color, thickness)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

def puttext(img, s, pos, scale, color, thick=2, font=cv2.FONT_HERSHEY_SIMPLEX):
    """Draw text with shadow."""
    cv2.putText(img, s, (pos[0]+1, pos[1]+1), font, scale, (0,0,0), thick+2, cv2.LINE_AA)
    cv2.putText(img, s, pos, font, scale, color, thick, cv2.LINE_AA)

def puttext_glow(img, s, pos, scale, color, thick=2, font=cv2.FONT_HERSHEY_SIMPLEX):
    """Draw text with colored glow."""
    glow = tuple(int(c * 0.3) for c in color)
    for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1),(0,-2),(0,2),(-2,0),(2,0)]:
        cv2.putText(img, s, (pos[0]+dx, pos[1]+dy), font, scale, glow, thick+3, cv2.LINE_AA)
    cv2.putText(img, s, (pos[0]+1, pos[1]+1), font, scale, (0,0,0), thick+1, cv2.LINE_AA)
    cv2.putText(img, s, pos, font, scale, color, thick, cv2.LINE_AA)

# ─── Gesture Detection ──────────────────────────────────────────────────────
def gesture(pts):
    up = lambda tip, mid: pts[tip][1] < pts[mid][1]
    i, m, r, p = up(8,6), up(12,10), up(16,14), up(20,18)
    thumb_out = abs(pts[4][0]-pts[0][0]) > 60
    fingers = sum([i, m, r, p])
    if fingers == 0 and not thumb_out: return "FIST"
    if fingers == 4 and thumb_out:     return "OPEN HAND"
    if i and m and not r and not p:    return "PEACE"
    if i and not m and not r and not p:return "POINTING"
    if not i and not m and not r and p:return "PINKY"
    if thumb_out and not i and not m:  return "THUMBS UP"
    return ""

def count_fingers(pts):
    up = lambda tip, mid: pts[tip][1] < pts[mid][1]
    thumb_out = abs(pts[4][0]-pts[0][0]) > 60
    return sum([thumb_out, up(8,6), up(12,10), up(16,14), up(20,18)])

def get_hand_angle(pts):
    """Get wrist rotation angle."""
    dx = pts[9][0] - pts[0][0]
    dy = pts[9][1] - pts[0][1]
    return math.degrees(math.atan2(dy, dx))

# ─── HUD Drawing ─────────────────────────────────────────────────────────────
def draw_hud_panel(img, x, y, w, panel_h, title, value, color, icon_char=""):
    """Draw a sleek HUD info panel."""
    draw_rounded_rect(img, (x, y), (x+w, y+panel_h), PANEL_BG, radius=8, alpha=0.75)
    # Accent bar on left
    cv2.rectangle(img, (x, y+6), (x+3, y+panel_h-6), color, -1)
    # Title
    puttext(img, title, (x+14, y+20), 0.4, TEXT_SECONDARY, 1)
    # Value
    puttext(img, str(value), (x+14, y+panel_h-10), 0.65, color, 2)

def draw_status_bar(img, h, w, fps, n_hands, n_particles, dark_mode, show_particles, show_grid, show_distances):
    """Draw the top status bar."""
    # Top bar background
    draw_rounded_rect(img, (10, 8), (w-10, 52), PANEL_BG, radius=10, alpha=0.7)

    # Title
    puttext_glow(img, "HAND VIZ PRO", (24, 38), 0.6, ACCENT_CYAN, 2)

    # Status pills
    pill_x = 220
    statuses = [
        (f"FPS {fps:.0f}", ACCENT_GREEN if fps > 24 else ACCENT_ROSE),
        (f"HANDS {n_hands}", ACCENT_CYAN if n_hands > 0 else TEXT_DIM),
    ]
    if show_particles:
        statuses.append((f"PARTICLES {n_particles}", ACCENT_PURPLE))

    for label, color in statuses:
        tw = len(label) * 11 + 16
        draw_rounded_rect(img, (pill_x, 16), (pill_x+tw, 44), (35,35,40), radius=6, alpha=0.8)
        puttext(img, label, (pill_x+8, 36), 0.4, color, 1)
        pill_x += tw + 8

    # Mode indicators on right
    rx = w - 30
    modes = []
    if dark_mode:
        modes.append(("DARK", ACCENT_PURPLE))
    else:
        modes.append(("LIGHT", ACCENT_AMBER))
    if show_particles:
        modes.append(("PRTCL", ACCENT_CYAN))
    if show_grid:
        modes.append(("GRID", ACCENT_GREEN))
    if show_distances:
        modes.append(("DIST", ACCENT_ROSE))

    for label, color in reversed(modes):
        tw = len(label) * 9 + 14
        draw_rounded_rect(img, (rx-tw, 16), (rx, 44), (35,35,40), radius=6, alpha=0.8)
        puttext(img, label, (rx-tw+7, 36), 0.35, color, 1)
        rx -= tw + 6

def draw_bottom_bar(img, h, w, show_help):
    """Draw bottom controls hint."""
    if show_help:
        return  # Help overlay handles this
    draw_rounded_rect(img, (10, h-42), (w-10, h-8), PANEL_BG, radius=10, alpha=0.65)
    controls = "Q Quit  │  D Dark Mode  │  P Particles  │  G Grid  │  M Distances  │  H Help"
    puttext(img, controls, (24, h-18), 0.4, TEXT_SECONDARY, 1)

def draw_help_overlay(img, h, w):
    """Draw full help overlay."""
    draw_rounded_rect(img, (w//4, h//6), (3*w//4, 5*h//6), (15,15,20), radius=16, alpha=0.92)

    cx = w//4 + 30
    cy = h//6 + 50

    puttext_glow(img, "HAND VIZ PRO", (cx, cy), 0.9, ACCENT_CYAN, 2)
    cy += 20
    puttext(img, "Real-time Hand Tracking Visualizer", (cx, cy+10), 0.45, TEXT_SECONDARY, 1)
    cy += 50

    controls = [
        ("Q", "Quit application", ACCENT_ROSE),
        ("D", "Toggle dark / light mode", ACCENT_PURPLE),
        ("P", "Toggle particle effects", ACCENT_CYAN),
        ("G", "Toggle background grid", ACCENT_GREEN),
        ("M", "Toggle distance measurements", ACCENT_AMBER),
        ("H", "Show / hide this help", TEXT_PRIMARY),
    ]
    for key, desc, color in controls:
        draw_rounded_rect(img, (cx, cy-16), (cx+30, cy+6), (40,40,50), radius=4, alpha=0.9)
        puttext(img, key, (cx+8, cy+2), 0.5, color, 2)
        puttext(img, desc, (cx+45, cy+2), 0.5, TEXT_PRIMARY, 1)
        cy += 38

    cy += 15
    puttext(img, "GESTURES DETECTED", (cx, cy), 0.5, ACCENT_AMBER, 1)
    cy += 30
    gestures = [
        ("Fist - Close all fingers", "✊"),
        ("Open Hand - Spread all fingers", "🖐️"),
        ("Peace - Index + middle up", "✌️"),
        ("Pointing - Index finger only", "☝️"),
        ("Thumbs Up - Thumb extended", "👍"),
    ]
    for desc, emoji in gestures:
        puttext(img, f"  {desc}", (cx, cy), 0.4, TEXT_SECONDARY, 1)
        cy += 28

def draw_finger_status(img, pts, x, y, hand_label):
    """Draw finger status panel for a hand."""
    panel_h = 175
    panel_w = 165
    draw_rounded_rect(img, (x, y), (x+panel_w, y+panel_h), PANEL_BG, radius=10, alpha=0.75)

    puttext(img, hand_label, (x+12, y+22), 0.45, ACCENT_CYAN, 1)
    cv2.line(img, (x+12, y+28), (x+panel_w-12, y+28), TEXT_DIM, 1)

    up = lambda tip, mid: pts[tip][1] < pts[mid][1]
    finger_states = [
        abs(pts[4][0]-pts[0][0]) > 60,
        up(8,6), up(12,10), up(16,14), up(20,18)
    ]

    finger_keys = ['thumb', 'index', 'middle', 'ring', 'pinky']
    for i, (name, state) in enumerate(zip(FINGER_NAMES, finger_states)):
        fy = y + 45 + i * 26
        color = FINGER_COLORS[finger_keys[i]][0] if state else TEXT_DIM
        dot_color = ACCENT_GREEN if state else (50,50,60)
        cv2.circle(img, (x+20, fy-4), 5, dot_color, -1, cv2.LINE_AA)
        puttext(img, name, (x+32, fy), 0.4, color, 1)
        status_text = "UP" if state else "—"
        puttext(img, status_text, (x+panel_w-40, fy), 0.38, color, 1)

def draw_angle_indicator(img, pts, color):
    """Draw wrist angle arc."""
    angle = get_hand_angle(pts)
    wrist = pts[0]
    radius = 35
    start_angle = -angle - 15
    end_angle = -angle + 15
    cv2.ellipse(img, wrist, (radius, radius), 0, start_angle, end_angle, color, 2, cv2.LINE_AA)
    puttext(img, f"{angle:.0f} deg", (wrist[0]+40, wrist[1]+5), 0.35, color, 1)

def draw_distance_lines(img, pts_list):
    """Draw distance measurements between fingertips of both hands."""
    if len(pts_list) < 2:
        return
    for tip in FINGERTIPS:
        p1 = pts_list[0][tip]
        p2 = pts_list[1][tip]
        dist = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
        mid = ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)
        color = lerp_color(ACCENT_GREEN, ACCENT_ROSE, min(1, dist/400))
        cv2.line(img, p1, p2, tuple(int(c*0.4) for c in color), 1, cv2.LINE_AA)
        puttext(img, f"{dist:.0f}px", (mid[0]+5, mid[1]-5), 0.3, color, 1)

def draw_grid(img, h, w, t):
    """Draw subtle animated background grid."""
    spacing = 50
    offset = int(t * 10) % spacing
    grid_color = (25, 28, 35)
    for x in range(offset, w, spacing):
        cv2.line(img, (x, 0), (x, h), grid_color, 1)
    for y in range(offset, h, spacing):
        cv2.line(img, (0, y), (w, y), grid_color, 1)

# ─── Main Loop ───────────────────────────────────────────────────────────────
cap = open_camera()
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"📐 {W}x{H} | Q=quit  D=dark  P=particles  G=grid  M=measure  H=help\n")

dark_mode = True
show_particles = True
show_help = False
show_grid = False
show_distances = False
fps_val = 0
frame_count = 0
prev_time = time.time()
timestamp_ms = 0
start_time = time.time()

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        t = time.time() - start_time
        pulse = (math.sin(t * 3) + 1) / 2  # 0-1 pulsation

        # FPS calculation
        frame_count += 1
        now = time.time()
        if now - prev_time >= 0.5:
            fps_val = frame_count / (now - prev_time)
            frame_count = 0
            prev_time = now
        display_fps = smooth_fps.update(fps_val)

        # Detect hands
        timestamp_ms += 33
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        result = detector.detect_for_video(mp_image, timestamp_ms)

        # Background
        if dark_mode:
            bg = cv2.convertScaleAbs(frame, alpha=0.2, beta=-10)
        else:
            bg = cv2.convertScaleAbs(frame, alpha=0.55, beta=15)

        # Animated grid
        if show_grid:
            draw_grid(bg, h, w, t)

        glow = np.zeros((h, w, 3), dtype=np.uint8)
        pcanvas = np.zeros((h, w, 3), dtype=np.uint8)
        gesture_labels = []
        all_pts_list = []

        for hand_idx, hand_lms in enumerate(result.hand_landmarks):
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lms]
            all_pts_list.append(pts)

            # Draw connections with per-finger gradient colors
            for group_name, conns in FINGER_GROUPS.items():
                colors = FINGER_COLORS[group_name]
                for ci, (a, b) in enumerate(conns):
                    frac = ci / max(1, len(conns)-1)
                    color = lerp_color(colors[0], colors[1], frac)
                    glow_line(glow, pts[a], pts[b], color, t=2)

            # Cross-fingertip web
            for i, ta in enumerate(FINGERTIPS):
                for j, tb in enumerate(FINGERTIPS):
                    if i >= j:
                        continue
                    dist = math.hypot(pts[ta][0]-pts[tb][0], pts[ta][1]-pts[tb][1])
                    if dist < 200:
                        alpha_val = max(0, 1 - dist/200)
                        finger_keys = ['thumb','index','middle','ring','pinky']
                        c1 = FINGER_COLORS[finger_keys[i]][0]
                        c2 = FINGER_COLORS[finger_keys[j]][0]
                        c = lerp_color(c1, c2, 0.5)
                        web_c = tuple(int(ch * alpha_val * 0.3) for ch in c)
                        cv2.line(glow, pts[ta], pts[tb], web_c, 1, cv2.LINE_AA)

            # Fingertip glow and trails
            finger_keys = ['thumb','index','middle','ring','pinky']
            for fi, tip in enumerate(FINGERTIPS):
                color = FINGER_COLORS[finger_keys[fi]][0]
                pt = pts[tip]
                key = hand_idx * 5 + fi

                # Trails
                tr = trails[key]
                tr.append(pt)
                if len(tr) > TRAIL_LEN:
                    tr.pop(0)
                for ti in range(1, len(tr)):
                    a = ti / len(tr)
                    trail_c = lerp_color((0,0,0), color, a)
                    thickness = max(1, int(3 * a))
                    cv2.line(glow, tr[ti-1], tr[ti], trail_c, thickness, cv2.LINE_AA)

                # Pulsating fingertip
                glow_circle(glow, pt, 7, color, pulse=pulse)

                # Particles
                if show_particles and random.random() < 0.4:
                    particles.append(Particle(pt[0], pt[1], color))

            # Wrist angle indicator
            draw_angle_indicator(glow, pts, ACCENT_CYAN)

            # Gesture detection
            g = gesture(pts)
            if g:
                gesture_labels.append((g, pts[0], hand_idx))

        # Two-hand connections
        if len(all_pts_list) == 2:
            # Wrist link
            glow_line(glow, all_pts_list[0][0], all_pts_list[1][0], (180, 180, 220), t=2)
            # Fingertip bridges
            for ta in FINGERTIPS:
                for tb in FINGERTIPS:
                    c1 = all_pts_list[0][ta]
                    c2 = all_pts_list[1][tb]
                    dist = math.hypot(c2[0]-c1[0], c2[1]-c1[1])
                    if dist < 250:
                        alpha_val = max(0, 1 - dist/250)
                        c = lerp_color(ACCENT_PURPLE, ACCENT_CYAN, alpha_val)
                        web_c = tuple(int(ch * alpha_val * 0.2) for ch in c)
                        cv2.line(glow, c1, c2, web_c, 1, cv2.LINE_AA)

        # Particle update
        if show_particles:
            alive = []
            for p in particles:
                p.update()
                if p.life > 0:
                    p.draw(pcanvas)
                    alive.append(p)
            particles[:] = alive[:800]

        # Composite
        out = cv2.addWeighted(bg, 1.0, glow, 1.0, 0)
        if show_particles:
            out = cv2.addWeighted(out, 1.0, pcanvas, 0.8, 0)

        # ─── HUD ─────────────────────────────────────────────────────
        draw_status_bar(out, h, w, display_fps, len(result.hand_landmarks),
                        len(particles), dark_mode, show_particles, show_grid, show_distances)

        # Gesture labels with emoji
        for label, pos, hidx in gesture_labels:
            emoji = GESTURE_EMOJI.get(label, "")
            display = f"{label}"
            gx = max(10, min(pos[0] - 60, w - 200))
            gy = max(80, pos[1] - 50)
            draw_rounded_rect(out, (gx-5, gy-25), (gx + len(display)*14 + 15, gy+8), PANEL_BG, radius=8, alpha=0.75)
            puttext_glow(out, display, (gx, gy), 0.7, ACCENT_AMBER, 2)

        # Finger status panels
        for hidx, pts in enumerate(all_pts_list):
            hand_label = "LEFT" if pts[0][0] > w//2 else "RIGHT"
            px = 12 if hidx == 0 else w - 180
            draw_finger_status(out, pts, px, 65, f"{hand_label} HAND")

        # Distance measurements
        if show_distances and len(all_pts_list) == 2:
            draw_distance_lines(out, all_pts_list)

        # Bottom bar
        draw_bottom_bar(out, h, w, show_help)

        # Help overlay
        if show_help:
            draw_help_overlay(out, h, w)

        # ─── Display ─────────────────────────────────────────────────
        cv2.imshow("Hand Viz Pro", out)
        key = cv2.waitKey(1) & 0xFF
        if   key == ord('q'): break
        elif key == ord('d'): dark_mode = not dark_mode
        elif key == ord('p'): show_particles = not show_particles
        elif key == ord('h'): show_help = not show_help
        elif key == ord('g'): show_grid = not show_grid
        elif key == ord('m'): show_distances = not show_distances

except KeyboardInterrupt:
    print("\n⚡ Interrupted by user")

cap.release()
cv2.destroyAllWindows()
detector.close()
print("✨ Hand Viz Pro closed. Goodbye!")

#!/usr/bin/env python3
"""
Kendrick Lamar & SZA — "luther" (GNX)
Cinematic Audio-Reactive Motion Graphics Music Video Renderer (1280x720 @ 30fps)
"""
import os
import re
import sys
import math
import time
import argparse
import subprocess
from multiprocessing import Pool
import numpy as np
import cv2
import cairo
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
CX, CY = W // 2, H // 2
FPS = 30
BAR_H = 44  # 2.35:1 cinema letterbox bars

SRT_PATH = "/working_dir/c_2475b8aa144e36fd/user_uploaded_files/ttl=63d/user_uploaded/luthor_srt.srt"
MP3_PATH = "/working_dir/c_2475b8aa144e36fd/user_uploaded_files/ttl=63d/user_uploaded/luther-Kendrick+Lamar#2Fc0n3.mp3"
FEAT_PATH = "/working_dir/c_2475b8aa144e36fd/work/audio_features.npz"
OUT_MP4 = "/working_dir/c_2475b8aa144e36fd/artifacts/file_generation/ttl=63d/output/luther_Kendrick_Lamar_SZA_MV_v2.mp4"
REF_BUST_IMG = "/working_dir/c_2475b8aa144e36fd/user_uploaded_files/ttl=63d/tool_generated/watermarked_img_18046160560861840547.jpg"

# Font paths
F_SERIF_REG   = "/usr/share/fonts/opentype/urw-base35/C059-Roman.otf"
F_SERIF_ITAL  = "/usr/share/fonts/opentype/urw-base35/C059-Italic.otf"
F_SERIF_BOLD  = "/usr/share/fonts/opentype/urw-base35/C059-Bold.otf"
F_SANS_BLACK  = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_SANS_BOLD   = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_SANS_SEMI   = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
F_SANS_ITAL   = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBoldItalic.otf"
F_SANS_LIGHT  = "/usr/share/fonts/opentype/inter/InterDisplay-Light.otf"
F_CJK_REG     = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"

# Poetic Chinese subtitles mapped by SRT cue index (1-based)
ZH_MAP = {
    5:  "若这世界归我所有",
    6:  "罗马数字七，宝贝，炽热绽放",
    7:  "若这世界归我，我愿让你的梦想成倍生长",
    8:  "若这世界归我，我愿将你的敌人带到神前",
    9:  "引他们步入光中，以圣火相迎",
    10: "",
    11: "罗马数字七，宝贝，炽热绽放",
    12: "若这世界归我，我愿让你的梦想成倍生长",
    13: "若这世界归我，我愿将你的敌人带到神前",
    14: "引他们步入光中，以圣火相迎",
    15: "氛围正浓，翩翩起舞，任他们仰望",
    16: "她是忠实信徒，他黯然失色，虚伪的和解免谈",
    17: "在这尘世里，水泥缝中亦会绽放繁花",
    18: "心碎之痛，她只是依循宿命前行",
    19: "周末的夜，低调燃起悸动",
    20: "更美好的日子，定会如期而至",
    21: "若由我主宰，绝不予那些无名之辈半点怜悯",
    22: "我愿带走你的伤痛，将世间万物予你",
    23: "我只想看你赢，只想见证你闪耀",
    24: "若这世界归我所有",
    25: "深入浅出，放慢节奏，沉醉其中",
    26: "宝贝你是星辰，尽情定格锋芒",
    27: "当我与你相拥，万物皆随心意慢行",
    28: "来吧，将这炽热烙印在我的灵魂之上",
    29: "绯红法拉利，叠起王冠，腕间霜寒闪耀",
    30: "璀璨流光，归途之上，告诉我你爱我",
    31: "在这尘世里，水泥缝中亦会绽放繁花",
    32: "心碎之痛，她只是依循宿命前行",
    33: "周末的夜，低调燃起悸动",
    34: "更美好的日子，定会如期而至",
    35: "若由我主宰，绝不予那些无名之辈半点怜悯",
    36: "我愿带走你的伤痛，将世间万物予你",
    37: "我只想看你赢，只想见证你闪耀",
    38: "若这世界归我所有",
    39: "我无法说谎，我信任你、深爱你，绝不虚度你的时光",
    40: "我愿关掉世界喧嚣，只为点燃你的心动",
    41: "我会让你大声倾诉",
    42: "我从不迷失，绝不让你徒增烦忧",
    43: "我甚至愿为你安定下来，向你证明我的深情",
    44: "我会放慢脚步，屏息沉静",
    45: "只为点燃你的心动，宝贝",
    46: "周末的夜，低调燃起悸动",
    47: "更美好的日子，定会如期而至",
    48: "我深知你正为此奔赴",
    49: "更美好的日子",
    50: "若这世界归我所有",
}

POWER_WORDS = {
    "seven", "seven,", "hot", "dreams", "multiply", "god", "light,", "fire",
    "concrete", "flowers", "grow", "better", "days", "everything", "win,",
    "star,", "soul", "love", "trust", "mine", "world", "pro", "loud", "pain,"
}

def parse_srt(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        text = f.read()
    blocks = re.split(r"\n\s*\n", text.strip())
    cues = []
    for b in blocks:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        if len(lines) < 3:
            continue
        idx = int(lines[0])
        m = re.match(r"(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)", lines[1])
        if not m:
            continue
        t0 = int(m[1])*3600 + int(m[2])*60 + int(m[3]) + int(m[4])/1000.0
        t1 = int(m[5])*3600 + int(m[6])*60 + int(m[7]) + int(m[8])/1000.0
        txt = " ".join(lines[2:])
        cues.append({"idx": idx, "t0": t0, "t1": t1, "text": txt, "zh": ZH_MAP.get(idx, "")})
    return cues

def ease_out_cubic(x):
    x = max(0.0, min(1.0, x))
    return 1.0 - (1.0 - x) ** 3

def smoothstep(edge0, edge1, x):
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0 + 1e-9)))
    return t * t * (3.0 - 2.0 * t)

def lerp_color(c1, c2, t):
    return (c1[0] + (c2[0]-c1[0])*t,
            c1[1] + (c2[1]-c1[1])*t,
            c1[2] + (c2[2]-c1[2])*t)

# =====================================================================
# PRECOMPUTED GRIDS, PARTICLES & BOTANICAL PETAL GEOMETRY
# =====================================================================
BG_W, BG_H = 320, 180
_yy, _xx = np.mgrid[0:BG_H, 0:BG_W].astype(np.float32)
NX = (_xx - BG_W / 2.0) / (BG_H / 2.0)
NY = (_yy - BG_H / 2.0) / (BG_H / 2.0)
NR = np.sqrt(NX * NX + NY * NY) + 1e-6
NANG = np.arctan2(NY, NX)

_fyy, _fxx = np.mgrid[0:H, 0:W].astype(np.float32)
_fnx = (_fxx - CX) / (W * 0.55)
_fny = (_fyy - CY) / (H * 0.55)
VIGNETTE = np.clip(1.0 - 0.52 * (_fnx*_fnx + _fny*_fny), 0.28, 1.0)[:, :, None]

_rng = np.random.default_rng(777)
GRAIN_TILES = [
    cv2.resize(_rng.normal(0.0, 5.0, (H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST)[:, :, None]
    for _ in range(16)
]

N_PART = 110
P_X = _rng.uniform(0.0, W, N_PART)
P_Y = _rng.uniform(0.0, H, N_PART)
P_Z = _rng.uniform(0.25, 1.0, N_PART)
P_PH = _rng.uniform(0.0, 2*math.pi, N_PART)
P_SP = _rng.uniform(18.0, 68.0, N_PART)
P_DRIFT = _rng.uniform(-18.0, 18.0, N_PART)

N_BOKEH = 48
B_X = _rng.uniform(0.0, W, N_BOKEH)
B_Y = _rng.uniform(0.0, H, N_BOKEH)
B_R = _rng.uniform(14.0, 48.0, N_BOKEH)
B_SP = _rng.uniform(22.0, 88.0, N_BOKEH)
B_COL_IDX = _rng.integers(0, 3, N_BOKEH)

CRACKS = []
for i in range(14):
    ang = (i / 14.0) * 2 * math.pi + _rng.uniform(-0.18, 0.18)
    pts = [(CX, CY)]
    r = 35.0
    for step in range(9):
        r += _rng.uniform(38.0, 82.0)
        ang += _rng.uniform(-0.22, 0.22)
        pts.append((int(CX + math.cos(ang) * r), int(CY + math.sin(ang) * r)))
    CRACKS.append(pts)

# Unit pointed botanical rose petal contour (16 vertices, base at 0, tip at 1.0)
_pt_u = np.linspace(0, 1, 9)
_pt_w = np.sin(_pt_u * math.pi) ** 0.72 * (1.0 - 0.18 * _pt_u)
_pt_x_top = _pt_u
_pt_y_top = _pt_w * 0.42
_pt_x = np.concatenate([_pt_x_top, _pt_x_top[-2:0:-1]])
_pt_y = np.concatenate([_pt_y_top, -_pt_y_top[-2:0:-1]])
UNIT_PETAL = np.stack([_pt_x, _pt_y], axis=1).astype(np.float32)

# Pre-rendered Roman Numeral VII watermark (computed once per worker!)
VII_WATERMARK = None
FONTS = {}

def init_fonts():
    global FONTS, VII_WATERMARK
    FONTS = {
        "title_big":   ImageFont.truetype(F_SERIF_ITAL, 108),
        "title_sub":   ImageFont.truetype(F_SANS_LIGHT, 20),
        "luther":      ImageFont.truetype(F_SERIF_ITAL, 52),
        "kendrick":    ImageFont.truetype(F_SANS_BOLD, 44),
        "kendrick_sm": ImageFont.truetype(F_SANS_SEMI, 37),
        "sza":         ImageFont.truetype(F_SANS_ITAL, 43),
        "sza_adlib":   ImageFont.truetype(F_SANS_ITAL, 31),
        "fah_huge":    ImageFont.truetype(F_SANS_BLACK, 148),
        "vii_bg":      ImageFont.truetype(F_SERIF_BOLD, 280),
        "zh":          ImageFont.truetype(F_CJK_REG, 22),
        "hud":         ImageFont.truetype(F_SANS_LIGHT, 13),
    }
    pil_vii = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(pil_vii)
    bbox = d.textbbox((0, 0), "VII", font=FONTS["vii_bg"])
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((CX - tw // 2, CY - th // 2 - 22), "VII", font=FONTS["vii_bg"], fill=255)
    VII_WATERMARK = (np.array(pil_vii, dtype=np.float32) / 255.0)[:, :, None]

def get_act_info(t):
    if t < 12.55:
        return 1, "I", "PROLOGUE · IF THIS WORLD WERE MINE"
    elif t < 26.29:
        return 2, "II", "ROMAN NUMERAL VII"
    elif t < 33.40:
        return 3, "II", "STRICTLY WITH THAT FIRE"
    elif t < 53.79:
        return 4, "II", "ORCHESTRAL SWELL"
    elif t < 69.56:
        return 5, "III", "CONCRETE FLOWERS GROW"
    elif t < 83.06:
        return 6, "III", "SOLAR ECLIPSE · HARMONY"
    elif t < 104.18:
        return 7, "IV", "NOCTURNAL DUET"
    elif t < 119.93:
        return 8, "V", "CONCRETE FLOWERS · REPRISE"
    elif t < 133.47:
        return 9, "V", "RADIANT ECLIPSE"
    elif t < 160.26:
        return 10, "VI", "DEVOTION"
    else:
        return 11, "VII", "BETTER DAYS · FULL CIRCLE"

def compute_background(t, sub, low, voc, hi, kick):
    kf_t = [0.0, 9.8, 12.6, 26.3, 33.4, 53.8, 69.6, 83.1, 104.2, 120.0, 133.5, 160.3, 170.0, 174.5, 178.0]
    kf_bg = [
        (14, 14, 15), (16, 16, 18), (10, 14, 24), (8, 10, 28), (14, 14, 30),
        (24, 16, 20), (22, 12, 26), (26, 13, 12), (22, 14, 22), (18, 16, 32),
        (16, 22, 38), (14, 24, 36), (16, 16, 18), (10, 10, 11), (4, 4, 4),
    ]
    kf_glow = [
        (110, 110, 115), (120, 120, 125), (45, 145, 225), (35, 95, 245), (55, 115, 235),
        (115, 80, 205), (135, 100, 230), (65, 42, 195), (110, 90, 225), (65, 155, 250),
        (75, 130, 235), (80, 175, 250), (125, 125, 130), (65, 65, 68), (10, 10, 10),
    ]
    kf_acc = [
        (70, 70, 72), (85, 85, 90), (90, 180, 240), (55, 160, 255), (95, 80, 195),
        (155, 115, 165), (70, 170, 245), (165, 105, 70), (85, 175, 245), (145, 110, 235),
        (115, 105, 215), (120, 200, 255), (90, 90, 95), (40, 40, 42), (5, 5, 5),
    ]
    i = 0
    while i < len(kf_t) - 2 and t > kf_t[i+1]:
        i += 1
    seg_u = smoothstep(kf_t[i], kf_t[i+1], t)
    c_bg   = lerp_color(kf_bg[i], kf_bg[i+1], seg_u)
    c_glow = lerp_color(kf_glow[i], kf_glow[i+1], seg_u)
    c_acc  = lerp_color(kf_acc[i], kf_acc[i+1], seg_u)

    w1 = np.sin(NX * 1.9 + t * 0.42 + np.cos(NY * 1.6 - t * 0.28)) * 0.5 + 0.5
    w2 = np.cos(NY * 2.2 - t * 0.33 + np.sin(NX * 1.4 + t * 0.21)) * 0.5 + 0.5
    radial = np.exp(-NR * (1.25 - 0.22 * sub - 0.15 * kick))
    god_rays = (np.sin(NANG * 7.0 + t * 0.55) * 0.5 + 0.5) * np.exp(-NR * 0.85)

    glow_amp = (0.36 + 0.26 * voc + 0.20 * sub + 0.24 * kick) * radial + 0.16 * w1 * (0.5 + 0.5 * low)
    acc_amp  = 0.20 * w2 * np.exp(-NR * 0.7) + 0.13 * god_rays * (0.4 + 0.6 * voc)

    if 9.8 < t < 13.0:
        glow_amp += math.exp(-((t - 10.8) / 1.1) ** 2) * 0.65 * np.exp(-NR * 1.1)
    if 26.0 <= t <= 33.5 and kick > 0.35:
        glow_amp += kick * 0.55 * np.exp(-NR * 0.9)

    img = np.zeros((BG_H, BG_W, 3), dtype=np.float32)
    for ch in range(3):
        img[:, :, ch] = c_bg[ch] + c_glow[ch] * glow_amp + c_acc[ch] * acc_amp
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)

def add_glow_layer(canvas, draw_fn, blur_k=25, strength=0.85, base_weight=0.92):
    layer = np.zeros((H, W, 3), dtype=np.uint8)
    draw_fn(layer)
    small = cv2.resize(layer, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    k = max(3, (blur_k // 2) | 1)
    bloom = cv2.GaussianBlur(small, (k, k), 0)
    bloom = cv2.resize(bloom, (W, H), interpolation=cv2.INTER_LINEAR)
    if base_weight > 0:
        canvas += layer.astype(np.float32) * base_weight + bloom.astype(np.float32) * strength
    else:
        canvas += bloom.astype(np.float32) * strength

def draw_anamorphic_flare(canvas, cy_off, color_bgr, intensity):
    if intensity <= 0.02:
        return
    y0 = int(CY + cy_off)
    layer = np.zeros((H // 4, W // 4, 3), dtype=np.uint8)
    cx4, y4 = CX // 4, y0 // 4
    w_len = int((W // 4) * (0.35 + 0.45 * min(1.2, intensity)))
    c = tuple(int(min(255, v * intensity)) for v in color_bgr)
    cv2.line(layer, (cx4 - w_len, y4), (cx4 + w_len, y4), c, 2, cv2.LINE_AA)
    cv2.ellipse(layer, (cx4, y4), (int(w_len * 0.52), 4), 0, 0, 360, c, -1, cv2.LINE_AA)
    bloom = cv2.GaussianBlur(layer, (31, 9), 0)
    bloom_full = cv2.resize(bloom, (W, H), interpolation=cv2.INTER_LINEAR)
    canvas += bloom_full.astype(np.float32) * 0.90

def scene_monochrome_atrium(canvas, t, low, voc, sub, alpha_scale=1.0, reverse=False):
    if alpha_scale <= 0.01:
        return
    def _draw(layer):
        gold_mix = smoothstep(9.9, 12.4, t) if not reverse else (1.0 - smoothstep(169.5, 173.5, t))
        c_ring = lerp_color((195, 195, 200), (80, 185, 245), gold_mix)
        for k in range(12):
            phase = ((k / 12.0) + (t * 0.085 * (-1 if reverse else 1))) % 1.0
            rad = int(45 + (phase ** 1.75) * 590)
            fade = math.sin(phase * math.pi) * alpha_scale
            thick = 1 if rad < 200 else 2
            col = tuple(int(v * fade * (0.45 + 0.35 * low)) for v in c_ring)
            cv2.circle(layer, (CX, CY), rad, col, thick, cv2.LINE_AA)
        for s in range(16):
            ang = s * (2 * math.pi / 16) + t * 0.06
            x1, y1 = int(CX + math.cos(ang) * 90), int(CY + math.sin(ang) * 90)
            x2, y2 = int(CX + math.cos(ang) * 650), int(CY + math.sin(ang) * 650)
            col = tuple(int(v * 0.18 * alpha_scale) for v in c_ring)
            cv2.line(layer, (x1, y1), (x2, y2), col, 1, cv2.LINE_AA)
        r_core = int(115 + 22 * voc + 18 * sub)
        c_core = tuple(int(v * alpha_scale * (0.7 + 0.3 * voc)) for v in lerp_color((220, 220, 225), (95, 205, 255), gold_mix))
        cv2.circle(layer, (CX, CY), r_core, c_core, 2, cv2.LINE_AA)
    add_glow_layer(canvas, _draw, blur_k=25, strength=0.75)

def scene_roman_vii_astrolabe(canvas, t, sub, voc, kick, spec, alpha_scale=1.0):
    if alpha_scale <= 0.01:
        return
    lum = (28.0 + 24.0 * voc + 20.0 * kick) * alpha_scale
    canvas[:, :, 0] += VII_WATERMARK[:, :, 0] * (lum * 0.35)
    canvas[:, :, 1] += VII_WATERMARK[:, :, 0] * (lum * 0.78)
    canvas[:, :, 2] += VII_WATERMARK[:, :, 0] * (lum * 1.00)

    def _draw(layer):
        c_gold = (75, 185, 250)
        c_warm = (60, 125, 245)
        r1 = int(175 + 24 * sub + 18 * kick)
        r2 = int(245 + 18 * voc)
        r3 = int(315 + 12 * sub)
        cv2.circle(layer, (CX, CY), r1, tuple(int(v * 0.75 * alpha_scale) for v in c_gold), 2, cv2.LINE_AA)
        cv2.circle(layer, (CX, CY), r2, tuple(int(v * 0.45 * alpha_scale) for v in c_warm), 1, cv2.LINE_AA)
        a1, a2 = (t * 28) % 360, (-t * 19) % 360
        cv2.ellipse(layer, (CX, CY), (r2, r2), 0, a1, a1 + 95, tuple(int(v * 0.85 * alpha_scale) for v in c_gold), 3, cv2.LINE_AA)
        cv2.ellipse(layer, (CX, CY), (r2, r2), 0, a1 + 180, a1 + 275, tuple(int(v * 0.85 * alpha_scale) for v in c_gold), 3, cv2.LINE_AA)
        cv2.ellipse(layer, (CX, CY), (r3, r3), 0, a2, a2 + 65, tuple(int(v * 0.55 * alpha_scale) for v in c_warm), 2, cv2.LINE_AA)
        cv2.ellipse(layer, (CX, CY), (r3, r3), 0, a2 + 180, a2 + 245, tuple(int(v * 0.55 * alpha_scale) for v in c_warm), 2, cv2.LINE_AA)
        for b in range(32):
            ang = (b / 32.0) * 2 * math.pi + t * 0.15
            amp = float(spec[b])
            length = 8 + amp * 42
            x1, y1 = int(CX + math.cos(ang) * (r1 + 4)), int(CY + math.sin(ang) * (r1 + 4))
            x2, y2 = int(CX + math.cos(ang) * (r1 + 4 + length)), int(CY + math.sin(ang) * (r1 + 4 + length))
            col = tuple(int(v * (0.35 + 0.65 * amp) * alpha_scale) for v in c_gold)
            cv2.line(layer, (x1, y1), (x2, y2), col, 2, cv2.LINE_AA)
    add_glow_layer(canvas, _draw, blur_k=27, strength=0.8)

def scene_fah_shockwaves(canvas, t, kick, sub):
    hits = [26.10, 27.40, 28.45, 29.57, 30.87, 31.95, 33.03]
    def _draw(layer):
        for ht in hits:
            dt = t - ht
            if 0.0 <= dt < 1.35:
                p = ease_out_cubic(dt / 1.35)
                rad = int(50 + p * 680)
                fade = (1.0 - p) ** 1.3
                thick = max(2, int(14 * (1.0 - p)))
                cv2.circle(layer, (CX, CY), rad, (int(60 * fade), int(155 * fade), int(255 * fade)), thick, cv2.LINE_AA)
                cv2.circle(layer, (CX, CY), int(rad * 0.72), (int(90*fade), int(210*fade), int(255*fade)), max(1, thick//2), cv2.LINE_AA)
        if kick > 0.35:
            for i in range(28):
                ang = (i / 28.0) * 2 * math.pi + math.sin(t * 7.0 + i) * 0.05
                r_in = int(140 + (i % 3) * 40)
                r_out = int(r_in + 160 + 260 * kick)
                cv2.line(layer, (int(CX + math.cos(ang)*r_in), int(CY + math.sin(ang)*r_in)),
                         (int(CX + math.cos(ang)*r_out), int(CY + math.sin(ang)*r_out)),
                         (int(70*kick), int(165*kick), int(255*kick)), 2, cv2.LINE_AA)
    add_glow_layer(canvas, _draw, blur_k=31, strength=1.15)
    draw_anamorphic_flare(canvas, 0, (80, 175, 255), min(1.2, kick * 1.15))

def scene_silk_ribbons(canvas, t, voc, low, sub, color1, color2, alpha_scale=1.0):
    if alpha_scale <= 0.01:
        return
    def _draw(layer):
        xs = np.linspace(0, W - 1, 90).astype(np.int32)
        for r in range(6):
            freq = 0.0042 + r * 0.0007
            amp = (38 + 65 * voc + 28 * sub) * (0.65 + 0.12 * r)
            phase = t * (1.2 + r * 0.22) + r * 1.05
            y_base = CY + (r - 2.5) * 42
            ys = y_base + np.sin(xs * freq + phase) * amp + np.cos(xs * freq * 1.7 - phase * 0.7) * (amp * 0.35)
            pts = np.stack([xs, ys.astype(np.int32)], axis=1).reshape(-1, 1, 2)
            col = lerp_color(color1, color2, r / 5.0)
            col = tuple(int(v * alpha_scale * (0.45 + 0.45 * voc)) for v in col)
            cv2.polylines(layer, [pts], False, col, 2, cv2.LINE_AA)
    add_glow_layer(canvas, _draw, blur_k=29, strength=0.95)

def scene_concrete_flowers(canvas, t, act_progress, voc, sub, alpha_scale=1.0, golden_boost=0.0):
    """Sculptural botanical pointed-petal Rose Mandala blooming from kintsugi concrete fractures."""
    if alpha_scale <= 0.01:
        return
    bloom_p = ease_out_cubic(min(1.0, act_progress * 1.35))
    def _draw(layer):
        # 1. Kintsugi golden-rose concrete fractures
        c_crack = lerp_color((140, 130, 195), (90, 190, 255), golden_boost)
        for pts in CRACKS:
            n_show = max(2, int(len(pts) * min(1.0, act_progress * 2.2)))
            arr = np.array(pts[:n_show], dtype=np.int32).reshape(-1, 1, 2)
            col = tuple(int(v * 0.42 * alpha_scale * (0.6 + 0.4 * sub)) for v in c_crack)
            cv2.polylines(layer, [arr], False, col, 1, cv2.LINE_AA)

        # 2. Concentric botanical whorls of pointed rose petals (outer to inner for depth)
        whorls = [
            (11, 245, 0.08, 0.20, 0.65),
            (9,  188, -0.11, 0.28, 0.78),
            (7,  132, 0.14, 0.35, 0.90),
            (5,   78, -0.18, 0.42, 1.00),
        ]
        for n_pet, max_len, rot_sp, fill_a, edge_a in whorls:
            plen = max_len * bloom_p * (1.0 + 0.06 * sub + 0.05 * voc)
            if plen < 12:
                continue
            for i in range(n_pet):
                ang = (i / float(n_pet)) * 2 * math.pi + t * rot_sp + n_pet * 0.5
                ca, sa = math.cos(ang), math.sin(ang)
                # Transform unit botanical petal
                px = CX + (UNIT_PETAL[:, 0] * ca - UNIT_PETAL[:, 1] * sa) * plen
                py = CY + (UNIT_PETAL[:, 0] * sa + UNIT_PETAL[:, 1] * ca) * plen
                poly = np.stack([px, py], axis=1).astype(np.int32).reshape(-1, 1, 2)
                frac = max_len / 245.0
                c_in = lerp_color((75, 58, 210), (75, 175, 250), golden_boost * 0.7)
                c_out = lerp_color((155, 115, 225), (125, 195, 255), golden_boost)
                col = lerp_color(c_in, c_out, frac)
                cv2.fillPoly(layer, [poly], tuple(int(v * fill_a * 0.48 * alpha_scale) for v in col), cv2.LINE_AA)
                cv2.polylines(layer, [poly], True, tuple(int(v * edge_a * 0.78 * alpha_scale) for v in col), 1, cv2.LINE_AA)
                # Delicate central golden vein inside each petal
                vx = int(CX + ca * plen * 0.72)
                vy = int(CY + sa * plen * 0.72)
                cv2.line(layer, (CX, CY), (vx, vy), tuple(int(v * 0.35 * alpha_scale) for v in (95, 200, 255)), 1, cv2.LINE_AA)
        # Subtle glowing pistil core
        cv2.circle(layer, (CX, CY), int(16 * bloom_p), tuple(int(v * 0.9 * alpha_scale) for v in (105, 205, 255)), 2, cv2.LINE_AA)
    add_glow_layer(canvas, _draw, blur_k=31, strength=0.9)

def scene_solar_eclipse(canvas, t, voc, sub, kick, spec, alpha_scale=1.0, intensity_boost=1.0):
    if alpha_scale <= 0.01:
        return
    r_sun = int(128 + 14 * sub + 10 * kick)
    # Place soft anamorphic flare BEHIND the dark eclipse moon so central lyrics stay ultra-legible!
    draw_anamorphic_flare(canvas, 0, (105, 175, 245), (0.42 + 0.42 * voc) * alpha_scale * intensity_boost)
    def _draw(layer):
        c_gold = (75, 195, 255)
        c_rose = (165, 115, 245)
        for k in range(64):
            ang = (k / 64.0) * 2 * math.pi + t * 0.12
            amp = float(spec[k % 32])
            ray_len = 22 + amp * 110 * intensity_boost + 22 * voc
            x1, y1 = int(CX + math.cos(ang) * r_sun), int(CY + math.sin(ang) * r_sun)
            x2, y2 = int(CX + math.cos(ang) * (r_sun + ray_len)), int(CY + math.sin(ang) * (r_sun + ray_len))
            mix = 0.5 + 0.5 * math.sin(ang * 2.0 - t * 0.9)
            col = lerp_color(c_gold, c_rose, mix)
            col = tuple(int(min(255, v * (0.45 + 0.65 * amp) * alpha_scale)) for v in col)
            cv2.line(layer, (x1, y1), (x2, y2), col, 2, cv2.LINE_AA)
        ox, oy = int(math.cos(t * 0.9) * 16), int(math.sin(t * 0.9) * 11)
        cv2.circle(layer, (CX + ox, CY + oy), r_sun + 11, tuple(int(v * 0.85 * alpha_scale) for v in c_gold), 3, cv2.LINE_AA)
        cv2.circle(layer, (CX - ox, CY - oy), r_sun + 11, tuple(int(v * 0.85 * alpha_scale) for v in c_rose), 3, cv2.LINE_AA)
        cv2.circle(layer, (CX, CY), r_sun + 3, (235, 242, 255), 3, cv2.LINE_AA)
    add_glow_layer(canvas, _draw, blur_k=35, strength=1.1)
    # Occlude dark eclipse moon over center (including over the flare!)
    mask = np.zeros((H, W), dtype=np.float32)
    cv2.circle(mask, (CX, CY), r_sun - 1, 1.0, -1, cv2.LINE_AA)
    mask = cv2.GaussianBlur(mask, (9, 9), 0)[:, :, None] * alpha_scale * 0.93
    canvas *= (1.0 - mask)

def scene_nocturnal_duet(canvas, t, sub, voc, kick, spec, alpha_scale=1.0):
    if alpha_scale <= 0.01:
        return
    # 1. Creamy out-of-focus 85mm cinema bokeh layer (pure blurred glow, no harsh edges!)
    def _draw_bokeh(layer):
        bokeh_cols = [(55, 45, 235), (85, 165, 245), (175, 105, 225)]
        for i in range(N_BOKEH):
            bx = int((B_X[i] + math.sin(t * 0.5 + i) * 14) % W)
            by = int((B_Y[i] + t * B_SP[i]) % H)
            br = int(B_R[i] * (0.85 + 0.22 * sub))
            col = tuple(int(v * 0.42 * alpha_scale) for v in bokeh_cols[B_COL_IDX[i]])
            cv2.circle(layer, (bx, by), br, col, -1, cv2.LINE_AA)
    add_glow_layer(canvas, _draw_bokeh, blur_k=39, strength=0.95, base_weight=0.12)

    # 2. Crisp glass elevator mullions + dual-hemisphere circular equalizer
    def _draw_eq(layer):
        for gx in [160, 340, 940, 1120]:
            cv2.line(layer, (gx, BAR_H), (gx, H - BAR_H), (85, 62, 62), 1, cv2.LINE_AA)
        floor_offset = int((t * 140) % 160)
        for fy in range(-160, H + 160, 160):
            y = H - ((fy + floor_offset) % (H + 160))
            cv2.line(layer, (0, y), (250, y), (70, 52, 105), 1, cv2.LINE_AA)
            cv2.line(layer, (W - 250, y), (W, y), (70, 52, 105), 1, cv2.LINE_AA)
        r_eq = int(198 + 16 * kick)
        for b in range(24):
            amp = float(spec[b])
            ang_l = math.pi * 0.58 + (b / 23.0) * math.pi * 0.84
            ang_r = -math.pi * 0.42 + (b / 23.0) * math.pi * 0.84
            ln = 10 + amp * 68
            cv2.line(layer, (int(CX + math.cos(ang_l)*r_eq), int(CY + math.sin(ang_l)*r_eq)),
                     (int(CX + math.cos(ang_l)*(r_eq+ln)), int(CY + math.sin(ang_l)*(r_eq+ln))),
                     tuple(int(v * alpha_scale) for v in (80, 190, 255)), 3, cv2.LINE_AA)
            cv2.line(layer, (int(CX + math.cos(ang_r)*r_eq), int(CY + math.sin(ang_r)*r_eq)),
                     (int(CX + math.cos(ang_r)*(r_eq+ln)), int(CY + math.sin(ang_r)*(r_eq+ln))),
                     tuple(int(v * alpha_scale) for v in (135, 90, 245)), 3, cv2.LINE_AA)
    add_glow_layer(canvas, _draw_eq, blur_k=23, strength=0.85)

def scene_devotion_window(canvas, t, voc, low, sub, alpha_scale=1.0):
    if alpha_scale <= 0.01:
        return
    def _draw(layer):
        r_win = 265
        cv2.circle(layer, (CX, CY), r_win, tuple(int(v * 0.65 * alpha_scale) for v in (95, 165, 235)), 3, cv2.LINE_AA)
        cv2.circle(layer, (CX, CY), r_win + 18, tuple(int(v * 0.30 * alpha_scale) for v in (90, 140, 215)), 1, cv2.LINE_AA)
        hy = CY + 62
        hw = int(math.sqrt(max(1, r_win*r_win - 62*62)))
        cv2.line(layer, (CX - hw, hy), (CX + hw, hy), tuple(int(v * 0.45 * alpha_scale) for v in (90, 170, 245)), 2, cv2.LINE_AA)
        a = t * 0.65
        for k in range(1, 22):
            ak = a - k * 0.06
            fade = (1.0 - k / 22.0) * 0.7 * alpha_scale
            cv2.circle(layer, (int(CX + math.cos(ak)*115), int(CY + math.sin(ak*2)*42)), max(2, int(14*fade)),
                       (int(80*fade), int(185*fade), int(255*fade)), -1, cv2.LINE_AA)
            cv2.circle(layer, (int(CX - math.cos(ak)*115), int(CY - math.sin(ak*2)*42)), max(2, int(14*fade)),
                       (int(165*fade), int(125*fade), int(245*fade)), -1, cv2.LINE_AA)
        cv2.circle(layer, (int(CX + math.cos(a)*115), int(CY + math.sin(a*2)*42)), int(18 + 10*voc), (120, 215, 255), -1, cv2.LINE_AA)
        cv2.circle(layer, (int(CX - math.cos(a)*115), int(CY - math.sin(a*2)*42)), int(18 + 10*voc), (195, 155, 255), -1, cv2.LINE_AA)
    add_glow_layer(canvas, _draw, blur_k=33, strength=1.0)
    scene_silk_ribbons(canvas, t, voc, low, sub, (80, 165, 245), (155, 115, 235), alpha_scale * 0.65)

def draw_particles(canvas, t, sub, voc, color_bgr, upward=True, density=1.0):
    layer = np.zeros((H, W, 3), dtype=np.uint8)
    n = int(N_PART * density)
    dir_y = -1.0 if upward else 1.0
    for i in range(n):
        z = P_Z[i]
        px = int((P_X[i] + math.sin(t * 0.6 + P_PH[i]) * 26 * z + P_DRIFT[i] * t * 0.25) % W)
        py = int((P_Y[i] + dir_y * t * P_SP[i] * z) % H)
        if py < BAR_H or py > H - BAR_H:
            continue
        twinkle = 0.45 + 0.55 * math.sin(t * 2.5 + P_PH[i] * 3.0)
        rad = max(1, int((1.5 + 3.2 * z) * (0.85 + 0.3 * voc)))
        col = tuple(int(min(255, v * twinkle * (0.4 + 0.6 * z))) for v in color_bgr)
        cv2.circle(layer, (px, py), rad, col, -1, cv2.LINE_AA)
    small = cv2.resize(layer, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    bloom = cv2.GaussianBlur(small, (7, 7), 0)
    bloom = cv2.resize(bloom, (W, H), interpolation=cv2.INTER_LINEAR)
    canvas += layer.astype(np.float32) * 0.85 + bloom.astype(np.float32) * 0.75

# =====================================================================
# ULTRA-FAST KINETIC TYPOGRAPHY & HUD (OpenCV + Numpy Compositing)
# =====================================================================
def draw_tracked_text(draw, cx, y, text, font, fill, tracking=4):
    widths = [draw.textbbox((0, 0), ch, font=font)[2] for ch in text]
    total_w = sum(widths) + tracking * max(0, len(text) - 1)
    x = cx - total_w / 2.0
    for ch, cw in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += cw + tracking

def wrap_words(draw, words, font, max_w):
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textbbox((0, 0), test, font=font)[2] <= max_w or not cur:
            cur.append(w)
        else:
            lines.append(cur)
            cur = [w]
    if cur:
        lines.append(cur)
    return lines

def render_typography_and_hud(frame_rgb, t, cues, kick, voc, sub):
    """Fast RGBA text overlay composited via numpy + cv2.GaussianBlur shadow."""
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt_layer)

    # 1. Opening Title Card (0.3s - 9.9s)
    if 0.3 <= t <= 9.9:
        a_in = ease_out_cubic((t - 0.5) / 1.8)
        a_out = 1.0 - ease_out_cubic((t - 8.4) / 1.4) if t > 8.4 else 1.0
        a = max(0.0, min(1.0, a_in * a_out))
        if a > 0.01:
            y_off = int((1.0 - a_in) * 18)
            draw_tracked_text(d, CX, CY - 78 + y_off, "luther", FONTS["title_big"], (242, 240, 235, int(245 * a)), tracking=14)
            draw_tracked_text(d, CX, CY + 54 + y_off, "KENDRICK LAMAR  &  SZA", FONTS["title_sub"], (205, 198, 185, int(195 * a)), tracking=7)
            line_w = int(120 * a)
            d.line([(CX - line_w, CY + 42 + y_off), (CX + line_w, CY + 42 + y_off)], fill=(215, 200, 170, int(130 * a)), width=1)
            if t < 8.5:
                cred = "PRODUCED BY SOUNWAVE · JACK ANTONOFF · KAMASI WASHINGTON · SCOTT BRIDGEWAY"
                draw_tracked_text(d, CX, H - BAR_H - 42, cred, FONTS["hud"], (185, 182, 178, int(145 * a)), tracking=2)

    # 2. Closing Title Card (173.4s - 177.6s)
    if t >= 173.4:
        a_in = ease_out_cubic((t - 173.4) / 1.6)
        a_out = 1.0 - smoothstep(176.5, 177.6, t)
        a = max(0.0, min(1.0, a_in * a_out))
        if a > 0.01:
            draw_tracked_text(d, CX, CY - 68, "luther", FONTS["title_big"], (242, 240, 235, int(245 * a)), tracking=14)
            draw_tracked_text(d, CX, CY + 60, "IF THIS WORLD WERE MINE", FONTS["title_sub"], (215, 200, 175, int(185 * a)), tracking=8)

    # 3. Active SRT Lyric Cue
    active = None
    for c in cues:
        if c["idx"] >= 5 and c["t0"] <= t <= c["t1"]:
            active = c
            break

    if active is not None:
        idx = active["idx"]
        dur = max(0.25, active["t1"] - active["t0"])
        el, rem = t - active["t0"], active["t1"] - t
        a_in = ease_out_cubic(el / min(0.32, dur * 0.35))
        a_out = ease_out_cubic(rem / min(0.28, dur * 0.30))
        alpha = max(0.0, min(1.0, a_in * a_out))
        text, zh = active["text"], active["zh"]

        if idx == 10:
            hits = [(26.10, "FAH"), (27.40, "FAH"), (28.45, "FAH · FAH"),
                    (29.57, "FAH"), (30.87, "FAH · FAH"), (31.95, "FAH"), (33.03, "FAH")]
            cur_word, dt_hit = "FAH", 1.0
            for ht, hw in hits:
                if t >= ht - 0.04:
                    cur_word, dt_hit = hw, max(0.0, t - ht)
            pop = math.exp(-dt_hit * 4.5)
            fa_alpha = int(max(40, min(255, (0.35 + 0.65 * pop) * 255)))
            y_jolt = int(-18 * pop)
            font_f = FONTS["fah_huge"] if len(cur_word) <= 4 else FONTS["title_big"]
            bbox = d.textbbox((0, 0), cur_word, font=font_f)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if pop > 0.15:
                off = int(10 * pop)
                d.text((CX - tw//2 - off, CY - th//2 - 14 + y_jolt), cur_word, font=font_f, fill=(255, 85, 70, int(150 * pop)))
                d.text((CX - tw//2 + off, CY - th//2 - 14 + y_jolt), cur_word, font=font_f, fill=(255, 220, 120, int(150 * pop)))
            d.text((CX - tw//2, CY - th//2 - 14 + y_jolt), cur_word, font=font_f, fill=(255, 248, 232, fa_alpha))

        elif idx in (5, 24, 38, 50):
            y_slide = int((1.0 - a_in) * 22)
            font_l = FONTS["luther"]
            bbox = d.textbbox((0, 0), text, font=font_l)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            d.text((CX - tw // 2, CY - th // 2 - 12 + y_slide), text, font=font_l, fill=(255, 232, 185, int(250 * alpha)))
            lw = int(55 * alpha)
            d.line([(CX - tw//2 - 22 - lw, CY - 4 + y_slide), (CX - tw//2 - 22, CY - 4 + y_slide)], fill=(255, 215, 145, int(170 * alpha)), width=1)
            d.line([(CX + tw//2 + 22, CY - 4 + y_slide), (CX + tw//2 + 22 + lw, CY - 4 + y_slide)], fill=(255, 215, 145, int(170 * alpha)), width=1)
            if zh:
                zb = d.textbbox((0, 0), zh, font=FONTS["zh"])
                d.text((CX - (zb[2]-zb[0]) // 2, CY + 36 + y_slide), zh, font=FONTS["zh"], fill=(245, 228, 200, int(195 * alpha)))

        elif "(" in text and ")" in text:
            parts = re.findall(r"\([^)]+\)|[^()]+", text)
            main_str = " ".join(p.strip() for p in parts if not p.strip().startswith("(") and p.strip())
            main_str = re.sub(r"\s+([,.;!?])", r"\1", main_str)
            adlib_str = "   ·   ".join(p.strip("() ") for p in parts if p.strip().startswith("("))
            y_slide = int((1.0 - a_in) * 20)
            mb = d.textbbox((0, 0), main_str, font=FONTS["kendrick"])
            d.text((CX - (mb[2]-mb[0]) // 2, CY - 46 + y_slide), main_str, font=FONTS["kendrick"], fill=(252, 248, 242, int(250 * alpha)))
            a_sza = ease_out_cubic(max(0.0, (el - 0.14)) / 0.35) * a_out
            ab = d.textbbox((0, 0), adlib_str, font=FONTS["sza_adlib"])
            d.text((CX - (ab[2]-ab[0]) // 2, CY + 16 + int((1.0 - a_sza) * 14)), adlib_str, font=FONTS["sza_adlib"], fill=(255, 185, 208, int(245 * a_sza)))
            if zh:
                zb = d.textbbox((0, 0), zh, font=FONTS["zh"])
                d.text((CX - (zb[2]-zb[0]) // 2, CY + 68 + y_slide), zh, font=FONTS["zh"], fill=(238, 222, 232, int(195 * alpha)))

        else:
            is_sza = idx in (17, 18, 19, 20, 21, 22, 23, 31, 32, 33, 34, 35, 36, 37, 46, 47, 48, 49)
            font_use = FONTS["sza"] if is_sza else (FONTS["kendrick"] if len(text) < 44 else FONTS["kendrick_sm"])
            words = text.split()
            lines = wrap_words(d, words, font_use, W - 240)
            line_h = 56 if font_use != FONTS["kendrick_sm"] else 48
            total_h = len(lines) * line_h
            y_start = CY - total_h // 2 - 14

            total_words = max(1, len(words))
            word_idx = 0
            for li, line_words in enumerate(lines):
                line_str = " ".join(line_words)
                lb = d.textbbox((0, 0), line_str, font=font_use)
                cur_x = CX - (lb[2] - lb[0]) // 2
                ly = y_start + li * line_h
                for w in line_words:
                    w_start = (word_idx / total_words) * min(dur * 0.50, 1.25)
                    wp = ease_out_cubic((el - w_start) / 0.28)
                    # Unrevealed words start at balanced 22% ghost opacity so layout is always symmetrical!
                    vis_a = (0.22 * a_in + 0.78 * wp) * a_out
                    wy = ly + int((1.0 - wp) * 8)
                    clean_w = w.lower().strip(".,!?\"'")
                    if clean_w in POWER_WORDS or w.lower() in POWER_WORDS:
                        col = (255, 214, 130, int(255 * vis_a)) if not is_sza else (255, 195, 215, int(255 * vis_a))
                    else:
                        col = (252, 249, 244, int(250 * vis_a)) if not is_sza else (255, 240, 244, int(250 * vis_a))
                    d.text((cur_x, wy), w, font=font_use, fill=col)
                    wb = d.textbbox((0, 0), w + " ", font=font_use)
                    cur_x += (wb[2] - wb[0])
                    word_idx += 1

            if zh:
                zb = d.textbbox((0, 0), zh, font=FONTS["zh"])
                d.text((CX - (zb[2]-zb[0]) // 2, y_start + total_h + 18 + int((1.0 - a_in) * 10)),
                       zh, font=FONTS["zh"], fill=(240, 232, 220, int(200 * alpha)))

    # Ultra-fast OpenCV shadow + numpy alpha composite!
    t_arr = np.array(txt_layer)
    t_rgb = t_arr[:, :, :3].astype(np.float32)
    t_a = t_arr[:, :, 3].astype(np.float32) / 255.0

    # Soft dark halo shadow for razor-sharp contrast
    sh_a = cv2.GaussianBlur(t_a, (17, 17), 0) * 0.88
    out = frame_rgb.astype(np.float32) * (1.0 - sh_a[:, :, None])
    out = out * (1.0 - t_a[:, :, None]) + t_rgb * t_a[:, :, None]
    out_u8 = np.clip(out, 0, 255).astype(np.uint8)

    # Cinema Letterbox Bars (pure numpy slice = 0.05ms!)
    out_u8[:BAR_H, :, :] = 5
    out_u8[H - BAR_H:, :, :] = 5

    # Minimalist HUD drawn directly onto PIL of just the top/bottom strips or full image
    pil_out = Image.fromarray(out_u8)
    hd = ImageDraw.Draw(pil_out)
    _, roman, act_label = get_act_info(t)
    hd.text((34, 14), "luther  ·  KENDRICK LAMAR & SZA", font=FONTS["hud"], fill=(175, 170, 162))
    act_str = f"ACT {roman}  —  {act_label}"
    ab = hd.textbbox((0, 0), act_str, font=FONTS["hud"])
    hd.text((W - 34 - (ab[2] - ab[0]), 14), act_str, font=FONTS["hud"], fill=(215, 192, 155))

    prog = max(0.0, min(1.0, t / 177.6))
    bar_x0, bar_x1, bar_y = 34, W - 110, H - 22
    hd.line([(bar_x0, bar_y), (bar_x1, bar_y)], fill=(65, 62, 60), width=2)
    px = int(bar_x0 + (bar_x1 - bar_x0) * prog)
    hd.line([(bar_x0, bar_y), (px, bar_y)], fill=(240, 198, 128), width=2)
    hd.ellipse([(px - 3, bar_y - 3), (px + 3, bar_y + 3)], fill=(255, 232, 180))
    mm, ss = int(t // 60), int(t % 60)
    hd.text((W - 92, H - 30), f"{mm:02d}:{ss:02d} / 02:57", font=FONTS["hud"], fill=(175, 170, 162))

    # 35mm Film Cue Dot near act transitions
    for trans_t in [10.1, 26.3, 53.8, 83.1, 104.2, 133.5, 170.2]:
        if 0.0 <= (t - (trans_t - 0.5)) <= 0.35:
            hd.ellipse([(W - 46, BAR_H + 16), (W - 30, BAR_H + 32)], outline=(245, 235, 215), width=2)
            hd.ellipse([(W - 41, BAR_H + 21), (W - 35, BAR_H + 27)], fill=(245, 235, 215))

    return np.array(pil_out)

# =====================================================================
# MASTER FRAME RENDERER
# =====================================================================
G_FEATS = None
G_CUES = None


CONTOUR_SHARP = None
CONTOUR_BLOOM = None

def build_marble_contour_bust_no_mic():
    """
    Pre-render Classical Style II (Topographic Marble Relief Contours) of the singer bust ONLY
    (microphone completely removed!) as crisp float32 sharp + bloom luminance masks centered at CX.
    """
    img = cv2.imread(REF_BUST_IMG)
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)
    b, g, r = cv2.split(img.astype(np.float32) / 255.0)
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    lum = 0.299 * r + 0.587 * g + 0.114 * b

    # Remove warm golden background splatters
    is_bg_gold = np.clip((sat - 0.14) * 5.0, 0.0, 1.0)
    clean_lum = lum * (1.0 - is_bg_gold)

    # STRICTLY isolate ONLY the bust/head/shoulders — completely exclude the left-side microphone & boom!
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # Bust is located around x=545..950, y=140..720; mic was around x<535, y<380
    w_bust = np.exp(-(((xx - 680.0) / 265.0) ** 2 + ((yy - 455.0) / 315.0) ** 2) ** 1.7)
    # Cleanly remove left-side microphone (x < 500) while preserving 100% of face profile (x >= 522)
    no_mic_cut = 1.0 / (1.0 + np.exp(-(xx - 512.0) / 5.0))
    field = clean_lum * w_bust * no_mic_cut

    # Center horizontally (bust center is ~705 -> shift left by 65px to CX=640) & lower slightly (+32px)
    field = np.roll(field, -65, axis=1)
    field[:, -65:] = 0.0
    field = np.roll(field, 8, axis=0)
    field[:8, :] = 0.0

    marble = cv2.bilateralFilter(field.astype(np.float32), 9, 0.12, 9)
    marble = np.clip(marble / (np.percentile(marble, 99.3) + 1e-6), 0.0, 1.0)
    smooth_m = cv2.GaussianBlur(marble, (11, 11), 0)

    # Render crisp multi-level topographic contour lines via PyCairo
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    levels = [0.09, 0.15, 0.22, 0.30, 0.38, 0.47, 0.56, 0.65, 0.74, 0.83, 0.91]
    for li, lv in enumerate(levels):
        mask = (smooth_m >= lv).astype(np.uint8) * 255
        cnts, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        frac = li / float(len(levels) - 1)
        val = 0.26 + 0.74 * frac
        ctx.set_source_rgba(val, val, val, val)
        ctx.set_line_width(0.75 + 1.15 * frac)
        for c in cnts:
            if len(c) < 18:
                continue
            pts = c[::3, 0, :]
            ctx.move_to(float(pts[0][0]), float(pts[0][1]))
            for p in pts[1:]:
                ctx.line_to(float(p[0]), float(p[1]))
            ctx.close_path()
            ctx.stroke()

    buf = np.frombuffer(surf.get_data(), dtype=np.uint8).reshape((H, W, 4))
    sharp = buf[:, :, 0].astype(np.float32) / 255.0
    small = cv2.resize(sharp, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    bloom = cv2.GaussianBlur(small, (11, 11), 0)
    bloom = cv2.resize(bloom, (W, H), interpolation=cv2.INTER_LINEAR)
    return sharp, bloom

def blend_bg_marble_silhouette(canvas, t, voc, sub, kick):
    """
    Blend the Classical Style II Marble Relief Contour bust into the BACKGROUND layer
    (behind all foreground motifs & lyrics), color-harmonized seamlessly to every Act!
    """
    # Gentle fade in after opening title card (from 9.5s) and gentle fade out into closing card (173.5s)
    vis = smoothstep(9.2, 11.2, t) * (1.0 - smoothstep(172.5, 175.0, t))
    if vis <= 0.005:
        return

    # Harmonized BGR tint matching each Act's exact palette
    kf_t = [0.0, 9.8, 12.6, 26.3, 33.4, 53.8, 69.6, 83.1, 104.2, 120.0, 133.5, 160.3, 170.0, 178.0]
    kf_col = [
        (210, 210, 215), # mono silver
        (215, 215, 220),
        (115, 198, 250), # Act II gold
        (90, 165, 255),  # Fah fire gold
        (125, 180, 250), # Verse 2 warm amber
        (185, 150, 235), # Concrete flowers rose-gold
        (150, 185, 250), # Eclipse champagne-gold
        (165, 130, 235), # Nocturnal duet rose-violet
        (165, 180, 245), # Chorus 2 rose-gold
        (125, 205, 255), # Radiant eclipse gold
        (135, 190, 245), # Devotion 80s amber
        (140, 205, 255), # Better days gold
        (210, 210, 215), # Return to mono silver
        (180, 180, 185),
    ]
    i = 0
    while i < len(kf_t) - 2 and t > kf_t[i+1]:
        i += 1
    c_bgr = lerp_color(kf_col[i], kf_col[i+1], smoothstep(kf_t[i], kf_t[i+1], t))

    # Subtle breathing motion & vocal-reactive background luminance (stays subtle so foreground pops!)
    dx = int(math.sin(t * 0.65) * 4)
    dy = int(math.cos(t * 0.90) * 3)
    sh = np.roll(np.roll(CONTOUR_SHARP, dy, axis=0), dx, axis=1)
    bl = np.roll(np.roll(CONTOUR_BLOOM, dy, axis=0), dx, axis=1)

    # Keep background silhouette refined and non-intrusive (around 0.34..0.58 strength)
    strength = (0.42 + 0.18 * voc + 0.08 * sub + 0.06 * kick) * vis
    combined = (sh * 0.85 + bl * 0.55) * strength
    canvas[:, :, 0] += combined * c_bgr[0]
    canvas[:, :, 1] += combined * c_bgr[1]
    canvas[:, :, 2] += combined * c_bgr[2]

def init_worker():
    global G_FEATS, G_CUES, CONTOUR_SHARP, CONTOUR_BLOOM
    init_fonts()
    CONTOUR_SHARP, CONTOUR_BLOOM = build_marble_contour_bust_no_mic()
    d = np.load(FEAT_PATH)
    G_FEATS = {k: d[k] for k in d.files}
    G_CUES = parse_srt(SRT_PATH)

def render_frame(f_idx):
    t = f_idx / float(FPS)
    sub  = float(G_FEATS["sub"][f_idx])
    low  = float(G_FEATS["low"][f_idx])
    voc  = float(G_FEATS["voc"][f_idx])
    hi   = float(G_FEATS["hi"][f_idx])
    kick = float(G_FEATS["kick"][f_idx])
    spec = G_FEATS["spec"][f_idx]

    canvas = compute_background(t, sub, low, voc, hi, kick)
    blend_bg_marble_silhouette(canvas, t, voc, sub, kick)

    if t < 13.8:
        a1 = 1.0 - smoothstep(12.2, 13.6, t)
        scene_monochrome_atrium(canvas, t, low, voc, sub, alpha_scale=a1, reverse=False)
        draw_particles(canvas, t, sub, voc, (195, 195, 200) if t < 10.1 else (90, 195, 255), upward=True, density=0.45)

    if 12.0 <= t <= 26.8:
        a2 = smoothstep(12.0, 13.4, t) * (1.0 - smoothstep(25.8, 26.6, t))
        scene_roman_vii_astrolabe(canvas, t, sub, voc, kick, spec, alpha_scale=a2)
        draw_particles(canvas, t, sub, voc, (80, 190, 255), upward=True, density=0.75)

    if 26.0 <= t <= 33.8:
        scene_fah_shockwaves(canvas, t, kick, sub)
        draw_particles(canvas, t, sub, voc, (65, 150, 255), upward=True, density=1.0)

    if 33.0 <= t <= 54.5:
        a4 = smoothstep(33.0, 34.4, t) * (1.0 - smoothstep(53.0, 54.4, t))
        scene_roman_vii_astrolabe(canvas, t, sub, voc, kick, spec, alpha_scale=a4 * 0.72)
        scene_silk_ribbons(canvas, t, voc, low, sub, (70, 175, 255), (105, 85, 240), alpha_scale=a4)
        draw_particles(canvas, t, sub, voc, (85, 175, 255), upward=True, density=0.85)

    if 53.2 <= t <= 70.4:
        a5 = smoothstep(53.2, 54.6, t) * (1.0 - smoothstep(69.0, 70.3, t))
        scene_concrete_flowers(canvas, t, (t - 53.5) / 16.0, voc, sub, alpha_scale=a5, golden_boost=0.15)
        draw_particles(canvas, t, sub, voc, (165, 125, 245), upward=True, density=0.85)

    if 68.8 <= t <= 83.8:
        a6 = smoothstep(68.8, 70.2, t) * (1.0 - smoothstep(82.4, 83.7, t))
        scene_solar_eclipse(canvas, t, voc, sub, kick, spec, alpha_scale=a6, intensity_boost=1.0)
        draw_particles(canvas, t, sub, voc, (110, 185, 255), upward=True, density=0.75)

    if 82.5 <= t <= 104.8:
        a7 = smoothstep(82.5, 83.8, t) * (1.0 - smoothstep(103.5, 104.7, t))
        scene_nocturnal_duet(canvas, t, sub, voc, kick, spec, alpha_scale=a7)
        draw_particles(canvas, t, sub, voc, (130, 115, 245), upward=False, density=0.65)

    if 103.6 <= t <= 120.6:
        a8 = smoothstep(103.6, 104.9, t) * (1.0 - smoothstep(119.3, 120.5, t))
        scene_concrete_flowers(canvas, t, (t - 103.8) / 15.0, voc, sub, alpha_scale=a8, golden_boost=0.55)
        draw_particles(canvas, t, sub, voc, (135, 165, 255), upward=True, density=0.95)

    if 119.2 <= t <= 134.2:
        a9 = smoothstep(119.2, 120.6, t) * (1.0 - smoothstep(132.8, 134.1, t))
        scene_solar_eclipse(canvas, t, voc, sub, kick, spec, alpha_scale=a9, intensity_boost=1.22)
        draw_particles(canvas, t, sub, voc, (95, 200, 255), upward=True, density=0.95)

    if 133.0 <= t <= 161.0:
        a10 = smoothstep(133.0, 134.6, t) * (1.0 - smoothstep(159.5, 160.9, t))
        scene_devotion_window(canvas, t, voc, low, sub, alpha_scale=a10)
        draw_particles(canvas, t, sub, voc, (110, 185, 245), upward=True, density=0.65)

    if t >= 159.8:
        a11 = smoothstep(159.8, 161.4, t)
        scene_monochrome_atrium(canvas, t, low, voc, sub, alpha_scale=a11, reverse=True)
        draw_anamorphic_flare(canvas, 0, (95, 195, 255), (1.0 - smoothstep(169.8, 173.5, t)) * (0.42 + 0.42 * voc) * a11)
        draw_particles(canvas, t, sub, voc, (145, 185, 235), upward=True, density=0.55)

    zoom = 1.0 + 0.018 * kick + (0.025 * kick if (26.0 <= t <= 33.5 and kick > 0.35) else 0.0)
    if zoom > 1.003:
        nw, nh = int(W / zoom), int(H / zoom)
        x0, y0 = (W - nw) // 2, (H - nh) // 2
        canvas = cv2.resize(canvas[y0:y0+nh, x0:x0+nw], (W, H), interpolation=cv2.INTER_LINEAR)

    if 26.0 <= t <= 33.5 and kick > 0.48:
        shift = int(kick * 7)
        if shift > 0:
            canvas[:, shift:, 2] = canvas[:, :-shift, 2]
            canvas[:, :-shift, 0] = canvas[:, shift:, 0]

    if t > 169.8:
        desat = smoothstep(169.8, 173.8, t) * 0.92
        gray = (0.114 * canvas[:, :, 0] + 0.587 * canvas[:, :, 1] + 0.299 * canvas[:, :, 2])[:, :, None]
        canvas = canvas * (1.0 - desat) + gray * desat

    canvas *= VIGNETTE
    canvas += GRAIN_TILES[f_idx % 16]

    if t < 1.2:
        canvas *= smoothstep(0.0, 1.2, t)
    elif t > 176.2:
        canvas *= (1.0 - smoothstep(176.2, 177.6, t))

    frame_rgb = np.clip(canvas, 0, 255).astype(np.uint8)[:, :, ::-1]
    return render_typography_and_hud(frame_rgb, t, G_CUES, kick, voc, sub)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()

    if args.preview:
        init_worker()
        os.makedirs("/working_dir/c_2475b8aa144e36fd/work/previews", exist_ok=True)
        times = [18.0, 58.0, 75.5, 92.0, 145.0]
        t0 = time.time()
        imgs = []
        for ts in times:
            f_idx = min(int(ts * FPS), int(G_FEATS["n_frames"]) - 1)
            imgs.append((ts, render_frame(f_idx)))
        dt = time.time() - t0
        print(f"Pure render speed: {dt/len(times)*1000:.1f} ms/frame (est. 2-core total for 5328 frames: {dt/len(times)*5328/2:.0f}s)")
        for idx_t, (ts, rgb) in enumerate(imgs):
            Image.fromarray(rgb).save(f"/working_dir/c_2475b8aa144e36fd/work/previews/v3_{idx_t:02d}_{ts:05.1f}s.png")

    if args.full:
        d = np.load(FEAT_PATH)
        n_frames = int(d["n_frames"])
        print(f"Rendering full MV: {n_frames} frames ({n_frames/FPS:.2f}s) -> {OUT_MP4}", flush=True)
        t0 = time.time()
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-",
            "-i", MP3_PATH,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-maxrate", "3600k", "-bufsize", "7200k",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "256k",
            "-shortest",
            OUT_MP4
        ]
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
        with Pool(processes=2, initializer=init_worker) as pool:
            for i, rgb in enumerate(pool.imap(render_frame, range(n_frames), chunksize=20)):
                proc.stdin.write(rgb.tobytes())
                if (i + 1) % 600 == 0 or i + 1 == n_frames:
                    el = time.time() - t0
                    fps_cur = (i + 1) / max(0.01, el)
                    print(f"  Progress: {i+1}/{n_frames} ({100*(i+1)/n_frames:.1f}%) | {el:.1f}s elapsed | {fps_cur:.1f} fps", flush=True)
        proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"ffmpeg failed with exit code {ret}")
        print(f"DONE! Total render time: {time.time() - t0:.1f}s | File size: {os.path.getsize(OUT_MP4)/1e6:.2f} MB", flush=True)

if __name__ == "__main__":
    main()

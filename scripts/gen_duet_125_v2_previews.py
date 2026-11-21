#!/usr/bin/env python3
"""Update Scene 5 (exact consistent wavy hair) and Scene 6 (sacred symmetrical centered
celestial star-river) and output the full 2x3 Style II preview board (v3)."""
import math
import numpy as np
import cv2
import cairo
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
CX, CY = W // 2, H // 2
BAR_H = 44

TOOL_DIR = "/working_dir/c_2475b8aa144e36fd/user_uploaded_files/ttl=63d/tool_generated"
F_SANS_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_CJK_REG   = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"

GOLD_COLOR = (112, 202, 255)   # BGR
SZA_COLOR  = (192, 148, 245)   # BGR
FROST_GOLD = (232, 224, 255)   # BGR

IMG_S1 = f"{TOOL_DIR}/watermarked_img_1851624638319278491.jpg"   # P4_EMB
IMG_S2 = f"{TOOL_DIR}/watermarked_img_9133214644071712511.jpg"   # Female looking at lower-right palm
IMG_S3 = f"{TOOL_DIR}/watermarked_img_6387655686324784955.jpg"   # Slow dance
IMG_S4 = f"{TOOL_DIR}/watermarked_img_16428730941476397623.jpg"  # Female hand on chest (flip_x -> left hand)
IMG_S5 = f"{TOOL_DIR}/watermarked_img_16484560350832102734.jpg"  # UPDATED Scene 5: exact consistent long wavy hair!
IMG_S6 = f"{TOOL_DIR}/watermarked_img_1868938928751587062.jpg"   # UPDATED Scene 6: sacred centered symmetrical male!

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
ped = np.clip((H - BAR_H - yy) / 38.0, 0.0, 1.0)
vig = np.clip(1.0 - 0.52 * (((xx - CX)/(W*0.55))**2 + ((yy - CY)/(H*0.55))**2), 0.30, 1.0)[:, :, None]

def load_marble(path, scale=0.84, y_shift=48, flip_x=False):
    img = cv2.imread(path)
    if flip_x:
        img = cv2.flip(img, 1)
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    sw, sh = int(W * scale), int(H * scale)
    small = cv2.resize(gray, (sw, sh), interpolation=cv2.INTER_AREA)
    field = np.zeros((H, W), dtype=np.float32)
    ox = (W - sw) // 2
    oy = max(0, min(H - sh, (H - sh) // 2 + y_shift))
    field[oy:oy+sh, ox:ox+sw] = small
    marble = cv2.bilateralFilter(field, 9, 0.15, 9)
    p99 = np.percentile(marble, 99.4) + 1e-6
    return np.clip(marble / p99, 0.0, 1.0)

def render_contour(field):
    smooth_m = cv2.GaussianBlur(field, (9, 9), 0)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    levels = [0.09, 0.16, 0.24, 0.32, 0.41, 0.50, 0.59, 0.68, 0.77, 0.85, 0.92]
    n_lv = len(levels)
    for li, lv in enumerate(levels):
        mask = (smooth_m >= lv).astype(np.uint8) * 255
        cnts, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        frac = li / float(n_lv - 1)
        val = 0.24 + 0.76 * frac
        lw = 0.85 + 1.25 * frac
        ctx.set_source_rgba(val, val, val, val)
        ctx.set_line_width(lw)
        for c in cnts:
            if len(c) < 16:
                continue
            pts = c[::3, 0, :]
            if len(pts) < 4:
                continue
            ctx.move_to(float(pts[0][0]), float(pts[0][1]))
            for p in pts[1:]:
                ctx.line_to(float(p[0]), float(p[1]))
            ctx.close_path()
            ctx.stroke()
    sharp = np.frombuffer(surf.get_data(), dtype=np.uint8).reshape((H, W, 4))[:, :, 0].astype(np.float32) / 255.0
    small = cv2.resize(sharp, (W // 3, H // 3), interpolation=cv2.INTER_AREA)
    bloom = cv2.resize(cv2.GaussianBlur(small, (11, 11), 0), (W, H), interpolation=cv2.INTER_LINEAR)
    return sharp * 0.88 + bloom * 0.55

def make_bg():
    bg = np.zeros((H, W, 3), dtype=np.float32)
    bg[:, :, 0] = 24.0
    bg[:, :, 1] = 14.0
    bg[:, :, 2] = 28.0
    return bg * vig

def draw_greco_roman_star(canvas, cx, cy, r_outer, color_bgr, intensity=1.0):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for rad, lw, a in [(r_outer * 1.18, 1.3, 0.55), (r_outer * 1.04, 0.9, 0.40), (r_outer * 0.42, 1.4, 0.72)]:
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.set_line_width(lw)
        ctx.arc(cx, cy, rad, 0, 2 * math.pi)
        ctx.stroke()
    ctx.set_source_rgba(1, 1, 1, 0.55)
    ctx.set_line_width(1.0)
    for k in range(32):
        ang = (k / 32.0) * 2 * math.pi
        r0 = r_outer * (1.04 if k % 4 == 0 else 1.10)
        r1 = r_outer * 1.18
        ctx.move_to(cx + math.cos(ang)*r0, cy + math.sin(ang)*r0)
        ctx.line_to(cx + math.cos(ang)*r1, cy + math.sin(ang)*r1)
        ctx.stroke()
    for scale_r, lw, a in [(1.00, 1.8, 0.95), (0.76, 1.4, 0.80), (0.52, 1.2, 0.65)]:
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.set_line_width(lw)
        for i in range(16):
            ang = (i / 16.0) * 2 * math.pi - math.pi / 2.0
            rad = r_outer * scale_r * ((1.0 if i % 4 == 0 else 0.76) if i % 2 == 0 else 0.22)
            px, py = cx + math.cos(ang) * rad, cy + math.sin(ang) * rad
            ctx.move_to(px, py) if i == 0 else ctx.line_to(px, py)
        ctx.close_path()
        ctx.stroke()
    ctx.set_source_rgba(1, 1, 1, 0.48)
    ctx.set_line_width(1.0)
    for i in range(8):
        ang = (i / 8.0) * 2 * math.pi + math.pi / 8.0
        ctx.move_to(cx + math.cos(ang) * r_outer * 0.28, cy + math.sin(ang) * r_outer * 0.28)
        ctx.line_to(cx + math.cos(ang) * r_outer * 1.38, cy + math.sin(ang) * r_outer * 1.38)
        ctx.stroke()
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.arc(cx, cy, r_outer * 0.11, 0, 2 * math.pi)
    ctx.fill()
    sh = np.frombuffer(surf.get_data(), dtype=np.uint8).reshape((H, W, 4))[:, :, 3].astype(np.float32) / 255.0
    bl = cv2.GaussianBlur(sh, (31, 31), 0)
    halo = np.exp(-(((xx - cx) / (r_outer * 1.4)) ** 2 + ((yy - cy) / (r_outer * 1.4)) ** 2)) * 0.32
    tot = (sh * 0.98 + bl * 0.95 + halo) * intensity
    for ch in range(3):
        canvas[:, :, ch] += tot * min(255.0, color_bgr[ch] * 1.12 + 28.0)

def render_edge_gold_flames(canvas, t=2.4, intensity=0.95):
    bw, bh = 320, 180
    gy, gx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    fx, fy = gx / float(bw), 1.0 - (gy / float(bh))
    d_edge = np.minimum(np.minimum(fx / 0.34, (1.0 - fx) / 0.34), fy / 0.30)
    wx = np.sin(fx * 8.0 + np.cos(fy * 6.0 - t * 3.8) * 1.4) * 0.12
    wy = np.cos(fx * 7.0 - fy * 5.0 + t * 3.4) * 0.12
    u, v = fx + wx, fy - t * 1.05 + wy
    turb = (0.48 * np.sin(u*12.0 + np.sin(v*7.5)*1.6) * np.cos(v*7.0 - u*4.5) +
            0.28 * np.sin(u*22.0 - v*14.0 + t*2.5) * np.cos(u*16.0 + v*11.0) +
            0.16 * np.cos(u*34.0 + v*24.0 - t*4.2))
    heat = np.clip(1.0 - d_edge + turb * 0.44, 0.0, 1.0) * intensity
    heat = cv2.GaussianBlur(heat.astype(np.float32), (5, 5), 0)
    heat_full = np.clip(cv2.resize(heat, (W, H), interpolation=cv2.INTER_CUBIC), 0.0, 1.0)
    heat_full[:BAR_H, :] = 0.0
    heat_full[H - BAR_H:, :] = 0.0
    layer = np.zeros((H, W, 3), dtype=np.uint8)
    levels = [0.16, 0.26, 0.36, 0.46, 0.56, 0.66, 0.76, 0.85]
    for li, lv in enumerate(levels):
        mask = (heat_full >= lv).astype(np.uint8) * 255
        cnts, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        frac = li / float(len(levels) - 1)
        col = (int(min(255, GOLD_COLOR[0]*(0.50+0.68*frac) + 45*(frac**2))),
               int(min(255, GOLD_COLOR[1]*(0.55+0.55*frac) + 45*(frac**2))),
               int(min(255, GOLD_COLOR[2]*(0.75+0.30*frac))))
        lw = 1 if li < 3 else 2
        for c in cnts:
            if len(c) >= 14:
                cv2.polylines(layer, [np.ascontiguousarray(c[::2], dtype=np.int32)], False, col, lw, cv2.LINE_AA)
    small = cv2.resize(layer, (W // 3, H // 3), interpolation=cv2.INTER_AREA)
    bloom = cv2.resize(cv2.GaussianBlur(small, (13, 13), 0), (W, H), interpolation=cv2.INTER_LINEAR)
    canvas += layer.astype(np.float32) * 0.85 + bloom.astype(np.float32) * 0.95

def draw_frost_crown_rays(canvas, cx, cy_crown, cy_wrist):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for rad, lw, a in [(155, 1.3, 0.45), (215, 0.9, 0.28)]:
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.set_line_width(lw)
        ctx.arc(cx, cy_crown, rad, 0, 2 * math.pi)
        ctx.stroke()
    for k in range(24):
        ang = (k / 24.0) * 2 * math.pi
        r0 = 95 if k % 2 == 0 else 125
        r1 = 290 if k % 4 == 0 else (220 if k % 2 == 0 else 175)
        ctx.set_source_rgba(1, 1, 1, 0.62 if k % 4 == 0 else 0.34)
        ctx.set_line_width(1.6 if k % 4 == 0 else 0.9)
        ctx.move_to(cx + math.cos(ang)*r0, cy_crown + math.sin(ang)*r0)
        ctx.line_to(cx + math.cos(ang)*r1, cy_crown + math.sin(ang)*r1)
        ctx.stroke()
        if k % 4 == 0:
            ctx.arc(cx + math.cos(ang)*(r1 + 8), cy_crown + math.sin(ang)*(r1 + 8), 3.0, 0, 2 * math.pi)
            ctx.fill()
    for sx, sy, sr in [(cx - 56, cy_wrist, 26), (cx + 56, cy_wrist, 26), (cx, cy_wrist + 6, 36)]:
        ctx.set_source_rgba(1, 1, 1, 0.72)
        ctx.set_line_width(1.3)
        for a_deg in [0, 45, 90, 135]:
            ar = math.radians(a_deg)
            l = sr if a_deg in (0, 90) else sr * 0.55
            ctx.move_to(sx - math.cos(ar)*l, sy - math.sin(ar)*l)
            ctx.line_to(sx + math.cos(ar)*l, sy + math.sin(ar)*l)
            ctx.stroke()
    sh = np.frombuffer(surf.get_data(), dtype=np.uint8).reshape((H, W, 4))[:, :, 3].astype(np.float32) / 255.0
    bl = cv2.GaussianBlur(sh, (25, 25), 0)
    tot = sh * 0.85 + bl * 0.78
    for ch in range(3):
        canvas[:, :, ch] += tot * FROST_GOLD[ch]

def draw_sacred_rose_star_river(canvas, t=1.6):
    """Sacred Renaissance-fresco symmetrical SZA Rose-Violet celestial halo + twin cascading
    star-rivers descending from the heavens into Male's outstretched palms and heart."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

    # 1. Sacred concentric celestial cathedral halo behind his head (CX, 225)
    hx, hy = CX, 232.0
    for rad, lw, a in [(135, 1.4, 0.52), (175, 1.0, 0.36), (265, 1.1, 0.28), (340, 0.8, 0.18)]:
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.set_line_width(lw)
        ctx.arc(hx, hy, rad, 0, 2 * math.pi)
        ctx.stroke()
    # Fine sacred sunbeam rays from behind his head
    for k in range(36):
        ang = (k / 36.0) * 2 * math.pi
        r0 = 138.0
        r1 = 365.0 if k % 3 == 0 else 255.0
        ctx.set_source_rgba(1, 1, 1, 0.34 if k % 3 == 0 else 0.16)
        ctx.set_line_width(1.2 if k % 3 == 0 else 0.7)
        ctx.move_to(hx + math.cos(ang)*r0, hy + math.sin(ang)*r0)
        ctx.line_to(hx + math.cos(ang)*r1, hy + math.sin(ang)*r1)
        ctx.stroke()

    # 2. Twin symmetrical cascading rose-violet star-rivers pouring from upper-left & upper-right heavens,
    #    flowing gracefully across his outstretched palms and converging into a radiant vortex at his heart!
    for side in (-1.0, 1.0):
        for i in range(11):
            frac = i / 10.0
            phase = frac * 3.4 + t * 1.2
            lw = 0.75 + 1.45 * math.sin(frac * math.pi)
            a = 0.26 + 0.62 * math.sin(frac * math.pi)
            ctx.set_source_rgba(1, 1, 1, a)
            ctx.set_line_width(lw)
            pts = []
            for s in range(85):
                u = s / 84.0  # 0 = upper heaven corner, 0.55 = outstretched palm, 1.0 = heart center (CX, 445)
                # Sweeps gracefully from outer upper heavens down to palm then arcs up-inward to his heart
                x_path = CX + side * (660.0 * ((1.0 - u) ** 1.15) + 95.0 * math.sin(u * math.pi * 1.4))
                y_path = 48.0 + 495.0 * math.sin(u * math.pi * 0.65) - 65.0 * (u ** 2.2)
                spread = (frac - 0.5) * (155.0 * (1.0 - 0.72 * u) + 22.0 * math.sin(u * 7.0 + phase))
                x = x_path + side * spread * 0.45 + math.cos(u * 8.0 + phase) * 10.0
                y = y_path + spread * 0.72 + math.sin(u * 7.5 - phase) * 12.0
                pts.append((x, y))
            ctx.move_to(pts[0][0], pts[0][1])
            for px, py in pts[1:]:
                ctx.line_to(px, py)
            ctx.stroke()

    # 3. Sacred descending stardust droplets + subtle glowing heart-star at his chest (CX, 440)
    rng = np.random.default_rng(7777)
    for _ in range(140):
        side = -1.0 if rng.random() < 0.5 else 1.0
        u = rng.uniform(0.02, 0.98)
        x_p = CX + side * (650.0 * ((1.0 - u) ** 1.15) + 90.0 * math.sin(u * math.pi * 1.4))
        y_p = 50.0 + 490.0 * math.sin(u * math.pi * 0.65) - 65.0 * (u ** 2.2)
        px = x_p + rng.normal(0, 42 * (1.0 - 0.4 * u))
        py = y_p + rng.normal(0, 48 * (1.0 - 0.4 * u))
        ctx.set_source_rgba(1, 1, 1, rng.uniform(0.32, 0.92))
        ctx.arc(px, py, rng.uniform(1.0, 2.8), 0, 2 * math.pi)
        ctx.fill()

    sh = np.frombuffer(surf.get_data(), dtype=np.uint8).reshape((H, W, 4))[:, :, 3].astype(np.float32) / 255.0
    small = cv2.resize(sh, (W // 3, H // 3), interpolation=cv2.INTER_AREA)
    bl = cv2.resize(cv2.GaussianBlur(small, (13, 13), 0), (W, H), interpolation=cv2.INTER_LINEAR)
    # Soft sacred rose-violet radiance behind his head & over his heart
    aura_head = np.exp(-(((xx - CX) / 260.0) ** 2 + ((yy - 232.0) / 220.0) ** 2)) * 0.22
    aura_heart = np.exp(-(((xx - CX) / 135.0) ** 2 + ((yy - 445.0) / 110.0) ** 2)) * 0.20
    tot = sh * 0.90 + bl * 0.88 + aura_head + aura_heart
    for ch in range(3):
        canvas[:, :, ch] += tot * min(255.0, SZA_COLOR[ch] * 1.08 + 18.0)

f_title = ImageFont.truetype(F_CJK_REG, 21)
f_sub   = ImageFont.truetype(F_SANS_BOLD, 15)

def finish_tile(bg, title, lyric):
    rgb = np.clip(bg, 0, 255).astype(np.uint8)[:, :, ::-1]
    rgb[:BAR_H, :, :] = 0
    rgb[H - BAR_H:, :, :] = 0
    pil = Image.fromarray(cv2.resize(rgb, (640, 360), interpolation=cv2.INTER_AREA))
    d = ImageDraw.Draw(pil)
    d.rectangle([(0, 0), (640, 56)], fill=(12, 10, 16))
    d.text((14, 6), title, font=f_title, fill=(248, 228, 178))
    d.text((14, 34), lyric, font=f_sub, fill=(215, 195, 228))
    return np.array(pil)

tiles = []

# Scene 1
bg = make_bg()
f1 = load_marble(IMG_S1, 0.84, 48) * ped
w_r = np.clip((xx - (CX - 6)) / 28.0 + 0.5, 0.0, 1.0)
c_l, c_r = render_contour(f1 * (1.0 - w_r)), render_contour(f1 * w_r)
for ch in range(3):
    bg[:, :, ch] += c_l * 0.88 * GOLD_COLOR[ch] + c_r * 0.90 * SZA_COLOR[ch]
tiles.append(finish_tile(bg, "1 | 01:23–01:27  保留现有 · 额头相抵", "It go in (when you), out (ride it), do it real slow"))

# Scene 2
bg = make_bg()
f2 = load_marble(IMG_S2, 0.86, 46) * ped
c2 = render_contour(f2)
for ch in range(3):
    bg[:, :, ch] += c2 * 0.92 * SZA_COLOR[ch]
draw_greco_roman_star(bg, cx=965, cy=360, r_outer=92, color_bgr=GOLD_COLOR, intensity=1.05)
tiles.append(finish_tile(bg, "2 | 01:27–01:30  掌中金星 · 女主先出 → 金星浮现", "Baby, you a star, strike a pose"))

# Scene 3
bg = make_bg()
f3 = load_marble(IMG_S3, 0.84, 48) * ped
w_r = np.clip((xx - (CX + 15)) / 36.0 + 0.5, 0.0, 1.0)
c_l, c_r = render_contour(f3 * (1.0 - w_r)), render_contour(f3 * w_r)
for ch in range(3):
    bg[:, :, ch] += c_l * 0.88 * GOLD_COLOR[ch] + c_r * 0.90 * SZA_COLOR[ch]
tiles.append(finish_tile(bg, "3 | 01:30–01:34  保留慢舞 · 双人错开共步", "When I'm (when you), with you (with me), everything goes (slow)"))

# Scene 4
bg = make_bg()
f4 = load_marble(IMG_S4, 0.84, 46, flip_x=True) * ped
c4 = render_contour(f4)
for ch in range(3):
    bg[:, :, ch] += c4 * 0.92 * SZA_COLOR[ch]
render_edge_gold_flames(bg, t=2.4, intensity=0.95)
tiles.append(finish_tile(bg, "4 | 01:34–01:37  灵魂圣火 · 左手抚胸 → 金火四面包围", "Come and (Put that), put that (On my), on my soul"))

# UPDATED Scene 5: Consistent cascading long wavy hair + monumental floating laurel crown!
bg = make_bg()
f5 = load_marble(IMG_S5, 0.86, 42) * ped
# Crown sits cleanly above her head (y < 235)
w_crown = np.clip((232.0 - yy) / 22.0, 0.0, 1.0)
c5_f = render_contour(f5 * (1.0 - w_crown))
c5_c = render_contour(f5 * w_crown)
for ch in range(3):
    bg[:, :, ch] += c5_f * 0.92 * SZA_COLOR[ch] + c5_c * 1.02 * GOLD_COLOR[ch]
draw_frost_crown_rays(bg, cx=CX, cy_crown=165, cy_wrist=520)
tiles.append(finish_tile(bg, "5 | 01:37–01:41  冰霜加冕 · 长卷发一致 → 圣冠寒霜降临", "'Rari (Red), crown (Stack), wrist (Stay), froze (Really)"))

# UPDATED Scene 6: Sacred symmetrical centered Male + twin cascading SZA Rose-Violet star-rivers + cathedral halo!
bg = make_bg()
draw_sacred_rose_star_river(bg, t=1.6)
f6 = load_marble(IMG_S6, 0.86, 52) * ped
c6 = render_contour(f6)
for ch in range(3):
    bg[:, :, ch] += c6 * 0.96 * GOLD_COLOR[ch]
tiles.append(finish_tile(bg, "6 | 01:41–01:44  圣殿星河 · 居中仰首张臂 → 双星河归怀", "Drip (tell me), pound (if you), on the way home (love me)"))

# Save both full 2x3 board AND high-res 1x2 zoom of just Scene 5 & Scene 6
grid = np.vstack([np.hstack(tiles[0:3]), np.hstack(tiles[3:6])])
out_full = "/working_dir/c_2475b8aa144e36fd/artifacts/file_generation/ttl=63d/output/act4_125_v3_mythic_preview.png"
Image.fromarray(grid).save(out_full)
print("Saved v3 mythic preview board:", out_full, grid.shape)

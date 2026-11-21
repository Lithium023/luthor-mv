#!/usr/bin/env python3
"""Render a 2x2 side-by-side preview of 4 curated Greco-Roman typography schemes
directly over actual MV frames (Act IV Greco Star + SZA Concrete Rose + Title) so the user
can compare them in real visual context."""
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import render_mv_720p_master as m

m.init_worker_1080()

# Grab two iconic clean background frames WITHOUT typography by temporarily capturing canvas before text
# Even simpler: render the frame cleanly at t=88.8s (Act IV Star) with typography disabled via a tiny wrapper
def get_clean_bg_frame(ts):
    # Temporarily stub render_clean_typography_1080 to only apply black letterbox bars
    orig = m.render_clean_typography_1080
    def _no_txt(rgb, t):
        out = rgb.copy()
        out[:m.BAR_H, :, :] = 0
        out[m.H - m.BAR_H:, :, :] = 0
        return out
    m.render_clean_typography_1080 = _no_txt
    try:
        rgb = m.render_frame_1080(int(ts * 30))
    finally:
        m.render_clean_typography_1080 = orig
    return rgb

bg_star = get_clean_bg_frame(88.8)

F_CJK_REG = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
F_LM_CAPS = "/usr/share/texmf/fonts/opentype/public/lm/lmromancaps10-regular.otf"
F_LM_BOLD = "/usr/share/texmf/fonts/opentype/public/lm/lmroman10-bold.otf"
F_PAG_REG = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-regular.otf"
F_PAG_BLD = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-bold.otf"
F_PAG_ITA = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-italic.otf"
F_NSD_REG = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Regular.ttf"
F_NSD_BLD = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf"
F_NSD_ITA = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Italic.ttf"
F_CHORUS  = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrechorus-mediumitalic.otf"

SCHEMES = [
    (
        "方案 A · 古罗马石碑铭文（Roman Small Caps）",
        "主歌词 LM Roman Caps 小型大写 + SZA 帕拉蒂诺斜体",
        ImageFont.truetype(F_LM_CAPS, 66),    # title
        ImageFont.truetype(F_LM_CAPS, 44),    # kendrick
        ImageFont.truetype(F_PAG_ITA, 38),    # sza
        ImageFont.truetype(F_CJK_REG, 22),    # zh
        True,  # wide tracking on main
    ),
    (
        "方案 B · 文艺复兴帕拉蒂诺（Renaissance Pagella）",
        "主歌词 TeX Gyre Pagella 雕凿衬线 + 帕拉蒂诺斜体",
        ImageFont.truetype(F_PAG_ITA, 74),
        ImageFont.truetype(F_PAG_BLD, 46),
        ImageFont.truetype(F_PAG_ITA, 40),
        ImageFont.truetype(F_CJK_REG, 22),
        False,
    ),
    (
        "方案 C · 新古典高反差展示体（Neoclassical Display）",
        "主歌词 Noto Serif Display 高反差衬线 + 纤雅斜体",
        ImageFont.truetype(F_NSD_ITA, 76),
        ImageFont.truetype(F_NSD_BLD, 46),
        ImageFont.truetype(F_NSD_ITA, 40),
        ImageFont.truetype(F_CJK_REG, 22),
        False,
    ),
    (
        "方案 D · 石刻铭文 × 古典手写花体（Caps + Chorus）",
        "男声 LM Roman Caps 铭文 + 女声 TeX Gyre Chorus 花体",
        ImageFont.truetype(F_CHORUS, 82),
        ImageFont.truetype(F_LM_CAPS, 44),
        ImageFont.truetype(F_CHORUS, 46),
        ImageFont.truetype(F_CJK_REG, 22),
        True,
    ),
]

def draw_tracked(draw, cx, y, text, font, fill, tracking=2):
    if tracking == 0:
        bb = draw.textbbox((0, 0), text, font=font)
        draw.text((cx - (bb[2]-bb[0])//2, y), text, font=font, fill=fill)
        return
    widths = [draw.textbbox((0, 0), ch, font=font)[2] - draw.textbbox((0, 0), ch, font=font)[0] for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = cx - total // 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking

f_hdr  = ImageFont.truetype(F_CJK_REG, 24)
f_desc = ImageFont.truetype(F_CJK_REG, 16)

tiles = []
for name, desc, f_title, f_main, f_sza, f_zh, wide_tr in SCHEMES:
    frame = bg_star.copy()
    txt = Image.new("RGBA", (m.W, m.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)

    # Top-left small title sample ("luther")
    draw_tracked(d, m.CX, 118, "luther", f_title, (248, 232, 195, 240), tracking=8 if wide_tr else 5)

    # Main Kendrick lyric sample (center)
    draw_tracked(d, m.CX, 286, "Baby, you a star, strike a pose", f_main, (254, 248, 236, 255), tracking=3 if wide_tr else 1)

    # SZA italic / chorus lyric sample below
    draw_tracked(d, m.CX, 368, "In this world, concrete flowers grow", f_sza, (255, 212, 232, 245), tracking=1)

    # Chinese classical serif subtitle with subtle wider tracking
    draw_tracked(d, m.CX, 444, "宝 贝 你 是 星 辰 ， 尽 情 定 格 锋 芒", f_zh, (242, 232, 214, 215), tracking=2)

    t_arr = np.array(txt)
    t_a = t_arr[:, :, 3].astype(np.float32) / 255.0
    sh = cv2.GaussianBlur(t_a, (17, 17), 0) * 0.90
    out = frame.astype(np.float32) * (1.0 - sh[:, :, None])
    out = out * (1.0 - t_a[:, :, None]) + t_arr[:, :, :3].astype(np.float32) * t_a[:, :, None]
    out_u8 = np.clip(out, 0, 255).astype(np.uint8)
    out_u8[:m.BAR_H, :, :] = 0
    out_u8[m.H - m.BAR_H:, :, :] = 0

    pil = Image.fromarray(cv2.resize(out_u8, (800, 450), interpolation=cv2.INTER_AREA))
    dh = ImageDraw.Draw(pil)
    dh.rectangle([(0, 0), (800, 62)], fill=(12, 10, 16))
    dh.text((18, 6), name, font=f_hdr, fill=(250, 228, 175))
    dh.text((18, 36), desc, font=f_desc, fill=(215, 200, 228))
    tiles.append(np.array(pil))

grid = np.vstack([np.hstack(tiles[0:2]), np.hstack(tiles[2:4])])
out_path = "/working_dir/c_2475b8aa144e36fd/artifacts/file_generation/ttl=63d/output/greco_roman_font_previews.png"
Image.fromarray(grid).save(out_path)
print("Saved Greco-Roman font preview board:", out_path, grid.shape)

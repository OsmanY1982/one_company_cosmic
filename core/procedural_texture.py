# -*- coding: utf-8 -*-
"""
程序化天体纹理生成器 — 为无真实纹理的卫星/矮行星生成类Perlin噪声表面
"""
import numpy as np


def _upsample_2d(grid, target_h, target_w):
    """纯 numpy 双线性插值上采样，替代 scipy.ndimage.zoom"""
    src_h, src_w = grid.shape
    y_ratio = np.linspace(0, src_h - 1, target_h)
    x_ratio = np.linspace(0, src_w - 1, target_w)
    y0 = np.floor(y_ratio).astype(int)
    y1 = np.minimum(y0 + 1, src_h - 1)
    x0 = np.floor(x_ratio).astype(int)
    x1 = np.minimum(x0 + 1, src_w - 1)
    wy = (y_ratio - y0)[:, None]
    wx = (x_ratio - x0)[None, :]
    q00 = grid[y0[:, None], x0[None, :]]
    q10 = grid[y1[:, None], x0[None, :]]
    q01 = grid[y0[:, None], x1[None, :]]
    q11 = grid[y1[:, None], x1[None, :]]
    return (1 - wy) * (1 - wx) * q00 + wy * (1 - wx) * q10 + (1 - wy) * wx * q01 + wy * wx * q11


def _fbm_noise(width, height, seed=0, octaves=4, lacunarity=2.0, gain=0.5):
    """分形布朗运动噪声 (2D)，纯 numpy 实现"""
    np.random.seed(seed)
    noise = np.zeros((height, width), dtype=np.float64)
    max_val = 0.0
    
    for octave in range(octaves):
        freq = lacunarity ** octave
        amp = gain ** octave
        max_val += amp
        
        nx = max(2, int(width / (8 * freq)))
        ny = max(2, int(height / (8 * freq)))
        grid = np.random.rand(ny, nx).astype(np.float64) * 2 - 1
        
        if nx != width or ny != height:
            upscaled = _upsample_2d(grid, height, width)
        else:
            upscaled = grid
        
        noise += amp * upscaled
    
    noise /= max_val
    return np.clip(noise, -1, 1)


def _apply_colormap(noise, colors, contrast=1.2):
    """将噪声映射到颜色梯度"""
    h, w = noise.shape
    # 归一化到 [0, 1]
    n = np.clip((noise - noise.min()) / (noise.max() - noise.min() + 1e-8), 0, 1)
    n = np.power(n, 1.0 / contrast)  # 对比度调整
    
    result = np.zeros((h, w, 3), dtype=np.uint8)
    n_segments = len(colors) - 1
    
    for i in range(n_segments):
        t0 = i / n_segments
        t1 = (i + 1) / n_segments
        mask = (n >= t0) & (n < t1)
        if i == n_segments - 1:
            mask = n >= t0
        
        frac = np.clip((n[mask] - t0) / (t1 - t0 + 1e-8), 0, 1)
        c0 = np.array(colors[i], dtype=np.float64)
        c1 = np.array(colors[i + 1], dtype=np.float64)
        
        for ch in range(3):
            result[:, :, ch][mask] = (c0[ch] + (c1[ch] - c0[ch]) * frac).astype(np.uint8)
    
    return result


def make_crater_noise(noise, crater_count=30, min_r=2, max_r=8):
    """在噪声图上叠加陨石坑"""
    h, w = noise.shape
    result = noise.copy()
    np.random.seed(42)
    
    for _ in range(crater_count):
        cx = np.random.randint(0, w)
        cy = np.random.randint(0, h)
        r = np.random.randint(min_r, max_r)
        
        yv, xv = np.ogrid[:h, :w]
        dist = np.sqrt((xv - cx)**2 + (yv - cy)**2)
        mask = dist <= r
        
        # 陨石坑：中心暗，边缘亮
        depth_mask = mask.astype(np.float64) * (1.0 - np.clip(dist / (r + 1e-8), 0, 1) * 0.8)
        result -= depth_mask * 0.3
    
    return np.clip(result, -1, 1)


# ── 预设卫星纹理配置 ──

MOON_TEXTURE_PRESETS = {
    "io": {
        "colors": [(200, 160, 30), (220, 180, 50), (170, 120, 20), (240, 200, 80),
                    (160, 100, 10), (200, 150, 40)],
        "octaves": 5, "contrast": 1.5,
    },
    "europa": {
        "colors": [(200, 205, 210), (220, 225, 230), (180, 185, 195), (210, 215, 220),
                    (230, 235, 240), (195, 200, 205)],
        "octaves": 4, "contrast": 1.8,
    },
    "ganymede": {
        "colors": [(120, 110, 100), (140, 130, 115), (100, 90, 80), (155, 140, 125),
                    (90, 80, 70), (130, 120, 105)],
        "octaves": 5, "contrast": 1.4,
    },
    "callisto": {
        "colors": [(80, 75, 70), (100, 95, 90), (60, 55, 50), (90, 85, 80),
                    (70, 65, 60), (110, 105, 100)],
        "octaves": 4, "contrast": 1.3,
    },
    "titan": {
        "colors": [(180, 140, 60), (210, 170, 80), (150, 110, 40), (200, 160, 70),
                    (170, 130, 50), (220, 180, 90)],
        "octaves": 3, "contrast": 1.2,
    },
    "enceladus": {
        "colors": [(230, 235, 240), (240, 245, 250), (220, 225, 230), (235, 240, 245),
                    (245, 248, 252), (225, 230, 235)],
        "octaves": 5, "contrast": 2.0,
    },
}


def generate_moon_texture(body_key, width=256, height=128):
    """
    为指定卫星生成等角矩形程序化纹理。
    返回 (H, W, 4) RGBA numpy 数组，可直接送入 texture_mapper。
    """
    import sys
    preset = MOON_TEXTURE_PRESETS.get(body_key)
    if preset is None:
        return None
    
    noise = _fbm_noise(width, height, seed=hash(body_key) % 2**31,
                        octaves=preset["octaves"], gain=0.55)
    
    # 陨石坑叠加（欧罗巴和恩克拉多斯除了冰裂缝外也有小陨石坑）
    if body_key in ("ganymede", "callisto"):
        noise = make_crater_noise(noise, crater_count=40 if body_key == "callisto" else 25,
                                  min_r=2, max_r=10)
    
    rgb = _apply_colormap(noise, preset["colors"], contrast=preset["contrast"])
    
    # 拼接成 RGBA
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[:, :, :3] = rgb
    rgba[:, :, 3] = 255
    
    return rgba

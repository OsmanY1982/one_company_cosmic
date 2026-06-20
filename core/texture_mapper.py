# -*- coding: utf-8 -*-
"""
球面纹理映射引擎
将等角矩形投影 (equirectangular) 纹理 → 球面正交投影 (orthographic)
纯 numpy 实现，生成 QImage 直接供 QPainter::drawImage 使用
"""
import numpy as np
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt


def _load_texture_array(path):
    """加载等角矩形纹理为 RGBA numpy 数组"""
    img = QImage(path)
    if img.isNull():
        return None
    img = img.convertToFormat(QImage.Format_RGBA8888)
    w, h = img.width(), img.height()
    ptr = img.bits()
    ptr.setsize(h * w * 4)
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, w, 4)).copy()
    return arr


# 纹理缓存: {path: (tex_array, timestamp)}
_texture_cache = {}


def load_texture(path):
    """加载并缓存纹理"""
    import os
    if not os.path.isfile(path):
        return None
    mtime = os.path.getmtime(path)
    if path in _texture_cache:
        cached_arr, cached_mtime = _texture_cache[path]
        if cached_mtime == mtime:
            return cached_arr
    arr = _load_texture_array(path)
    if arr is not None:
        _texture_cache[path] = (arr, mtime)
    return arr


def _fast_equirect_to_ortho(tex_arr, diameter):
    """
    等角矩形纹理 → 球面正交投影（向量化 numpy）
    tex_arr: (H, W, 4) RGBA uint8 array
    diameter: 输出直径 (px)
    return: (diameter, diameter, 4) RGBA uint8 array
    """
    r = diameter / 2.0
    tex_h, tex_w = tex_arr.shape[0], tex_arr.shape[1]

    # 生成输出坐标网格
    yv, xv = np.mgrid[0:diameter, 0:diameter].astype(np.float64)
    dx = (xv - r + 0.5) / r      # [-1, 1]
    dy = (yv - r + 0.5) / r      # [-1, 1]
    dz2 = 1.0 - dx*dx - dy*dy

    # 球面可见区域 mask
    mask = dz2 > 0
    dz = np.sqrt(np.maximum(dz2, 0))

    # 球面法线 → 等角矩形纹理坐标
    u = 0.5 + np.arctan2(dx, dz) / (2.0 * np.pi)
    v = 0.5 - np.arcsin(np.clip(dy, -1.0, 1.0)) / np.pi

    # 纹理坐标 → 像素索引
    tx = np.clip((u * tex_w).astype(np.int32), 0, tex_w - 1)
    ty = np.clip((v * tex_h).astype(np.int32), 0, tex_h - 1)

    result = np.zeros((diameter, diameter, 4), dtype=np.uint8)
    result[mask] = tex_arr[ty[mask], tx[mask]]

    return result


def _apply_lighting(sphere_arr, light_angle_deg=45, ambient=0.3):
    """
    在球面纹理上叠加方向光照明 (Lambertian + 环境光)
    light_angle_deg: 光线从左上角照射的角度
    """
    d = sphere_arr.shape[0]
    r = d / 2.0
    yv, xv = np.mgrid[0:d, 0:d].astype(np.float64)
    dx = (xv - r + 0.5) / r
    dy = (yv - r + 0.5) / r
    dz2 = 1.0 - dx*dx - dy*dy
    mask = dz2 > 0
    dz = np.sqrt(np.maximum(dz2, 0))

    # 光线方向（单位向量，从左上角照射）
    import math
    rad = math.radians(light_angle_deg)
    light_x = -math.sin(rad) * 0.6
    light_y = -math.sin(rad) * 0.6
    light_z = 1.0
    light_len = math.sqrt(light_x**2 + light_y**2 + light_z**2)
    lx, ly, lz = light_x / light_len, light_y / light_len, light_z / light_len

    diffuse = np.maximum(dx * lx + dy * ly + dz * lz, 0.0)
    lighting = np.clip(ambient + (1.0 - ambient) * diffuse, 0.0, 1.0)

    # 应用到 RGB 通道
    lit = sphere_arr.astype(np.float64)
    lit[:, :, 0] *= lighting
    lit[:, :, 1] *= lighting
    lit[:, :, 2] *= lighting
    lit[:, :, 3] = sphere_arr[:, :, 3].astype(np.float64)

    # 球体边缘暗角
    edge_factor = np.where(mask, np.abs(dz), 0.0)
    edge_alpha = np.clip(edge_factor * 1.5, 0.0, 1.0)
    lit[:, :, 3] *= edge_alpha

    return np.clip(lit, 0, 255).astype(np.uint8)


def render_sphere(tex_arr, diameter, light_angle=45, ambient=0.25):
    """
    全流程: 纹理加载 → 球面映射 → 光照 → QPixmap
    """
    if tex_arr is None:
        return None
    sphere = _fast_equirect_to_ortho(tex_arr, diameter)
    sphere = _apply_lighting(sphere, light_angle, ambient)
    img = QImage(sphere.data, diameter, diameter, diameter * 4, QImage.Format_RGBA8888)
    return QPixmap.fromImage(img.copy())  # copy to detach from numpy buffer


# ── 预生成缓存，避免每帧重复映射 ──
# {(tex_path, diameter): QPixmap}
_render_cache = {}
CACHE_MAX_SIZE = 128


def get_sphere_pixmap(tex_path, diameter, light_angle=45):
    """获取缓存的球面贴图，缓存未命中时生成"""
    if not tex_path:
        return None

    key = (tex_path, diameter, light_angle)
    if key in _render_cache:
        return _render_cache[key]

    tex = load_texture(tex_path)
    if tex is None:
        return None

    pix = render_sphere(tex, diameter, light_angle)
    if pix is None:
        return None

    # LRU 驱逐
    if len(_render_cache) >= CACHE_MAX_SIZE:
        oldest = next(iter(_render_cache))
        del _render_cache[oldest]

    _render_cache[key] = pix
    return pix


def clear_cache():
    """清除所有缓存"""
    global _texture_cache, _render_cache
    _texture_cache.clear()
    _render_cache.clear()

# -*- coding: utf-8 -*-
"""
天体百科数据 — 加载器 (306 天体)
从 body_data_entries 加载 33 颗主要天体的详细数据，
其余 273 颗小卫星通过模板自动生成简介。
"""
import math
from modules.astronomy.star_catalog.data_entries import PLANET_ENTRIES, MOON_ENTRIES

# ═══════════════════════════════════════════════════════
# 从 solar_system_data 获取天体目录
# ═══════════════════════════════════════════════════════

def _load_catalog():
    """加载 solar_system_data 中的 SOLAR_CATALOG"""
    from modules.astronomy.solar_system.data import SOLAR_CATALOG
    return SOLAR_CATALOG


# ═══════════════════════════════════════════════════════
# 小卫星模板生成器
# ═══════════════════════════════════════════════════════

def _gen_moon_summary(body):
    """为小卫星生成简介模板"""
    parent_name = body.get("parent_name", "")
    name = body.get("name", "")
    radius = body.get("radius_km", 0)
    orbit = body.get("orbit_km", 0)

    size_desc = _size_desc(radius)
    orbit_desc = _orbit_desc(orbit)
    return (
        f"{name}是{parent_name}的一颗{size_desc}卫星，直径约{int(radius * 2)}公里。"
        f"它沿{orbit_desc}轨道绕行{parent_name}，是IAU已命名的太阳系天体之一。"
    )


def _gen_moon_physics(body):
    """为小卫星生成物理特征"""
    radius = body.get("radius_km", 0)
    period = body.get("period_d", 0)
    lines = [
        f"直径约{int(radius * 2)}公里，由冰和岩石混合组成。表面布满撞击坑，没有大气层。",
    ]
    if period:
        if period < 1:
            lines.append(f"公转周期仅约{period * 24:.1f}小时，是{body.get('parent_name', '其母行星')}最内侧的卫星之一。")
        elif period < 10:
            lines.append(f"公转周期约{period:.1f}地球日，轨道稳定。")
        else:
            lines.append(f"公转周期约{period:.0f}地球日，属于外层卫星。")
    return " ".join(lines)


def _gen_moon_facts(body):
    """为小卫星生成趣味事实"""
    facts = ["是IAU（国际天文学联合会）正式命名的太阳系天体"]
    radius = body.get("radius_km", 0)
    orbit = body.get("orbit_km", 0)
    if radius < 10:
        facts.append(f"直径仅约{int(radius * 2)}公里，形状极不规则")
    if orbit > 10_000_000:
        facts.append(f"轨道距离母行星超过{orbit / 1_000_000:.0f}百万公里，属于远距离逆行卫星群")
    return facts


def _size_desc(radius_km):
    if radius_km >= 500:
        return "大型"
    elif radius_km >= 50:
        return "中型"
    elif radius_km >= 10:
        return "小型"
    else:
        return "微型不规则"


def _orbit_desc(orbit_km):
    if orbit_km < 100_000:
        return "极近的"
    elif orbit_km < 500_000:
        return "近距"
    elif orbit_km < 5_000_000:
        return "中距"
    else:
        return "远距"


def _parent_cn_name(parent_id):
    """获取母天体中文名"""
    mapping = {
        "sun": "太阳", "mercury": "水星", "venus": "金星", "earth": "地球",
        "mars": "火星", "jupiter": "木星", "saturn": "土星", "uranus": "天王星",
        "neptune": "海王星", "pluto": "冥王星", "eris": "阋神星",
        "ceres": "谷神星", "haumea": "妊神星", "makemake": "鸟神星",
    }
    return mapping.get(parent_id, parent_id)


def _parent_style(parent_id):
    mapping = {
        "sun": "sun", "mercury": "mercury", "venus": "venus", "earth": "earth",
        "mars": "mars", "jupiter": "jupiter", "saturn": "saturn", "uranus": "uranus",
        "neptune": "neptune", "pluto": "pluto", "eris": "pluto",
        "ceres": "mercury", "haumea": "mars", "makemake": "pluto",
    }
    return mapping.get(parent_id, "neptune")


# ═══════════════════════════════════════════════════════
# BODIES 构建
# ═══════════════════════════════════════════════════════
_BODIES = None


def _build_bodies():
    """懒加载：构建 306 天体的百科字典"""
    global _BODIES
    if _BODIES is not None:
        return _BODIES

    catalog = _load_catalog()
    bodies = {}

    for body_id, body in catalog.items():
        if body_id in PLANET_ENTRIES:
            # 行星/矮行星/太阳 — 使用详细数据
            entry = dict(PLANET_ENTRIES[body_id])
            # 补充物理数据字段
            entry.setdefault("diameter_km", body.get("radius_km", 0) * 2)
            entry.setdefault("mass_kg", "—")
            entry.setdefault("temp_surface_c", "—")
            entry.setdefault("distance_au", 0)
            entry.setdefault("orbit_period_days", body.get("period_d", 0))
            entry.setdefault("rotation_period_hours", 0)
            entry.setdefault("discovered_year", "—")
            entry.setdefault("discovered_by", "—")
            entry.setdefault("style", body.get("style", "neptune"))
            entry["catalog_id"] = body_id
            bodies[body_id] = entry

        elif body.get("name_en") in MOON_ENTRIES:
            # 大卫星 — 使用详细数据
            entry = dict(MOON_ENTRIES[body["name_en"]])
            entry.setdefault("diameter_km", body.get("radius_km", 0) * 2)
            entry.setdefault("mass_kg", "—")
            entry.setdefault("temp_surface_c", "—")
            entry.setdefault("distance_au", 0)
            entry.setdefault("orbit_period_days", body.get("period_d", 0))
            entry.setdefault("rotation_period_hours", 0)
            entry.setdefault("discovered_year", "—")
            entry.setdefault("discovered_by", "—")
            entry.setdefault("style", body.get("style", _parent_style(body.get("parent", ""))))
            entry["catalog_id"] = body_id
            bodies[body_id] = entry

        else:
            # 小卫星 — 模板生成
            parent_id = body.get("parent", "")
            parent_name = _parent_cn_name(parent_id)
            body_with_parent = dict(body)
            body_with_parent["parent_name"] = parent_name

            bodies[body_id] = {
                "name": body.get("name_en", body.get("name", "")),
                "name_cn": body.get("name", ""),
                "type": "moon",
                "parent": parent_name,
                "summary": _gen_moon_summary(body_with_parent),
                "physics": _gen_moon_physics(body_with_parent),
                "exploration": (
                    f"{body.get('name', '这颗卫星')}目前仅通过望远镜观测，"
                    f"尚未有探测器近距离飞掠。其基本信息来源于地面天文观测和空间望远镜数据。"
                ),
                "facts": _gen_moon_facts(body_with_parent),
                "diameter_km": body.get("radius_km", 0) * 2,
                "mass_kg": "—",
                "temp_surface_c": "—",
                "distance_au": 0,
                "orbit_period_days": body.get("period_d", 0),
                "rotation_period_hours": 0,
                "discovered_year": "—",
                "discovered_by": "—",
                "style": _parent_style(parent_id),
                "catalog_id": body_id,
            }

    _BODIES = bodies
    return bodies


def get_entry(body_id):
    """获取单个天体百科条目"""
    bodies = _build_bodies()
    return bodies.get(body_id)


def get_all_entries():
    """获取所有天体百科条目"""
    return list(_build_bodies().values())


def get_entries_by_type(body_type):
    """按类型筛选天体条目"""
    return [e for e in _build_bodies().values() if e.get("type") == body_type]


def get_entries_by_parent(parent_name):
    """按母天体筛选（卫星用）"""
    return [e for e in _build_bodies().values() if e.get("parent") == parent_name]


def get_statistics():
    """获取统计信息"""
    bodies = _build_bodies()
    stars = sum(1 for e in bodies.values() if e["type"] == "star")
    planets = sum(1 for e in bodies.values() if e["type"] == "planet")
    dwarfs = sum(1 for e in bodies.values() if e["type"] == "dwarf_planet")
    moons = sum(1 for e in bodies.values() if e["type"] == "moon")
    return {
        "total": len(bodies),
        "stars": stars,
        "planets": planets,
        "dwarfs": dwarfs,
        "moons": moons,
    }

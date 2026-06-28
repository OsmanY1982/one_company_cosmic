import logging

logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
"""
Multi-Channel Content Distribution Module
==========================================
一键分发到微信公众号、微博、知乎、Twitter/X、LinkedIn 等多平台。

核心 API:
    publish(platform, content, credentials)       → 单平台发布
    publish_all(content, platforms)                → 多平台同步发布
    schedule_publish(platform, content, execute_at) → 定时发布
    list_drafts()                                   → 列出草稿箱
    get_publish_history()                           → 发布历史

使用前先注册平台适配器:
    from iqra.core.multi_channel.platforms.wechat import WechatAdapter
    register_adapter("wechat", WechatAdapter())
"""

import os
import json
import traceback
import threading
import time as _time
from typing import Dict, Any, List, Optional

# ── 平台适配器注册表 ──
_ADAPTERS: Dict[str, Any] = {}
_ADAPTER_LOCK = threading.Lock()

# ── 发布历史（进程内存储）──
_PUBLISH_HISTORY: List[Dict[str, Any]] = []
_HISTORY_LOCK = threading.Lock()

# ── 项目根 ──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_DRAFTS_DIR = os.path.join(_PROJECT_ROOT, "data", "drafts")
os.makedirs(_DRAFTS_DIR, exist_ok=True)


def register_adapter(platform_name: str, adapter_instance) -> None:
    """注册平台适配器"""
    with _ADAPTER_LOCK:
        _ADAPTERS[platform_name] = adapter_instance


def unregister_adapter(platform_name: str) -> None:
    """注销平台适配器"""
    with _ADAPTER_LOCK:
        _ADAPTERS.pop(platform_name, None)


def list_adapters() -> List[str]:
    """列出已注册的平台适配器"""
    with _ADAPTER_LOCK:
        return list(_ADAPTERS.keys())


def get_adapter(platform_name: str):
    """获取平台适配器，未注册返回 None"""
    with _ADAPTER_LOCK:
        return _ADAPTERS.get(platform_name)


# ═══════════════════════════════════════════
# 发布核心 API
# ═══════════════════════════════════════════

def publish(platform: str, content: str, credentials: Optional[Dict[str, str]] = None,
            title: str = "", cover_image: str = "", extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    单平台发布

    Args:
        platform: 平台名称（wechat / weibo / zhihu / twitter / linkedin）
        content: 发布内容
        credentials: 认证凭据字典，不传则从环境变量读取
        title: 标题（文章类平台需要）
        cover_image: 封面图路径
        extra: 平台特定额外参数

    Returns:
        {"success": bool, "platform": str, "result": dict, "error": str}
    """
    adapter = get_adapter(platform)
    if adapter is None:
        # 尝试自动注册
        adapter = _auto_register(platform)
    if adapter is None:
        return {
            "success": False,
            "platform": platform,
            "error": f"平台 '{platform}' 未注册适配器，且无法自动注册",
        }

    try:
        credentials = credentials or {}
        # 尝试发布
        result = _do_publish(adapter, platform, content, title, cover_image, extra, credentials)
        # 记录历史
        _add_history(platform, content, result)
        return result
    except Exception as e:
        traceback.print_exc()
        return {
            "success": False,
            "platform": platform,
            "error": f"发布失败: {e}",
        }


def _do_publish(adapter, platform, content, title, cover_image, extra, credentials) -> Dict[str, Any]:
    """执行具体发布调用"""
    extra = extra or {}

    if platform == "wechat":
        if hasattr(adapter, "publish_article"):
            return adapter.publish_article(
                title=title or "无标题",
                content=content,
                cover_image=cover_image,
            )
        elif hasattr(adapter, "publish"):
            return adapter.publish(content=content, title=title, cover_image=cover_image)
    elif platform == "weibo":
        if hasattr(adapter, "post_status"):
            return adapter.post_status(text=content, images=extra.get("images"))
        elif hasattr(adapter, "publish"):
            return adapter.publish(content=content, images=extra.get("images"))
    elif platform == "zhihu":
        if hasattr(adapter, "create_article"):
            return adapter.create_article(title=title or "无标题", content=content)
        elif hasattr(adapter, "publish"):
            return adapter.publish(content=content, title=title)
    elif platform in ("twitter", "x", "linkedin"):
        if hasattr(adapter, "publish"):
            return adapter.publish(content=content, title=title)
        else:
            return {
                "success": False,
                "platform": platform,
                "error": f"适配器缺少 publish 方法",
            }

    # 通用 publish 方法
    if hasattr(adapter, "publish"):
        return adapter.publish(content=content, title=title, cover_image=cover_image, extra=extra)
    return {
        "success": False,
        "platform": platform,
        "error": "适配器无 publish 方法",
    }


def publish_all(content: str, platforms: Optional[List[str]] = None,
                title: str = "", cover_image: str = "",
                credentials: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    多平台同步发布

    Args:
        content: 发布内容
        platforms: 目标平台列表，不传则发布到所有已注册平台
        title: 标题
        cover_image: 封面图
        credentials: 多平台凭据字典 {platform: {...}}

    Returns:
        {"total": int, "success_count": int, "failed_count": int, "results": {...}}
    """
    if platforms is None:
        platforms = list_adapters()
    if not platforms:
        return {"total": 0, "success_count": 0, "failed_count": 0, "results": {}, "error": "没有可用的平台适配器"}

    results = {}
    success_count = 0
    failed_count = 0

    for plat in platforms:
        plat_creds = (credentials or {}).get(plat)
        r = publish(platform=plat, content=content, credentials=plat_creds,
                    title=title, cover_image=cover_image)
        results[plat] = r
        if r.get("success"):
            success_count += 1
        else:
            failed_count += 1

    return {
        "total": len(platforms),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results,
    }


def schedule_publish(platform: str, content: str, execute_at: str,
                     title: str = "", cover_image: str = "",
                     credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    定时发布

    Args:
        platform: 平台名称
        content: 发布内容
        execute_at: 执行时间（ISO 8601 格式）
        title: 标题
        cover_image: 封面图
        credentials: 认证凭据

    Returns:
        {"status": "scheduled", "platform": platform, "execute_at": str, "task_id": str}
    """
    task_id = f"publish_{platform}_{int(_time.time() * 1000)}"
    task = {
        "task_id": task_id,
        "platform": platform,
        "content": content[:200] + "..." if len(content) > 200 else content,
        "execute_at": execute_at,
        "title": title,
        "cover_image": cover_image,
        "status": "scheduled",
        "created_at": _time.time(),
    }
    # 保存为草稿，等定时器触发
    draft_path = os.path.join(_DRAFTS_DIR, f"scheduled_{task_id}.json")
    with open(draft_path, "w", encoding="utf-8") as f:
        json.dump(task, f, ensure_ascii=False, indent=2)

    return {
        "status": "scheduled",
        "platform": platform,
        "execute_at": execute_at,
        "task_id": task_id,
        "message": f"已安排于 {execute_at} 在 {platform} 发布",
    }


# ═══════════════════════════════════════════
# 草稿管理
# ═══════════════════════════════════════════

def list_drafts(platform: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出草稿箱"""
    drafts = []
    if not os.path.isdir(_DRAFTS_DIR):
        return drafts
    for fname in os.listdir(_DRAFTS_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(_DRAFTS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                draft = json.load(f)
            draft["_file"] = fpath
            draft["_id"] = fname.replace(".json", "")
            if platform is None or draft.get("platform") == platform:
                drafts.append(draft)
        except Exception:
            logger.exception("异常详情")
    # 按创建时间倒序
    drafts.sort(key=lambda d: d.get("created_at", 0), reverse=True)
    return drafts


def save_draft(platform: str, content: str, title: str = "",
               extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """保存草稿"""
    draft_id = f"draft_{platform}_{int(_time.time() * 1000)}"
    draft = {
        "draft_id": draft_id,
        "platform": platform,
        "title": title,
        "content": content,
        "extra": extra or {},
        "created_at": _time.time(),
        "status": "draft",
    }
    draft_path = os.path.join(_DRAFTS_DIR, f"{draft_id}.json")
    with open(draft_path, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)
    draft["_file"] = draft_path
    draft["_id"] = draft_id
    return draft


def load_draft(draft_id: str) -> Optional[Dict[str, Any]]:
    """加载草稿"""
    draft_path = os.path.join(_DRAFTS_DIR, f"{draft_id}.json")
    if not os.path.exists(draft_path):
        return None
    try:
        with open(draft_path, "r", encoding="utf-8") as f:
            draft = json.load(f)
        draft["_file"] = draft_path
        draft["_id"] = draft_id
        return draft
    except Exception:
        return None


def delete_draft(draft_id: str) -> bool:
    """删除草稿"""
    draft_path = os.path.join(_DRAFTS_DIR, f"{draft_id}.json")
    if os.path.exists(draft_path):
        os.remove(draft_path)
        return True
    return False


# ═══════════════════════════════════════════
# 发布历史
# ═══════════════════════════════════════════

def get_publish_history(platform: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """获取发布历史"""
    with _HISTORY_LOCK:
        history = list(_PUBLISH_HISTORY)
    if platform:
        history = [h for h in history if h.get("platform") == platform]
    return sorted(history, key=lambda h: h.get("timestamp", 0), reverse=True)[:limit]


def _add_history(platform: str, content: str, result: Dict[str, Any]) -> None:
    """记录发布历史"""
    entry = {
        "platform": platform,
        "content_preview": content[:200] + "..." if len(content) > 200 else content,
        "success": result.get("success", False),
        "result": result,
        "timestamp": _time.time(),
    }
    with _HISTORY_LOCK:
        _PUBLISH_HISTORY.append(entry)
        # 保留最近 200 条
        if len(_PUBLISH_HISTORY) > 200:
            _PUBLISH_HISTORY[:] = _PUBLISH_HISTORY[-200:]


# ═══════════════════════════════════════════
# 自动注册
# ═══════════════════════════════════════════

_AUTO_REGISTERED = False


def _auto_register(platform: str):
    """尝试自动注册平台适配器"""
    global _AUTO_REGISTERED
    try:
        if platform == "wechat":
            from .platforms.wechat import WechatAdapter
            adapter = WechatAdapter()
            register_adapter("wechat", adapter)
            return adapter
        elif platform == "weibo":
            from .platforms.weibo import WeiboAdapter
            adapter = WeiboAdapter()
            register_adapter("weibo", adapter)
            return adapter
        elif platform == "zhihu":
            from .platforms.zhihu import ZhihuAdapter
            adapter = ZhihuAdapter()
            register_adapter("zhihu", adapter)
            return adapter
        elif platform in ("twitter", "x"):
            from .platforms.twitter import TwitterAdapter
            adapter = TwitterAdapter()
            register_adapter("twitter", adapter)
            return adapter
        elif platform == "linkedin":
            from .platforms.linkedin import LinkedInAdapter
            adapter = LinkedInAdapter()
            register_adapter("linkedin", adapter)
            return adapter
    except ImportError:
        logger.exception("异常详情")
    return None


def auto_register_all() -> int:
    """自动注册所有可用平台适配器（从环境变量检测凭据）"""
    global _AUTO_REGISTERED
    if _AUTO_REGISTERED:
        return len(_ADAPTERS)
    _AUTO_REGISTERED = True
    count = 0
    try:
        if os.environ.get("WECHAT_APPID") and os.environ.get("WECHAT_APPSECRET"):
            from .platforms.wechat import WechatAdapter
            register_adapter("wechat", WechatAdapter())
            count += 1
    except ImportError:
        logger.exception("异常详情")
    try:
        if os.environ.get("WEIBO_ACCESS_TOKEN"):
            from .platforms.weibo import WeiboAdapter
            register_adapter("weibo", WeiboAdapter())
            count += 1
    except ImportError:
        logger.exception("异常详情")
    try:
        from .platforms.zhihu import ZhihuAdapter
        register_adapter("zhihu", ZhihuAdapter())
        count += 1
    except ImportError:
        logger.exception("异常详情")
    try:
        from .platforms.twitter import TwitterAdapter
        register_adapter("twitter", TwitterAdapter())
        count += 1
    except ImportError:
        logger.exception("异常详情")
    try:
        from .platforms.linkedin import LinkedInAdapter
        register_adapter("linkedin", LinkedInAdapter())
        count += 1
    except ImportError:
        logger.exception("异常详情")
    return count

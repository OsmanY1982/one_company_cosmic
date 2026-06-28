import logging

logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
"""
草稿管理器
==========
提供多平台的草稿 CRUD 操作，基于 JSON 文件存储。

存储路径: {项目根}/data/drafts/
"""

import os
import json
import time
import traceback
from typing import Dict, Any, List, Optional


class DraftManager:
    """草稿管理器"""

    def __init__(self, drafts_dir: str = ""):
        if not drafts_dir:
            _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            drafts_dir = os.path.join(_project_root, "data", "drafts")
        self.drafts_dir = drafts_dir
        os.makedirs(self.drafts_dir, exist_ok=True)

    # ── 保存草稿 ──

    def save_draft(self, platform: str, content: str,
                   title: str = "",
                   extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        保存草稿

        Args:
            platform: 平台名称
            content: 内容
            title: 标题
            extra: 额外元数据

        Returns:
            {"draft_id": str, "platform": str, "title": str, "_file": str}
        """
        draft_id = f"draft_{platform}_{int(time.time() * 1000)}"
        draft = {
            "draft_id": draft_id,
            "platform": platform,
            "title": title,
            "content": content,
            "extra": extra or {},
            "created_at": time.time(),
            "updated_at": time.time(),
            "status": "draft",
        }
        draft_path = os.path.join(self.drafts_dir, f"{draft_id}.json")
        try:
            with open(draft_path, "w", encoding="utf-8") as f:
                json.dump(draft, f, ensure_ascii=False, indent=2)
        except Exception as e:
            traceback.print_exc()
            return {"error": f"保存草稿失败: {e}"}
        draft["_file"] = draft_path
        draft["_id"] = draft_id
        return draft

    # ── 加载草稿 ──

    def load_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """
        加载草稿

        Args:
            draft_id: 草稿 ID

        Returns:
            草稿字典或 None
        """
        draft_path = os.path.join(self.drafts_dir, f"{draft_id}.json")
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

    # ── 列出草稿 ──

    def list_drafts(self, platform: Optional[str] = None,
                    status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出草稿

        Args:
            platform: 按平台过滤（可选）
            status: 按状态过滤（可选）

        Returns:
            草稿列表
        """
        drafts = []
        if not os.path.isdir(self.drafts_dir):
            return drafts
        for fname in sorted(os.listdir(self.drafts_dir), reverse=True):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(self.drafts_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    draft = json.load(f)
                if platform and draft.get("platform") != platform:
                    continue
                if status and draft.get("status") != status:
                    continue
                draft["_file"] = fpath
                draft["_id"] = fname.replace(".json", "")
                drafts.append(draft)
            except Exception:
                logger.exception("异常详情")
        drafts.sort(key=lambda d: d.get("updated_at", 0), reverse=True)
        return drafts

    # ── 更新草稿 ──

    def update_draft(self, draft_id: str, content: str = "",
                     title: str = "",
                     extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        更新草稿

        Args:
            draft_id: 草稿 ID
            content: 新内容（不传则不变）
            title: 新标题（不传则不变）
            extra: 新元数据（不传则不变）

        Returns:
            更新后的草稿
        """
        draft = self.load_draft(draft_id)
        if draft is None:
            return {"error": f"草稿 '{draft_id}' 不存在"}

        if content:
            draft["content"] = content
        if title:
            draft["title"] = title
        if extra is not None:
            draft["extra"] = extra
        draft["updated_at"] = time.time()

        draft_path = draft["_file"]
        try:
            with open(draft_path, "w", encoding="utf-8") as f:
                json.dump({k: v for k, v in draft.items()
                           if not k.startswith("_")},
                          f, ensure_ascii=False, indent=2)
        except Exception as e:
            return {"error": f"更新草稿失败: {e}"}
        return draft

    # ── 删除草稿 ──

    def delete_draft(self, draft_id: str) -> bool:
        """
        删除草稿

        Args:
            draft_id: 草稿 ID

        Returns:
            是否删除成功
        """
        draft_path = os.path.join(self.drafts_dir, f"{draft_id}.json")
        if os.path.exists(draft_path):
            try:
                os.remove(draft_path)
                return True
            except Exception:
                traceback.print_exc()
        return False

    # ── 统计 ──

    def get_stats(self) -> Dict[str, Any]:
        """获取草稿统计"""
        all_drafts = self.list_drafts()
        platforms = {}
        for d in all_drafts:
            plat = d.get("platform", "unknown")
            platforms[plat] = platforms.get(plat, 0) + 1
        return {
            "total": len(all_drafts),
            "by_platform": platforms,
        }

    # ── 批量删除 ──

    def delete_by_platform(self, platform: str) -> int:
        """批量删除某平台的所有草稿"""
        drafts = self.list_drafts(platform=platform)
        count = 0
        for d in drafts:
            if self.delete_draft(d["_id"]):
                count += 1
        return count

    def delete_all(self) -> int:
        """删除所有草稿"""
        drafts = self.list_drafts()
        count = 0
        for d in drafts:
            if self.delete_draft(d["_id"]):
                count += 1
        return count

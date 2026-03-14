"""
Data Cache
文件缓存 -- 按日期+指数 key 存储, 支持 TTL 过期
"""
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


class DataCache:
    """文件缓存, 支持 DataFrame 和基本类型"""

    def __init__(self, cache_dir: str = "cache/", ttl_hours: int = 24):
        """
        Args:
            cache_dir: 缓存目录路径
            ttl_hours: 缓存有效期 (小时)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = ttl_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _meta_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.meta.json"

    def _data_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.pkl"

    def is_valid(self, key: str) -> bool:
        """检查缓存是否存在且未过期"""
        meta_path = self._meta_path(key)
        data_path = self._data_path(key)
        if not meta_path.exists() or not data_path.exists():
            return False
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            stored_at = datetime.fromisoformat(meta["stored_at"])
            return datetime.now() - stored_at < timedelta(hours=self.ttl_hours)
        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """读取缓存, 命中且有效返回 DataFrame, 否则 None"""
        if not self.is_valid(key):
            return None
        try:
            with open(self._data_path(key), "rb") as f:
                return pickle.load(f)
        except Exception:
            return None

    def set(self, key: str, data: pd.DataFrame) -> None:
        """写入缓存"""
        meta = {
            "stored_at": datetime.now().isoformat(),
            "ttl_hours": self.ttl_hours,
            "rows": len(data),
        }
        with open(self._meta_path(key), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        with open(self._data_path(key), "wb") as f:
            pickle.dump(data, f)

    def clear(self) -> int:
        """清除所有缓存文件, 返回删除数量"""
        count = 0
        for path in self.cache_dir.glob("*"):
            if path.is_file():
                path.unlink()
                count += 1
        return count

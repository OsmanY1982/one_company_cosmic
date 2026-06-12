# `opcclaw/core/supabase_client.py`

> 路径：`opcclaw/core/supabase_client.py` | 行数：51


---


```python
"""
Supabase 客户端配置
与移动端共享同一个 Supabase 项目
"""
import os
from supabase import create_client, Client
from supabase._sync.client import ClientOptions
from supabase_auth._sync.storage import SyncMemoryStorage

# Supabase 项目配置
PROJECT_URL = 'https://zkpymaioolnxxbqsapnj.supabase.co'
ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InprcHltYWlvb2xueHhicXNhcG5qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxNTI2NzIsImV4cCI6MjA5MjcyODY3Mn0.c7IO7Cf2u4EgwMwB-zF7KGO38XkAg19guwmfEUGEJk8'
SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InprcHltYWlvb2xueHhicXNhcG5qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzE1MjY3MiwiZXhwIjoyMDkyNzI4NjcyfQ.a9wsDspX9zytWNQXReS6ytsFQP2Zw_YdiAlNUV0XQps'

class SupabaseClient:
    """Supabase 客户端单例"""
    _instance = None
    _client = None
    _service_client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def client(self) -> Client:
        """普通客户端（受 RLS 限制）"""
        if self._client is None:
            self._client = create_client(PROJECT_URL, ANON_KEY)
        return self._client
    
    @property
    def service_client(self) -> Client:
        """Service Role 客户端（绕过 RLS）"""
        if self._service_client is None:
            # 使用 service_role key 创建客户端，绕过 RLS
            self._service_client = create_client(
                PROJECT_URL, 
                SERVICE_KEY
            )
        return self._service_client

# 便捷访问函数
def get_client() -> Client:
    """获取普通客户端"""
    return SupabaseClient().client

def get_service_client() -> Client:
    """获取 Service Role 客户端（用于数据同步）"""
    return SupabaseClient().service_client

```

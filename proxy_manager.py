# proxy_manager.py
# -*- coding: utf-8 -*-
"""
HTTP(S) 代理管理器
统一管理项目中所有网络请求的代理设置
"""
import os
import logging
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class ProxyManager:
    """HTTP(S) 代理管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProxyManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.http_proxy = "http://127.0.0.1:10808",
            self.https_proxy = "https://127.0.0.1:10808",
            self.no_proxy = None
            self.enabled = False
            self._initialized = True
    
    def configure(self, http_proxy: str = None, https_proxy: str = None, 
                  no_proxy: str = None, enabled: bool = False):
        """
        配置代理设置
        
        Args:
            http_proxy: HTTP代理地址，格式: http://proxy.example.com:8080
            https_proxy: HTTPS代理地址，格式: http://proxy.example.com:8080  
            no_proxy: 不使用代理的域名列表，用逗号分隔
            enabled: 是否启用代理
        """
        self.http_proxy = http_proxy
        self.https_proxy = https_proxy or http_proxy  # 如果没有指定HTTPS代理，使用HTTP代理
        self.no_proxy = no_proxy
        self.enabled = enabled
        
        if enabled:
            self._apply_proxy_settings()
            logging.info(f"代理已启用 - HTTP: {self.http_proxy}, HTTPS: {self.https_proxy}")
        else:
            self._clear_proxy_settings()
            logging.info("代理已禁用")
    
    def _apply_proxy_settings(self):
        """应用代理设置到环境变量和请求库"""
        if not self.enabled:
            return
            
        # 设置环境变量（影响大多数HTTP客户端）
        if self.http_proxy:
            os.environ['HTTP_PROXY'] = self.http_proxy
            os.environ['http_proxy'] = self.http_proxy
            
        if self.https_proxy:
            os.environ['HTTPS_PROXY'] = self.https_proxy
            os.environ['https_proxy'] = self.https_proxy
            
        if self.no_proxy:
            os.environ['NO_PROXY'] = self.no_proxy
            os.environ['no_proxy'] = self.no_proxy
    
    def _clear_proxy_settings(self):
        """清除代理设置"""
        proxy_env_vars = ['HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy', 
                         'NO_PROXY', 'no_proxy']
        for var in proxy_env_vars:
            if var in os.environ:
                del os.environ[var]
    
    def get_proxies_dict(self) -> Optional[Dict[str, str]]:
        """
        获取代理字典，用于requests等库
        
        Returns:
            代理字典或None
        """
        if not self.enabled:
            return None
            
        proxies = {}
        if self.http_proxy:
            proxies['http'] = self.http_proxy
        if self.https_proxy:
            proxies['https'] = self.https_proxy
            
        return proxies if proxies else None
    
    def get_session(self) -> requests.Session:
        """
        获取配置了代理的requests Session对象
        
        Returns:
            配置了代理的Session对象
        """
        session = requests.Session()
        if self.enabled:
            proxies = self.get_proxies_dict()
            if proxies:
                session.proxies.update(proxies)
        return session
    
    def test_proxy(self, test_url: str = "https://httpbin.org/ip") -> bool:
        """
        测试代理连接是否正常
        
        Args:
            test_url: 测试URL
            
        Returns:
            代理是否可用
        """
        if not self.enabled:
            logging.info("代理未启用，无需测试")
            return True
            
        try:
            session = self.get_session()
            response = session.get(test_url, timeout=10)
            response.raise_for_status()
            
            logging.info(f"代理测试成功: {response.json() if 'json' in response.headers.get('content-type', '') else 'OK'}")
            return True
            
        except Exception as e:
            logging.error(f"代理测试失败: {e}")
            return False
    
    def get_openai_client_kwargs(self) -> Dict[str, Any]:
        """
        获取OpenAI客户端的代理配置参数
        
        Returns:
            包含代理配置的参数字典
        """
        kwargs = {}
        if self.enabled:
            # OpenAI客户端使用httpx，支持代理配置
            proxies = self.get_proxies_dict()
            if proxies:
                kwargs['proxies'] = proxies
        return kwargs
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取当前代理状态
        
        Returns:
            代理状态信息
        """
        return {
            'enabled': self.enabled,
            'http_proxy': self.http_proxy,
            'https_proxy': self.https_proxy,
            'no_proxy': self.no_proxy,
            'env_http_proxy': os.environ.get('HTTP_PROXY'),
            'env_https_proxy': os.environ.get('HTTPS_PROXY'),
            'env_no_proxy': os.environ.get('NO_PROXY')
        }


# 全局代理管理器实例
proxy_manager = ProxyManager()
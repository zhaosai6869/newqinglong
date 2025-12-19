#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 Bing Rewards 自动化脚本 - 多账号分离版-v2.0

变量名：
bing_ck_1、bing_ck_2、bing_ck_3、bing_ck_4... （必需）
bing_token_1、bing_token_2、bing_token_3、bing_token_4... （可选，用于阅读任务）

下面url抓取CK，必须抓取到 tifacfaatcs 和认证字段，否则cookie无效
1. 登录 https://cn.bing.com/
2. 点右侧的【查看仪表板】,会跳转到 https://rewards.bing.com/?ref=rewardspanel  
3. 确认两个地址登录的是同一个账号，抓CK

Cookie验证规则：
- tifacfaatcs: 影响账号信息获取（必需）
- 认证字段: 影响搜索任务是否加分（必须包含 .MSA.Auth、_U 中的任意一个）
- 以上字段缺失会导致cookie无效

🔑 阅读任务需要配置刷新令牌：
1. 安装"Bing Rewards 自动获取刷新令牌"油猴脚本
2. 访问 https://login.live.com/oauth20_authorize.srf?client_id=0000000040170455&scope=service::prod.rewardsplatform.microsoft.com::MBI_SSL&response_type=code&redirect_uri=https://login.live.com/oauth20_desktop.srf
3. 登录后，使用"Bing Rewards 自动获取刷新令牌"油猴脚本，自动获取刷新令牌
4. 设置环境变量 bing_token_1、bing_token_2、bing_token_3...

From:yaohuo28507
cron: 10 0-22 * * *

"""

import requests
import random
import re
import time
import json
import os
from datetime import datetime, date
from urllib.parse import urlparse, parse_qs, quote
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from functools import wraps

# 内置令牌缓存管理功能
CACHE_ENABLED = True

# ==================== 配置管理 ====================
@dataclass
class Config:
    """配置类，统一管理所有配置项"""
    # 搜索配置
    SEARCH_CHECK_INTERVAL: int = 6
    SEARCH_DELAY_MIN: int = 20
    SEARCH_DELAY_MAX: int = 30
    TASK_DELAY_MIN: int = 2
    TASK_DELAY_MAX: int = 4
    
    # 重试配置
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    
    # 文件配置
    CACHE_FILE: str = "Bing_Rewards_Cache.json"
    TOKEN_CACHE_FILE: str = "bing_refresh_tokens.json"
    
    # API配置
    REQUEST_TIMEOUT: int = 15
    HOT_WORDS_MAX_COUNT: int = 30
    
    # User-Agent池配置
    PC_USER_AGENTS: List[str] = None
    MOBILE_USER_AGENTS: List[str] = None
    
    # 热搜API配置
    HOT_WORDS_APIS: List[Tuple[str, List[str]]] = None
    DEFAULT_HOT_WORDS: List[str] = None
    
    def __post_init__(self):
        if self.HOT_WORDS_APIS is None:
            self.HOT_WORDS_APIS = [
                ("https://dailyapi.eray.cc/", ["weibo", "douyin", "baidu", "toutiao", "thepaper", "qq-news", "netease-news", "zhihu"]),
                ("https://hot.baiwumm.com/api/", ["weibo", "douyin", "baidu", "toutiao", "thepaper", "qq", "netease", "zhihu"]),
                ("https://cnxiaobai.com/DailyHotApi/", ["weibo", "douyin", "baidu", "toutiao", "thepaper", "qq-news", "netease-news", "zhihu"]),
                ("https://hotapi.nntool.cc/", ["weibo", "douyin", "baidu", "toutiao", "thepaper", "qq-news", "netease-news", "zhihu"]),
            ]
        
        if self.DEFAULT_HOT_WORDS is None:
            self.DEFAULT_HOT_WORDS = [
                "盛年不重来，一日难再晨", "千里之行，始于足下", "少年易学老难成，一寸光阴不可轻",
                "敏而好学，不耻下问", "海内存知已，天涯若比邻", "三人行，必有我师焉",
                "莫愁前路无知已，天下谁人不识君", "人生贵相知，何用金与钱", "天生我材必有用",
                "海纳百川有容乃大；壁立千仞无欲则刚", "穷则独善其身，达则兼济天下", "读书破万卷，下笔如有神",
            ]
        
        if self.PC_USER_AGENTS is None:
            self.PC_USER_AGENTS = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.2478.131",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.181",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
            ]
        
        if self.MOBILE_USER_AGENTS is None:
            self.MOBILE_USER_AGENTS = [
                "Mozilla/5.0 (Linux; Android 14; 2210132C Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.52 Mobile Safari/537.36 EdgA/125.0.2535.51",
                "Mozilla/5.0 (iPad; CPU OS 16_7_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/120.0.2210.150 Version/16.0 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/123.0.2420.108 Version/18.0 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.44 Mobile Safari/537.36 EdgA/124.0.2478.49",
                "Mozilla/5.0 (Linux; Android 14; Mi 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.40 Mobile Safari/537.36 EdgA/123.0.2420.65",
                "Mozilla/5.0 (Linux; Android 9; ONEPLUS A5000 Build/PKQ1.180716.001; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36  BingSapphire/32.2.430730002",
            ]
    
    @staticmethod
    def generate_random_tnTID() -> str:
        """生成随机的tnTID参数"""
        # 生成32位随机十六进制字符串
        import secrets
        random_hex = secrets.token_hex(16).upper()
        return f"DSBOS_{random_hex}"
    
    @staticmethod
    def generate_random_tnCol() -> str:
        """生成1-50之间的随机数字"""
        return str(random.randint(1, 50))
    
    @staticmethod
    def get_random_pc_ua() -> str:
        """获取随机PC端User-Agent"""
        return random.choice(config.PC_USER_AGENTS)
    
    @staticmethod
    def get_random_mobile_ua() -> str:
        """获取随机移动端User-Agent"""
        return random.choice(config.MOBILE_USER_AGENTS)

config = Config()

# ==================== 账号管理 ====================
@dataclass
class AccountInfo:
    """账号信息类"""
    index: int
    alias: str
    cookies: str
    refresh_token: str = ""

class AccountManager:
    """账号管理器 - 读取环境变量中的账号配置"""
    
    @staticmethod
    def get_accounts() -> List[AccountInfo]:
        """获取所有账号配置"""
        accounts = []
        index = 1
        consecutive_empty = 0  # 连续空配置计数器
        max_consecutive_empty = 5  # 允许最多连续5个空配置
        max_check_index = 50  # 最大检查到第50个账号
        
        while index <= max_check_index:
            cookies = os.getenv(f"bing_ck_{index}")
            refresh_token = os.getenv(f"bing_token_{index}", "")
            
            # 如果既没有cookies也没有refresh_token
            if not cookies and not refresh_token:
                consecutive_empty += 1
                # 如果连续空配置超过限制，则停止搜索
                if consecutive_empty >= max_consecutive_empty:
                    break
                index += 1
                continue
            else:
                # 重置连续空配置计数器
                consecutive_empty = 0
            
            # 如果只有refresh_token没有cookies，跳过该账号
            if not cookies:
                print_log("账号配置", f"账号{index} 缺少cookies配置，跳过", index)
                # 发送缺少cookies配置的通知
                notification_manager.send_missing_cookies_config(index)
                index += 1
                continue
            
            # 验证cookie是否包含必需字段
            # 必须包含tifacfaatcs
            if 'tifacfaatcs=' not in cookies:
                print_log("账号配置", f"账号{index} 的cookie缺少必需字段: tifacfaatcs，cookie无效，请重新抓取", index)
                # 发送cookie失效通知
                notification_manager.send_cookie_missing_required_field(index, "tifacfaatcs")
                index += 1
                continue
            
            # 必须包含 .MSA.Auth、_U 中的任意一个
            auth_fields = ['.MSA.Auth=', '_U=']
            has_auth_field = any(field in cookies for field in auth_fields)
            
            if not has_auth_field:
                print_log("账号配置", f"账号{index} 的cookie缺少认证字段（需要包含 .MSA.Auth、_U 中的任意一个），cookie无效，请重新抓取", index)
                # 发送cookie失效通知
                notification_manager.send_cookie_missing_auth_field(index)
                index += 1
                continue
            
            alias = f"账号{index}"
            accounts.append(AccountInfo(
                index=index,
                alias=alias,
                cookies=cookies,
                refresh_token=refresh_token
            ))
            
            index += 1
        
        # 从令牌缓存文件加载保存的令牌
        token_cache_manager = TokenCacheManager()
        for account in accounts:
            cached_token = token_cache_manager.get_cached_token(account.alias, account.index)
            if cached_token:
                account.refresh_token = cached_token
        
        # 如果没有有效账号，发送总结性通知
        if not accounts:
            notification_manager.send_no_valid_accounts()
        
        return accounts

# ==================== 全局变量 ====================
search_thread_stopped = threading.Event()

# ==================== 日志系统 ====================

def print_log(title: str, msg: str, account_index: Optional[int] = None):
    """保持向后兼容的日志函数"""
    now = datetime.now().strftime("%H:%M:%S")
    if account_index is not None:
        title = f"账号{account_index} - {title}"
    # 确保输出格式一致，避免显示问题
    log_message = f"{now} [{title}]: {msg or ''}"
    print(log_message, flush=True)

# ==================== 异常处理装饰器 ====================
def retry_on_failure(max_retries: int = config.MAX_RETRIES, delay: int = config.RETRY_DELAY):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            # 获取更友好的函数名显示
            func_name = func.__name__
            if func_name == 'make_request':
                func_name = "网络请求"
            elif func_name == 'get_access_token':
                func_name = "令牌获取"
            elif func_name == 'get_read_progress':
                func_name = "阅读进度"
            elif func_name == 'submit_read_activity':
                func_name = "阅读提交"
            elif func_name == 'get_rewards_points':
                func_name = "积分查询"
            elif func_name == 'get_dashboard_data':
                func_name = "数据获取"
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        account_index = kwargs.get('account_index')
                        if account_index is not None:
                            print_log(f"{func_name}重试", f"第{attempt + 1}次尝试失败，{delay}秒后重试...", account_index)
                        else:
                            print_log(f"{func_name}重试", f"第{attempt + 1}次尝试失败，{delay}秒后重试...")
                        time.sleep(delay)
                    else:
                        account_index = kwargs.get('account_index')
                        if account_index is not None:
                            print_log(f"{func_name}失败", f"重试{max_retries}次后仍失败: {e}", account_index)
                        else:
                            print_log(f"{func_name}失败", f"重试{max_retries}次后仍失败: {e}")
            raise last_exception
        return wrapper
    return decorator

# ==================== 通知系统 ====================

class NotificationTemplates:
    """通知模板管理器 - 统一管理所有通知内容"""
    
    # Cookie获取地址
    COOKIE_URLS = "https://rewards.bing.com/welcome"
    
    @staticmethod
    def get_cookie_urls_text() -> str:
        """获取Cookie获取地址的格式化文本"""
        return f"   {NotificationTemplates.COOKIE_URLS}"
    
    @staticmethod
    def get_current_time() -> str:
        """获取当前时间格式化字符串"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @classmethod
    def missing_cookies_config(cls, account_index: int) -> tuple[str, str]:
        """缺少cookies配置的通知模板"""
        title = "🚨 Microsoft Rewards 配置缺失"
        content = (
            f"账号{account_index} 缺少cookies配置\n\n"
            f"错误时间: {cls.get_current_time()}\n"
            f"需要处理: 为账号{account_index}添加环境变量 bing_ck_{account_index}\n\n"
            f"配置说明:\n"
            f"1. 设置环境变量: bing_ck_{account_index}=你的完整cookie字符串\n"
            f"2. Cookie获取地址:\n"
            f"{cls.get_cookie_urls_text()}"
        )
        return title, content
    
    @classmethod
    def cookie_missing_required_field(cls, account_index: int, field_name: str) -> tuple[str, str]:
        """Cookie缺少必需字段的通知模板"""
        title = "🚨 Microsoft Rewards Cookie配置错误"
        content = (
            f"账号{account_index} 的Cookie缺少必需字段: {field_name}\n\n"
            f"错误时间: {cls.get_current_time()}\n"
            f"需要处理: 重新获取账号{account_index}的完整Cookie\n\n"
            f"Cookie获取地址:\n"
            f"{cls.get_cookie_urls_text()}"
        )
        return title, content
    
    @classmethod
    def cookie_missing_auth_field(cls, account_index: int) -> tuple[str, str]:
        """Cookie缺少认证字段的通知模板"""
        title = "🚨 Microsoft Rewards Cookie认证字段缺失"
        content = (
            f"账号{account_index} 的Cookie缺少认证字段（需要包含 .MSA.Auth、_U 中的任意一个）\n\n"
            f"错误时间: {cls.get_current_time()}\n"
            f"需要处理: 重新获取账号{account_index}的完整Cookie\n\n"
            f"Cookie获取地址:\n"
            f"{cls.get_cookie_urls_text()}"
        )
        return title, content
    
    @classmethod
    def no_valid_accounts(cls) -> tuple[str, str]:
        """无有效账号配置的通知模板"""
        title = "🚨 Microsoft Rewards 无有效账号配置"
        content = (
            "所有账号配置均存在问题，无法启动任务！\n\n"
            f"检查时间: {cls.get_current_time()}\n\n"
            "常见问题及解决方案:\n"
            "1. 环境变量未设置: 检查 bing_ck_1, bing_ck_2 等\n"
            "2. Cookie格式错误: 确保包含 tifacfaatcs 字段\n"
            "3. 认证字段缺失: 确保包含 .MSA.Auth 或 _U 字段\n\n"
            f"Cookie获取地址:\n"
            f"{cls.get_cookie_urls_text()}"
        )
        return title, content
    
    @classmethod
    def cookie_invalid(cls, account_index: Optional[int] = None) -> tuple[str, str]:
        """Cookie失效的通知模板"""
        account_info = f"账号{account_index} " if account_index else ""
        title = "🚨 Microsoft Rewards Cookie失效"
        content = (
            f"{account_info}Cookie已失效，需要重新获取\n\n"
            f"失效时间: {cls.get_current_time()}\n"
            f"需要处理: 重新获取{account_info}的完整Cookie\n\n"
            f"Cookie获取地址:\n"
            f"{cls.get_cookie_urls_text()}"
        )
        return title, content
    
    @classmethod
    def token_invalid(cls, account_index: Optional[int] = None) -> tuple[str, str]:
        """Token失效的通知模板"""
        account_info = f"账号{account_index} " if account_index else ""
        title = "🚨 Microsoft Rewards Token失效"
        content = (
            f"{account_info}Refresh Token已失效，需要重新获取\n\n"
            f"失效时间: {cls.get_current_time()}\n"
            f"需要处理: 重新获取{account_info}的Refresh Token\n\n"
            "获取方法:\n"
            "1. 访问 https://login.live.com/oauth20_authorize.srf\n"
            "2. 使用Microsoft账号登录\n"
            "3. 获取授权码并换取Refresh Token"
        )
        return title, content
    
    @classmethod
    def task_summary(cls, summaries: List[str]) -> tuple[str, str]:
        """任务完成总结的通知模板"""
        title = "✅ Microsoft Rewards 任务完成"
        content = "\n\n".join(summaries)
        return title, content

class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.notify_client = self._init_notify_client()
    
    def _init_notify_client(self):
        """初始化通知客户端"""
        try:
            import notify
            return notify
        except ImportError:
            return self._create_mock_notify()
    
    def _create_mock_notify(self):
        """创建模拟通知客户端"""
        class MockNotify:
            def send(self, title, content):
                print("\n--- [通知] ---")
                print(f"标题: {title}")
                print(f"内容:\n{content}")
                print("-------------------------------")
        return MockNotify()
    
    def send(self, title: str, content: str):
        """发送通知"""
        self.notify_client.send(title, content)
    
    # 便捷的通知方法
    def send_missing_cookies_config(self, account_index: int):
        """发送缺少cookies配置的通知"""
        title, content = NotificationTemplates.missing_cookies_config(account_index)
        self.send(title, content)
    
    def send_cookie_missing_required_field(self, account_index: int, field_name: str):
        """发送Cookie缺少必需字段的通知"""
        title, content = NotificationTemplates.cookie_missing_required_field(account_index, field_name)
        self.send(title, content)
    
    def send_cookie_missing_auth_field(self, account_index: int):
        """发送Cookie缺少认证字段的通知"""
        title, content = NotificationTemplates.cookie_missing_auth_field(account_index)
        self.send(title, content)
    
    def send_no_valid_accounts(self):
        """发送无有效账号配置的通知"""
        title, content = NotificationTemplates.no_valid_accounts()
        self.send(title, content)
    
    def send_cookie_invalid(self, account_index: Optional[int] = None):
        """发送Cookie失效的通知"""
        title, content = NotificationTemplates.cookie_invalid(account_index)
        self.send(title, content)
    
    def send_token_invalid(self, account_index: Optional[int] = None):
        """发送Token失效的通知"""
        title, content = NotificationTemplates.token_invalid(account_index)
        self.send(title, content)
    
    def send_task_summary(self, summaries: List[str]):
        """发送任务完成总结的通知"""
        title, content = NotificationTemplates.task_summary(summaries)
        self.send(title, content)

notification_manager = NotificationManager()

# ==================== 缓存管理 ====================
class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_file: str = config.CACHE_FILE):
        self.cache_file = cache_file
        self.lock = threading.Lock()
    
    def load_cache(self) -> Dict[str, Any]:
        """加载缓存数据"""
        if not os.path.exists(self.cache_file):
            return {}
        
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print_log("缓存错误", f"加载缓存失败: {e}")
            return {}
    
    def save_cache(self, data: Dict[str, Any]):
        """保存缓存数据"""
        try:
            with self.lock:
                # 清理过期数据
                today = date.today().isoformat()
                cleaned_data = self._clean_expired_data(data, today)
                
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print_log("缓存错误", f"保存缓存失败: {e}")
    
    def _clean_expired_data(self, data: Dict[str, Any], today: str) -> Dict[str, Any]:
        """清理过期的缓存数据"""
        keys_to_keep = []
        for k in data:
            date_part = None
            if '_' in k:
                date_part = k.split('_')[-1]
            elif k.startswith('push_'):
                date_part = k.replace('push_', '')
            
            if date_part and date_part >= today:
                keys_to_keep.append(k)
        
        return {k: data[k] for k in keys_to_keep}
    
    def get_cached_init_points(self, email: str, date_str: str) -> Optional[int]:
        """获取缓存的初始积分"""
        key = f"init_{email}_{date_str}"
        data = self.load_cache()
        entry = data.get(key)
        if entry and str(entry.get("init_points")) != "None":
            return entry["init_points"]
        return None
    
    def set_cached_init_points(self, email: str, date_str: str, points: int):
        """设置缓存的初始积分"""
        try:
            data = self.load_cache()
            key = f"init_{email}_{date_str}"
            
            if key in data and str(data[key].get("init_points")) != "None":
                return
            
            data[key] = {
                "init_points": points,
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.save_cache(data)
        except Exception as e:
            print_log("缓存错误", f"设置初始积分缓存失败: {e}")
    
    def has_pushed_today(self) -> bool:
        """检查今天是否已推送"""
        today = date.today().isoformat()
        data = self.load_cache()
        return data.get(f"push_{today}", False)
    
    def mark_pushed_today(self):
        """标记今天已推送"""
        today = date.today().isoformat()
        data = self.load_cache()
        data[f"push_{today}"] = True
        self.save_cache(data)

cache_manager = CacheManager()

# ==================== Refresh Token 缓存管理 ====================
class TokenCacheManager:
    """Refresh Token 缓存管理器"""
    
    def __init__(self, token_file: str = config.TOKEN_CACHE_FILE):
        self.token_file = token_file
        self.lock = threading.Lock()
        self._cached_tokens = {}  # 内存缓存，避免重复保存
    
    def load_tokens(self) -> Dict[str, Any]:
        """加载缓存的token数据"""
        if not os.path.exists(self.token_file):
            return {}
        
        try:
            with open(self.token_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print_log("令牌缓存", f"❌ 读取失败: {e}")
            return {}
    
    def save_token(self, account_alias: str, refresh_token: str, account_index: Optional[int] = None):
        """保存刷新令牌到缓存文件"""
        try:
            # 检查是否已经缓存过相同的令牌
            cache_key = f"{account_alias}_{refresh_token}"
            if cache_key in self._cached_tokens:
                return  # 已经缓存过，跳过
            
            with self.lock:
                # 确保目录存在
                os.makedirs(os.path.dirname(self.token_file) if os.path.dirname(self.token_file) else '.', exist_ok=True)
                
                # 读取现有数据
                token_data = self.load_tokens()
                
                # 检查是否与现有令牌相同
                existing_token = token_data.get(account_alias, {}).get("refreshToken")
                if existing_token == refresh_token:
                    return  # 令牌没有变化，跳过
                
                # 更新令牌
                token_data[account_alias] = {
                    "refreshToken": refresh_token,
                    "updatedAt": datetime.now().isoformat()
                }
                
                # 保存到文件
                with open(self.token_file, "w", encoding="utf-8") as f:
                    json.dump(token_data, f, ensure_ascii=False, indent=2)
                
                # 标记为已缓存
                self._cached_tokens[cache_key] = True
                
                print_log("令牌缓存", f"✅ 缓存成功", account_index)
                
        except Exception as e:
            print_log("令牌缓存", f"❌ 缓存失败: {e}", account_index)
    
    def get_cached_token(self, account_alias: str, account_index: Optional[int] = None) -> Optional[str]:
        """获取缓存的刷新令牌"""
        try:
            token_data = self.load_tokens()
            account_data = token_data.get(account_alias)
            if account_data and account_data.get("refreshToken"):
                # print_log("令牌缓存", f"加载缓存", account_index)
                return account_data["refreshToken"]
            return None
        except Exception as e:
            print_log("令牌缓存", f"❌ 读取失败: {e}", account_index)
            return None

token_cache_manager = TokenCacheManager()

# ==================== 热搜词管理 ====================
class HotWordsManager:
    """热搜词管理器"""
    
    def __init__(self):
        self.hot_words = self._fetch_hot_words()
    
    @retry_on_failure(max_retries=2, delay=1)
    def _fetch_hot_words(self, max_count: int = config.HOT_WORDS_MAX_COUNT) -> List[str]:
        """获取热搜词"""
        apis_shuffled = config.HOT_WORDS_APIS[:]
        random.shuffle(apis_shuffled)
        
        for base_url, sources in apis_shuffled:
            sources_shuffled = sources[:]
            random.shuffle(sources_shuffled)
            
            for source in sources_shuffled:
                api_url = base_url + source
                try:
                    resp = requests.get(api_url, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict) and 'data' in data and data['data']:
                            all_titles = [item.get('title') for item in data['data'] if item.get('title')]
                            if all_titles:
                                print_log("热搜词", f"成功获取热搜词 {len(all_titles)} 条，来源: {api_url}")
                                random.shuffle(all_titles)
                                return all_titles[:max_count]
                except Exception:
                    continue
        
        print_log("热搜词", "全部热搜API失效，使用默认搜索词。")
        default_words = config.DEFAULT_HOT_WORDS[:max_count]
        random.shuffle(default_words)
        return default_words
    
    def get_random_word(self) -> str:
        """获取随机热搜词"""
        return random.choice(self.hot_words) if self.hot_words else random.choice(config.DEFAULT_HOT_WORDS)

hot_words_manager = HotWordsManager()

# ==================== HTTP请求管理 ====================
class RequestManager:
    """HTTP请求管理器"""
    
    @staticmethod
    def get_browser_headers(cookies: str) -> Dict[str, str]:
        """获取浏览器请求头"""
        return {
            "user-agent": config.get_random_pc_ua(),
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "accept-encoding": "gzip, deflate, br, zstd",
            "sec-ch-ua": '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "upgrade-insecure-requests": "1",
            "x-edge-shopping-flag": "1",
            "referer": "https://rewards.bing.com/",
            "cookie": cookies
        }
    
    @staticmethod
    def get_mobile_headers(cookies: str) -> Dict[str, str]:
        """获取移动端请求头"""
        return {
            "user-agent": config.get_random_mobile_ua(),
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "sec-ch-ua": '"Not;A=Brand";v="99", "Chromium";v="124"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "upgrade-insecure-requests": "1",
            "cookie": cookies
        }
    
    @staticmethod
    @retry_on_failure(max_retries=2)
    def make_request(method: str, url: str, headers: Dict[str, str], 
                    params: Optional[Dict] = None, data: Optional[str] = None,
                    timeout: int = config.REQUEST_TIMEOUT, account_index: Optional[int] = None) -> requests.Response:
        """统一的HTTP请求方法"""
        if method.upper() == 'GET':
            return requests.get(url, headers=headers, params=params, timeout=timeout)
        elif method.upper() == 'POST':
            # 判断是否为JSON数据
            if headers.get('Content-Type') == 'application/json' and data:
                return requests.post(url, headers=headers, json=json.loads(data), timeout=timeout)
            elif isinstance(data, dict):
                # 表单数据
                return requests.post(url, headers=headers, data=data, timeout=timeout)
            else:
                # 字符串数据
                return requests.post(url, headers=headers, data=data, timeout=timeout)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")

request_manager = RequestManager()

# ==================== 主要业务逻辑类 ====================
class RewardsService:
    """Microsoft Rewards服务类 - 增强版本支持令牌缓存"""
    
    def __init__(self):
        pass
    
    @retry_on_failure()
    def get_rewards_points(self, cookies: str, account_index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """查询当前积分和账号信息"""
        headers = request_manager.get_browser_headers(cookies)
        
        url = 'https://rewards.bing.com/'
      
        response = request_manager.make_request('GET', url, headers, account_index=account_index)
        response.raise_for_status()
        
        content = response.text
        
        # 提取积分和邮箱
        points_pattern = r'"availablePoints":(\d+)'
        email_pattern = r'email:\s*"([^"]+)"'
        
        points_match = re.search(points_pattern, content)
        email_match = re.search(email_pattern, content)
        
        available_points = int(points_match.group(1)) if points_match else None
        email = email_match.group(1) if email_match else None
        
        if available_points is None or email is None:
            print_log("账号信息", "Cookie可能已失效，请重新获取Cookie后再试", account_index)
            # 立即推送Cookie失效通知
            self._send_cookie_invalid_notification(account_index)
            return None
        
        return {
            'points': available_points,
            'email': email
        }
    
    @retry_on_failure()
    def get_access_token(self, refresh_token: str, account_alias: str = "", account_index: Optional[int] = None, silent: bool = False) -> Optional[str]:
        """获取访问令牌用于阅读任务 - 支持令牌自动更新"""
        try:
            data = {
                'client_id': '0000000040170455',
                'refresh_token': refresh_token,
                'scope': 'service::prod.rewardsplatform.microsoft.com::MBI_SSL',
                'grant_type': 'refresh_token'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': config.get_random_pc_ua(),
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
                'sec-ch-ua-mobile': '?0',
                'Accept': '*/*',
                'Origin': 'https://login.live.com',
                'X-Edge-Shopping-Flag': '1',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': 'https://login.live.com/oauth20_desktop.srf',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
            }
            
            response = request_manager.make_request(
                'POST', 'https://login.live.com/oauth20_token.srf', 
                headers, data=data, account_index=account_index
            )
            
            if response.status_code == 200:
                token_data = response.json()
                if 'access_token' in token_data:
                    # print_log("令牌获取", "成功获取访问令牌", account_index)
                    
                    # 检查是否有新的refresh_token返回并启用了缓存（非静默模式）
                    if (not silent and CACHE_ENABLED and 'refresh_token' in token_data and 
                        token_data['refresh_token'] != refresh_token and account_alias):
                        # print_log("令牌更新", f"检测到新的刷新令牌，正在更新缓存", account_index)
                        # 保存新的refresh_token到缓存
                        token_cache_manager.save_token(account_alias, token_data['refresh_token'], account_index)
                    
                    return token_data['access_token']
            
            # 静默模式下不处理错误通知
            if silent:
                return None
            
            # 检查是否为令牌失效错误
            if response.status_code in [400, 401, 403]:
                try:
                    error_data = response.json()
                    error_description = error_data.get('error_description', '').lower()
                    error_code = error_data.get('error', '').lower()
                    
                    # 常见的令牌失效错误标识
                    token_invalid_indicators = [
                        'invalid_grant', 'expired_token', 'refresh_token', 
                        'invalid_request', 'unauthorized', 'invalid refresh token'
                    ]
                    
                    if any(indicator in error_description or indicator in error_code for indicator in token_invalid_indicators):
                        print_log("令牌获取", "刷新令牌已失效，发送通知", account_index)
                        self._send_token_invalid_notification(account_index)
                        return None
                except:
                    pass
            
            print_log("令牌获取", f"获取访问令牌失败，状态码: {response.status_code}", account_index)
            return None
            
        except Exception as e:
            # 静默模式下不处理错误通知
            if silent:
                return None
                
            # 检查异常是否包含令牌失效的信息
            error_message = str(e).lower()
            token_invalid_indicators = [
                'invalid_grant', 'expired_token', 'refresh_token', 
                'unauthorized', '401', '403', 'invalid refresh token'
            ]
            
            if any(indicator in error_message for indicator in token_invalid_indicators):
                print_log("令牌获取", "刷新令牌已失效（异常检测），发送通知", account_index)
                self._send_token_invalid_notification(account_index)
            else:
                print_log("令牌获取", f"获取访问令牌异常: {e}", account_index)
            return None
    
    @retry_on_failure()
    def get_read_progress(self, access_token: str, account_index: Optional[int] = None) -> Dict[str, int]:
        """获取阅读任务进度"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'User-Agent': config.get_random_mobile_ua(),
                'Accept-Encoding': 'gzip',
                'x-rewards-partnerid': 'startapp',
                'x-rewards-appid': 'SAAndroid/32.2.430730002',
                'x-rewards-country': 'cn',
                'x-rewards-language': 'zh-hans',
                'x-rewards-flights': 'rwgobig'
            }
            
            response = request_manager.make_request(
                'GET', 
                'https://prod.rewardsplatform.microsoft.com/dapi/me?channel=SAAndroid&options=613',
                headers, account_index=account_index
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'promotions' in data['response']:
                    for promotion in data['response']['promotions']:
                        if (promotion.get('attributes', {}).get('offerid') == 
                            'ENUS_readarticle3_30points'):
                            return {
                                'max': int(promotion['attributes'].get('max', 3)),
                                'progress': int(promotion['attributes'].get('progress', 0))
                            }
                
                return {'max': 3, 'progress': 0}
            
            print_log("阅读进度", f"获取阅读进度失败，状态码: {response.status_code}", account_index)
            return {'max': 3, 'progress': 0}
            
        except Exception as e:
            print_log("阅读进度", f"获取阅读进度异常: {e}", account_index)
            return {'max': 3, 'progress': 0}
    
    @retry_on_failure()
    def submit_read_activity(self, access_token: str, account_index: Optional[int] = None) -> bool:
        """提交阅读活动"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'User-Agent': config.get_random_mobile_ua(),
                'Accept-Encoding': 'gzip',
                'x-rewards-partnerid': 'startapp',
                'x-rewards-appid': 'SAAndroid/32.2.430730002',
                'x-rewards-country': 'cn',
                'x-rewards-language': 'zh-hans',
                'x-rewards-flights': 'rwgobig'
            }
            
            payload = {
                'amount': 1,
                'country': 'cn',
                'id': '',
                'type': 101,
                'attributes': {
                    'offerid': 'ENUS_readarticle3_30points'
                }
            }
            
            response = request_manager.make_request(
                'POST',
                'https://prod.rewardsplatform.microsoft.com/dapi/me/activities',
                headers,
                data=json.dumps(payload), account_index=account_index
            )
            
            if response.status_code == 200:
                # print_log("阅读提交", "文章阅读提交成功", account_index)
                return True
            else:
                print_log("阅读提交", f"文章阅读提交失败，状态码: {response.status_code}", account_index)
                return False
                
        except Exception as e:
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    if (error_data.get('error', {}).get('description', '').find('already') != -1):
                        print_log("阅读提交", "文章阅读任务已完成", account_index)
                        return True
                except:
                    pass
            
            print_log("阅读提交", f"文章阅读提交异常: {e}", account_index)
            return False
    
    def complete_read_tasks(self, refresh_token: str, account_alias: str = "", account_index: Optional[int] = None) -> int:
        """完成阅读任务 - 支持令牌缓存"""
        if not refresh_token:
            print_log("阅读任务", "未提供刷新令牌，跳过阅读任务", account_index)
            return 0
        
        try:
            # 获取访问令牌（支持令牌自动更新）
            access_token = self.get_access_token(refresh_token, account_alias, account_index)
            if not access_token:
                print_log("阅读任务", "无法获取访问令牌，跳过阅读任务", account_index)
                return 0
            
            # 获取阅读进度
            progress_data = self.get_read_progress(access_token, account_index)
            max_reads = progress_data['max']
            current_progress = progress_data['progress']
            
            
            if current_progress >= max_reads:
                # print_log("阅读任务", "阅读任务已完成", account_index)
                return current_progress
            else:
                print_log("阅读任务", f"当前阅读进度: {current_progress}/{max_reads}", account_index)

            # 执行阅读任务
            read_attempts = 0
            max_attempts = max_reads - current_progress
            
            for i in range(max_attempts):
                print_log("阅读任务", f"执行第 {i + 1} 次阅读任务", account_index)
                
                if self.submit_read_activity(access_token, account_index):
                    read_attempts += 1
                    
                    # 延迟一段时间
                    delay = random.uniform(5, 10)
                    print_log("阅读任务", f"阅读任务提交成功，等待 {delay:.1f} 秒", account_index)
                    time.sleep(delay)
                    
                    # 再次检查进度
                    progress_data = self.get_read_progress(access_token, account_index)
                    new_progress = progress_data['progress']
                    
                    if new_progress > current_progress:
                        current_progress = new_progress
                        print_log("阅读任务", f"阅读进度更新: {current_progress}/{max_reads}", account_index)
                        
                        if current_progress >= max_reads:
                            # print_log("阅读任务", "所有阅读任务已完成", account_index)
                            break
                else:
                    print_log("阅读任务", f"第 {i + 1} 次阅读任务提交失败", account_index)
                    time.sleep(random.uniform(2, 5))
            
            print_log("阅读任务", f"阅读任务执行完成，最终进度: {current_progress}/{max_reads}", account_index)
            return current_progress
            
        except Exception as e:
            print_log("阅读任务", f"阅读任务执行异常: {e}", account_index)
            return 0
    
    def _send_cookie_invalid_notification(self, account_index: Optional[int] = None):
        """发送Cookie失效的独立通知"""
        try:
            notification_manager.send_cookie_invalid(account_index)
            print_log("Cookie通知", f"已发送账号{account_index}的Cookie失效通知", account_index)
        except Exception as e:
            print_log("Cookie通知", f"发送Cookie失效通知失败: {e}", account_index)
    
    def _send_token_invalid_notification(self, account_index: Optional[int] = None):
        """发送刷新令牌失效的独立通知"""
        try:
            title = f"🚨 Microsoft Rewards 刷新令牌失效警告"
            content = f"账号{account_index} 的刷新令牌已失效，阅读任务无法执行！\n\n"
            content += f"失效时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += f"需要处理: 重新获取账号{account_index}的刷新令牌\n\n"
            content += "刷新令牌获取步骤:\n"
            content += "1. 访问 https://login.live.com/oauth20_authorize.srf?client_id=0000000040170455&scope=service::prod.rewardsplatform.microsoft.com::MBI_SSL&response_type=code&redirect_uri=https://login.live.com/oauth20_desktop.srf\n"
            content += "2. 登录后从返回的URL中获取code参数\n"
            content += "3. 使用code换取refresh_token\n"
            content += "4. 更新环境变量 bing_token_{account_index}"
            
            notification_manager.send(title, content)
            print_log("令牌通知", f"已发送账号{account_index}的刷新令牌失效通知", account_index)
        except Exception as e:
            print_log("令牌通知", f"发送刷新令牌失效通知失败: {e}", account_index)

    @retry_on_failure()
    def get_dashboard_data(self, cookies: str, account_index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """统一获取dashboard数据和token"""
        try:
            headers = request_manager.get_browser_headers(cookies)
            resp = request_manager.make_request('GET', "https://rewards.bing.com/", headers, timeout=30, account_index=account_index)
            resp.raise_for_status()
            
            html_text = resp.text
            token_match = re.search(r'name="__RequestVerificationToken".*?value="([^"]+)"', html_text)
            dashboard_match = re.search(r'var dashboard\s*=\s*(\{.*?\});', html_text, re.DOTALL)
            
            if not token_match:
                print_log('Dashboard错误', "未能获取 __RequestVerificationToken", account_index)
                return None
            
            if not dashboard_match:
                print_log('Dashboard错误', "未能获取 dashboard 数据", account_index)
                return None
            
            token = token_match.group(1)
            dashboard_json = json.loads(dashboard_match.group(1).rstrip().rstrip(';'))
            
            return {
                'dashboard_data': dashboard_json,
                'token': token
            }
        except Exception as e:
            print_log('Dashboard错误', str(e), account_index)
            return None

    def is_pc_search_complete(self, dashboard_data: Dict[str, Any]) -> bool:
        """检查PC搜索是否完成"""
        if not dashboard_data:
            return False
        user_status = dashboard_data.get('userStatus', {})
        counters = user_status.get('counters', {})
        pc_search_tasks = counters.get('pcSearch', [])
        
        # 如果没有任务数据，认为未完成
        if not pc_search_tasks:
            return False
            
        for task in pc_search_tasks:
            # 明确检查complete字段，默认为False（未完成）
            if not task.get('complete', False):
                return False
        return True

    def is_mobile_search_complete(self, dashboard_data: Dict[str, Any]) -> bool:
        """检查移动搜索是否完成"""
        if not dashboard_data:
            return False
        user_status = dashboard_data.get('userStatus', {})
        counters = user_status.get('counters', {})
        mobile_search_tasks = counters.get('mobileSearch', [])
        
        # 如果没有任务数据，认为未完成
        if not mobile_search_tasks:
            return False
            
        for task in mobile_search_tasks:
            # 明确检查complete字段，默认为False（未完成）
            if not task.get('complete', False):
                return False
        return True

    def get_account_level(self, dashboard_data: Dict[str, Any]) -> str:
        """获取账号等级"""
        if not dashboard_data:
            return "Level1"
        user_status = dashboard_data.get('userStatus', {})
        level_info = user_status.get('levelInfo', {})
        return level_info.get('activeLevel', 'Level1')

    @retry_on_failure(max_retries=2, delay=1)
    def perform_pc_search(self, cookies: str, account_index: Optional[int] = None, 
                         email: Optional[str] = None) -> bool:
        """执行PC搜索"""
        q = hot_words_manager.get_random_word()
        search_url = "https://cn.bing.com/search"
        params = {
            "q": q,
            "qs": "SC",
            "form": "TSASDS"
        }
        
        headers = request_manager.get_browser_headers(cookies)
        
        try:
            # 执行PC搜索
            search_response = request_manager.make_request('GET', search_url, headers, params, account_index=account_index)
            return 200 <= search_response.status_code < 400
            
        except Exception as e:
            print_log("电脑搜索", f"搜索失败: {e}", account_index)
            return False
    
    @retry_on_failure(max_retries=2, delay=1)
    def perform_mobile_search(self, cookies: str, account_index: Optional[int] = None, 
                            email: Optional[str] = None) -> bool:
        """执行移动搜索"""
        q = hot_words_manager.get_random_word()

        # 处理cookie
        enhanced_cookies = self._enhance_mobile_cookies(cookies)

        # 生成随机的tnTID和tnCol参数
        random_tnTID = config.generate_random_tnTID()
        random_tnCol = config.generate_random_tnCol()
        
        search_url = "https://cn.bing.com/search"
        params = {
            "q": q,
            "form": "LWI001",
            "filters": f'tnTID:"{random_tnTID}" tnVersion:"36f91593efb34a38bbc225e32632c4f5" Segment:"popularnow.carousel" tnCol:"{random_tnCol}" tnScenario:"TrendingTopicsAPI" tnOrder:"a23421ac-7c69-4533-a740-1d1577b784ba"',
            "efirst": "0",
            "ssp": "1",
            "safesearch": "moderate",
            "setlang": "zh-hans",
            "cc": "cn",
            "PC": "SANSAAND"
        }
        
        headers = request_manager.get_mobile_headers(enhanced_cookies)
        
        try:
            # 执行移动搜索
            search_response = request_manager.make_request('GET', search_url, headers, params, account_index=account_index)
            return 200 <= search_response.status_code < 400
            
        except Exception as e:
            print_log("移动搜索", f"搜索失败: {e}", account_index)
            return False
    

    def complete_daily_set_tasks(self, cookies: str, account_index: Optional[int] = None) -> int:
        """完成每日活动任务"""
        completed_count = 0
        try:
            # 获取dashboard数据
            dashboard_result = self.get_dashboard_data(cookies, account_index)
            if not dashboard_result:
                return completed_count
            
            dashboard_data = dashboard_result['dashboard_data']
            token = dashboard_result['token']
            
            # 提取每日任务
            today_str = date.today().strftime('%m/%d/%Y')
            daily_tasks = dashboard_data.get('dailySetPromotions', {}).get(today_str, [])
            
            if not daily_tasks:
                print_log("每日活动", "没有找到今日的每日活动任务", account_index)
                return completed_count
            
            # 过滤未完成的任务
            incomplete_tasks = [task for task in daily_tasks if not task.get('complete')]
            
            if not incomplete_tasks:
                return completed_count
            
            print_log("每日活动", f"找到 {len(incomplete_tasks)} 个未完成的每日活动任务", account_index)
            
            # 执行任务
            for i, task in enumerate(incomplete_tasks, 1):
                print_log("每日活动", f"⏳ 执行任务 {i}/{len(incomplete_tasks)}: {task.get('title', '未知任务')}", account_index)
                
                if self._execute_task(task, token, cookies, account_index):
                    completed_count += 1
                    print_log("每日活动", f"✅ 任务完成: {task.get('title', '未知任务')}", account_index)
                else:
                    print_log("每日活动", f"❌ 任务失败: {task.get('title', '未知任务')}", account_index)
                
                # 随机延迟
                time.sleep(random.uniform(config.TASK_DELAY_MIN, config.TASK_DELAY_MAX))
            
            # print_log("每日活动", f"每日活动执行完成，成功完成 {completed_count} 个任务", account_index)
            
        except Exception as e:
            print_log('每日活动出错', f"异常: {e}", account_index)
        
        return completed_count

    def complete_more_activities(self, cookies: str, account_index: Optional[int] = None) -> int:
        """完成更多活动任务"""
        completed_count = 0
        
        try:
            # 获取dashboard数据
            dashboard_result = self.get_dashboard_data(cookies, account_index)
            if not dashboard_result:
                print_log("更多活动", "无法获取dashboard数据，跳过更多活动", account_index)
                return completed_count
            
            dashboard_data = dashboard_result['dashboard_data']
            token = dashboard_result['token']
            
            # 提取更多活动任务
            more_promotions = dashboard_data.get('morePromotions', [])
            tasks = self._extract_tasks(more_promotions)
            
            if not tasks:
                return completed_count
            
            print_log("更多活动", f"找到 {len(tasks)} 个可执行的更多活动任务", account_index)
            
            # 执行任务
            for i, task in enumerate(tasks, 1):
                print_log("更多活动", f"⏳ 执行任务 {i}/{len(tasks)}: {task.get('title', '未知任务')}", account_index)
                
                if self._execute_task(task, token, cookies, account_index):
                    completed_count += 1
                else:
                    print_log("更多活动", f"❌ 任务失败: {task.get('title', '未知任务')}", account_index)
                
                # 随机延迟
                time.sleep(random.uniform(config.TASK_DELAY_MIN, config.TASK_DELAY_MAX))
            
            # print_log("更多活动", f"更多活动执行完成，成功完成 {completed_count} 个任务", account_index)
            
        except Exception as e:
            print_log('更多活动出错', f"异常: {e}", account_index)
        
        return completed_count

    def _extract_tasks(self, more_promotions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取任务"""
        tasks = []
        for promotion in more_promotions:
            complete = promotion.get('complete')
            priority = promotion.get('priority')
            attributes = promotion.get('attributes', {})
            is_unlocked = attributes.get('is_unlocked')
            
            # 任务必须未完成
            if complete == False:
                if (priority == 0 or priority == 7 or is_unlocked == 'True' or is_unlocked is None):
                    tasks.append(promotion)
        return tasks

    def _execute_task(self, task: Dict[str, Any], token: str, cookies: str, account_index: Optional[int] = None) -> bool:
        """执行单个任务"""
        try:
            destination_url = task.get('destinationUrl') or task.get('attributes', {}).get('destination')
            if not destination_url:
                print_log("任务执行", f"❌ 任务 {task.get('name')} 没有目标URL", account_index)
                return False
            
            # 设置任务执行请求头
            headers = {
                'User-Agent': config.get_random_pc_ua(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Cookie': cookies
            }
            
            # 发送请求
            response = request_manager.make_request(
                'GET',
                destination_url, 
                headers, 
                timeout=config.REQUEST_TIMEOUT,
                account_index=account_index
            )
            
            if response.status_code == 200:
                # 报告活动
                if self._report_activity(task, token, cookies, account_index):
                    return True
                else:
                    print_log("任务执行", f"⚠️ 任务执行成功但活动报告失败", account_index)
                    return False
            else:
                print_log("任务执行", f"❌ 任务执行失败，状态码: {response.status_code}", account_index)
                return False
                
        except Exception as e:
            print_log("任务执行", f"❌ 执行任务时出错: {e}", account_index)
            return False

    def _report_activity(self, task: Dict[str, Any], token: str, cookies: str, account_index: Optional[int] = None) -> bool:
        """报告任务活动，真正完成任务"""
        if not token:
            return False
        
        try:
            post_url = 'https://rewards.bing.com/api/reportactivity?X-Requested-With=XMLHttpRequest'
            post_headers = {
                'User-Agent': config.get_random_pc_ua(),
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://rewards.bing.com',
                'Referer': 'https://rewards.bing.com/',
                'Cookie': cookies
            }
            payload = f"id={task.get('offerId', task.get('name'))}&hash={task.get('hash', '')}&timeZone=480&activityAmount=1&dbs=0&form=&type=&__RequestVerificationToken={token}"
            response = request_manager.make_request('POST', post_url, post_headers, data=payload, timeout=config.REQUEST_TIMEOUT, account_index=account_index)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("activity") and result["activity"].get("points", 0) > 0:
                        print_log("任务奖励", f"✅ 获得{result['activity']['points']}积分", account_index)
                        return True
                    else:
                        return False
                except json.JSONDecodeError:
                    return False
            else:
                return False
        except Exception as e:
            return False
    
    def _enhance_mobile_cookies(self, cookies: str) -> str:
        """增强移动端cookies"""
        enhanced_cookies = cookies
        
        # 移除桌面端特有字段
        desktop_fields_to_remove = [
            r'_HPVN=[^;]+', r'_RwBf=[^;]+', r'USRLOC=[^;]+',
            r'BFBUSR=[^;]+', r'_Rwho=[^;]+', r'ipv6=[^;]+', r'_clck=[^;]+',
            r'_clsk=[^;]+', r'webisession=[^;]+', r'MicrosoftApplicationsTelemetryDeviceId=[^;]+',
            r'MicrosoftApplicationsTelemetryFirstLaunchTime=[^;]+', r'MSPTC=[^;]+', r'vdp=[^;]+'
        ]
        
        for pattern in desktop_fields_to_remove:
            enhanced_cookies = re.sub(pattern, '', enhanced_cookies)
        
        enhanced_cookies = re.sub(r';;+', ';', enhanced_cookies).strip('; ')
        
        # 添加移动端特有字段
        # 1. SRCHD字段 - 移动端必需
        if 'SRCHD=' not in enhanced_cookies:
            enhanced_cookies += '; SRCHD=AF=NOFORM'
        
        # 2. SRCHUSR字段 - 更新为移动端格式
        current_date = datetime.now().strftime('%Y%m%d')
        if 'SRCHUSR=' in enhanced_cookies:
            enhanced_cookies = re.sub(r'SRCHUSR=[^;]+', f'SRCHUSR=DOB={current_date}&DS=1', enhanced_cookies)
        else:
            enhanced_cookies += f'; SRCHUSR=DOB={current_date}&DS=1'
        
        return enhanced_cookies


# ==================== 主程序类 ====================
class RewardsBot:
    """Microsoft Rewards 自动化机器人主类 - 多账号分离版本"""
    
    def __init__(self):
        self.service = RewardsService()
        self.accounts = AccountManager.get_accounts()
        
        if not self.accounts:
            print_log("启动错误", "没有检测到任何账号配置，程序退出")
            print_log("配置提示", "请设置环境变量: bing_ck_1, bing_ck_2... 和可选的 bing_token_1, bing_token_2...")
            exit(1)
        
        print_log("初始化", f"检测到 {len(self.accounts)} 个账号，即将开始...")
        
        # 统计有效刷新令牌数量
        valid_tokens = sum(1 for account in self.accounts if account.refresh_token)
        if valid_tokens > 0:
            print_log("初始化", f"检测到 {valid_tokens} 个有效刷新令牌，将启用阅读任务")
    
    def process_single_account(self, account: AccountInfo) -> Optional[str]:
        """处理单个账号的完整流程"""
        try:
            account_index = account.index
            cookies = account.cookies
            
            # 获取账号信息
            initial_data = self.service.get_rewards_points(cookies, account_index)
            if not initial_data:
                print_log("账号处理", "Cookie验证失败，跳过此账号", account_index)
                return None
            
            email = initial_data.get('email', '未知邮箱')
            today_str = date.today().isoformat()
            
            # 获取初始积分
            cached_init_points = cache_manager.get_cached_init_points(email, today_str)
            script_start_points = cached_init_points if cached_init_points is not None else initial_data['points']
            
            if cached_init_points is None:
                cache_manager.set_cached_init_points(email, today_str, script_start_points)
            
            print_log("账号信息", f"账号: {email}, 初始积分: {script_start_points}", account_index)

            # 执行阅读任务
            read_completed = 0
            if account.refresh_token:
                read_completed = self.service.complete_read_tasks(account.refresh_token, account.alias, account_index)
                print_log("阅读任务", "【阅读任务 - 已完成】", account_index)
            else:
                print_log("阅读任务", "【阅读任务 - 跳过】（未配置刷新令牌）", account_index)

            # 执行每日任务
            daily_completed = self.service.complete_daily_set_tasks(cookies, account_index)
            print_log("每日活动", "【每日活动 - 已完成】", account_index)
            
            # 执行更多任务
            more_completed = self.service.complete_more_activities(cookies, account_index)
            print_log("更多活动", "【更多活动 - 已完成】", account_index)
            

            
            # 执行搜索任务
            self._perform_search_tasks(cookies, account_index, email)
            
            # 获取最终积分
            final_data = self.service.get_rewards_points(cookies, account_index)
            if final_data and final_data['points'] is not None:
                final_points = final_data['points']
                points_earned = final_points - script_start_points
                print_log("脚本完成", f"🎉 最终积分：{final_points}（+{points_earned}）", account_index)
                
                # 生成详细的任务摘要
                summary = self._format_account_summary(
                    email, script_start_points, final_points, 
                    daily_completed, more_completed, read_completed, account_index, cookies, account
                )
                return summary
            else:
                print_log("脚本完成", "无法获取最终积分", account_index)
                return None
        
        except SystemExit:
            # 搜索任务未完成，线程被终止
            print_log("账号处理", f"搜索任务未完成，账号处理被终止", account_index)
            return None
        except Exception as e:
            print_log("账号处理错误", f"处理账号时发生异常: {e}", account_index)
            return None
    
    def _perform_search_tasks(self, cookies: str, account_index: int, email: str):
        """执行搜索任务"""
        global search_thread_stopped
        
        # 获取初始dashboard数据检查任务状态
        dashboard_result = self.service.get_dashboard_data(cookies, account_index)
        dashboard_data = dashboard_result['dashboard_data'] if dashboard_result else None
        
        # 获取账号等级
        account_level = self.service.get_account_level(dashboard_data)
        # print_log("账号等级", f"当前账号等级: {account_level}", account_index)
        
        # PC搜索
        if dashboard_data and not self.service.is_pc_search_complete(dashboard_data):
            print_log("电脑搜索", f"开始执行PC搜索，最多{config.SEARCH_CHECK_INTERVAL}次", account_index)
            
            # 记录初始进度
            last_progress = self._get_search_progress_sum(dashboard_data, 'pcSearch')
            
            # 执行搜索，如果任务完成则提前终止
            count = 0
            for i in range(config.SEARCH_CHECK_INTERVAL):
                count += 1
                if self.service.perform_pc_search(cookies, account_index, email):
                    delay = random.randint(config.SEARCH_DELAY_MIN, config.SEARCH_DELAY_MAX)
                    print_log("电脑搜索", f"第{i+1}次搜索成功，等待{delay}秒...", account_index)
                    time.sleep(delay)
                else:
                    print_log("电脑搜索", f"第{i+1}次搜索失败", account_index)
                
                # 每次搜索后检查进度
                dashboard_result = self.service.get_dashboard_data(cookies, account_index)
                dashboard_data = dashboard_result['dashboard_data'] if dashboard_result else None
                current_progress = self._get_search_progress_sum(dashboard_data, 'pcSearch') if dashboard_data else last_progress
                
                # 第6次搜索完成后输出进度变化
                if count == config.SEARCH_CHECK_INTERVAL:
                    print_log("电脑搜索", f"已完成{count} 次，进度变化: {last_progress} -> {current_progress}", account_index)
                
                # 检查任务是否完成，如果完成则提前终止
                if dashboard_data and self.service.is_pc_search_complete(dashboard_data):
                    print_log("电脑搜索", f"PC搜索任务已完成，执行了{i+1}次搜索", account_index)
                    break
            
            # 如果循环正常结束（没有break），检查任务是否真正完成
            else:
                if dashboard_data and not self.service.is_pc_search_complete(dashboard_data):
                    print_log("电脑搜索", f"执行完{config.SEARCH_CHECK_INTERVAL}次搜索后任务未完成，停止线程", account_index)
                    search_thread_stopped.set()
                    raise SystemExit()
        
        # 最终检查PC搜索是否真正完成
        final_dashboard_result = self.service.get_dashboard_data(cookies, account_index)
        final_dashboard_data = final_dashboard_result['dashboard_data'] if final_dashboard_result else None
        
        if final_dashboard_data and self.service.is_pc_search_complete(final_dashboard_data):
            print_log("电脑搜索", "【电脑搜索 - 已完成】", account_index)
        else:
            print_log("电脑搜索", "【电脑搜索 - 未完成】", account_index)
        
        # 移动搜索 - 只有非1级账号才执行
        if account_level != "Level1":
            # 重新获取dashboard数据，因为PC搜索可能已经改变了状态
            dashboard_result = self.service.get_dashboard_data(cookies, account_index)
            dashboard_data = dashboard_result['dashboard_data'] if dashboard_result else None
            
            if dashboard_data and not self.service.is_mobile_search_complete(dashboard_data):
                print_log("移动搜索", f"开始执行移动搜索，最多{config.SEARCH_CHECK_INTERVAL}次", account_index)
                
                # 记录初始进度
                last_progress = self._get_search_progress_sum(dashboard_data, 'mobileSearch')
                
                # 执行搜索，如果任务完成则提前终止
                count = 0
                for i in range(config.SEARCH_CHECK_INTERVAL):
                    count += 1
                    if self.service.perform_mobile_search(cookies, account_index, email):
                        delay = random.randint(config.SEARCH_DELAY_MIN, config.SEARCH_DELAY_MAX)
                        print_log("移动搜索", f"第{i+1}次搜索成功，等待{delay}秒...", account_index)
                        time.sleep(delay)
                    else:
                        print_log("移动搜索", f"第{i+1}次搜索失败", account_index)
                    
                    # 每次搜索后检查进度
                    dashboard_result = self.service.get_dashboard_data(cookies, account_index)
                    dashboard_data = dashboard_result['dashboard_data'] if dashboard_result else None
                    current_progress = self._get_search_progress_sum(dashboard_data, 'mobileSearch') if dashboard_data else last_progress
                    
                    # 第6次搜索完成后输出进度变化
                    if count == config.SEARCH_CHECK_INTERVAL:
                        print_log("移动搜索", f"已完成{count} 次，进度变化: {last_progress} -> {current_progress}", account_index)
                    
                    # 检查任务是否完成，如果完成则提前终止
                    if dashboard_data and self.service.is_mobile_search_complete(dashboard_data):
                        print_log("移动搜索", f"移动搜索任务已完成，执行了{i+1}次搜索", account_index)
                        break
                
                # 如果循环正常结束（没有break），检查任务是否真正完成
                else:
                    if dashboard_data and not self.service.is_mobile_search_complete(dashboard_data):
                        print_log("移动搜索", f"执行完{config.SEARCH_CHECK_INTERVAL}次搜索后任务未完成，停止线程", account_index)
                        search_thread_stopped.set()
                        raise SystemExit()
            
            # 最终检查移动搜索是否真正完成
            final_dashboard_result = self.service.get_dashboard_data(cookies, account_index)
            final_dashboard_data = final_dashboard_result['dashboard_data'] if final_dashboard_result else None
            
            if final_dashboard_data and self.service.is_mobile_search_complete(final_dashboard_data):
                print_log("移动搜索", "【移动搜索 - 已完成】", account_index)
            else:
                print_log("移动搜索", "【移动搜索 - 未完成】", account_index)
        else:
            print_log("移动搜索", "【移动搜索 - 跳过】（1级账号无移动搜索任务）", account_index)

    def _get_search_progress_sum(self, dashboard_data: Dict[str, Any], search_type: str) -> int:
        """获取搜索进度总和"""
        if not dashboard_data:
            return 0
        user_status = dashboard_data.get('userStatus', {})
        counters = user_status.get('counters', {})
        search_tasks = counters.get(search_type, [])
        return sum(task.get('pointProgress', 0) for task in search_tasks)

    def _format_account_summary(self, email: str, start_points: int, final_points: int, 
                               daily_completed: int, more_completed: int, read_completed: int, 
                               account_index: int, cookies: str, account: AccountInfo) -> str:
        """格式化账号摘要"""
        points_earned = final_points - start_points
        lines = [
            f"账号{account_index} - {email}",
            f"✨ 积分变化: {start_points} -> {final_points} (+{points_earned})"
        ]
        
        # 获取dashboard数据
        try:
            dashboard_result = self.service.get_dashboard_data(cookies, account_index)
            if dashboard_result and dashboard_result.get('dashboard_data'):
                dashboard_data = dashboard_result['dashboard_data']
                user_status = dashboard_data.get('userStatus', {})
                counters = user_status.get('counters', {})
                
                # 每日活动统计
                today_str = date.today().strftime('%m/%d/%Y')
                daily_tasks = dashboard_data.get('dailySetPromotions', {}).get(today_str, [])
                daily_completed_count = 0
                daily_total_count = 0
                if daily_tasks:
                    daily_completed_count = sum(1 for task in daily_tasks if task.get('complete'))
                    daily_total_count = len(daily_tasks)
                lines.append(f"📅每日活动: {daily_completed_count}/{daily_total_count}")
                
                # 更多活动统计
                more_tasks = dashboard_data.get('morePromotions', [])
                more_completed_count = 0
                more_total_count = 0
                if more_tasks:
                    for task in more_tasks:
                        # 只统计pointProgressMax大于0的任务
                        ppm = task.get('pointProgressMax', 0) or 0
                        if ppm > 0:
                            more_total_count += 1
                            if task.get('complete'):
                                more_completed_count += 1
                lines.append(f"🎯更多活动: {more_completed_count}/{more_total_count}")
                
                # 阅读任务进度 - 获取真实进度，但避免重复缓存
                read_progress_text = f"📖阅读任务: {read_completed}/30"
                if account.refresh_token:
                    try:
                        # 静默获取access_token，不触发缓存
                        access_token = self.service.get_access_token(account.refresh_token, account.alias, account_index, silent=True)
                        if access_token:
                            progress_data = self.service.get_read_progress(access_token, account_index)
                            read_progress_text = f"📖阅读任务: {progress_data['progress']}/{progress_data['max']}"
                    except:
                        pass  # 如果获取失败，使用默认格式
                lines.append(read_progress_text)

                # 搜索任务进度
                # 获取账号等级
                account_level = self.service.get_account_level(dashboard_data)
                
                # 电脑搜索进度
                pc_search_tasks = counters.get("pcSearch", [])
                for task in pc_search_tasks:
                    title = task.get('title', "电脑搜索")
                    progress = f"{task.get('pointProgress', 0)}/{task.get('pointProgressMax', 0)}"
                    lines.append(f"💻电脑搜索: {progress}")
                
                # 移动搜索进度 - 只有非1级账号才显示
                if account_level != "Level1":
                    mobile_search_tasks = counters.get("mobileSearch", [])
                    for task in mobile_search_tasks:
                        title = task.get('title', "移动搜索")
                        progress = f"{task.get('pointProgress', 0)}/{task.get('pointProgressMax', 0)}"
                        lines.append(f"📱移动搜索: {progress}")
                else:
                    lines.append("📱移动搜索: 1级账号无此任务")
            else:
                # 如果无法获取dashboard数据，使用简化格式
                lines.extend([
                    f"📅每日活动: 完成 {daily_completed} 个任务",
                    f"🎯更多活动: 完成 {more_completed} 个任务",
                    f"📖阅读任务: 完成 {read_completed} 个任务",
                    f"🔍搜索任务: PC搜索和移动搜索已执行"
                ])
        except Exception as e:
            # 异常情况下使用简化格式
            lines.extend([
                f"📅每日活动: 完成 {daily_completed} 个任务",
                f"🎯更多活动: 完成 {more_completed} 个任务",
                f"📖阅读任务: 完成 {read_completed} 个任务",
                f"🔍搜索任务: PC搜索和移动搜索已执行"
            ])
        
        return '\n'.join(lines)
    
    def run(self):
        """运行主程序"""
        account_summaries = {}  # 使用字典保存账号摘要，key为账号索引
        threads = []
        summaries_lock = threading.Lock()
        
        def thread_worker(account: AccountInfo):
            try:
                summary = self.process_single_account(account)
                if summary:
                    with summaries_lock:
                        account_summaries[account.index] = summary
            except SystemExit:
                # 搜索任务失败导致的线程终止，不记录为错误
                pass
            except Exception as e:
                print_log(f"账号{account.index}错误", f"处理账号时发生异常: {e}", account.index)
        
        # 启动所有账号的处理线程
        for account in self.accounts:
            t = threading.Thread(target=thread_worker, args=(account,))
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 按账号索引排序并转换为列表
        sorted_summaries = []
        if account_summaries:
            # 按账号索引排序
            for account_index in sorted(account_summaries.keys()):
                sorted_summaries.append(account_summaries[account_index])
        
        # 推送结果
        self._send_notification(sorted_summaries)
    
    def _send_notification(self, summaries: List[str]):
        """发送通知"""
        print(f"\n\n{'='*10} [全部任务完成] {'='*10}")
        
        if search_thread_stopped.is_set():
            print_log("统一推送", "搜索任务未完成，线程被终止，取消推送。")
            return
        
        if cache_manager.has_pushed_today():
            print_log("统一推送", "今天已经推送过，取消本次推送。")
            return
        
        if summaries:
            print_log("统一推送", "准备发送所有账号的总结报告...")
            try:
                title = f"Microsoft Rewards 任务总结 ({date.today().strftime('%Y-%m-%d')})"
                content = "\n\n".join(summaries)
                notification_manager.send(title, content)
                print_log("推送成功", "总结报告已发送。")
                cache_manager.mark_pushed_today()
            except Exception as e:
                print_log("推送失败", f"发送总结报告时出错: {e}")
        else:
            print_log("统一推送", "没有可供推送的账号信息。")

# ==================== 主程序入口 ====================
def main():
    """主程序入口"""
    try:
        bot = RewardsBot()
        bot.run()
    except KeyboardInterrupt:
        print_log("程序中断", "用户中断程序执行")
    except Exception as e:
        print_log("程序错误", f"程序执行出错: {e}")

if __name__ == "__main__":
    main() 
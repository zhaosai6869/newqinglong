# encoding: utf-8
"""
联通APP自动登录并签到脚本
优化内容：
1. 添加推送通知功能
2. 优先使用缓存参数，失败后再登录获取新参数
3. 支持多账号顺序执行
4. 添加账号序号显示
5. 完善的缓存管理
环境变量：'ltqd'，账号格式：'手机号1#密码1@手机号2#密码2'
"""

import base64
import hashlib
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from notify import send

import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

PUBLIC_KEY_BASE64 = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDc+CZK9bBA9IU+gZUOc6FUGu7yO9WpTNB0PzmgFBh96Mg1WrovD1oqZ+eIF4LjvxKXGOdI79JRdve9NPhQo07+uqGQgE4imwNnRx7PFtCRryiIEcUoavuNtuRVoBAm6qdB0SrctgaqGfLgKvZHOnwTjyNqjBUxzMeQlEC2czEMSwIDAQAB"
DEFAULT_SPLIT = "#PART#"
MAX_BLOCK_SIZE = 117
CACHE_FILE = "chinaUnicom_cache.json"

# 全局推送消息列表
msg = []


def rsa_encrypt(plaintext: str, public_key_base64: str) -> bytes:
    public_key_der = base64.b64decode(public_key_base64)
    public_key = RSA.import_key(public_key_der)
    cipher = PKCS1_v1_5.new(public_key)

    if len(plaintext) <= MAX_BLOCK_SIZE:
        return cipher.encrypt(plaintext.encode('utf-8'))

    encrypted_blocks = []
    for i in range(0, len(plaintext), MAX_BLOCK_SIZE):
        block = plaintext[i:i + MAX_BLOCK_SIZE]
        encrypted_block = cipher.encrypt(block.encode('utf-8'))
        if i > 0:
            encrypted_blocks.append(DEFAULT_SPLIT.encode('utf-8'))
        encrypted_blocks.append(encrypted_block)

    return b''.join(encrypted_blocks)


def mobile_encrypt(data: str) -> str:
    encrypted_bytes = rsa_encrypt(data, PUBLIC_KEY_BASE64)
    return base64.b64encode(encrypted_bytes).decode('utf-8').replace('\n', '')


def password_encrypt(password: str, random_str: str = "000000") -> str:
    combined = password + random_str
    return mobile_encrypt(combined)


class Constants:
    REQUEST_DELAY = 1
    MAX_LOGIN_ATTEMPTS = 2

    # 接口信息
    LOGIN_URL = "https://m.client.10010.com/mobileService/login.htm"
    SIGNIN_PAGE_URL = 'https://img.client.10010.com/SigininApp/index.html'
    CONTINUOUS_SIGN_URL = 'https://activity.10010.com/sixPalaceGridTurntableLottery/signin/getContinuous'
    DAY_SIGN_URL = 'https://activity.10010.com/sixPalaceGridTurntableLottery/signin/daySign'

    # 固定参数
    LOGIN_APP_ID = "06eccb0b7c2fd02bc1bb5e8a9ca2874175f50d8af589ecbd499a7c937a2fda7754dc135192b3745bd20073a687faee1755c67fab695164a090edd8e0da8771b83913890a44ec38e628cf2445bc476dfd"
    LOGIN_KEY_VERSION = "2"
    LOGIN_VOIP_TOKEN = "citc-default-token-do-not-push"
    LOGIN_IS_FIRST_INSTALL = "1"
    LOGIN_IS_REMEMBER_PWD = "false"
    LOGIN_SIM_COUNT = "1"
    LOGIN_NET_WAY = "wifi"

    SIGNIN_PAGE_PARAMS = {
        'cdncachetime': '2909378',
        'channel': 'wode',
        'webViewNavIsHidden': 'webViewNavIsHidden'
    }


class Logger:
    @staticmethod
    def section(title):
        message = f"\n=== {title} ==="
        print(message)
        msg.append(message)

    @staticmethod
    def info(message):
        print(f"[INFO] {message}")
        msg.append(f"[INFO] {message}")

    @staticmethod
    def success(message):
        print(f"[SUCCESS] {message}")
        msg.append(f"✅ {message}")

    @staticmethod
    def warning(message):
        print(f"[WARNING] {message}")
        msg.append(f"⚠️ {message}")

    @staticmethod
    def error(message):
        print(f"[ERROR] {message}")
        msg.append(f"❌ {message}")


class CacheManager:
    @staticmethod
    def load_cache():
        try:
            if Path(CACHE_FILE).exists():
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            Logger.warning(f"加载缓存失败: {e}")
        return {}

    @staticmethod
    def save_cache(cache_data):
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=4)
        except Exception as e:
            Logger.warning(f"保存缓存失败: {e}")


class RequestHelper:
    @staticmethod
    def retry_request(request_func, attempts=3, delay=5, timeout=10):
        for i in range(attempts):
            try:
                response = request_func(timeout=timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if i < attempts - 1:
                    Logger.warning(f"请求失败，第 {i + 1}/{attempts} 次重试... 错误: {e}")
                    time.sleep(delay)
                else:
                    raise

    @staticmethod
    def build_headers(base_headers=None):
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_8_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 unicom android@12.0100'
        }
        if base_headers:
            headers.update(base_headers)
        return headers


class ChinaUnicomSigner:
    def __init__(self, account_index, mobile, password):
        self.account_index = account_index
        self.mobile = mobile
        self.password = password
        self.notification_messages = []
        self.cookie = None
        self.device_id = hashlib.md5(mobile.encode()).hexdigest()
        self.cache = CacheManager.load_cache()

    def add_notification(self, message):
        """添加通知消息，同时记录到推送列表"""
        self.notification_messages.append(f"[账号{self.account_index}] {message}")
        msg.append(f"[账号{self.account_index}] {message}")

    def try_use_cached_credentials(self):
        """尝试使用缓存的登录凭证"""
        if self.mobile not in self.cache:
            return False

        cached_data = self.cache[self.mobile]
        self.cookie = cached_data.get('cookie')

        # 验证缓存是否有效
        if self._validate_cached_credentials():
            Logger.info(f"使用缓存凭证成功")
            return True
        return False

    def _validate_cached_credentials(self):
        """验证缓存的cookie是否有效"""
        if not self.cookie:
            return False

        try:
            headers = RequestHelper.build_headers({
                'Host': 'activity.10010.com',
                'Cookie': self.cookie,
                'Referer': 'https://img.client.10010.com/'
            })

            response = requests.get(
                Constants.CONTINUOUS_SIGN_URL,
                params={'channel': 'wode', 'imei': self.device_id},
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('code') == '0000'
        except Exception:
            return False

    def perform_login(self):
        """执行登录流程并更新缓存"""
        Logger.section(f"中国联通自动登录 (账号 {self.account_index})")
        mobile_enc = mobile_encrypt(self.mobile)
        password_enc = password_encrypt(self.password)

        req_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        payload = {
            "voipToken": Constants.LOGIN_VOIP_TOKEN,
            "deviceBrand": "iPhone",
            "simOperator": "--,%E4%B8%AD%E5%9B%BD%E7%A7%BB%E5%8A%A8,--,--,--",
            "deviceId": self.device_id,
            "netWay": Constants.LOGIN_NET_WAY,
            "deviceCode": self.device_id,
            "deviceOS": "15.8.3",
            "uniqueIdentifier": self.device_id,
            "latitude": "",
            "version": "iphone_c@12.0200",
            "pip": "192.168.5.14",
            "isFirstInstall": Constants.LOGIN_IS_FIRST_INSTALL,
            "remark4": "",
            "keyVersion": Constants.LOGIN_KEY_VERSION,
            "longitude": "",
            "simCount": Constants.LOGIN_SIM_COUNT,
            "mobile": mobile_enc,
            "isRemberPwd": Constants.LOGIN_IS_REMEMBER_PWD,
            "appId": Constants.LOGIN_APP_ID,
            "reqtime": req_time,
            "deviceModel": "iPhone8,2",
            "password": password_enc
        }

        headers = RequestHelper.build_headers({
            "Host": "m.client.10010.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://m.client.10010.com/"
        })

        try:
            Logger.info("正在发送登录请求...")
            response = RequestHelper.retry_request(
                lambda timeout: requests.post(
                    Constants.LOGIN_URL,
                    data=payload,
                    headers=headers,
                    timeout=timeout
                )
            )

            data = response.json()
            Logger.info(
                f"接收到响应：HTTP状态码 {response.status_code}, 业务码: {data.get('code')}, 描述: {data.get('desc')}")

            if data.get("code") in ("0", "0000"):
                Logger.success("登录成功！正在提取凭证...")
                self.cookie = "; ".join([f"{c.name}={c.value}" for c in response.cookies])
                account_phone = next((c.value for c in response.cookies if c.name == 'u_account'), "未知")

                # 更新缓存
                self.cache[self.mobile] = {
                    'cookie': self.cookie,
                    'device_id': self.device_id,
                    'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                CacheManager.save_cache(self.cache)

                msg = f"登录成功！账号: {account_phone}"
                self.add_notification(msg)
                return True

            msg = f"登录失败！业务码: {data.get('code')}, 描述: {data.get('desc')}"
            Logger.error(msg)
            self.add_notification(msg)
            return False

        except Exception as e:
            msg = f"登录请求发生错误：{e}"
            Logger.error(msg)
            self.add_notification(msg)
            return False

    def signin_page_request(self):
        Logger.section(f"访问签到页面 (账号 {self.account_index})")
        headers = RequestHelper.build_headers({
            'Host': 'img.client.10010.com',
            'Cookie': self.cookie,
            'Referer': 'https://img.client.100.com/'
        })

        try:
            response = RequestHelper.retry_request(
                lambda timeout: requests.get(
                    Constants.SIGNIN_PAGE_URL,
                    params=Constants.SIGNIN_PAGE_PARAMS,
                    headers=headers,
                    timeout=timeout
                )
            )

            if response.status_code == 200:
                msg = "访问签到页面成功"
                Logger.success(msg)
            else:
                msg = f"访问签到页面失败，状态码: {response.status_code}"
                Logger.error(msg)

            self.add_notification(msg)
            return response.status_code == 200

        except Exception as e:
            msg = f"访问签到页面异常: {e}"
            Logger.error(msg)
            self.add_notification(msg)
            return False

    def get_sign_status(self):
        Logger.section(f"获取签到状态 (账号 {self.account_index})")
        headers = RequestHelper.build_headers({
            'Host': 'activity.10010.com',
            'Cookie': self.cookie,
            'Origin': 'https://img.client.10010.com',
            'Referer': 'https://img.client.10010.com/'
        })

        params = {
            'taskId': '',
            'channel': 'wode',
            'imei': self.device_id
        }

        try:
            response = RequestHelper.retry_request(
                lambda timeout: requests.get(
                    Constants.CONTINUOUS_SIGN_URL,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )
            )

            data = response.json()
            Logger.info(f"业务响应码: {data.get('code')}, 描述: {data.get('desc')}")

            if data.get('code') == '0000':
                info_data = data.get('data', {})
                continue_count = info_data.get('continueCount', '未知')
                today_signed = info_data.get('todayIsSignIn', 'n') == 'y'
                keep_desc = info_data.get('keepDesc', '')

                msg = f"获取签到信息成功 | 连续签到{continue_count}天, 今日{'已' if today_signed else '未'}签到"
                if keep_desc:
                    msg += f", 奖励: {keep_desc}"

                Logger.success(msg)
                self.add_notification(msg)
                return True, today_signed

            msg = f"获取签到信息失败 | 响应代码: {data.get('code')}, 描述: {data.get('desc')}"
            Logger.error(msg)
            self.add_notification(msg)
            return False, False

        except Exception as e:
            msg = f"获取签到信息异常: {e}"
            Logger.error(msg)
            self.add_notification(msg)
            return False, False

    def perform_sign(self):
        Logger.section(f"执行每日签到 (账号 {self.account_index})")
        headers = RequestHelper.build_headers({
            'Host': 'activity.10010.com',
            'Cookie': self.cookie,
            'Origin': 'https://img.client.10010.com',
            'Referer': 'https://img.client.10010.com/',
            'Content-Type': 'application/x-www-form-urlencoded'
        })

        try:
            response = RequestHelper.retry_request(
                lambda timeout: requests.post(
                    Constants.DAY_SIGN_URL,
                    headers=headers,
                    timeout=timeout
                )
            )

            data = response.json()
            Logger.info(f"业务响应码: {data.get('code')}, 描述: {data.get('desc')}")

            if data.get('code') == '0000':
                sign_data = data.get('data', {})
                msg = "每日签到成功！"
                status_desc = sign_data.get('statusDesc', '')
                if status_desc:
                    msg += f" {status_desc}"

                rewards = []
                for key, name in [('redSignMessage', '获得奖励'),
                                  ('blackSignMessage', '额外奖励'),
                                  ('flowerCount', '花朵数量'),
                                  ('growthV', '成长值')]:
                    if value := sign_data.get(key):
                        rewards.append(f"{name}: {value}")

                if rewards:
                    msg += "\n🎁 " + ", ".join(rewards)

                Logger.success(msg)
                self.add_notification(msg)
                return True

            elif data.get('code') == '0002' and '已经签到' in data.get('desc', ''):
                msg = "今日已完成签到！"
                Logger.success(msg)
                self.add_notification(msg)
                return True

            msg = f"每日签到失败！响应代码: {data.get('code')}, 描述: {data.get('desc')}"
            Logger.error(msg)
            self.add_notification(msg)
            return False

        except Exception as e:
            msg = f"每日签到异常: {e}"
            Logger.error(msg)
            self.add_notification(msg)
            return False

    def run(self):
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.add_notification(f"脚本开始运行: {start_time}")

        # 1. 尝试使用缓存凭证
        if not self.try_use_cached_credentials():
            # 2. 缓存无效则执行登录
            attempts = 0
            login_success = False
            while attempts < Constants.MAX_LOGIN_ATTEMPTS and not login_success:
                attempts += 1
                login_success = self.perform_login()
                if not login_success and attempts < Constants.MAX_LOGIN_ATTEMPTS:
                    time.sleep(2)

        if self.cookie:  # 有有效cookie才继续
            Logger.section(f"联通签到流程开始 (账号 {self.account_index})")
            self.add_notification("\n--- 签到流程 ---")

            # 访问签到页面
            self.signin_page_request()
            time.sleep(Constants.REQUEST_DELAY)

            # 获取签到状态
            status_success, already_signed = self.get_sign_status()

            if status_success and not already_signed:
                Logger.info("检测到今日未签到，准备执行每日签到...")
                time.sleep(Constants.REQUEST_DELAY)
                self.perform_sign()
            elif already_signed:
                Logger.info("今日已签到，无需重复签到")

            Logger.section(f"联通签到流程结束 (账号 {self.account_index})")

        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.add_notification(f"\n脚本运行结束: {end_time}")

        # 打印当前账号的所有通知消息
        print("\n".join(self.notification_messages))


def get_account_credentials():
    """从环境变量获取账号信息"""
    mobile_password = os.environ.get('ltqd', "")
    if not mobile_password:
        Logger.error("环境变量 'ltqd' 未设置")
        sys.exit(1)

    accounts = []
    # 支持两种分隔符：@和|
    separator = '@' if '@' in mobile_password else '|'
    for account in mobile_password.split(separator):
        if "#" not in account:
            Logger.error(f"账号格式错误，应为 '手机号#密码'，当前: {account}")
            continue
        mobile, password = account.split("#", 1)
        accounts.append((mobile.strip(), password.strip()))

    if not accounts:
        Logger.error("没有有效的账号信息，请检查环境变量 'ltqd'")
        sys.exit(1)

    return accounts


if __name__ == "__main__":
    # 清空全局推送消息
    msg.clear()

    # 获取账号信息
    accounts = get_account_credentials()
    Logger.info(f"找到 {len(accounts)} 个账号，准备依次执行...")

    # 依次处理每个账号
    for index, (mobile, password) in enumerate(accounts, 1):
        Logger.section(f"开始处理第 {index} 个账号: {mobile[:3]}****{mobile[-4:]}")
        signer = ChinaUnicomSigner(index, mobile, password)
        signer.run()

        # 账号间延迟
        if index < len(accounts):
            Logger.info(f"等待 {Constants.REQUEST_DELAY} 秒后处理下一个账号...")
            time.sleep(Constants.REQUEST_DELAY)

    Logger.section("所有账号处理完成")

    # 发送推送通知
    send("联通签到结果", "\n".join(msg))
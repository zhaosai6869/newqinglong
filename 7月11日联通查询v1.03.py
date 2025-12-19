# encoding: utf-8
import requests
import time
import sys
import json
import os
from datetime import datetime
import hashlib
import execjs
from notify import send 
from dotenv import load_dotenv
load_dotenv('联通.env') 

COLOR_RESET = "\033[0m"
COLOR_RED = "\033[1;31m"
COLOR_GREEN = "\033[1;32m"
COLOR_YELLOW = "\033[1;33m"
COLOR_BLUE = "\033[1;34m"
COLOR_PURPLE = "\033[1;35m"
COLOR_CYAN = "\033[1;36m"
COLOR_WHITE = "\033[1;37m"
COLOR_BOLD = "\033[1m"
COLOR_UNDERLINE = "\033[4m"

ENV_MOBILE_PASSWORD = 'MOBILE_PASSWORD'
ENV_SINGLE_NOTIFICATION = 'SINGLE_NOTIFICATION'

LOGIN_URL = "https://m.client.10010.com/mobileService/login.htm"
BALANCE_URL = "https://m.client.10010.com/servicequerybusiness/balancenew/accountBalancenew.htm"
FLOW_INFO_URL = 'https://m.client.10010.com/servicequerybusiness/operationservice/queryOcsPackageFlowLeftContentRevisedInJune'
VOICE_INFO_URL = 'https://m.client.10010.com/servicequerybusiness/operationservice/queryOcsPackageFlowLeftContentRevisedInJune'

LOGIN_APP_ID = "06eccb0b7c2fd02bc1bb5e8a9ca2874175f50d8af589ecbd499a7c937a2fda7754dc135192b3745bd20073a687faee1755c67fab695164a090edd8e0da8771b83913890a44ec38e628cf2445bc476dfd"
LOGIN_KEY_VERSION = "2"
LOGIN_VOIP_TOKEN = "citc-default-token-do-not-push"
LOGIN_IS_FIRST_INSTALL = "1"
LOGIN_IS_REMEMBER_PWD = "false"
LOGIN_SIM_COUNT = "1"
LOGIN_NET_WAY = "wifi"

BALANCE_PARAMS = {
    "duanlianjieabc": "",
    "channelCode": "",
    "serviceType": "",
    "saleChannel": "",
    "externalSources": "",
    "contactCode": "",
    "ticket": "",
    "ticketPhone": "",
    "ticketChannel": "",
    "language": "chinese",
    "channel": "client"
}
FLOW_INFO_PARAMS = {
    "duanlianjieabc": "",
    "channelCode": "",
    "serviceType": "",
    "saleChannel": "",
    "externalSources": "",
    "contactCode": "",
    "ticket": "",
    "ticketPhone": "",
    "ticketChannel": "",
    "language": "chinese"
}
VOICE_INFO_PARAMS = FLOW_INFO_PARAMS.copy()

def print_color(message, color=COLOR_RESET, bold=False):
    bold_code = COLOR_BOLD if bold else ""
    print(f"{color}{bold_code}{message}{COLOR_RESET}")
    sys.stdout.flush()

def get_env(name, required=True, default=None):
    value = os.getenv(name, default)
    if required and value is None:
        print_color(f"❌ {COLOR_RED}错误：请设置环境变量 {COLOR_BOLD}{name}{COLOR_RED}", COLOR_RED)
        exit(1)
    return value

JS_ENCRYPT_CODE = """
const crypto = require("crypto");
const PUBLIC_KEY_BASE64 = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDc+CZK9bBA9IU+gZUOc6FUGu7yO9WpTNB0PzmgFBh96Mg1WrovD1oqZ+eIF4LjvxKXGOdI79JRdve9NPhQo07+uqGQgE4imwNnRx7PFtCRryiIEcUoavuNtuRVoBAm6qdB0SrctgaqGfLgKvZHOnwTjyNqjBUxzMeQlEC2czEMSwIDAQAB";
const DEFAULT_SPLIT = "#PART#";
const max_block_size = 117;

function rsa_encrypt(plaintext, public_key_base64) {
    const publicKey = Buffer.from(public_key_base64, "base64");
    const pemPublicKey = "-----BEGIN PUBLIC KEY-----\\n" + publicKey.toString("base64").match(/.{1,64}/g).join("\\n") + "\\n-----END PUBLIC KEY-----";
    
    if (plaintext.length <= max_block_size) {
        return crypto.publicEncrypt({
            key: pemPublicKey,
            padding: crypto.constants.RSA_PKCS1_PADDING
        }, Buffer.from(plaintext));
    }
    
    const encrypted_blocks = [];
    for (let i = 0; i < plaintext.length; i += max_block_size) {
        const block = plaintext.slice(i, i + max_block_size);
        const encrypted_block = crypto.publicEncrypt({
            key: pemPublicKey,
            padding: crypto.constants.RSA_PKCS1_PADDING
        }, Buffer.from(block));
        
        if (i > 0) {
            encrypted_blocks.push(Buffer.from(DEFAULT_SPLIT));
        }
        encrypted_blocks.push(encrypted_block);
    }
    
    return Buffer.concat(encrypted_blocks);
}

function mobile_encrypt(data) {
    const encrypted_bytes = rsa_encrypt(data, PUBLIC_KEY_BASE64);
    return encrypted_bytes.toString("base64").replace(/\\n/g, "");
}

function password_encrypt(password, random_str = "000000") {
    const combined = password + random_str;
    return mobile_encrypt(combined);
}
"""

try:
    ctx = execjs.compile(JS_ENCRYPT_CODE)
    print_color(f"✅ 成功加载内置加密JS代码", COLOR_GREEN)
except Exception as e:
    print(f"❌ 加载加密JS代码失败: {e}")
    print("-"*50)
    print(JS_ENCRYPT_CODE)
    print("-"*50)
    sys.exit(1)

def retry_request(request_func, attempts=3, delay=5):
    for i in range(attempts):
        try:
            response = request_func()
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if i < attempts - 1:
                print_color(f"⚠️ 请求失败，第 {i + 1}/{attempts} 次重试... 错误: {e}", COLOR_YELLOW)
                time.sleep(delay)
            else:
                raise

def parse_accounts(account_str):
    accounts = []
    if not account_str:
        return accounts
    
    pairs = account_str.split('#')
    for pair in pairs:
        pair = pair.strip()
        if not pair:
            continue
            
        try:
            mobile, password = pair.split('@', 1)
            accounts.append({
                'mobile': mobile,
                'password': password
            })
        except ValueError:
            print_color(f"❌ 账号格式错误: {pair}，请使用手机号@密码格式，跳过该账号", COLOR_RED)
    
    return accounts

def format_flow(size_mb):
    if size_mb >= 1024:
        return f"{size_mb / 1024:.2f} GB"
    return f"{size_mb:.2f} MB"

def format_money(amount):
    try:
        return f"{float(amount):.2f}元"
    except (ValueError, TypeError):
        return "N/A元"

def perform_login(mobile, password):
    print_color(f"\n=== 中国联通账号 {mobile} 自动登录 ===", color=COLOR_BOLD)
    print_color("ℹ️ 正在准备登录...", COLOR_BLUE)
 
    try:
        print(f"🔐 开始加密手机号和密码...")
        mobile_encrypted = ctx.call('mobile_encrypt', mobile)
        password_encrypted = ctx.call('password_encrypt', password)
        print(f"✅ 加密成功")
    except Exception as e:
        print_color(f"❌ {COLOR_RED}加密过程出错：{e}", COLOR_RED)
        print_color(f"请检查内置加密函数是否正确", COLOR_RED)
        print(f"手机号: {mobile}")
        print(f"密码长度: {len(password)}")
        exit(1)
    
    device_id = hashlib.md5(mobile.encode()).hexdigest()
    unique_identifier = hashlib.md5(mobile.encode()).hexdigest()
    
    device_brand = "iPhone"
    device_model = "iPhone8,2"
    device_os = "15.8.3"
    app_version = "iphone_c@12.0200"
    channel = "GGPD"
    city = "074|742"
    sim_operator = "--,%E4%B8%AD%E5%9B%BD%E7%A7%BB%E5%8A%A8,--,--,--"
    ip_address = "192.168.5.14"

    req_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    payload = {
        "voipToken": LOGIN_VOIP_TOKEN,
        "deviceBrand": device_brand,
        "simOperator": sim_operator,
        "deviceId": device_id,
        "netWay": LOGIN_NET_WAY,
        "deviceCode": device_id,
        "deviceOS": device_os,
        "uniqueIdentifier": unique_identifier,
        "latitude": "",
        "version": app_version,
        "pip": ip_address,
        "isFirstInstall": LOGIN_IS_FIRST_INSTALL,
        "remark4": "",
        "keyVersion": LOGIN_KEY_VERSION,
        "longitude": "",
        "simCount": LOGIN_SIM_COUNT,
        "mobile": mobile_encrypted,
        "isRemberPwd": LOGIN_IS_REMEMBER_PWD,
        "appId": LOGIN_APP_ID,
        "reqtime": req_time,
        "deviceModel": device_model,
        "password": password_encrypted
    }

    headers = {
        "Host": "m.client.10010.com",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "keep-alive",
        "Accept": "*/*",
        "User-Agent": f"ChinaUnicom4.x/12.2 (com.chinaunicom.mobilebusiness; build:44; iOS {device_os}) Alamofire/4.7.3 unicom{{version:{app_version}}}",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    }

    try:
        print_color(f"🌐 正在发送登录请求到登录接口...", COLOR_BLUE)
        response = retry_request(lambda: requests.post(LOGIN_URL, data=payload, headers=headers, timeout=10))

        data = response.json()
        print_color(f"✅ 接收到响应：HTTP状态码 {response.status_code}, 业务码: {COLOR_BOLD}{data.get('code')}{COLOR_RESET}{COLOR_GREEN}, 描述: {data.get('desc')}", COLOR_GREEN)

        if data.get("code") in ["0", "0000"]:
            print_color("\n✨ 登录成功！", COLOR_GREEN)

            cookie_string = "; ".join([f"{cookie.name}={cookie.value}" for cookie in response.cookies])
            account_phone = next((cookie.value for cookie in response.cookies if cookie.name == 'u_account'), mobile)

            login_message = f"✅ 登录成功！账号: {account_phone}"
            return True, cookie_string, device_id, login_message

        else:
            login_message = f"❌ 登录失败！业务码: {data.get('code')}, 描述: {data.get('desc')}"
            print_color(f"\n{login_message}", COLOR_RED)
            return False, None, None, login_message

    except json.JSONDecodeError:
        login_message = f"❌ 登录响应不是有效的JSON格式！响应内容: {response.text[:200]}..."
        print_color(login_message, COLOR_RED)
        return False, None, None, login_message
    except requests.exceptions.RequestException as e:
        login_message = f"❌ 登录请求发生网络错误：{e}", COLOR_RED
        print_color(login_message, COLOR_RED)
        return False, None, None, login_message
    except Exception as e:
        login_message = f"❌ 登录时发生未知错误：{e}", COLOR_RED
        print_color(login_message, COLOR_RED)
        return False, None, None, login_message


def query_balance_info(headers):
    balance_messages = []
    try:
        print_color(f"🌐 正在查询话费信息...", COLOR_BLUE)
        response = retry_request(lambda: requests.post(
            BALANCE_URL,
            json=BALANCE_PARAMS,
            headers=headers,
            timeout=10
        ))
        
        data = response.json()
        
        if data.get('code') != '0000':
            raise Exception(f"查询失败: {data.get('desc', '未知错误')}")
        
        balance_messages = ["\n💸 【话费信息】"]
        
        if 'curntbalancecust' in data:
            current_balance = data['curntbalancecust']
            balance_messages.append(f"  当前可用余额: {format_money(current_balance)}")
        
        if 'realfeecust' in data:
            real_time_fee = data['realfeecust']
            balance_messages.append(f"  实时话费: {format_money(real_time_fee)}")
        
        if 'carryOverArrears' in data:
            carry_over_arrears = data['carryOverArrears']
            balance_messages.append(f"  月初结转欠费: {format_money(carry_over_arrears)}")
        
        if 'unavailablelimitfeecust' in data:
            unavailable_limit_fee = data['unavailablelimitfeecust']
            balance_messages.append(f"  未使用定向金额: {format_money(unavailable_limit_fee)}")
        
        if 'feefrozen' in data:
            frozen_fee = data['feefrozen']
            balance_messages.append(f"  冻结金额: {format_money(frozen_fee)}")
        
        if 'depositForTheMonth' in data:
            deposit_for_month = data['depositForTheMonth']
            balance_messages.append(f"  本月存款: {format_money(deposit_for_month)}")
        
        if 'realTimeFeeSpecialFlagThree' in data and isinstance(data['realTimeFeeSpecialFlagThree'], list):
            balance_messages.append("\n  套餐详情:")
            for item in data['realTimeFeeSpecialFlagThree']:
                if isinstance(item, dict) and 'subItems' in item:
                    for sub_item in item['subItems']:
                        if isinstance(sub_item, dict) and 'bill' in sub_item:
                            bill = sub_item['bill']
                            if isinstance(bill, dict) and 'integrateitem' in bill and 'realfee' in bill:
                                fee = bill['realfee']
                                name = bill['integrateitem']
                                balance_messages.append(f"  - {name}: {format_money(fee)}")
        
        if 'reminder' in data and isinstance(data['reminder'], str):
            reminder = data['reminder'].replace('</br>', ' ')
            if reminder:
                balance_messages.append(f"\n  提醒: {reminder}")
        
        return balance_messages
    
    except Exception as e:
        error_msg = f"❌ 话费查询失败: {str(e)}"
        balance_messages.append(error_msg)
        return balance_messages

def query_flow_info(headers):
    flow_messages = []
    flow_card_usage = {}
    try:
        print_color(f"🌐 正在查询流量信息...", COLOR_BLUE)
        response = retry_request(lambda: requests.post(
            FLOW_INFO_URL,
            json=FLOW_INFO_PARAMS,
            headers=headers,
            timeout=10
        ))
        
        data = response.json()
        
        if data.get('code') != '0000':
            raise Exception(f"查询失败: {data.get('desc', '未知错误')}")

        package_name = data.get('packageName', "联通套餐")
        flow_messages = [f"📊 【{package_name}】"]

        total_used_str = data.get('sum', '0')
        summary = data.get('summary', {})
        limitValue = summary.get('limitValue', '0')
        limitSpeed = summary.get('limitSpeed', '0')
        
        try:
            total_used = float(total_used_str)
        except (ValueError, TypeError):
            total_used = 0.0

        flow_messages.insert(1, f"  流量使用: {format_flow(total_used)} | 限速{limitValue}GB | 限制速率{limitSpeed}Mbps\n")

        share_data = data.get('shareData', {})
        flow_details = share_data.get('details', [])
        
        for detail in flow_details:
            if isinstance(detail, dict) and detail.get('addUpItemName') == '套餐内流量':
                try:
                    used = float(detail.get('use', '0'))
                    flow_messages.append(f"  - {detail.get('addUpItemName')}: {format_flow(used)}")
                except (ValueError, TypeError):
                    flow_messages.append(f"  - {detail.get('addUpItemName')}: 数据获取失败")

        vice_cards = share_data.get('viceCardList', [])
        
        if vice_cards:
            flow_messages.append("\n  各卡流量使用:")
            for idx, card in enumerate(vice_cards):
                if isinstance(card, dict):
                    card_number = card.get('usernumber', '未知号码')
                    try:
                        card_used = float(card.get('use', '0'))
                    except (ValueError, TypeError):
                        card_used = 0.0
                        
                    card_label = "主卡" if idx == 0 else "副卡"
                    flow_card_usage[card_number] = card_used
                    flow_messages.append(f"  - {card_number}（{card_label}）: {format_flow(card_used)}")

        return flow_messages, flow_card_usage

    except Exception as e:
        error_msg = f"❌ 流量查询失败: {str(e)}"
        flow_messages.append(error_msg)
        return flow_messages, flow_card_usage

def query_voice_info(headers, flow_card_usage):
    voice_messages = ["\n📞 【套餐语音使用情况】"]
    voice_card_usage = {}
    try:
        print_color(f"🌐 正在查询语音信息...", COLOR_BLUE)
        response = retry_request(lambda: requests.post(
            VOICE_INFO_URL,
            json=VOICE_INFO_PARAMS,
            headers=headers,
            timeout=10
        ))
        
        data = response.json()
        
        if data.get('code') != '0000':
            raise Exception(f"查询失败: {data.get('desc', '未知错误')}")

        total_minutes = 0
        total_used = 0
        
        if 'resources' in data and isinstance(data['resources'], list):
            for resource in data['resources']:
                if isinstance(resource, dict) and resource.get('type') == 'Voice':
                    if 'remainResource' in resource and 'userResource' in resource:
                        try:
                            remain = float(resource['remainResource'])
                            used = float(resource['userResource'])
                            total_minutes += remain + used
                            total_used += used
                        except (ValueError, TypeError):
                            continue
                    
                    if 'details' in resource and isinstance(resource['details'], list):
                        for detail in resource['details']:
                            if isinstance(detail, dict) and 'viceCardlist' in detail:
                                for card in detail.get('viceCardlist', []):
                                    if isinstance(card, dict) and 'usernumber' in card and 'use' in card:
                                        card_number = card['usernumber']
                                        try:
                                            used = int(float(card['use']))
                                            voice_card_usage[card_number] = voice_card_usage.get(card_number, 0) + used
                                        except (ValueError, TypeError):
                                            continue
        
        total_remaining = total_minutes - total_used
        
        voice_messages.append(f"  总可用: {total_minutes}分钟 | 已用: {total_used}分钟 | 剩余: {total_remaining}分钟")

        if voice_card_usage and flow_card_usage:
            voice_messages.append("\n  各卡累计语音使用:")
            for idx, card_number in enumerate(flow_card_usage.keys()):
                used = voice_card_usage.get(card_number, 0)
                card_label = "主卡" if idx == 0 else "副卡"
                voice_messages.append(f"  - {card_number}（{card_label}）: {used}分钟")

        return voice_messages

    except Exception as e:
        error_msg = f"❌ 语音查询失败: {str(e)}"
        voice_messages.append(error_msg)
        return voice_messages
    
    
def process_account(account):
    mobile = account['mobile']
    password = account['password']
    
    notification_messages = []
    script_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notification_messages.append(f"账号 {mobile} 脚本开始运行: {script_start_time}")
    
    MAX_LOGIN_ATTEMPTS = 2
    login_success = False
    attempts = 0
    
    while attempts < MAX_LOGIN_ATTEMPTS and not login_success:
        attempts += 1
        login_success, cookie, device_id_val, login_msg = perform_login(mobile, password)
        notification_messages.append(f"尝试 {attempts}/{MAX_LOGIN_ATTEMPTS}: {login_msg}")
        if not login_success and "ECS99999" in login_msg and attempts < MAX_LOGIN_ATTEMPTS:
            time.sleep(2)

    if login_success and cookie:
        print_color("\n" + "="*40, color=COLOR_BOLD)
        print_color(f"\n=== 账号 {mobile} 信息查询流程开始 ===", color=COLOR_BOLD)
        notification_messages.append("\n--- 查询流程 ---")

        headers = {
            "Host": "m.client.10010.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Connection": "keep-alive",
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_8_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 unicom android@12.0100",
            "Origin": "https://m.client.10010.com",
            "Referer": "https://m.client.10010.com/"
        }

        print_color("\n🔍 开始查询话费信息...", COLOR_YELLOW)
        balance_messages = query_balance_info(headers)
        notification_messages.extend(balance_messages)
        for msg in balance_messages:
            print_color(msg, COLOR_CYAN)

        time.sleep(1)

        print_color("\n🔍 开始查询流量信息...", COLOR_YELLOW)
        flow_messages, flow_card_usage = query_flow_info(headers)
        notification_messages.extend(flow_messages)
        for msg in flow_messages:
            print_color(msg, COLOR_CYAN)

        time.sleep(1)

        print_color("\n🔍 开始查询语音信息...", COLOR_YELLOW)
        voice_messages = query_voice_info(headers, flow_card_usage)
        notification_messages.extend(voice_messages)
        for msg in voice_messages:
            print_color(msg, COLOR_PURPLE)

        print_color(f"\n=== 账号 {mobile} 信息查询流程结束 ===", color=COLOR_BOLD)
        print_color("\n" + "="*40, color=COLOR_BOLD)

    else:
        print_color(f"\n❌ 账号 {mobile} 登录失败，无法执行查询操作。", COLOR_RED)

    print_color(f"\n=== 账号 {mobile} 脚本运行结束 ===", color=COLOR_BOLD)
    script_end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notification_messages.append(f"\n脚本运行结束: {script_end_time}")

    full_notification_content = "\n".join(notification_messages)
    notification_title = f"联通查询 {mobile}"
    
    single_notification = get_env(ENV_SINGLE_NOTIFICATION, required=False, default="false").lower()
    if single_notification != "true":
        send(notification_title, full_notification_content)
    
    return {
        'mobile': mobile,
        'success': login_success,
        'messages': notification_messages
    }

if __name__ == "__main__":
    print_color(f"{'='*20} 联通多账号信息查询脚本 {'='*20}", color=COLOR_BOLD)
    
    accounts_str = get_env(ENV_MOBILE_PASSWORD)
    accounts = parse_accounts(accounts_str)
    
    if not accounts:
        print_color(f"❌ 未配置有效账号，请检查 {ENV_MOBILE_PASSWORD} 环境变量", COLOR_RED)
        exit(1)
    
    print_color(f"ℹ️ 共配置 {len(accounts)} 个有效账号，开始处理...", COLOR_BLUE)
    
    all_results = []
    overall_success = True
    
    for i, account in enumerate(accounts):
        print_color(f"\n{'='*40}", color=COLOR_BOLD)
        print_color(f"{'='*10} 开始处理账号 {i+1}/{len(accounts)}: {account['mobile']} {'='*10}", color=COLOR_BOLD)
        print_color(f"{'='*40}\n", color=COLOR_BOLD)
        
        result = process_account(account)
        all_results.append(result)
        
        if not result['success']:
            overall_success = False
        
        if i < len(accounts) - 1:
            print_color(f"\nℹ️ 等待5秒后处理下一个账号...", COLOR_BLUE)
            time.sleep(5)
    
    single_notification = get_env(ENV_SINGLE_NOTIFICATION, required=False, default="false").lower()
    if single_notification == "true":
        combined_title = f"联通多账号查询结果: {'全部成功' if overall_success else '部分失败'}"
        combined_content = f"脚本执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for result in all_results:
            combined_content += f"{'='*20} 账号 {result['mobile']} {'='*20}\n"
            combined_content += "\n".join(result['messages'])
            combined_content += "\n\n"
        
        send(combined_title, combined_content)
    
    print_color(f"\n{'='*20} 所有账号处理完成 {'='*20}", color=COLOR_BOLD)
    print_color(f"执行结果: {'全部成功' if overall_success else '部分失败'}", COLOR_GREEN if overall_success else COLOR_RED)
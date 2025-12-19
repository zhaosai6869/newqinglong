import os
import sys
import json
import time
import requests
import random
import uuid
import platform
import hashlib
from datetime import datetime
import urllib3

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 变量名
ENV_NAME = "S_DFCF"
# 账号分隔符
ACCOUNT_SEPARATOR = "&"
# 参数分隔符
PARAM_SEPARATOR = "#"

# 日志级别
LOG_DEBUG = 0
LOG_INFO = 1
LOG_WARNING = 2
LOG_ERROR = 3
# 当前日志级别
LOG_LEVEL = LOG_INFO

def log(level, message, end="\n"):
    """
    日志输出
    
    Args:
        level: 日志级别
        message: 日志消息
        end: 行尾字符，默认为换行
    """
    if level >= LOG_LEVEL:
        level_str = {
            LOG_DEBUG: "DEBUG",
            LOG_INFO: "INFO",
            LOG_WARNING: "WARNING",
            LOG_ERROR: "ERROR"
        }.get(level, "INFO")
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{level_str}] {time_str} - {message}", end=end)

def get_env(env_name):
    """
    获取环境变量
    """
    value = os.getenv(env_name)
    if not value:
        log(LOG_ERROR, f"未设置环境变量: {env_name}")
        return None
    return value

def generate_req_id():
    """
    生成随机请求ID，格式类似UUID
    """
    return str(uuid.uuid4())

def generate_app_guid():
    """
    生成AppGUID，格式为"appzxzw"+UUID
    """
    return f"appzxzw{uuid.uuid4()}"

def collect_read_info(account, info_id, req_id):
    """
    发送资讯阅读数据收集请求
    """
    try:
        url = "https://np-metadata.eastmoney.com/api/collect"
        
        headers = {
            "EM-OS": "Android",
            "EM-PKG": "com.eastmoney.android.berlin",
            "EM-VER": "10.28.1",
            "EM-GT": account["gtoken"],
            "EM-MD": account["em_md"],
            "EM-CHL": "xiaomi22_64",
            "EM-GV": "3f4605b67",
            "EM-CT": account["ctoken"],
            "EM-UT": account["utoken"],
            "EM-SL": "0",
            "EM-PA": "1",
            "em-dns": "1",
            "EM-AB": "R_1Lk;test_1LG;",
            "Content-Type": "application/json; charset=UTF-8",
            "Host": "np-metadata.eastmoney.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/3.12.13"
        }
        
        data = {
            "collect_mode": 1,
            "device_id": account["device_id"],
            "event_type": 1,
            "info_id": info_id,
            "info_subtype": 0,
            "info_type": 1,
            "mac": "02:00:00:00:00:00",
            "orig_id": "",
            "os_name": "android",
            "os_ver": "Xiaomi 2210132C 15",
            "pc_token": account["utoken"],
            "pkg_name": "cfw",
            "pkg_ver": "10.28.1",
            "req_id": req_id,
            "source": 1,
            "uid": account["uid"]
        }
        
        log(LOG_DEBUG, f"数据收集请求URL: {url}")
        log(LOG_DEBUG, f"数据收集请求头: {json.dumps(headers, ensure_ascii=False)}")
        log(LOG_DEBUG, f"数据收集请求体: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=10, verify=False)
        log(LOG_DEBUG, f"数据收集响应: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        log(LOG_ERROR, f"发送数据收集请求异常: {str(e)}")
        return False

def get_news_content(news_id, guid):
    """
    获取资讯内容
    """
    try:
        url = f"https://newsinfo.eastmoney.com/kuaixun/v2/api/content/getnews"
        params = {
            "newsid": news_id,
            "newstype": "1",
            "guid": guid,
            "source": "sec_android",
            "version": "10.28.1",
            "pkg": "com.eastmoney.android.berlin"
        }
        
        headers = {
            "Host": "newsinfo.eastmoney.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=145570492;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "Accept": "*/*",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        log(LOG_DEBUG, f"获取资讯内容请求URL: {url}")
        log(LOG_DEBUG, f"获取资讯内容请求参数: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取资讯内容响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                content = response.json()
                log(LOG_DEBUG, "获取资讯内容成功")
                return True
            except:
                log(LOG_WARNING, "获取资讯内容解析失败")
                return False
        else:
            log(LOG_WARNING, f"获取资讯内容请求失败, 状态码: {response.status_code}")
            return False
    except Exception as e:
        log(LOG_ERROR, f"获取资讯内容异常: {str(e)}")
        return False

def parse_account(account_str):
    """
    解析账号字符串
    变量值格式: UID#CTOKEN#UTOKEN#GTOKEN#EM-MD#DEVICEID#NAME
    """
    try:
        if not account_str or account_str.count(PARAM_SEPARATOR) < 6:
            log(LOG_ERROR, f"账号格式错误: {account_str}")
            return None

        parts = account_str.split(PARAM_SEPARATOR)
        return {
            "uid": parts[0],
            "ctoken": parts[1],
            "utoken": parts[2],
            "gtoken": parts[3],
            "em_md": parts[4],
            "device_id": parts[5],
            "name": parts[6] if len(parts) > 6 else "未知用户"
        }
    except Exception as e:
        log(LOG_ERROR, f"解析账号出错: {str(e)}")
        return None

def sign_in(account):
    """
    东方财富签到
    """
    try:
        url = "https://empointcpf.eastmoney.com/ActivityView/ShareActivity/shareactivitybusiness/fission/receivesignredpacket"
        headers = {
            "Host": "empointcpf.eastmoney.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=176099162;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Accept": "application/json, text/plain, */*",
            "GToken": account["gtoken"],
            "Content-Type": "application/json;charset=UTF-8",
            "EM-MD": account["em_md"],
            "Origin": "https://empointcpf.eastmoney.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://empointcpf.eastmoney.com/ActivityView/ShareActivity/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        # 请求体为空JSON
        data = {}

        log(LOG_DEBUG, f"签到请求URL: {url}")
        log(LOG_DEBUG, f"签到请求头: {json.dumps(headers, ensure_ascii=False)}")
        log(LOG_DEBUG, f"签到请求体: {json.dumps(data, ensure_ascii=False)}")

        response = requests.post(url, headers=headers, json=data, timeout=10, verify=False)
        log(LOG_DEBUG, f"签到响应: {response.text}")

        if response.status_code != 200:
            log(LOG_ERROR, f"签到请求失败, 状态码: {response.status_code}")
            return False, f"请求失败, 状态码: {response.status_code}"

        result = response.json()
        if result.get("result") == 1:
            # 签到成功
            amount = result.get("data", {}).get("Amount", "0")
            return True, f"签到成功, 获得红包: {amount}元"
        elif result.get("result") == 2203:
            # 已经签到过
            return True, "今日已签到"
        else:
            # 其他错误
            return False, f"签到失败: {result.get('message', '未知错误')}"

    except Exception as e:
        log(LOG_ERROR, f"签到过程发生异常: {str(e)}")
        return False, f"签到异常: {str(e)}"

def get_task_list(account):
    """
    获取任务列表
    """
    try:
        url = "https://empointcpf.eastmoney.com/ShareActivity//ShareActivityTask/GetUserActivityList"
        headers = {
            "Host": "empointcpf.eastmoney.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=176099162;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Accept": "application/json, text/plain, */*",
            "GToken": account["gtoken"],
            "EM-MD": account["device_id"],
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://empointcpf.eastmoney.com/ActivityView/ShareActivity/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        response = requests.get(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取任务列表响应: {response.text}")

        if response.status_code != 200:
            log(LOG_ERROR, f"获取任务列表请求失败, 状态码: {response.status_code}")
            return None

        result = response.json()
        if result.get("result") == 1:
            # 获取成功
            return result.get("data", [])
        else:
            # 获取失败
            log(LOG_ERROR, f"获取任务列表失败: {result.get('message', '未知错误')}")
            return None

    except Exception as e:
        log(LOG_ERROR, f"获取任务列表发生异常: {str(e)}")
        return None

def get_news_id(account):
    """
    获取资讯ID
    """
    try:
        url = "https://empointcpf.eastmoney.com/ActivityView/ShareActivity/shareactivitybusiness/query/getinfobygolook"
        headers = {
            "Host": "empointcpf.eastmoney.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=176099162;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Accept": "application/json, text/plain, */*",
            "GToken": account["gtoken"],
            "EM-MD": account["em_md"],
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://empointcpf.eastmoney.com/ActivityView/ShareActivity/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        response = requests.get(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取资讯ID响应: {response.text}")

        if response.status_code != 200:
            log(LOG_ERROR, f"获取资讯ID请求失败, 状态码: {response.status_code}")
            return None

        result = response.json()
        if result.get("result") == 1:
            # 获取成功
            return result.get("data")
        else:
            # 获取失败
            log(LOG_ERROR, f"获取资讯ID失败: {result.get('message', '未知错误')}")
            return None

    except Exception as e:
        log(LOG_ERROR, f"获取资讯ID发生异常: {str(e)}")
        return None

def get_task_status(account, task_id, post_id):
    """
    获取任务状态
    """
    try:
        url = "https://empointcpf.eastmoney.com/ShareActivity/ShareActivityTask/GetUserActivityStatus"
        params = {
            "TaskId": task_id,
            "PostId": post_id
        }
        
        headers = {
            "Host": "empointcpf.eastmoney.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=145570492;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "GToken": account["gtoken"],
            "EM-MD": account["em_md"],
            "Accept": "*/*",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        log(LOG_DEBUG, f"获取任务状态请求URL: {url}")
        log(LOG_DEBUG, f"获取任务状态请求参数: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取任务状态响应: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        log(LOG_ERROR, f"获取任务状态异常: {str(e)}")
        return False

def finish_task(account, task_id, post_id):
    """
    完成任务
    """
    try:
        url = "https://empointcpf.eastmoney.com/ShareActivity/ShareActivityTask/FinishTaskV2"
        headers = {
            "Host": "empointcpf.eastmoney.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=262117811;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "GToken": account["gtoken"],
            "Content-Type": "application/json",
            "EM-MD": account["device_id"],
            "Accept": "*/*",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        data = {
            "TaskId": task_id,
            "PostId": post_id
        }

        log(LOG_DEBUG, f"完成任务请求URL: {url}")
        log(LOG_DEBUG, f"完成任务请求头: {json.dumps(headers, ensure_ascii=False)}")
        log(LOG_DEBUG, f"完成任务请求体: {json.dumps(data, ensure_ascii=False)}")

        response = requests.post(url, headers=headers, json=data, timeout=10, verify=False)
        log(LOG_DEBUG, f"完成任务响应: {response.text}")

        if response.status_code != 200:
            log(LOG_ERROR, f"完成任务请求失败, 状态码: {response.status_code}")
            return False, f"请求失败, 状态码: {response.status_code}"

        result = response.json()
        if result.get("result") == 1:
            # 完成成功
            reward = result.get("data", {}).get("Money", "0")
            return True, f"任务完成, 奖励: {reward}元红包"
        else:
            # 完成失败
            return False, f"任务失败: {result.get('message', '未知错误')}"

    except Exception as e:
        log(LOG_ERROR, f"完成任务过程发生异常: {str(e)}")
        return False, f"任务异常: {str(e)}"

def do_read_news_task(account, results=None):
    """
    执行浏览资讯任务
    
    Args:
        account: 账号信息
        results: 用于存储每次任务结果的列表
    """
    try:
        # 获取任务列表
        task_list = get_task_list(account)
        if not task_list:
            log(LOG_ERROR, "获取任务列表失败")
            return False, "获取任务列表失败"

        # 查找浏览资讯任务
        read_news_task = None
        for task in task_list:
            if "浏览一篇资讯" in task.get("Name", ""):
                read_news_task = task
                break

        if not read_news_task:
            log(LOG_WARNING, "未找到浏览资讯任务")
            return False, "未找到浏览资讯任务"

        # 检查任务完成情况
        task_id = read_news_task.get("TaskID")
        day_times = read_news_task.get("DayTimes", 0)  # 每日可完成次数
        day_finish_times = read_news_task.get("DayFinishTimes", 0)  # 已完成次数
        remaining_times = day_times - day_finish_times

        if remaining_times <= 0:
            return True, "任务已达到每日上限"

        # 如果传入了results参数，初始化为空列表
        if results is not None and not isinstance(results, list):
            results = []

        # 开始执行任务
        success_count = 0
        print("-----开始阅读分享任务-----")
        for i in range(remaining_times):
            # 获取资讯ID
            news_id = get_news_id(account)
            if not news_id:
                log(LOG_ERROR, "获取资讯ID失败")
                if results is not None:
                    results.append((False, "获取资讯ID失败"))
                continue
            
            # 生成请求ID和GUID，在后续请求中复用
            req_id = generate_req_id()
            app_guid = generate_app_guid()
            
            # 获取资讯内容
            content_result = get_news_content(news_id, app_guid)

            # 第一次模拟阅读时间
            first_read_time = 7 + random.random() * 3  # 随机7-10秒
            time.sleep(first_read_time)
            
            # 获取任务状态
            status_result = get_task_status(account, task_id, news_id)
            
            # 发送数据收集请求
            collect_result = collect_read_info(account, news_id, req_id)
            
            # 第二次模拟阅读时间
            second_read_time = 7 + random.random() * 3  # 随机7-10秒
            time.sleep(second_read_time)

            # 完成任务
            success, message = finish_task(account, task_id, news_id)
            
            # 将任务结果添加到结果列表
            if results is not None:
                results.append((success, message))

            if success:
                success_count += 1
                # 获取奖励金额
                reward = "0"
                if "奖励" in message:
                    reward = message.split("奖励: ")[1].split("元")[0]
                
                # 更新并显示最新进度
                current_progress = day_finish_times + success_count
                log(LOG_INFO, f"📰 资讯信息：浏览进度({current_progress}/{day_times})【红包 {reward}元】")

            # 任务间隔
            if i < remaining_times - 1:
                delay = 2 + random.random() * 3
                time.sleep(delay)

        return True, f"浏览资讯任务完成，成功 {success_count} 次，剩余 {remaining_times - success_count} 次未完成"

    except Exception as e:
        log(LOG_ERROR, f"执行浏览资讯任务发生异常: {str(e)}")
        return False, f"执行浏览资讯任务异常: {str(e)}"

def get_share_news_list(account, page_index=1, page_size=20):
    """
    获取趣图要闻列表
    """
    try:
        url = "https://empointcpf.eastmoney.com/ActivityView/ShareActivity/shareactivitybusiness/query/getinfolist"
        headers = {
            "Host": "empointcpf.eastmoney.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=61014566;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Accept": "application/json, text/plain, */*",
            "GToken": account["gtoken"],
            "Content-Type": "application/json;charset=UTF-8",
            "EM-MD": account["em_md"],
            "Origin": "https://empointcpf.eastmoney.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://empointcpf.eastmoney.com/ActivityView/ShareActivity/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        data = {
            "pageIndex": page_index,
            "pageSize": page_size
        }

        log(LOG_DEBUG, f"获取趣图要闻列表请求URL: {url}")
        log(LOG_DEBUG, f"获取趣图要闻列表请求体: {json.dumps(data, ensure_ascii=False)}")

        response = requests.post(url, headers=headers, json=data, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取趣图要闻列表响应: {response.text}")

        if response.status_code != 200:
            log(LOG_ERROR, f"获取趣图要闻列表请求失败, 状态码: {response.status_code}")
            return None

        result = response.json()
        if result.get("data"):
            # 获取成功
            return result.get("data", [])
        else:
            # 获取失败
            log(LOG_ERROR, f"获取趣图要闻列表失败: {result.get('message', '未知错误')}")
            return None

    except Exception as e:
        log(LOG_ERROR, f"获取趣图要闻列表过程发生异常: {str(e)}")
        return None

def share_news_complete(account, info_code, content_type=1):
    """
    完成分享趣图/要闻任务
    """
    try:
        url = "https://empointcpf.eastmoney.com/ActivityView/ShareActivity/shareactivitybusiness/fission/sharecompletenotify"
        headers = {
            "Host": "empointcpf.eastmoney.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=202965796;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Accept": "application/json, text/plain, */*",
            "GToken": account["gtoken"],
            "Content-Type": "application/json;charset=UTF-8",
            "EM-MD": account["em_md"],
            "Origin": "https://empointcpf.eastmoney.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://empointcpf.eastmoney.com/ActivityView/ShareActivity/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        data = {
            "Code": info_code,
            "ContentType": content_type
        }

        log(LOG_DEBUG, f"完成分享任务请求URL: {url}")
        log(LOG_DEBUG, f"完成分享任务请求体: {json.dumps(data, ensure_ascii=False)}")

        response = requests.post(url, headers=headers, json=data, timeout=10, verify=False)
        log(LOG_DEBUG, f"完成分享任务响应: {response.text}")

        if response.status_code != 200:
            log(LOG_ERROR, f"完成分享任务请求失败, 状态码: {response.status_code}")
            return False, f"请求失败, 状态码: {response.status_code}"

        result = response.json()
        if result.get("result") == 1:
            # 分享成功
            amount = result.get("data", {}).get("Amount", "0")
            return True, f"分享成功, 获得红包: {amount}元"
        else:
            # 分享失败
            return False, f"分享失败: {result.get('message', '未知错误')}"

    except Exception as e:
        log(LOG_ERROR, f"完成分享任务过程发生异常: {str(e)}")
        return False, f"分享任务异常: {str(e)}"

def do_share_news_task(account, results=None):
    """
    执行分享趣图/要闻任务
    
    Args:
        account: 账号信息
        results: 用于存储每次任务结果的列表
    """
    try:
        # 获取任务列表
        task_list = get_task_list(account)
        if not task_list:
            log(LOG_ERROR, "获取任务列表失败")
            return False, "获取任务列表失败"

        # 查找分享趣图/要闻任务
        share_news_task = None
        for task in task_list:
            if "分享趣图" in task.get("Name", "") or "分享要闻" in task.get("Name", ""):
                share_news_task = task
                break

        if not share_news_task:
            log(LOG_WARNING, "未找到分享趣图/要闻任务")
            return False, "未找到分享趣图/要闻任务"

        # 检查任务完成情况
        task_name = share_news_task.get("Name", "分享任务")
        day_times = share_news_task.get("DayTimes", 0)  # 每日可完成次数
        day_finish_times = share_news_task.get("DayFinishTimes", 0)  # 已完成次数
        remaining_times = day_times - day_finish_times

        if remaining_times <= 0:
            return True, f"{task_name}已达到每日上限"

        # 如果传入了results参数，初始化为空列表
        if results is not None and not isinstance(results, list):
            results = []
            
        # 开始执行任务
        success_count = 0
        current_page = 1
        
        while success_count < remaining_times:
            # 获取趣图要闻列表
            news_list = get_share_news_list(account, current_page)
            if not news_list:
                log(LOG_ERROR, f"获取趣图要闻列表失败，页码: {current_page}")
                break
            
            # 找到未分享过的内容
            unshared_news = [news for news in news_list if not news.get("IsShare", False)]
            if not unshared_news:
                current_page += 1
                continue
                
            # 分享内容
            for news in unshared_news:
                if success_count >= remaining_times:
                    break
                    
                info_code = news.get("InfoCode")
                title = news.get("Title", "未知标题")
                
                if not info_code:
                    continue
                
                # 完成分享任务
                success, message = share_news_complete(account, info_code)
                
                # 将任务结果添加到结果列表
                if results is not None:
                    results.append((success, message))
                
                if success:
                    success_count += 1
                    # 获取奖励金额
                    reward = "0"
                    if "获得红包" in message:
                        reward = message.split("获得红包: ")[1].split("元")[0]
                    
                    # 更新并显示最新进度
                    current_progress = day_finish_times + success_count
                    log(LOG_INFO, f"📤 分享信息：分享进度({current_progress}/{day_times})【红包 {reward}元】")
                    
                # 分享任务间隔
                if success_count < remaining_times:
                    delay = 3 + random.random() * 5  # 随机3-8秒
                    time.sleep(delay)
                    
            # 如果当前页的内容都处理完了但还有剩余次数，尝试下一页
            if success_count < remaining_times:
                current_page += 1
                
        return True, f"{task_name}完成，成功 {success_count} 次，剩余 {remaining_times - success_count} 次未完成"
        
    except Exception as e:
        log(LOG_ERROR, f"执行分享趣图/要闻任务发生异常: {str(e)}")
        return False, f"执行分享趣图/要闻任务异常: {str(e)}"

def query_account_info(account):
    """
    查询账号信息
    """
    try:
        url = "https://empointcpf.eastmoney.com/ActivityView/ShareActivity//ShareActivityAccount/UserAccountInfo"
        headers = {
            "Host": "empointcpf.eastmoney.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=176099162;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Accept": "application/json, text/plain, */*",
            "GToken": account["gtoken"],
            "EM-MD": account["em_md"],
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://empointcpf.eastmoney.com/ActivityView/ShareActivity/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        response = requests.get(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"查询账号响应: {response.text}")

        if response.status_code != 200:
            log(LOG_ERROR, f"查询账号信息请求失败, 状态码: {response.status_code}")
            return None

        result = response.json()
        if result.get("result") == 1:
            # 查询成功
            data = result.get("data", {})
            balance = data.get("Balance", "0")
            acc_amount = data.get("AccAmount", "0")
            return {
                "balance": balance,
                "acc_amount": acc_amount
            }
        else:
            # 查询失败
            log(LOG_ERROR, f"查询账号信息失败: {result.get('message', '未知错误')}")
            return None

    except Exception as e:
        log(LOG_ERROR, f"查询账号信息过程发生异常: {str(e)}")
        return None

def get_card_task_list(account):
    """
    获取集卡任务列表
    """
    try:
        # 构建请求URL
        timestamp = int(time.time() * 1000)
        url = f"https://empointcpf.eastmoney.com:9001/ActivityTask/getUserActivityList?activityCode=pncdm&tag=6&st={timestamp}"
        
        headers = {
            "Host": "empointcpf.eastmoney.com:9001",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=107639295;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Accept": "application/json, text/plain, */*",
            "gtoken": account["gtoken"],
            "EM-MD": account["em_md"],
            "Appkey": "EIBnBlYuvK",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://marketing.dfcfs.com/views/xcxdrawcard/maintain",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        log(LOG_DEBUG, f"获取集卡任务列表请求URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取集卡任务列表响应: {response.text}")
        
        if response.status_code != 200:
            log(LOG_ERROR, f"获取集卡任务列表请求失败, 状态码: {response.status_code}")
            return None
            
        result = response.json()
        if result.get("data"):
            return result.get("data")
        else:
            log(LOG_ERROR, f"获取集卡任务列表失败: {result.get('message', '未知错误')}")
            return None
            
    except Exception as e:
        log(LOG_ERROR, f"获取集卡任务列表发生异常: {str(e)}")
        return None

def finish_card_task(account, task_id):
    """
    完成集卡任务
    """
    try:
        url = "https://empointcpf.eastmoney.com:9001/ActivityTask/FinishActivity"
        
        headers = {
            "Host": "empointcpf.eastmoney.com:9001",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=107639296;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Accept": "application/json, text/plain, */*",
            "gtoken": account["gtoken"],
            "Content-Type": "application/json;charset=UTF-8",
            "EM-MD": account["em_md"],
            "Appkey": "EIBnBlYuvK",
            "Origin": "https://marketing.dfcfs.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://marketing.dfcfs.com/views/xcxdrawcard/maintain",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        data = {
            "TaskId": task_id
        }
        
        log(LOG_DEBUG, f"完成集卡任务请求URL: {url}")
        log(LOG_DEBUG, f"完成集卡任务请求体: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=10, verify=False)
        log(LOG_DEBUG, f"完成集卡任务响应: {response.text}")
        
        if response.status_code != 200:
            log(LOG_ERROR, f"完成集卡任务请求失败, 状态码: {response.status_code}")
            return False, f"请求失败, 状态码: {response.status_code}"
            
        result = response.json()
        if result.get("result") == 1:
            return True, "任务完成成功"
        else:
            return False, f"任务完成失败: {result.get('message', '未知错误')}"
            
    except Exception as e:
        log(LOG_ERROR, f"完成集卡任务发生异常: {str(e)}")
        return False, f"任务异常: {str(e)}"

def get_draw_card_count(account):
    """
    获取抽卡次数
    """
    try:
        # 构建请求URL
        timestamp = int(time.time() * 1000)
        url = f"https://empointcpf.eastmoney.com:9003/ActivityAccount/UserTotalPoints?activityCode=pncdm&st={timestamp}"
        
        headers = {
            "Host": "empointcpf.eastmoney.com:9003",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=104296964;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Accept": "application/json, text/plain, */*",
            "gtoken": account["gtoken"],
            "EM-MD": account["em_md"],
            "Appkey": "EIBnBlYuvK",
            "Origin": "https://marketing.dfcfs.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://marketing.dfcfs.com/views/xcxdrawcard/maintain",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        log(LOG_DEBUG, f"获取抽卡次数请求URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取抽卡次数响应: {response.text}")
        
        if response.status_code != 200:
            log(LOG_ERROR, f"获取抽卡次数请求失败, 状态码: {response.status_code}")
            return 0
            
        result = response.json()
        if result.get("result") == 1:
            draw_count = int(float(result.get("data", 0)))
            return draw_count
        else:
            log(LOG_ERROR, f"获取抽卡次数失败: {result.get('message', '未知错误')}")
            return 0
            
    except Exception as e:
        log(LOG_ERROR, f"获取抽卡次数发生异常: {str(e)}")
        return 0

def draw_card(account):
    """
    执行抽卡操作
    """
    try:
        url = "https://mkapi2.dfcfs.com/miniCollectCard/api/in/xcxjk/collectTask/drawGift"
        
        headers = {
            "Host": "mkapi2.dfcfs.com",
            "Connection": "keep-alive",
            "ut": account["utoken"],
            "sec-ch-ua-platform": "\"Android\"",
            "haslogin": "true",
            "hasSecurities": "false",
            "uid": account["uid"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "ct": account["ctoken"],
            "Accept": "application/json, text/plain, */*",
            "gtoken": account["gtoken"],
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=104296964;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "EM-MD": account["em_md"],
            "Appkey": "EIBnBlYuvK",
            "Origin": "https://marketing.dfcfs.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://marketing.dfcfs.com/views/xcxdrawcard/maintain",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        log(LOG_DEBUG, f"抽卡请求URL: {url}")
        
        response = requests.post(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"抽卡响应: {response.text}")
        
        if response.status_code != 200:
            log(LOG_ERROR, f"抽卡请求失败, 状态码: {response.status_code}")
            return False, "请求失败"
            
        result = response.json()
        if result.get("status") == 0:
            gift_type = result.get("data", {}).get("giftType", "未知")
            gift_count = result.get("data", {}).get("giftCount", 0)
            return True, f"获得卡片类型: {gift_type}, 数量: {gift_count}"
        else:
            return False, f"抽卡失败: {result.get('message', '未知错误')}"
            
    except Exception as e:
        log(LOG_ERROR, f"抽卡操作发生异常: {str(e)}")
        return False, f"抽卡异常: {str(e)}"

def get_user_card_list(account):
    """
    获取用户卡片列表
    """
    try:
        url = "https://mkapi2.dfcfs.com/miniCollectCard/api/in/xcxjk/giftList/getUserGiftList"
        
        headers = {
            "Host": "mkapi2.dfcfs.com",
            "Connection": "keep-alive",
            "ut": account["utoken"],
            "sec-ch-ua-platform": "\"Android\"",
            "haslogin": "true",
            "hasSecurities": "false",
            "uid": account["uid"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "ct": account["ctoken"],
            "Accept": "application/json, text/plain, */*",
            "gtoken": account["gtoken"],
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=255489738;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "EM-MD": account["em_md"],
            "Appkey": "EIBnBlYuvK",
            "Origin": "https://marketing.dfcfs.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://marketing.dfcfs.com/views/xcxdrawcard/maintain",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        log(LOG_DEBUG, f"获取卡片列表请求URL: {url}")
        
        response = requests.post(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取卡片列表响应: {response.text}")
        
        if response.status_code != 200:
            log(LOG_ERROR, f"获取卡片列表请求失败, 状态码: {response.status_code}")
            return None
            
        result = response.json()
        if result.get("status") == 0:
            return result.get("data", [])
        else:
            log(LOG_ERROR, f"获取卡片列表失败: {result.get('message', '未知错误')}")
            return None
            
    except Exception as e:
        log(LOG_ERROR, f"获取卡片列表发生异常: {str(e)}")
        return None

def do_card_tasks(account):
    """
    执行所有集卡任务
    """
    try:
        # 获取集卡任务列表
        tasks = get_card_task_list(account)
        if not tasks:
            log(LOG_ERROR, "获取集卡任务列表失败")
            return False, "获取集卡任务列表失败"
        
        # 记录成功和失败的任务数量
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        # 遍历并处理每个任务
        for i, task in enumerate(tasks):
            task_id = task.get("TaskID")
            task_name = task.get("Name", "未知任务")
            task_desc = task.get("Description", "")
            task_state = task.get("UserTaskState", 0)
            
            # 如果任务已完成，跳过
            if task_state == 1:  # 假设1表示已完成状态
                skipped_count += 1
                continue
                
            # 执行任务
            success, message = finish_card_task(account, task_id)
            
            if success:
                success_count += 1
                log(LOG_INFO, f"🎴 集卡任务[{i+1}/{len(tasks)}]:【{task_name}】✅ 成功")
            else:
                failed_count += 1
                log(LOG_ERROR, f"🎴 集卡任务[{i+1}/{len(tasks)}]:【{task_name}】❌失败: {message}")
                
            # 避免请求过快，添加随机延迟
            if i < len(tasks) - 1:
                delay = 1 + random.random() * 2
                time.sleep(delay)
        
        # 集卡任务完成后，执行抽卡操作
        log(LOG_INFO, "-----开始抽卡任务-----")
        
        # 获取当前抽卡次数
        draw_count = get_draw_card_count(account)
        log(LOG_INFO, f"🎴 当前可用抽卡次数: {draw_count}")
        
        # 执行抽卡
        card_success_count = 0
        if draw_count > 0:
            for i in range(draw_count):
                success, message = draw_card(account)
                if success:
                    card_success_count += 1
                    log(LOG_INFO, f"🎴 集卡抽卡: 第({i+1}/{draw_count})次 ✅ {message}")
                else:
                    log(LOG_ERROR, f"🎴 集卡抽卡: 第({i+1}/{draw_count})次 ❌ {message}")
                
                # 添加短暂延迟
                if i < draw_count - 1:
                    time.sleep(0.5 + random.random())
        
        # 查询拥有的卡片
        card_list = get_user_card_list(account)
        if card_list:
            # 统计拥有的卡片类型数量
            card_types = [card for card in card_list if card.get("count", 0) > 0]
            total_types = len([card for card in card_list if card.get("type", 0) != 99])
            log(LOG_INFO, f"🎴 集卡数量: ({len(card_types)}/{total_types})")
            
            # 显示每种卡片的数量
            for card in card_list:
                card_type = card.get("type", 0)
                card_count = card.get("count", 0)
                if card_type != 99:  # 忽略特殊类型
                    log(LOG_INFO, f"🎴 卡片类型 {card_type}: {card_count}张")
        
        return True, f"集卡任务完成，成功: {success_count}，失败: {failed_count}，跳过: {skipped_count}，抽卡: {card_success_count}"
        
    except Exception as e:
        log(LOG_ERROR, f"执行集卡任务发生异常: {str(e)}")
        return False, f"执行集卡任务异常: {str(e)}"

def get_box_task_list(account):
    """
    获取盲盒任务列表
    """
    try:
        # 构建请求URL
        timestamp = int(time.time() * 1000)
        url = f"https://empointcpf.eastmoney.com:9001/ActivityTask/getUserActivityList?activityCode=pefcb&st={timestamp}"
        
        headers = {
            "Host": "empointcpf.eastmoney.com:9001",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=197655749;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Appkey": "EIBnBlYuvK",
            "Accept": "application/json, text/plain, */*",
            "GToken": account["gtoken"],
            "EM-MD": account["em_md"],
            "Origin": "https://marketing.dfcfs.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://marketing.dfcfs.com/views/etfblindbox/index",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        log(LOG_DEBUG, f"获取盲盒任务列表请求URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取盲盒任务列表响应: {response.text}")
        
        if response.status_code != 200:
            log(LOG_ERROR, f"获取盲盒任务列表请求失败, 状态码: {response.status_code}")
            return None
            
        result = response.json()
        if result.get("data"):
            return result.get("data")
        else:
            log(LOG_ERROR, f"获取盲盒任务列表失败: {result.get('message', '未知错误')}")
            return None
            
    except Exception as e:
        log(LOG_ERROR, f"获取盲盒任务列表发生异常: {str(e)}")
        return None

def finish_box_task(account, task_id):
    """
    完成盲盒任务
    """
    try:
        url = "https://empointcpf.eastmoney.com:9001/ActivityTask/FinishActivity"
        
        headers = {
            "Host": "empointcpf.eastmoney.com:9001",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=197655749;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Accept": "application/json, text/plain, */*",
            "GToken": account["gtoken"],
            "Content-Type": "application/json;charset=UTF-8",
            "EM-MD": account["em_md"],
            "Appkey": "EIBnBlYuvK",
            "Origin": "https://marketing.dfcfs.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://marketing.dfcfs.com/views/etfblindbox/index",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        data = {
            "TaskId": task_id
        }
        
        log(LOG_DEBUG, f"完成盲盒任务请求URL: {url}")
        log(LOG_DEBUG, f"完成盲盒任务请求体: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=10, verify=False)
        log(LOG_DEBUG, f"完成盲盒任务响应: {response.text}")
        
        if response.status_code != 200:
            log(LOG_ERROR, f"完成盲盒任务请求失败, 状态码: {response.status_code}")
            return False, f"请求失败, 状态码: {response.status_code}"
            
        result = response.json()
        if result.get("result") == 1:
            return True, "任务完成成功"
        else:
            return False, f"任务完成失败: {result.get('message', '未知错误')}"
            
    except Exception as e:
        log(LOG_ERROR, f"完成盲盒任务发生异常: {str(e)}")
        return False, f"任务异常: {str(e)}"

def get_box_count(account):
    """
    获取盲盒数量
    """
    try:
        # 构建请求URL
        timestamp = int(time.time() * 1000)
        url = f"https://empointcpf.eastmoney.com:9003/ActivityAccount/UserTotalPoints?activityCode=pefcb&st={timestamp}"
        
        headers = {
            "Host": "empointcpf.eastmoney.com:9003",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "CToken": account["ctoken"],
            "UToken": account["utoken"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "EM-OS": "android",
            "EM-VER": "10.28.1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=197655749;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "Appkey": "EIBnBlYuvK",
            "Accept": "application/json, text/plain, */*",
            "GToken": account["gtoken"],
            "EM-MD": account["em_md"],
            "Origin": "https://marketing.dfcfs.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://marketing.dfcfs.com/views/etfblindbox/index",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        log(LOG_DEBUG, f"获取盲盒数量请求URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取盲盒数量响应: {response.text}")
        
        if response.status_code != 200:
            log(LOG_ERROR, f"获取盲盒数量请求失败, 状态码: {response.status_code}")
            return 0
            
        result = response.json()
        if result.get("result") == 1:
            box_count = int(float(result.get("data", 0)))
            return box_count
        else:
            log(LOG_ERROR, f"获取盲盒数量失败: {result.get('message', '未知错误')}")
            return 0
            
    except Exception as e:
        log(LOG_ERROR, f"获取盲盒数量发生异常: {str(e)}")
        return 0

def open_box(account):
    """
    开盲盒
    """
    try:
        url = "https://mkapi2.dfcfs.com/etfBlindBox/api/in/openBox"
        
        headers = {
            "Host": "mkapi2.dfcfs.com",
            "Connection": "keep-alive",
            "ut": account["utoken"],
            "sec-ch-ua-platform": "\"Android\"",
            "haslogin": "true",
            "hasSecurities": "false",
            "uid": account["uid"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "ct": account["ctoken"],
            "Accept": "application/json, text/plain, */*",
            "gtoken": account["gtoken"],
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=197655749;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "EM-MD": account["em_md"],
            "Appkey": "EIBnBlYuvK",
            "Origin": "https://marketing.dfcfs.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://marketing.dfcfs.com/views/etfblindbox/index",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        log(LOG_DEBUG, f"开盲盒请求URL: {url}")
        
        response = requests.post(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"开盲盒响应: {response.text}")
        
        if response.status_code != 200:
            log(LOG_ERROR, f"开盲盒请求失败, 状态码: {response.status_code}")
            return False, "请求失败"
            
        result = response.json()
        if result.get("status") == 0:
            box_type = result.get("data", "未知")
            return True, f"获得盲盒类型: {box_type}"
        else:
            return False, f"开盲盒失败: {result.get('message', '未知错误')}"
            
    except Exception as e:
        log(LOG_ERROR, f"开盲盒操作发生异常: {str(e)}")
        return False, f"开盲盒异常: {str(e)}"

def get_user_box_list(account):
    """
    获取用户盲盒列表
    """
    try:
        url = "https://mkapi2.dfcfs.com/etfBlindBox/api/in/card"
        
        headers = {
            "Host": "mkapi2.dfcfs.com",
            "Connection": "keep-alive",
            "ut": account["utoken"],
            "sec-ch-ua-platform": "\"Android\"",
            "haslogin": "true",
            "hasSecurities": "false",
            "uid": account["uid"],
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Android WebView\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?1",
            "ct": account["ctoken"],
            "Accept": "application/json, text/plain, */*",
            "gtoken": account["gtoken"],
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2210132C Build/AQ3A.240912.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.86 Mobile Safari/537.36;eastmoney_android;color=w;pkg=com.eastmoney.android.berlin;appver=10.28.1;tag=197655749;statusBarHeight=35.142857;titleBarHeight=45.142857;density=3.5;androidsdkversion=35;fontsize=2;listFontSize=1;adaptAgedSwitch=0",
            "EM-MD": account["em_md"],
            "Appkey": "EIBnBlYuvK",
            "Origin": "https://marketing.dfcfs.com",
            "X-Requested-With": "com.eastmoney.android.berlin",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://marketing.dfcfs.com/views/etfblindbox/index",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        log(LOG_DEBUG, f"获取盲盒列表请求URL: {url}")
        
        response = requests.post(url, headers=headers, timeout=10, verify=False)
        log(LOG_DEBUG, f"获取盲盒列表响应: {response.text}")
        
        if response.status_code != 200:
            log(LOG_ERROR, f"获取盲盒列表请求失败, 状态码: {response.status_code}")
            return None
            
        result = response.json()
        if result.get("status") == 0:
            return result.get("data", {})
        else:
            log(LOG_ERROR, f"获取盲盒列表失败: {result.get('message', '未知错误')}")
            return None
            
    except Exception as e:
        log(LOG_ERROR, f"获取盲盒列表发生异常: {str(e)}")
        return None

def do_box_tasks(account):
    """
    执行所有盲盒任务
    """
    try:
        # 获取盲盒任务列表
        log(LOG_INFO, "-----开始盲盒任务-----")
        tasks = get_box_task_list(account)
        if not tasks:
            log(LOG_ERROR, "获取盲盒任务列表失败")
            return False, "获取盲盒任务列表失败"
        
        # 记录成功和失败的任务数量
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        # 遍历并处理每个任务
        for i, task in enumerate(tasks):
            task_id = task.get("TaskID")
            task_name = task.get("Name", "未知任务")
            task_desc = task.get("Description", "")
            task_state = task.get("UserTaskState", 0)
            
            # 如果任务已完成，跳过
            if task_state == 1:  # 假设1表示已完成状态
                skipped_count += 1
                continue
                
            # 执行任务
            success, message = finish_box_task(account, task_id)
            
            if success:
                success_count += 1
                log(LOG_INFO, f"📦 盲盒任务[{i+1}/{len(tasks)}]:【{task_name}】✅ 成功")
            else:
                failed_count += 1
                log(LOG_ERROR, f"📦 盲盒任务[{i+1}/{len(tasks)}]:【{task_name}】❌失败: {message}")
                
            # 避免请求过快，添加随机延迟
            if i < len(tasks) - 1:
                delay = 1 + random.random() * 2
                time.sleep(delay)
        
        # 盲盒任务完成后，执行开盲盒操作
        log(LOG_INFO, "-----开始开盲盒-----")
        
        # 获取当前盲盒数量
        box_count = get_box_count(account)
        log(LOG_INFO, f"📦 当前可用盲盒数量: {box_count}")
        
        # 执行开盲盒
        box_success_count = 0
        if box_count > 0:
            for i in range(box_count):
                success, message = open_box(account)
                if success:
                    box_success_count += 1
                    log(LOG_INFO, f"📦 开盲盒: 第({i+1}/{box_count})次 ✅ {message}")
                else:
                    log(LOG_ERROR, f"📦 开盲盒: 第({i+1}/{box_count})次 ❌ {message}")
                
                # 添加短暂延迟
                if i < box_count - 1:
                    time.sleep(0.5 + random.random())
        
        # 查询拥有的盲盒
        box_list = get_user_box_list(account)
        if box_list:
            # 统计拥有的盲盒类型数量
            box_types = [key for key, value in box_list.items() if int(value) > 0]
            total_types = 9  # 根据用户说明，总共有9种类型
            log(LOG_INFO, f"📦 盲盒类型数量: ({len(box_types)}/{total_types})")
            
            # 显示每种盲盒的数量
            for box_type, count in box_list.items():
                if int(count) > 0:
                    log(LOG_INFO, f"📦 盲盒类型 {box_type}: {count}个")
        
        return True, f"盲盒任务完成，成功: {success_count}，失败: {failed_count}，跳过: {skipped_count}，开盲盒: {box_success_count}"
        
    except Exception as e:
        log(LOG_ERROR, f"执行盲盒任务发生异常: {str(e)}")
        return False, f"执行盲盒任务异常: {str(e)}"

def main():
    """
    主函数
    """
    
    log(LOG_INFO, "====== 东方财富签到任务开始 ======")
    
    # 获取环境变量
    env_value = get_env(ENV_NAME)
    if not env_value:
        log(LOG_ERROR, "未获取到有效环境变量，退出")
        sys.exit(1)
    
    # 分割多账号
    account_list = env_value.split(ACCOUNT_SEPARATOR)
    log(LOG_INFO, f"📱 一共 {len(account_list)} 个账号")

    # 处理每个账号
    sign_success_count = 0
    task_success_count = 0
    card_task_success_count = 0
    box_task_success_count = 0
    
    for index, account_str in enumerate(account_list):
        account_info = parse_account(account_str)
        if not account_info:
            log(LOG_ERROR, f"第 {index+1} 个账号解析失败，跳过")
            continue
        
        # 账号信息
        uid = account_info["uid"]
        name = account_info["name"]
        
        # 账号分隔显示
        log(LOG_INFO, f"\n=========开始运行第{index+1}个账号{name}==========")
        
        # 查询账号余额信息
        account_data = query_account_info(account_info)
        if account_data:
            log(LOG_INFO, f"💰 账号余额：{account_data['balance']}元, 累计：{account_data['acc_amount']}元")
        
        # 执行签到
        sign_success, sign_message = sign_in(account_info)
        
        if sign_success:
            if "已签到" in sign_message:
                log(LOG_INFO, f"📝 每日签到：✅已完成")
            else:
                amount = sign_message.split("红包: ")[1].split("元")[0] if "红包" in sign_message else "0"
                log(LOG_INFO, f"📝 每日签到：✅已完成【红包 {amount}元】")
            sign_success_count += 1
        else:
            log(LOG_ERROR, f"❌失败: {sign_message}")
        
        # 获取任务列表 - 用于显示进度
        task_list = get_task_list(account_info)
        
        # 处理浏览资讯任务
        read_news_task = None
        if task_list:
            for task in task_list:
                if "浏览一篇资讯" in task.get("Name", ""):
                    read_news_task = task
                    break
                    
        if read_news_task:
            day_times = read_news_task.get("DayTimes", 0)  # 每日可完成次数
            day_finish_times = read_news_task.get("DayFinishTimes", 0)  # 已完成次数
            log(LOG_INFO, f"📰 资讯信息：浏览进度({day_finish_times}/{day_times})")
        
        # 执行浏览资讯任务
        print("-----开始阅读分享任务-----")
        task_results = []
        task_success, task_message = do_read_news_task(account_info)
        
        for idx, result in enumerate(task_results):
            success, message = result
            if not success:
                log(LOG_ERROR, f"🔍 浏览资讯：第({idx+1}/{len(task_results)})次 ❌失败: {message}")
                
        if task_success:
            task_success_count += 1
            
        # 处理分享趣图/要闻任务
        share_news_task = None
        if task_list:
            for task in task_list:
                if "分享趣图" in task.get("Name", "") or "分享要闻" in task.get("Name", ""):
                    share_news_task = task
                    break
                    
        if share_news_task:
            task_name = share_news_task.get("Name", "分享任务")
            day_times = share_news_task.get("DayTimes", 0)  # 每日可完成次数
            day_finish_times = share_news_task.get("DayFinishTimes", 0)  # 已完成次数
            log(LOG_INFO, f"📤 分享信息：分享进度({day_finish_times}/{day_times})")
        
        # 执行分享趣图/要闻任务
        share_results = []
        share_success, share_message = do_share_news_task(account_info)
        
        for idx, result in enumerate(share_results):
            success, message = result
            if success:
                amount = message.split("获得红包: ")[1].split("元")[0] if "获得红包" in message else "0"
                log(LOG_INFO, f"📤 分享趣闻：第({idx+1}/{len(share_results)})次【红包 {amount}元】")
            else:
                log(LOG_ERROR, f"📤 分享趣闻：第({idx+1}/{len(share_results)})次 ❌失败: {message}")
        
        if share_success:
            task_success_count += 1
        
        # 执行集卡任务
        log(LOG_INFO, f"-----开始执行集卡任务-----")
        card_success, card_message = do_card_tasks(account_info)
        
        if card_success:
            card_task_success_count += 1
            log(LOG_INFO, f"🎴 集卡任务：✅ {card_message}")
        else:
            log(LOG_ERROR, f"🎴 集卡任务：❌ {card_message}")
            
        # 执行盲盒任务
        box_success, box_message = do_box_tasks(account_info)
        
        if box_success:
            box_task_success_count += 1
            log(LOG_INFO, f"📦 盲盒任务：✅ {box_message}")
        else:
            log(LOG_ERROR, f"📦 盲盒任务：❌ {box_message}")
        
        # 再次查询账号余额，显示变化
        if account_data:
            new_account_data = query_account_info(account_info)
            if new_account_data:
                old_balance = float(account_data.get("balance", "0"))
                new_balance = float(new_account_data.get("balance", "0"))
                log(LOG_INFO, f"💰 账号余额: {old_balance}元 -> {new_balance}元，本次获得 {new_balance - old_balance}元")
        
        # 多账号之间添加随机延迟，避免请求过快
        if index < len(account_list) - 1:
            delay = round(3 + 2 * (index % 3), 2)
            log(LOG_DEBUG, f"等待 {delay} 秒后处理下一个账号")
            time.sleep(delay)
    
    # 任务总结
    log(LOG_INFO, f"\n====== 东方财富任务结束 ======")
    log(LOG_INFO, f"📊 总计 {len(account_list)} 个账号，签到成功 {sign_success_count} 个，任务成功 {task_success_count} 个，集卡任务成功 {card_task_success_count} 个，盲盒任务成功 {box_task_success_count} 个")

if __name__ == "__main__":
    main()

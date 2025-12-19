import time
import hashlib
import requests
from datetime import datetime
import json

# 修改信息
TOKEN = "7 29"  # 替换为实际 token
DEVICESN = "d0 89fe8"  # 替换为实际设备序列号

# 固定信息
BASE_URL = "https://app.geely.com"
APP_VERSION = "3.30.0"
SECRET_KEY = "0]3K@'9MK+6Jf"  

def get_headers():
    """生成请求头"""
    return {
        "User-Agent": "okhttp/4.9.3",
        "Content-Type": "application/json",
        "gl_dev_name": "PJA210",
        "gl_dev_model": "PJA210",
        "gl_dev_brand": "OPPO",
        "appversion": APP_VERSION,
        "gl_dev_id": DEVICESN,
        "gl_os_version": "35",
        "platform": "Android",
        "token": TOKEN,
        "gl_dev_platform": "android",
        "accept-language": "zh-Hans-CN;q=1",
        "devicesn": DEVICESN,
    }

def sign_in():
    """执行签到"""
    url = f"{BASE_URL}/api/v1/userSign/sign/risk"
    ts = int(time.time())
    sign_date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    body = {
        "ts": ts,
        "cId": "BLqo2nmmoPgGuJtFDWlUjRI2b1b"
    }
    sign_str = f"cId=BLqo2nmmoPgGuJtFDWlUjRI2b1b&ts={ts}{SECRET_KEY}"
    md5_sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    sweet_security_info = {
        "appVersion": APP_VERSION,
        "deviceUUID": DEVICESN,
        "geelyDeviceId": DEVICESN,
    }

    headers = get_headers()
    headers.update({
        "X-Data-Sign": md5_sign,
        "sweet_security_info": json.dumps(sweet_security_info)
    })

    print("签到请求发送中...")
    try:
        response = requests.post(url, headers=headers, json=body)
        response_data = response.json()
        if response_data.get("code") == "success":
            print(f"签到成功：{response_data.get('message')}")
        else:
            print(f"签到失败：{response_data.get('message')}")
    except Exception as e:
        print(f"签到请求失败：{e}")

def check_points():
    """查询积分"""
    url = f"{BASE_URL}/api/v1/point/available"
    headers = get_headers()

    print("积分查询请求发送中...")
    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()
        if response_data.get("code") == "success":
            available_points = response_data.get("data", {}).get("availablePoint", 0)
            print(f"可用积分：{available_points}")
        else:
            print(f"查询积分失败：{response_data.get('message')}")
    except Exception as e:
        print(f"查询积分请求失败：{e}")

def get_sign_info():
    """查询累计签到天数"""
    url = f"{BASE_URL}/api/v1/userSign/getSignMsg"
    headers = get_headers()
    current_date = datetime.now()
    body = {
        "year": current_date.year,
        "month": current_date.month
    }

    print("签到信息请求发送中...")
    try:
        response = requests.post(url, headers=headers, json=body)
        response_data = response.json()
        if response_data.get("code") == "success":
            continuous_days = response_data.get("data", {}).get("continuousSignDay", 0)
            print(f"已连续签到：{continuous_days} 天")
        else:
            print(f"查询累计签到失败：{response_data.get('message')}")
    except Exception as e:
        print(f"查询累计签到请求失败：{e}")

if __name__ == "__main__":
    sign_in()
    get_sign_info()
    check_points()
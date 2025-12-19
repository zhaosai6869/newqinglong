# ==============================================================================
# 免责声明
# 1. 本脚本仅用于个人学习和技术研究，请勿用于商业用途或大规模批量操作，使用前请遵守蜜雪冰城平台规则；
# 2. 因使用本脚本导致的账号封禁、数据异常等风险，均由使用者自行承担，脚本开发者不承担任何责任；
# 3. 请勿泄露Access-Token等隐私信息，避免账号被盗用；若平台禁止第三方脚本，請立即停止使用。
# ==============================================================================

import os
import requests
import time
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64
import urllib3
# 导入通知模块（确保notify.py在同级目录，支持notify.send(title, content)接口）
import notify

# 禁用HTTPS证书验证警告（解决InsecureRequestWarning，不影响功能）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===================== 基础配置（可根据需求调整） =====================
NOTIFY = 1  # 1=开启通知推送，0=关闭
DEBUG = 1   # 1=显示调试日志（含接口返回），0=仅显示关键信息
ENV_SPLITORS = ["@", "\n"]  # 多账号分隔符（支持@或换行）
APP_ID = "d82be6bbc1da11eb9dd000163e122ecb"  # 接口固定APP_ID，不可修改
# 私钥（用于生成接口签名，从App逆向提取，若失效需替换）
PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQCtypUdHZJKlQ9L
L6lIJSphnhqjke7HclgWuWDRWvzov30du235cCm13mqJ3zziqLCwstdQkuXo9sOP
Ih94t6nzBHTuqYA1whrUnQrKfv9X4/h3QVkzwT+xWflE+KubJZoe+daLKkDeZjVW
nUku8ov0E5vwADACfntEhAwiSZUALX9UgNDTPbj5ESeII+VztZ/KOFsRHMTfDb1G
IR/dAc1mL5uYbh0h2Fa/fxRPgf7eJOeWGiygesl3CWj0Ue13qwX9PcG7klJXfToI
576MY+A7027a0aZ49QhKnysMGhTdtFCksYG0lwPz3bIR16NvlxNLKanc2h+ILTFQ
bMW/Y3DRAgMBAAECggEBAJGTfX6rE6zX2bzASsu9HhgxKN1VU6/L70/xrtEPp4SL
SpHKO9/S/Y1zpsigr86pQYBx/nxm4KFZewx9p+El7/06AX0djOD7HCB2/+AJq3iC
5NF4cvEwclrsJCqLJqxKPiSuYPGnzji9YvaPwArMb0Ff36KVdaHRMw58kfFys5Y2
HvDqh4x+sgMUS7kSEQT4YDzCDPlAoEFgF9rlXnh0UVS6pZtvq3cR7pR4A9hvDgX9
wU6zn1dGdy4MEXIpckuZkhwbqDLmfoHHeJc5RIjRP7WIRh2CodjetgPFE+SV7Sdj
ECmvYJbet4YLg+Qil0OKR9s9S1BbObgcbC9WxUcrTgECgYEA/Yj8BDfxcsPK5ebE
9N2teBFUJuDcHEuM1xp4/tFisoFH90JZJMkVbO19rddAMmdYLTGivWTyPVsM1+9s
tq/NwsFJWHRUiMK7dttGiXuZry+xvq/SAZoitgI8tXdDXMw7368vatr0g6m7ucBK
jZWxSHjK9/KVquVr7BoXFm+YxaECgYEAr3sgVNbr5ovx17YriTqe1FLTLMD5gPrz
ugJj7nypDYY59hLlkrA/TtWbfzE+vfrN3oRIz5OMi9iFk3KXFVJMjGg+M5eO9Y8m
14e791/q1jUuuUH4mc6HttNRNh7TdLg/OGKivE+56LEyFPir45zw/dqwQM3jiwIz
yPz/+bzmfTECgYATxrOhwJtc0FjrReznDMOTMgbWYYPJ0TrTLIVzmvGP6vWqG8rI
S8cYEA5VmQyw4c7G97AyBcW/c3K1BT/9oAj0wA7wj2JoqIfm5YPDBZkfSSEcNqqy
5Ur/13zUytC+VE/3SrrwItQf0QWLn6wxDxQdCw8J+CokgnDAoehbH6lTAQKBgQCE
67T/zpR9279i8CBmIDszBVHkcoALzQtU+H6NpWvATM4WsRWoWUx7AJ56Z+joqtPK
G1WztkYdn/L+TyxWADLvn/6Nwd2N79MyKyScKtGNVFeCCJCwoJp4R/UaE5uErBNn
OH+gOJvPwHj5HavGC5kYENC1Jb+YCiEDu3CB0S6d4QKBgQDGYGEFMZYWqO6+LrfQ
ZNDBLCI2G4+UFP+8ZEuBKy5NkDVqXQhHRbqr9S/OkFu+kEjHLuYSpQsclh6XSDks
5x/hQJNQszLPJoxvGECvz5TN2lJhuyCupS50aGKGqTxKYtiPHpWa8jZyjmanMKnE
dOGyw/X4SFyodv8AEloqd81yGg==
-----END PRIVATE KEY-----
"""


# ===================== 工具函数（核心逻辑支撑） =====================
def get_13bit_timestamp():
    """生成13位时间戳（接口要求毫秒级，与App请求一致）"""
    return str(round(time.time() * 1000))


def sign_with_rsa(content):
    """RSA-SHA256签名：生成接口所需的sign参数，步骤：
    1. 用SHA256计算待签名内容的哈希值；
    2. 用私钥对哈希值进行RSA加密；
    3. 转换为URL安全的Base64编码（替换+为-、/为_，去除=）
    """
    try:
        # 加载私钥
        key = RSA.import_key(PRIVATE_KEY)
        # 计算SHA256哈希
        hash_obj = SHA256.new(content.encode("utf-8"))
        # RSA签名（二进制结果）
        signature = pkcs1_15.new(key).sign(hash_obj)
        # 转换为URL安全的Base64
        sign_b64 = base64.b64encode(signature).decode("utf-8")
        return sign_b64.replace("+", "-").replace("/", "_").rstrip("=")
    except Exception as e:
        if DEBUG:
            print(f"❌ [签名错误] {str(e)}")
        return ""


def http_request(url, headers, method="GET"):
    """发送HTTP请求：支持GET/POST，自动处理超时和HTTP错误，返回JSON结果"""
    try:
        if method.upper() == "GET":
            response = requests.get(
                url, headers=headers, timeout=10, verify=False  # verify=False：跳过证书验证
            )
        else:
            response = requests.post(
                url, headers=headers, timeout=10, verify=False
            )
        response.raise_for_status()  # 触发4xx/5xx HTTP错误
        return response.json()  # 接口返回JSON格式，直接解析
    except requests.exceptions.RequestException as e:
        if DEBUG:
            print(f"❌ [请求错误] {str(e)}")
        return None


def get_env_cookies(env_name="mxbc_data"):
    """从环境变量读取账号Token：解析多账号，返回Token列表"""
    # 读取环境变量（优先系统环境变量，本地调试可通过.env文件加载）
    user_cookie = os.getenv(env_name, "").strip()
    if not user_cookie:
        print(f"❌ 未在环境变量中找到 {env_name}，请先配置账号")
        return []
    
    # 确定多账号分隔符（优先使用存在的分隔符，与原JS脚本逻辑一致）
    splitor = ENV_SPLITORS[0]
    for s in ENV_SPLITORS:
        if s in user_cookie:
            splitor = s
            break
    
    # 分割并过滤空账号（避免无效Token）
    accounts = []
    for acc in user_cookie.split(splitor):
        acc = acc.strip()
        if acc:
            accounts.append(acc)
    return accounts


# ===================== 用户类（单账号逻辑封装） =====================
class MxbcUser:
    def __init__(self, index, token):
        self.index = index  # 账号序号（用于区分多账号）
        self.token = token  # 账号Access-Token
        self.ck_status = True  # Token有效性（默认有效，查询后更新）
        self.mobile = ""  # 绑定手机号（查询后赋值）
        self.snow_coin = 0  # 剩余雪王币（查询后赋值）
        self.notify_msg = ""  # 该账号的通知内容（汇总后推送）

    def get_headers(self):
        """生成接口请求头：模拟蜜雪冰城App的请求头，确保接口识别"""
        return {
            "app": "mxbc",  # App标识
            "appchannel": "xiaomi",  # 渠道（小米应用商店，可保留默认）
            "appversion": "3.0.3",  # App版本（需与接口兼容，勿随意修改）
            "Access-Token": self.token,  # 用户身份凭证
            "Host": "mxsa.mxbc.net",  # 接口域名
            "Connection": "Keep-Alive",  # 长连接标识
            "User-Agent": "okhttp/4.4.1"  # 网络库标识（App使用okhttp）
        }

    def query_user_info(self):
        """查询用户信息：验证Token有效性，获取手机号和雪王币"""
        print(f"\n📱 [账号{self.index}] 开始查询用户信息...")
        # 1. 生成签名和请求URL
        ts = get_13bit_timestamp()
        sign_content = f"appId={APP_ID}&t={ts}"  # 待签名内容（固定格式）
        sign = sign_with_rsa(sign_content)  # 生成sign参数
        url = f"https://mxsa.mxbc.net/api/v1/customer/info?appId={APP_ID}&t={ts}&sign={sign}"
        
        # 2. 发送请求并解析结果
        result = http_request(url, headers=self.get_headers())
        if not result:
            msg = f"[账号{self.index}] 查询失败：请求超时或接口异常"
            print(f"❌ {msg}")
            self.notify_msg += f"\n{msg}"
            self.ck_status = False
            return

        # 3. 处理接口返回（code=0表示成功）
        if result.get("code") == 0:
            data = result.get("data", {})
            self.mobile = data.get("mobilePhone", "未知手机号")  # 手机号（部分隐藏，如138****1234）
            self.snow_coin = data.get("customerPoint", 0)  # 剩余雪王币
            msg = f"[账号{self.index}] 查询成功：{self.mobile}，雪王币剩余 {self.snow_coin}枚"
            print(f"✅ {msg}")
            self.notify_msg += f"\n{msg}"
            self.ck_status = True
        else:
            err_msg = result.get("msg", "未知错误")  # 错误信息（如Token过期）
            msg = f"[账号{self.index}] Token失效：{err_msg}"
            print(f"❌ {msg}")
            self.notify_msg += f"\n{msg}"
            self.ck_status = False
            if DEBUG:
                print(f"🔍 [调试信息] 接口返回：{result}")

    def daily_signin(self):
        """每日签到：执行签到操作，获取奖励"""
        # 若Token失效，直接跳过签到
        if not self.ck_status:
            msg = f"[账号{self.index}] 跳过签到：Token已失效"
            print(f"⏭️ {msg}")
            self.notify_msg += f"\n{msg}"
            return

        print(f"\n📅 [账号{self.index}] 开始执行签到...")
        # 1. 生成签名和请求URL（与查询接口逻辑一致，仅路径不同）
        ts = get_13bit_timestamp()
        sign_content = f"appId={APP_ID}&t={ts}"
        sign = sign_with_rsa(sign_content)
        url = f"https://mxsa.mxbc.net/api/v1/customer/signin?appId={APP_ID}&t={ts}&sign={sign}"
        
        # 2. 发送请求并解析结果
        result = http_request(url, headers=self.get_headers())
        if not result:
            msg = f"[账号{self.index}] 签到失败：请求超时或接口异常"
            print(f"❌ {msg}")
            self.notify_msg += f"\n{msg}"
            return

        # 3. 处理接口返回
        if result.get("code") == 0:
            data = result.get("data", {})
            total_days = data.get("ruleValueGrowth", 0)  # 累计签到天数
            coin_got = data.get("ruleValuePoint", 0)  # 本次签到获得的雪王币
            msg = f"[账号{self.index}] 签到成功！累计{total_days}天，获得{coin_got}枚雪王币"
            print(f"🎉 {msg}")
            self.notify_msg += f"\n{msg}"
        else:
            err_msg = result.get("msg", "未知错误")  # 如“今日已签到”“账号异常”
            msg = f"[账号{self.index}] 签到失败：{err_msg}"
            print(f"❌ {msg}")
            self.notify_msg += f"\n{msg}"
            if DEBUG:
                print(f"🔍 [调试信息] 接口返回：{result}")


# ===================== 主逻辑（脚本入口） =====================
def main():
    # 打印脚本标题
    print("=" * 60)
    print("🍦 蜜雪冰城自动签到脚本（仅用于学习研究） 🍦")
    print("=" * 60)

    # 1. 从环境变量读取账号
    accounts = get_env_cookies("mxbc_data")
    if not accounts:
        print("❌ 未解析到有效账号，脚本退出")
        return
    print(f"📊 共找到 {len(accounts)} 个账号，准备执行操作...")

    # 2. 初始化用户列表（每个Token对应一个用户实例）
    all_notify_msg = []  # 汇总所有账号的通知内容
    user_list = [MxbcUser(index + 1, token) for index, token in enumerate(accounts)]

    # 3. 批量查询用户信息（验证Token有效性）
    print("\n" + "=" * 40)
    print("📝 用户信息查询结果")
    print("=" * 40)
    for user in user_list:
        user.query_user_info()
        time.sleep(1)  # 间隔1秒，避免接口限流
        if user.notify_msg:
            all_notify_msg.append(user.notify_msg.strip())  # 收集通知内容

    # 4. 批量执行签到（仅对有效Token执行）
    print("\n" + "=" * 40)
    print("🎯 签到执行结果")
    print("=" * 40)
    for user in user_list:
        user.daily_signin()
        time.sleep(1)  # 间隔1秒，避免接口限流
        # 若签到新增了通知内容（如跳过/失败），补充到汇总列表
        if user.notify_msg.strip() not in all_notify_msg:
            all_notify_msg.append(user.notify_msg.strip())

    # 5. 发送通知（汇总所有结果）
    if NOTIFY and all_notify_msg:
        notify_content = "\n".join(all_notify_msg)  # 拼接通知内容
        # 调用notify模块推送（标题+内容）
        try:
            notify.send("蜜雪冰城签到结果", notify_content)
            print("\n📤 通知已发送，请查收")
        except Exception as e:
            print(f"\n❌ 通知发送失败：{str(e)}（请检查notify.py是否存在）")

    # 打印脚本结束信息
    print("\n" + "=" * 60)
    print("👋 脚本执行完成，感谢使用（请勿违规操作）")
    print("=" * 60)


# 脚本入口：执行主逻辑
if __name__ == "__main__":
    main()
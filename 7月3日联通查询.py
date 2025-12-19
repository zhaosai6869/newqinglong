# encoding: utf-8

import os
import requests
import time
import json
from datetime import datetime

# 定义环境变量名称 (输入)
ENV_COOKIE = 'UNICOM_COOKIE'
ENV_DEVICE_ID = 'UNICOM_DEVICE_ID'
ENV_PUSH_PLUS_TOKEN = 'PUSH_PLUS_TOKEN'
ENV_TOKEN_ONLINE = 'UNICOM_TOKEN_ONLINE'
ENV_PRIVATE_TOKEN = 'UNICOM_PRIVATE_TOKEN'

# 可选环境变量
ENV_APP_VERSION = 'UNICOM_APP_VERSION'
ENV_CHANNEL = 'UNICOM_CHANNEL'

# --- 接口信息 ---
FLOW_INFO_URL = 'https://m.client.10010.com/servicequerybusiness/operationservice/queryOcsPackageFlowLeftContentRevisedInJune'
VOICE_INFO_URL = 'https://m.client.10010.com/servicequerybusiness/operationservice/queryOcsPackageFlowLeftContentRevisedInJune'
PUSHPLUS_URL = 'http://www.pushplus.plus/send'

# 固定参数
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

VOICE_INFO_PARAMS = FLOW_INFO_PARAMS.copy()  # 修正：使用副本避免参数污染

# 工具函数：格式化流量单位（MB/GB转换）
def format_flow(size_mb):
    """将MB转换为最合适的单位（MB/GB/TB）并保留2位小数"""
    units = ['MB', 'GB', 'TB']
    unit_index = 0
    size = size_mb
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"

# 工具函数：发送PushPlus推送
def send_pushplus_notification(token, title, content):
    """发送PushPlus消息通知，返回成功或失败信息"""
    try:
        headers = {'Content-Type': 'application/json'}
        payload = {
            "token": token,
            "title": title,
            "content": content,
            "channel": "wechat",
            "template": "txt"
        }
        
        response = requests.post(PUSHPLUS_URL, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        
        result = response.json()
        if result.get("code") == 200:
            return "✅ PushPlus推送成功"
        else:
            return f"❌ PushPlus推送失败: {result.get('msg', '未知错误')}"
    except requests.exceptions.RequestException as e:
        return f"❌ PushPlus网络请求错误: {str(e)}"
    except Exception as e:
        return f"❌ PushPlus推送异常: {str(e)}"

# --- 主程序入口 ---
if __name__ == "__main__":
    # 存储所有通知消息的列表
    notification_messages = []
    script_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notification_messages.append(f"📅 脚本开始运行: {script_start_time}\n")
    
    try:
        # 读取环境变量
        cookie = os.getenv(ENV_COOKIE)
        if not cookie:
            raise ValueError("请设置环境变量 UNICOM_COOKIE")
            
        device_id_val = os.getenv(ENV_DEVICE_ID)
        if not device_id_val:
            raise ValueError("请设置环境变量 UNICOM_DEVICE_ID")
            
        token_online = os.getenv(ENV_TOKEN_ONLINE)
        if not token_online:
            raise ValueError("请设置环境变量 UNICOM_TOKEN_ONLINE")
            
        private_token = os.getenv(ENV_PRIVATE_TOKEN)
        if not private_token:
            raise ValueError("请设置环境变量 UNICOM_PRIVATE_TOKEN")
            
        app_version = os.getenv(ENV_APP_VERSION, "iphone_c@12.0200")
        channel = os.getenv(ENV_CHANNEL, "GGPD")
        
        notification_messages.append("✅ 环境变量读取完成")
        
        # 验证Cookie有效性
        headers = {
            'Host': 'm.client.10010.com',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN',
            'Connection': 'keep-alive',
            'Cookie': cookie,
            'User-Agent': f"Mozilla/5.0 (iPhone; CPU iPhone OS 15_8_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 unicom{{version:{app_version}}}",
            'Origin': 'https://m.client.10010.com',
            'Referer': 'https://m.client.10010.com/',
            'token_online': token_online,
            'private_token': private_token
        }
        
        for attempt in range(3):
            try:
                response = requests.post(FLOW_INFO_URL, json=FLOW_INFO_PARAMS, headers=headers, timeout=10)
                data = response.json()
                
                if data.get('code') == '0000':
                    notification_messages.append("✅ Cookie验证成功")
                    break
                else:
                    raise Exception(f"Cookie验证失败: {data.get('desc', '未知错误')}")
            except Exception as e:
                if attempt == 2:
                    raise Exception(f"Cookie验证失败: {str(e)}")
                time.sleep(2)
        
        # 查询流量信息
        flow_messages = ["\n📊 【流量使用情况】"]
        for attempt in range(3):
            try:
                response = requests.post(FLOW_INFO_URL, json=FLOW_INFO_PARAMS, headers=headers, timeout=10)
                data = response.json()
                
                if data.get('code') != '0000':
                    raise Exception(f"查询失败: {data.get('desc', '未知错误')}")
                
                flow_data = data.get('shareData', {})
                flow_details = flow_data.get('details', [])
                
                if not flow_details:
                    raise Exception("未获取到流量详情")
                
                total_used = 0.0
                
                # 流量类型使用详情
                for detail in flow_details:
                    item_name = detail.get('addUpItemName', '未知流量类型')
                    used = float(detail.get('use', '0'))
                    total_used += used
                    flow_messages.append(f"  - {item_name}: {format_flow(used)}")
                
                # 副卡流量使用情况
                vice_cards = flow_data.get('viceCardList', [])
                if vice_cards:
                    flow_messages.append("\n  副卡流量使用:")
                    for card in vice_cards:
                        card_number = card.get('usernumber', '未知号码')
                        card_used = float(card.get('use', '0'))
                        card_label = "主卡" if card_number.startswith('131') else "副卡"
                        flow_messages.append(f"  - {card_number}（{card_label}）: {format_flow(card_used)}")
                
                # 总使用量
                flow_messages.insert(1, f"  总使用: {format_flow(total_used)}\n")
                
                notification_messages.extend(flow_messages)
                break
            except Exception as e:
                if attempt == 2:
                    flow_messages.append(f"❌ 流量查询失败: {str(e)}")
                    notification_messages.extend(flow_messages)
        
        # 查询语音信息
        voice_messages = ["\n📞 【语音使用情况】"]
        for attempt in range(3):
            try:
                response = requests.post(VOICE_INFO_URL, json=VOICE_INFO_PARAMS, headers=headers, timeout=10)
                data = response.json()
                
                if data.get('code') != '0000':
                    raise Exception(f"查询失败: {data.get('desc', '未知错误')}")
                
                # 定位语音资源
                resources = data.get('resources', [])
                voice_data = None
                for res in resources:
                    if res.get('type') == 'Voice':
                        voice_data = res
                        break
                
                if not voice_data:
                    raise Exception("未找到语音资源数据")
                
                # 总语音统计
                total_minutes = 0
                total_used = 0
                total_remaining = 0
                
                # 提取总可用分钟数
                outer_total = data.get('canUseValueAll', '0')
                try:
                    total_minutes = int(float(outer_total))
                except (ValueError, TypeError):
                    pass
                
                # 提取已用和剩余
                try:
                    total_used = int(float(voice_data.get('userResource', '0')))
                    total_remaining = int(float(voice_data.get('remainResource', '0')))
                except (ValueError, TypeError):
                    pass
                
                # 各卡语音使用量合并
                card_usage = {}
                voice_details = voice_data.get('details', [])
                for detail in voice_details:
                    for card in detail.get('viceCardlist', []):
                        card_number = card.get('usernumber', '未知号码')
                        try:
                            used = int(float(card.get('use', '0')))
                            card_usage[card_number] = card_usage.get(card_number, 0) + used
                        except (ValueError, TypeError):
                            continue
                
                # 语音信息组装
                voice_messages.append(f"  总可用: {total_minutes}分钟 | 已用: {total_used}分钟 | 剩余: {total_remaining}分钟")
                
                # 各卡累计使用
                if card_usage:
                    voice_messages.append("\n  各卡累计语音使用:")
                    for card_number, used in card_usage.items():
                        card_label = "主卡" if card_number.startswith('131') else "副卡"
                        voice_messages.append(f"  - {card_number}（{card_label}）: {used}分钟")
                
                notification_messages.extend(voice_messages)
                break
            except Exception as e:
                if attempt == 2:
                    voice_messages.append(f"❌ 语音查询失败: {str(e)}")
                    notification_messages.extend(voice_messages)
        
    except Exception as e:
        notification_messages.append(f"\n❌ 执行错误: {str(e)}")
    
    # 脚本结束时间
    script_end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notification_messages.append(f"\n📅 脚本运行结束: {script_end_time}")
    
    # 打印最终结果
    final_message = "\n".join(notification_messages)
    print(final_message)
    
    # 发送PushPlus通知
    push_token = os.getenv(ENV_PUSH_PLUS_TOKEN)
    if push_token:
        # 获取套餐名称（如果有）
        package_name = "联通套餐"
        try:
            if 'data' in locals() and data.get('packageName'):
                package_name = data.get('packageName')
        except:
            pass
            
        # 生成推送标题（包含套餐名称和日期）
        title = f"{package_name}使用情况查询"
        
        # 发送推送并获取结果
        push_result = send_pushplus_notification(push_token, title, final_message)
        print(f"\n{push_result}")
        notification_messages.append(f"\n{push_result}")
    else:
        print("\n⚠️ 未设置PushPlus Token，跳过推送")
        notification_messages.append("\n⚠️ 未设置PushPlus Token，跳过推送")
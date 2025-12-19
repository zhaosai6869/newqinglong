/**
 * 小程序：银鱼质亨
 * 
 * YYZH_ck = '备注#authori-zation'
 * 
 * 
 */
const $ = new Env("🎬 银鱼质亨");
const notify = $.isNode() ? require('../sendNotify') : '';
const YYZH_CK = process.env.YYZH_ck || '';

// 配置参数
const config = {
  onlyWithdraw: false,   // true = 只提现, false = 先刷视频再提现
  notify: true,          // 是否发送通知
  delay: 1500,           // 请求间隔时间(毫秒)
  watchDuration: 80000,  // 模拟观看时长(毫秒)
  baseVersion: "3.8.9"   // 更新为最新版本号
};

// 全局统计
const stats = {
  totalAccounts: 0,
  processedAccounts: 0,
  successWithdraw: 0,
  alreadyWithdraw: 0,
  failedWithdraw: 0,
  watchedVideos: 0
};

// 主函数
!(async () => {
  if (!YYZH_CK) {
    const msg = '❌ 请先设置环境变量 YYZH_ck';
    console.log(msg);
    if (config.notify) await notify.sendNotify('视频刷量提现错误', msg);
    return;
  }

  const accounts = YYZH_CK.split('\n').filter(v => v.trim());
  stats.totalAccounts = accounts.length;
  
  if (accounts.length === 0) {
    const msg = '❌ 未找到有效的账号信息';
    console.log(msg);
    if (config.notify) await notify.sendNotify('视频刷量提现错误', msg);
    return;
  }

  console.log(`\n🎉 共找到 ${accounts.length} 个账号`);
  
  for (let i = 0; i < accounts.length; i++) {
    const account = accounts[i].trim();
    if (!account) continue;
    
    const [remark, auth] = account.split('#').map(v => v.trim());
    const accountName = remark || `账号 ${i + 1}`;
    
    console.log(`\n📌 ━━━━━━━━━━━━━ 开始处理 ${accountName} ━━━━━━━━━━━━━`);
    await processAccount(auth, accountName);
    stats.processedAccounts++;
    
    if (i < accounts.length - 1) {
      await $.wait(2000); // 账号间间隔2秒
    }
  }
  
  // 生成统计报告
  const report = [
    '✅ 所有账号处理完成',
    `📊 统计报告:`,
    `├─ 总账号数: ${stats.totalAccounts}`,
    `├─ 已处理账号: ${stats.processedAccounts}`,
    `├─ 成功提现: ${stats.successWithdraw}`,
    `├─ 今日已提现: ${stats.alreadyWithdraw}`,
    `├─ 提现失败: ${stats.failedWithdraw}`,
    `└─ 刷视频数: ${stats.watchedVideos}`
  ].join('\n');
  
  console.log(`\n${report}`);
  if (config.notify) {
    await notify.sendNotify('🎬 视频刷量提现完成', report);
  }
})().catch(e => {
  const errorMsg = `❌ 脚本运行出错: ${e.message || e}`;
  console.log(errorMsg);
  if (config.notify) {
    notify.sendNotify('🎬 视频刷量提现错误', errorMsg);
  }
}).finally(() => {
  $.done();
});

// 处理单个账号
async function processAccount(auth, accountName) {
  try {
    if (config.onlyWithdraw) {
      console.log('ℹ️ 只提现模式已启用，跳过刷视频步骤');
      await doWithdraw(auth, accountName);
    } else {
      const videoIds = await getVideoIds(auth, accountName);
      if (videoIds.length > 0) {
        console.log(`📽️ 获取到 ${videoIds.length} 个视频ID，准备刷视频...`);
        await watchVideos(videoIds, auth, accountName);
        stats.watchedVideos += videoIds.length;
      } else {
        console.log('⚠️ 无视频可刷，跳过刷视频步骤');
      }
      await doWithdraw(auth, accountName);
    }
  } catch (e) {
    // 特殊处理提现限制错误，不中断整个流程
    if (e.message.includes('每天只可提现1次')) {
      console.log(`💰 ${accountName} 今日已提现过`);
      stats.alreadyWithdraw++;
      return;
    }
    console.log(`❌ ${accountName} 处理失败:`, e.message || e);
    stats.failedWithdraw++;
  }
}

// 获取视频ID列表
async function getVideoIds(auth, accountName) {
  const url = 'https://n05.sentezhenxuan.com/api/video/list?page=1&limit=10&status=1&source=0&isXn=1';
  const headers = getBaseHeaders(auth);
  
  try {
    console.log(`🔍 ${accountName} 正在获取视频列表...`);
    const response = await $.get({ url, headers });
    const data = safeJsonParse(response);
    
    if (!data) {
      throw new Error('无效的JSON响应');
    }
    
    if (data.status !== 200 || !Array.isArray(data.data)) {
      console.log(`⚠️ ${accountName} 获取视频列表失败:`, data.msg || '未知错误');
      return [];
    }
    
    return data.data.map(item => item.id).filter(id => typeof id === 'number');
  } catch (e) {
    console.log(`⚠️ ${accountName} 获取视频列表异常:`, e.message || e);
    return [];
  }
}

// 安全解析JSON
function safeJsonParse(str) {
  try {
    return JSON.parse(str);
  } catch (e) {
    return null;
  }
}

// 刷视频
async function watchVideos(videoIds, auth, accountName) {
  const total = videoIds.length;
  for (let i = 0; i < total; i++) {
    const vid = videoIds[i];
    const now = Date.now();
    const body = JSON.stringify({
      vid: vid,
      startTime: now - config.watchDuration,
      endTime: now,
      baseVersion: config.baseVersion,
      playMode: 0,
    });
    
    const url = 'https://n05.sentezhenxuan.com/api/video/videoJob';
    const headers = getBaseHeaders(auth);
    
    try {
      const response = await $.post({ url, headers, body });
      const data = safeJsonParse(response);
      
      if (data && data.status === 200) {
        console.log(`🎥 ${accountName} 视频 ${i + 1}/${total} 刷完 (ID: ${vid})`);
      } else {
        console.log(`⚠️ ${accountName} 视频 ${i + 1}/${total} 返回异常:`, data?.msg || '无返回数据');
      }
    } catch (e) {
      console.log(`⚠️ ${accountName} 视频 ${i + 1}/${total} 请求失败:`, e.message || e);
    }
    
    if (i < total - 1) {
      await $.wait(config.delay);
    }
  }
}

// 提现
async function doWithdraw(auth, accountName) {
  const url = 'https://n05.sentezhenxuan.com/api/userTx';
  const headers = getWithdrawHeaders(auth);
  
  try {
    console.log(`💳 ${accountName} 正在尝试提现...`);
    const response = await $.get({ url, headers });
    const data = safeJsonParse(response);
    
    if (!data) {
      throw new Error('无效的JSON响应');
    }
    
    if (data.code === 200 || data.status === 200) {
      console.log(`💰 ${accountName} 提现成功:`, data.msg || '成功');
      stats.successWithdraw++;
    } else if (data.msg && data.msg.includes('每天只可提现1次')) {
      console.log(`💰 ${accountName} 今日已提现过`);
      stats.alreadyWithdraw++;
      throw new Error(data.msg); // 特殊处理提现限制错误
    } else {
      throw new Error(data.msg || '提现失败: 未知错误');
    }
    return data;
  } catch (e) {
    if (e.message.includes('每天只可提现1次')) {
      throw e; // 重新抛出以便特殊处理
    }
    console.log(`❌ ${accountName} 提现异常:`, e.message || e);
    stats.failedWithdraw++;
    throw e;
  }
}

// 获取基础headers
function getBaseHeaders(auth) {
  return {
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json",
    "Connection": "keep-alive",
    "Referer": "https://servicewechat.com/wx5b82dfe3747e533f/5/page-frame.html",
    "Host": "n05.sentezhenxuan.com",
    "Authori-zation": auth,
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.50 NetType/WIFI Language/zh_CN",
    "Cb-lang": "zh-CN",
    "Form-type": "routine-zhixiang",
    "xweb_xhr": "1"
  };
}

// 获取提现headers
function getWithdrawHeaders(auth) {
  return {
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Referer": "https://servicewechat.com/wx5b82dfe3747e533f/5/page-frame.html",
    "Host": "n05.sentezhenxuan.com",
    "Authori-zation": auth,
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.50(0x1800323d) NetType/WIFI Language/zh_CN",
    "Cb-lang": "zh-CN",
    "Form-type": "routine-zhixiang",
    "xweb_xhr": "1"
  };
}

// 环境兼容代码
function Env(name) {
  this.name = name;
  this.isNode = () => typeof process !== 'undefined' && process.version;
  this.wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  
  // GET请求
  this.get = ({ url, headers }) => {
    if (this.isNode()) {
      return new Promise((resolve, reject) => {
        const https = require('https');
        const zlib = require('zlib');
        
        const options = {
          method: 'GET',
          headers: headers
        };
        
        const req = https.request(url, options, res => {
          let chunks = [];
          res.on('data', chunk => chunks.push(chunk));
          res.on('end', () => {
            const buffer = Buffer.concat(chunks);
            
            // 处理Gzip压缩
            if (res.headers['content-encoding'] === 'gzip') {
              zlib.gunzip(buffer, (err, decompressed) => {
                if (err) reject(err);
                else resolve(decompressed.toString());
              });
            } else {
              resolve(buffer.toString());
            }
          });
        });
        
        req.on('error', reject);
        req.end();
      });
    } else {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        for (const key in headers) {
          xhr.setRequestHeader(key, headers[key]);
        }
        xhr.responseType = 'text';
        xhr.onload = () => resolve(xhr.responseText);
        xhr.onerror = reject;
        xhr.send();
      });
    }
  };
  
  // POST请求
  this.post = ({ url, headers, body }) => {
    if (this.isNode()) {
      return new Promise((resolve, reject) => {
        const https = require('https');
        const zlib = require('zlib');
        
        const options = {
          method: 'POST',
          headers: headers
        };
        
        const req = https.request(url, options, res => {
          let chunks = [];
          res.on('data', chunk => chunks.push(chunk));
          res.on('end', () => {
            const buffer = Buffer.concat(chunks);
            
            // 处理Gzip压缩
            if (res.headers['content-encoding'] === 'gzip') {
              zlib.gunzip(buffer, (err, decompressed) => {
                if (err) reject(err);
                else resolve(decompressed.toString());
              });
            } else {
              resolve(buffer.toString());
            }
          });
        });
        
        req.on('error', reject);
        req.write(body);
        req.end();
      });
    } else {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        for (const key in headers) {
          xhr.setRequestHeader(key, headers[key]);
        }
        xhr.responseType = 'text';
        xhr.onload = () => resolve(xhr.responseText);
        xhr.onerror = reject;
        xhr.send(body);
      });
    }
  };
  
  this.done = () => {};
}
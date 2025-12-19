/**
 * create: 2025/07/20
 * author: 问情，Q群：960690899
 * description: 自行寻找
 * test: 青龙2.19.2
 * 环境变量：wqwl_hg，多个换行或者新建多个
 * 免责声明：本脚本仅用于学习，请勿用于商业用途，否则后果自负，请在下载24小时之内删除，否则请自行承担。有问题自行解决。
 * 注：本脚本大多数代码均为ai写。
 */

const axios = require('axios')
const BASE_URL = 'http://www.iuris.cn'

let index = 0
class HongGuo {
    constructor(userCookie) {
        this.index = index++
        this.ck = userCookie.split("#")
        this.headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/json",
            "token": "",
            "unionid": "null",
            "Referer": "http://app.ooowz.cn/"
        }
        this.unionid = ""

    }
    async getCookie() {
        this.sendMessage(`开始执行第${this.index + 1}个账号:${this.ck[0].slice(0, 3)}****${this.ck[0].slice(-4)}`)
        const user = this.ck[0]
        const password = this.ck[1]
        const config = {
            url: BASE_URL + '/user/isuser2',
            method: 'POST',
            headers: this.headers,
            data: JSON.stringify({
                phone: user,
                password: password
            })
        }
        const res = await axios(config)
        if (res.data.data == 1) {
            this.headers['unionid'] = res.data.result.unionid
            this.headers['token'] = res.data.result.token
            this.unionid = res.data.result.unionid
            this.sendMessage('登录成功')
        }
        else {
            this.sendMessage(res.data.content)
            return
        }
    }

    //打卡
    async sign() {
        const config = {
            url: BASE_URL + '/user/activeone',
            method: 'POST',
            headers: this.headers,
            data: JSON.stringify({
                unionid: this.unionid
            })
        }
        const res = await axios(config)
        if (res.data.code == 1) {
            this.sendMessage('打卡成功')
        } else {
            this.sendMessage(res.data.content)
        }
    }

    //提现
    async pushcash() {
        const config = {
            url: BASE_URL + '/trade/pushcash',
            method: 'POST',
            headers: this.headers,
            data: JSON.stringify({
                unionid: this.unionid,
                money: 0.5
            })
        }
        const res = await axios(config)
        if (res.data.code == 1) {
            this.sendMessage('提现成功')
        } else {
            this.sendMessage(res.data.content)
        }
    }

    async main() {
        this.sendMessage('>开始登录')
        await this.getCookie()
        await this.sleep(3000)
        this.sendMessage('>开始签到')
        await this.sign()
        await this.sleep(3000)
        this.sendMessage('>开始提现')
        await this.pushcash()
        await this.sleep(3000)
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    sendMessage(text) {
        console.log(`账号[${this.index + 1}]:${text}`)
    }
}

//获取环境变量
function checkEnv(userCookie) {
    try {
        const envSplitor = ["&", "\n"];
        //this.sendMessage(userCookie);
        let userList = userCookie
            .split(envSplitor.find((o) => userCookie.includes(o)) || "&")
            .filter((n) => n);
        if (!userList || userList.length === 0) {
            console.log("没配置环境变量就要跑脚本啊！！！");
            console.log("🔔还没开始已经结束!");
            process.exit(1);
        }

        console.log(`共找到${userList.length}个账号`);
        return userList;
    } catch (e) {
        console.log("环境变量格式错误,下面是报错信息")
        console.log(e);
    }
}

!(async function () {
    console.log("红果诈骗开始运行");
    const tokens = checkEnv(process.env['wqwl_hg']);
    const tasks = tokens.map(token => new HongGuo(token).main());
    await Promise.all(tasks); // 所有任务并发执行
    console.log("全部任务已完成！");
})(); 
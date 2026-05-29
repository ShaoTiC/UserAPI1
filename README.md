# UserAPI1

A little REST API.

## 端午高铁抢票 Skill

本仓库包含一个本地演示版的 12306 风格抢票技能：

- `ticket_skill/skill.py`：Python 抢票核心逻辑，支持起始地、终止地、车次和一等座/二等座/无座选择。
- `ticket_skill/server.py`：无外部依赖的 HTTP API 和静态页面服务器。
- `static/index.html`：Vue3 页面，展示成功购买页面或失败结果。

> 安全说明：该实现是本地演示技能，不会登录真实 12306、不会绕过验证码、不会排队下单、不会发起真实支付。真实接入应遵守 12306 官方规则和用户授权流程。

### 运行页面

```bash
python -m ticket_skill.server
```

然后打开 <http://127.0.0.1:8000>。

### 命令行调用

```bash
python -m ticket_skill.skill \
  --passenger 张三 \
  --origin 北京南 \
  --destination 上海虹桥 \
  --travel-date 2026-06-19 \
  --seat-type second_class \
  --seat-type first_class
```

成功时会返回购买人、乘车时间、起始地、终止地、检票口、座位号、车次和席别；失败时会返回失败原因与可参考的余票信息。

### 测试

```bash
python -m unittest discover -s tests
```

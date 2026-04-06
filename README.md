# 草台香飞书自动检查服务 - 云端部署指南

## 🚀 部署到Railway（推荐）

### 步骤1：准备代码

代码已经准备好，位于���`/Users/a0/Desktop/caotaixiang_feishu_checker/`

### 步骤2：上传到GitHub

#### 2.1 创建GitHub仓库

1. 访问 https://github.com/new
2. 仓库名称：`caotaixiang-feishu-checker`
3. 设为私有仓库（推荐）
4. 点击"Create repository"

#### 2.2 上传代码

在终端执行：

```bash
cd /Users/a0/Desktop/caotaixiang_feishu_checker

# 初始化Git
git init
git add .
git commit -m "Initial commit"

# 连接到GitHub（替换YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/caotaixiang-feishu-checker.git
git branch -M main
git push -u origin main
```

### 步骤3：部署到Railway

#### 3.1 注册Railway

1. 访问：https://railway.app/
2. 点击"Login" → 使用GitHub账号登录
3. 授权Railway访问你的GitHub

#### 3.2 创建新项目

1. 点击"New Project"
2. 选择"Deploy from GitHub repo"
3. 选择你的仓库：`caotaixiang-feishu-checker`
4. Railway会自动检测Python项目

#### 3.4 配置环境变量

在Railway项目页面：

1. 点击"Variables"
2. 添加以下环境变量：

```
FEISHU_APP_ID=cli_a94657a12e785bef
FEISHU_APP_SECRET=WkdaUXI3mK6gHEkPG4zLWRav7MbNSzDH
FEISHU_TABLE_ID=IfjDbTm0taVdnTsIQVscLVR6nFg/tblFgjLfovuQR6e2
CLAUDE_API_BASE=https://cloud.hongqiye.com
CLAUDE_API_KEY=sk-6uvjtSSt8vZlJ4SByF9ciuCohRq4IUCMWs0FPW3qsYdQkHcc
CLAUDE_MODEL=claude-opus-4-5-20251101
```

#### 3.5 获取服务地址

1. 等待部署完成（约2-3分钟）
2. 在Railway项目首页，会看到生成的域名
3. 例如：`https://caotaixiang-checker.up.railway.app`

**记住这个地址，后面配置飞书webhook需要用到！**

---

## 🔧 配置飞书自动化

### 步骤4：设置飞书自动化

#### 4.1 打开飞书多维表格

访问：https://feishu.cn/base/IfjDbTm0taVdnTsIQVscLVR6nFg

#### 4.2 创建自动化

1. 点击右上角 **"自动化"** 按钮
2. 点击 **"新建自动化"**
3. 选择触发条件：**"当记录创建时"**

#### 4.3 配置触发条件

**条件：**
- 字段：`原文案`
- 运算符：`不为空`

#### 4.4 添加操作：发送Webhook

1. 点击 **"添加操作"**
2. 搜索并选择 **"发送webhook请求"**
3. 配置webhook：

**请求URL：**
```
https://你的Railway域名/webhook/check
```

例如：
```
https://caotaixiang-checker.up.railway.app/webhook/check
```

**请求方法：**
```
POST
```

**请求头（Headers）：**
```json
{
  "Content-Type": "application/json"
}
```

**请求体（Body）：**
```json
{
  "record_id": {{记录ID}},
  "original_copy": {{原文案}},
  "content_type": "通用"
}
```

> **注意：** `{{记录ID}}` 和 `{{原文案}}` 需要从飞书的动态字段中选择！

#### 4.5 启用自动化

1. 点击 **"保存"**
2. 给自动化命名：`草台香文案自动检查`
3. 打开自动化开关

---

## 🎉 完成！开始使用

### 使用流程：

1. ✅ Railway服务自动运行（24小时在线）
2. 打开飞书多维表格
3. 添加新记录
4. 填写`原文案`字段
5. 保存记录
6. 🤖 **自动触发检查！**
7. 等待10-20秒
8. 刷新表格，查看`毒舌点评`、`修改建议`、`修改后内容`

---

## 📊 监控和日志

### 查看Railway日志

1. 访问Railway项目
2. 点击你的服务
3. 点击"View Logs"
4. 实时查看请求和处理日志

### 查看服务状态

访问：`https://你的Railway域名/`

应该看到：
```json
{
  "service": "草台香飞书自动检查服务",
  "status": "running",
  "version": "1.0"
}
```

---

## 💰 成本说明

### Railway免费套餐

- ✅ 每月 $5 免费额度
- ✅ 足够个人使用
- ✅ 自动休眠（无请求30分钟后）
- ✅ 有请求时自动唤醒（约10-20秒）

### 升级到付费（可选）

如果需要更快的响应速度：
- Pay as you go：$0.000272/请求
- 一般月费用 <$5

---

## 🛠️ 故障排查

### 问题1：Webhook连接失败

**检查：**
1. Railway服务是否正在运行
2. 域名是否正确
3. 环境变量是否配置正确

**解决：**
- 查看Railway日志
- 测试服务：访问 `https://你的域名/health`

### 问题2：没有自动触发

**检查：**
1. 飞书自动化是否开启
2. 触发条件是否正确设置
3. Webhook URL是否正确

**解决：**
- 重新配置飞书自动化
- 在飞书自动化日志中查看错误信息

### 问题3：检查结果没有出现

**检查：**
1. 等待20-30秒（Claude分析需要时间）
2. 刷新表格
3. 查看Railway日志是否有错误

---

## 🔄 更新代码

如果需要修改代码：

```bash
# 在本地修改
cd /Users/a0/Desktop/caotaixiang_feishu_checker
# 编辑文件...

# 提交到GitHub
git add .
git commit -m "Update code"
git push

# Railway会自动重新部署
```

---

## 📞 技术支持

如有问题，查看：
- Railway日志：https://railway.app/
- 飞书自动化日志：飞书多维表格 → 自动化

---

**部署完成后，你的服务就是24小时在线的全自动文案检查系统！** 🚀

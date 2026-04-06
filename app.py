from flask import Flask, request, jsonify
import json
import requests
import os
from pathlib import Path

app = Flask(__name__)

# 从环境变量读取配置
CONFIG_FILE = Path("/data/feishu_config.json")

class FeishuWebhookHandler:
    def __init__(self):
        self.load_config()
        self.checked_ids = set()

    def load_config(self):
        """从环境变量或文件加载配置"""
        # 优先使用环境变量
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.table_id = os.getenv("FEISHU_TABLE_ID")
        self.claude_api_base = os.getenv("CLAUDE_API_BASE", "https://cloud.hongqiye.com")
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-opus-4-5-20251101")

        # 如果环境变量为空，尝试从文件读取
        if not all([self.app_id, self.app_secret, self.table_id]):
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.app_id = config.get("app_id", self.app_id)
                    self.app_secret = config.get("app_secret", self.app_secret)
                    self.table_id = config.get("table_id", self.table_id)
                    self.claude_api_base = config.get("claude_api_base", self.claude_api_base)
                    self.claude_api_key = config.get("claude_api_key", self.claude_api_key)
                    self.claude_model = config.get("claude_model", self.claude_model)

        # 验证配置
        if not all([self.app_id, self.app_secret, self.table_id, self.claude_api_key]):
            raise Exception("配置不完整，请检查环境变量或配置文件")

    def get_tenant_access_token(self):
        """获取飞书令牌"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        response = requests.post(url, json={
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })
        data = response.json()
        if data.get("code") != 0:
            raise Exception(f"获取令牌失败：{data.get('msg')}")
        return data.get("tenant_access_token")

    def call_claude(self, copy_text, content_type):
        """调用Claude API"""
        url = f"{self.claude_api_base}/v1/messages"
        headers = {
            "x-api-key": self.claude_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        prompt = f"""你是草台香品牌的毒舌文案专家。

【品牌信息】
- 草台香·草本酱香
- 核心工艺：入曲前36味草本
- 创始人：王绍岐（69岁退伍军人，实在、直爽、有温度）
- 理念：好酒不该是有钱人的专利

【合规要求】
- 严禁：最好、第一、顶级、解酒、护肝、葛根、不上头、不口干
- 王绍岐人设：不说网络用语（yyds、绝绝子、家人们）
- 不涉及未成年人

【文案类型】：{content_type}

【原文案】：
{copy_text}

【请按以下格式回复，不要有多余废话】：

🎯 毒舌点评：
[犀利、幽默地指出问题]

❌ 主要问题：
1. [问题1]
2. [问题2]

💡 修改建议：
[具体建议]

✨ 修改后文案：
[完整的修改版本]"""

        payload = {
            "model": self.claude_model,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            data = response.json()
            if "content" in data:
                return data["content"][0]["text"]
            return "API调用失败"
        except Exception as e:
            return f"调用失败：{str(e)}"

    def parse_claude_response(self, response):
        """解析Claude回复"""
        import re
        result = {"毒舌点评": "", "修改建议": "", "修改后内容": ""}

        lines = response.split('\n')
        current_key = None
        current_content = []

        for line in lines:
            if "🎯" in line or "毒舌点评" in line:
                if current_key and current_content:
                    result[current_key] = '\n'.join(current_content).strip()
                current_key = "毒舌点评"
                current_content = []
            elif "❌" in line or "主要问题" in line:
                if current_key and current_content:
                    result[current_key] = '\n'.join(current_content).strip()
                current_key = "主要问题"
                current_content = []
            elif "💡" in line or "修改建议" in line:
                if current_key and current_content:
                    result[current_key] = '\n'.join(current_content).strip()
                current_key = "修改建议"
                current_content = []
            elif "✨" in line or "修改后文案" in line:
                if current_key and current_content:
                    result[current_key] = '\n'.join(current_content).strip()
                current_key = "修改后内容"
                current_content = []
            elif line.strip():
                clean = re.sub(r'^[\d\.\-\*]+\s*', '', line.strip())
                if clean:
                    current_content.append(clean)

        if current_key and current_content:
            result[current_key] = '\n'.join(current_content).strip()

        return result

    def update_record(self, token, app_token, table_id, record_id, analysis_data):
        """更新记录"""
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        fields = {
            "毒舌点评": str(analysis_data.get("毒舌点评", ""))[:1900],
            "修改建议": str(analysis_data.get("修改建议", ""))[:1900],
            "修改后内容": str(analysis_data.get("修改后内容", ""))[:1900],
        }

        response = requests.put(url, json={"fields": fields}, headers=headers)
        return response.json()

    def process_record(self, record_id, original_copy, content_type):
        """处理单条记录"""
        try:
            # 调用Claude分析
            response = self.call_claude(original_copy, content_type)
            parsed = self.parse_claude_response(response)

            # 更新飞书记录
            token = self.get_tenant_access_token()
            app_token, table_id = self.table_id.split('/')
            result = self.update_record(token, app_token, table_id, record_id, parsed)

            if result.get("code") == 0:
                print(f"✅ 记录 {record_id} 处理成功")
                return {"success": True}
            else:
                print(f"❌ 记录 {record_id} 更新失败：{result.get('msg')}")
                return {"success": False, "error": result.get('msg')}

        except Exception as e:
            print(f"❌ 处理记录 {record_id} 时出错：{str(e)}")
            return {"success": False, "error": str(e)}


# 创建全局处理器
handler = None

@app.before_request
def initialize():
    global handler
    if handler is None:
        handler = FeishuWebhookHandler()


@app.route('/')
def index():
    """首页"""
    return jsonify({
        "service": "草台香飞书自动检查服务",
        "status": "running",
        "version": "1.0"
    })


@app.route('/webhook/check', methods=['POST'])
def webhook_check():
    """接收飞书自动化webhook"""
    try:
        data = request.json

        # 获取记录信息
        record_id = data.get('record_id')
        original_copy = data.get('original_copy')
        content_type = data.get('content_type', '通用')

        # 如果没有record_id，使用原文案查找记录
        if not record_id and original_copy:
            print(f"\n📋 收到检查请求（通过原文案查找）：{original_copy[:50]}...")
            # 通过原文案查找记录ID
            try:
                token = handler.get_tenant_access_token()
                app_token, table_id = handler.table_id.split('/')

                # 获取所有记录
                url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                response = requests.get(url, headers=headers, params={"page_size": 100})
                records_data = response.json()

                if records_data.get("code") == 0:
                    records = records_data.get("data", {}).get("items", [])
                    # 查找匹配的记录
                    for record in records:
                        if record.get("fields", {}).get("原文案") == original_copy:
                            record_id = record.get("record_id")
                            break

                if not record_id:
                    return jsonify({
                        "success": False,
                        "error": "未找到匹配的记录"
                    }), 404

            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"查找记录失败：{str(e)}"
                }), 500

        elif not original_copy:
            return jsonify({
                "success": False,
                "error": "缺少原文案参数"
            }), 400

        print(f"\n📋 收到检查请求：记录ID={record_id}")

        # 异步处理（避免飞书超时）
        def async_process():
            handler.process_record(record_id, original_copy, content_type)

        import threading
        thread = threading.Thread(target=async_process)
        thread.start()

        return jsonify({
            "success": True,
            "message": "正在处理中，请稍候查看结果"
        })

    except Exception as e:
        print(f"❌ Webhook处理错误：{str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "service": "草台香飞书自动检查服务"
    })


# 后台定时检查任务
def background_checker():
    """后台定时检查表格"""
    import time
    print("🔄 后台检查任务启动...")

    while True:
        try:
            if handler is None:
                time.sleep(30)
                continue

            # 获取所有记录
            token = handler.get_tenant_access_token()
            app_token, table_id = handler.table_id.split('/')

            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers, params={"page_size": 100})
            records_data = response.json()

            if records_data.get("code") == 0:
                records = records_data.get("data", {}).get("items", [])

                for record in records:
                    record_id = record.get("record_id")
                    fields = record.get("fields", {})
                    original_copy = fields.get("原文案", "")

                    # 检查是否有原文案但没有结果
                    if original_copy and original_copy.strip():
                        has_result = fields.get("毒舌点评") or fields.get("修改建议")

                        if not has_result and record_id not in handler.checked_ids:
                            print(f"📋 发现未处理记录：{record_id}")
                            handler.process_record(record_id, original_copy, "通用")
                            handler.checked_ids.add(record_id)

        except Exception as e:
            print(f"❌ 后台检查错误：{str(e)}")

        time.sleep(30)  # 每30秒检查一次


# 启动后台任务
def start_background_task():
    """启动后台任务"""
    import threading
    thread = threading.Thread(target=background_checker, daemon=True)
    thread.start()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))

    # 启动后台任务
    start_background_task()

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

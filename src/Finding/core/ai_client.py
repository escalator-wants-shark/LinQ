import requests
import json


class AIClient:
    def __init__(self, model="qwen2.5:0.5b"):
        self.model = model
        # 尝试不同的端点
        self.base_urls = [
            "http://127.0.0.1:11434/api/generate",
            "http://127.0.0.1:11434/v1/chat/completions",
            "http://127.0.0.1:11434/api/chat"
        ]
        self.timeout = 300  # 减少到5分钟，避免手机卡死

    def chat(self, user_input, conversation_history, user_memory):
        """与AI对话 - 优化版本，考虑用户偏好和记忆"""
        print(f"开始处理用户输入: {user_input}")

        # 构建智能提示词，考虑用户偏好和对话历史
        prompt = self.build_chat_prompt(user_input, conversation_history, user_memory)

        # 方法1: 简单生成请求（最适合小模型）
        payload_simple = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        # 方法2: OpenAI兼容格式
        payload_openai = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个贴心的AI学习伙伴，根据用户的偏好和记忆进行个性化对话。"},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "max_tokens": 150  # 限制输出长度，避免手机卡顿
        }

        # 尝试不同的端点和格式
        endpoints_to_try = [
            (self.base_urls[0], payload_simple),  # 原始端点 + 简单格式
            (self.base_urls[1], payload_openai),  # OpenAI端点 + OpenAI格式
            (self.base_urls[2], payload_simple),  # 聊天端点 + 简单格式
        ]

        for url, payload in endpoints_to_try:
            try:
                print(f"尝试端点: {url}")
                # 简化日志输出，减少手机负担
                print(f"请求数据长度: {len(str(payload))}")

                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout
                )

                print(f"响应状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()

                    # 不同端点返回格式不同
                    if 'response' in data:
                        return data['response']
                    elif 'choices' in data and len(data['choices']) > 0:
                        return data['choices'][0]['message']['content']
                    elif 'message' in data:
                        return data['message']['content']
                    else:
                        # 返回前100字符用于调试，避免日志过长
                        return str(data)[:100]
                else:
                    print(f"错误响应: {response.text[:100]}")  # 简化错误日志

            except requests.exceptions.ConnectionError:
                print(f"无法连接到: {url}")
                continue
            except requests.exceptions.Timeout:
                print(f"端点超时: {url}")
                continue
            except Exception as e:
                print(f"端点 {url} 错误: {str(e)}")
                continue

        return "抱歉，我现在有点忙，请稍后再试。"

    def build_chat_prompt(self, user_input, conversation_history, user_memory):
        """构建简洁的对话prompt - 完全按照你提供的示例风格"""
        prompt_parts = []

        # 1. 用户偏好信息（如果有）
        if user_memory and user_memory != "目前还没有记录任何用户偏好信息。":
            prompt_parts.append(user_memory)

        # 2. 对话历史（保持简洁）
        if conversation_history:
            prompt_parts.append("当前对话历史：")
            # 只保留最近2轮对话，避免prompt过长
            recent_history = conversation_history[-2:] if len(conversation_history) > 2 else conversation_history
            for msg in recent_history:
                prompt_parts.append(f"用户: {msg.get('user', '')}")
                prompt_parts.append(f"AI: {msg.get('ai', '')}")

        # 3. 核心指令 - 完全按照你提供的格式
        prompt_parts.append("请根据以上已知信息，自然地与用户对话。如果信息相关，请在回复中体现出来。")

        # 4. 当前用户输入
        prompt_parts.append(f"用户: {user_input}")
        prompt_parts.append("AI: ")

        return "\n".join(prompt_parts)

    def generate_reminder(self, schedule_info, user_memory):
        """为行程生成智能提醒 - 优化版本，考虑用户偏好"""
        # 构建个性化的提醒提示词
        prompt = self.build_reminder_prompt(schedule_info, user_memory)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "max_tokens": 100  # 提醒信息限制长度
        }

        try:
            response = requests.post(
                self.base_urls[0],  # 使用第一个端点，最稳定
                json=payload,
                timeout=120  # 提醒功能超时缩短
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '该完成计划的任务了！加油！')
            else:
                return self.get_fallback_reminder(schedule_info)
        except Exception as e:
            print(f"生成提醒失败: {e}")
            return self.get_fallback_reminder(schedule_info)

    def build_reminder_prompt(self, schedule_info, user_memory):
        """构建简洁的行程提醒prompt"""
        prompt_parts = []

        # 1. 用户偏好信息（如果有）
        if user_memory and user_memory != "目前还没有记录任何用户偏好信息。":
            prompt_parts.append(user_memory)

        # 2. 行程信息
        prompt_parts.append(f"今日行程安排：{schedule_info}")

        # 3. 简洁指令
        prompt_parts.append("请根据以上信息生成一个简短的提醒，温暖地鼓励并监督用户：")

        return "\n".join(prompt_parts)

    def get_fallback_reminder(self, schedule_info):
        """备用提醒，当AI服务不可用时使用"""
        # 简单的规则化提醒
        if "学习" in schedule_info or "数学" in schedule_info or "英语" in schedule_info:
            return "学习时间到！坚持就是胜利，开始今天的知识探索吧！💪"
        elif "运动" in schedule_info or "健身" in schedule_info:
            return "运动时间到！身体健康最重要，动起来吧！🏃‍♂️"
        else:
            return "该完成计划的任务了！一步一个脚印，加油！✨"
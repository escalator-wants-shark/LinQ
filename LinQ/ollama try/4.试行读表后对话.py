import sqlite3
import requests


def get_user_preferences():
    """从数据库获取所有已知的用户偏好，并格式化成一段文本"""
    try:
        with sqlite3.connect('preferences.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, key_text, value_text FROM PREFERENCES")
            preferences = cursor.fetchall()

            if not preferences:
                return "目前还没有记录任何用户偏好信息。"

            # 将偏好信息格式化成一段自然的描述
            memory_text = "以下是你已知的关于用户的信息：\n"
            for category, key, value in preferences:
                if category == 'fact' and key == 'user_name':
                    memory_text += f"- 用户的名字叫{value}\n"
                elif category == 'fact' and key == 'ai_name':
                    memory_text += f"- 你（AI）的名字是{value}\n"
                elif category == 'like':
                    memory_text += f"- 用户{value}{key}\n"
                elif category == 'hobby':
                    memory_text += f"- 用户{value}{key}\n"
                else:
                    memory_text += f"- 用户的{key}是{value}\n"

            return memory_text

    except Exception as e:
        return f"读取记忆时出错：{e}"


def chat_with_ai(user_input, conversation_history):
    """与AI对话，并传入记忆和对话历史"""
    # 1. 获取用户偏好（记忆）
    user_memory = get_user_preferences()

    # 2. 构建系统提示词，告诉AI这些记忆
    system_prompt = f"""{user_memory}

请根据以上已知信息，自然地与用户对话。如果信息相关，请在回复中体现出来。
当前对话：
"""

    # 3. 将记忆、对话历史和当前输入组合成完整的提示
    full_prompt = system_prompt
    for msg in conversation_history[-4:]:  # 只保留最近4轮对话作为上下文
        full_prompt += f"用户: {msg['user']}\n"
        full_prompt += f"你: {msg['ai']}\n"

    full_prompt += f"用户: {user_input}\n你: "

    # 4. 调用Ollama
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2:7b",
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data['response']
    except Exception as e:
        return f"抱歉，我遇到了一些问题：{e}"


def main():
    print("=== 有记忆的AI对话 ===")
    print("输入'退出'或'quit'结束对话")
    print("-" * 30)

    # 存储当前会话的对话历史
    conversation_history = []

    while True:
        user_input = input("\n你说：").strip()

        if user_input.lower() in ['退出', 'quit', 'exit']:
            print("对话结束，再见！")
            break

        if not user_input:
            continue

        # 显示"思考中..."提示
        print("AI思考中...")

        # 获取AI回复
        ai_response = chat_with_ai(user_input, conversation_history)
        print(f"AI: {ai_response}")

        # 将本轮对话添加到历史中
        conversation_history.append({
            'user': user_input,
            'ai': ai_response
        })

        # 保持对话历史不超过一定长度（避免上下文过长）
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]


if __name__ == "__main__":
    main()
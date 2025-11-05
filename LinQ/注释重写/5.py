import sqlite3
import requests # 这是没有用过的不熟悉的库！


def get_user_preferences():
    """从数据库获取所有已知的用户偏好，并格式化成一段文本"""
    try:
        with sqlite3.connect('preferences.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, key_text, value_text FROM PREFERENCES")
            preferences = cursor.fetchall() # 和上一段代码一样，应该是读取内容的函数，没用过，查一下，可能会得到列表数据类型

            if not preferences: # 这句话啥意思……？
                return "目前还没有记录任何用户偏好信息。"

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
                 # 感觉这里像是再把数据库里面记录的偏好信息全部格式化让AI在对话前看一遍的意思吗？？
            return memory_text

    except Exception as e:
        return f"读取记忆时出错：{e}"


def save_conversation(user_input, ai_response):
    """将单轮对话保存到数据库"""
    try:
        with sqlite3.connect('memory.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO MEMORY (user_input, AI_output) VALUES (?, ?)",
                (user_input, ai_response)
            )
        return True
    except Exception as e:
        print(f"保存对话时出错：{e}")
        return False # 这一块的操作很熟悉了呀，都能够看得懂


def chat_with_ai(user_input, conversation_history):
    """与AI对话，并传入记忆和对话历史"""
    # 1. 获取用户偏好（长期记忆）
    user_memory = get_user_preferences()

    # 2. 构建系统提示词
    system_prompt = f"""{user_memory}

请根据以上已知信息，自然地与用户对话。如果信息相关，请在回复中体现出来。
当前对话历史：
""" # 这个操作以前没有用过，所有AI都会这么做吗？？？？？？

    # 3. 组合记忆、历史和新输入
    full_prompt = system_prompt
    for msg in conversation_history[-4:]: # 保留最近4轮作为上下文
        # 吼!我就说嘛，不是啥都记得，只记得最近的四点东西……嗯……
        full_prompt += f"用户：{msg['user']}\n"
        full_prompt += f"你：{msg['ai']}\n" # 这种格式化是什么意思……额，咋区分俩人的信息的，而且，数据表里面不是大部分都只记录了我的东西吗？

    full_prompt += f"用户：{user_input}\n你："

    # 4.调用Ollama
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2:7b",
        "prompt": full_prompt, # 原来用在这里吗？那这种prompt具体在这种代码里……额……这代码是谁发明的（？思考思考
        "stream": False
    }

    try:
        response = requests.post(url, json=payload) # requests在这里用到了，果然是请求关于http的，但是要查查学学
        response.raise_for_status() # 这啥函数（？
        data = response.json() # 数据改成json格式吗？
        return  data['response'] # 真要看看一些关于json的规则了，就好像调用数列索引似的
    except Exception as e:
        return f"抱歉，我遇到了一些问题：{e}"


def main():
    print("===有记忆的AI对话 (自动保存版) ===")
    print("输出'退出'或'quit'结束对话")
    print("-" * 40)

    # 存储当前会话的对话历史（短期记忆）
    conversation_history = []

    while True: # 这个语句的用法，还不太明白在哪里会用到之类的
        user_input = input("\n你说：").strip() # 这个strip也忘了，查查

        if user_input.lower() in ['退出', 'quit', 'exit']: # 我咋觉得这步写反了嘞？
            print("对话结束，再见！")
            break

        if not  user_input:
            continue # 这啥？

        print("AI思考中...")

        # 获取AI回复（这个过程包含了读取长期记忆）
        ai_response = chat_with_ai(user_input, conversation_history)
        print(f"AI:{ai_response}")

        # ！！！核心：将本轮对话保存到数据库（持久化）
        if save_conversation(user_input, ai_response):
            print("(对话已自动保存)")
        else:
            print("(对话保存失败)")

        # 将本轮对话添加到本次会话的历史中（短期记忆）
        conversation_history.append({
            'user':user_input,
            'ai':ai_response
        }) # 这个和偏好有关系吗，所以每次是偏好和前四轮历史对话都读吗？

        # 保持对话历史不超过一定长度
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
            # 这啥意思，那我输入很长的时候几乎记不了几个字啊……是不是这样，去测一下……


if __name__ == "__main__":
    main()
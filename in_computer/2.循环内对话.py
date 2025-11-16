import sqlite3
import requests



# 主循环
def main():
    print("对话开始。输入'再见'结束程序。")

    while True:
        # 获取用户输入
        user_input = input("\n你说：").strip()

        # 检查退出条件
        if user_input.lower() in ['再见', 'bye', 'exit', 'quit']:
            print("再见啦！")
            break

        # 调用Ollama API获取AI回复
        ai_response = get_ai_response(user_input)
        print(f"AI: {ai_response}")

        # 将对话存入数据库
        save_conversation(user_input, ai_response)


# 调用Ollama的函数
def get_ai_response(user_message):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2:7b",
        "prompt": user_message,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()
        return data['response']
    except Exception as e:
        return f"出错了：{e}"


# 存入数据库的函数
def save_conversation(user_msg, ai_msg):
    try:
        with sqlite3.connect('memory.db', timeout=10, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO MEMORY (user_input, AI_output) VALUES (?, ?)",
                (user_msg, ai_msg)
            )
        print("对话已保存！") # 可选：需要时再打开打印
    except Exception as e:
        print(f"保存对话时出错：{e}")

# 程序入口
if __name__ == "__main__":
    main()
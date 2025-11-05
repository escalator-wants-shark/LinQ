import requests
import sqlite3

# 打开数据库，进行连接
memory = sqlite3.connect('memory.db')
c = memory.cursor()

url = "http://127.0.0.1:11434/api/generate"
user_message = input("请输入你的问题：")
payload = {
    "model": "qwen2:7b",
    "prompt": user_message,
    "stream": False
}

response = requests.post(url, json=payload)
print(response.json())

if response.status_code == 200:
    data = response.json()
    ai_response = data['response']
    print("AI回复：", ai_response)
    # 保存对话记录
    c.execute("INSERT INTO MEMORY (user_input, AI_output) VALUES(?, ?)",
              (user_message, ai_response))
    memory.commit()
    memory.close()
else:
    print("请求失败，错误代码：", response.status_code)
    print(response.text)


import sqlite3

# 创建一张表
memory = sqlite3.connect('memory.db')
print("数据库打开成功")
c = memory.cursor()
c.execute('''CREATE TABLE MEMORY
        (ID INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input      TEXT    NOT NULL,
        AI_output       TEXT    NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);''')
print("数据表创建成功")
memory.commit()
memory.close()
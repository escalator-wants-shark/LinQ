import sqlite3

preferences = sqlite3.connect('preferences.db')
print("数据库打开成功")
c = preferences.cursor()
c.execute('''CREATE TABLE PREFERENCES
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            key_text TEXT NOT NULL,
            value_text TEXT,
            source_ID INTEGER,
            FOREIGN KEY (source_ID) REFERENCES MEMORY (ID)
            CONSTRAINT uc_content UNIQUE (key_text, value_text)
            );''')
import sqlite3
import json

# 1. 连接到你的.db文件（请将'your_database.db'替换为你的实际文件路径）
conn = sqlite3.connect('memory.db')
# 为了获取字段名，将row_factory设置为sqlite3.Row
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 2. 执行SQL查询，提取数据（请将'your_table_name'替换为你的实际表名）
cursor.execute("SELECT * FROM MEMORY")
rows = cursor.fetchall()

# 3. 将数据转换为列表字典形式，便于转为JSON
# 使用sqlite3.Row后，可以直接将每一行转换为字典
data = [dict(row) for row in rows]

# 4. 将数据写入JSON文件（'output.json'是你要生成的JSON文件名）
with open('memory_1.json', 'w', encoding='utf-8') as f:
    # indent参数用于美化输出，使JSON文件更易读
    json.dump(data, f, indent=4, ensure_ascii=False) # ensure_ascii=False确保中文正常显示

# 5. 关闭连接
cursor.close()
conn.close()

print("数据已成功从.db文件转换到memory_1.json")
import sqlite3
import json

# 1. 加载规则
with open('rules.json', 'r', encoding='utf-8') as f:
    rules = json.load(f)

print("规则加载成功！")


# 2. 连接数据库，获取所有对话记录
def get_all_conversations():
    """获取所有历史对话"""
    with sqlite3.connect('memory.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ID, user_input FROM MEMORY")
        return cursor.fetchall()


# 3. 插入偏好记录
def insert_preference(category, key_text, value_text, source_id):
    """向偏好表插入一条新记录"""
    try:
        with sqlite3.connect('preferences.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO PREFERENCES (category, key_text, value_text, source_ID) VALUES (?, ?, ?, ?)",
                (category, key_text, value_text, source_id)
            )
        return True
    except Exception as e:
        print(f"插入数据时出错: {e}")
        return False


# 4. 核心处理逻辑
def main():
    all_conversations = get_all_conversations()
    print(f"共读取到 {len(all_conversations)} 条对话记录。")

    new_preferences_count = 0

    for conv_id, user_input in all_conversations:
        for category, keywords in rules.items():
            for keyword in keywords:
                if keyword in user_input:
                    print(f"在对话ID {conv_id} 中发现关键词 '{keyword}', 类别: '{category}'")
                    print(f"完整对话: {user_input}")

                    try:
                        keyword_index = user_input.index(keyword)
                        content_after_keyword = user_input[keyword_index + len(keyword):].strip()
                        extracted_content = content_after_keyword.split(' ')[0] if content_after_keyword else ""

                        if extracted_content:
                            if category == 'fact' and ('名字' in keyword or '叫我' in keyword):
                                key_to_store = 'user_name'
                                value_to_store = extracted_content
                            else:
                                key_to_store = extracted_content
                                value_to_store = keyword

                            # 使用专门的函数插入数据
                            if insert_preference(category, key_to_store, value_to_store, conv_id):
                                new_preferences_count += 1
                                print(f"--> 已存储: {category} | {key_to_store} | {value_to_store}")
                            else:
                                print("--> 存储失败")

                    except Exception as e:
                        print(f"处理句子时出错: {user_input}, 错误: {e}")
                    break

    print(f"挖掘完成！共新增了 {new_preferences_count} 条偏好记录到数据库。")


if __name__ == "__main__":
    main()
import sqlite3
import json

# 打开文件的语句，文件名，只读格式，……，可识别中文的符号码（？utf-8),给文件命名为一个变量，加载文件内容存为变量
with open('rules.json', 'r', encoding='utf-8') as f:
    rules = json.load(f) # 注意这里不在函数里面，规则已经被加载出来了

def get_all_conversation():
    """获取所有历史对话"""
    with sqlite3.connect('memory.db') as conn: # 连接打开数据库的表
        cursor = conn.cursor() # 不记得是什么函数什么意思，但能感觉到用法……
        cursor.execute("SELECT ID, userinput FROM MEMORY") # 执行：选择特定列
        return cursor.fetchall() # 这是什么函数？


def insert_preference(category, key_text, value_text, source_id):
    """向偏好表插入一条新记录"""
    try: # 这里用这个，逻辑和if差不多，可是试错，看看报什么错，而且程序可以继续运行（这种写法也快要学会了吧……
        with sqlite3.connect('preferences.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO PREFERENCES (category, key_text, value_text, source_ID) VALUES(?, ?, ?, ?)",
                (category, key_text, value_text, source_id)
            ) # 这个可以学学，数据库的插入代码执行语句
        return True
    except Exception as e:
        print(f"插入数据时出错：{e}") # 格式化输出语句，只是不太明白为什么一直会有警告……以前都不注意警告，以后要不要把这些搞懂呢？
        return False

# 重点解决区……
def main():
    all_conversations = get_all_conversation()
    print(f"共读取到 {len(all_conversations)} 条对话记录。") # 所以之前获取到的数据类型是数列吗？？数组？？列表？

    new_preferences_count = 0 # 做一个数目记录。

    # 问题就主要是这里，一大堆 for 循环嵌套……好像在找关键词……
    # 这几个变量名好像都是新起的，all_conversations是已经提取到的，有可能是列表（？
    for conv_id, user_input in all_conversations: # 循环遍历每一个用户输入及其编号
        for category, keywords in rules.items(): # .items()不知道什么意思，可能是json文件里面的东西……
            # 遍历json规则文件里的每一份“类型”及“对应关键词们”
            '''那记住回去看看json文件一般有什么格式规则……'''
            for keyword in keywords: # 就是说，keywords是列表，keyword是列表里面的元素咯，遍历列表里的所有关键词元素，
                if keyword in user_input: # 看看上面遍历的东西在不在用户输入里面
                    print(f"在对话ID {conv_id} 中发现关键词 '{keyword}', 类别：'{category}'") # 这里就用到上面新命名的变量了吧
                    print(f"完整对话：{user_input}") # 所以这类变量可以不单独命名，直接出现在上面的循环语句里面吗？这种我不常用因为以前没写过

                    try:
                        keyword_index = user_input.index(keyword) # 这是啥？是不是把输入内容看成字符数组之类的，找到关键词所在的索引位置……
                        content_after_keyword = user_input[keyword_index + len(keyword):].strip()
                        # 这里只取和关键词一样长的内容作为需要提取的内容吗，一会儿看看数据库是不是
                        extracted_content = content_after_keyword.split(' ')[0] if content_after_keyword else ""
                        # 这个像数据清洗，分词，不过……不太懂确实

                        if extracted_content:
                            if category == 'fact' and ('名字' in keyword or '叫我' in keyword):
                                key_to_store = 'user_name'
                                value_to_store = extracted_content # 名字还作为单独的存储？这样有用吗……要再测测
                            else:
                                key_to_store = extracted_content
                                value_to_store = keyword # 这里就是存储关键词及其相关内容了
                                # 其实这块儿存什么，怎么存，怎么找，就是以后改进的一个方向。不过需要学习一些别人的做法，或者官方方法？

                            # 使用专门的函数插入数据
                            if insert_preference(category, key_to_store, value_to_store, conv_id):
                                new_preferences_count += 1
                                print(f"--> 已存储：{category} | {key_to_store} | {value_to_store}")
                            else:
                                print("--> 存储失败")

                    except Exception as e:
                        print(f"处理句子时出错：{user_input}, 错误：{e}")
                    break

    print(f"挖掘完成！共新增了 {new_preferences_count} 条偏好记录到数据库。")

if __name__ == "__main__": # 这个东西应该是启动脚本的意思……一会儿可以查查问问，很少写脚本（？
    main()

# 现在主要问题是，每操作一次，先前已有的记录都会再被重复记录一次
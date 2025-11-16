import sqlite3
import os
import json
from datetime import datetime, time


class DatabaseManager:
    def __init__(self, data_dir):
        # 确保数据目录存在
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
                print(f"创建数据目录: {data_dir}")  # 调试信息
            except Exception as e:
                print(f"创建数据目录失败: {e}")

        self.data_dir = data_dir
        self.memory_db_path = os.path.join(data_dir, 'memory.db')
        self.preferences_db_path = os.path.join(data_dir, 'preferences.db')
        self.schedule_db_path = os.path.join(data_dir, 'schedule.db')

        # 初始化数据库
        self.init_databases()

        # 加载规则
        self.rules = self.load_rules()

    def load_rules(self):
        """加载偏好挖掘规则"""
        default_rules = {
            "fact": ["我叫", "我是", "我的名字是", "你可以叫我", "我学", "专业是"],
            "like": ["喜欢", "爱", "讨厌", "不喜欢", "受不了", "挺喜欢"],
            "hobby": ["经常", "习惯", "总是", "每次", "一般会"]
        }

        rules_path = os.path.join(self.data_dir, 'rules.json')
        try:
            if os.path.exists(rules_path):
                with open(rules_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 如果文件不存在，创建默认规则文件
                with open(rules_path, 'w', encoding='utf-8') as f:
                    json.dump(default_rules, f, ensure_ascii=False, indent=2)
                print(f"创建默认规则文件: {rules_path}")  # 调试信息
                return default_rules
        except Exception as e:
            print(f"加载规则文件失败，使用默认规则: {e}")  # 调试信息
            return default_rules

    def init_databases(self):
        """初始化所有数据库表 - 增强错误处理"""
        databases = [
            (self.memory_db_path, '''
                CREATE TABLE IF NOT EXISTS MEMORY
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                AI_output TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)
            '''),
            (self.preferences_db_path, '''
                CREATE TABLE IF NOT EXISTS PREFERENCES
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key_text TEXT NOT NULL,
                value_text TEXT,
                source_ID INTEGER,
                CONSTRAINT uc_content UNIQUE (key_text, value_text))
            '''),
            (self.schedule_db_path, '''
                CREATE TABLE IF NOT EXISTS SCHEDULE
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TEXT NOT NULL,
                event_name TEXT NOT NULL,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP)
            ''')
        ]

        for db_path, create_sql in databases:
            try:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute(create_sql)
                conn.commit()
                conn.close()
                print(f"初始化数据库表成功: {db_path}")  # 调试信息
            except Exception as e:
                print(f"初始化数据库表失败 {db_path}: {e}")  # 调试信息

    def mine_new_preferences(self):
        """挖掘新的用户偏好"""
        try:
            # 只需要打开memory数据库，获取所有对话记录
            conn_memory = sqlite3.connect(self.memory_db_path)
            cursor_memory = conn_memory.cursor()
            cursor_memory.execute("SELECT ID, user_input FROM MEMORY")
            all_conversations = cursor_memory.fetchall()
            conn_memory.close()

            if not all_conversations:
                return 0, "没有发现对话记录可供分析"

            new_preferences_count = 0

            for conv_id, user_input in all_conversations:
                for category, keywords in self.rules.items():
                    for keyword in keywords:
                        if keyword in user_input:
                            try:
                                keyword_index = user_input.index(keyword)
                                content_after_keyword = user_input[keyword_index + len(keyword):].strip()

                                # 提取关键词后的内容（取第一个短语）
                                if content_after_keyword:
                                    # 简单的分割，取第一个有意义的片段
                                    extracted_content = content_after_keyword.split('。')[0].split('，')[0].split(' ')[0]
                                    extracted_content = extracted_content[:20]  # 限制长度

                                    if extracted_content and len(extracted_content) > 0:
                                        if category == 'fact' and ('名字' in keyword or '叫我' in keyword):
                                            key_to_store = 'user_name'
                                            value_to_store = extracted_content
                                        else:
                                            key_to_store = extracted_content
                                            value_to_store = keyword

                                        # 插入偏好记录，利用唯一约束避免重复
                                        if self.insert_preference(category, key_to_store, value_to_store, conv_id):
                                            new_preferences_count += 1

                            except Exception as e:
                                print(f"处理句子时出错: {user_input}, 错误: {e}")
                            break  # 一个对话只匹配一个关键词

            if new_preferences_count > 0:
                return new_preferences_count, f"成功挖掘到 {new_preferences_count} 条新偏好！"
            else:
                return 0, "没有发现新的用户偏好"

        except Exception as e:
            return 0, f"挖掘偏好时出错: {str(e)}"

    def insert_preference(self, category, key_text, value_text, source_id):
        """向偏好表插入一条新记录（内部方法）"""
        try:
            conn = sqlite3.connect(self.preferences_db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO PREFERENCES (category, key_text, value_text, source_ID) VALUES (?, ?, ?, ?)",
                (category, key_text, value_text, source_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"插入偏好数据时出错: {e}")
            return False

    def get_user_preferences(self):
        """获取用户偏好"""
        try:
            conn = sqlite3.connect(self.preferences_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT category, key_text, value_text FROM PREFERENCES")
            preferences = cursor.fetchall()

            if not preferences:
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

            return memory_text
        except Exception as e:
            print(f"获取用户偏好时出错: {e}")  # 调试信息
            return "目前还没有记录任何用户偏好信息。"

    def save_conversation(self, user_input, ai_response):
        """保存对话记录"""
        try:
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO MEMORY (user_input, AI_output) VALUES (?, ?)",
                (user_input, ai_response)
            )
            conn.commit()
            conn.close()
            print(f"对话保存成功: {user_input[:20]}...")  # 调试信息
            return True
        except Exception as e:
            print(f"保存对话时出错：{e}")  # 调试信息
            return False

    def add_schedule(self, event_time, event_name):
        """添加新行程"""
        try:
            conn = sqlite3.connect(self.schedule_db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO SCHEDULE (event_time, event_name) VALUES (?, ?)",
                (event_time, event_name)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加行程时出错：{e}")
            return False

    def get_upcoming_schedules(self, hours=24):
        """获取即将到来的行程 - 简化版本，返回所有行程"""
        try:
            conn = sqlite3.connect(self.schedule_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT event_time, event_name FROM SCHEDULE ORDER BY event_time")
            schedules = cursor.fetchall()
            conn.close()
            return schedules
        except Exception as e:
            print(f"获取行程时出错：{e}")
            return []

    def get_all_data(self):
        """获取所有数据用于调试查看"""
        try:
            # 获取记忆
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT user_input, AI_output, timestamp FROM MEMORY ORDER BY timestamp DESC LIMIT 10")
            memories = cursor.fetchall()
            conn.close()

            # 获取偏好
            conn = sqlite3.connect(self.preferences_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT category, key_text, value_text FROM PREFERENCES")
            preferences = cursor.fetchall()
            conn.close()

            # 获取行程
            conn = sqlite3.connect(self.schedule_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT ID, event_time, event_name, created_time FROM SCHEDULE ORDER BY event_time")
            schedules = cursor.fetchall()
            conn.close()

            return {
                'memories': memories,
                'preferences': preferences,
                'schedules': schedules
            }
        except Exception as e:
            print(f"获取所有数据时出错: {e}")  # 调试信息
            return {'error': str(e)}

    def check_table_exists(self, db_path, table_name):
        """检查表是否存在"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            print(f"检查表存在性时出错: {e}")
            return False

    def import_from_json(self, db_type, data):
        """从JSON数据导入到指定数据库 - 修复版本"""
        try:
            count = 0

            if db_type == "memory":
                # 导入对话记忆
                for item in data:
                    if isinstance(item, dict) and 'user_input' in item and 'ai_output' in item:
                        success = self.save_conversation(item['user_input'], item['ai_output'])
                        if success:
                            count += 1
                    elif isinstance(item, dict) and 'user_input' in item and 'AI_output' in item:
                        # 兼容不同大小写的字段名
                        success = self.save_conversation(item['user_input'], item['AI_output'])
                        if success:
                            count += 1
                    elif isinstance(item, (list, tuple)) and len(item) >= 2:
                        success = self.save_conversation(str(item[0]), str(item[1]))
                        if success:
                            count += 1

            elif db_type == "preferences":
                # 导入用户偏好
                for item in data:
                    if isinstance(item, dict) and all(key in item for key in ['category', 'key_text', 'value_text']):
                        # 使用现有方法插入偏好
                        source_id = item.get('source_ID', None)
                        success = self.insert_preference(
                            item['category'],
                            item['key_text'],
                            item['value_text'],
                            source_id
                        )
                        if success:
                            count += 1
                    elif isinstance(item, (list, tuple)) and len(item) >= 3:
                        source_id = item[3] if len(item) > 3 else None
                        success = self.insert_preference(
                            str(item[0]), str(item[1]), str(item[2]), source_id
                        )
                        if success:
                            count += 1

            elif db_type == "schedule":
                # 导入行程安排
                for item in data:
                    if isinstance(item, dict) and all(key in item for key in ['event_time', 'event_name']):
                        success = self.add_schedule(item['event_time'], item['event_name'])
                        if success:
                            count += 1
                    elif isinstance(item, dict) and 'event_time' in item and 'event_name' in item:
                        # 兼容不同大小写的字段名
                        success = self.add_schedule(item['event_time'], item['event_name'])
                        if success:
                            count += 1
                    elif isinstance(item, (list, tuple)) and len(item) >= 2:
                        success = self.add_schedule(str(item[0]), str(item[1]))
                        if success:
                            count += 1
            else:
                return {'success': False, 'error': f'未知的数据库类型: {db_type}'}

            return {'success': True, 'count': count}

        except Exception as e:
            print(f"导入数据时出错: {e}")  # 调试信息
            return {'success': False, 'error': str(e)}

    def export_to_json(self, db_type, file_path):
        """将指定数据库导出为JSON文件"""
        try:
            data = []

            if db_type == "memory":
                # 导出对话记忆
                conn = sqlite3.connect(self.memory_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT user_input, AI_output, timestamp FROM MEMORY")
                rows = cursor.fetchall()
                conn.close()

                for row in rows:
                    data.append({
                        'user_input': row[0],
                        'ai_output': row[1],
                        'timestamp': row[2]
                    })

            elif db_type == "preferences":
                # 导出用户偏好
                conn = sqlite3.connect(self.preferences_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT category, key_text, value_text, source_ID FROM PREFERENCES")
                rows = cursor.fetchall()
                conn.close()

                for row in rows:
                    data.append({
                        'category': row[0],
                        'key_text': row[1],
                        'value_text': row[2],
                        'source_ID': row[3]
                    })

            elif db_type == "schedule":
                # 导出行程安排
                conn = sqlite3.connect(self.schedule_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT event_time, event_name, created_time FROM SCHEDULE")
                rows = cursor.fetchall()
                conn.close()

                for row in rows:
                    data.append({
                        'event_time': row[0],
                        'event_name': row[1],
                        'created_time': row[2]
                    })
            else:
                return {'success': False, 'error': f'未知的数据库类型: {db_type}'}

            # 写入JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return {'success': True, 'count': len(data)}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # 辅助方法：获取所有数据（用于调试）
    def get_all_data_for_export(self, db_type):
        """获取指定数据库的所有数据（用于导出）"""
        if db_type == "memory":
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM MEMORY")
            data = cursor.fetchall()
            conn.close()
            return data

        elif db_type == "preferences":
            conn = sqlite3.connect(self.preferences_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM PREFERENCES")
            data = cursor.fetchall()
            conn.close()
            return data

        elif db_type == "schedule":
            conn = sqlite3.connect(self.schedule_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM SCHEDULE")
            data = cursor.fetchall()
            conn.close()
            return data

        else:
            return []

    def delete_schedule(self, schedule_id):
        """根据ID删除行程"""
        try:
            conn = sqlite3.connect(self.schedule_db_path)
            cursor = conn.cursor()

            # 先检查行程是否存在
            cursor.execute("SELECT event_time, event_name FROM SCHEDULE WHERE ID = ?", (schedule_id,))
            schedule = cursor.fetchone()

            if not schedule:
                return False, "行程不存在"

            # 删除行程
            cursor.execute("DELETE FROM SCHEDULE WHERE ID = ?", (schedule_id,))
            conn.commit()
            conn.close()

            return True, f"已删除行程: {schedule[0]} - {schedule[1]}"

        except Exception as e:
            return False, f"删除失败: {str(e)}"

    def get_conversations(self):
        """获取所有对话记录 - 确保返回一致的字段"""
        try:
            self.cursor.execute("SELECT user_input, ai_response FROM conversations ORDER BY timestamp DESC LIMIT 50")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取对话记录错误: {e}")
            return []

    def get_all_schedules(self):
        """获取所有行程 - 确保返回一致的字段"""
        try:
            self.cursor.execute("SELECT schedule_time, event FROM schedules ORDER BY schedule_time")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取行程错误: {e}")
            return []



"""
Talk to AI locally in my phone for the first time to help life and learning.
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import threading
import os
from datetime import datetime
from pathlib import Path
import json

# 导入我们之前创建的核心模块
from core.database import DatabaseManager
from core.ai_client import AIClient


class Talk_in_App_v01(toga.App):
    def startup(self):
        """Construct and show the Toga application."""
        self.icon = "ai_companion_icon"

        # 获取应用的专用数据目录
        data_dir = Path(self.paths.data) / "databases"
        data_dir.mkdir(parents=True, exist_ok=True)  # 确保目录存在

        # 初始化核心组件
        self.data_dir = self.paths.data
        self.db = DatabaseManager(self.data_dir)
        self.ai_client = AIClient()

        # 确保规则文件存在（这会触发DatabaseManager创建默认规则文件）
        rules_path = os.path.join(self.data_dir, 'rules.json')
        if not os.path.exists(rules_path):
            self.db.load_rules()  # 这会创建默认规则文件

        # 对话状态
        self.conversation_history = []

        # 创建主窗口
        self.main_window = toga.MainWindow(title=self.formal_name)

        # 创建界面组件
        self.create_ui()

        # 显示窗口
        self.main_window.show()

        # 启动时显示欢迎信息
        self.show_welcome_message()

        # 导入导出状态管理
        self.waiting_for_input = None  # 当前等待的输入类型
        self.selected_db_type = None  # 选择的数据库类型
        self.import_export_state = None  # 导入导出状态


        # 设置公共目录路径
        # 使用Download目录下的子目录，避免文件混乱
        self.public_base_dir = "/storage/emulated/0/Download/ai_companion/"
        self.import_dir = os.path.join(self.public_base_dir, "import")
        self.export_dir = os.path.join(self.public_base_dir, "export")

        # 自动创建这些目录（如果不存在）
        try:
            os.makedirs(self.import_dir, exist_ok=True)
            os.makedirs(self.export_dir, exist_ok=True)
            print(f"✅ 公共目录创建成功:")
            print(f"   导入目录: {self.import_dir}")
            print(f"   导出目录: {self.export_dir}")
        except Exception as e:
            print(f"❌ 创建公共目录失败: {e}")
            # 如果失败，回退到应用私有目录
            self.import_dir = os.path.join(self.data_dir, "import")
            self.export_dir = os.path.join(self.data_dir, "export")
            os.makedirs(self.import_dir, exist_ok=True)
            os.makedirs(self.export_dir, exist_ok=True)

        # 修正：使用 resources 目录而不是 assets
        # 如果使用 Toga 的标准资源路径
        self.resources_dir = self.paths.resources if hasattr(self.paths, 'resources') else os.path.join(self.paths.app,
                                                                                                        'resources')
        self.predefined_data_dir = os.path.join(self.resources_dir, 'predefined_data')

        print(f"Resources目录: {self.resources_dir}")
        print(f"预设数据目录: {self.predefined_data_dir}")

        # 检查目录是否存在
        if os.path.exists(self.resources_dir):
            print("✅ Resources目录存在")
            if os.path.exists(self.predefined_data_dir):
                print("✅ 预设数据目录存在")
                files = os.listdir(self.predefined_data_dir)
                print(f"目录中的文件: {files}")
            else:
                print("❌ 预设数据目录不存在，将创建")
                os.makedirs(self.predefined_data_dir, exist_ok=True)
        else:
            print("❌ Resources目录不存在")

        # 同时检查其他可能的路径
        possible_paths = [
            self.paths.app,  # 应用主目录
            os.path.join(self.paths.app, 'resources'),
            os.path.join(self.paths.app, 'assets'),
            os.path.join(self.paths.app, 'src', 'resources'),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                print(f"📁 存在的路径: {path}")
                if os.path.isdir(path):
                    files = os.listdir(path)
                    print(f"  包含的文件: {files}")

        # 详细的路径调试信息
        print("=== 路径调试信息 ===")
        print(f"应用路径 (self.paths.app): {self.paths.app}")
        print(f"数据路径 (self.paths.data): {self.paths.data}")

        # 检查所有可能的资源路径
        check_paths = [
            ("应用主目录", self.paths.app),
            ("Resources目录", os.path.join(self.paths.app, 'resources')),
            ("Assets目录", os.path.join(self.paths.app, 'assets')),
            ("src/resources", os.path.join(self.paths.app, 'src', 'resources')),
        ]

        for name, path in check_paths:
            exists = os.path.exists(path)
            print(f"{name}: {path} - {'✅ 存在' if exists else '❌ 不存在'}")
            if exists and os.path.isdir(path):
                try:
                    files = os.listdir(path)
                    print(f"  包含: {files}")
                except:
                    print("  无法列出文件")

        print("==================")

    def create_ui(self):
        """创建用户界面"""
        # 聊天显示区域 - 显示对话历史
        self.chat_display = toga.MultilineTextInput(
            readonly=True,
            style=Pack(flex=1, padding=5)
        )

        # 消息输入区域
        message_label = toga.Label('输入消息:', style=Pack(padding=5))

        self.message_input = toga.TextInput(
            placeholder='在这里输入你想说的话...',
            style=Pack(flex=1, padding=5)
        )

        # 将发送按钮保存为实例变量，以便后续启用/禁用
        self.send_button = toga.Button(
            '发送',
            on_press=self.send_message,
            style=Pack(padding=5, width=80)
        )

        # 行程管理区域
        schedule_label = toga.Label('添加行程:', style=Pack(padding=5))

        time_label = toga.Label('时间:', style=Pack(padding=5, width=60))
        self.schedule_time_input = toga.TextInput(
            placeholder='14:30',
            style=Pack(flex=1, padding=5)
        )

        event_label = toga.Label('事件:', style=Pack(padding=5, width=60))
        self.schedule_event_input = toga.TextInput(
            placeholder='学习数学',
            style=Pack(flex=1, padding=5)
        )

        add_schedule_button = toga.Button(
            '添加行程',
            on_press=self.add_schedule,
            style=Pack(padding=5)
        )

        # 功能按钮区域
        view_data_button = toga.Button(
            '查看数据',
            on_press=self.view_data,
            style=Pack(flex=1, padding=5)
        )

        check_schedules_button = toga.Button(
            '检查行程',
            on_press=self.check_upcoming_schedules,
            style=Pack(flex=1, padding=5)
        )

        clear_chat_button = toga.Button(
            '清空对话',
            on_press=self.clear_chat,
            style=Pack(flex=1, padding=5)
        )

        # 添加"挖掘偏好"按钮
        mine_preferences_button = toga.Button(
            '挖掘偏好',
            on_press=self.mine_preferences,
            style=Pack(flex=1, padding=5)
        )

        # 新增的导入导出按钮
        import_data_button = toga.Button(
            '导入数据',
            on_press=self.import_data,
            style=Pack(flex=1, padding=5)
        )

        export_data_button = toga.Button(
            '导出数据',
            on_press=self.export_data,
            style=Pack(flex=1, padding=5)
        )

        # 添加文件管理帮助按钮
        file_help_button = toga.Button(
            '文件位置',
            on_press=self.show_file_locations,
            style=Pack(flex=1, padding=5)
        )

        # 在功能按钮区域添加删除行程按钮
        delete_schedule_button = toga.Button(
            '删除行程',
            on_press=self.delete_schedule,
            style=Pack(flex=1, padding=5)
        )

        # 布局组织
        # 消息输入行
        input_box = toga.Box(
            children=[self.message_input, self.send_button],
            style=Pack(direction=ROW, padding=5)
        )

        # 时间输入行
        time_box = toga.Box(
            children=[time_label, self.schedule_time_input],
            style=Pack(direction=ROW, padding=5)
        )

        # 事件输入行
        event_box = toga.Box(
            children=[event_label, self.schedule_event_input],
            style=Pack(direction=ROW, padding=5)
        )

        # 行程管理区域
        schedule_box = toga.Box(
            children=[time_box, event_box, add_schedule_button],
            style=Pack(direction=COLUMN, padding=10)
        )

        # 功能按钮区域
        button_box_row1 = toga.Box(
            children=[
                view_data_button,
                check_schedules_button,
                mine_preferences_button,
                clear_chat_button
            ],
            style=Pack(direction=ROW, padding=5)
        )

        button_box_row2 = toga.Box(
            children=[
                import_data_button,
                export_data_button,
                file_help_button,
                delete_schedule_button
            ],
            style=Pack(direction=ROW, padding=5)
        )

        # 主容器 - 将所有组件垂直排列
        main_box = toga.Box(
            children=[
                self.chat_display,
                message_label,
                input_box,
                schedule_label,
                schedule_box,
                button_box_row1,
                button_box_row2
            ],
            style=Pack(direction=COLUMN, flex=1)
        )

        self.main_window.content = main_box

    def show_welcome_message(self):
        """显示欢迎信息"""
        welcome_msg = """=== 欢迎! ===

请确保已在Termux中运行: ollama serve

现在开始对话吧！"""
        self.chat_display.value = welcome_msg + "\n\n"

    def send_message(self, widget):
        """发送消息处理"""
        user_input = self.message_input.value.strip()
        if not user_input:
            self.show_message("提示", "请输入消息内容")
            return

        # 禁用发送按钮避免重复发送
        self.send_button.enabled = False

        # 清空输入框（只清空一次）
        self.message_input.value = ''

        # 在界面显示用户消息
        self.append_to_chat("你", user_input)

        # 检查是否处于导入导出流程中
        if hasattr(self, 'waiting_for_input') and self.waiting_for_input:
            self.handle_import_export_flow(user_input)
            return

        # 显示"思考中..."提示
        thinking_msg = "AI伙伴正在思考..."
        self.append_to_chat("系统", thinking_msg)

        # 在新线程中处理AI回复（避免界面卡顿）
        thread = threading.Thread(target=self.process_ai_response, args=(user_input,))
        thread.daemon = True
        thread.start()

    def process_ai_response(self, user_input):
        """处理AI回复（在后台线程中运行）"""
        try:
            print("=== 开始AI处理 ===")
            print(f"用户输入: {user_input}")

            # 获取用户偏好（记忆）
            user_memory = self.db.get_user_preferences()
            print(f"用户记忆: {user_memory[:100]}...")  # 只打印前100字符

            # 调用AI
            print("开始调用AI客户端...")
            ai_response = self.ai_client.chat(user_input, self.conversation_history, user_memory)
            print(f"AI回复: {ai_response}")


            # 在主线程中更新UI
            self.main_window.app.loop.call_soon_threadsafe(
                self.update_chat_with_ai_response,
                ai_response,
                user_input
            )
        except Exception as e:
            error_msg = f"AI回复处理出错: {str(e)}"
            print(f"错误详情: {error_msg}")
            import traceback
            traceback.print_exc()  # 打印完整堆栈跟踪

            self.main_window.app.loop.call_soon_threadsafe(
                self.show_error_and_reenable_button,
                error_msg
            )

    def update_chat_with_ai_response(self, ai_response, user_input):
        """在主线程中更新AI回复"""
        # 移除"思考中..."消息，用实际回复替换
        current_text = self.chat_display.value
        if "AI伙伴正在思考..." in current_text:
            lines = current_text.split('\n')
            # 移除最后两行（思考消息）
            lines = lines[:-2]
            self.chat_display.value = '\n'.join(lines) + '\n\n'

        # 显示AI回复
        self.append_to_chat("AI伙伴", ai_response)

        # 保存对话到数据库
        success = self.db.save_conversation(user_input, ai_response)
        if not success:
            self.append_to_chat("系统", "⚠️ 对话保存失败")

        # 更新对话历史
        self.conversation_history.append({
            'user': user_input,
            'ai': ai_response
        })

        # 保持历史长度
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

        # 重新启用发送按钮
        self.send_button.enabled = True

    def show_error_and_reenable_button(self, error_msg):
        """显示错误并重新启用发送按钮"""
        self.show_message("错误", error_msg)
        self.send_button.enabled = True

    def add_schedule(self, widget):
        """添加新行程"""
        event_time = self.schedule_time_input.value.strip()
        event_name = self.schedule_event_input.value.strip()

        if not event_time:
            self.show_message("提示", "请输入行程时间")
            return

        if not event_name:
            self.show_message("提示", "请输入事件内容")
            return

        # 简单验证时间格式
        if not self.is_valid_time(event_time):
            self.show_message("提示", "时间格式不正确，请使用 HH:MM 格式，如 14:30")
            return

        if self.db.add_schedule(event_time, event_name):
            self.schedule_time_input.value = ''
            self.schedule_event_input.value = ''
            self.append_to_chat("系统", f"✅ 已添加行程: {event_time} - {event_name}")
        else:
            self.show_message("错误", "添加行程失败")

    def is_valid_time(self, time_str):
        """简单验证时间格式"""
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except:
            return False

    def check_upcoming_schedules(self, widget):
        """检查即将到来的行程"""
        try:
            schedules = self.db.get_upcoming_schedules()

            if schedules:
                schedule_text = "\n".join([f"• {time} - {event}" for time, event in schedules])

                # 获取用户记忆来生成智能提醒
                user_memory = self.db.get_user_preferences()
                reminder = self.ai_client.generate_reminder(schedule_text, user_memory)

                # 将提醒保存到记忆库
                self.db.save_conversation(f"检查行程: {schedule_text}", reminder)

                self.append_to_chat("行程提醒", f"{reminder}\n\n今日安排:\n{schedule_text}")
            else:
                self.append_to_chat("系统", "今天没有即将到来的行程")
        except Exception as e:
            self.show_message("错误", f"检查行程时出错: {str(e)}")

    def view_data(self, widget):
        """查看所有数据 - 直接在聊天页面显示，可滚动查看"""
        try:
            # 使用统一的get_all_data方法获取数据
            all_data = self.db.get_all_data()

            if 'error' in all_data:
                self.append_to_chat("系统", f"获取数据失败: {all_data['error']}")
                return

            # 格式化显示数据
            display_text = "=== 所有数据 ===\n\n"

            # 对话记忆
            display_text += "📝 对话记忆 (最近10条):\n"
            if all_data['memories']:
                for memory in all_data['memories']:
                    display_text += f"• 用户: {memory[0][:50]}...\n"
                    display_text += f"  AI: {memory[1][:50]}...\n"
                    display_text += f"  时间: {memory[2]}\n\n"
            else:
                display_text += "  暂无对话记录\n\n"

            # 用户偏好
            display_text += "🎯 用户偏好:\n"
            if all_data['preferences']:
                for pref in all_data['preferences']:
                    category_display = {
                        'fact': '基本信息',
                        'like': '喜好',
                        'hobby': '习惯'
                    }.get(pref[0], pref[0])
                    display_text += f"• {category_display}: {pref[1]} = {pref[2]}\n"
            else:
                display_text += "  暂无偏好记录\n"
            display_text += "\n"

            # 行程安排
            display_text += "📅 行程安排:\n"
            if all_data['schedules']:
                for schedule in all_data['schedules']:
                    display_text += f"• ID:{schedule[0]} 时间:{schedule[1]} 事件:{schedule[2]}\n"
            else:
                display_text += "  暂无行程安排\n"

            # 直接在聊天区域显示，用户可以滚动查看
            self.append_to_chat("系统", display_text)

        except Exception as e:
            self.append_to_chat("系统", f"查看数据时出错: {str(e)}")

    def clear_chat(self, widget):
        """清空聊天显示（不影响数据库）"""
        self.chat_display.value = "对话记录已清空\n\n"
        self.append_to_chat("系统", "对话显示已清空，但所有数据仍保存在数据库中")

    def append_to_chat(self, speaker, text):
        """向聊天区域添加消息"""
        current_time = datetime.now().strftime("%H:%M")
        formatted_msg = f"[{current_time}] {speaker}: {text}\n\n"

        # 添加到显示区域
        self.chat_display.value += formatted_msg

        # 尝试滚动到底部 - 使用正确的方法名
        self.chat_display.focus()

    def show_message(self, title, message):
        """显示消息对话框"""
        self.main_window.info_dialog(title, message)

    def mine_preferences(self, widget):
        """挖掘新的用户偏好"""
        try:
            # 显示处理中状态
            self.append_to_chat("系统", "正在分析对话记录，挖掘新的用户偏好...")

            # 在新线程中执行挖掘，避免界面卡顿
            thread = threading.Thread(target=self.process_preference_mining)
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.show_message("错误", f"开始挖掘时出错: {str(e)}")

    def process_preference_mining(self):
        """在后台线程中处理偏好挖掘"""
        try:
            count, message = self.db.mine_new_preferences()

            # 在主线程中更新结果
            self.main_window.app.loop.call_soon_threadsafe(
                self.update_mining_result,
                count,
                message
            )
        except Exception as e:
            error_msg = f"偏好挖掘过程出错: {str(e)}"
            self.main_window.app.loop.call_soon_threadsafe(
                self.show_message, "错误", error_msg
            )

    def update_mining_result(self, count, message):
        """更新挖掘结果到界面"""
        if count > 0:
            self.append_to_chat("系统", f"✅ {message}")
            # 可以自动刷新显示新的偏好
            self.append_to_chat("系统", "偏好已更新，下次对话AI会记住这些信息！")
        else:
            self.append_to_chat("系统", f"ℹ️ {message}")

    def import_data(self, widget):
        """导入数据功能 - 简化版本"""
        print("导入数据按钮被点击")

        # 清空状态
        self.waiting_for_input = None
        self.selected_db_type = None

        # 显示选择提示
        self.append_to_chat("系统", "请选择要导入的数据库类型：")
        self.append_to_chat("系统", "1. 记忆数据库 (memory)")
        self.append_to_chat("系统", "2. 偏好数据库 (preferences)")
        self.append_to_chat("系统", "3. 行程数据库 (schedule)")
        self.append_to_chat("系统", "输入数字选择，或输入'取消'退出")

        self.waiting_for_input = "import_db_selection"

    def export_data(self, widget):
        """导出数据功能 - 文本交互版本"""
        print("导出数据按钮被点击")

        # 清空当前选择状态
        self.import_export_state = None
        self.selected_db_type = None

        # 显示数据库选择提示
        self.append_to_chat("系统", "请选择要导出的数据库，输入对应数字：")
        self.append_to_chat("系统", "1. 记忆数据库 (memory)")
        self.append_to_chat("系统", "2. 偏好数据库 (preferences)")
        self.append_to_chat("系统", "3. 行程数据库 (schedule)")
        self.append_to_chat("系统", "输入数字选择，或输入'取消'退出")

        # 设置状态为等待数据库选择
        self.waiting_for_input = "export_db_selection"


    def show_import_result(self, result, db_type):
        """显示导入结果"""
        if result.get('success'):
            count = result.get('count', 0)
            self.append_to_chat("系统", f"✅ 成功导入 {count} 条数据到{db_type}数据库")
        else:
            error_msg = result.get('error', '未知错误')
            self.show_message("导入失败", f"导入{db_type}数据库时出错: {error_msg}")

    def show_export_result(self, result, db_type, save_path):
        """显示导出结果"""
        if result.get('success'):
            count = result.get('count', 0)
            self.append_to_chat("系统", f"✅ 成功从{db_type}数据库导出 {count} 条数据")
            self.append_to_chat("系统", f"文件已保存到: {save_path}")
        else:
            error_msg = result.get('error', '未知错误')
            self.show_message("导出失败", f"导出{db_type}数据库时出错: {error_msg}")

    def handle_import_export_flow(self, user_input):
        """处理导入导出的文本交互流程"""
        user_input = user_input.lower().strip()

        if user_input in ['取消', 'exit', 'quit', '退出']:
            self.waiting_for_input = None
            self.selected_db_type = None
            self.append_to_chat("系统", "操作已取消")
            self.send_button.enabled = True
            return

        # 删除行程相关处理
        if self.waiting_for_input == "delete_schedule_id":
            self.handle_delete_schedule(user_input)

        # 数据库选择阶段
        elif self.waiting_for_input in ["import_db_selection", "export_db_selection"]:
            self.handle_database_selection(user_input)

        # 文件路径输入阶段
        elif self.waiting_for_input in ["import_file_path", "export_file_path"]:
            self.handle_file_path_input(user_input)

        elif self.waiting_for_input == "import_asset_filename":
            self.handle_asset_filename_input(user_input)


        elif self.waiting_for_input == "import_filename":
            filename = user_input.strip()
            if not filename.endswith('.json'):
                filename += '.json'

            # 从导入目录读取文件
            file_path = os.path.join(self.import_dir, filename)

            if not os.path.exists(file_path):
                self.append_to_chat("系统", f"❌ 文件不存在: {file_path}")
                # 重置状态
                self.waiting_for_input = None
                self.selected_db_type = None
            else:
                self.append_to_chat("系统", f"开始导入文件: {filename}")
                # 在新线程中处理导入
                thread = threading.Thread(
                    target=self.process_text_import,
                    args=(self.selected_db_type, file_path)
                )
                thread.daemon = True
                thread.start()
                # 注意：状态会在 process_text_import 完成后重置

        # 确保按钮启用
        self.send_button.enabled = True


    def handle_database_selection(self, user_input):
        """处理数据库选择"""
        db_mapping = {
            '1': 'memory',
            '2': 'preferences',
            '3': 'schedule',
            '记忆': 'memory',
            '偏好': 'preferences',
            '行程': 'schedule'
        }

        db_type = db_mapping.get(user_input)

        if db_type:
            self.selected_db_type = db_type
            db_display_names = {
                'memory': '记忆数据库',
                'preferences': '偏好数据库',
                'schedule': '行程数据库'
            }

            if self.waiting_for_input == "import_db_selection":
                self.append_to_chat("系统", f"已选择: {db_display_names[db_type]}")
                # 修改：从assets目录读取文件
                self.append_to_chat("系统", "请输入要导入的JSON文件名（从assets目录读取）：")

                # 列出assets中可用的文件
                asset_files = self.list_available_asset_files()
                if asset_files:
                    self.append_to_chat("系统", "📁📁 可用的预设数据文件:")
                    for file in asset_files:
                        self.append_to_chat("系统", f"  • {file}")
                else:
                    self.append_to_chat("系统", "❌❌ assets目录中没有预设数据文件")

                self.waiting_for_input = "import_asset_filename"  # 修改状态标识

            elif self.waiting_for_input == "export_db_selection":
                self.append_to_chat("系统", f"已选择: {db_display_names[db_type]}")
                # 生成默认文件名
                default_filename = f"{db_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.append_to_chat("系统", f"请输入保存路径（默认: {default_filename}），或输入'取消'退出：")
                self.waiting_for_input = "export_file_path"

        else:
            self.append_to_chat("系统", "无效选择，请输入 1、2 或 3：")
        # 在方法最后添加：
        self.send_button.enabled = True


    def handle_file_path_input(self, user_input):
        """处理文件路径输入"""
        if self.waiting_for_input == "import_file_path":
            # 导入文件处理
            if user_input and user_input not in ['取消', 'exit']:
                file_path = user_input
                self.append_to_chat("系统", f"开始导入文件: {file_path}")

                # 在新线程中处理导入
                thread = threading.Thread(
                    target=self.process_text_import,
                    args=(self.selected_db_type, file_path)
                )
                thread.daemon = True
                thread.start()
            else:
                self.waiting_for_input = None
                self.append_to_chat("系统", "导入操作已取消")

        elif self.waiting_for_input == "export_file_path":
            # 导出文件处理
            if user_input and user_input not in ['取消', 'exit']:
                save_path = user_input
                # 如果用户只输入了目录，添加默认文件名
                if save_path.endswith('/') or save_path.endswith('\\'):
                    default_filename = f"{self.selected_db_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    save_path = os.path.join(save_path, default_filename)

                self.append_to_chat("系统", f"开始导出到: {save_path}")

                # 在新线程中处理导出
                thread = threading.Thread(
                    target=self.process_text_export,
                    args=(self.selected_db_type, save_path)
                )
                thread.daemon = True
                thread.start()
            else:
                self.waiting_for_input = None
                self.append_to_chat("系统", "导出操作已取消")
        # 在方法最后添加：
        self.send_button.enabled = True



    def process_text_import(self, db_type, file_path):
        """处理文本交互的导入（后台线程）"""
        try:
            # 先检查文件格式
            is_valid, message = self.check_import_file(file_path)
            if not is_valid:
                self.main_window.app.loop.call_soon_threadsafe(
                    self.append_to_chat, "系统", f"❌❌ {message}"
                )
                return

            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 调用DatabaseManager的导入方法
            result = self.db.import_from_json(db_type, data)

            # 重置状态
            self.waiting_for_input = None
            self.selected_db_type = None

            # 在主线程中显示结果
            self.main_window.app.loop.call_soon_threadsafe(
                self.show_import_result,
                result,
                db_type
            )

        except Exception as e:
            error_msg = f"导入失败: {str(e)}"
            print(f"导入错误: {error_msg}")
            self.main_window.app.loop.call_soon_threadsafe(
                self.append_to_chat, "系统", f"❌ {error_msg}"
            )
            # 重置状态
            self.waiting_for_input = None
            self.selected_db_type = None

    def process_text_export(self, db_type, save_path):
        """处理文本交互的导出（后台线程）"""
        try:
            # 确保目录存在
            save_dir = os.path.dirname(save_path)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)

            # 调用DatabaseManager的导出方法
            result = self.db.export_to_json(db_type, save_path)

            # 重置状态
            self.waiting_for_input = None
            self.selected_db_type = None

            # 在主线程中显示结果
            self.main_window.app.loop.call_soon_threadsafe(
                self.show_export_result,
                result,
                db_type,
                save_path
            )

        except Exception as e:
            error_msg = f"导出失败: {str(e)}"
            print(f"导出错误: {error_msg}")
            self.main_window.app.loop.call_soon_threadsafe(
                self.append_to_chat, "系统", f"❌ {error_msg}"
            )
            # 重置状态
            self.waiting_for_input = None
            self.selected_db_type = None

    def show_file_locations(self, widget):
        """显示文件位置帮助信息"""
        self.append_to_chat("系统", "=== 文件位置说明 ===")
        self.append_to_chat("系统", f"📂 导入目录: {self.import_dir}")
        self.append_to_chat("系统", f"📂 导出目录: {self.export_dir}")
        self.append_to_chat("系统", "📱 使用文件管理器访问这些目录")
        self.append_to_chat("系统", "💡 提示: 在文件管理器中搜索'ai_companion'即可找到")

    def list_available_files(self, widget):
        """列出可用的文件"""
        try:
            import_files = os.listdir(self.import_dir)
            json_files = [f for f in import_files if f.endswith('.json')]

            self.append_to_chat("系统", "=== 可导入的文件 ===")
            if json_files:
                for file in json_files:
                    self.append_to_chat("系统", f"📄 {file}")
            else:
                self.append_to_chat("系统", "导入目录中没有JSON文件")

            export_files = os.listdir(self.export_dir)
            export_json_files = [f for f in export_files if f.endswith('.json')]

            self.append_to_chat("系统", "=== 已导出的文件 ===")
            if export_json_files:
                for file in export_json_files:
                    self.append_to_chat("系统", f"📄 {file}")
            else:
                self.append_to_chat("系统", "导出目录中没有文件")

        except Exception as e:
            self.append_to_chat("系统", f"查看文件失败: {str(e)}")

    def import_from_app_assets(self, filename, db_type):
        """从APP资源目录导入数据"""
        try:
            # 使用正确的资源路径
            # 在Android上，资源文件通常打包在apk中，需要使用特殊方式访问
            # 这里我们回退到使用预定义的import目录
            file_path = os.path.join(self.import_dir, filename)

            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, f"文件不存在: {file_path}"

            # 读取并导入数据
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 调用DatabaseManager的导入方法
            result = self.db.import_from_json(db_type, data)

            if result.get('success'):
                return True, f"成功导入 {result.get('count', 0)} 条数据"
            else:
                return False, result.get('error', '导入失败')

        except Exception as e:
            return False, f"导入失败: {str(e)}"

    def list_available_asset_files(self):
        """列出可用的资源文件"""
        try:
            # 尝试多个可能的路径
            possible_dirs = [
                self.predefined_data_dir,
                os.path.join(self.paths.app, 'resources', 'predefined_data'),
                os.path.join(self.paths.app, 'assets', 'predefined_data'),
                os.path.join(self.paths.app, 'src', 'resources', 'predefined_data'),
                os.path.join(self.paths.app, 'predefined_data'),  # 直接放在应用目录
            ]

            json_files = []
            for dir_path in possible_dirs:
                if os.path.exists(dir_path):
                    print(f"🔍 检查目录: {dir_path}")
                    files = os.listdir(dir_path)
                    json_files = [f for f in files if f.endswith('.json')]
                    if json_files:
                        print(f"✅ 在 {dir_path} 找到JSON文件: {json_files}")
                        break

            return json_files

        except Exception as e:
            print(f"列出资源文件时出错: {e}")
            return []

    def show_asset_files(self, widget):
        """显示可用的资源文件"""
        json_files = self.list_available_asset_files()

        if json_files:
            self.append_to_chat("系统", "📁 可用的预设数据文件:")
            for file in json_files:
                self.append_to_chat("系统", f"  • {file}")
            self.append_to_chat("系统", "💡 输入文件名即可导入")
        else:
            self.append_to_chat("系统", "❌ 没有找到预设数据文件")

    def import_from_assets(self, filename, db_type):
        """从assets目录导入数据"""
        try:
            # 构建assets文件路径
            file_path = os.path.join(self.predefined_data_dir, filename)

            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {'success': False, 'error': f"文件不存在: {file_path}"}

            # 读取并导入数据
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 调用DatabaseManager的导入方法
            result = self.db.import_from_json(db_type, data)
            return result

        except Exception as e:
            return {'success': False, 'error': f"导入失败: {str(e)}"}

    def process_asset_import(self, filename, db_type):
        """处理assets导入（后台线程）"""
        try:
            result = self.import_from_assets(filename, db_type)

            # 在主线程中显示结果
            self.main_window.app.loop.call_soon_threadsafe(
                self.show_import_result,
                result,
                db_type
            )

        except Exception as e:
            error_msg = f"assets导入失败: {str(e)}"
            self.main_window.app.loop.call_soon_threadsafe(
                self.append_to_chat, "系统", f"❌❌ {error_msg}"
            )
        finally:
            # 重置状态
            self.waiting_for_input = None
            self.selected_db_type = None

    def handle_filename_input(self, user_input):
        """处理文件名输入"""
        filename = user_input.strip()
        if not filename.endswith('.json'):
            filename += '.json'

        # 从 import 目录读取文件
        file_path = os.path.join(self.import_dir, filename)

        if not os.path.exists(file_path):
            self.append_to_chat("系统", f"❌ 文件不存在: {file_path}")
            self.waiting_for_input = None
            self.selected_db_type = None
            return

        self.append_to_chat("系统", f"开始导入文件: {filename}")

        # 在新线程中处理导入
        thread = threading.Thread(
            target=self.process_text_import,
            args=(self.selected_db_type, file_path)
        )
        thread.daemon = True
        thread.start()

    def check_import_file(self, file_path):
        """检查导入文件是否有效"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                return False, "文件格式错误：应该是JSON数组"

            return True, "文件格式正确"
        except Exception as e:
            return False, f"文件读取失败: {str(e)}"

    def handle_asset_filename_input(self, user_input):
        """处理assets文件名输入"""
        filename = user_input.strip()
        if not filename.endswith('.json'):
            filename += '.json'

        # 从assets目录读取文件
        file_path = os.path.join(self.predefined_data_dir, filename)

        if not os.path.exists(file_path):
            self.append_to_chat("系统", f"❌❌ assets中文件不存在: {filename}")
            self.append_to_chat("系统", f"请检查文件是否在: {self.predefined_data_dir}")
            self.waiting_for_input = None
            self.selected_db_type = None
            return

        self.append_to_chat("系统", f"开始从assets导入文件: {filename}")

        # 在新线程中处理导入
        thread = threading.Thread(
            target=self.process_asset_import,
            args=(filename, self.selected_db_type)
        )
        thread.daemon = True
        thread.start()

    def handle_import_confirmation(self, user_input):
        """处理导入确认"""
        if user_input.lower() in ['是', 'yes', 'y']:
            # 在新线程中处理导入
            thread = threading.Thread(
                target=self.process_text_import,
                args=(self.selected_db_type, self.temp_file_path)
            )
            thread.daemon = True
            thread.start()
        else:
            self.append_to_chat("系统", "导入操作已取消")
            self.waiting_for_input = None
            self.selected_db_type = None
            self.temp_file_path = None

    def delete_schedule(self, widget):
        """删除行程 - 文本交互方式"""
        try:
            # 获取所有行程供用户选择
            schedules = self.db.get_all_data().get('schedules', [])

            if not schedules:
                self.append_to_chat("系统", "当前没有可删除的行程")
                return

            # 显示所有行程供用户选择
            self.append_to_chat("系统", "📋 当前所有行程:")
            for schedule in schedules:
                self.append_to_chat("系统", f"  ID:{schedule[0]} - {schedule[1]} - {schedule[2]}")

            self.append_to_chat("系统", "请输入要删除的行程ID，或输入'取消'退出:")
            self.waiting_for_input = "delete_schedule_id"

        except Exception as e:
            self.append_to_chat("系统", f"获取行程列表时出错: {str(e)}")

    def handle_delete_schedule(self, user_input):
        """处理删除行程的输入"""
        if user_input.lower() in ['取消', 'exit', 'quit']:
            self.append_to_chat("系统", "删除操作已取消")
            self.waiting_for_input = None
            return

        try:
            schedule_id = int(user_input.strip())

            # 执行删除
            success, message = self.db.delete_schedule(schedule_id)

            if success:
                self.append_to_chat("系统", f"✅ {message}")
            else:
                self.append_to_chat("系统", f"❌ {message}")

        except ValueError:
            self.append_to_chat("系统", "❌ 请输入有效的数字ID")
        except Exception as e:
            self.append_to_chat("系统", f"删除行程时出错: {str(e)}")

        # 清理状态
        self.waiting_for_input = None

    def confirm_delete_schedule(self, user_input):
        """确认删除行程"""
        if user_input.lower() in ['确认', 'yes', 'y', '是']:
            # 执行删除
            success, message = self.db.delete_schedule(self.temp_schedule_id)

            if success:
                self.append_to_chat("系统", f"✅ {message}")
            else:
                self.append_to_chat("系统", f"❌ {message}")

        else:
            self.append_to_chat("系统", "删除操作已取消")

        # 清理状态
        self.waiting_for_input = None
        self.temp_schedule_id = None

    def show_confirm_dialog(self, title, message):
        """显示确认对话框"""
        # 这里需要根据你的GUI框架实现确认对话框
        # 如果是Kivy，可以使用Popup
        # 这里先返回True，你需要根据实际框架实现
        print(f"确认对话框: {title} - {message}")
        return True

    def update_schedule_list(self):
        """更新行程列表显示"""
        # 清空当前列表
        self.schedule_list.clear()

        # 重新添加所有行程
        for i, (schedule_id, time, event) in enumerate(self.schedules):
            self.schedule_list.add_item(f"{time} - {event}")





def main():
    return Talk_in_App_v01(formal_name="Finding", app_id="com.sharkfinder.finding251018")
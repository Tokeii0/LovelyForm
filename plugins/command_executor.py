import csv
import imp
from threading import Thread
from typing import List, Dict, Optional
import json
import os
import pandas as pd
import yaml
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QListWidget, QMessageBox,
    QInputDialog, QComboBox, QCheckBox, QSizePolicy,
    QTableView, QWidget, QTextEdit
)
from PySide6.QtCore import Qt, Signal
import subprocess
from lovelyform.plugins import CellPlugin
from plugin.csv_rules import pslist_context_menu

class CommandConfig:
    def __init__(self, name: str = "", path_name: str = "", prefix: str = "", suffix: str = "", executor_name: str = "", 
                 globally_enabled: bool = True, enabled_columns: str = "", json_to_csv: bool = False, category: str = ""):
        self.name = name
        self.path_name = path_name  # 存储选择的路径名称
        self.prefix = prefix
        self.suffix = suffix
        self.executor_name = executor_name  # 存储执行程序的路径名称
        self.globally_enabled = globally_enabled  # 是否全局可用
        self.enabled_columns = enabled_columns  # 逗号分隔的可用列名称
        self.json_to_csv = json_to_csv  # json转csv开关
        self.category = category  # 菜单分类
        
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path_name": self.path_name,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "executor_name": self.executor_name,
            "globally_enabled": self.globally_enabled,
            "enabled_columns": self.enabled_columns,
            "json_to_csv": self.json_to_csv,
            "category": self.category
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'CommandConfig':
        return CommandConfig(
            name=data.get("name", ""),
            path_name=data.get("path_name", ""),
            prefix=data.get("prefix", ""),
            suffix=data.get("suffix", ""),
            executor_name=data.get("executor_name", ""),
            globally_enabled=data.get("globally_enabled", True),
            enabled_columns=data.get("enabled_columns", ""),
            json_to_csv=data.get("json_to_csv", False),
            category=data.get("category", "")
        )

def load_base_config() -> Dict[str, str]:
    """加载基础配置文件中的路径"""
    paths = {}
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_file = os.path.join(base_dir, "config", "base_config.yaml")
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # 收集所有工具的路径
            for category in ['tools', 'base_tools', 'other_tools']:
                if category in config:
                    for tool_name, tool_info in config[category].items():
                        if isinstance(tool_info, dict) and 'path' in tool_info:
                            paths[f"{category}/{tool_name}"] = tool_info['path']
                            
    except Exception as e:
        print(f"加载基础配置失败：{str(e)}")
        
    return paths

class CustomCommandPlugin(CellPlugin):
    """自定义命令执行插件"""
    
    def __init__(self, command_config: CommandConfig, paths: Dict[str, str], variables: Optional[Dict[str, str]] = None):
        super().__init__()
        self.command_config = command_config
        self.paths = paths
        self.variables = variables or {}
        
    @property
    def name(self) -> str:
        return self.command_config.name
        
    @property
    def description(self) -> str:
        path = self.paths.get(self.command_config.path_name, "")
        if path:
            return f"执行命令: {path} {self.command_config.prefix} [内容] {self.command_config.suffix}"
        return f"执行命令: {self.command_config.prefix} [内容] {self.command_config.suffix}"
        
    def is_column_enabled(self, col_name: str) -> bool:
        """判断指定列是否允许使用该命令"""
        # 如果全局启用,则所有列都可用
        if self.command_config.globally_enabled:
            return True
            
        # 如果没有指定启用列,则所有列都不可用
        if not self.command_config.enabled_columns:
            return False
            
        # 检查列名是否在启用列列表中
        enabled_columns = [col.strip() for col in self.command_config.enabled_columns.split(',') if col.strip()]
        return col_name in enabled_columns
        
    def _replace_variables(self, text: str, value: str = "") -> str:
        """替换变量"""
        if not text:
            return text
            
        # 添加当前选中单元格的值作为变量
        variables = {
            **{k: v for k, v in self.variables.items()},  # 复制系统变量
            "value": value  # 添加当前选中的单元格值
        }
            
        # 替换变量
        result = text
        for var_name, var_value in variables.items():
            # 确保变量名格式正确
            placeholder = "${" + var_name + "}"
            result = result.replace(placeholder, str(var_value))
            
        return result
        
    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        try:
            # 获取主窗口实例
            from PySide6.QtWidgets import QApplication
            main_window = QApplication.activeWindow()
            if not main_window:
                return df
                
            # 获取表格视图和代理模型
            table_view = main_window.findChild(QTableView)
            if not table_view:
                return df
                
            proxy_model = table_view.model()
            source_model = proxy_model.sourceModel()
            
            for row, col in selected_cells:
                # 将视图索引转换为源模型索引
                proxy_index = proxy_model.index(row, col)
                source_index = proxy_model.mapToSource(proxy_index)
                source_row = source_index.row()
                source_col = source_index.column()
                
                # 获取列名并检查是否启用
                col_name = df.columns[source_col]
                if not self.is_column_enabled(col_name):
                    continue
                    
                # 使用源模型索引获取值，并去除引号
                value = str(df.iloc[source_row, source_col]).strip('"')
                
                # 获取选择的路径并替换变量
                path = self._replace_variables(self.paths.get(self.command_config.path_name, ""))
                
                # 获取执行程序并替换变量
                executor = self._replace_variables(self.paths.get(self.command_config.executor_name, ""))
                
                # 构建完整命令
                command_parts = []
                
                # 添加执行程序
                if executor:
                    command_parts.append(f'"{os.path.normpath(executor)}"')
                
                # 添加路径
                if path:
                    command_parts.append(f'"{os.path.normpath(path)}"')
                
                # 替换前缀中的变量并去除引号
                if self.command_config.prefix:
                    prefix = self._replace_variables(self.command_config.prefix, value=value).strip('"')
                    command_parts.append(prefix)
                
                # 替换值中的变量并去除引号
                value = self._replace_variables(value, value=value).strip('"')
                command_parts.append(value)
                
                # 替换后缀中的变量并去除引号
                if self.command_config.suffix:
                    suffix = self._replace_variables(self.command_config.suffix, value=value).strip('"')
                    command_parts.append(suffix)
                
                command = " ".join(command_parts)
                print(f"执行命令: {command}")
                
                def execute_command():
                    def run_command():
                        try:
                            print(f"\n[*] 开始执行命令: {command}")
                            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            stdout, stderr = process.communicate()
                            
                            # 打印命令输出
                            if stdout:
                                print("\n[+] 命令输出:")
                                print(stdout)
                            
                            import time
                            time.sleep(2)  # 等待2秒
                            
                            # 检查是否需要转换json到csv
                            if self.command_config.json_to_csv:
                                # 查找output目录下的json文件
                                import glob
                                import json
                                import pandas as pd
                                
                                # 使用正确的output目录路径
                                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output')
                                if not os.path.exists(output_dir):
                                    os.makedirs(output_dir)
                                
                                # 切换到output目录
                                original_dir = os.getcwd()  # 保存当前目录
                                os.chdir(output_dir)
                                
                                try:
                                    print(f"\n[*] 正在检查目录 {output_dir} 中的json文件")
                                    json_files = glob.glob('*.json')
                                    print(f"[*] 找到 {len(json_files)} 个json文件")
                                    
                                    for json_file in json_files:
                                        try:
                                            print(f"[*] 正在处理文件: {json_file}")
                                            with open(json_file, 'r', encoding='utf-8') as f:
                                                data = json.load(f)
                                            if isinstance(data, list):
                                                # 如果是列表，直接转换
                                                df = pd.DataFrame(data)
                                                csv_file = json_file.replace('.json', '.csv')
                                                df.to_csv(csv_file, index=False)
                                                print(f"[+] 成功将 {json_file} 转换为 {csv_file}")
                                                os.remove(json_file)
                                            elif isinstance(data, dict):
                                                if 'rows' in data and 'columns' in data:
                                                    # 如果包含rows和columns字段
                                                    df = pd.DataFrame(data['rows'], columns=data['columns'])
                                                else:
                                                    # 如果是普通字典，尝试直接转换
                                                    df = pd.DataFrame([data])
                                                csv_file = json_file.replace('.json', '.csv')
                                                df.to_csv(csv_file, index=False)
                                                print(f"[+] 成功将 {json_file} 转换为 {csv_file}")
                                                os.remove(json_file)
                                            else:
                                                print(f"[!] {json_file} 格式不支持转换")
                                        except Exception as e:
                                            print(f"[!] 转换 {json_file} 时出错: {str(e)}")
                                finally:
                                    os.chdir(original_dir)  # 恢复原来的工作目录
                        except Exception as e:
                            print(f"[!] 执行命令时出错: {str(e)}")
                            if hasattr(e, 'output'):
                                print(f"[!] 错误输出: {e.output}")       
                    # 创建并启动新线程
                    command_thread = Thread(target=run_command)
                    command_thread.daemon = True  # 设置为守护线程
                    command_thread.start()
                    
                    

                # 使用线程执行命令
                execute_command()
                
                print(f"[*] 命令执行完成,请在文件槽中查看相关文件")

        except Exception as e:
            print(f"执行命令时出错: {str(e)}")
        
        # import re
        # try:
        #     csv_file = re.search(r'output/(\S+\.csv)', command)
        #     print(csv_file.group(1))
        #     if csv_file:
        #         from lovelyform import show_csv_viewer
        #         show_csv_viewer("output/" + csv_file.group(1))
        except Exception as e:
            pass
                
            
        return df
        
    def match_column(self, col_name: str) -> bool:
        """重写match_column方法,加入列启用检查"""
        # 首先检查列是否启用
        if not self.is_column_enabled(col_name):
            return False
        # 然后调用父类的match_column方法进行模式匹配
        return super().match_column(col_name)
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*"]  # 匹配所有列

def get_command_plugins() -> Dict[str, CellPlugin]:
    """获取所有已配置的命令插件"""
    plugins = {}
    # 获取lovelyform目录的路径
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_file = os.path.join(base_dir, "lovelyform", "config", "commands.json")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                paths = load_base_config()
                
                # 读取image_info.txt并解析内容
                variables = {}
                try:
                    with open("output/image_info.txt", "r") as var_f:
                        content = var_f.read().strip()
                        mem_path, profile = content.split(",")
                        variables["mem_path"] = mem_path
                        variables["profile"] = profile
                except Exception as e:
                    print(f"读取image_info.txt失败: {str(e)}")
                    
                # 添加output路径变量
                variables["output"] = "output"
                
                for cmd_data in data:
                    cmd = CommandConfig.from_dict(cmd_data)
                    plugins[cmd.name] = CustomCommandPlugin(cmd, paths, variables)
        except Exception as e:
            print(f"加载命令配置失败：{str(e)}")
            
    return plugins

class CommandConfigDialog(QDialog):
    # 添加信号
    plugins_updated = Signal()
    
    def __init__(self, parent=None, variables: Optional[Dict[str, str]] = None):
        super().__init__(parent)
        self.setWindowTitle("命令配置")
        self.setMinimumWidth(500)
        self.commands: List[CommandConfig] = []
        self.paths = load_base_config()
        self.variables = variables or {}
        
        # 读取image_info.txt并解析内容
        try:
            with open("output/image_info.txt", "r") as f:
                content = f.read().strip()
                mem_path, profile = content.split(",")
                # 添加到变量中
                self.variables["mem_path"] = mem_path
                self.variables["profile"] = profile
        except Exception as e:
            print(f"读取image_info.txt失败: {str(e)}")
            
        # 添加output路径变量
        self.variables["output"] = "output"
        
        # 如果有传入变量，添加到路径列表中
        for var_name, var_value in self.variables.items():
            self.paths[f"variables/{var_name}"] = f"${{{var_name}}}"
            
        self.load_commands()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 命令列表
        list_label = QLabel("已配置的命令:")
        layout.addWidget(list_label)
        
        self.command_list = QListWidget()
        self.command_list.currentRowChanged.connect(self.on_selection_changed)
        layout.addWidget(self.command_list)
        
        # 编辑区域
        edit_widget = QWidget()
        edit_layout = QVBoxLayout()
        edit_widget.setLayout(edit_layout)
        
        # 名称输入
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        name_label.setFixedWidth(100)  # 增加标签宽度
        name_layout.addWidget(name_label)
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        edit_layout.addLayout(name_layout)
        
        # 路径选择
        path_layout = QHBoxLayout()
        path_label = QLabel("路径:")
        path_label.setFixedWidth(100)  # 增加标签宽度
        path_layout.addWidget(path_label)
        self.path_combo = QComboBox()
        self.path_combo.addItem("")  # 添加一个空选项
        self.path_combo.addItems(self.paths.keys())
        path_layout.addWidget(self.path_combo)
        edit_layout.addLayout(path_layout)
        
        # 执行程序选择
        executor_layout = QHBoxLayout()
        executor_label = QLabel("执行程序:")
        executor_label.setFixedWidth(100)  # 增加标签宽度
        executor_layout.addWidget(executor_label)
        self.executor_combo = QComboBox()
        self.executor_combo.addItem("")  # 添加一个空选项
        self.executor_combo.addItems(self.paths.keys())
        executor_layout.addWidget(self.executor_combo)
        edit_layout.addLayout(executor_layout)
        
        # 前缀命令输入
        prefix_layout = QHBoxLayout()
        prefix_label = QLabel("前缀命令:")
        prefix_label.setFixedWidth(100)  # 增加标签宽度
        prefix_layout.addWidget(prefix_label)
        self.prefix_edit = QLineEdit()
        prefix_layout.addWidget(self.prefix_edit)
        edit_layout.addLayout(prefix_layout)
        
        # 后缀命令输入
        suffix_layout = QHBoxLayout()
        suffix_label = QLabel("后缀命令:")
        suffix_label.setFixedWidth(100)  # 增加标签宽度
        suffix_layout.addWidget(suffix_label)
        self.suffix_edit = QLineEdit()
        suffix_layout.addWidget(self.suffix_edit)
        edit_layout.addLayout(suffix_layout)
        
        # 全局启用
        globally_enabled_layout = QHBoxLayout()
        globally_enabled_label = QLabel("全局启用:")
        globally_enabled_label.setFixedWidth(100)  # 增加标签宽度
        globally_enabled_layout.addWidget(globally_enabled_label)
        self.globally_enabled_checkbox = QCheckBox()
        globally_enabled_layout.addWidget(self.globally_enabled_checkbox)
        globally_enabled_layout.addStretch()  # 添加弹性空间
        edit_layout.addLayout(globally_enabled_layout)
        
        # 启用列
        enabled_columns_layout = QHBoxLayout()
        enabled_columns_label = QLabel("启用列:")
        enabled_columns_label.setFixedWidth(100)  # 增加标签宽度
        enabled_columns_layout.addWidget(enabled_columns_label)
        self.enabled_columns_edit = QLineEdit()
        enabled_columns_layout.addWidget(self.enabled_columns_edit)
        edit_layout.addLayout(enabled_columns_layout)
        
        # json转csv
        json_to_csv_layout = QHBoxLayout()
        json_to_csv_label = QLabel("json转csv:")
        json_to_csv_label.setFixedWidth(100)  # 增加标签宽度
        json_to_csv_layout.addWidget(json_to_csv_label)
        self.json_to_csv_checkbox = QCheckBox()
        json_to_csv_layout.addWidget(self.json_to_csv_checkbox)
        json_to_csv_layout.addStretch()  # 添加弹性空间
        edit_layout.addLayout(json_to_csv_layout)
        
        # 菜单分类
        category_layout = QHBoxLayout()
        category_label = QLabel("菜单分类:")
        category_label.setFixedWidth(100)  # 增加标签宽度
        category_layout.addWidget(category_label)
        self.category_edit = QLineEdit()
        category_layout.addWidget(self.category_edit)
        edit_layout.addLayout(category_layout)
        
        # 如果有变量，显示变量列表
        if self.variables:
            var_label = QLabel("可用变量:")
            edit_layout.addWidget(var_label)
            var_text = QTextEdit()
            var_text.setReadOnly(True)
            var_text.setMaximumHeight(100)
            
            # 格式化变量列表
            variables_text = "系统变量:\n"
            for k, v in self.variables.items():
                variables_text += f"${{{k}}}: {v}\n"
            
            # 添加当前选中单元格的值作为变量
            variables_text += "\n特殊变量:\n"
            variables_text += "${value}: 当前选中的单元格值"
            
            var_text.setText(variables_text)
            var_text.setStyleSheet("QTextEdit { background-color: #f5f5f5; }")
            edit_layout.addWidget(var_text)
        
        layout.addWidget(edit_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("新增")
        add_btn.clicked.connect(self.add_command)
        button_layout.addWidget(add_btn)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_command)
        button_layout.addWidget(save_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_command)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.update_list()
        
    def update_list(self):
        """更新命令列表"""
        self.command_list.clear()
        for cmd in self.commands:
            path = self.paths.get(cmd.path_name, "")
            if path:
                self.command_list.addItem(f"{cmd.name} ({cmd.path_name})")
            else:
                self.command_list.addItem(cmd.name)
                
    def on_selection_changed(self):
        """选中项改变时的处理"""
        row = self.command_list.currentRow()
        if row >= 0 and row < len(self.commands):
            cmd = self.commands[row]
            self.name_edit.setText(cmd.name)
            # 设置路径选择
            index = self.path_combo.findText(cmd.path_name)
            self.path_combo.setCurrentIndex(index if index >= 0 else 0)
            # 设置执行程序选择
            index = self.executor_combo.findText(cmd.executor_name)
            self.executor_combo.setCurrentIndex(index if index >= 0 else 0)
            self.prefix_edit.setText(cmd.prefix)
            self.suffix_edit.setText(cmd.suffix)
            self.globally_enabled_checkbox.setChecked(cmd.globally_enabled)
            self.enabled_columns_edit.setText(cmd.enabled_columns)
            self.json_to_csv_checkbox.setChecked(cmd.json_to_csv)
            self.category_edit.setText(cmd.category)
        else:
            self.name_edit.clear()
            self.path_combo.setCurrentIndex(0)
            self.executor_combo.setCurrentIndex(0)
            self.prefix_edit.clear()
            self.suffix_edit.clear()
            self.globally_enabled_checkbox.setChecked(True)
            self.enabled_columns_edit.clear()
            self.json_to_csv_checkbox.setChecked(False)
            self.category_edit.clear()
            
    def get_config_file(self) -> str:
        """获取配置文件路径"""
        # 获取lovelyform目录的路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_dir = os.path.join(base_dir, "lovelyform", "config")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        return os.path.join(config_dir, "commands.json")
        
    def load_commands(self):
        """加载命令配置"""
        config_file = self.get_config_file()
        self.commands = []
        
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for cmd_data in data:
                        self.commands.append(CommandConfig.from_dict(cmd_data))
            except Exception as e:
                QMessageBox.warning(self, "加载失败", f"加载命令配置失败：{str(e)}")
                
    def save_commands(self):
        """保存命令配置"""
        config_file = self.get_config_file()
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                data = [cmd.to_dict() for cmd in self.commands]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存命令配置失败：{str(e)}")
            
    def add_command(self):
        """添加新命令"""
        name, ok = QInputDialog.getText(self, "新建命令", "请输入命令名称:")
        if ok and name:
            # 检查名称是否已存在
            if any(cmd.name == name for cmd in self.commands):
                QMessageBox.warning(self, "错误", "命令名称已存在")
                return
                
            cmd = CommandConfig(name=name)
            self.commands.append(cmd)
            self.save_commands()
            self.update_list()
            # 选中新添加的命令
            self.command_list.setCurrentRow(len(self.commands) - 1)
            
    def save_command(self):
        """保存当前编辑的命令"""
        row = self.command_list.currentRow()
        if row < 0:
            return
            
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "请输入命令名称")
            return
            
        path_name = self.path_combo.currentText()
        if path_name == "":
            path_name = ""
            
        executor_name = self.executor_combo.currentText()
        if executor_name == "":
            executor_name = ""
            
        prefix = self.prefix_edit.text().strip()
        suffix = self.suffix_edit.text().strip()
        globally_enabled = self.globally_enabled_checkbox.isChecked()
        enabled_columns = self.enabled_columns_edit.text().strip()
        json_to_csv = self.json_to_csv_checkbox.isChecked()
        category = self.category_edit.text().strip()
        
        if row < len(self.commands):
            self.commands[row] = CommandConfig(name, path_name, prefix, suffix, executor_name, globally_enabled, enabled_columns, json_to_csv, category)
        else:
            self.commands.append(CommandConfig(name, path_name, prefix, suffix, executor_name, globally_enabled, enabled_columns, json_to_csv, category))
            
        self.save_commands()
        self.update_list()
        self.command_list.setCurrentRow(row)
        QMessageBox.information(self, "成功", "命令配置已保存")
        self.plugins_updated.emit()  # 发送信号
            
    def delete_command(self):
        """删除选中的命令"""
        row = self.command_list.currentRow()
        if row >= 0:
            reply = QMessageBox.question(self, "确认删除", 
                                       f"确定要删除命令 '{self.commands[row].name}' 吗？",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.commands.pop(row)
                self.save_commands()
                self.update_list()

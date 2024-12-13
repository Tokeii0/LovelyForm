from typing import List, Dict
import json
import os
import pandas as pd
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QListWidget, QMessageBox,
    QInputDialog
)
from PySide6.QtCore import Qt
import subprocess
from plugins import CellPlugin

class CommandConfig:
    def __init__(self, name: str = "", prefix: str = "", suffix: str = ""):
        self.name = name
        self.prefix = prefix
        self.suffix = suffix
        
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "prefix": self.prefix,
            "suffix": self.suffix
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'CommandConfig':
        return CommandConfig(
            name=data.get("name", ""),
            prefix=data.get("prefix", ""),
            suffix=data.get("suffix", "")
        )

class CustomCommandPlugin(CellPlugin):
    """自定义命令执行插件"""
    
    def __init__(self, command_config: CommandConfig):
        super().__init__()
        self.command_config = command_config
        
    @property
    def name(self) -> str:
        return self.command_config.name
        
    @property
    def description(self) -> str:
        return f"执行命令: {self.command_config.prefix} [内容] {self.command_config.suffix}"
        
    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        for row, col in selected_cells:
            value = str(df.iloc[row, col]).strip()
            if value:
                try:
                    # 构建完整命令
                    full_command = f"{self.command_config.prefix} {value} {self.command_config.suffix}".strip()
                    subprocess.Popen(full_command, shell=True)
                except Exception as e:
                    QMessageBox.warning(None, "命令执行错误", f"执行命令时出错：{str(e)}")
        return df
    
    @property
    def column_patterns(self) -> List[str]:
        return ["*"]  # 匹配所有列

def get_command_plugins() -> Dict[str, CellPlugin]:
    """获取所有已配置的命令插件"""
    plugins = {}
    config_file = os.path.join("config", "commands.json")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                commands = json.load(f)
                for cmd_data in commands:
                    config = CommandConfig.from_dict(cmd_data)
                    plugin = CustomCommandPlugin(config)
                    plugins[f"CustomCommand_{config.name}"] = plugin
        except Exception as e:
            print(f"加载命令配置失败: {str(e)}")
            
    return plugins

class CommandConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("命令配置")
        self.setMinimumWidth(400)
        self.commands: List[CommandConfig] = []
        self.load_commands()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 命令列表
        self.command_list = QListWidget()
        self.command_list.currentRowChanged.connect(self.on_selection_changed)
        layout.addWidget(self.command_list)
        
        # 编辑区域
        edit_layout = QVBoxLayout()
        
        # 名称输入
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        edit_layout.addLayout(name_layout)
        
        # 前缀命令输入
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("前缀命令:"))
        self.prefix_edit = QLineEdit()
        prefix_layout.addWidget(self.prefix_edit)
        edit_layout.addLayout(prefix_layout)
        
        # 后缀命令输入
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("后缀命令:"))
        self.suffix_edit = QLineEdit()
        suffix_layout.addWidget(self.suffix_edit)
        edit_layout.addLayout(suffix_layout)
        
        layout.addLayout(edit_layout)
        
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
        
    def get_config_file(self) -> str:
        """获取配置文件路径"""
        config_dir = "config"
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
            
    def update_list(self):
        """更新命令列表"""
        self.command_list.clear()
        for cmd in self.commands:
            self.command_list.addItem(cmd.name)
            
    def on_selection_changed(self):
        """选中项改变时的处理"""
        current = self.command_list.currentRow()
        if current >= 0:
            cmd = self.commands[current]
            self.name_edit.setText(cmd.name)
            self.prefix_edit.setText(cmd.prefix)
            self.suffix_edit.setText(cmd.suffix)
        else:
            self.name_edit.clear()
            self.prefix_edit.clear()
            self.suffix_edit.clear()
            
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
        current = self.command_list.currentRow()
        if current >= 0:
            cmd = self.commands[current]
            new_name = self.name_edit.text().strip()
            
            # 如果名称改变了，检查是否与其他命令重名
            if new_name != cmd.name and any(c.name == new_name for c in self.commands if c != cmd):
                QMessageBox.warning(self, "错误", "命令名称已存在")
                return
                
            cmd.name = new_name
            cmd.prefix = self.prefix_edit.text().strip()
            cmd.suffix = self.suffix_edit.text().strip()
            
            self.save_commands()
            self.update_list()
            self.command_list.setCurrentRow(current)
            QMessageBox.information(self, "成功", "命令配置已保存")
            
    def delete_command(self):
        """删除选中的命令"""
        current = self.command_list.currentRow()
        if current >= 0:
            reply = QMessageBox.question(self, "确认删除", 
                                       f"确定要删除命令 '{self.commands[current].name}' 吗？",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.commands.pop(current)
                self.save_commands()
                self.update_list()

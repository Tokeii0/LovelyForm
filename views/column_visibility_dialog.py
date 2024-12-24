from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QCheckBox, QScrollArea, QWidget)
from PySide6.QtCore import Qt

class ColumnVisibilityDialog(QDialog):
    def __init__(self, columns, visible_columns=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("列显示设置")
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)
        
        # 保存列信息
        self.columns = columns
        # 如果没有指定可见列，则默认全部可见
        self.visible_columns = visible_columns if visible_columns is not None else columns.copy()
        
        # 创建主布局
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 创建全选/取消全选按钮
        select_all_btn = QPushButton("全选")
        deselect_all_btn = QPushButton("取消全选")
        select_btns_layout = QHBoxLayout()
        select_btns_layout.addWidget(select_all_btn)
        select_btns_layout.addWidget(deselect_all_btn)
        layout.addLayout(select_btns_layout)
        
        # 创建复选框
        self.checkboxes = {}
        for column in columns:
            checkbox = QCheckBox(column)
            checkbox.setChecked(column in self.visible_columns)
            self.checkboxes[column] = checkbox
            scroll_layout.addWidget(checkbox)
        
        # 设置滚动区域
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # 创建确定和取消按钮
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        # 连接信号
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn.clicked.connect(self.deselect_all)
    
    def select_all(self):
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
    
    def deselect_all(self):
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
    
    def get_visible_columns(self):
        return [col for col, checkbox in self.checkboxes.items() if checkbox.isChecked()]

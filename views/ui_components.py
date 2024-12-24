from PySide6.QtWidgets import (QPushButton, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QFrame, QSpinBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import ui.styles

class UIComponentMixin:
    def create_circle_button(self, color):
        """创建圆形按钮"""
        button = QPushButton()
        button.setFixedSize(12, 12)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ui.styles.button_hover_color};
            }}
        """)
        return button

    def create_title_bar(self):
        """创建自定义标题栏"""
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet(f"""
            {ui.styles.candy_background}
            {ui.styles.common_font_style}
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon = QIcon("res/logo.ico")
        icon_label.setPixmap(icon.pixmap(20, 20))
        title_layout.addWidget(icon_label)
        title_layout.addSpacing(5)  # 添加一些间距
        
        # 添加标题
        self.title_label = QLabel("LovelyForm")
        self.title_label.setStyleSheet(ui.styles.common_font_style)
        title_layout.addWidget(self.title_label)
        
        # 添加文件名标签
        self.file_label = QLabel()
        self.file_label.setStyleSheet(f"""
            {ui.styles.common_font_style}
            color: #666666;
        """)
        title_layout.addWidget(self.file_label)
        
        title_layout.addStretch()
        
        return self.title_bar, title_layout

    def update_title(self, filename=None):
        """更新标题，包括文件名"""
        if filename:
            self.file_label.setText(f" - {filename}")
        else:
            self.file_label.setText("")

    def create_toolbar(self):
        """创建工具栏"""
        toolbar_group = QGroupBox("工具栏")
        toolbar_layout = QHBoxLayout()
        toolbar_group.setLayout(toolbar_layout)
        
        return toolbar_group, toolbar_layout

    def create_pagination_controls(self):
        """创建分页控件"""
        pagination_widget = QWidget()
        pagination_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("上一页")
        self.next_btn = QPushButton("下一页")
        self.page_label = QLabel("页码: 0/0")
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(10, 1000)
        self.page_size_spin.setValue(100)
        self.page_size_spin.setSingleStep(10)
        self.page_size_spin.setMinimumWidth(100)  # 设置最小宽度
        self.page_size_spin.setMaximumWidth(150)  # 设置最大宽度
        
        # 添加页码跳转控件
        self.page_jump_spin = QSpinBox()
        self.page_jump_spin.setRange(1, 1)
        self.page_jump_spin.setMinimumWidth(100)  # 设置最小宽度
        self.page_jump_spin.setMaximumWidth(150)  # 设置最大宽度
        self.page_jump_btn = QPushButton("跳转")
        
        pagination_layout.addWidget(QLabel("每页行数:"))
        pagination_layout.addWidget(self.page_size_spin)
        pagination_layout.addSpacing(20)  # 添加间距
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        pagination_layout.addWidget(QLabel("跳转到页码:"))
        pagination_layout.addWidget(self.page_jump_spin)
        pagination_layout.addWidget(self.page_jump_btn)
        
        pagination_widget.setLayout(pagination_layout)
        return pagination_widget

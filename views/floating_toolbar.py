from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QFrame, QHBoxLayout, QApplication)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPalette

class FloatingToolBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setParent(None)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.dragging = False
        self.offset = QPoint()
        
        # 设置固定宽度
        self.setFixedWidth(150)
        
        # 设置主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(2)
        
        # 创建标题栏
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 4, 8, 4)
        
        # 标题
        self.title_label = QLabel("全局工具")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        title_layout.addWidget(self.title_label)
        
        # 最小化按钮
        min_btn = QPushButton("-")
        min_btn.setFixedSize(20, 20)
        min_btn.clicked.connect(self.showMinimized)
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        title_layout.addWidget(min_btn)
        
        self.main_layout.addWidget(title_bar)
        
        # 创建内容区域
        self.content_frame = QFrame()
        self.content_frame.setFrameShape(QFrame.StyledPanel)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(6, 6, 6, 6)
        self.content_layout.setSpacing(6)
        self.main_layout.addWidget(self.content_frame)
        
        # 设置样式
        self.setStyleSheet("""
            FloatingToolBar {
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QFrame {
                background-color: transparent;
                border: none;
            }
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                color: #333;
                font-size: 12px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-color: #ccc;
            }
            QPushButton:pressed {
                background-color: #d8d8d8;
                border-color: #bbb;
            }
        """)
        
    def add_button(self, text, callback, tooltip=None):
        """添加按钮到工具栏"""
        button = QPushButton(text)
        if tooltip:
            button.setToolTip(tooltip)
        button.clicked.connect(callback)
        self.content_layout.addWidget(button)
        return button
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging:
            # 获取屏幕尺寸
            screen = QApplication.primaryScreen().geometry()
            # 计算新位置
            new_pos = event.globalPos() - self.offset
            # 确保窗口不会移出屏幕
            x = max(0, min(new_pos.x(), screen.width() - self.width()))
            y = max(0, min(new_pos.y(), screen.height() - self.height()))
            self.move(x, y)
            
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.setWindowOpacity(1.0)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.setWindowOpacity(0.8)

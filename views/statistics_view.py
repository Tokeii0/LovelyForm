from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                             QVBoxLayout, QLabel, QDialog)
from PySide6.QtCore import Qt
import pandas as pd

class StatisticsView(QDialog):
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.df = df
        self._init_ui()
        
    def _init_ui(self):
        self.setWindowTitle("数据统计结果")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 设置数据
        rows, cols = self.df.shape
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)
        
        # 设置表头
        self.table.setHorizontalHeaderLabels(self.df.columns)
        self.table.setVerticalHeaderLabels(self.df.index)
        
        # 填充数据
        for i in range(rows):
            for j in range(cols):
                value = self.df.iloc[i, j]
                if isinstance(value, float):
                    # 格式化浮点数，保留4位小数
                    item = QTableWidgetItem(f"{value:.4f}")
                else:
                    item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, j, item)
        
        # 设置表格样式
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                border: 1px solid #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
                border: none;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-right: 1px solid #d0d0d0;
                border-bottom: 1px solid #d0d0d0;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)
        
        # 添加说明标签
        info_label = QLabel("注：统计结果包含基本统计量和空值分析")
        info_label.setStyleSheet("""
            QLabel {
                color: #666;
                padding: 5px;
            }
        """)
        
        layout.addWidget(self.table)
        layout.addWidget(info_label)
        self.setLayout(layout)
        
        # 设置窗口大小和样式
        self.resize(1000, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 移除帮助按钮
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
        """)

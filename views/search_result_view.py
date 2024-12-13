from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QVBoxLayout)
from PySide6.QtCore import Qt, Signal

class SearchResultView(QGroupBox):
    # 定义双击信号
    item_double_clicked = Signal(int)  # 发送行号

    def __init__(self, parent=None):
        super().__init__("搜索结果", parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        
        # 创建搜索结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["行号", "列名", "内容"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # 设置表格样式
        self._setup_table_style()
        
        layout.addWidget(self.result_table)
        self.setLayout(layout)
        
        # 设置组框的最大高度
        self.setMaximumHeight(200)
        self.setVisible(False)

    def _setup_table_style(self):
        # 设置表格的固定高度
        self.result_table.setMinimumHeight(100)
        self.result_table.setMaximumHeight(150)

        # 设置表头左对齐
        self.result_table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 设置表格样式
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                border: 1px solid #d0d0d0;
            }
            QTableWidget::item {
                padding-left: 5px;
                padding-right: 5px;
                border: none;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding-left: 5px;
                padding-right: 5px;
                border: none;
                border-right: 1px solid #d0d0d0;
                border-bottom: 1px solid #d0d0d0;
            }
        """)
        
        # 设置行高
        self.result_table.verticalHeader().setDefaultSectionSize(24)
        self.result_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

    def _on_item_double_clicked(self, item):
        row = item.row()
        # 获取行号单元格的值并转换为整数
        row_num = int(self.result_table.item(row, 0).text())
        self.item_double_clicked.emit(row_num)

    def update_results(self, results):
        """更新搜索结果
        
        Args:
            results: List of tuples (row_num, col_name, value)
        """
        self.result_table.setRowCount(0)
        
        if not results:
            self.result_table.setRowCount(1)
            self.result_table.setSpan(0, 0, 1, 3)
            no_result_item = QTableWidgetItem("未找到匹配结果")
            no_result_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.result_table.setItem(0, 0, no_result_item)
            self.setVisible(True)
            return

        self.result_table.setRowCount(len(results))
        for i, (row_num, col_name, value) in enumerate(results):
            # 行号从1开始显示
            row_item = QTableWidgetItem(str(row_num + 1))
            col_item = QTableWidgetItem(col_name)
            value_item = QTableWidgetItem(str(value))
            
            # 设置对齐方式
            for item in (row_item, col_item, value_item):
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            self.result_table.setItem(i, 0, row_item)
            self.result_table.setItem(i, 1, col_item)
            self.result_table.setItem(i, 2, value_item)

        self.result_table.resizeColumnsToContents()
        self.setVisible(True)

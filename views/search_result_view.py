from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton,
                             QWidget, QStyledItemDelegate, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette

class TextItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() == 0:  # 行号列不可编辑
            return None
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.data(Qt.DisplayRole)
        if value is not None:
            editor.setText(str(value))
            editor.selectAll()

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class SearchResultView(QWidget):
    # 定义双击信号
    item_double_clicked = Signal(int)  # 发送行号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(1)

        # 创建标题栏布局
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加标题标签
        self.group_box = QGroupBox("搜索结果")
        
        # 添加关闭按钮
        close_button = QPushButton("×")
        close_button.setFixedSize(16, 16)
        close_button.clicked.connect(self.hide)
        title_layout.addWidget(self.group_box)
        title_layout.addWidget(close_button, 0, Qt.AlignTop)
        
        # 创建搜索结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["行号", "列名", "内容"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.verticalHeader().setVisible(False)
        
        # 设置自定义代理以处理编辑行为
        delegate = TextItemDelegate()
        self.result_table.setItemDelegate(delegate)
        
        # 设置表格样式
        self._setup_table_style()
        
        # 将表格添加到组框中
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(2, 2, 2, 2)
        group_layout.setSpacing(1)
        group_layout.addWidget(self.result_table)
        self.group_box.setLayout(group_layout)
        
        main_layout.addLayout(title_layout)
        self.setLayout(main_layout)
        
        # 设置组件的高度
        self.setMaximumHeight(220)
        self.setMinimumHeight(120)

    def _setup_table_style(self):
        # 设置表格的固定高度
        self.result_table.setMinimumHeight(100)
        self.result_table.setMaximumHeight(160)

        # 设置表头
        header = self.result_table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setHighlightSections(False)
        header.setMinimumSectionSize(40)
        header.setFixedHeight(20)
        
        # 使用系统主题色
        header.setAutoFillBackground(True)
        palette = self.palette()
        header.setPalette(palette)
        
        # 设置基本列宽
        self.result_table.setColumnWidth(0, 40)  # 行号列
        self.result_table.setColumnWidth(1, 120)  # 列名列
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 内容列自动拉伸
        
        # 设置表格属性
        self.result_table.setEditTriggers(QTableWidget.DoubleClicked)  # 只允许双击触发编辑
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setWordWrap(True)  # 允许文本换行
        
        # 设置行高自适应
        self.result_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # 连接双击信号
        self.result_table.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _on_item_double_clicked(self, item):
        """处理双击事件"""
        row = item.row()
        # 获取行号单元格中的值（需要减1因为显示时加了1）
        row_num = int(self.result_table.item(row, 0).text()) - 1
        self.item_double_clicked.emit(row_num)

    def update_results(self, results):
        """更新搜索结果"""
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
            
            # 设置行号列为不可编辑
            row_item.setFlags(row_item.flags() & ~Qt.ItemIsEditable)
            
            # 设置单元格
            self.result_table.setItem(i, 0, row_item)
            self.result_table.setItem(i, 1, col_item)
            self.result_table.setItem(i, 2, value_item)
        
        # 调整列宽以适应内容
        self.result_table.resizeColumnsToContents()
        
        # 设置最小和最大列宽限制
        if self.result_table.columnWidth(0) > 60:
            self.result_table.setColumnWidth(0, 60)
        if self.result_table.columnWidth(1) > 150:
            self.result_table.setColumnWidth(1, 150)
        
        self.setVisible(True)

    def clear(self):
        """清空搜索结果"""
        self.result_table.setRowCount(0)
        self.setVisible(False)

    def changeEvent(self, event):
        """处理主题变化事件"""
        if event.type() == event.Type.PaletteChange:
            # 更新表头调色板
            header = self.result_table.horizontalHeader()
            header.setPalette(self.palette())
        super().changeEvent(event)

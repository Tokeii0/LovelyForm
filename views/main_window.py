from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QLabel, QSpinBox, QTableView,
                             QHeaderView, QMessageBox, QMenu, QFileDialog, QToolBar,
                             QCheckBox, QInputDialog, QDialog, QGroupBox)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QAction
import pandas as pd
import numpy as np
import os
from models.table_model import PandasModel
from views.search_result_view import SearchResultView
from views.statistics_view import StatisticsView
from plugins.plugin_manager import PluginManager
from plugins import CellPlugin

class CSVViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LovelyForm")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化数据
        self.df = pd.DataFrame()
        self.current_page = 0
        self.page_size = 100
        self.proxy_model = QSortFilterProxyModel()
        
        # 初始化分页控件
        self.prev_btn = None
        self.next_btn = None
        self.page_label = None
        self.page_size_spin = None
        
        self.plugin_manager = PluginManager()
        
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 工具栏区域
        toolbar_group = QGroupBox("工具栏")
        toolbar_layout = QHBoxLayout()
        toolbar_group.setLayout(toolbar_layout)
        
        # 文件操作按钮
        load_btn = QPushButton("打开文件")
        load_btn.setMinimumWidth(80)
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        load_btn.clicked.connect(self.load_csv)
        toolbar_layout.addWidget(load_btn)
        
        save_btn = QPushButton("保存文件")
        save_btn.setMinimumWidth(80)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #008CBA;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #007399;
            }
        """)
        save_btn.clicked.connect(self.save_csv)
        toolbar_layout.addWidget(save_btn)
        
        # 命令配置按钮
        command_btn = QPushButton("命令配置")
        command_btn.setMinimumWidth(80)
        command_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        command_btn.clicked.connect(self.show_command_config)
        toolbar_layout.addWidget(command_btn)
        
        # 搜索区域
        toolbar_layout.addSpacing(20)  # 添加一些间距
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        toolbar_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("搜索")
        search_btn.setMinimumWidth(60)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        search_btn.clicked.connect(self.search_table)
        toolbar_layout.addWidget(search_btn)
        
        # 隐藏空白列复选框
        toolbar_layout.addSpacing(20)
        self.hide_empty_checkbox = QCheckBox("隐藏空白列")
        self.hide_empty_checkbox.stateChanged.connect(self.on_hide_empty_changed)
        toolbar_layout.addWidget(self.hide_empty_checkbox)
        
        toolbar_layout.addStretch()  # 添加弹性空间
        
        # 添加工具栏到主布局
        layout.addWidget(toolbar_group)
        
        # 表格视图
        self.table_view = QTableView()
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.create_context_menu)
        self.proxy_model = QSortFilterProxyModel()
        self.table_view.setModel(self.proxy_model)
        
        # 设置表格样式
        self.table_view.setStyleSheet("""
            QTableView {
                gridline-color: #d0d0d0;
                border: 1px solid #d0d0d0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-right: 1px solid #d0d0d0;
                border-bottom: 1px solid #d0d0d0;
            }
        """)
        
        # 设置表头样式
        header = self.table_view.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionsMovable(True)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        layout.addWidget(self.table_view)
        
        # 分页控件
        self._init_pagination(layout)
        
        # 搜索结果视图
        self.search_view = SearchResultView(self)
        self.search_view.item_double_clicked.connect(self.jump_to_result)
        layout.addWidget(self.search_view)

    def _init_pagination(self, layout):
        page_control = QHBoxLayout()
        
        # 添加全局插件工具栏
        plugin_toolbar = QToolBar()
        plugin_toolbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                padding: 0 5px;
            }
            QToolButton {
                background-color: #673AB7;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                min-width: 80px;
            }
            QToolButton:hover {
                background-color: #5E35B1;
            }
        """)
        
        for name, plugin_class in self.plugin_manager.get_table_plugins().items():
            plugin = plugin_class()
            action = QAction(plugin.button_text, self)
            action.setToolTip(plugin.description)
            action.triggered.connect(lambda checked, p=plugin: self.handle_table_plugin(p))
            plugin_toolbar.addAction(action)
        page_control.addWidget(plugin_toolbar)
        
        page_control.addStretch()  # 添加弹性空间，使后面的控件靠右
        
        # 每页显示数量
        page_control.addWidget(QLabel("每页行数:"))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(10, 1000)
        self.page_size_spin.setValue(self.page_size)
        self.page_size_spin.valueChanged.connect(self.update_page_size)
        page_control.addWidget(self.page_size_spin)
        
        # 翻页按钮
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.clicked.connect(self.prev_page)
        page_control.addWidget(self.prev_btn)
        
        # 页码显示
        self.page_label = QLabel("页码: 1")
        page_control.addWidget(self.page_label)
        
        self.next_btn = QPushButton("下一页")
        self.next_btn.clicked.connect(self.next_page)
        page_control.addWidget(self.next_btn)
        
        layout.addLayout(page_control)

    def load_csv(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "打开CSV文件",
            "",
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if filename:
            try:
                # 记录当前文件名
                self.current_file = filename
                
                # 使用分块读取大文件
                self.df = pd.read_csv(filename, chunksize=None)
                self.current_page = 0
                self.update_table()
                
                # 更新窗口标题
                self.setWindowTitle(f"CSV查看器 - {os.path.basename(filename)}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法加载文件：{str(e)}")

    def save_csv(self):
        if self.df.empty:
            return
        
        file_name, _ = QFileDialog.getSaveFileName(
            self, "保存CSV文件", "", "CSV文件 (*.csv);;所有文件 (*.*)")
        if file_name:
            try:
                self.df.to_csv(file_name, index=False)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存CSV文件时出错: {str(e)}")

    def update_table(self):
        """更新表格显示"""
        if self.df.empty:
            return
            
        # 计算当前页的数据范围
        start = self.current_page * self.page_size
        end = min(start + self.page_size, len(self.df))
        
        # 更新模型
        current_df = self.df.iloc[start:end]
        model = PandasModel(current_df)
        self.proxy_model.setSourceModel(model)
        self.table_view.setModel(self.proxy_model)
        
        # 如果需要隐藏空白列
        if self.hide_empty_checkbox.isChecked():
            self.hide_empty_columns(current_df)
            
        # 调整列宽
        self.adjust_column_widths()
        
        # 更新分页状态
        total_pages = (len(self.df) - 1) // self.page_size + 1
        self.page_label.setText(f"页码: {self.current_page + 1}/{total_pages}")
        
        # 更新按钮状态
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

    def hide_empty_columns(self, df):
        """隐藏空白列"""
        for column in df.columns:
            is_empty = df[column].isna().all() or \
                      (df[column].astype(str).str.strip() == '').all()
            if is_empty:
                col_index = df.columns.get_loc(column)
                self.table_view.hideColumn(col_index)
            else:
                col_index = df.columns.get_loc(column)
                self.table_view.showColumn(col_index)

    def adjust_column_widths(self):
        """自适应列宽，根据每列内容的最大宽度来设置"""
        header = self.table_view.horizontalHeader()
        
        # 获取表格的字体度量对象
        font_metrics = self.table_view.fontMetrics()
        
        for column in range(self.proxy_model.columnCount()):
            # 获取列头文本宽度
            header_text = self.proxy_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
            max_width = font_metrics.horizontalAdvance(str(header_text)) + 20  # 添加一些边距
            
            # 遍历该列的所有行，找出最长的内容
            for row in range(self.proxy_model.rowCount()):
                index = self.proxy_model.index(row, column)
                content = str(self.proxy_model.data(index, Qt.DisplayRole))
                content_width = font_metrics.horizontalAdvance(content) + 20  # 添加一些边距
                max_width = max(max_width, content_width)
            
            # 限制最大宽度，避免过宽
            max_width = min(max_width, 300)  # 最大宽度限制为300像素
            
            # 确保最小宽度不小于50像素
            max_width = max(max_width, 50)
            
            # 设置列宽
            self.table_view.setColumnWidth(column, max_width)
            
            # 设置列可以调整大小
            header.setSectionResizeMode(column, QHeaderView.Interactive)

    def on_hide_empty_changed(self, state):
        """空白列隐藏状态改变时的处理函数"""
        self.update_table()

    def search_table(self):
        search_text = self.search_input.text().strip()
        if not search_text or self.df.empty:
            self.search_view.setVisible(False)
            return

        results = []
        for col in self.df.columns:
            # 将列转换为字符串类型进行搜索
            mask = self.df[col].astype(str).str.contains(search_text, case=False, na=False)
            matches = self.df[mask]
            
            for idx, value in matches[col].items():
                # 行号从0开始，但显示时从1开始
                results.append((idx, col, str(value)))

        self.search_view.update_results(results)

    def create_context_menu(self, pos):
        menu = QMenu(self)
        
        # 获取选中的单元格
        indexes = self.table_view.selectedIndexes()
        if not indexes:
            return
            
        # 获取当前文件名
        current_file = getattr(self, 'current_file', '')
        
        # 获取选中的列名
        selected_columns = set()
        model = self.table_view.model()
        for index in indexes:
            col_index = index.column()
            col_name = model.headerData(col_index, Qt.Horizontal, Qt.DisplayRole)
            selected_columns.add(col_name)
        
        # 添加插件菜单项
        plugins_added = False
        for plugin_name, plugin_class in self.plugin_manager.get_cell_plugins().items():
            # 如果是命令执行插件，plugin_class 已经是实例了，不需要再实例化
            if isinstance(plugin_class, CellPlugin):
                plugin = plugin_class
            else:
                plugin = plugin_class()
            
            # 检查文件名是否匹配
            if not plugin.match_file(os.path.basename(current_file)):
                continue
                
            # 检查是否至少有一个选中的列匹配插件的列名模式
            if not any(plugin.match_column(col_name) for col_name in selected_columns):
                continue
            
            # 创建菜单项
            action = QAction(plugin.name, menu)
            action.setStatusTip(plugin.description)
            action.triggered.connect(lambda checked, p=plugin: self.handle_cell_plugin(p))
            menu.addAction(action)
            plugins_added = True
            
        # 如果没有添加任何插件，显示提示信息
        if not plugins_added:
            action = QAction("没有可用的插件", menu)
            action.setEnabled(False)
            menu.addAction(action)
            
        menu.exec_(self.table_view.viewport().mapToGlobal(pos))
        
    def show_plugin_config(self, plugin):
        """显示插件配置对话框"""
        if hasattr(plugin, 'show_config_dialog'):
            dialog = plugin.show_config_dialog(self)
            dialog.exec_()
            
    def handle_cell_plugin(self, plugin):
        # 处理选中的单元格
        indexes = self.table_view.selectedIndexes()
        if not hasattr(self, 'df') or not indexes:
            return
            
        # 过滤出匹配列名模式的单元格
        filtered_cells = []
        model = self.table_view.model()
        for index in indexes:
            col_index = index.column()
            col_name = model.headerData(col_index, Qt.Horizontal, Qt.DisplayRole)
            if plugin.match_column(col_name):
                filtered_cells.append((index.row(), col_index))
                
        if filtered_cells:
            self.df = plugin.process_cells(self.df, filtered_cells)
            self.update_table()
            
    def handle_table_plugin(self, plugin):
        # 处理整个表格
        if hasattr(self, 'df'):
            result = plugin.process_table(self.df)
            # 在新窗口中显示结果
            if isinstance(result, pd.DataFrame):
                dialog = StatisticsView(result, self)
                dialog.exec_()
            else:
                QMessageBox.information(self, "处理结果", str(result))

    def jump_to_result(self, row_num):
        """跳转到搜索结果所在行
        
        Args:
            row_num: 实际的行号（从1开始）
        """
        # 将行号转换为0基索引
        row_index = row_num - 1
        
        # 计算目标页码
        target_page = row_index // self.page_size
        
        # 如果页码发生变化，更新当前页
        if target_page != self.current_page:
            self.current_page = target_page
            self.update_table()
        
        # 计算在当前页中的相对行号
        relative_row = row_index % self.page_size
        
        # 选中并滚动到目标行
        self.table_view.selectRow(relative_row)
        self.table_view.scrollTo(
            self.table_view.model().index(relative_row, 0),
            QTableView.PositionAtCenter
        )

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        total_pages = (len(self.df) - 1) // self.page_size + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_table()

    def update_page_size(self):
        self.page_size = self.page_size_spin.value()
        self.current_page = 0  # 重置到第一页
        self.update_table()

    def show_command_config(self):
        """显示命令配置对话框"""
        from plugins.command_executor import CommandConfigDialog
        dialog = CommandConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 重新加载插件以更新命令
            self.plugin_manager.load_plugins()

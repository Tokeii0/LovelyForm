from PySide6.QtWidgets import (QTableView, QHeaderView, QMessageBox, QMenu,
                             QLineEdit, QVBoxLayout, QDialog, QPushButton, QHBoxLayout, QWidget, QLabel, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from lovelyform.models.table_model import PandasModel
from lovelyform.plugins import CellPlugin
from lovelyform.views.statistics_view import StatisticsView
from lovelyform.views.column_visibility_dialog import ColumnVisibilityDialog
from lovelyform.models.item_delegate import TableItemDelegate
import pandas as pd
import ui.styles
import os

class TableOperationsMixin:
    def setup_table_view(self):
        """设置表格视图"""
        # 创建搜索框和表格的容器
        self.table_container = QWidget()
        main_layout = QVBoxLayout(self.table_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建工具栏布局
        toolbar_layout = QHBoxLayout()
        
        # 创建列显示控制按钮
        self.column_visibility_btn = QPushButton("列显示设置")
        self.column_visibility_btn.clicked.connect(self.show_column_visibility_dialog)
        toolbar_layout.addWidget(self.column_visibility_btn)
        
        # 创建搜索框
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索内容...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        
        # 创建列选择下拉框
        self.column_combo = QComboBox()
        self.column_combo.addItem("全部列")
        self.column_combo.currentIndexChanged.connect(self.on_search_column_changed)
        
        search_layout.addWidget(QLabel("搜索列:"))
        search_layout.addWidget(self.column_combo)
        search_layout.addWidget(self.search_input)
        
        toolbar_layout.addLayout(search_layout)
        
        main_layout.addLayout(toolbar_layout)
        
        # 创建表格视图
        self.table_view = QTableView()
        main_layout.addWidget(self.table_view)
        
        # 创建并设置数据模型
        self.data_model = PandasModel(pd.DataFrame())
        self.proxy_model.setSourceModel(self.data_model)
        
        self.table_view.setModel(self.proxy_model)
        self.table_view.setAlternatingRowColors(False)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.create_context_menu)
        
        # 设置自定义的ItemDelegate
        self.table_view.setItemDelegate(TableItemDelegate())
        
        # 启用手动排序功能
        self.table_view.setSortingEnabled(True)
        self.proxy_model.setDynamicSortFilter(False)  # 禁用动态排序
        self.table_view.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        
        # 添加列宽调整标志
        self._column_widths_adjusted = False
        # 连接列宽变化信号
        self.table_view.horizontalHeader().sectionResized.connect(self._on_column_resized)
        
        # 设置表头右键菜单
        self.table_view.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.horizontalHeader().customContextMenuRequested.connect(self.show_header_menu)
        
        # 设置表格样式
        self.update_table_style()
        
        # 返回表格视图和容器
        return self.table_view, self.table_container

    def update_table_style(self):
        """更新表格样式"""
        self.table_view.setStyleSheet(f"""
            {ui.styles.candy_background}
            {ui.styles.common_font_style}
            border: 1px solid #ccc;
            border-radius: 4px;
            
            QHeaderView::section {{
                background-color: white;
                color: black;
                padding: 4px;
                border: 1px solid #ccc;
            }}
            
            QTableView QTableCornerButton::section {{
                background-color: white;
                border: 1px solid #ccc;
            }}
        """)

    def update_table(self):
        """更新表格显示"""
        if self.data_manager is None or self.data_manager.df is None or self.data_manager.df.empty:
            return
            
        # 清除当前选择状态
        self.table_view.clearSelection()
            
        # 计算当前页的数据范围
        page_size = self.page_size_spin.value() if hasattr(self, 'page_size_spin') else self.page_size
        start = self.current_page * page_size
        end = min(start + page_size, len(self.data_manager.df))
        
        # 更新模型，传入页面偏移量
        current_df = self.data_manager.df.iloc[start:end]
        model = PandasModel(current_df, page_offset=start)
        self.proxy_model.setSourceModel(model)
        
        # 更新列选择下拉框
        self.column_combo.blockSignals(True)
        self.column_combo.clear()
        self.column_combo.addItem("全部列")
        for col in range(model.columnCount()):
            self.column_combo.addItem(model.headerData(col, Qt.Horizontal))
        self.column_combo.blockSignals(False)
        
        # 确保所有列都是可见的
        for i in range(model.columnCount()):
            self.table_view.showColumn(i)
        
        # 处理隐藏空白列
        if hasattr(self, 'hide_empty_checkbox') and self.hide_empty_checkbox.isChecked():
            self.hide_empty_columns()
            
        # 只在第一次加载时自动调整列宽
        if not self._column_widths_adjusted:
            self.adjust_column_widths()
        
        # 更新分页状态
        total_pages = (len(self.data_manager.df) - 1) // page_size + 1
        self.update_page_label()
        
        # 更新按钮状态
        if hasattr(self, 'prev_btn'):
            self.prev_btn.setEnabled(self.current_page > 0)
        if hasattr(self, 'next_btn'):
            self.next_btn.setEnabled(self.current_page < total_pages - 1)

    def hide_empty_columns(self):
        """隐藏空白列"""
        source_model = self.proxy_model.sourceModel()
        last_visible_column = -1
        
        # 首先隐藏空白列并记录最后一个可见列
        for col in range(source_model.columnCount()):
            is_empty = True
            for row in range(source_model.rowCount()):
                value = source_model.data(source_model.index(row, col), Qt.DisplayRole)
                if value and str(value).strip():
                    is_empty = False
                    break
            
            if is_empty:
                self.table_view.hideColumn(col)
            else:
                self.table_view.showColumn(col)
                last_visible_column = col
        
        # 设置最后一个可见列为Stretch模式
        if last_visible_column >= 0:
            header = self.table_view.horizontalHeader()
            # 先将所有列设置为Interactive模式
            for col in range(source_model.columnCount()):
                header.setSectionResizeMode(col, QHeaderView.Interactive)
            # 将最后一个可见列设置为Stretch模式
            header.setSectionResizeMode(last_visible_column, QHeaderView.Stretch)

    def adjust_column_widths(self):
        """自适应列宽"""
        header = self.table_view.horizontalHeader()
        font_metrics = self.table_view.fontMetrics()
        
        for column in range(self.proxy_model.columnCount()):
            header_text = self.proxy_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
            max_width = font_metrics.horizontalAdvance(str(header_text)) + 20
            
            for row in range(self.proxy_model.rowCount()):
                index = self.proxy_model.index(row, column)
                content = str(self.proxy_model.data(index, Qt.DisplayRole))
                content_width = font_metrics.horizontalAdvance(content) + 20
                max_width = max(max_width, content_width)
            
            max_width = min(max(max_width, 50), 300)
            self.table_view.setColumnWidth(column, max_width)
            header.setSectionResizeMode(column, QHeaderView.Interactive)

    def on_sort_changed(self, logical_index, order):
        """处理排序变化"""
        if self.data_manager.df.empty:
            return
            
        column_name = self.data_manager.df.columns[logical_index]
        if not column_name:
            return
            
        ascending = order == Qt.AscendingOrder
        self.status_bar.showMessage(f"正在排序 {column_name} 列...")
        
        try:
            # 对整个数据集进行排序
            sorted_df = self.data_manager.df.sort_values(by=column_name, ascending=ascending)
            # 重置索引，这样DataFrame的顺序将与显示顺序一致
            self.data_manager.df = sorted_df.reset_index(drop=True)
            
            # 重置到第一页
            self.current_page = 0
            
            # 更新显示
            self.update_table()
            
            # 更新分页控件
            self.update_page_label()
            if hasattr(self, 'prev_btn'):
                self.prev_btn.setEnabled(False)  # 回到第一页，禁用上一页按钮
            if hasattr(self, 'next_btn'):
                total_pages = (len(self.data_manager.df) - 1) // self.page_size + 1
                self.next_btn.setEnabled(total_pages > 1)
            
            self.status_bar.showMessage(f"排序完成：{column_name} 列 {'升序' if ascending else '降序'}", 3000)
            
        except Exception as e:
            self.status_bar.showMessage(f"排序失败：{str(e)}", 3000)

    def create_context_menu(self, pos):
        """创建右键菜单"""
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
        
        # 重新加载插件
        self.plugin_manager.load_plugins()
        
        # 获取按分类组织的插件
        plugins_by_category = self.plugin_manager.get_cell_plugins_by_category()
        
        # 添加插件菜单项
        plugins_added = False
        
        # 首先添加未分类的插件
        uncategorized_plugins = {}
        for plugin_name, plugin_class in self.plugin_manager.get_cell_plugins().items():
            # 跳过已经分类的插件
            skip = False
            for category_plugins in plugins_by_category.values():
                if plugin_name in category_plugins:
                    skip = True
                    break
            if skip:
                continue
                
            # 如果是命令执行插件，plugin_class 已经是实例了，不需要再实例化
            if isinstance(plugin_class, CellPlugin):
                plugin = plugin_class
            else:
                plugin = plugin_class()
                
            # 检查文件名是否匹配
            if not plugin.match_file(os.path.basename(current_file)):
                continue
            
            # 检查是否有任何选中的列可以使用此插件
            valid_columns = False
            for col_name in selected_columns:
                if plugin.match_column(col_name):
                    valid_columns = True
                    break
                    
            if not valid_columns:
                continue
                
            uncategorized_plugins[plugin_name] = plugin
            
        # 添加未分类的插件到主菜单
        if uncategorized_plugins:
            for plugin_name, plugin in uncategorized_plugins.items():
                action = QAction(plugin.name, menu)
                action.setStatusTip(plugin.description)
                action.triggered.connect(lambda checked, p=plugin: self.handle_cell_plugin(p))
                menu.addAction(action)
                plugins_added = True
                
        # 如果有未分类插件和分类插件,添加分隔符
        if uncategorized_plugins and plugins_by_category:
            menu.addSeparator()
            
        # 添加分类的插件到子菜单
        for category, category_plugins in plugins_by_category.items():
            # 创建子菜单
            submenu = QMenu(category, menu)
            valid_plugins = False
            
            for plugin_name, plugin in category_plugins.items():
                # 检查文件名是否匹配
                if not plugin.match_file(os.path.basename(current_file)):
                    continue
                
                # 检查是否有任何选中的列可以使用此插件
                valid_columns = False
                for col_name in selected_columns:
                    if plugin.match_column(col_name):
                        valid_columns = True
                        break
                        
                if not valid_columns:
                    continue
                    
                # 创建菜单项
                action = QAction(plugin.name, submenu)
                action.setStatusTip(plugin.description)
                action.triggered.connect(lambda checked, p=plugin: self.handle_cell_plugin(p))
                submenu.addAction(action)
                valid_plugins = True
                plugins_added = True
                
            # 只有当子菜单中有有效插件时才添加到主菜单
            if valid_plugins:
                menu.addMenu(submenu)
            
        # 如果没有添加任何插件，显示提示信息
        if not plugins_added:
            action = QAction("没有可用的插件", menu)
            action.setEnabled(False)
            menu.addAction(action)
            
        menu.exec_(self.table_view.viewport().mapToGlobal(pos))

    def handle_cell_plugin(self, plugin):
        """处理单元格插件"""
        # 处理选中的单元格
        if not hasattr(self, 'data_manager') or not hasattr(self, 'table_view'):
            return
            
        if self.data_manager is None or self.data_manager.df is None:
            return
            
        indexes = self.table_view.selectedIndexes()
        if not indexes:
            return
            
        # 过滤出匹配列名模式的单元格
        filtered_cells = []
        proxy_model = self.table_view.model()
        source_model = proxy_model.sourceModel()
        if source_model is None:
            return
            
        # 获取当前页的偏移量
        page_size = self.page_size_spin.value() if hasattr(self, 'page_size_spin') else self.page_size
        page_offset = self.current_page * page_size
            
        for index in indexes:
            # 将代理模型的索引转换为源模型的索引
            source_index = proxy_model.mapToSource(index)
            col_index = source_index.column()
            col_name = source_model.headerData(col_index, Qt.Horizontal, Qt.DisplayRole)
            if plugin.match_column(col_name):
                # 使用源模型的行索引加上页面偏移量
                absolute_row = source_index.row() + page_offset
                filtered_cells.append((absolute_row, col_index))
                
        if filtered_cells:
            try:
                result = plugin.process_cells(self.data_manager.df, filtered_cells)
                if result is not None:
                    self.data_manager.df = result
                self.update_table()
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "插件执行错误",
                    f"执行插件时发生错误：{str(e)}",
                    QMessageBox.Ok
                )

    def handle_table_plugin(self, plugin):
        """处理表格插件"""
        if hasattr(self, 'data_manager'):
            result = plugin.process_table(self.data_manager.df)
            # 在新窗口中显示结果
            if isinstance(result, pd.DataFrame):
                dialog = StatisticsView(result, self)
                dialog.exec_()
            else:
                QMessageBox.information(self, "处理结果", str(result))

    def show_header_menu(self, pos):
        """显示表头右键菜单"""
        header = self.table_view.horizontalHeader()
        column = header.logicalIndexAt(pos)
        if column < 0:
            return
            
        menu = QMenu(self)
        filter_action = QAction("筛选", menu)
        filter_action.triggered.connect(lambda: self.show_filter_dialog(column))
        menu.addAction(filter_action)
        
        clear_filter_action = QAction("清除筛选", menu)
        clear_filter_action.triggered.connect(lambda: self.clear_filter(column))
        menu.addAction(clear_filter_action)
        
        menu.exec_(header.viewport().mapToGlobal(pos))

    def show_filter_dialog(self, column):
        """显示筛选对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("筛选")
        layout = QVBoxLayout()
        
        # 获取列名
        column_name = self.proxy_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
        
        # 创建筛选输入框
        filter_input = QLineEdit()
        filter_input.setPlaceholderText(f"输入要筛选的{column_name}值...")
        layout.addWidget(filter_input)
        
        # 创建确定和取消按钮
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        ok_button.clicked.connect(lambda: self.apply_filter(column, filter_input.text(), dialog))
        cancel_button.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
        
    def apply_filter(self, column, filter_text, dialog):
        """应用筛选"""
        if not filter_text:
            self.clear_filter(column)
            dialog.accept()
            return
            
        try:
            # 获取列名
            column_name = self.proxy_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
            
            # 应用筛选
            self.proxy_model.setFilterKeyColumn(column)
            self.proxy_model.setFilterFixedString(filter_text)  # 使用setFilterFixedString替代setFilterRegExp
            
            # 更新状态栏
            self.status_bar.showMessage(f"筛选开始...")
            dialog.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"应用筛选时出错：{str(e)}")
            
    def clear_filter(self, column):
        """清除筛选"""
        self.proxy_model.setFilterKeyColumn(column)
        self.proxy_model.setFilterFixedString("")  # 使用setFilterFixedString替代setFilterRegExp
        self.status_bar.showMessage("筛选结束")

    def _on_column_resized(self, logical_index, old_size, new_size):
        """处理列宽调整事件"""
        self._column_widths_adjusted = True

    def on_search_text_changed(self, text):
        """处理搜索文本变化"""
        if not text:
            self.proxy_model.setFilterFixedString("")
            self.status_bar.showMessage("已清除筛选", 3000)  # 显示3秒后消失
            return
            
        self.status_bar.showMessage("正在筛选...")
        selected_column = self.column_combo.currentText()
        source_model = self.proxy_model.sourceModel()
        
        if selected_column == "全部列":
            # 搜索所有列
            self.proxy_model.setFilterKeyColumn(-1)
        else:
            # 获取列索引
            for col in range(source_model.columnCount()):
                if source_model.headerData(col, Qt.Horizontal) == selected_column:
                    self.proxy_model.setFilterKeyColumn(col)
                    break
                    
        self.proxy_model.setFilterFixedString(text)
        
        # 计算匹配的行数
        matched_rows = self.proxy_model.rowCount()
        total_rows = source_model.rowCount()
        self.status_bar.showMessage(f"筛选完成：显示 {matched_rows}/{total_rows} 行")
        
    def on_search_column_changed(self, index):
        """处理搜索列变化"""
        # 重新应用当前的搜索文本
        self.on_search_text_changed(self.search_input.text())

    def show_column_visibility_dialog(self):
        """显示列可见性设置对话框"""
        if not hasattr(self, 'proxy_model') or not self.proxy_model.sourceModel():
            QMessageBox.warning(self, "警告", "请先加载数据")
            return
            
        source_model = self.proxy_model.sourceModel()
        if source_model.rowCount() == 0:
            QMessageBox.warning(self, "警告", "请先加载数据")
            return
            
        # 获取所有列
        columns = [source_model.headerData(i, Qt.Horizontal, Qt.DisplayRole) 
                  for i in range(source_model.columnCount())]
                  
        # 获取当前可见列
        visible_columns = []
        for i in range(source_model.columnCount()):
            if not self.table_view.isColumnHidden(i):
                visible_columns.append(columns[i])
        
        # 创建并显示对话框
        dialog = ColumnVisibilityDialog(columns, visible_columns, self)
        if dialog.exec_():
            # 获取用户选择的可见列
            visible_columns = dialog.get_visible_columns()
            
            # 更新列的可见性
            for i, column in enumerate(columns):
                self.table_view.setColumnHidden(i, column not in visible_columns)

    def on_header_clicked(self, logical_index):
        """处理表头点击事件"""
        # 获取当前排序状态
        order = self.table_view.horizontalHeader().sortIndicatorOrder()
        # 获取当前排序列
        current_sort_column = self.table_view.horizontalHeader().sortIndicatorSection()
        
        # 如果点击的列是当前排序列，则切换排序顺序
        if logical_index == current_sort_column:
            if order == Qt.AscendingOrder:
                order = Qt.DescendingOrder
            else:
                order = Qt.AscendingOrder
        # 否则，设置新的排序列和顺序
        else:
            order = Qt.AscendingOrder
        
        # 更新排序状态
        self.table_view.horizontalHeader().setSortIndicator(logical_index, order)
        
        # 触发排序变化事件
        self.on_sort_changed(logical_index, order)

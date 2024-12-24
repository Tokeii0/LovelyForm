from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox,
                             QMessageBox, QMenu, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

class SearchFilterMixin:
    def search_table(self):
        """搜索表格内容"""
        if not hasattr(self, 'data_manager') or self.data_manager.df.empty:
            return
            
        search_text = self.global_search_input.text().strip()
        if not search_text:
            return
            
        try:
            self.status_bar.showMessage("正在搜索...")
            results = []
            total_rows = len(self.data_manager.df)
            
            # 更新进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, total_rows)
            self.progress_bar.setValue(0)
            
            for idx, row in enumerate(self.data_manager.df.itertuples()):
                if idx % 100 == 0:
                    self.progress_bar.setValue(idx)
                    QApplication.processEvents()
                
                for col_idx, val in enumerate(row[1:]):
                    if search_text.lower() in str(val).lower():
                        col_name = self.data_manager.df.columns[col_idx]
                        results.append((idx, col_name, val))
            
            self.progress_bar.setVisible(False)
            
            # 显示搜索结果
            self.search_result_view.update_results(results)
            self.status_bar.showMessage(f"搜索完成：找到 {len(results)} 个匹配项")
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.warning(self, "搜索错误", f"搜索时发生错误：{str(e)}")
            self.status_bar.showMessage("搜索出错")

    def show_filter_dialog(self, column):
        """显示筛选对话框"""
        if not hasattr(self, 'data_manager') or self.data_manager.df.empty:
            return
            
        column_name = self.data_manager.df.columns[column]
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"列筛选 - {column_name}")
        layout = QVBoxLayout()
        
        filter_input = QLineEdit()
        filter_input.setPlaceholderText("输入筛选条件，只显示当前列中匹配的行...")
        layout.addWidget(filter_input)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            filter_text = filter_input.text().strip()
            if filter_text:
                self.apply_filter(column, filter_text)

    def apply_filter(self, column, filter_text):
        """应用筛选条件"""
        if not hasattr(self, 'data_manager') or self.data_manager.df.empty:
            return
            
        column_name = self.data_manager.df.columns[column]
        try:
            mask = self.data_manager.df[column_name].astype(str).str.contains(filter_text, case=False, na=False)
            self.proxy_model.setFilterKeyColumn(column)
            self.proxy_model.setFilterRegExp(filter_text)
            
            matched_count = mask.sum()
            self.status_bar.showMessage(f"筛选 {column_name}: 匹配 {matched_count} 行")
            
        except Exception as e:
            QMessageBox.warning(self, "筛选错误", str(e))

    def clear_filter(self, column):
        """清除筛选条件"""
        if hasattr(self, 'proxy_model'):
            self.proxy_model.setFilterRegExp("")
            self.status_bar.showMessage("已清除筛选", 3000)

    def show_header_menu(self, pos):
        """显示列头的上下文菜单"""
        if not self.enable_filter_checkbox.isChecked():
            return
            
        header = self.table_view.horizontalHeader()
        column = header.logicalIndexAt(pos)
        
        if column < 0:
            return
            
        column_name = self.table_view.model().headerData(column, Qt.Horizontal, Qt.DisplayRole)
        
        menu = QMenu(self)
        
        filter_action = QAction("设置筛选条件", menu)
        filter_action.triggered.connect(lambda: self.show_filter_dialog(column))
        menu.addAction(filter_action)
        
        clear_action = QAction("清除筛选", menu)
        clear_action.triggered.connect(lambda: self.clear_filter(column))
        menu.addAction(clear_action)
        
        menu.exec_(header.mapToGlobal(pos))

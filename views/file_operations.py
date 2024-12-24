from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import Qt

class FileOperationsMixin:
    def load_csv_file(self, file_path=None):
        """加载CSV文件"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择CSV文件", "", "CSV files (*.csv)"
            )
            if not file_path:
                return

        self.current_file = file_path
        self.status_bar.showMessage(f"正在加载文件: {file_path}")
        
        # 启动加载线程
        load_thread = self.data_manager.load_csv(file_path)
        load_thread.progress.connect(self.update_load_progress)
        load_thread.error.connect(self.show_error_message)
        load_thread.finished.connect(self.on_load_completed)
        load_thread.start()

    def update_load_progress(self, progress):
        """更新加载进度"""
        self.status_bar.showMessage(f"正在加载文件: {progress}%")

    def show_error_message(self, error):
        """显示错误消息"""
        QMessageBox.critical(self, "错误", f"加载文件时发生错误: {error}")
        self.status_bar.showMessage("加载失败")

    def on_load_completed(self):
        """文件加载完成时的处理"""
        self.status_bar.showMessage("文件加载完成")
        self.current_page = 0
        self.update_table()
        self.update_page_jump_range()

    def save_csv(self):
        """保存CSV文件"""
        if not hasattr(self, 'data_manager') or self.data_manager.df.empty:
            QMessageBox.warning(self, "警告", "没有数据可以保存")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存CSV文件", "", "CSV files (*.csv)"
        )
        
        if file_path:
            try:
                self.data_manager.df.to_csv(file_path, index=False, encoding='utf-8-sig')
                self.status_bar.showMessage(f"文件已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存错误", f"保存文件时发生错误: {str(e)}")
                self.status_bar.showMessage("保存失败")

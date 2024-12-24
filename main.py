import sys
import os

try:
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    from PySide6.QtWidgets import QApplication
    from lovelyform.views.main_window import CSVViewer
except Exception as e:
    from PySide6.QtWidgets import QApplication
    from views.main_window import CSVViewer
def show_csv_viewer(csv_file_path=None):
    """
    显示CSV查看器的接口函数
    
    Args:
        csv_file_path (str, optional): CSV文件路径。如果提供，将直接打开该文件
        
    Returns:
        tuple: (QApplication实例, CSVViewer实例)
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 设置应用程序样式
    #app.setStyle('Fusion')
    
    viewer = CSVViewer()
    
    # 如果提供了文件路径，先加载文件再显示窗口
    if csv_file_path and os.path.exists(csv_file_path):
        viewer.load_csv_file(csv_file_path)
        
    viewer.show()
    return app, viewer

def main():
    app, viewer = show_csv_viewer()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
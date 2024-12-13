import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from views.main_window import CSVViewer

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    viewer = CSVViewer()
    viewer.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
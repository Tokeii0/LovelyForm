from PySide6.QtWidgets import QApplication
from lovelyform.views.main_window import CSVViewer
import sys

def show_csv_viewer(
    csv_file=None,
    window_title=None,
    window_icon=None,
    variables=None,
    plugins=None,
):
    """显示CSV查看器
    
    Args:
        csv_file: CSV文件路径
        window_title: 窗口标题
        window_icon: 窗口图标
        variables: 要设置的变量字典
        plugins: 要加载的插件列表
    
    Returns:
        tuple: (QApplication, CSVViewer)
    """
    app = QApplication.instance() or QApplication([])
    
    viewer = CSVViewer()
    if window_title:
        viewer.setWindowTitle(window_title)
    if window_icon:
        viewer.setWindowIcon(QIcon(window_icon))
    if variables:
        viewer.set_variables(variables)
    if plugins:
        viewer.load_plugins(plugins)
    
    # 加载CSV文件
    if csv_file:
        viewer.load_csv_file(csv_file)
    
    viewer.show()
    return app, viewer

__all__ = ['show_csv_viewer', 'CSVViewer']

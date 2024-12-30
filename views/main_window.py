from lovelyform.models.data_manager import DataManager
from lovelyform.views.search_result_view import SearchResultView
from lovelyform.views.statistics_view import StatisticsView
from lovelyform.plugins.plugin_manager import PluginManager
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QLabel, QSpinBox, QTableView,
                             QHeaderView, QAbstractItemView, QMessageBox, QMenu, QFileDialog, QToolBar,
                             QCheckBox, QInputDialog, QDialog, QGroupBox, QFrame,
                             QProgressBar, QSplitter, QApplication)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QAction, QIcon, QGuiApplication

import os
import sys

# 添加主程序路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from lovelyform.models.data_manager import DataManager
from lovelyform.views.search_result_view import SearchResultView
from lovelyform.views.statistics_view import StatisticsView
from lovelyform.plugins.plugin_manager import PluginManager
from lovelyform.plugins.command_executor import CommandConfigDialog

# 导入拆分出的模块
from lovelyform.views.ui_components import UIComponentMixin
from lovelyform.views.table_operations import TableOperationsMixin
from lovelyform.views.file_operations import FileOperationsMixin
from lovelyform.views.search_filter import SearchFilterMixin
from lovelyform.views.theme_manager import ThemeManagerMixin
from lovelyform.views.pagination import PaginationMixin
from lovelyform.views.floating_toolbar import FloatingToolBar

# 导入样式配置
import ui.styles

class CSVViewer(QMainWindow, UIComponentMixin, TableOperationsMixin,
               FileOperationsMixin, SearchFilterMixin, ThemeManagerMixin,
               PaginationMixin):
    def __init__(self):
        super().__init__()
        self.variables = {}
        self.setWindowTitle("LovelyForm")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)  # 移除原生标题栏
        
        # 初始化数据管理器
        self.data_manager = DataManager()
        self.current_file = None
        self.proxy_model = QSortFilterProxyModel()
        
        # 初始化分页相关的属性
        self.current_page = 0
        self.page_size = 100
        
        # 初始化状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
        
        # 初始化分页控件
        self.prev_btn = None
        self.next_btn = None
        self.page_label = None
        self.page_size_spin = None
        
        self.plugin_manager = PluginManager()
        
        # 加载用户主题设置
        self.load_user_theme()
        self._init_ui()  # 只调用本类的_init_ui方法
        self.update_all_styles()

    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建自定义标题栏
        title_bar, title_layout = self.create_title_bar()
        
        # 添加主题切换按钮
        self.theme_button = self.create_circle_button(ui.styles.theme_button_color)
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setToolTip("切换主题")
        
        # 添加最小化按钮
        self.min_button = self.create_circle_button(ui.styles.minimize_button_color)
        self.min_button.clicked.connect(self.showMinimized)
        self.min_button.setToolTip("最小化")
        
        # 添加最大化/还原按钮
        self.max_button = self.create_circle_button(ui.styles.maximize_button_color)
        self.max_button.clicked.connect(self.toggle_maximize)
        self.max_button.setToolTip("最大化")
        
        # 添加关闭按钮
        self.close_button = self.create_circle_button(ui.styles.close_button_color)
        self.close_button.clicked.connect(self.close)
        self.close_button.setToolTip("关闭")
        
        title_layout.addWidget(self.theme_button)
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.max_button)
        title_layout.addWidget(self.close_button)
        
        main_layout.addWidget(title_bar)
        
        # 内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # 工具栏区域
        toolbar_group, toolbar_layout = self.create_toolbar()
        
        # 文件操作按钮
        load_btn = QPushButton("打开文件")
        load_btn.setMinimumWidth(80)
        load_btn.clicked.connect(self.load_csv_file)
        toolbar_layout.addWidget(load_btn)
        
        save_btn = QPushButton("保存文件")
        save_btn.setMinimumWidth(80)
        save_btn.clicked.connect(self.save_csv)
        toolbar_layout.addWidget(save_btn)
        
        # 添加命令编辑按钮
        command_btn = QPushButton("命令编辑")
        command_btn.setMinimumWidth(80)
        command_btn.clicked.connect(self.show_command_config)
        toolbar_layout.addWidget(command_btn)
        
        # 搜索区域
        toolbar_layout.addSpacing(20)
        self.global_search_input = QLineEdit()
        self.global_search_input.setPlaceholderText("在整个表格中搜索内容...")
        self.global_search_input.setMinimumWidth(200)
        toolbar_layout.addWidget(self.global_search_input)
        
        search_btn = QPushButton("全局搜索")
        search_btn.setMinimumWidth(60)
        search_btn.clicked.connect(lambda: self.search_table())
        toolbar_layout.addWidget(search_btn)
        
        # 隐藏空白列复选框
        toolbar_layout.addSpacing(20)
        self.hide_empty_checkbox = QCheckBox("隐藏空白列")
        self.hide_empty_checkbox.stateChanged.connect(self.on_hide_empty_changed)
        toolbar_layout.addWidget(self.hide_empty_checkbox)
        
        # 添加插件菜单按钮
        plugins_menu = QMenu(self)
        plugins_button = QPushButton("全局插件菜单")
        plugins_button.setMenu(plugins_menu)
        
        # 为每个插件创建菜单项
        for plugin_name, plugin_class in self.plugin_manager.get_table_plugins().items():
            plugin_instance = plugin_class()
            action = plugins_menu.addAction(plugin_instance.button_text)
            # 使用lambda创建闭包来保存plugin_instance
            action.triggered.connect(lambda checked=False, p=plugin_instance: self.handle_table_plugin(p))
            if hasattr(plugin_instance, 'description'):
                action.setToolTip(plugin_instance.description)
        
        toolbar_layout.addWidget(plugins_button)
        toolbar_layout.addStretch()
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setVisible(False)
        toolbar_layout.addWidget(self.progress_bar)
        
        content_layout.addWidget(toolbar_group)
        
        # 表格视图
        self.table_view, self.table_container = self.setup_table_view()
        content_layout.addWidget(self.table_container)
        
        # 搜索结果视图
        self.search_result_view = SearchResultView(self)
        self.search_result_view.setVisible(False)
        self.search_result_view.item_double_clicked.connect(self.on_search_result_double_clicked)
        content_layout.addWidget(self.search_result_view)
        
        # 分页控件
        pagination_widget = self.create_pagination_controls()
        content_layout.addWidget(pagination_widget)
        
        # 设置信号连接
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.page_size_spin.valueChanged.connect(self.update_page_size)
        self.page_jump_btn.clicked.connect(self.jump_to_page)
        
        main_layout.addWidget(content_widget)
        
        # 创建中心窗口
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def toggle_maximize(self):
        """切换最大化/还原窗口状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于窗口拖动"""
        if event.button() == Qt.LeftButton:
            if self.title_bar.geometry().contains(event.pos()):
                self._drag_pos = event.pos()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于窗口拖动"""
        if hasattr(self, '_drag_pos'):
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.pos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if hasattr(self, '_drag_pos'):
            del self._drag_pos

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        page_size = self.page_size_spin.value() if hasattr(self, 'page_size_spin') else self.page_size
        total_pages = (len(self.data_manager.df) - 1) // page_size + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_table()

    def update_page_size(self):
        """更新每页显示的行数"""
        self.page_size = self.page_size_spin.value()
        self.current_page = 0
        self.update_table()

    def update_page_label(self):
        """更新页码显示标签"""
        if not hasattr(self, 'page_label') or self.data_manager.df.empty:
            return
            
        page_size = self.page_size_spin.value() if hasattr(self, 'page_size_spin') else self.page_size
        total_pages = (len(self.data_manager.df) - 1) // page_size + 1
        current_page = self.current_page + 1
        self.page_label.setText(f"页码: {current_page}/{total_pages}")

    def update_title(self, filename=None):
        """更新窗口标题"""
        if filename:
            self.title_label.setText(f"LovelyForm - {filename}")
        elif self.current_file:
            self.title_label.setText(f"LovelyForm - {self.current_file}")
        else:
            self.title_label.setText("LovelyForm")

    def on_hide_empty_changed(self, state):
        """空白列隐藏状态改变时的处理函数"""
        self.update_table()

    def on_search_result_double_clicked(self, row_num):
        """处理搜索结果双击事件"""
        # 确保搜索结果视图可见
        self.search_result_view.setVisible(True)
        
        # 计算目标页码
        page = row_num // self.page_size
        
        # 跳转到对应页
        if page != self.current_page:
            self.current_page = page
            self.update_table()
            
        # 计算在当前页中的行号
        row_in_page = row_num % self.page_size
        
        # 选中对应的行并滚动到可见区域
        model_index = self.table_view.model().index(row_in_page, 0)
        self.table_view.scrollTo(model_index, QAbstractItemView.ScrollHint.PositionAtCenter)
        self.table_view.selectRow(row_in_page)
        self.table_view.setFocus()

        
    def show_command_config(self):
        """显示命令配置对话框"""
        dialog = CommandConfigDialog(self, variables=self.variables)
        dialog.exec_()

        
    def show_command_config(self):
        """显示命令配置对话框"""
        dialog = CommandConfigDialog(self, variables=self.variables)
        dialog.exec_()

    def set_variables(self, variables: dict):
        """设置变量字典
        
        Args:
            variables: 要设置的变量字典
        """
        self.variables = variables

    def load_csv_file(self, file_path=None):
        """加载CSV文件
        Args:
            file_path: 可选，直接指定要加载的文件路径。如果不指定，则弹出文件选择对话框。
        """
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "打开CSV文件", "", "CSV文件 (*.csv)")
            
        if file_path:
            try:
                # 更新标题显示文件名
                filename = os.path.basename(file_path)
                self.update_title(filename)
                
                # 加载文件
                load_thread = self.data_manager.load_file(file_path)
                load_thread.error.connect(lambda e: QMessageBox.critical(self, "错误", f"加载文件失败(文件可能为空))"))
                load_thread.progress.connect(lambda p: self.status_bar.showMessage(f"正在加载文件: {p}%"))
                load_thread.finished.connect(lambda: self.status_bar.showMessage(f"已加载文件: {file_path}"))
                
                self.current_file = file_path
                
                # 更新表格和搜索结果
                self.data_manager.data_changed.connect(self.update_table)
                self.search_result_view.clear()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载文件失败: {str(e)}")

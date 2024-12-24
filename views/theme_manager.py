import json
import os
from PySide6.QtWidgets import QWidget, QPushButton, QGroupBox, QTableView, QHeaderView
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from ui.theme_selector import ThemeSelectorDialog
import ui.styles

class ThemeManagerMixin:
    def toggle_theme(self):
        """切换主题"""
        theme_selector = ThemeSelectorDialog(list(ui.styles.color_schemes.keys()))
        theme_selector.theme_selected.connect(self.apply_selected_theme)
        
        # 计算屏幕中心位置
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        dialog_geometry = theme_selector.geometry()
        
        x = screen_geometry.center().x() - dialog_geometry.width() // 2
        y = screen_geometry.center().y() - dialog_geometry.height() // 2
        theme_selector.move(x, y)
        
        theme_selector.exec()

    def apply_selected_theme(self, theme_name):
        """应用选择的主题"""
        is_dark = ui.styles.is_dark_mode()
        ui.styles.apply_color_scheme(theme_name, is_dark)
        self.update_all_styles()
        self.save_theme(theme_name)

    def load_user_theme(self):
        """加载用户主题设置"""
        try:
            with open('config/user_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                theme_name = settings.get('theme', '默认')
                ui.styles.apply_color_scheme(theme_name, ui.styles.is_dark_mode())
        except Exception as e:
            print(f"加载主题设置失败: {str(e)}")
            ui.styles.apply_color_scheme('默认', ui.styles.is_dark_mode())

    def save_theme(self, theme_name):
        """保存主题设置"""
        try:
            settings_path = 'config/user_settings.json'
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            settings['theme'] = theme_name
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存主题设置失败: {str(e)}")

    def update_all_styles(self):
        """更新所有样式"""
        # 更新已有的样式
        self.update_header_style()  # 水平表头
        self.update_header_style(self.table_view.verticalHeader())  # 垂直表头
        
        # 更新主窗口样式
        self.setStyleSheet(ui.styles.main_window_style)
        self.setStyleSheet(ui.styles.right_panel_style)
        
        # 表格样式
        self.table_view.setStyleSheet(ui.styles.newtable_widget_style)
        
        # 更新所有子组件的样式
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(ui.styles.button_style)
            elif isinstance(widget, QGroupBox):
                widget.setStyleSheet(ui.styles.right_panel_style)
            elif isinstance(widget, QTableView):
                widget.setStyleSheet("")
                
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            
            if isinstance(widget, (QTableView, QHeaderView)):
                widget.viewport().update()
            else:
                try:
                    widget.update()
                except TypeError:
                    pass
        
        self.repaint()

    def update_header_style(self, header=None):
        """更新表头样式"""
        if header is None:
            header = self.table_view.horizontalHeader()
            
        header_style = f"""
            QHeaderView::section {{
                background-color: {ui.styles.button_bg_color};
                color: {ui.styles.text_color};
                padding: 4px;
                border: 1px solid {ui.styles.border_color};
            }}
        """
        header.setStyleSheet(header_style)

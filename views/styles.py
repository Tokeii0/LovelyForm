from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
import sys
import json
import os

# 从主项目导入样式配置
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ui.styles import (color_schemes, is_dark_mode, get_color_scheme, 
                      background_color, text_color, button_bg_color, 
                      button_text_color, button_hover_color, border_color)

def apply_theme():
    """应用主题样式"""
    # CSV查看器的样式
    csv_viewer_style = f"""
    QMainWindow {{
        background-color: {background_color};
        color: {text_color};
    }}
    
    QTableView {{
        background-color: {background_color};
        color: {text_color};
        border: 1px solid {border_color};
        gridline-color: {border_color};
        alternate-background-color: {background_color};  /* 设置交替行颜色与背景色相同 */
    }}
    
    QPushButton {{
        background-color: {button_bg_color};
        color: {button_text_color};
        border: 1px solid {border_color};
        padding: 5px 10px;
        border-radius: 3px;
    }}
    
    QPushButton:hover {{
        background-color: {button_hover_color};
    }}
    
    QHeaderView::section {{
        background-color: {button_bg_color};
        color: {button_text_color};
        padding: 5px;
        border: 1px solid {border_color};
    }}
    
    QScrollBar:horizontal {{
        background: {background_color};
        height: 12px;
        margin: 0px 12px 0px 12px;
        border: 1px solid {border_color};
    }}

    QScrollBar:vertical {{
        background: {background_color};
        width: 12px;
        margin: 12px 0px 12px 0px;
        border: 1px solid {border_color};
    }}

    QScrollBar::handle:horizontal {{
        background: {button_bg_color};
        min-width: 20px;
        border-radius: 2px;
    }}

    QScrollBar::handle:vertical {{
        background: {button_bg_color};
        min-height: 20px;
        border-radius: 2px;
    }}

    QScrollBar::add-line:horizontal {{
        border: none;
        background: none;
        width: 12px;
        subcontrol-position: right;
        subcontrol-origin: margin;
    }}

    QScrollBar::sub-line:horizontal {{
        border: none;
        background: none;
        width: 12px;
        subcontrol-position: left;
        subcontrol-origin: margin;
    }}

    QScrollBar::add-line:vertical {{
        border: none;
        background: none;
        height: 12px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }}

    QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
        height: 12px;
        subcontrol-position: top;
        subcontrol-origin: margin;
    }}

    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
        border: none;
    }}
    
    QMenuBar {{
        background-color: {background_color};
        color: {text_color};
    }}
    
    QMenuBar::item:selected {{
        background-color: {button_hover_color};
    }}
    
    QMenu {{
        background-color: {background_color};
        color: {text_color};
        border: 1px solid {border_color};
    }}
    
    QMenu::item:selected {{
        background-color: {button_hover_color};
    }}
    """
    
    return csv_viewer_style

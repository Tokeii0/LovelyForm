from abc import ABC, abstractmethod
import pandas as pd
import re
from typing import List, Optional, Dict, Any, Union, Pattern, Set
from PySide6.QtWidgets import QWidget

class BasePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass

    @property
    def author(self) -> str:
        """插件作者"""
        return "Unknown"

    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"
        
    @property
    def category(self) -> str:
        """插件分类"""
        return "未分类"
        
    @property
    def file_pattern(self) -> Optional[Union[str, Pattern]]:
        """文件名匹配模式
        
        Returns:
            str: 简单的文件名匹配模式，支持 * 和 ? 通配符
            Pattern: 正则表达式模式
            None: 不进行文件名匹配，适用于所有文件
        """
        return None
        
    @property
    def column_patterns(self) -> Optional[List[Union[str, Pattern]]]:
        """列名匹配模式列表
        
        Returns:
            List[Union[str, Pattern]]: 列名匹配模式列表，可以是字符串或正则表达式
            None: 不进行列名匹配，适用于所有列
        """
        return None
        
    def match_file(self, filename: str) -> bool:
        """检查文件名是否匹配
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否匹配
        """
        pattern = self.file_pattern
        if pattern is None:
            return True
            
        if isinstance(pattern, Pattern):
            return bool(pattern.search(filename))
            
        # 将通配符模式转换为正则表达式
        if isinstance(pattern, str):
            regex = pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".")
            return bool(re.match(f"^{regex}$", filename))
            
        return False
        
    def match_column(self, column_name: str) -> bool:
        """检查列名是否匹配
        
        Args:
            column_name: 列名
            
        Returns:
            bool: 是否匹配
        """
        patterns = self.column_patterns
        if patterns is None:
            return True
            
        for pattern in patterns:
            if isinstance(pattern, Pattern):
                if pattern.search(column_name):
                    return True
            elif isinstance(pattern, str):
                if pattern == column_name:
                    return True
                # 支持通配符
                regex = pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".")
                if re.match(f"^{regex}$", column_name):
                    return True
                    
        return False

class CellPlugin(BasePlugin):
    """单元格操作插件基类"""
    
    @abstractmethod
    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        """处理选中的单元格
        
        Args:
            df: 当前DataFrame
            selected_cells: 选中的单元格列表，每个元素为 (row, col) 元组
        
        Returns:
            处理后的DataFrame
        """
        pass

class TablePlugin(BasePlugin):
    """表格操作插件基类"""
    
    @abstractmethod
    def process_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理整个表格
        
        Args:
            df: 当前DataFrame
        
        Returns:
            处理后的DataFrame
        """
        pass

    @property
    @abstractmethod
    def button_text(self) -> str:
        """按钮显示文本"""
        pass

    @abstractmethod
    def create_config_widget(self) -> Optional[QWidget]:
        """创建配置界面
        
        Returns:
            配置界面组件，如果不需要配置则返回None
        """
        pass

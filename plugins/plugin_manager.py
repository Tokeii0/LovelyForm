import os
import sys
import importlib
import inspect
from typing import Dict, List, Type, Union
from plugins import CellPlugin, TablePlugin, BasePlugin
from plugins.command_executor import get_command_plugins

class PluginManager:
    def __init__(self):
        """初始化插件管理器"""
        self._cell_plugins: Dict[str, Type[CellPlugin]] = {}
        self._table_plugins: Dict[str, Type[TablePlugin]] = {}
        self.load_plugins()
        
    def load_plugins(self):
        """加载所有插件"""
        self._cell_plugins.clear()
        self._table_plugins.clear()
        
        # 加载内置插件
        from plugins import example_plugins
        for name, obj in vars(example_plugins).items():
            if isinstance(obj, type):
                if issubclass(obj, CellPlugin) and obj != CellPlugin:
                    self._cell_plugins[name] = obj
                elif issubclass(obj, TablePlugin) and obj != TablePlugin:
                    self._table_plugins[name] = obj
                    
        # 加载自定义命令插件
        command_plugins = get_command_plugins()
        if command_plugins:
            self._cell_plugins.update(command_plugins)
            
    def get_cell_plugins(self) -> Dict[str, Union[Type[CellPlugin], CellPlugin]]:
        """获取所有单元格插件"""
        return self._cell_plugins
        
    def get_table_plugins(self) -> Dict[str, Type[TablePlugin]]:
        """获取所有表格插件"""
        return self._table_plugins

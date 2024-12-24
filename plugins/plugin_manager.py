import os
import sys
import importlib
import inspect
from typing import Dict, List, Type, Union
from lovelyform.plugins import CellPlugin, TablePlugin, BasePlugin
from lovelyform.plugins.command_executor import get_command_plugins

class PluginManager:
    def __init__(self):
        """初始化插件管理器"""
        self._cell_plugins: Dict[str, Type[CellPlugin]] = {}
        self._table_plugins: Dict[str, Type[TablePlugin]] = {}
        self._cell_plugins_by_category: Dict[str, Dict[str, Union[Type[CellPlugin], CellPlugin]]] = {}
        self.load_plugins()
        
    def load_plugins(self):
        """加载所有插件"""
        self._cell_plugins.clear()
        self._table_plugins.clear()
        self._cell_plugins_by_category.clear()
        
        # 加载内置插件
        from lovelyform.plugins import example_plugins
        for name, obj in vars(example_plugins).items():
            if isinstance(obj, type):
                if issubclass(obj, CellPlugin) and obj != CellPlugin:
                    plugin = obj()  # 实例化插件以获取category
                    self._cell_plugins[name] = obj
                    # 按分类组织内置插件
                    category = plugin.category
                    if category not in self._cell_plugins_by_category:
                        self._cell_plugins_by_category[category] = {}
                    self._cell_plugins_by_category[category][name] = plugin
                elif issubclass(obj, TablePlugin) and obj != TablePlugin:
                    self._table_plugins[name] = obj
                    
        # 加载自定义命令插件
        command_plugins = get_command_plugins()
        if command_plugins:
            self._cell_plugins.update(command_plugins)
            # 按分类组织命令插件
            for name, plugin in command_plugins.items():
                if hasattr(plugin, 'command_config') and hasattr(plugin.command_config, 'category'):
                    category = plugin.command_config.category or "未分类"
                    if category not in self._cell_plugins_by_category:
                        self._cell_plugins_by_category[category] = {}
                    self._cell_plugins_by_category[category][name] = plugin
            
    def get_cell_plugins(self) -> Dict[str, Union[Type[CellPlugin], CellPlugin]]:
        """获取所有单元格插件"""
        return self._cell_plugins
        
    def get_table_plugins(self) -> Dict[str, Type[TablePlugin]]:
        """获取所有表格插件"""
        return self._table_plugins
        
    def get_cell_plugins_by_category(self) -> Dict[str, Dict[str, Union[Type[CellPlugin], CellPlugin]]]:
        """获取按分类组织的单元格插件"""
        return self._cell_plugins_by_category

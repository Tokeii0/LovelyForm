# LovelyForm 

从lovelymem中分离重构出来的表格展示工具，为之后lovelymem开源完全体做准备，支持命令自定义执行

## 功能特点

- 加载CSV文件：支持通过文件对话框加载CSV文件
- 保存CSV文件：可将表格内容保存为CSV文件
- 增强搜索功能：
  - 全局搜索：在整个表格中搜索内容
  - 列筛选：对特定列进行实时筛选
  - 显示匹配项的行号、列名和内容
  - 双击搜索结果可快速跳转到对应位置
- 排序与筛选：支持按列排序和数据筛选
- 分页功能：大型数据集分页加载
- 插件系统：支持自定义单元格和表格操作插件
  - 支持命令执行插件：可配置自定义命令对选中单元格进行处理
- 自定义右键菜单：支持扩展右键菜单功能
- 智能列处理：自动隐藏全空列
- 灵活布局：支持列拖动和自适应单元格大小
- 编辑功能：支持删除行和列
- 增强复制：支持多选单元格的表格式复制
- 主题系统：支持切换不同的主题样式
- 自定义命令：支持配置和执行自定义命令

## 最近更新

### 2024-12-14
- 优化了搜索功能：
  - 区分全局搜索和列筛选功能
  - 改进搜索和筛选的状态提示
  - 优化了搜索结果的显示
- 新增主题切换功能
- 改进了命令执行插件的配置界面
- 优化了用户界面提示和交互
- 修复了搜索框冲突的问题

### 2024-12-13
- 项目初始化
- 实现基础功能：CSV文件加载、保存
- 添加搜索和筛选功能
- 实现分页功能
- 添加自定义右键菜单支持
- 新增：自动隐藏空列功能
- 新增：列拖动和自适应单元格大小
- 新增：删除行列功能
- 新增：增强的多选复制功能
- 优化：改进搜索功能，添加结果展示区域和快速跳转

## 插件系统

LovelyForm 提供了强大的插件系统，支持两种类型的插件：

### 单元格插件 (CellPlugin)
- 通过右键菜单操作选中的单元格
- 可以自定义单元格数据的处理逻辑
- 示例：字符串转大写插件

### 表格插件 (TablePlugin)
- 通过工具栏按钮操作整个表格
- 可以进行数据分析和统计
- 示例：数据统计插件

### 开发自定义插件

1. 在 `plugins` 目录下创建新的 Python 文件
2. 继承 `CellPlugin` 或 `TablePlugin` 基类
3. 实现必要的方法：
   - CellPlugin: `create_menu_action()` 和 `process_cell()`
   - TablePlugin: `create_button()` 和 `process_table()`

示例插件代码：
```python
from plugins import CellPlugin

class MyCustomPlugin(CellPlugin):
    def __init__(self):
        self.name = "我的插件"
        self.description = "这是一个示例插件"

    def create_menu_action(self, menu):
        action = QAction(self.name, menu)
        action.setStatusTip(self.description)
        return action

    def process_cell(self, value):
        return str(value).upper()
```

## 安装要求

- Python 3.8+
- PySide6
- pandas

## 安装步骤

1. 克隆仓库到本地
2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

运行主程序：
```bash
python main.py
```

## 更新日志

### 2024-12-13
- 项目初始化
- 实现基础功能：CSV文件加载、保存
- 添加搜索和筛选功能
- 实现分页功能
- 添加自定义右键菜单支持
- 新增：自动隐藏空列功能
- 新增：列拖动和自适应单元格大小
- 新增：删除行列功能
- 新增：增强的多选复制功能
- 优化：改进搜索功能，添加结果展示区域和快速跳转

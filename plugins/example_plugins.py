from calendar import c
import imp
from numpy import imag
import pandas as pd
from typing import List
import re
import importlib,json
from lovelyform.plugins import CellPlugin, TablePlugin
from PySide6.QtWidgets import QApplication, QTableView, QInputDialog, QStyledItemDelegate, QWidget, QVBoxLayout, QLabel, QLineEdit, QMessageBox
from PySide6.QtCore import Qt,QObject,Signal,QThread
from PySide6.QtWidgets import QDialog, QApplication, QTreeWidget, QTreeWidgetItem
from PySide6.QtGui import QColor
import yaml
import os
import subprocess
import shutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout
from plugin.vol2 import Vol2

def get_image_info_file():
    #output/image.txt
    mem_path = open('output/image_info.txt', 'r',encoding='utf-8').read().split(',')[0]
    profile = open('output/image_info.txt', 'r',encoding='utf-8').read().split(',')[1]
    return mem_path, profile

def readconfig():
    with open('config/base_config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    python27 = config['base_tools']['python27']['path']
    python27 = os.path.abspath(python27)
    volatility2 = config['tools']['volatility2_python']['path']
    volatility2_plugin = config['tools']['volatility2_plugin']['path']
    volatility2 = os.path.abspath(volatility2)
    volatility2_plugin = os.path.abspath(volatility2_plugin)
    gimppath = config['tools']['gimp']['path']
    return python27, volatility2, volatility2_plugin, gimppath

def get_sorted_cell_value(df: pd.DataFrame, row: int, col: int) -> str:
    """
    获取表格中指定单元格的实际值
    
    Args:
        df: DataFrame对象（仅作为备用）
        row: 视图中的行索引
        col: 视图中的列索引
        
    Returns:
        str: 单元格的值
    """
    try:
        # 获取主窗口实例
        main_window = QApplication.activeWindow()
        if not main_window:
            return str(df.iloc[row, col])
            
        # 获取表格视图
        table_view = main_window.findChild(QTableView)
        if not table_view:
            return str(df.iloc[row, col])
        
        # 获取模型
        model = table_view.model()
        if not model:
            return str(df.iloc[row, col])
            
        # 检查索引是否有效
        if row < 0 or row >= model.rowCount() or col < 0 or col >= model.columnCount():
            return str(df.iloc[row, col])
        
        # 直接从视图模型中获取值
        index = model.index(row, col)
        value = model.data(index)
        
        # 确保返回有效的值
        if value is None or value == '':
            return str(df.iloc[row, col])
            
        return str(value)
    except Exception:
        # 如果出现任何错误，回退到使用 DataFrame
        return str(df.iloc[row, col])

def set_sorted_cell_value(df: pd.DataFrame, row: int, col: int, value: str) -> None:
    """
    设置排序后的表格中指定单元格的值
    
    Args:
        df: DataFrame对象
        row: 视图中的行索引
        col: 视图中的列索引
        value: 要设置的值
    """
    # 获取主窗口实例
    main_window = QApplication.activeWindow()
    if not main_window:
        df.iloc[row, col] = value
        return
        
    # 获取表格视图和代理模型
    table_view = main_window.findChild(QTableView)
    if not table_view:
        df.iloc[row, col] = value
        return
        
    proxy_model = table_view.model()
    if not proxy_model:
        df.iloc[row, col] = value
        return
        
    source_model = proxy_model.sourceModel()
    if not source_model:
        df.iloc[row, col] = value
        return
        
    # 获取页面偏移量
    page_size = getattr(main_window, 'page_size', 100)
    current_page = getattr(main_window, 'current_page', 0)
    page_offset = current_page * page_size
    
    # 计算实际行索引（考虑分页）
    absolute_row = row + page_offset
    
    # 将视图索引转换为源模型索引（考虑排序）
    proxy_index = proxy_model.index(row, col)
    source_index = proxy_model.mapToSource(proxy_index)
    source_col = source_index.column()
    
    # 使用绝对行索引和源模型列索引设置值
    df.iloc[absolute_row, source_col] = value

class TimelinePlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "时间戳转换"
    
    @property
    def description(self) -> str:
        return "将UNIX时间戳转换为可读时间"
        
    @property
    def category(self) -> str:
        return "时间分析"
        
    @property
    def file_pattern(self) -> str:
        return "*timeline*.csv"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*Time*", "*Date*", "Timestamp"]  # 只处理时间相关的列

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        from datetime import datetime
        for row, col in selected_cells:
            try:
                # 获取值并转换
                value = get_sorted_cell_value(df, row, col)
                timestamp = float(value)
                dt = datetime.fromtimestamp(timestamp)
                # 设置转换后的值
                set_sorted_cell_value(df, row, col, dt.strftime("%Y-%m-%d %H:%M:%S"))
            except (ValueError, TypeError):
                pass  # 如果转换失败，保持原值不变
        return df

# 进程转储 >exe vol2
class Vol2PidtoProcPlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "进程转储为可执行程序(volatility2)"
    
    @property
    def description(self) -> str:
        return "将PidProc文件导出"
        
    @property
    def category(self) -> str:
        return "进程转储"
        
    @property
    def file_pattern(self) -> str:
        return "*"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*PID*"]

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        # 提取所选单元格内容
        from plugin.vol2 import Vol2Plugin
        image_path = get_image_info_file()[0]
        
        # 处理每个选中的单元格
        for row, col in selected_cells:
            value = get_sorted_cell_value(df, row, col).strip('"')
            print(f"获取到的 PID 值: {value}")
            
            def process_procdump():
                Vol2Plugin(image_path).vol2_procdump(value)
                print(f"PID {value} 的进程转储已导出到 output/executable.{value}.exe")
                
            from threading import Thread
            thread = Thread(target=process_procdump)
            thread.daemon = True
            thread.start()
        return df

# 进程转储 >exe vol3
class Vol3PidtoProcPlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "进程转储为可执行程序(volatility3)"
    
    @property
    def description(self) -> str:
        return "将PidProc文件导出"
        
    @property
    def category(self) -> str:
        return "进程转储"
        
    @property
    def file_pattern(self) -> str:
        return "*"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*PID*"]

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        # 提取所选单元格内容
        from plugin.vol3 import Vol3Plugin
        image_path = get_image_info_file()[0]
        for row, col in selected_cells:
            value = get_sorted_cell_value(df, row, col).strip('"')
            print(f"获取到的 PID 值： {value}")
            
            def process_procdump():
                Vol3Plugin(image_path).vol3procdump(value)
                print(f"PID {value} 的进程转储已导出到 output/{value}.procname.exe.xxxxxx.dmp")
                
            from threading import Thread
            thread = Thread(target=process_procdump)
            thread.daemon = True
            thread.start()
        return df

# 进程转储后通过GIMP打开 vol2
class Vol2PidDumptoGimpPlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "进程转储后通过GIMP打开(volatility2)"
    
    @property
    def description(self) -> str:
        return "将PidDump文件导出并通过GIMP打开"
        
    @property
    def category(self) -> str:
        return "进程分析(CTF)"
        
    @property
    def file_pattern(self) -> str:
        return "*"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*PID*"]

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        # 提取所选单元格内容
        from plugin.vol2 import Vol2Plugin
        image_path = get_image_info_file()[0]
        gimppath = readconfig()[3]
        # 处理每个选中的单元格
        for row, col in selected_cells:
            value = get_sorted_cell_value(df, row, col).strip('"')
            print(f"获取到的 PID 值: {value}")
            # 使用线程执行耗时操作
            def process_dump():
                Vol2Plugin(image_path).vol2_memdump(value)
                procdumpfile = rf'output/{value}.dmp'
                os.makedirs('tmp', exist_ok=True)
                newpath = rf'tmp/{value}.data'
                if os.path.exists(newpath):
                    os.remove(newpath)
                shutil.copy(procdumpfile, newpath)
                cmd2 = rf'"{gimppath}" tmp/{value}.data'
                print('[*] 正在调用gimp执行命令：' + cmd2)
                subprocess.Popen(cmd2, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                print('[+] 执行成功！下面gimp相关报错可无视')

            from threading import Thread
            thread = Thread(target=process_dump)
            thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
            thread.start()
        return df

# 进程转储后通过GIMP打开 vol3
class Vol3PidDumptoGimpPlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "进程转储后通过GIMP打开(volatility3)"
    
    @property
    def description(self) -> str:
        return "将PidDump文件导出"
        
    @property
    def category(self) -> str:
        return "进程分析(CTF)"
        
    @property
    def file_pattern(self) -> str:
        return "*"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*PID*"]

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        # 提取所选单元格内容
        from plugin.vol3 import Vol3Plugin
        image_path = get_image_info_file()[0]
        gimppath = readconfig()[3]
        for row, col in selected_cells:
            value = get_sorted_cell_value(df, row, col).strip('"')
            print(f"获取到的 PID 值： {value}")
            # 使用线程执行耗时操作
            def process_dump():
                Vol3Plugin(image_path).vol3memmap(value)
                
                while not os.path.exists(f'output/pid.{value}.dmp'):
                    print(f"PID {value} 的进程转储尚未导出，等待中...")
                    import time
                    time.sleep(1)
                print(f"PID {value} 的进程转储已导出到 output/pid.{value}.dmp")
                procdumpfile = rf'output/pid.{value}.dmp'
                os.makedirs('tmp', exist_ok=True)
                newpath = rf'tmp/{value}.data'
                if os.path.exists(newpath):
                    os.remove(newpath)
                shutil.copy(procdumpfile, newpath)
                cmd2 = rf'"{gimppath}" tmp/{value}.data'
                print('[*] 正在调用gimp执行命令：' + cmd2)
                subprocess.Popen(cmd2, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                print('[+] 执行成功！')
            

            from threading import Thread
            thread = Thread(target=process_dump)
            thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
            thread.start()

# 进程转储后通过GIMP打开 memprocfs
class MemprocfsPidDumptoGimpPlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "进程转储后通过GIMP打开(memprocfs)"
    
    @property
    def description(self) -> str:
        return "将PidDump文件导出并通过GIMP打开"
        
    @property
    def category(self) -> str:
        return "进程分析(CTF)"
        
    @property
    def file_pattern(self) -> str:
        return "*"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*PID*"]

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        # 提取所选单元格内容
        from plugin.memprocfs import MemprocfsPlugin
        image_path = get_image_info_file()[0]
        gimppath = readconfig()[3]
        for row, col in selected_cells:
            value = get_sorted_cell_value(df, row, col).strip('"')
            print(f"获取到的 PID 值： {value}")
            # 使用线程执行耗时操作
            def process_dump():
                procmemfile = rf'M:/pid/{value}/minidump/minidump.dmp'
                os.makedirs('tmp', exist_ok=True)
                newpath = r'tmp/minidump.data'
                if os.path.exists(newpath):
                    os.remove(newpath)
                shutil.copy(procmemfile, newpath)
                cmd2 = rf'"{gimppath}" tmp/minidump.data'
                print('[*] 正在调用gimp执行命令：' + cmd2)
                subprocess.Popen(cmd2, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                print('[+] 执行成功！')

            from threading import Thread
            thread = Thread(target=process_dump)
            thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
            thread.start()
# 导出该文件(vol2-dumpfile)
class Vol2DumpFilePlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "导出该文件(vol2-dumpfile)"
    
    @property
    def description(self) -> str:
        return "将fileDump文件导出"
        
    @property
    def category(self) -> str:
        return "文件导出"
        
    @property
    def file_pattern(self) -> str:
        return "*vol2*file*"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*Offset*"]

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        # 提取所选单元格内容
        from plugin.vol2 import Vol2Plugin
        image_path = get_image_info_file()[0]
        profile = get_image_info_file()[1]
        # 处理每个选中的单元格
        for row, col in selected_cells:
            value = get_sorted_cell_value(df, row, col).strip('"')
            print(f"获取到的偏移量： {value}")
            def process_dump():
                Vol2Plugin(image_path).vol2_dumpfiles(value)
                print('[+] 执行成功！')
            from threading import Thread
            thread = Thread(target=process_dump)
            thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
            thread.start()
        return df

# 导出该文件(vol3-dumpfile)
class Vol3DumpFilePlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "导出该文件(vol3-dumpfile)"
    
    @property
    def description(self) -> str:
        return "将fileDump文件导出"
        
    @property
    def category(self) -> str:
        return "文件导出"
        
    @property
    def file_pattern(self) -> str:
        return "output_vol3_filescan*"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*Offset*"]

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        # 提取所选单元格内容
        from plugin.vol3 import Vol3Plugin
        image_path = get_image_info_file()[0]
        # 处理每个选中的单元格
        for row, col in selected_cells:
            value = get_sorted_cell_value(df, row, col).strip('"')
            print(f"获取到的偏移量： {value}")
            # 使用线程执行耗时操作
            def process_dump():
                Vol3Plugin(image_path).vol3dumpfiles(value)
                print('[+] 执行成功！')
            from threading import Thread
            thread = Thread(target=process_dump)
            thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
            thread.start()
        return df

# 复制该程序所需的所有文件 Memprocfs
class CopyProcAllPlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "复制该程序所需的所有文件(Memprocfs)"
    
    @property
    def description(self) -> str:
        return "复制该程序所需的所有文件"
        
    @property
    def category(self) -> str:
        return "文件分析"
        
    @property
    def file_pattern(self) -> str:
        return "*"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*PID*"]

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        # 提取所选单元格内容
        for row, col in selected_cells:
            value = get_sorted_cell_value(df, row, col).strip('"')
            print(f"获取到的 PID 值： {value}")
            def proc_to_files():
                    filespath = rf'M:/pid/{value}/files/vads/'
                    if os.path.exists(filespath):
                        shutil.copytree(filespath, f'output/files_{value}')

                        print(f'[+] 已把该程序所使用的所有文件复制到output/files_{value}文件夹，请注意不要运行任何文件！！！！！！')
                    else:
                        print('[×] 该文件夹不存在！')
            from threading import Thread
            thread = Thread(target=proc_to_files)
            thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
            thread.start()

# 句柄信息 memprocfs
class MemprocfsHandleInfoPlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "句柄信息(memprocfs)"
    
    @property
    def description(self) -> str:
        return "显示句柄信息"
        
    @property
    def category(self) -> str:
        return "句柄分析"
        
    @property
    def file_pattern(self) -> str:
        return "*"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*PID*"]

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        # 提取所选单元格内容
        for row, col in selected_cells:
            value = get_sorted_cell_value(df, row, col).strip('"')
            print(f"获取到的 PID 值： {value}")
            def handles_to_files():
                    handlefile = rf'M:/pid/{value}/handles/handles.txt'
                    if os.path.exists(handlefile):
                        from plugin.QuicklyView import QuicklyView
                        with open(handlefile, 'r', encoding='utf-8') as f:
                            handlewindows = QuicklyView(f'文件内容,文件路径：{handlefile}', size=(500, 900))
                            handlewindows.textEdit.setPlainText(f.read())
                        handlewindows.show()
                    else:
                        print('[×] 该文件不存在！')
            from threading import Thread
            thread = Thread(target=handles_to_files)
            thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
            thread.start()

# NTFS Use explorer to open the file
class MemprocfsNTFSExplorerPlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "从资源管理器中查看文件(NTFS)"
    
    @property
    def description(self) -> str:
        return "从资源管理器中查看文件"
        
    @property
    def category(self) -> str:
        return "查看文件"
        
    @property
    def file_pattern(self) -> str:
        return "*"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*Text*"]

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        # 提取所选单元格内容
        for row, col in selected_cells:
            value = get_sorted_cell_value(df, row, col).strip('"')
            print(f"获取到的文件路径： {value}")
            def ntfs_to_files():
                import subprocess
                # \0\Users\admin\Desktop\ADMIN-PC-20220414-013700.raw 取出文件路径
                filepath = r"M:\forensic\ntfs"+ value.rsplit('\\', 1)[0]
                value_path = ["explorer", filepath]
                subprocess.run(value_path)
                print('[+] 请查看资源管理器')

            from threading import Thread
            thread = Thread(target=ntfs_to_files)
            thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
            thread.start()

# 权限信息

class DataStatisticsPlugin(TablePlugin):
    @property
    def name(self) -> str:
        return "数据统计"
        
    @property
    def description(self) -> str:
        return "计算并显示数据统计信息"
        
    @property
    def category(self) -> str:
        return "数据分析"
        
    @property
    def button_text(self) -> str:
        return "数据统计"
        
    def create_config_widget(self) -> None:
        return None
        
    def process_table(self, df: pd.DataFrame) -> pd.DataFrame:
        # 分离数值列和字符串列
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        string_cols = df.select_dtypes(include=['object', 'string']).columns
        
        result_dfs = []
        
        # 处理数值列
        if len(numeric_cols) > 0:
            # 计算基本统计信息
            numeric_stats = df[numeric_cols].describe()
            
            # 添加更多统计信息
            additional_numeric_stats = pd.DataFrame({
                col: {
                    '非空值数': df[col].count(),
                    '空值数': df[col].isna().sum(),
                    '空值比例': f"{(df[col].isna().sum() / len(df) * 100):.2f}%",
                    '唯一值数': df[col].nunique(),
                    '众数': df[col].mode().iloc[0] if not df[col].mode().empty else None,
                    '变异系数': f"{(df[col].std() / df[col].mean() * 100):.2f}%" if df[col].mean() != 0 else "N/A",
                } for col in numeric_cols
            })
            
            # 合并数值列统计信息
            numeric_final = pd.concat([numeric_stats, additional_numeric_stats])
            numeric_final.insert(0, '统计类型', '数值统计')
            result_dfs.append(numeric_final)
        
        # 处理字符串列
        if len(string_cols) > 0:
            string_stats = pd.DataFrame({
                col: {
                    '非空值数': df[col].count(),
                    '空值数': df[col].isna().sum(),
                    '空值比例': f"{(df[col].isna().sum() / len(df) * 100):.2f}%",
                    '唯一值数': df[col].nunique(),
                    '最常见值': df[col].mode().iloc[0] if not df[col].mode().empty else None,
                    '最常见值出现次数': df[col].value_counts().iloc[0] if not df[col].value_counts().empty else 0,
                    '最长字符串长度': df[col].str.len().max() if df[col].dtype == 'object' else None,
                    '最短字符串长度': df[col].str.len().min() if df[col].dtype == 'object' else None,
                    '平均字符串长度': f"{df[col].str.len().mean():.1f}" if df[col].dtype == 'object' else None,
                } for col in string_cols
            })
            string_stats.insert(0, '统计类型', '字符串统计')
            result_dfs.append(string_stats)
        
        if not result_dfs:
            return pd.DataFrame({"消息": ["没有找到可以统计的列"]})
            
        # 合并所有统计结果
        final_stats = pd.concat(result_dfs)
        
        # 对索引进行重命名，使其更易读
        index_map = {
            'count': '计数',
            'mean': '平均值',
            'std': '标准差',
            'min': '最小值',
            '25%': '25%分位数',
            '50%': '中位数',
            '75%': '75%分位数',
            'max': '最大值',
        }
        final_stats.index = final_stats.index.map(lambda x: index_map.get(x, x))
        
        return final_stats

# 全局插件，替换指定关键词
class ReplaceKeywordPlugin(TablePlugin):
    def __init__(self):
        super().__init__()
        
    @property
    def name(self) -> str:
        return "关键词替换"
        
    @property
    def description(self) -> str:
        return "将表格中指定的关键词替换为目标文本"
        
    @property
    def category(self) -> str:
        return "文本处理"
        
    @property
    def button_text(self) -> str:
        return "替换关键词"
        
    def create_config_widget(self) -> None:
        # 返回None表示不需要配置窗口
        return None
        
    def process_table(self, df: pd.DataFrame) -> pd.DataFrame:
        # 弹出对话框获取关键词
        source_text, ok = QInputDialog.getText(None, "输入关键词", "请输入要替换的关键词:")
        if not ok or not source_text:
            return df
            
        target_text, ok = QInputDialog.getText(None, "输入替换文本", "请输入替换后的文本:")
        if not ok or not target_text:
            return df
            
        # 在原表格内直接替换关键词
        df = df.replace(source_text, target_text)
        return df


# 全局插件，高亮指定关键词 所在行
class HighlightKeywordPlugin(TablePlugin):
    def __init__(self):
        super().__init__()
        self.highlight_keywords = {}
        self.search_task = None
        self.worker = None
        
    @property
    def name(self) -> str:
        return "关键词高亮"
        
    @property
    def description(self) -> str:
        return "高亮表格中指定的关键词所在行"
        
    @property
    def category(self) -> str:
        return "文本处理"
        
    @property
    def button_text(self) -> str:
        return "关键词高亮"
        
    def create_config_widget(self) -> None:
        return None
        
    def get_random_color(self):
        """生成随机的高亮颜色"""
        import random
        
        # 预定义一些好看的高亮颜色组合
        colors = [
            (255, 200, 200),  # 淡红色
            (200, 255, 200),  # 淡绿色
            (200, 200, 255),  # 淡蓝色
            (255, 255, 200),  # 淡黄色
            (255, 200, 255),  # 淡紫色
            (200, 255, 255),  # 淡青色
            (255, 220, 180),  # 淡橙色
            (220, 180, 255),  # 淡紫罗兰
            (180, 255, 220),  # 淡薄荷绿
            (255, 180, 220),  # 淡粉红
            (220, 255, 180),  # 淡黄绿
            (180, 220, 255),  # 淡天蓝
            (255, 240, 200),  # 淡杏色
            (240, 200, 255),  # 淡丁香紫
            (200, 255, 240),  # 淡蓝绿
            (255, 200, 180),  # 淡珊瑚色
            (200, 180, 255),  # 淡薰衣草
            (180, 255, 200)   # 淡青柠
        ]
        
        # 随机选择一个颜色组合
        r, g, b = random.choice(colors)
        return QColor(r, g, b, 120)  # 增加不透明度到120
        
    def search_keywords(self, df: pd.DataFrame, progress_callback):
        try:
            import re  # 将re的导入移到函数开始处
            
            # 读取配置文件
            with open('lovelyform/config/highlight.json', 'r', encoding='utf-8') as f:
                highlight_config = json.load(f)
                
            # 清空之前的高亮关键词
            self.highlight_keywords.clear()
                
            # 遍历所有配置的关键词
            for config in highlight_config:
                if 'keyword' in config and 'msg' in config:
                    keyword = config['keyword']
                    msg = config['msg']
                    is_regex = config.get('is_regex', False)
                    
                    try:
                        # 根据关键词类型选择不同的匹配方式
                        if is_regex:
                            # 使用正则表达式匹配
                            try:
                                pattern = re.compile(keyword, re.IGNORECASE)
                            except re.error as e:
                                print(f"正则表达式编译错误 '{keyword}': {str(e)}")
                                continue
                                
                            # 对每一列进行匹配
                            matches = []
                            matched_content = set()  # 使用set避免重复
                            
                            for col in df.columns:
                                col_str = df[col].astype(str)
                                for idx, value in col_str.items():
                                    if pattern.search(value):
                                        matches.append(idx)
                                        matched_content.add(value)
                                        
                            if matches:
                                print(f"[{keyword}] {msg}")
                                print(f"匹配到的内容: {', '.join(matched_content)}")
                                
                                # 创建掩码用于高亮显示
                                mask = df.index.isin(matches)
                                if mask.any():
                                    # 为每个关键词生成随机颜色
                                    color = self.get_random_color()
                                    self.highlight_keywords[keyword] = color
                                    
                        elif keyword.isdigit():  # 如果是纯数字（端口号）
                            # 使用正则表达式匹配端口号格式
                            pattern = re.compile(fr'\b{keyword}\b')
                            matches = []
                            matched_content = set()
                            
                            for col in df.columns:
                                col_str = df[col].astype(str)
                                for idx, value in col_str.items():
                                    if pattern.search(value):
                                        matches.append(idx)
                                        matched_content.add(value)
                                        
                            if matches:
                                print(f"[{keyword}] {msg}")
                                print(f"匹配到的内容: {', '.join(matched_content)}")
                                
                                mask = df.index.isin(matches)
                                self.highlight_keywords[keyword] = self.get_random_color()
                                
                        elif keyword.endswith('.exe'):  # 如果是进程名
                            # 进程名需要精确匹配，避免路径中的误匹配
                            pattern = re.compile(fr'(?i)\b{re.escape(keyword)}\b')
                            matches = []
                            matched_content = set()
                            
                            for col in df.columns:
                                col_str = df[col].astype(str)
                                for idx, value in col_str.items():
                                    if pattern.search(value):
                                        matches.append(idx)
                                        matched_content.add(value)
                                        
                            if matches:
                                print(f"[{keyword}] {msg}")
                                print(f"匹配到的内容: {', '.join(matched_content)}")
                                
                                mask = df.index.isin(matches)
                                self.highlight_keywords[keyword] = self.get_random_color()
                                
                        else:  # 其他关键词
                            # 普通关键词使用包含匹配
                            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                            matches = []
                            matched_content = set()
                            
                            for col in df.columns:
                                col_str = df[col].astype(str)
                                for idx, value in col_str.items():
                                    if pattern.search(value):
                                        matches.append(idx)
                                        matched_content.add(value)
                                        
                            if matches:
                                print(f"[{keyword}] {msg}")
                                print(f"匹配到的内容: {', '.join(matched_content)}")
                                
                                mask = df.index.isin(matches)
                                self.highlight_keywords[keyword] = self.get_random_color()
                                
                    except Exception as e:
                        print(f"处理关键词 '{keyword}' 时出错: {str(e)}")
                        continue
                        
            return df
        except Exception as e:
            QMessageBox.warning(None, "错误", f"读取配置文件失败: {str(e)}")
            return df
            
    def process_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理表格数据"""
        if not hasattr(self, 'highlight_keywords'):
            self.highlight_keywords = {}
            
        print("开始处理表格数据...")
        # 开始搜索关键词
        self.search_keywords(df, self.update_progress)
        
        #print(f"高亮关键词和颜色: {self.highlight_keywords}")
        # 返回原始DataFrame，高亮效果会通过 highlight_keywords 属性传递给表格模型
        return df
        
    def update_progress(self, value):
        # 更新进度条或状态栏
        print(f"搜索进度: {value}%")
        
class SearchWorker(QObject):
    finished = Signal()
    progress = Signal(int)
    
    def __init__(self, df):
        super().__init__()
        self.df = df
        
    def run(self):
        # 执行搜索操作
        HighlightKeywordPlugin().search_keywords(self.df, self.progress)
        self.finished.emit()
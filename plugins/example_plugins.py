import pandas as pd
from typing import List
import re
import importlib
from plugins import CellPlugin, TablePlugin

class UpperCaseCellPlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "转大写"
    
    @property
    def description(self) -> str:
        return "将选中的单元格内容转换为大写"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*name*", "*title*", "*description*"]  # 只处理包含这些关键词的列

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        for row, col in selected_cells:
            value = df.iloc[row, col]
            if isinstance(value, str):
                df.iloc[row, col] = value.upper()
        return df

class TimelinePlugin(CellPlugin):
    @property
    def name(self) -> str:
        return "时间戳转换"
    
    @property
    def description(self) -> str:
        return "将UNIX时间戳转换为可读时间"
        
    @property
    def file_pattern(self) -> str:
        return "*timeline*.csv"
        
    @property
    def column_patterns(self) -> List[str]:
        return ["*Time*", "*Date*", "Timestamp"]  # 只处理时间相关的列

    def process_cells(self, df: pd.DataFrame, selected_cells: List[tuple]) -> pd.DataFrame:
        from datetime import datetime
        for row, col in selected_cells:
            value = df.iloc[row, col]
            try:
                # 尝试将值转换为时间戳
                timestamp = float(value)
                # 转换为datetime对象
                dt = datetime.fromtimestamp(timestamp)
                # 格式化输出
                df.iloc[row, col] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass  # 如果转换失败，保持原值不变
        return df

class DataStatisticsPlugin(TablePlugin):
    @property
    def name(self) -> str:
        return "数据统计"
        
    @property
    def description(self) -> str:
        return "计算并显示数据统计信息"
        
    @property
    def button_text(self) -> str:
        return "数据统计"
        
    def create_config_widget(self) -> None:
        # 这个插件不需要配置界面
        return None
        
    def process_table(self, df: pd.DataFrame) -> pd.DataFrame:
        # 计算数值列的统计信息
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) == 0:
            return pd.DataFrame({"消息": ["没有找到数值类型的列"]})
            
        # 计算基本统计信息
        stats = df[numeric_cols].describe()
        
        # 添加更多统计信息
        additional_stats = pd.DataFrame({
            col: {
                '非空值数': df[col].count(),
                '空值数': df[col].isna().sum(),
                '空值比例': f"{(df[col].isna().sum() / len(df) * 100):.2f}%",
                '唯一值数': df[col].nunique(),
            } for col in numeric_cols
        })
        
        # 合并所有统计信息
        final_stats = pd.concat([stats, additional_stats])
        
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
            '非空值数': '非空值数',
            '空值数': '空值数',
            '空值比例': '空值比例',
            '唯一值数': '唯一值数'
        }
        final_stats.index = final_stats.index.map(lambda x: index_map.get(x, x))
        
        return final_stats

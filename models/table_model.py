from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from PySide6.QtGui import QColor
import pandas as pd

class PandasModel(QAbstractTableModel):
    dataChanged = Signal(QModelIndex, QModelIndex)

    def __init__(self, data: pd.DataFrame, page_offset: int = 0):
        super().__init__()
        self._data = data
        self.highlight_keywords = {}  # 改为字典，存储关键词和对应的颜色
        self.page_offset = page_offset
        # 缓存数据转换结果以提高性能
        self._str_cache = {}
        # 添加行号索引，使用DataFrame的原始索引
        self._row_indices = list(data.index)

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data.columns)

    def _get_str_value(self, row, col):
        """获取单元格的字符串值，使用缓存提高性能"""
        cache_key = (row, col)
        if cache_key not in self._str_cache:
            value = self._data.iloc[row, col]
            self._str_cache[cache_key] = str(value) if pd.notna(value) else ''
        return self._str_cache[cache_key]

    def get_absolute_row(self, row):
        """获取实际的行索引（考虑页面偏移）"""
        return row + self.page_offset

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return self._get_str_value(index.row(), index.column())
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter
        elif role == Qt.BackgroundRole and self.highlight_keywords:
            text = self._get_str_value(index.row(), index.column()).lower()
            for keyword, color in self.highlight_keywords.items():
                if keyword.lower() in text:
                    return color
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            else:
                # 使用原始索引获取行号
                original_index = self._row_indices[section]
                return str(original_index + 1)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            try:
                # 更新DataFrame中的值
                self._data.iloc[row, col] = value
                # 清除该单元格的缓存
                self._str_cache.pop((row, col), None)
                # 发出数据改变信号
                self.dataChanged.emit(index, index)
                return True
            except Exception as e:
                print(f"设置数据时出错: {str(e)}")
                return False
        return False

    def update_data(self, new_data: pd.DataFrame):
        """更新模型的数据"""
        self.beginResetModel()
        self._data = new_data
        # 更新行号索引，保持原始索引
        self._row_indices = list(new_data.index)
        self._str_cache.clear()  # 清除缓存
        self.endResetModel()

    def clear_cache(self):
        """清除字符串缓存"""
        self._str_cache.clear()

    def sort(self, column, order):
        """排序功能 - 保持原始行号顺序，禁用排序"""
        return False

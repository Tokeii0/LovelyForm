from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor
import pandas as pd

class PandasModel(QAbstractTableModel):
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        self._data = data
        self.highlight_text = ""
        # 缓存数据转换结果以提高性能
        self._str_cache = {}

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data.columns)

    def _get_str_value(self, row, col):
        # 使用缓存来避免重复的字符串转换
        cache_key = (row, col)
        if cache_key not in self._str_cache:
            value = self._data.iloc[row, col]
            self._str_cache[cache_key] = str(value)
        return self._str_cache[cache_key]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return self._get_str_value(index.row(), index.column())
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter
        elif role == Qt.BackgroundRole and self.highlight_text:
            text = self._get_str_value(index.row(), index.column()).lower()
            if self.highlight_text.lower() in text:
                return QColor(255, 255, 0, 70)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(section + 1)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter
        return None

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsEditable

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            self._data.iloc[index.row(), index.column()] = value
            # 清除缓存的字符串值
            self._str_cache.pop((index.row(), index.column()), None)
            return True
        return False

    def clear_cache(self):
        """清除字符串缓存"""
        self._str_cache.clear()

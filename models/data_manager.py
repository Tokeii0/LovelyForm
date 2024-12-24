from PySide6.QtCore import QObject, Signal, QThread
import pandas as pd
import numpy as np

class DataLoadThread(QThread):
    chunk_loaded = Signal(pd.DataFrame)
    finished = Signal()
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, file_path, chunk_size=10000):
        super().__init__()
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.is_running = True

    def run(self):
        try:
            total_rows = sum(1 for _ in open(self.file_path, 'r', encoding='utf-8')) - 1
            chunks = pd.read_csv(self.file_path, chunksize=self.chunk_size)
            loaded_rows = 0

            for chunk in chunks:
                if not self.is_running:
                    break
                self.chunk_loaded.emit(chunk)
                loaded_rows += len(chunk)
                progress = int((loaded_rows / total_rows) * 100)
                self.progress.emit(progress)

            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.is_running = False

class DataSorterThread(QThread):
    progress = Signal(int)
    finished = Signal(object, str)  # DataFrame, error message

    def __init__(self, df, column, ascending=True):
        super().__init__()
        self.df = df.copy()
        self.column = column
        self.ascending = ascending

    def run(self):
        try:
            # 执行排序
            self.df.sort_values(by=self.column, ascending=self.ascending, inplace=True)
            self.df.reset_index(drop=True, inplace=True)
            self.finished.emit(self.df, "")
        except Exception as e:
            self.finished.emit(None, str(e))

class DataManager(QObject):
    data_changed = Signal()
    sort_changed = Signal()
    progress = Signal(int)

    def __init__(self):
        super().__init__()
        self.df = pd.DataFrame()
        self.sort_column = None
        self.sort_order = None
        self.load_thread = None
        self.sort_thread = None

    def load_csv(self, file_path):
        if self.load_thread and self.load_thread.isRunning():
            self.load_thread.stop()
            self.load_thread.wait()

        self.df = pd.DataFrame()
        self.load_thread = DataLoadThread(file_path)
        self.load_thread.chunk_loaded.connect(self.append_chunk)
        self.load_thread.progress.connect(lambda p: self.progress.emit(p))
        self.load_thread.start()  # 启动线程
        return self.load_thread

    def load_file(self, file_path):
        """加载文件（CSV格式）
        这是load_csv方法的别名，为了保持API一致性
        """
        return self.load_csv(file_path)

    def append_chunk(self, chunk):
        if self.df.empty:
            self.df = chunk
        else:
            self.df = pd.concat([self.df, chunk], ignore_index=True)
        
        if self.sort_column is not None:
            self.sort_data(self.sort_column, self.sort_order, apply_immediately=True)
        
        self.data_changed.emit()

    def sort_data(self, column, order='ascending', apply_immediately=False):
        """
        对数据进行排序
        :param column: 排序列名
        :param order: 'ascending' 或 'descending'
        :param apply_immediately: 是否立即应用排序
        """
        self.sort_column = column
        self.sort_order = order
        
        if apply_immediately and not self.df.empty:
            try:
                ascending = order == 'ascending'
                if len(self.df) > 100000:  # 大数据量使用线程排序
                    self.sort_thread = DataSorterThread(self.df, column, ascending)
                    self.sort_thread.finished.connect(self._on_sort_finished)
                    self.sort_thread.start()
                else:  # 小数据量直接排序
                    self.df.sort_values(by=column, ascending=ascending, inplace=True)
                    self.df.reset_index(drop=True, inplace=True)
                    self.sort_changed.emit()
            except Exception as e:
                print(f"排序错误: {str(e)}")

    def _on_sort_finished(self, sorted_df, error):
        """排序完成的处理"""
        if error:
            print(f"排序错误: {error}")
        elif sorted_df is not None:
            self.df = sorted_df
            self.sort_changed.emit()

    def get_data(self, start=None, end=None):
        """获取指定范围的数据"""
        if start is None or end is None:
            return self.df
        return self.df.iloc[start:end]

    def get_total_rows(self):
        """获取总行数"""
        return len(self.df)

    def create_sorter_thread(self, column_name: str, ascending: bool = True) -> 'DataSorterThread':
        """创建排序线程"""
        return DataSorterThread(self.df, column_name, ascending)

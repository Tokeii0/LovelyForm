from PySide6.QtWidgets import QStyledItemDelegate, QLineEdit
from PySide6.QtCore import Qt

class TableItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor
        
    def setEditorData(self, editor, index):
        # 获取当前单元格的值
        value = index.data(Qt.DisplayRole)
        editor.setText(value)
        # 全选文本
        editor.selectAll()
        
    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, value, Qt.EditRole)

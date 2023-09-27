import sqlite3
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QPushButton, \
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QDialog
from .input_dialog import MultiInputDialog

from .db import DATABASE
class ClassesEditorWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        actions_layout = QHBoxLayout()

        self.table_widget = QTableWidget(self)

        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_widget)

        btn_add = QPushButton('Add', self)
        btn_add.clicked.connect(self.add_item)
        actions_layout.addWidget(btn_add)

        btn_edit = QPushButton('Edit', self)
        btn_edit.clicked.connect(self.edit_item)
        actions_layout.addWidget(btn_edit)

        btn_delete = QPushButton('Delete', self)
        btn_delete.clicked.connect(self.delete_item)
        actions_layout.addWidget(btn_delete)

        layout.addLayout(actions_layout)

        self.setLayout(layout)

        self.load_data()

    def load_data(self):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM classes")

        # Set column count and headers
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(['ID', 'Class ID', 'Class Name', 'RGBA'])

        self.table_widget.setRowCount(0)
        for row_number, row_data in enumerate(cursor):
            self.table_widget.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.table_widget.setItem(row_number, column_number, QTableWidgetItem(str(data)))

        # Optional: Resize columns to fit contents
        self.table_widget.resizeColumnsToContents()
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        conn.close()

    def add_item(self):
        dialog = MultiInputDialog()
        result = dialog.exec_()
        if result == QDialog.Accepted:
            class_id, class_name, rgba = dialog.get_values()
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO classes (class_id, class, rgba) VALUES (?, ?, ?)", (class_id, class_name, rgba))
            conn.commit()
            conn.close()
            self.load_data()
            self.parent.load_classes()

    def edit_item(self):
        row = self.table_widget.currentRow()
        old_data = (
            self.table_widget.item(row, 0).text(),
            self.table_widget.item(row, 1).text(),
            self.table_widget.item(row, 2).text(),
            self.table_widget.item(row, 3).text()
        )

        dialog = MultiInputDialog(old_data=old_data)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            class_id, class_name, rgba = dialog.get_values()
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("UPDATE classes SET class_id=?, class=?, rgba=? WHERE id=?",
                           (class_id, class_name, rgba, old_data[0]))
            conn.commit()
            conn.close()
            self.load_data()
            self.parent.load_classes()

    def delete_item(self):
        row = self.table_widget.currentRow()
        class_id = int(self.table_widget.item(row, 0).text())  # Convert to integer
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM classes WHERE id = ?", (class_id,))
        conn.commit()
        conn.close()
        self.load_data()
        self.parent.load_classes()
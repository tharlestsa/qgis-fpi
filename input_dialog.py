from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QLineEdit, QHBoxLayout
class MultiInputDialog(QDialog):
    def __init__(self, old_data=None):
        super().__init__()

        self.layout = QHBoxLayout()

        self.lbl_class_id = QLabel("Class ID")
        self.layout.addWidget(self.lbl_class_id)

        self.txt_class_id = QLineEdit(self)
        self.layout.addWidget(self.txt_class_id)

        self.lbl_class = QLabel("Class Name")
        self.layout.addWidget(self.lbl_class)

        self.txt_class = QLineEdit(self)
        self.layout.addWidget(self.txt_class)

        self.lbl_rgba = QLabel("RGBA")
        self.layout.addWidget(self.lbl_rgba)

        self.txt_rgba = QLineEdit(self)
        self.layout.addWidget(self.txt_rgba)

        if old_data:  # If old_data is provided (in edit mode)
            self.txt_class_id.setText(str(old_data[1]))
            self.txt_class.setText(old_data[2])
            self.txt_rgba.setText(old_data[3])

        self.btn_ok = QPushButton('OK', self)
        self.btn_ok.clicked.connect(self.accept)
        self.layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.clicked.connect(self.reject)
        self.layout.addWidget(self.btn_cancel)

        self.setLayout(self.layout)

    def get_values(self):
        return self.txt_class_id.text(), self.txt_class.text(), self.txt_rgba.text()
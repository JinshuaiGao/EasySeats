import sys
import json
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QFrame, QComboBox, QLineEdit, QLabel,
                               QMenuBar, QMenu, QMessageBox, QScrollArea, QPushButton,
                               QSizePolicy, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIntValidator


# 座位类型样式
seat_style = """
QFrame {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #e6f7ff, stop:1 #bae7ff);
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #e6f7ff, stop:1 #bae7ff);
}
"""

# 过道类型样式
aisle_style = """
QFrame {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #f6ffed, stop:1 #d9f7be);
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #f6ffed, stop:1 #d9f7be);
}
"""


class ColumnWidget(QFrame):
    def __init__(self, parent=None, remove_callback=None):
        super().__init__(parent)
        self.remove_callback = remove_callback

        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setMaximumWidth(200)

        # 设置尺寸策略，使高度可以扩展
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)

        # 类型选择 - 修改为两行布局
        type_label = QLabel("类型:")
        type_label.setAlignment(Qt.AlignLeft)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["座位", "过道"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        # 类型选择器宽度撑满
        self.type_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 座位类型的控件
        self.seat_widget = QWidget()
        seat_layout = QVBoxLayout()

        length_layout = QHBoxLayout()
        length_label = QLabel("可用长度:")
        self.length_input = QLineEdit()
        self.length_input.setPlaceholderText("输入座位数量（整数）")
        # 添加整数验证器
        self.length_input.setValidator(QIntValidator(1, 999, self))
        self.length_input.textChanged.connect(self.validate_inputs)
        length_layout.addWidget(length_label)
        length_layout.addWidget(self.length_input)

        start_layout = QHBoxLayout()
        start_label = QLabel("列首空长度:")
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("列首空出的座位数量（整数）")
        # 添加整数验证器
        self.start_input.setValidator(QIntValidator(0, 999, self))
        self.start_input.textChanged.connect(self.validate_inputs)
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_input)

        seat_layout.addLayout(length_layout)
        seat_layout.addLayout(start_layout)
        self.seat_widget.setLayout(seat_layout)

        # 过道类型的控件
        self.aisle_widget = QWidget()
        aisle_layout = QVBoxLayout()
        aisle_label = QLabel("显示文字:")
        self.aisle_input = QLineEdit()
        self.aisle_input.setPlaceholderText("输入文字")

        # 设置过道输入框的尺寸策略，使其可以扩展
        self.aisle_input.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)

        aisle_layout.addWidget(aisle_label)
        aisle_layout.addWidget(self.aisle_input)
        self.aisle_widget.setLayout(aisle_layout)

        # 删除按钮
        self.delete_btn = QPushButton("删除列")
        self.delete_btn.clicked.connect(self.remove_column)

        # 添加到主布局
        self.layout.addWidget(type_label)
        self.layout.addWidget(self.type_combo)  # 直接添加，不再居中
        self.layout.addWidget(self.seat_widget)
        self.layout.addWidget(self.aisle_widget)

        # 添加弹性空间，使内容在顶部，删除按钮在底部
        self.layout.addStretch(1)
        self.layout.addWidget(self.delete_btn)

        self.setLayout(self.layout)

        # 初始显示状态
        self.on_type_changed("座位")

    def on_type_changed(self, text):
        if text == "座位":
            self.seat_widget.show()
            self.aisle_widget.hide()
            # 恢复控件宽度
            self.setMaximumWidth(200)

            # 重置座位输入框的尺寸策略
            self.length_input.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.start_input.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # 设置座位类型的背景颜色
            self.setStyleSheet(seat_style)
        else:
            self.seat_widget.hide()
            self.aisle_widget.hide()  # 过道时不显示任何内容
            # 缩小控件宽度
            self.setMaximumWidth(100)

            # 设置过道类型的背景颜色
            self.setStyleSheet(aisle_style)

    def validate_inputs(self):
        """验证座位类型的输入是否为有效整数"""
        if self.type_combo.currentText() == "座位":
            # 检查长度输入
            length_valid = self.length_input.hasAcceptableInput()
            # 检查起始编号输入
            start_valid = self.start_input.hasAcceptableInput()

            # 设置输入框样式
            if not length_valid and self.length_input.text():
                self.length_input.setStyleSheet("background-color: #ffcccc;")
            else:
                self.length_input.setStyleSheet("")

            if not start_valid and self.start_input.text():
                self.start_input.setStyleSheet("background-color: #ffcccc;")
            else:
                self.start_input.setStyleSheet("")

            return length_valid and start_valid
        return True

    def is_valid(self):
        """检查当前列的数据是否有效"""
        if self.type_combo.currentText() == "座位":
            # 对于座位类型，长度和起始编号必须为有效整数
            length_valid = self.length_input.hasAcceptableInput() and self.length_input.text()
            start_valid = self.start_input.hasAcceptableInput() and self.start_input.text()
            return length_valid and start_valid
        elif self.type_combo.currentText() == "过道":
            # 对于过道类型，显示文字可以为空
            return True
        return False

    def remove_column(self):
        if self.remove_callback:
            self.remove_callback(self)

    def get_data(self):
        data = {
            "type": "seats" if self.type_combo.currentText() == "座位" else "way",
            "length": int(self.length_input.text()) if self.type_combo.currentText() == "座位" else 0,
            "start": int(self.start_input.text()) if self.type_combo.currentText() == "座位" else 0,
            "text": self.aisle_input.text() if self.type_combo.currentText() == "过道" else ""
        }
        return data

    def set_data(self, data):
        type = "座位" if data["type"] == "seats" else "过道"
        self.type_combo.setCurrentText(type)
        self.length_input.setText(str(data["length"]))
        self.start_input.setText(str(data["start"]))
        self.aisle_input.setText(data.get("text", ""))
        # 根据类型设置宽度
        self.on_type_changed(type)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("课室座位布局管理器")
        self.resize(800, 600)

        self.current_file = None
        self.columns = []

        self.init_ui()

    def init_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 创建菜单栏
        self.create_menu_bar()

        # 添加讲台标识
        platform_frame = QFrame()
        platform_frame.setFrameStyle(QFrame.Box)
        platform_frame.setLineWidth(1)
        platform_frame.setFixedHeight(40)
        platform_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        platform_layout = QHBoxLayout()
        platform_label = QLabel("讲台")
        platform_label.setAlignment(Qt.AlignCenter)
        platform_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        platform_layout.addWidget(platform_label)
        platform_frame.setLayout(platform_layout)

        main_layout.addWidget(platform_frame)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 创建滚动区域的内部部件
        self.scroll_widget = QWidget()
        self.columns_layout = QHBoxLayout(self.scroll_widget)
        self.columns_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.columns_layout.setSpacing(10)  # 设置列间距

        # 设置滚动区域的部件
        scroll_area.setWidget(self.scroll_widget)

        # 添加列按钮 - 宽度撑满窗口
        add_column_btn = QPushButton("添加列")
        add_column_btn.clicked.connect(self.add_column)
        add_column_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        add_column_btn.setFixedHeight(30)

        main_layout.addWidget(scroll_area)
        main_layout.addWidget(add_column_btn)

        central_widget.setLayout(main_layout)

        # 初始添加一个列
        self.add_column()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        # 新增新建选项
        new_action = QAction("新建", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("打开", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("保存", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("另存为", self)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)

    def new_file(self):
        # 确认是否保存当前文件
        if self.columns and any(self.has_column_data()):
            reply = QMessageBox.question(
                self, "新建文件",
                "当前座位布局有未保存的更改，是否保存？",
                QMessageBox.Save | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return

        # 清除所有列
        for column in self.columns:
            column.deleteLater()
        self.columns.clear()

        # 添加一个初始列
        self.add_column()

        self.current_file = None
        self.setWindowTitle("课室座位布局管理器 - 新文件")

    def has_column_data(self):
        """检查是否有列包含数据"""
        for column in self.columns:
            data = column.get_data()
            if data["type"] == "座位" and (data["length"] or data["start"]):
                return True
            if data["type"] == "过道" and data["text"]:
                return True
        return False

    def add_column(self):
        column = ColumnWidget(remove_callback=self.remove_column)
        # 设置列的最小高度，使其撑满可用空间
        column.setMinimumHeight(450)
        self.columns_layout.addWidget(column)
        self.columns.append(column)

    def remove_column(self, column):
        if len(self.columns) > 1:  # 至少保留一列
            self.columns_layout.removeWidget(column)
            self.columns.remove(column)
            column.deleteLater()
        else:
            QMessageBox.warning(self, "警告", "至少需要保留一列！")

    def validate_all_columns(self):
        """验证所有列的数据是否有效"""
        invalid_columns = []
        for i, column in enumerate(self.columns):
            if not column.is_valid():
                invalid_columns.append(i + 1)  # 列号从1开始

        if invalid_columns:
            QMessageBox.warning(
                self,
                "输入错误",
                f"以下列的数据无效：{', '.join(map(str, invalid_columns))}\n\n"
                "请确保座位类型的列中，长度和起始编号都是有效的整数。"
            )
            return False
        return True

    def open_file(self):
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开座位布局文件", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                # 清除现有列
                for column in self.columns:
                    column.deleteLater()
                self.columns.clear()

                # 添加新列
                for column_data in data.get("map", []):
                    column = ColumnWidget(remove_callback=self.remove_column)
                    column.set_data(column_data)
                    column.setMinimumHeight(450)  # 设置最小高度
                    self.columns_layout.addWidget(column)
                    self.columns.append(column)

                self.name = data.get("name", "未命名布局")

                self.current_file = file_path
                self.setWindowTitle(f"课室座位布局管理器 - {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")

    def save_file(self):
        # 在保存前验证所有列的数据
        if not self.validate_all_columns():
            return

        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_as_file()

    def save_as_file(self):
        # 在保存前验证所有列的数据
        if not self.validate_all_columns():
            return

        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存座位表文件", "", "JSON Files (*.json)"
        )

        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'

            self._save_to_file(file_path)
            self.current_file = file_path
            self.setWindowTitle(f"课室座位布局管理器 - {file_path}")

    def _save_to_file(self, file_path):
        try:
            data = {
                "name": "未命名布局",
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "map": [column.get_data() for column in self.columns]
            }

            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "成功", f"已保存到: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

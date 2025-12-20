import sys
import os
import json
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QComboBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QDialog, QGroupBox, QMessageBox,
    QScrollArea, QGridLayout, QFrame, QDialogButtonBox, QSlider, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont

import lib


class NameDialog(QDialog):
    """命名对话框"""

    def __init__(self, default_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入文件名称")
        self.setModal(True)
        self.setFixedSize(300, 120)

        layout = QVBoxLayout()

        # 名称输入框
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        self.name_edit = QLineEdit()
        self.name_edit.setText(default_name)
        self.name_edit.setPlaceholderText("请输入文件名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_name(self):
        return self.name_edit.text().strip()


class StoredItemWidget(QFrame):
    """用于显示已存储的学生列表或布局的小部件"""
    selected = Signal(str)  # 当该项被选中时发射信号，参数为文件路径
    deleted = Signal(str)   # 当该项被删除时发射信号，参数为文件路径

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setMaximumWidth(200)

        layout = QVBoxLayout()

        # 显示文件名
        name = self.get_name(file_path)
        name_label = QLabel(name)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        # 显示文件路径（截断）
        path_label = QLabel(file_path)
        path_label.setWordWrap(True)
        path_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(path_label)

        # 按钮布局
        buttons_layout = QHBoxLayout()

        # 选择按钮
        select_btn = QPushButton("选择")
        select_btn.clicked.connect(self.on_select_clicked)
        buttons_layout.addWidget(select_btn)

        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.on_delete_clicked)
        buttons_layout.addWidget(delete_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def on_select_clicked(self):
        self.selected.emit(self.file_path)

    def on_delete_clicked(self):
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 {os.path.basename(self.file_path)} 吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.deleted.emit(self.file_path)

    def get_name(self, path) -> str:
        with open(path, 'r', encoding='utf-8') as j:
            data = json.load(j)
        return data["name"]


class ResultWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("座位安排结果")
        self.setGeometry(100, 100, 1000, 700)

        # 字体初始化
        self.size_rate = 1  # 缩放倍率(0.5~3，初始1)
        """字号是像素"""
        self.o_name_fontPixel = 25  # 初始内容字号
        self.f_name_fontPixel = 25  # 最终内容字号
        self.o_head_fontPixel = 35  # 初始标题字号
        self.f_head_fontPixel = 35  # 最终标题字号

        self.head_font = QFont()
        self.name_font = QFont()
        self.change_QFont()
        

        # 添加全屏状态标志
        self.is_fullscreen = False

        # 创建布局
        layout = QVBoxLayout()

        # 创建控制面板
        control_layout = QHBoxLayout()

        # 添加"缩放值"文字说明
        scale_label = QLabel("缩放值%")
        control_layout.addWidget(scale_label)

        # 缩放调整
        self.binding_slider = QSlider(Qt.Horizontal)
        self.binding_slider.setRange(50, 300)
        self.binding_slider.setValue(100)

        self.binding_spinbox = QSpinBox()
        self.binding_spinbox.setRange(50, 300)
        self.binding_spinbox.setValue(100)

        # 双向绑定信号
        self.binding_slider.valueChanged.connect(self.binding_spinbox.setValue)
        self.binding_slider.valueChanged.connect(self.update_size_rate)
        self.binding_spinbox.valueChanged.connect(self.binding_slider.setValue)
        self.binding_spinbox.valueChanged.connect(self.update_size_rate)

        control_layout.addWidget(self.binding_slider)
        control_layout.addWidget(self.binding_spinbox)

        # 添加伸缩空间，将后面的元素推到右边
        control_layout.addStretch()

        # 全屏按钮（右顶格）
        self.fullscreen_btn = QPushButton("全屏")  # 改为实例变量
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        control_layout.addWidget(self.fullscreen_btn)

        # 创建表格显示区
        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(False)

        # 设置表格样式
        self.table_widget.setStyleSheet("""
            QTableWidget {
                gridline-color: black;
            }
        """)

        # 设置表头调整模式
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # 添加到主布局
        layout.addLayout(control_layout)
        layout.addWidget(self.table_widget)

        self.setLayout(layout)

        self.way_columns: list
        self.stu_dic: dict
        self.display_unit: tuple

    def toggle_fullscreen(self):
        """切换全屏状态"""
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
            self.fullscreen_btn.setText("全屏")  # 退出全屏时显示"全屏"
        else:
            self.showFullScreen()
            self.is_fullscreen = True
            self.fullscreen_btn.setText("退出全屏")  # 进入全屏时显示"退出全屏"

    def update_size_rate(self, value):
        """当缩放更新时执行"""
        self.size_rate = value/100
        self.f_head_fontPixel = int(self.o_head_fontPixel*self.size_rate)
        self.f_name_fontPixel = int(self.o_name_fontPixel*self.size_rate)
        self.auto_adjust()

    def auto_adjust(self):
        """自动调整"""
        stus = self.stu_dic
        unit = self.display_unit
        ways = self.way_columns

        # 计算所需的尺寸
        head_height_pixel = int(self.f_head_fontPixel*2)  # 讲台行的高度

        # 寻找最长名字
        __lengths = []
        for i in stus.values():
            name: str = i['name']
            __lengths.append(len(name))
        max_length = max(__lengths)

        # 姓名单元格尺寸
        normal_weight_pixel = int(max_length*self.f_name_fontPixel*1.7)
        normal_height_pixel = int(self.f_name_fontPixel*1.4)

        way_weight_pixel = int(normal_weight_pixel*0.6)  # 过道列的宽度

        # 更改尺寸
        table = self.table_widget

        # 更改讲台行高
        table.setRowHeight(0, head_height_pixel)

        # 更改普通尺寸
        for column_index in range(0, unit[0]+1):
            table.setColumnWidth(column_index, normal_weight_pixel)
        for row_index in range(1, unit[1]+1):
            table.setRowHeight(row_index, normal_height_pixel)

        # 覆写过道列宽
        for column_index in ways:
            table.setColumnWidth(column_index, way_weight_pixel)

        # 更改字号
        self.reFont()
    
    def change_QFont(self):
        """QFont更新"""
        self.head_font.setFamily("Microsoft YaHei")
        self.head_font.setBold(True)
        self.head_font.setPixelSize(self.f_head_fontPixel)

        self.name_font.setFamily("KaiTi")
        self.name_font.setPixelSize(self.f_name_fontPixel)

    def reFont(self):
        """调整字号"""
        self.change_QFont()
        stu_dic = self.stu_dic
        table = self.table_widget

        # 更改学生
        for key in stu_dic.keys():
            # 解析位置
            coords = key.strip('()').split(',')
            x, y = int(coords[0].strip()), int(coords[1].strip())+1

            # 解析学生信息
            stu_dict = stu_dic[key]
            name = stu_dict['name']
            sex = stu_dict['sex']

            # 填充数据
            item = QTableWidgetItem(name)
            item.setFont(self.name_font)
            item.setTextAlignment(Qt.AlignCenter)
            # 根据性别设置不同的背景色
            if sex:
                item.setBackground(QColor("#87CEEB"))
            else:
                item.setBackground(QColor("#FFB6C1"))
            table.setItem(y, x, item)
        
        # 更改讲台
        item = QTableWidgetItem("讲台")
        item.setFont(self.head_font)
        item.setTextAlignment(Qt.AlignCenter)
        item.setBackground(QColor("#C7C7C7"))
        table.setItem(0, 0, item)

    def show_table_data(self, data):
        """首次填充文字、合并单元格、调整缩放"""
        table = self.table_widget

        # 填充文字
        if type(data) != lib.Classs:
            # 错误情况
            table.setRowCount(1)
            table.setColumnCount(1)
            item = QTableWidgetItem(
                f"随机程序意外终止，错误代码：{'None' if data==None else data}")
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(0, 0, item)
            return

        # 成功情况
        classs = data
        (columns, rows) = classs.display_unit()

        table.setRowCount(rows)
        table.setColumnCount(columns)

        stu_dic = classs.get_processed_data()

        # 重复利用传参
        self.stu_dic = stu_dic
        self.display_unit = classs.display_unit()

        # 放置学生
        for key in stu_dic.keys():
            # 解析位置
            coords = key.strip('()').split(',')
            x, y = int(coords[0].strip()), int(coords[1].strip())+1

            # 解析学生信息
            stu_dict = stu_dic[key]
            name = stu_dict['name']
            sex = stu_dict['sex']

            # 填充数据
            item = QTableWidgetItem(name)
            item.setFont(self.name_font)
            item.setTextAlignment(Qt.AlignCenter)
            # 根据性别设置不同的背景色
            if sex:
                item.setBackground(QColor("#87CEEB"))
            else:
                item.setBackground(QColor("#FFB6C1"))
            table.setItem(y, x, item)

        # 合并过道并记录过道列
        ways = classs.way_gather()
        self.way_columns = ways  # 存储过道列索引
        for i in ways:
            table.setSpan(1, i, rows-1, 1)  # 修正行跨度

        # 合并讲台
        item = QTableWidgetItem("讲台")
        item.setBackground(QColor("#C7C7C7"))
        item.setFont(self.head_font)
        item.setTextAlignment(Qt.AlignCenter)
        table.setItem(0, 0, item)
        table.setSpan(0, 0, 1, columns)

        self.auto_adjust()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("课室座位随机生成器")
        self.setFixedSize(800, 600)

        # 初始化变量
        self.selected_student_list = None
        self.selected_layout = None

        # 设置存储文件夹路径
        self.students_folder = ".\\students"  # 学生列表存储文件夹
        self.layouts_folder = ".\\layouts"    # 布局存储文件夹

        # 确保文件夹存在
        os.makedirs(self.students_folder, exist_ok=True)
        os.makedirs(self.layouts_folder, exist_ok=True)

        # 创建中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 学生列表设置组
        student_group = QGroupBox("学生列表设置")
        student_layout = QVBoxLayout()

        # 当前选择显示
        self.current_student_label = QLabel("当前未选择学生列表")
        student_layout.addWidget(self.current_student_label)

        # 导入学生列表按钮
        import_student_btn = QPushButton("导入新学生列表")
        import_student_btn.clicked.connect(self.import_student_list)
        student_layout.addWidget(import_student_btn)

        # 已存储学生列表区域
        student_stored_label = QLabel("已存储的学生列表:")
        student_layout.addWidget(student_stored_label)

        # 创建滚动区域用于显示已存储的学生列表
        student_scroll = QScrollArea()
        student_scroll.setWidgetResizable(True)
        student_scroll.setFixedHeight(150)

        self.student_stored_widget = QWidget()
        self.student_stored_layout = QHBoxLayout()
        self.student_stored_widget.setLayout(self.student_stored_layout)
        student_scroll.setWidget(self.student_stored_widget)

        student_layout.addWidget(student_scroll)
        student_group.setLayout(student_layout)
        main_layout.addWidget(student_group)

        # 教室布局设置组
        layout_group = QGroupBox("教室布局设置")
        layout_layout = QVBoxLayout()

        # 当前选择显示
        self.current_layout_label = QLabel("当前未选择教室布局")
        layout_layout.addWidget(self.current_layout_label)

        # 导入布局按钮
        import_layout_btn = QPushButton("导入新布局")
        import_layout_btn.clicked.connect(self.import_layout)
        layout_layout.addWidget(import_layout_btn)

        # 已存储布局区域
        layout_stored_label = QLabel("已存储的教室布局:")
        layout_layout.addWidget(layout_stored_label)

        # 创建滚动区域用于显示已存储的布局
        layout_scroll = QScrollArea()
        layout_scroll.setWidgetResizable(True)
        layout_scroll.setFixedHeight(150)

        self.layout_stored_widget = QWidget()
        self.layout_stored_layout = QHBoxLayout()
        self.layout_stored_widget.setLayout(self.layout_stored_layout)
        layout_scroll.setWidget(self.layout_stored_widget)

        layout_layout.addWidget(layout_scroll)
        layout_group.setLayout(layout_layout)
        main_layout.addWidget(layout_group)

        # 开始生成按钮
        self.generate_btn = QPushButton("开始生成座位安排")
        self.generate_btn.clicked.connect(self.generate_seating)
        main_layout.addWidget(self.generate_btn)

        # 初始化扫描存储的文件
        self.scan_stored_files()

    def scan_stored_files(self):
        """扫描存储的学生列表和布局文件"""
        # 清空当前显示
        self.clear_layout(self.student_stored_layout)
        self.clear_layout(self.layout_stored_layout)

        # 扫描学生列表文件夹
        if os.path.exists(self.students_folder):
            for file_name in os.listdir(self.students_folder):
                file_path = os.path.join(self.students_folder, file_name)
                if os.path.isfile(file_path):
                    self.add_stored_student_list(file_path)

        # 扫描布局文件夹
        if os.path.exists(self.layouts_folder):
            for file_name in os.listdir(self.layouts_folder):
                file_path = os.path.join(self.layouts_folder, file_name)
                if os.path.isfile(file_path):
                    self.add_stored_layout(file_path)

    def clear_layout(self, layout):
        """清空布局中的所有小部件"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def import_student_list(self):
        """导入学生列表"""
        # 选择文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择学生列表", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            # 显示命名对话框
            default_name = os.path.splitext(os.path.basename(file_path))[0]
            name_dialog = NameDialog(default_name, self)

            if name_dialog.exec() == QDialog.Accepted:
                name = name_dialog.get_name()

                if not name:
                    QMessageBox.warning(self, "警告", "名称不能为空!")
                    return

                # 检查名称是否已存在
                expected_filename = f"{name}.json"
                expected_path = os.path.join(
                    self.students_folder, expected_filename)
                if os.path.exists(expected_path):
                    reply = QMessageBox.question(
                        self,
                        "名称已存在",
                        f"名称 '{name}' 已存在，是否覆盖?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return

                try:
                    # 调用您的导入学生列表功能
                    operator = lib.Student_Operate()
                    operator.read_from_xlsx(file_path)

                    # 保存到JSON文件
                    file_name = operator.save_to_json(
                        name, self.students_folder)
                    dest_path = os.path.join(self.students_folder, file_name)

                    # 重新扫描存储的文件
                    self.scan_stored_files()

                    # 自动选择新导入的列表
                    self.select_student_list(dest_path)

                    QMessageBox.information(self, "成功", f"学生列表 '{name}' 导入成功!")

                except Exception as e:
                    QMessageBox.critical(self, "错误", f"导入学生列表时出错: {str(e)}")

    def import_layout(self):
        """导入布局"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择教室布局", "", "JSON Files (*.json)"
        )
        if file_path:
            file_name = time.strftime("%Y%m%d_%H%M%S", time.localtime())

            # 将文件复制到存储文件夹
            import shutil
            dest_path = os.path.join(
                self.layouts_folder, f"{file_name}.json")
            shutil.copy2(file_path, dest_path)

            with open(dest_path, 'r', encoding='utf-8') as j:
                data = json.load(j)
            name = data["name"]
            # 重新扫描存储的文件
            self.scan_stored_files()

            # 自动选择新导入的布局
            self.select_layout(dest_path)

            QMessageBox.information(self, "成功", f"布局 '{name}' 导入成功!")

    def add_stored_student_list(self, file_path):
        """添加已存储的学生列表到界面"""
        item_widget = StoredItemWidget(file_path)
        item_widget.selected.connect(self.select_student_list)
        item_widget.deleted.connect(self.delete_student_list)
        self.student_stored_layout.addWidget(item_widget)

    def add_stored_layout(self, file_path):
        """添加已存储的布局到界面"""
        item_widget = StoredItemWidget(file_path)
        item_widget.selected.connect(self.select_layout)
        item_widget.deleted.connect(self.delete_layout)
        self.layout_stored_layout.addWidget(item_widget)

    def select_student_list(self, file_path):
        """选择学生列表"""
        self.selected_student_list = file_path
        file_name = os.path.basename(file_path)
        self.current_student_label.setText(f"当前选择: {file_name}")

    def select_layout(self, file_path):
        """选择布局"""
        self.selected_layout = file_path
        file_name = os.path.basename(file_path)
        self.current_layout_label.setText(f"当前选择: {file_name}")

    def delete_student_list(self, file_path):
        """删除学生列表"""
        # 在这里接入删除学生列表功能
        os.remove(file_path)

        # 重新扫描存储的文件
        self.scan_stored_files()

        # 如果删除的是当前选中的列表，清空选择
        if self.selected_student_list == file_path:
            self.selected_student_list = None
            self.current_student_label.setText("当前未选择学生列表")

    def delete_layout(self, file_path):
        """删除布局"""
        # 在这里接入删除布局功能
        os.remove(file_path)

        # 重新扫描存储的文件
        self.scan_stored_files()

        # 如果删除的是当前选中的布局，清空选择
        if self.selected_layout == file_path:
            self.selected_layout = None
            self.current_layout_label.setText("当前未选择教室布局")

    def generate_seating(self):
        """生成座位安排"""
        # 验证必要参数
        if not self.selected_student_list:
            QMessageBox.warning(self, "警告", "请先选择学生列表!")
            return

        if not self.selected_layout:
            QMessageBox.warning(self, "警告", "请先选择教室布局!")
            return

        # 链接布局
        layout = lib.Layout_Connector(self.selected_layout)

        # 链接学生列表
        stu_op = lib.Student_Operate()
        stu_op.read_from_json(self.selected_student_list)
        stu_list = stu_op.get_stu_list()

        # 实例化班级
        classs = lib.Classs(layout)
        # 失败传错误代码，成功传随机后的Classs类
        final = classs.check(stu_list)
        if final == False:
            classs.random(stu_list)
            self.show_result_window(classs)
        else:
            self.show_result_window(final)

    def show_result_window(self, data):
        """显示结果窗口"""
        self.result_window = ResultWindow(self)

        # 使用新的方法显示表格数据
        self.result_window.show_table_data(data)

        # 显示窗口
        self.result_window.exec()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

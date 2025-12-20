import pandas as pd
import json
import random
import time


class Layout_Connector():
    """布局连接器，用于读取和处理座位布局JSON文件"""

    def __init__(self, path) -> None:
        with open(path, "r", encoding='utf-8') as j:
            data = json.load(j)

        self.create_time = data['time']  # 布局创建时间
        self.map = data['map']  # 座位布局数据

    def get_map(self) -> list:
        """获取完整的座位布局"""
        return self.map

    def get_column(self, index: int) -> dict:
        """获取指定行的布局数据"""
        return self.get_map()[index]


class Student():
    """学生类，存储学生基本信息"""

    def __init__(self, name, id, sex) -> None:
        self.name = name
        self.id = id
        self.sex = sex

    def get_data(self) -> dict:
        """获取学生数据的字典形式"""
        data = {
            "name": self.name,
            "id": self.id,
            "sex": self.sex
        }
        return data


class Seat():
    """单个座位类，包含可用状态和学生信息"""

    def __init__(self, avail: bool) -> None:
        self.avail = avail  # 座位是否可用
        self.stu: Student    # 座位上的学生，初始为None

    def dump(self, student: Student):
        """在该座位写入学生信息"""
        self.stu = student

    def get_avail(self) -> bool:
        """查询座位的可用状态"""
        return self.avail

    def get_stu(self) -> Student:
        """查询该座位的学生信息"""
        return self.stu


class Column():
    """单列类，管理一列的座位和过道"""

    def __init__(self, data: dict) -> None:
        self.column = []
        self.type = data["type"]  # 行类型："seats"或"way"
        length = data["length"] + data["start"]

        # 初始化行中的每个位置
        for i in range(length):
            booll = False if i < data["start"] else True  # 起始位置前不可用
            self.column.append(Seat(booll))

    def dump(self, index: int, stu: Student):
        """在指定位置写入学生信息"""
        if self.column[index].get_avail():
            self.column[index].dump(stu)

    def get_all_seats(self) -> list:
        """返回该行所有的座位"""
        return self.column

    def get_seat(self, index: int) -> Seat:
        """返回指定索引的座位"""
        return self.get_all_seats()[index]

    def get_all_avail_seats_index(self) -> list:
        """返回该行所有可用座位的索引列表"""
        avail = []
        for i in range(len(self.get_all_seats())):
            if self.column[i].get_avail():
                avail.append(i)
        return avail

    def get_type(self) -> str:
        """返回该行的类型"""
        return self.type


class Classs():
    """班级类，管理整个班级的座位布局和学生分配"""

    def __init__(self, layout: Layout_Connector) -> None:
        self.map = []
        # 根据布局数据创建行
        for data in layout.get_map():
            self.map.append(Column(data))
        
        self.have_random = False  # 标记是否已完成随机分配
        self.have_random_seats = []  # 已分配座位的坐标列表

        # 列举所有可用座位坐标
        self.avail_seats = []
        for x in range(len(self.map)):
            column: Column = self.map[x]
            if column.get_type() == "seats":
                for y in column.get_all_avail_seats_index():
                    self.avail_seats.append((x, y))

    def get_all_avail_seats(self) -> list:
        """获取所有可用座位坐标"""
        return self.avail_seats

    def check(self, stu_list: list):
        """
        检查布局和学生列表的合法性

        Error Code:
        -1: 空布局
        -2: 空学生列表  
        -3: 座位不足
        """
        l1 = len(self.avail_seats)
        if l1 == 0:
            return -1
        l2 = len(stu_list)
        if l2 == 0:
            return -2
        if l1 < l2:
            return -3
        return False

    def random(self, stu_list: list):
        """随机分配学生到座位"""
        if self.check(stu_list) != False:
            return

        avail_seats = self.avail_seats.copy()
        stu_list_copy = stu_list.copy()

        while stu_list_copy and avail_seats:
            # 随机选择学生和座位
            stu = stu_list_copy.pop(random.randint(0, len(stu_list_copy)-1))
            position = avail_seats.pop(random.randint(0, len(avail_seats)-1))

            self.have_random_seats.append(position)
            # 将学生分配到座位
            x, y = position[0], position[1]
            self.map[x].dump(y, stu)

        self.have_random = True

    def get_processed_data(self) -> dict:
        """获取随机后数据（仅包含被分配的座位）"""
        result = {}
        for position in self.have_random_seats:
            x, y = position[0], position[1]
            seat: Seat = self.map[x].get_seat(y)
            result[str(position)] = seat.get_stu().get_data()
        return result
    
    def display_unit(self) -> tuple:
        """输出显示所需的列、行数量"""
        column = len(self.map)
        rows = []
        for i in self.map:
            i:Column
            rows.append(len(i.get_all_seats()))
        row = max(rows)
        return (column, row+1)
    
    def way_gather(self) -> list:
        """输出需要合并的列"""
        result = []
        for index in range(len(self.map)):
            column : Column = self.map[index]
            if column.get_type() == "way":
                result.append(index)

        return result



class Student_Operate():
    def __init__(self) -> None:
        self.stu_list = []
        self.time = ''
        self.name = ''

    def read_from_xlsx(self, path):
        xlsx = pd.read_excel(path, header=0)
        for row in xlsx.itertuples(index=False, name=None):
            if row[2] == "男":
                sex = True
            else:
                sex = False
            self.stu_list.append(Student(str(row[0]), str(row[1]), sex))
    def read_from_json(self, path):
        with open(path, 'r', encoding='utf-8') as j:
            data = json.load(j)
        self.name = data['name']
        self.time = data['time']
        temp = data['stu_list']
        for i in temp:
            self.stu_list.append(Student(i['name'], i['id'], i['sex']))

    def get_stu_list(self):
        return self.stu_list
    
    def save_to_json(self, name, folder) -> str:
        file_name = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        stu_list_final = []
        for i in self.stu_list:
            i:Student
            stu_list_final.append(i.get_data())
        result = {
            'name': name,
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'stu_list': stu_list_final
        }
        with open(f'{folder}\\{file_name}.json', 'w', encoding='utf-8') as j:
            json.dump(result, j)
        return f"{file_name}.json"
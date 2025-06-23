import sys

from PyQt5.QtWidgets import QMainWindow, QApplication
import cv2
from oxeye import Ui_MainWindow
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QRect
import os
from calculate_oxy import calculate_oxy,read_image
import nrrd
import numpy as np
import csv

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        self.setupUi(self)  # 渲染页面控件

        self.number_lable = self.label_3
        self.number_lable1 = self.label_4

        self.detect_image = self.label
        self.detect_image1 = self.label_2

        # 设置路径
        self.path = ("F:\\data\\视网膜\\mask\\")
        self.path1 = ("F:\\data\\视网膜\\mask_t\\")


        self.img_list = os.listdir(self.path)
        self.img_list1 = os.listdir(self.path1)

        self.comboBox.addItems([self.img_list[i] for i in range(len(self.img_list))])
        self.comboBox.activated.connect(self.show_img)

        self.comboBox_2.addItems([self.img_list1[i] for i in range(len(self.img_list1))])
        self.comboBox_2.activated.connect(self.show_img1)

        self.pushButton_7.clicked.connect(self.exit)
        self.pushButton.clicked.connect(self.ecalculate)

        vbox = QVBoxLayout()
        self.button_width = self.pushButton_3
        vbox.addWidget(self.button_width)
        vbox.addStretch()
        self.button_width.clicked.connect(self.choose_width)

        self.button_color = self.pushButton_4
        vbox.addWidget(self.button_color)
        vbox.addStretch()
        self.button_color.clicked.connect(self.choose_color)

        # self.button_color = self.pushButton_5
        # vbox.addWidget(self.button_color)
        # vbox.addStretch()
        # self.button_color.clicked.connect(self.choose_color)

        # 选择绘画文件 按钮
        self.button_file = self.pushButton_5

        vbox.addWidget(self.button_file)
        vbox.addStretch()
        self.button_file.clicked.connect(self.show_img)



        eraser = QAction(QIcon("1239616.png"), "Eraser", self)
        eraser.setToolTip("Eraser")

        # # 工具栏
        # self.menubar = self.addToolBar("ToolBar")
        # self.menubar.addAction(eraser)




        # self.detect_image.resize(700, 550)
        # self.detect_image.move(550, 100)
        #
        # self.detect_image1.resize(700, 550)
        # self.detect_image1.move(1400, 100)
        #
        # self.number_lable.resize(200, 50)
        # self.number_lable.move(900, 700)
        #
        # self.number_lable1.resize(200, 50)
        # self.number_lable1.move(1400, 700)



    def show_img(self):
        img = self.comboBox.currentText()
        pix = QPixmap(self.path + "\\" + img)
        self.detect_image.setPixmap(pix)
        self.detect_image.setScaledContents(True)
        lable = img.split(".")[0]
        self.number_lable.setText(lable)

    def show_img1(self):
        img = self.comboBox_2.currentText()
        pix = QPixmap(self.path1 + "\\" + img)
        self.detect_image1.setPixmap(pix)
        self.detect_image1.setScaledContents(True)
        lable = img.split(".")[0]
        self.number_lable1.setText(lable)

    def choose_width(self):
        width, ok = QInputDialog.getInt(self, '选择画笔粗细', '请输入粗细：', min=1, step=1)
        if ok:
            self.lb.penwidth = width

    def choose_color(self):
        Color = QColorDialog.getColor()  # color是Qcolor
        if Color.isValid():
            self.lb.Color = Color

    def erase(self):
        self.lb.Color = Qt.white
        self.lb.setCursor(Qt.CrossCursor)
        self.lb.penwidth = self.lb.penwidth + 2


    def ecalculate(self):
        img2 = self.comboBox.currentText()
        img1 ='D:/OXeye/{name}'.format(name=img2)
        filename = os.path.splitext(img2)[0]
        mask2 = self.comboBox_2.currentText()
        mask1 = 'D:/OXeye/{name}'.format(name=mask2)
        file_extension=os.path.splitext(mask1)[0]
        mask = '{name}.nrrd'.format(name=file_extension)
        #
        #mask = r"D:\OXeye\OD_20230428121539.nrrd"
        img, mask = read_image(img1, mask)
        ves_info, art_info = calculate_oxy(img, mask.T)
        ves_info[0].sort(key=None, reverse=False)
        art_info[0].sort(key=None, reverse=False)
        n = len(ves_info[0])
        m = (0.05*n)/2
        m = int(m)
        print(ves_info[0][m:n-m])
        print(art_info[0][m:n-m])
        ves = np.mean(ves_info[0][10:n - 10])
        art = np.mean(art_info[0][10:n - 10])
        list1=[filename,ves,art]
            # import matplotlib.pyplot as plt
            # plt.figure()
            # bins = np.linspace(-5, 5, 100)
            # plt.hist(ves_info[0], bins, alpha=0.5)
            # plt.hist(art_info[0], bins, alpha=0.5)
            # plt.show()

        with open("file.csv", "a", encoding="utf-8", newline="") as f:
            # 2. 基于文件对象构建 csv写入对象
            csv_writer = csv.writer(f)
            # 3. 构建列表头
            name = ['ID', '静脉血氧', '动脉血氧']
            csv_writer.writerow(name)
            # 4. 写入csv文件内容

            csv_writer.writerow(list1)
            print("写入数据成功")
                # 5. 关闭文件
            f.close()

    def openfile(self):
        fname = QFileDialog.getOpenFileName(self, "选择图片文件", ".")
        if fname[0]:
            self.lb.pixmap = QPixmap(fname[0])

    def exit(self):
        while True:
            sys.exit(0)


def main():
    app = QApplication(sys.argv)
    mywindow = Window()
    mywindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
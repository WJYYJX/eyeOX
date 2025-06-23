import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QGridLayout ,QLineEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import shutil
from PyQt5.QtCore import QDir, QFileInfo

class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.images = []
        self.current_page = 0
        self.images_per_page = 12
        self.grid_size = 200  # 每个图片的显示大小（这里假设为200x200像素）
        self.target_path = r'C:\Users\111\Desktop\xinjiang_select\val\-4.5'
        self.current_path = None
        self.minimal_folders = []
        self.current_index = 0


    def initUI(self):
        self.setWindowTitle('图片查看器')
        self.setGeometry(300, 300, 800, 600)

        layout = QVBoxLayout()

        self.root_path_line = QLineEdit()
        self.num_line = QLineEdit()
        self.open_button = QPushButton('打开文件夹')
        self.open_button.clicked.connect(self.openFolder)
        layout.addWidget(self.root_path_line)
        layout.addWidget(self.open_button)

        self.prev_button = QPushButton('剪切')
        self.prev_button.clicked.connect(self.CutPath)
        self.prev_button.setDisabled(True)
        layout.addWidget(self.prev_button)

        self.next_button = QPushButton('下一页')
        self.next_button.clicked.connect(self.nextPage)
        self.next_button.setDisabled(True)
        layout.addWidget(self.next_button)

        self.pre_button = QPushButton('上一页')
        self.pre_button.clicked.connect(self.prePage)
        self.pre_button.setDisabled(True)
        layout.addWidget(self.pre_button)

        self.grid_layout = QGridLayout()
        self.image_labels = [QLabel() for _ in range(12)]
        for i, label in enumerate(self.image_labels):
            self.grid_layout.addWidget(label, i // 4, i % 4)

        widget = QWidget()
        widget.setLayout(self.grid_layout)
        layout.addWidget(widget)

        self.setLayout(layout)

    def openFolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        print(folder_path)
        for root, dirs, files in os.walk(folder_path):
            if not dirs:  # 如果当前目录下没有子目录，则认为是最小文件夹
                self.minimal_folders.append(root)

        if self.minimal_folders[0]:
            self.root_path_line.setText(self.minimal_folders[0])
            self.current_path = self.minimal_folders[0]
            self.images = [os.path.join(self.minimal_folders[0], f) for f in os.listdir(self.minimal_folders[0]) if
                           os.path.isfile(os.path.join(self.minimal_folders[0], f))]
            if self.images:  # 确保图片列表不为空
                self.current_page = 0
                self.updateImages()  # 先更新图片
                self.updateButtons()  # 然后更新按钮状态
            else:
                # 如果没有图片，可以清空图片列表，并禁用所有按钮（如果需要）
                self.images.clear()
                self.updateButtons()

    def updateButtons(self):
        self.prev_button.setDisabled(False)
        self.next_button.setDisabled(False)
        self.pre_button.setDisabled(False)
        # if self.current_page > 0:
        #     self.prev_button.setDisabled(True)
        # else:
        #     self.prev_button.setDisabled(False)
        #
        # if (self.current_page + 1) * self.images_per_page >= len(self.images):
        #     self.next_button.setDisabled(True)
        # else:
        #     self.next_button.setDisabled(False)

    def updateImages(self):
        for i, label in enumerate(self.image_labels):
            index = i + self.current_page * self.images_per_page
            if index < len(self.images):
                pixmap = self.loadScaledPixmap(self.images[index], self.grid_size)
                label.setPixmap(pixmap)
            else:
                label.clear()

    def loadScaledPixmap(self, image_path, size):
        original_pixmap = QPixmap(image_path)
        original_size = original_pixmap.size()

        # 计算缩放比例
        width_ratio = size / original_size.width()
        height_ratio = size / original_size.height()
        ratio = min(width_ratio, height_ratio)

        # 根据缩放比例调整图片大小
        scaled_size = original_size * ratio
        scaled_pixmap = original_pixmap.scaled(scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        return scaled_pixmap



    def CutPath(self):
        if os.path.exists(self.current_path):
            shutil.move(self.current_path, self.target_path)
            print("完成剪切")



    def nextPage(self):
        self.current_index += 1
        print(self.current_index)
        if self.minimal_folders[self.current_index]:
            self.current_path = self.minimal_folders[self.current_index]
            self.root_path_line.setText(self.current_path)
            self.images = [os.path.join(self.current_path, f) for f in os.listdir(self.current_path) if
                           os.path.isfile(os.path.join(self.current_path, f))]
            if self.images:  # 确保图片列表不为空
                self.current_page = 0
                self.updateImages()  # 先更新图片
                self.updateButtons()  # 然后更新按钮状态
            else:
                # 如果没有图片，可以清空图片列表，并禁用所有按钮（如果需要）
                self.images.clear()
                self.updateButtons()
    def prePage(self):
        self.current_index -= 1
        print(self.current_index)
        if self.minimal_folders[self.current_index]:
            self.current_path = self.minimal_folders[self.current_index]
            self.root_path_line.setText(self.current_path)
            self.images = [os.path.join(self.current_path, f) for f in os.listdir(self.current_path) if
                           os.path.isfile(os.path.join(self.current_path, f))]
            if self.images:  # 确保图片列表不为空
                self.current_page = 0
                self.updateImages()  # 先更新图片
                self.updateButtons()  # 然后更新按钮状态
            else:
                # 如果没有图片，可以清空图片列表，并禁用所有按钮（如果需要）
                self.images.clear()
                self.updateButtons()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageViewer()
    ex.show()
    sys.exit(app.exec_())

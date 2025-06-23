import cv2
import numpy as np
from skimage.morphology import skeletonize
from skimage.transform import hough_ellipse
import nrrd
import warnings
from find_single_vessel import getSkeletonIntersection

warnings.filterwarnings("error")
import csv
from calculate_oxy1 import read_image,calculate_oxy

img1 = r"C:\Users\111\Desktop\CQP\00AA0D03A3194A2EBB93D2A67D880A60\OD_20231121172625.jpg"
mask = r"C:\Users\111\Desktop\CQP-3\OD_20231121172625_result.jpg"
img, mask = read_image(img1, mask)
mask = cv2.cvtColor(mask,cv2.COLOR_BGR2GRAY)
a= np.unique(mask)
shipan = mask > 16
mask[shipan] = 3
jingmai = mask > 10
mask[jingmai] = 1
dongmai = mask > 5
mask[dongmai] = 2
b= np.unique(mask)
cv2.imshow('i',img)
cv2.waitKey(0)
cv2.imshow('ii',mask)
cv2.waitKey(0)
# =mask[:, :, 1]
# mask =mask[:, :, 1]*80
# a= np.unique(mask)
# cv2.imshow('ii',mask)
# cv2.waitKey(0)
#img, mask = read_image(img1, mask)#nrrd
ves_info, art_info = calculate_oxy(img, mask)

print(ves_info[0])
print(art_info[0])

list1=[img1,ves_info[0][0],art_info[0][0]]
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
    name = ['ID', 'ves_info', 'art_info']
    csv_writer.writerow(name)
            # 4. 写入csv文件内容

    csv_writer.writerow(list1)
    print("写入数据成功")
                # 5. 关闭文件
    f.close()
import cv2
import numpy as np
from skimage.morphology import skeletonize
from skimage.transform import hough_ellipse
import nrrd
import warnings
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
import csv


def read_image(image, mask):
    '''
    read from path
    :param image: path to image
    :param mask: path to mask
    :return: return numpy array for post process
    '''

    image = cv2.imread(image)
    mask, info = nrrd.read(mask)


    return image, mask

def read_png(image, mask):
    '''
    read from path
    :param image: path to image
    :param mask: path to mask
    :return: return numpy array for post process
    '''

    image = cv2.imread(image)
    #mask, info = nrrd.read(mask)
    mask = cv2.imread(mask)

    return image, mask
def calculate_oxy(image, mask):
    '''
    process image
    :param image: numpy array
    :param mask: numpy array
    :return: two array. (1) index 1 and index 2 is the oxygen saturation and distance
                            x, y is the index of the outer points (draw it)
    '''
    print("load imge")
    img = image
    red = img[:, :, 2]
    green = img[:, :, 1]
    print("find disk")
    mask_ves, mask_art = find_ellipse(mask)
    print("vessel process")
    oxy_ves, dis_ves, x_ves1, y_ves1, x_ves2, y_ves2 = get_oxy(red, green, mask_ves, mask_art)
    print("artery process")
    oxy_art, dis_art, x_art1, y_art1, x_art2, y_art2 = get_oxy(red, green, mask_art, mask_ves)

    return [oxy_ves, dis_ves, x_ves1, y_ves1, x_ves2, y_ves2], [oxy_art, dis_art, x_art1, y_art1, x_art2, y_art2]


def get_oxy(red, green, labels_im, labels_im1):
    map_ske = skeletonize(np.ascontiguousarray(labels_im.astype(bool)))
    # map_ske = skeletonize(labels_im.astype(bool))
    indexes = np.where(map_ske[1:-2, 1:-2] == 1)
    a = []
    distance = []
    x_ind1 = []
    y_ind1 = []
    x_ind2 = []
    y_ind2 = []
    for i in range(len(indexes[0])):
        point = [indexes[0][i] + 1, indexes[1][i] + 1]
        mode = find_direction(point, map_ske)
        if mode == None:
            continue
        results = find_min_outer(point, mode, labels_im, labels_im1, red)
        results1 = find_min_outer(point, mode, labels_im, labels_im1, green)
        if results == None:
            continue
        try:
            a.append(np.log(results[1] / results[0]) / np.log(results1[1] / results1[0]))
            distance.append(results[-1])
            x_ind1.append(results[2])
            y_ind1.append(results[3])
            x_ind2.append(results[4])
            y_ind2.append(results[5])
        except RuntimeWarning:
            continue

    return a, distance, x_ind1, y_ind1, x_ind2, y_ind2


def find_direction(point, map):
    if map[point[0] + 1, point[1]] == 1 and np.sum(map[point[0] - 1, point[1] - 1:point[1] + 2]) == 1:
        mode = 1  # 0
        return mode
    if map[point[0] - 1, point[1]] == 1 and np.sum(map[point[0] + 1, point[1] - 1:point[1] + 2]) == 1:
        mode = 2  # 180
        return mode
    if map[point[0], point[1] + 1] == 1 and np.sum(map[point[0] - 1:point[0] + 2, point[1] - 1]) == 1:
        mode = 3  # 90
        return mode
    if map[point[0], point[1] - 1] == 1 and np.sum(map[point[0] - 1:point[0] + 2, point[1] + 1]) == 1:
        mode = 4  # -90
        return mode
    if map[point[0] + 1, point[1] + 1] == 1 and np.sum(map[point[0] - 1:point[0] + 1, point[1] - 1:point[1] + 1]) > 1:
        mode = 5  # 45
        return mode
    if map[point[0] + 1, point[1] - 1] == 1 and np.sum(map[point[0] - 1:point[0] + 1, point[1]:point[1] + 2]) > 1:
        mode = 6  # -45
        return mode
    if map[point[0] - 1, point[1] + 1] == 1 and np.sum(map[point[0]:point[0] + 2, point[1] - 1:point[1] + 1]) > 1:
        mode = 7  # 135
        return mode
    if map[point[0] - 1, point[1] - 1] == 1 and np.sum(map[point[0]:point[0] + 2, point[1]:point[1] + 2]) > 1:
        mode = 8  # -135
        return mode
    return None


def checklength(image, x, y):
    if x >= image.shape[0] or y >= image.shape[1]:
        return True
    else:
        return False


def find_min_outer(point, mode, map, old_map, intensity):
    if mode == 1 or mode == 2:
        line = map[point[0], :]
        upper = point[1]
        lower = point[1]
        flag = True
        while flag:
            if line[upper + 1] == 0:
                break
            upper = upper + 1
            if upper == len(line):
                break
        while flag:
            if line[lower - 1] == 0:
                break
            lower = lower - 1
            if lower == 0:
                break
        width = upper - lower
        if width == 0:
            return None
        minimum = intensity[point[0], lower:upper].min()
        if upper + width > len(line) or lower - width < 0:
            return None
        if old_map[point[0], upper:upper + width].sum() > 1 or old_map[point[0], lower - width:lower].sum() > 1:
            return None
        if width > 20:
            if (upper - point[1]) > (point[1] - lower) * 1.2 or (upper - point[1]) * 1.2 < (point[1] - lower):
                return None
        if checklength(intensity, point[0], upper + width) or checklength(intensity, point[0], lower - width):
            return None
        outer = intensity[point[0], upper + width] / 2 + intensity[point[0], lower - width] / 2
        x_1 = point[0]
        x_2 = point[0]
        y_1 = upper + width
        y_2 = lower - width
    elif mode == 3 or mode == 4:
        line = map[:, point[1]]
        upper = point[0]
        lower = point[0]
        flag = True
        while flag:
            if line[upper + 1] == 0:
                break
            upper = upper + 1
            if upper == len(line) - 1:
                break
        while flag:
            if line[lower - 1] == 0:
                break
            lower = lower - 1
            if lower == 0:
                break
        width = upper - lower
        if width == 0:
            return None
        minimum = intensity[lower:upper, point[1]].min()
        if upper + width > len(line) or lower - width < 0:
            return None
        if old_map[upper:upper + width, point[1]].sum() > 1 or old_map[lower - width:lower, point[1]].sum() > 1:
            return None
        if width > 20:
            if (upper - point[0]) > (point[0] - lower) * 1.2 or (upper - point[0]) * 1.2 < (point[0] - lower):
                return None
        if checklength(intensity, upper + width, point[1]) or checklength(intensity, lower - width, point[1]):
            return None
        outer = intensity[upper + width, point[1]] / 2 + intensity[lower - width, point[1]] / 2
        x_1 = upper + width
        x_2 = lower - width
        y_1 = point[1]
        y_2 = point[1]
    elif mode == 5 or mode == 8:
        upper = 0
        lower = 0
        flag = True
        minimum = 1e10
        while flag:
            if map[point[0] + upper, point[1] - upper] == 1:
                if intensity[point[0] + upper, point[1] - upper] < minimum:
                    minimum = intensity[point[0] + upper, point[1] - upper]
                upper = upper + 1
            else:
                break
        while flag:
            if map[point[0] - lower, point[1] + lower] == 1:
                if intensity[point[0] - lower, point[1] + lower] < minimum:
                    minimum = intensity[point[0] - lower, point[1] + lower]
                lower = lower + 1
            else:
                break
        width = (upper + lower)
        if point[0] + width + upper >= map.shape[0] or point[1] + lower + width >= map.shape[1]:
            return None
        if point[1] - upper - width < 0 or point[0] - lower - width < 0:
            return None
        for i in range(1, width + 1):
            if old_map[point[0] + upper + i, point[1] - upper - i] > 0 or old_map[
                point[0] - lower - i, point[1] + lower + i] > 0:
                return None
        if width > 20:
            if upper > 1.2 * lower or lower > 1.2 * upper:
                return None
        if checklength(intensity, point[0] + upper + width, point[1] - upper - width) or checklength(intensity, point[
                                                                                                                    0] - lower - width,
                                                                                                     point[
                                                                                                         1] + lower + width):
            return None
        outer = intensity[point[0] + upper + width, point[1] - upper - width] / 2 + intensity[
            point[0] - lower - width, point[1] + lower + width] / 2
        x_1 = point[0] + width + upper
        x_2 = point[0] - width - lower
        y_1 = point[1] - width - upper
        y_2 = point[1] + width + lower

    elif mode == 6 or mode == 7:
        upper = 0
        lower = 0
        flag = True
        minimum = 1e10
        while flag:
            if map[point[0] + upper, point[1] + upper] == 1:
                if intensity[point[0] + upper, point[1] + upper] < minimum:
                    minimum = intensity[point[0] + upper, point[1] + upper]
                upper = upper + 1
            else:
                break
        while flag:
            if map[point[0] - lower, point[1] - lower] == 1:
                if intensity[point[0] - lower, point[1] - lower] < minimum:
                    minimum = intensity[point[0] - lower, point[1] - lower]
                lower = lower + 1
            else:
                break
        width = (upper + lower)
        if point[0] + width + upper >= map.shape[0] or point[1] + width + upper >= map.shape[1]:
            return None
        if point[1] - lower - width < 0 or point[0] - lower - width < 0:
            return None
        for i in range(1, width + 1):
            if old_map[point[0] + upper + i, point[1] + upper + i] > 0 or old_map[
                point[0] - lower - i, point[1] - lower - i] > 0:
                return None
        if width > 20:
            if upper > 1.2 * lower or lower > 1.2 * upper:
                return None
        if checklength(intensity, point[0] + width + upper, point[1] + width + upper) or checklength(intensity, point[
                                                                                                                    0] - width - lower,
                                                                                                     point[
                                                                                                         1] - width - lower):
            return None
        outer = intensity[point[0] + width + upper, point[1] + width + upper] / 2 + intensity[
            point[0] - width - lower, point[1] - width - lower] / 2
        x_1 = point[0] + width + upper
        x_2 = point[0] - width - lower
        y_1 = point[1] + width + upper
        y_2 = point[1] - width - lower
    else:
        return None
    return minimum, outer, x_1, x_2, y_1, y_2, width


def find_ellipse(mask):
    disk = np.zeros_like(mask)
    disk[mask == 3] = 200
    contours, _ = cv2.findContours(disk.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnt = contours[0]
    (x, y), radius = cv2.minEnclosingCircle(cnt)

    result = [y, x, radius]

    mask[mask == 3] = 0
    mask1 = np.zeros_like(mask)
    mask2 = np.zeros_like(mask)
    for i in range(mask.shape[0]):
        for j in range(mask.shape[1]):
            # if mask[i, j] == 0:
            #     continue
            dis = (i - result[0]) * (i - result[0]) + (j - result[1]) * (j - result[1])
            if (dis > (result[2] * result[2])) and (dis < (result[2] * result[2] * 4)):
                pass
            else:
                mask[i, j] = 0

    mask1[mask == 1] = 1
    mask2[mask == 2] = 1
    return mask1, mask2


img1 = r"C:\Users\111\Desktop\CQP\00AA0D03A3194A2EBB93D2A67D880A60\OD_20231121172625.jpg"
mask = r"C:\Users\111\Desktop\CQP-3\OD_20231121172625_result.jpg"
img, mask = read_png(img1, mask)
mask = cv2.cvtColor(mask,cv2.COLOR_BGR2GRAY)
a= np.unique(mask)
shipan = mask > 16
mask[shipan] = 3
jingmai = mask > 10
mask[jingmai] = 1
dongmai = mask > 5
mask[dongmai] = 2
b= np.unique(mask)
# cv2.imshow('ii',mask)
# cv2.waitKey(0)
# =mask[:, :, 1]
# mask =mask[:, :, 1]*80
# a= np.unique(mask)
# cv2.imshow('ii',mask)
# cv2.waitKey(0)
#img, mask = read_image(img1, mask)#nrrd
ves_info, art_info = calculate_oxy(img, mask.T)

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


plt.figure()
bins = np.linspace(-5, 5, 100)
plt.hist(ves_info[0], bins, alpha=0.5)
plt.hist(art_info[0], bins, alpha=0.5)
plt.show()


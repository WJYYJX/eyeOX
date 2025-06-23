import os

import cv2
import numpy as np
from skimage.morphology import skeletonize
from skimage.transform import hough_ellipse
import nrrd
import warnings
from find_single_vessel import getSkeletonIntersection

warnings.filterwarnings("error")
import csv


def read_image(image, mask):
    '''
    read from path
    :param image: path to image
    :param mask: path to mask
    :return: return numpy array for post process
    '''
    mask_path = mask
    image = cv2.imread(image)
    if mask_path.endswith('nrrd'):
        mask, info = nrrd.read(mask)
    else:
        mask = cv2.imread(mask, cv2.IMREAD_GRAYSCALE)

    a = np.unique(mask)
    mask1 = mask.copy()
    mask[mask1 == a[-1]] = 3
    mask[mask1 == a[-2]] = 2
    mask[mask1 == a[-3]] = 1

    if image.shape[0] == mask.shape[0]:
        pass
    else:
        mask = np.transpose(mask)

    temp_mask = np.zeros_like(mask)
    kernel = np.ones((3, 3), np.uint8)
    kernel1 = np.ones((5, 5), np.uint8)

    temp = np.zeros_like(mask)
    temp[mask == 1] = 1
    temp = cv2.erode(cv2.dilate(temp, kernel), kernel)
    temp = cv2.dilate(cv2.erode(temp, kernel1), kernel1)
    temp_mask[temp == 1] = 1

    temp = np.zeros_like(mask)
    temp[mask == 2] = 1
    temp = cv2.erode(cv2.dilate(temp, kernel), kernel)
    temp = cv2.dilate(cv2.erode(temp, kernel1), kernel1)
    temp_mask[temp == 1] = 2

    temp = np.zeros_like(mask)
    temp[mask == 3] = 1
    temp = cv2.erode(cv2.dilate(temp, kernel), kernel)
    temp = cv2.dilate(cv2.erode(temp, kernel1), kernel1)
    temp_mask[temp == 1] = 3

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
    mask_ves, mask_art = find_ellipse(mask.copy())
    print("vessel process")
    oxy_ves, _, x_ves1, y_ves1, x_ves2, y_ves2 = get_oxy(red, green, mask_ves, mask_art)
    print("artery process")
    oxy_art, _, x_art1, y_art1, x_art2, y_art2 = get_oxy(red, green, mask_art, mask_ves)

    mask1 = np.zeros_like(mask)
    mask2 = np.zeros_like(mask)
    mask3 = np.zeros_like(mask)

    mask1[mask == 1] = 1
    mask2[mask == 2] = 1

    _, dis_ves, _, _, _, _ = get_oxy(red, green, mask1, mask3, False)
    _, dis_art, _, _, _, _ = get_oxy(red, green, mask2, mask3, False)

    print("diameter process")
    labels_ves, labels_art = get_art_ves_segment(mask_ves, mask_art)

    # cv2.imwrite(r"C:\Users\xiaof\Desktop\test1.png", mask_art * 255)
    # cv2.imwrite(r"C:\Users\xiaof\Desktop\test2.png", mask_ves * 255)
    # count = 2
    # for i in labels_art[1:]:
    #     labels_art[0] = i * count + labels_art[0]
    #     count = count + 1
    # count = 2
    # for i in labels_ves[1:]:
    #     labels_ves[0] = i*count+labels_ves[0]
    #     count = count+1
    # cv2.imwrite(r"C:\Users\xiaof\Desktop\test3.png", labels_art[0] * 10)
    # cv2.imwrite(r"C:\Users\xiaof\Desktop\test4.png", labels_ves[0] * 10)
    # exit()

    radius_art = []
    radius_ves = []
    for i in labels_art:
        temp_radius = get_radius(red, i, mask2, mask3, False)
        radius_art.append(np.mean(temp_radius))
    for i in labels_ves:
        temp_radius = get_radius(red, i, mask1, mask3, False)
        radius_ves.append(np.mean(temp_radius))
    if len(radius_art) >= 6:
        radius_art = np.sort(radius_art)[-6:]
    else:
        radius_art = np.sort(radius_art)
    if len(radius_ves) >= 6:
        radius_ves = np.sort(radius_ves)[-6:]
    else:
        radius_ves = np.sort(radius_ves)

    CRAE_2 = radius_art[-1]
    CRVE_2 = radius_ves[-1]
    AVR_2 = CRAE_2 / CRVE_2

    while len(radius_art) > 1:
        if len(radius_art) % 2 == 1:
            temp = np.zeros(len(radius_art) // 2 + 1)
            for i in range(len(temp) - 1):
                temp[i] = 0.88 * np.sqrt(np.square(radius_art[i]) + np.square(radius_art[-(i + 1)]))
            temp[-1] = radius_art[len(temp) - 1]
        else:
            temp = np.zeros(len(radius_art) // 2)
            for i in range(len(temp)):
                temp[i] = 0.88 * np.sqrt(np.square(radius_art[i]) + np.square(radius_art[-(i + 1)]))
        radius_art = np.sort(temp).copy()

    while len(radius_ves) > 1:
        if len(radius_ves) % 2 == 1:
            temp = np.zeros(len(radius_ves) // 2 + 1)
            for i in range(len(temp) - 1):
                temp[i] = 0.95 * np.sqrt(np.square(radius_ves[i]) + np.square(radius_ves[-(i + 1)]))
            temp[-1] = radius_ves[len(temp) - 1]
        else:
            temp = np.zeros(len(radius_ves) // 2)
            for i in range(len(temp)):
                temp[i] = 0.95 * np.sqrt(np.square(radius_ves[i]) + np.square(radius_ves[-(i + 1)]))
        radius_ves = np.sort(temp).copy()

    CRAE_1 = radius_art[0]
    CRVE_1 = radius_ves[0]
    AVR_1 = CRAE_1 / CRVE_1

    return [oxy_ves, dis_ves, x_ves1, y_ves1, x_ves2, y_ves2], [oxy_art, dis_art, x_art1, y_art1, x_art2, y_art2], \
        [CRAE_1, CRVE_1, AVR_1, CRAE_2, CRVE_2, AVR_2]


def get_oxy(red, green, labels_im, labels_im1, flag=True):
    map_ske = skeletonize(labels_im.astype(bool))
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
        if flag and results[-1] < 2:
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


def get_radius(red, map_ske, labels_im, labels_im1, flag=True):
    indexes = np.where(map_ske[1:-2, 1:-2] == 1)
    distance = []
    for i in range(len(indexes[0])):
        point = [indexes[0][i] + 1, indexes[1][i] + 1]
        mode = find_direction(point, map_ske)
        if mode == None:
            continue
        results = find_min_outer(point, mode, labels_im, labels_im1, red)
        if results == None:
            continue
        if flag and results[-1] < 2:
            continue
        try:
            distance.append(results[-1])
        except RuntimeWarning:
            continue

    return distance


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
    len_c = 0
    index = 0
    for i, contour in enumerate(contours):
        if len_c < len(contour):
            len_c = len(contour)
            index = i
    cnt = contours[index]

    (x, y), radius = cv2.minEnclosingCircle(cnt)

    result = [y, x, radius]

    mask[mask == 3] = 0
    mask1 = np.zeros_like(mask)
    mask2 = np.zeros_like(mask)
    for i in range(mask.shape[0]):
        for j in range(mask.shape[1]):
            if mask[i, j] == 0:
                continue
            dis = (i - result[0]) * (i - result[0]) + (j - result[1]) * (j - result[1])
            if (dis > (result[2] * result[2] * 2)) and (dis < (result[2] * result[2] * 16)):
                pass
            else:
                mask[i, j] = 0

    mask1[mask == 1] = 1
    mask2[mask == 2] = 1
    return mask1, mask2


def call_calculate_oxy(img, mask):
    img, mask = read_image(img, mask)
    ves_info, art_info = calculate_oxy(img, mask.T)
    print(ves_info)
    print(art_info)
    return ves_info, art_info


def get_art_ves_segment(art, ves):
    art = skeletonize(art, method='lee')
    ves = skeletonize(ves, method='lee')

    art_num, art_labels = cv2.connectedComponents(art)
    ves_num, ves_labels = cv2.connectedComponents(ves)

    point1 = getSkeletonIntersection(art)
    point2 = getSkeletonIntersection(ves)

    labels_art = []
    for i in range(1, art_num):
        label = np.zeros_like(art_labels)
        label[art_labels == i] = 1
        flag = False
        points = []
        for point in point1:
            if label[point[1], point[0]] == 0:
                pass
            else:
                flag = True
                points.append(point)

        if flag:
            for point in points:
                label[point[1] - 1:point[1] + 2, point[0] - 1:point[0] + 2] = 0
            label_num, label_labels = cv2.connectedComponents(label.astype(np.uint8))
            for i in range(1, label_num):
                label1 = np.zeros_like(art_labels)
                label1[label_labels == i] = 1
                labels_art.append(label1)
        else:
            labels_art.append(label)

    labels_ves = []
    for i in range(1, ves_num):
        label = np.zeros_like(ves_labels)
        label[ves_labels == i] = 1
        flag = False
        points = []
        for point in point2:
            if label[point[1], point[0]] == 0:
                pass
            else:
                flag = True
                points.append(point)

        if flag:
            for point in points:
                label[point[1] - 1:point[1] + 2, point[0] - 1:point[0] + 2] = 0
            label_num, label_labels = cv2.connectedComponents(label.astype(np.uint8))
            for i in range(1, label_num):
                label1 = np.zeros_like(art_labels)
                label1[label_labels == i] = 1
                labels_ves.append(label1)
        else:
            labels_ves.append(label)
    return labels_art, labels_ves


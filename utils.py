import hashlib
from collections import Counter

import numpy as np
from PIL import ImageFont, ImageDraw
from PIL.Image import Image
from interval import Interval


def count_occurrences(strings):
    occurrences = {}

    for string in strings:
        if string in occurrences:
            occurrences[string] += 1
        else:
            occurrences[string] = 1

    result = [(string, count) for string, count in occurrences.items()]
    sorted_result = sorted(result, key=lambda x: x[1], reverse=True)
    return sorted_result


def count_char_occurrences(strings):
    merged_string = ''.join(strings)
    char_count = Counter(merged_string)
    sorted_result = sorted(char_count.items(), key=lambda x: x[1], reverse=True)
    return sorted_result


def rotate_array(array):
    rotations = len(array) - 1
    rotated_arrays = [array]

    for _ in range(rotations):
        array = array[1:] + [array[0]]  # 将数组左移一位
        rotated_arrays.append(array)

    return rotated_arrays


def find_longest_string_length(str_array):
    lengths = np.array([len(string) for string in str_array])
    return np.max(lengths)


def find_longest_array_length(arr):
    lengths = np.array([len(sub_array) for sub_array in arr])
    longest_length = lengths.max()
    return longest_length


def is_empty(image):
    extrema = image.convert("L").getextrema()
    if extrema[0] == extrema[1]:
        return True
    else:
        return False


def create_image(font_path, font_size, encoding, row_height, lines):
    font = ImageFont.truetype(font_path, font_size, encoding=encoding)
    image_height = row_height * len(lines)

    column_count = find_longest_string_length(lines)

    image = Image.new("RGB", (font_size * column_count, image_height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    y = 0
    for line in lines:
        draw.text((0, y), line, font=font, fill=(0, 0, 0))
    y += row_height

    return image


def align_text(res, threshold=0):
    res.sort(key=lambda i: (i[0][0][0]))  # 按照x排
    already_in, line_list = [], []
    for i in range(len(res)):  # i当前
        if res[i][0][0] in already_in:
            continue
        line_txt = res[i][1][0] + ""
        already_in.append(res[i][0][0])
        y_i_points = [res[i][0][0][1], res[i][0][1][1], res[i][0][3][1], res[i][0][2][1]]
        min_I_y, max_I_y = min(y_i_points), max(y_i_points)
        curr = Interval(min_I_y + (max_I_y - min_I_y) // 3, max_I_y)
        curr_mid = min_I_y + (max_I_y - min_I_y) // 2

        for j in range(i + 1, len(res)):  # j下一个
            if res[j][0][0] in already_in:
                continue
            y_j_points = [res[j][0][0][1], res[j][0][1][1], res[j][0][3][1], res[j][0][2][1]]
            min_J_y, max_J_y = min(y_j_points), max(y_j_points)
            next_j = Interval(min_J_y, max_J_y - (max_J_y - min_J_y) // 3)

            if next_j.overlaps(curr) and curr_mid in Interval(min_J_y, max_J_y):
                line_txt += (res[j][1][0] + "  ")
                already_in.append(res[j][0][0])
                curr = Interval(min_J_y + (max_J_y - min_J_y) // 3, max_J_y)
                curr_mid = min_J_y + (max_J_y - min_J_y) // 2
        line_list.append((res[i][0][0][1], line_txt))
    line_list.sort(key=lambda x: x[0])
    txt = '\n'.join([(i[1]) for i in line_list])
    return txt


def keep_largest_n(items, n, new_item):
    # if not (len(new_item["possible_unicode"]) >0 and '\u4e00' <= new_item["possible_unicode"][0] <= '\u9fff'):
    if not (len(new_item["possible_unicode"]) > 0 and 'A' <= new_item["possible_unicode"][0] <= 'Z'):
        return items

    items.append(new_item)
    sorted_items = sorted(items, key=lambda x: x['probability'], reverse=True)
    return sorted_items[:n]


kangxi_map = {"⼀": "一", "⼄": "乙", "⼆": "二", "⼈": "人", "⼉": "儿", "⼊": "入", "⼋": "八", "⼏": "几", "⼑": "刀", "⼒": "力",
              "⼔": "匕", "⼗": "十", "⼘": "卜", "⼚": "厂", "⼜": "又", "⼝": "口", "⼞": "口", "⼟": "土", "⼠": "士", "⼣": "夕",
              "⼤": "大", "⼥": "女", "⼦": "子", "⼨": "寸", "⼩": "小", "⼫": "尸", "⼭": "山", "⼯": "工", "⼰": "己", "⼲": "干",
              "⼴": "广", "⼸": "弓", "⼼": "心", "⼽": "戈", "⼿": "手", "⽀": "支", "⽂": "文", "⽃": "斗", "⽄": "斤", "⽅": "方",
              "⽆": "无", "⽇": "日", "⽈": "曰", "⽉": "月", "⽊": "木", "⽋": "欠", "⽌": "止", "⽍": "歹", "⽏": "毋", "⽐": "比",
              "⽑": "毛", "⽒": "氏", "⽓": "气", "⽔": "水", "⽕": "火", "⽖": "爪", "⽗": "父", "⽚": "片", "⽛": "牙", "⽜": "牛",
              "⽝": "犬", "⽞": "玄", "⽟": "玉", "⽠": "瓜", "⽡": "瓦", "⽢": "甘", "⽣": "生", "⽤": "用", "⽥": "田", "⽩": "白",
              "⽪": "皮", "⽫": "皿", "⽬": "目", "⽭": "矛", "⽮": "矢", "⽯": "石", "⽰": "示", "⽲": "禾", "⽳": "穴", "⽴": "立",
              "⽵": "竹", "⽶": "米", "⽸": "缶", "⽹": "网", "⽺": "羊", "⽻": "羽", "⽼": "老", "⽽": "而", "⽿": "耳", "⾁": "肉",
              "⾂": "臣", "⾃": "自", "⾄": "至", "⾆": "舌", "⾈": "舟", "⾉": "艮", "⾊": "色", "⾍": "虫", "⾎": "血", "⾏": "行",
              "⾐": "衣", "⾒": "儿", "⾓": "角", "⾔": "言", "⾕": "谷", "⾖": "豆", "⾚": "赤", "⾛": "走", "⾜": "足", "⾝": "身",
              "⾞": "车", "⾟": "辛", "⾠": "辰", "⾢": "邑", "⾣": "酉", "⾤": "采", "⾥": "里", "⾦": "金", "⾧": "长", "⾨": "门",
              "⾩": "阜", "⾪": "隶", "⾬": "雨", "⾭": "青", "⾮": "非", "⾯": "面", "⾰": "革", "⾲": "韭", "⾳": "音", "⾴": "页",
              "⾵": "风", "⾶": "飞", "⾷": "食", "⾸": "首", "⾹": "香", "⾺": "马", "⾻": "骨", "⾼": "高", "⿁": "鬼", "⿂": "鱼",
              "⿃": "鸟", "⿄": "卤", "⿅": "鹿", "⿇": "麻", "⿉": "黍", "⿊": "黑", "⿍": "鼎", "⿎": "鼓", "⿏": "鼠", "⿐": "鼻",
              "⿒": "齿", "⿓": "龙", "⿔": "龟", "⿕": "仑"}
kangxi_map_2 = {"⼀": "一", "⼄": "乙", "⼆": "二", "⼈": "人", "⼉": "儿", "⼊": "入", "⼋": "八", "⼏": "几", "⼑": "刀", "⼒": "力",
                "⼔": "匕", "⼗": "十", "⼘": "卜", "⼚": "厂", "⼜": "又", "⼝": "口", "⼞": "口", "⼟": "土", "⼠": "士", "⼤": "大",
                "⼥": "女", "⼦": "子", "⼨": "寸", "⼩": "小", "⼫": "尸", "⼭": "山", "⼯": "工", "⼰": "己", "⼲": "干", "⼴": "广",
                "⼸": "弓", "⼼": "心", "⼽": "戈", "⼿": "手", "⽀": "支", "⽂": "文", "⽃": "斗", "⽄": "斤", "⽅": "方", "⽆": "无",
                "⽇": "日", "⽈": "曰", "⽉": "月", "⽊": "木", "⽋": "欠", "⽌": "止", "⽍": "歹", "⽏": "毋", "⽐": "比", "⽑": "毛",
                "⽒": "氏", "⽓": "气", "⽔": "水", "⽕": "火", "⽖": "爪", "⽗": "父", "⽚": "片", "⽛": "牙", "⽜": "牛", "⽝": "犬",
                "⽞": "玄", "⽟": "玉", "⽠": "瓜", "⽡": "瓦", "⽢": "甘", "⽣": "生", "⽤": "用", "⽥": "田", "⽩": "白", "⽪": "皮",
                "⽫": "皿", "⽬": "目", "⽭": "矛", "⽮": "矢", "⽯": "石", "⽰": "示", "⽲": "禾", "⽳": "穴", "⽴": "立", "⽵": "竹",
                "⽶": "米", "⽸": "缶", "⽹": "网", "⽺": "羊", "⽻": "羽", "⽼": "老", "⽽": "而", "⽿": "耳", "⾁": "肉", "⾂": "臣",
                "⾃": "自", "⾄": "至", "⾆": "舌", "⾈": "舟", "⾉": "艮", "⾊": "色", "⾍": "虫", "⾎": "血", "⾏": "行", "⾐": "衣",
                "⾒": "儿", "⾓": "角", "⾔": "言", "⾕": "谷", "⾖": "豆", "⾚": "赤", "⾛": "走", "⾜": "足", "⾝": "身", "⾞": "车",
                "⾟": "辛", "⾠": "辰", "⾢": "邑", "⾣": "酉", "⾤": "采", "⾥": "里", "⾦": "金", "⾧": "长", "⾨": "门", "⾩": "阜",
                "⾪": "隶", "⾬": "雨", "⾭": "青", "⾮": "非", "⾯": "面", "⾰": "革", "⾲": "韭", "⾳": "音", "⾴": "页", "⾵": "风",
                "⾶": "飞", "⾷": "食", "⾸": "首", "⾹": "香", "⾺": "马", "⾻": "骨", "⾼": "高", "⿁": "鬼", "⿂": "鱼", "⿃": "鸟",
                "⿄": "卤", "⿅": "鹿", "⿇": "麻", "⿉": "黍", "⿊": "黑", "⿍": "鼎", "⿎": "鼓", "⿏": "鼠", "⿐": "鼻", "⿒": "齿",
                "⿓": "龙", "⼣": "夕"
                }
cjk_map = {"⺁": "厂", "⺇": "几", "⺌": "小", "⺎": "兀", "⺏": "尣", "⺐": "尢", "⺑": "𡯂", "⺒": "巳", "⺓": "幺", "⺛": "旡",
           "⺝": "月", "⺟": "母", "⺠": "民", "⺱": "冈", "⺸": "芈", "⻁": "虎", "⻄": "西", "⻅": "见", "⻆": "角", "⻇": "𧢲",
           "⻉": "贝", "⻋": "车", "⻒": "镸", "⻓": "长", "⻔": "门", "⻗": "雨", "⻘": "青", "⻙": "韦", "⻚": "页", "⻛": "风", "⻜": "飞",
           "⻝": "食", "⻡": "𩠐", "⻢": "马", "⻣": "骨", "⻤": "鬼", "⻥": "鱼", "⻦": "鸟", "⻧": "卤", "⻨": "麦", "⻩": "黄",
           "⻬": "齐", "⻮": "齿", "⻯": "竜", "⻰": "龙", "⻳": "龟", "⾅": "臼", "⼝": "口", "⼾": "户", "⼉": "儿", "⼱": "巾",
           "⺫": "目", "⺲": "目", "⺁": "厂", "⺠": "民"
           }


def convert_kangxi_to_chinese(text):
    """
    将康熙部首转换为汉字
    :param text:
    :return:
    """
    dicts = [kangxi_map, kangxi_map_2, cjk_map]

    for dictionary in dicts:
        for word in dictionary.keys():
            text = text.replace(word, dictionary[word])

    return text


def get_optional_bbox(o) -> str:
    """Bounding box of LTItem if available, otherwise empty string"""
    if hasattr(o, 'bbox'):
        return o.bbox
    return None


def rectangle_contains(rectangle1, rectangle2):
    x1, y1, x2, y2 = rectangle1
    x3, y3, x4, y4 = rectangle2

    # 检查矩形2的四个顶点是否都在矩形1内部
    if x1 <= x3 <= x4 and x1 <= x4 <= x2 and y1 <= y3 <= y4 and y1 <= y4 <= y2:
        return True
    else:
        return False


def point_inside_rectangle(point, rectangle):
    x, y = point
    x1, y1, x2, y2 = rectangle

    if x1 <= x <= x2 and y1 <= y <= y2:
        return True
    else:
        return False


def convert_pixel_pdf(rectangle, dpi):
    x1, y1, x2, y2 = rectangle
    dpi_ratio = 72.0 / dpi

    converted_rectangle = [
        x1 * dpi_ratio,
        y1 * dpi_ratio,
        x2 * dpi_ratio,
        y2 * dpi_ratio
    ]

    return converted_rectangle


def glyph_md5(font, glyph_name):
    glyph = font['glyf'][glyph_name]
    coordinates, endPts, flags = glyph.getCoordinates(font['glyf'])
    contours = []
    contour = []
    for i, (x, y) in enumerate(coordinates):
        contour.append((x, y, flags[i]))
        if i in endPts:
            contours.append(contour)
            contour = []
    string = str(contours)
    md5_hash = hashlib.md5(string.encode()).hexdigest()
    return md5_hash


def is_empty_glyph(font, glyph_name):
    glyph = font['glyf'][glyph_name]
    coordinates, endPts, flags = glyph.getCoordinates(font['glyf'])

    if len(coordinates) == 0:
        return True

    return False




def get_flag(char):
    if '1' <= char <= '9':
        return 1
    elif 'a' <= char <= 'z':
        return 2
    elif 'A' <= char <= 'Z':
        return 3
    elif '\u4e00' <= char <= '\u9fff':
        return 4
    else:
        return 5


def islandinfo(y, trigger_val, stopind_inclusive=True):
    # Setup "sentients" on either sides to make sure we have setup
    # "ramps" to catch the start and stop for the edge islands
    # (left-most and right-most islands) respectively
    y_ext = np.r_[False, y == trigger_val, False]

    # Get indices of shifts, which represent the start and stop indices
    idx = np.flatnonzero(y_ext[:-1] != y_ext[1:])

    # Lengths of islands if needed
    lens = idx[1::2] - idx[:-1:2]

    # Using a stepsize of 2 would get us start and stop indices for each island
    return list(zip(idx[:-1:2], idx[1::2] - int(stopind_inclusive))), lens


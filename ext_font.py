import random
import re
from collections import Counter

import numpy as np
from PIL import Image
from fontTools.misc.transform import Identity
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.ttLib import TTFont
from numpy import asarray
from paddleocr import PaddleOCR

from config import *
from utils import rotate_array, find_longest_array_length, is_empty, \
    keep_largest_n, convert_kangxi_to_chinese, get_flag, islandinfo, is_empty_glyph


def get_cid(pdf_unicode):
    return int(re.findall(r'\(cid\:(\d+)\)', pdf_unicode)[0])


def array_to_dict(recognized_gids):
    # 转换成为字符词典表
    gid2unicode = {}
    for item in recognized_gids:
        gid2unicode[item['gid']] = item['real_unicode']
    print(gid2unicode)
    return gid2unicode


def calculate_probability(counter):
    # 计算总数
    total_count = sum(counter.values())

    # 计算每个元素的可能性
    probabilities = Counter({key: value / total_count for key, value in counter.items()})

    return probabilities


def select_probability(probabilities, threshold):
    most_common = probabilities.most_common()

    current_probability = 0
    none_empty_probability = 0

    selected_probabilities = []
    for probability_counter in most_common:
        unicode, probability = probability_counter
        if unicode.strip() != "":
            selected_probabilities.append(probability_counter)
            none_empty_probability += probability
        current_probability += probability

        if current_probability >= threshold:
            break

    return selected_probabilities, current_probability, none_empty_probability


def statics_column(result_strings):
    column_counts = []
    for i in range(len(result_strings[0])):
        column_values = [row[i] for row in result_strings]
        counts = Counter(column_values)
        column_counts.append(counts)
    print(column_counts)
    return column_counts


class ExtFont:
    _ocr = None

    def __init__(self, pdf_font, font_file):
        self._font_file = font_file
        if font_file is not None:
            self.font = TTFont(font_file)
            self.is_sys_font = False
        else:
            self.is_sys_font = True

        # self._ocr = None
        self._gid2unicode = {}
        self._cid2unicode = {}

        if pdf_font is None:
            return

        self.font_name = pdf_font.fontname
        self.pdf_font = pdf_font
        self._pdf_unicode2cid = self.get_pdf_unicode2cid()
        return

    def _need_recognize(self):
        if self._font_file is not None:
            if self.pdf_font.unicode_map:
                if len(self.pdf_font.unicode_map.cid2unichr) != 0:
                    return False

            return True
        else:
            return False

    def run(self):
        if self._need_recognize():
            self._gid2unicode = self.glyph_to_unicode()
            self._cid2unicode = self.get_cid2unicode(self._gid2unicode)
        return

    @property
    def ocr(self):
        if self._ocr is None:
            self._ocr = PaddleOCR(lang="ch",
                                  use_gpu=use_gpu,
                                  )

        return self._ocr

    def get_pdf_unicode2cid(self):
        pdf_unicode2cid = {}

        pdf_cid2unicode = {}
        if hasattr(self.pdf_font, "cid2unicode"):
            if self.pdf_font.cid2unicode:
                pdf_cid2unicode = self.pdf_font.cid2unicode
            for cid, unicode in pdf_cid2unicode.items():
                pdf_unicode2cid[unicode] = cid

        pdf_cid2unicode = {}
        if self.pdf_font.unicode_map:
            pdf_cid2unicode = self.pdf_font.unicode_map.cid2unichr

        for cid, unicode in pdf_cid2unicode.items():
            pdf_unicode2cid[unicode] = cid

        return pdf_unicode2cid

    def get_unicode(self, pdf_unicode):
        unicode = self._get_unicode(pdf_unicode)
        decoded_unicode = convert_kangxi_to_chinese(unicode)

        return decoded_unicode

    def _get_unicode(self, pdf_unicode):
        if "cid" in pdf_unicode:
            cid = get_cid(pdf_unicode)
            return self._cid2unicode[cid]

        if len(self._cid2unicode) == 0:
            return pdf_unicode

        # 如果pdf文件中的ToUnicode不为空，用它，注意这可能导致故意加密的文件提取错误，更好的办法应该是直接忽略它，而用图形字符
        if self.pdf_font.unicode_map:
            if len(self.pdf_font.unicode_map.cid2unichr) != 0:
                return pdf_unicode

        if pdf_unicode in self._pdf_unicode2cid:
            cid = self._pdf_unicode2cid[pdf_unicode]
            if cid in self._cid2unicode:
                return self._cid2unicode[cid]

        return pdf_unicode

    def get_glyph(self, gid):
        glyph_set = self.font.getGlyphSet()
        name = self.font.getGlyphName(gid)
        return glyph_set[name]

    def get_glyphs(self, gids):
        result = []
        glyph_set = self.font.getGlyphSet()
        for gid in gids:
            name = self.font.getGlyphName(gid)
            result.append(glyph_set[name])
        return result

    def get_cmap(self):
        cmap = self.font.getBestCmap()
        if cmap is not None:
            return cmap

        for cmap in self.font['cmap'].tables:
            return cmap

    def cid_to_gid(self, unicode):
        cmap = self.get_cmap()
        glyph_name = cmap.cmap[ord(unicode)]
        glyph_id = self.font.getGlyphID(glyph_name)

        return glyph_id

    def text_to_gid(self, text):
        result = []
        for char in text:
            gid = self.cid_to_gid(char)
            result.append(gid)

        return result

    def ocr_image(self, image):
        if isinstance(image, str):
            result = self.ocr.ocr(image)
        else:
            numpy_data = asarray(image)
            result = self.ocr.ocr(numpy_data)

        return result

    def do_ocr(self, image):
        result = self.ocr_image(image)
        if (len(result[0])) == 0:
            return "", 0

        return result[0][0][1][0], result[0][0][1][1]

    @classmethod
    def merge_text(cls, result, height, count):
        text_lines = [""] * count
        lines = [[] for _ in range(count)]
        for result_item in result:
            coordinates = result_item[0]
            text_item = result_item[1]
            result_array = [sub_array[1] / height for sub_array in coordinates]
            print(result_array)
            print(text_item)

            min_value = int(min(result_array))
            max_value = int(max(result_array))

            if min_value == max_value:
                lines[max_value].append(result_item)
            else:
                lines[max_value - 1].append(result_item)

        for index in range(len(lines)):
            line = lines[index]
            line.sort(key=lambda i: (i[0][0][0]))
            text_lines[index] = ''.join([(i[1][0]) for i in line])

        return text_lines

    def recognize_multiple_chars_anchor(self, elements, anchor_gids, count):
        if len(elements) != count:
            random.shuffle(elements)

        gids = [element["gid"] for element in elements]

        glyphs = self.get_glyphs(gids)
        glyphs_array = rotate_array(glyphs)

        image = self.draw_glyphs(glyphs_array, "数序快")
        image.save('temp/temp.png')

        result = self.ocr.ocr(asarray(image))

        if len(result[0]) == 0:
            return []

        if len(result[0]) != len(elements):
            merged_strings = self.merge_text(result[0], 150, len(elements))
            result_strings = [re.split('序快|序|快', item[1:])[1:-1] for item in merged_strings]
        else:
            result_strings = [re.split('序快|序|快', item[1][0][1:])[1:-1] for item in result[0]]

        for index in range(0, len(result_strings)):
            result_strings[index] = result_strings[index][-index:] + result_strings[index][:-index]

        column_counts = statics_column(result_strings)

        recognized_elements = []
        for index in range(0, len(column_counts)):
            counter = column_counts[index]
            element = elements[index]

            if 'candicate_1' in element:
                element['candicate_1'] += counter
            else:
                element['candicate_1'] = counter

            accumulate_counter = element['candicate_1']
            element['candicate_1_p'] = calculate_probability(accumulate_counter)
            print(element)

            probability_counters = calculate_probability(counter)
            probabilities, current_probability, non_empty_probability = select_probability(probability_counters,
                                                                                           0.9)
            if len(probabilities) == 1 and non_empty_probability > 0.9:
                element["real_unicode"] = probabilities[0][0]
                recognized_elements.append(element)
                print("new recognized:")
                print(element)
                continue

            if sum(accumulate_counter.values()) >= 100:
                probabilities, current_probability, non_empty_probability = select_probability(
                    element['candicate_1_p'], 0.9)

                if len(probabilities) == 1 and non_empty_probability > 0.6:
                    recognized_elements.append(element)
                    print("new recognized:")
                    print(element)

        print(recognized_elements)
        return recognized_elements

    def recognize_chars_with_anchor(self, to_recognize_gids, anchor_gids):
        count = 15
        index = 0  # 当前元素的索引

        processed_elements = []
        empty_run_count = 0

        while len(to_recognize_gids) > 0:
            if len(to_recognize_gids) <= count:
                elements = to_recognize_gids[:]
            else:
                if index + count <= len(to_recognize_gids):
                    elements = to_recognize_gids[index:index + count]  # 依次往后取n个元素
                else:
                    elements = to_recognize_gids[index:] + to_recognize_gids[
                                                           :count - (len(to_recognize_gids) - index)]  # 循环取剩余的元素

            round_processed_elements = self.recognize_multiple_chars_anchor(elements, anchor_gids, count)  # 对元素进行处理操作
            round_processed_gids = set([element['gid'] for element in round_processed_elements])

            # 根据条件删除满足条件的元素
            to_recognize_gids = [elem for elem in to_recognize_gids if elem["gid"] not in round_processed_gids]
            processed_elements.extend(round_processed_elements)

            if len(to_recognize_gids) == 0:
                break

            if len(round_processed_elements) == 0:
                empty_run_count = empty_run_count + 1
                if empty_run_count > 3:
                    break
            else:
                empty_run_count = 0

            print("ok:%d to:%d" % (len(processed_elements), len(to_recognize_gids)))
            # 调整index的值
            index = (index + count - len(round_processed_elements)) % len(to_recognize_gids)

        return processed_elements

    def get_anchor(self, anchors):
        for anchor in anchors:
            glyph = self.get_glyph(anchor['gid'])
            image = self.draw_glyphs([[glyph]], '', 1)
            image.save("./anchors/" + anchor['possible_unicode'] + ".png")

    def glyph_to_unicode(self):
        recognized_gids = []
        to_recognize_gids = []

        best_recognized_gids = []

        # 首先单个字符识别，获得初步识别结果，并找出确定率比较高的字符，作为以后定位的锚字符
        for name, glyph in self.font.getGlyphSet().items():
            gid = self.font.getGlyphID(name)

            if is_empty_glyph(self.font, name):
                recognized_gids.append({
                    "gid": gid,
                    "real_unicode": " ",
                    "probability": 1
                })
                continue

            try:
                image = self.draw_glyphs([[glyph]])
                image.save("temp/" + name + ".png")
            except:
                recognized_gids.append({
                    "gid": gid,
                    "real_unicode": " ",
                    "probability": 1
                })
                continue

            if image is not None:
                ocr_result = self.ocr.ocr(asarray(image), det=False, rec=True, cls=False)

                if len(ocr_result[0]) == 0:
                    result = ""
                else:
                    result, probability = ocr_result[0][0]

                if result.strip() == "":
                    if is_empty(image):
                        recognized_gids.append({
                            "gid": gid,
                            "real_unicode": " ",
                            "probability": 1
                        })
                        continue
                item = {
                    "gid": gid,
                    "possible_unicode": result,
                    "real_unicode": " ",
                    "probability": probability
                }
                to_recognize_gids.append(item)
                best_recognized_gids = keep_largest_n(best_recognized_gids, 5, item)

        to_remove = []

        recognized_dict = {}
        for item in to_recognize_gids:
            probability = item["probability"]
            if probability > 0.85:
                if item["possible_unicode"] not in recognized_dict \
                        or recognized_dict[item["possible_unicode"]]["probability"] < probability:
                    if item["possible_unicode"] in recognized_dict:
                        last_item = recognized_dict[item["possible_unicode"]]
                        recognized_gids.remove(last_item)
                        to_remove.remove(last_item)

                    item["real_unicode"] = item["possible_unicode"]
                    recognized_dict[item["real_unicode"]] = item
                    recognized_gids.append(item)
                    to_remove.append(item)

        for item in to_remove:
            to_recognize_gids.remove(item)

        print(recognized_gids)
        print(len(to_recognize_gids))

        recognized_dict = set([element['real_unicode'] for element in recognized_gids])
        processed_elements = self.recognize_chars_with_anchor(to_recognize_gids, best_recognized_gids)
        to_remove = []
        for element in processed_elements:
            if element['real_unicode'] not in recognized_dict:
                recognized_gids.append(element)
                recognized_dict.add(element['real_unicode'])
                to_remove.append(element)
            else:
                print("need more strategy")
                print(element)

                most_common = element['candicate_1'].most_common()
                for counter in most_common:
                    if counter[0] != '' and counter[0] not in recognized_dict:
                        element['real_unicode'] = counter[0]
                        recognized_gids.append(element)
                        recognized_dict.add(element['real_unicode'])
                        to_remove.append(element)
                        break

        for item in to_remove:
            to_recognize_gids.remove(item)

        recognized_gids = sorted(recognized_gids, key=lambda x: x['gid'])
        print(recognized_gids)
        print(len(to_recognize_gids))

        to_remove = []
        for element in to_recognize_gids:
            most_common = element['candicate_1'].most_common()
            for counter in most_common:
                if counter[0] != '' and counter[0] not in recognized_dict:
                    element['real_unicode'] = counter[0]
                    recognized_gids.append(element)
                    recognized_dict.add(element['real_unicode'])
                    to_remove.append(element)
                    break

        for item in to_remove:
            to_recognize_gids.remove(item)

        recognized_gids = sorted(recognized_gids, key=lambda x: x['gid'])
        print(recognized_gids)
        print(len(to_recognize_gids))

        flag_array = [get_flag(element['real_unicode'][0]) for element in recognized_gids]

        island, _ = islandinfo(np.asarray(flag_array), 3)
        gaps = [(island[i][1] + 1, island[i + 1][0] - 1) for i in range(len(island) - 1)]
        for gap in gaps:
            if gap[0] == gap[1]:
                recognized_gids[gap[0]]["real_unicode"] = recognized_gids[gap[0]]["real_unicode"].upper()

        island, _ = islandinfo(np.asarray(flag_array), 2)
        gaps = [(island[i][1] + 1, island[i + 1][0] - 1) for i in range(len(island) - 1)]
        for gap in gaps:
            if gap[0] == gap[1]:
                recognized_gids[gap[0]]["real_unicode"] = recognized_gids[gap[0]]["real_unicode"].lower()

        gid2unicode = array_to_dict(recognized_gids)

        return gid2unicode

    def get_cid2unicode(self, gid_unicode_dict):
        cmap = self.get_cmap()

        cid2unicode = {}

        if hasattr(cmap, "cmap"):
            cmap = cmap.cmap

        for key, glyph_name in cmap.items():  # cmap.cmap.items():
            gid = self.font.getGlyphID(glyph_name)

            if gid in gid_unicode_dict:
                cid2unicode[key] = gid_unicode_dict[gid]

        return cid2unicode

    def draw_glyph(self, glyph):
        pen = FreeTypePen(None)
        glyph.draw(pen)

        row_height = self.get_row_height()

        width = glyph.width
        if width == 0:
            return None

        _glyph = glyph.glyphSet.glyfTable[glyph.name]

        xMin = 0
        if hasattr(_glyph, "xMin"):
            if _glyph.xMin < 0:
                xMin = -_glyph.xMin

        if xMin == -self.font['head'].xMin:
            xMin += 10

        yMin = -self.font['head'].yMin
        if hasattr(_glyph, "yMin"):
            if _glyph.yMin == yMin:
                yMin += 18

        image = pen.image(width, row_height, transform=Identity.translate(xMin, yMin))

        return image

    def draw_glyphs(self, lines, anchor='', scale=0.5):
        scale = 150.0 / self.get_row_height()
        row_height = round(self.get_row_height() * scale)
        image_height = row_height * len(lines)

        anchor_images = []
        for char in anchor:
            anchor_image = Image.open("anchors/" + char + ".png")
            anchor_scale = row_height * 1.0 / anchor_image.size[1]
            anchor_image_size = (round(anchor_image.size[0] * anchor_scale), row_height)

            anchor_image = anchor_image.resize(anchor_image_size)
            anchor_images.append(anchor_image)
            anchor_image.save("temp/anchor/" + char + ".png")

        column_count = find_longest_array_length(lines)

        if len(anchor_images) != 0:
            column_count = 1 + 3 * column_count + 2

        image_width = round(self.font["hhea"].xMaxExtent * column_count * scale)
        if len(anchor_images) != 0:
            image_width += 40
            image_height += 40

        image = Image.new("RGB", (image_width, image_height), (255, 255, 255))
        y = 0
        if len(anchor_images) != 0:
            y = 20

        for line in lines:
            x = 0
            if len(anchor_images) != 0:
                x = 20
                image.paste(anchor_images[0], (x, y))
                x += anchor_images[0].size[0]
                image.paste(anchor_images[1], (x, y))
                x += anchor_images[1].size[0]
                image.paste(anchor_images[2], (x, y))
                x += anchor_images[2].size[0]

            for glyph in line:
                glyph_image = self.draw_glyph(glyph)
                if glyph_image is None:
                    continue

                glyph_image = glyph_image.resize(tuple([round(x * scale) for x in glyph_image.size]))

                image.paste(glyph_image, (x, y), glyph_image)
                x += glyph_image.size[0]

                if len(anchor_images) != 0:
                    image.paste(anchor_images[1], (x, y))
                    x += anchor_images[1].size[0]
                    image.paste(anchor_images[2], (x, y))
                    x += anchor_images[2].size[0]

            y += row_height

        return image

    def get_row_height(self):
        y_min = self.font['head'].yMin
        y_max = self.font['head'].yMax
        row_height = round((y_max - y_min))
        return row_height

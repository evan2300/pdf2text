from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextLineHorizontal, LTAnno

from font_utils import FontUtil
from utils import get_optional_bbox, convert_pixel_pdf

region = {
    # "bbox": [5, 27, 301, 1123],
    "bbox": [0, 0, 827, 1169],
    "dpi": 100,
    "data": []
}


class TextPdf:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file
        self.font_util = None
        return

    def prepare(self):
        self.font_util = FontUtil(self.pdf_file)
        self.font_util.run()
        return

    def merge_text(self, extracted_data):
        # extracted_data 为 [[字符串段], 坐标]的集合，总共三个[[[
        sorted_data = sorted(extracted_data, key=lambda x: x[1][3], reverse=True)

        merged_lines = []
        for line in sorted_data:
            y1 = line[1][3]

            if len(merged_lines) == 0 or abs(merged_lines[-1][0][1][3] - y1) > 1:
                merged_lines.append([line])
            else:
                merged_lines[-1].append(line)

        for index in range(len(merged_lines)):
            merged_lines[index] = sorted(merged_lines[index], key=lambda x: x[1][0])

        # for index in range(len(merged_lines)):
        #     result = []
        #
        #     for line_segment in merged_lines[index]:
        #         result.extend(line_segment)
        #
        #     merged_lines[index] = result

        return merged_lines

    def extract_text(self):
        region["bbox"] = convert_pixel_pdf(region["bbox"], 100)

        pure_text = ""
        extracted_data = []
        for page_layout in extract_pages(self.pdf_file):
            width = page_layout.bbox[2] * 100 / 72
            height = page_layout.bbox[3] * 100 / 72
            print(width, height)
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        if isinstance(text_line, LTTextLineHorizontal):
                            line = []
                            current_text = ["XXXXX", -2, ""]

                            for character in text_line:
                                if isinstance(character, LTChar):
                                    font_size = round(character.size, 1)
                                    font_name = character.fontname
                                    if font_name != current_text[0] or font_size != current_text[1]:
                                        if current_text[0] != "XXXXX":
                                            line.append(current_text)
                                            current_text = ["XXXXX", -2, ""]

                                    current_text[0] = font_name
                                    current_text[1] = font_size

                                    char = character.get_text()
                                    decoded = self.font_util.get_unicode(font_name, char)
                                    current_text[2] += decoded
                                elif isinstance(character, LTAnno):
                                    current_text[2] += character.get_text()

                            if current_text[0] != "XXXXX":
                                line.append(current_text)

                            bbox = get_optional_bbox(text_line)

                            if bbox is not None:
                                extracted_data.append([line, bbox])

            extracted_data = self.merge_text(extracted_data)
            print(extracted_data)

            pure_text += self.pure_text(extracted_data)
            extracted_data = []

        return pure_text

    def pure_text(self, extracted_data):
        text = ""
        for line in extracted_data:
            for line_segments in line:
                text_segments = line_segments[0]

                for text_segment in text_segments:
                    text += text_segment[2].rstrip("\n").replace("\t", " ")

                text += " "

            text += "\n"

        return text



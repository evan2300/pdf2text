from wand.image import Image as WandImage
from wand.color import Color as WandColor
from paddleocr import PaddleOCR
from utils import *
from config import *


class ImagePdf:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file
        self.image = WandImage(filename=pdf_file, resolution=300)
        self.image.background_color = WandColor('white')
        self.image.alpha_channel = 'remove'
        self.image.format = 'png'

        return

    def extract_text(self):
        ocr = PaddleOCR(lang="ch", use_gpu=use_gpu)

        pure_text = ""
        for single_image in self.image.sequence:
            single_wand_image = WandImage(image=single_image)
            image_array = np.array(single_wand_image)
            image_array = image_array[:, :, :3]

            result = ocr.ocr(image_array)
            text = align_text(result[0])
            pure_text += text

        return pure_text

    def close(self):
        self.image.close()
        self.image = None


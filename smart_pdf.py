from text_pdf import *
from image_pdf import *


class SmartPdf:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file

        return

    def extract_text(self):
        text_pdf = TextPdf(self.pdf_file)
        text_pdf.prepare()
        text = text_pdf.extract_text()

        if text is None or text == "":
            image_pdf = ImagePdf(self.pdf_file)
            text = image_pdf.extract_text()

        return text



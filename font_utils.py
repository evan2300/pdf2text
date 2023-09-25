from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdftypes import PDFObjRef
from pdfminer.pdftypes import dict_value
from pdfreader import PDFDocument as xPDFDocument
from ext_font import ExtFont


class FontUtil:
    def __init__(self, pdf_file:str):
        self._pdf_file = pdf_file
        self._font_dict = {}

    def extract_pdf_font_file(self):
        if not hasattr(self._pdf_file, "read"):
            _pdf_file = open(self._pdf_file, "rb")

        doc = xPDFDocument(_pdf_file)
        page = next(doc.pages())

        result = {}
        if page.Resources.Font is None:
            return result

        for font_key in sorted(page.Resources.Font.keys()):
            font = page.Resources.Font[font_key]
            font_name = font_key # font["BaseFont"]

            if font.FontDescriptor is None:
                continue

            font_file = font.FontDescriptor.FontFile2
            if hasattr(font_file, "filtered"):
                data = font_file.filtered

                font_file_name = "font/" + font_name + ".ttf"
                with open(font_file_name, "wb") as f:
                    f.write(data)
                result[font_key] = font_file_name

        return result

    def extract_pdf_font(self):
        miner_font_dict = {}

        with open(self._pdf_file, 'rb') as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            resource_manager = PDFResourceManager()

            for page in PDFPage.create_pages(doc):
                for (k, v) in page.resources.items():
                    if k == "Font":
                        for (font_key, spec) in dict_value(v).items():
                            obj_id = None
                            if isinstance(spec, PDFObjRef):
                                obj_id = spec.objid
                            spec = dict_value(spec)
                            font = resource_manager.get_font(obj_id, spec)
                            miner_font_dict[font_key] = font

        return miner_font_dict

    def run(self):
        pdf_fonts = self.extract_pdf_font()
        font_files = self.extract_pdf_font_file()

        self._font_dict = {}
        for font_key, pdf_font in pdf_fonts.items():
            font_file_path = None

            if font_key in font_files:
                font_file_path = font_files[font_key]

            ext_font = ExtFont(pdf_font, font_file_path)
            ext_font.run()
            self._font_dict[pdf_font.fontname] = ext_font

        return

    def get_unicode(self, font_name, pdf_unicode):
        ext_font = self._font_dict[font_name]
        unicode = ext_font.get_unicode(pdf_unicode)
        return unicode


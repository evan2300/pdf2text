from utils import *
from fontTools.ttLib import TTFont


class FontHasher:
    def __init__(self, path):
        self.font = TTFont(path)
        return

    def get_md52unicode(self):
        cmap = self.get_cmap()

        md52unicode = {}

        for key, glyph_name in cmap.items():
            unicode = key
            md5 = glyph_md5(self.font, glyph_name)

            if md5 in md52unicode:
                print("error:" + chr(key) + " " + chr(md52unicode[md5]))

            md52unicode[md5] = unicode

        return md52unicode

    def get_cmap(self):
        cmap = self.font.getBestCmap()
        if cmap is not None:
            return cmap

        for cmap in self.font['cmap'].tables:
            return cmap

__all__ = ['BoxType', 'BoxDouble', 'BoxSingle']

import term
glyph = term.impl.convert_glyph

class BoxType(object):
    """
    A class containing the various line-drawing characters used in
    drawing CP437 boxes.
    """
    blank = ' '
    horiz = ' '
    vert = ' '
    tl = ' '
    bl = ' '
    tr = ' '
    br = ' '

    scrollbar_top = ' '
    scrollbar_bottom = ' '
    scrollbar_center = ' '

    scrollbar_center_block = glyph(0xDB)
    scrollbar_bottom_block = glyph(0xDC)
    scrollbar_top_block = glyph(0xDF)

class BoxDouble(BoxType):
    """
    A box bordered with double-line drawing characters.
    """
    blank = ' '
    horiz = glyph(0xCD)
    vert = glyph(0xBA)
    tl = glyph(0xC9)
    bl = glyph(0xC8)
    tr = glyph(0xBB)
    br = glyph(0xBC)

    scrollbar_top = glyph(0xD2)
    scrollbar_bottom = glyph(0xD0)
    scrollbar_center = glyph(0xF0)

class BoxSingle(BoxType):
    """
    A box bordered with single-line drawing characters.
    """
    horiz = glyph(0xC4)
    vert = glyph(0xB3)
    tl = glyph(0xDA)
    bl = glyph(0xC0)
    tr = glyph(0xBF)
    br = glyph(0xD9)

    scrollbar_top = glyph(0xD1)
    scrollbar_bottom = glyph(0xCF)
    scrollbar_center = glyph(0xD8)

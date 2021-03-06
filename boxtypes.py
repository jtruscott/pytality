__all__ = ['BoxType', 'BoxDouble', 'BoxSingle']

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

    scrollbar_center_block = chr(0xDB)
    scrollbar_bottom_block = chr(0xDC)
    scrollbar_top_block = chr(0xDF)

class BoxDouble(BoxType):
    """
    A box bordered with double-line drawing characters.
    """
    blank = ' '
    horiz = chr(0xCD)
    vert = chr(0xBA)
    tl = chr(0xC9)
    bl = chr(0xC8)
    tr = chr(0xBB)
    br = chr(0xBC)

    scrollbar_top = chr(0xD2)
    scrollbar_bottom = chr(0xD0)
    scrollbar_center = chr(0xF0)

class BoxSingle(BoxType):
    """
    A box bordered with single-line drawing characters.
    """
    horiz = chr(0xC4)
    vert = chr(0xB3)
    tl = chr(0xDA)
    bl = chr(0xC0)
    tr = chr(0xBF)
    br = chr(0xD9)

    scrollbar_top = chr(0xD1)
    scrollbar_bottom = chr(0xCF)
    scrollbar_center = chr(0xD8)

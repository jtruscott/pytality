class BoxType:
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

class BoxDouble(BoxType):
    blank = ' '
    horiz = chr(0xCD)
    vert = chr(0xBA)
    tl = chr(0xC9)
    bl = chr(0xC8)
    tr = chr(0xBB)
    br = chr(0xBC)

class BoxSingle(BoxType):
    horiz = chr(0xC4)
    vert = chr(0xB3)
    tl = chr(0xDA)
    bl = chr(0xC0)
    tr = chr(0xBF)
    br = chr(0xD9)

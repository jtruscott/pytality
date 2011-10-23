import winconsole
import msvcrt

import logging
log = logging.getLogger('pytality.term.winconsole')

C = winconsole.Console()

class colors:
    """
    Constants for the sixteen ANSI colors.
    On Windows, these are simple ints.
    """
    BLACK = 0
    BLUE = 1
    GREEN = 2
    CYAN = 3
    RED = 4
    MAGENTA = 5
    BROWN = 6
    LIGHTGRAY = LIGHTGREY = 7
    DARKGRAY = DARKGREY = 8
    LIGHTBLUE = 9
    LIGHTGREEN = 10
    LIGHTCYAN = 11
    LIGHTRED = 12
    LIGHTMAGENTA = 13
    YELLOW = 14
    WHITE = 15

"""
    A mapping of special keycodes into representative strings.
    Based off the keymap in WConio, but with 'alt', 'ctrl', and 'shift'
    stripped in order to be portable with the other pytality backends.
"""
key_map = {
    0x3b : 'f1',
    0x3c : 'f2',
    0x3d : 'f3',
    0x3e : 'f4',
    0x3f : 'f5',
    0x40 : 'f6',
    0x41 : 'f7',
    0x42 : 'f8',
    0x43 : 'f9',
    0x44 : 'f10',

    0x68 : 'f1',
    0x69 : 'f2',
    0x6a : 'f3',
    0x6b : 'f4',
    0x6c : 'f5',
    0x6d : 'f6',
    0x6e : 'f7',
    0x6f : 'f8',
    0x70 : 'f9',
    0x71 : 'f10',

    0x5e : 'f1',
    0x5f : 'f2',
    0x60 : 'f3',
    0x61 : 'f4',
    0x62 : 'f5',
    0x63 : 'f6',
    0x64 : 'f7',
    0x65 : 'f8',
    0x66 : 'f9',
    0x67 : 'f10',

    0x54 : 'f1',
    0x55 : 'f2',
    0x56 : 'f3',
    0x57 : 'f4',
    0x58 : 'f5',
    0x59 : 'f6',
    0x5a : 'f7',
    0x5b : 'f8',
    0x5c : 'f9',
    0x5d : 'f10',

    0x52 : 'ins',
    0x53 : 'del',
    0x4f : 'end',
    0x50 : 'down',
    0x51 : 'pgdn',
    0x4b : 'left',
    0x4d : 'right',
    0x47 : 'home',
    0x48 : 'up',
    0x49 : 'pgup',

    0xa2 : 'ins',
    0xa3 : 'del',
    0x9f : 'end',
    0xa0 : 'down',
    0xa1 : 'pgdn',
    0x9b : 'left',
    0x9d : 'right',
    0x97 : 'home',
    0x98 : 'up',
    0x99 : 'pgup',

    0x92 : 'ins',
    0x93 : 'del',
    0x75 : 'end',
    0x91 : 'down',
    0x76 : 'pgdn',
    0x73 : 'left',
    0x74 : 'right',
    0x77 : 'home',
    0x8d : 'up',
    0x84 : 'pgup',

    3 : '2'
}

def init(use_cp437=True):
    global defaultcolor
    defaultcolor = C.get_color()

    if use_cp437:
        C.set_code_page(437)

    reset()
    C.set_cursor_type(0)

#----------------------------------------------------------------------------
#Actual functions

def flip():
    backing.draw(C, backing.width, backing.height, 0, 0)

def clear():
    C.clear()

def resize(width, height):
    C.set_size(width, height)

    #build a new "backing" buffer for double buffering
    global backing
    backing = winconsole.ConsoleBuffer(width, height)
        
    
def reset():
    C.clear_line()
    C.set_color(*defaultcolor)
    C.set_cursor_type(1)

def move_cursor(x, y):
    C.move_cursor(x, y)

def set_title(title):
    C.set_title(title)

def set_cursor_type(i):
    C.set_cursor_type(i)

def draw_buffer(source, start_x, start_y):
    #log.debug("drawing a w=%r, h=%r buffer at x=%r, y=%r", source.width, source.height, start_x, start_y)
    #log.debug("firstfour: %r", source._data[0][:4])
    #render the buffer to our backing
    y = start_y
    for row in source._data:
        if y >= backing.height:
            break
        x = start_x
        for fg, bg, ch in row[:source.width]:
            if x >= backing.width:
                break
            #log.debug("x=%r y=%r, fg=%r bg=%r ch=%r", x, y, fg, bg, ch)
            #convert the character
            try:
                coord = backing.buffer[(y*backing.width) + x]
            except:
                log.exception("could not index x=%r, y=%r", x, y)
                raise
            coord.attr = fg + (bg << 4)
            coord.ascii = ch
            
            x += 1
        y += 1

    source.dirty = False
    return

def get_at(x, y):
    coord = backing.buffer[(y*backing.width) + x]
    ch = coord.ascii
    fg = coord.attr & 0xF
    bg = (coord.attr >> 4) & 0xF
    return [fg, bg, ch]

def raw_getkey():
    key = msvcrt.getwch()
    log.debug('key: %r', key)
    nkey = ord(key)
    
    if nkey in (0, 224):
        key2 = msvcrt.getwch()
        nkey2 = ord(key2)
        log.debug('key2: %r nkey2: %r', key2, nkey2)
        if nkey2 in key_map:
            return key_map[nkey2]
        return "key%s" % key

    if key in ('\r', '\n'):
        key = 'enter'
        
    return key

import sys
import curses
import locale

import logging
import ansi
log = logging.getLogger('pytality.term.curses')
    
#Curses requires this fairly magical invocation to support unicode correctly
locale.setlocale(locale.LC_ALL,"")

"""
Conversions for the sixteen ANSI colors.
With curses, we treat these as 2-tuples of (color, bold)
"""
color_map = {
    0: (curses.COLOR_BLACK, False)
    1: (curses.COLOR_BLUE, False)
    2: (curses.COLOR_GREEN, False)
    3: (curses.COLOR_CYAN, False)
    4: (curses.COLOR_RED, False)
    5: (curses.COLOR_MAGENTA, False)
    6: (curses.COLOR_YELLOW, False)
    7: (curses.COLOR_WHITE, False)

    8: (curses.COLOR_BLACK, True)
    9: (curses.COLOR_BLUE, True)
    10: (curses.COLOR_GREEN, True)
    11: (curses.COLOR_CYAN, True)
    12: (curses.COLOR_RED, True)
    13: (curses.COLOR_MAGENTA, True)
    14: (curses.COLOR_YELLOW, True)
    15: (curses.COLOR_WHITE, True)
}

def init():
    global scr
    scr = curses.initscr()
    curses.start_color()
    scr.keypad(False)
    curses.noecho()

class Glyph(str):
    """
        A string that's already been converted from codepage 437 to unicode.
    """
    pass

def uni(c):
    """
        Convert a string from codepage 437 to unicode.
        We use Glyph shenanigans to not convert twice.
    """
    if isinstance(c, Glyph):
        return c
    return Glyph(c.decode('cp437').encode('utf-8'))

#----------------------------------------------------------------------------
#Screen functions

def flip():
    scr.refresh()
    #scr.noutrefresh()
    #curses.doupdate()

def clear():
    scr.erase()
    scr.refresh()

def resize(width, height):
    """
        It's a little weird, but curses effectively demands an extra row and column
        or else you get "addstr() returned ERROR" nonesense while writing to the bottom-rightmost cell.
        Sorry linux users!
    """
    global MAX_X
    global MAX_Y
    MAX_X = width
    MAX_Y = height
    width += 1
    height += 1
    y, x = scr.getmaxyx()
    if y < height or x < width:
        raise Exception("Your window is x=%s, y=%s. Minimum required size is x=%s, y=%s" % (x, y, width, height))
        curses.resizeterm(height, width)
        scr.resize(height, width)
        
    
def reset():
    curses.nocbreak()
    curses.noraw()
    curses.echo()
    scr.keypad(False)
    curses.endwin()

def set_title(title):
    #gibberish, i tell you
    sys.stdout.write("\x1b]2;%s\x07" % title)

def set_cursor_type(i):
    curses.curs_set(i)

color_pairs = {}
next_pair = 0
def get_color(fg, bg):
    '''
        Curses wants it's colors to be in preset "color pairs",
        so we have to translate each combination into one.
    '''
    global next_pair
    #convert the color IDs to curses colors
    fg, bold = color_map[fg]
    bg, _ = color_map[bg] #backgrounds can't be bold

    if (fg, bg) not in color_pairs:
        next_pair += 1
        #log.debug("creating pair %i: (%r, %r)", next_pair, fg, bg)

        curses.init_pair(next_pair, fg, bg)
        color_pair = curses.color_pair(next_pair)
        color_pairs[(fg, bg)] = color_pair

    else:
        color_pair = color_pairs[(fg, bg)]
    if bold:
        color_pair |= curses.A_BOLD
        
    return color_pair
    
def draw_buffer(source, start_x, start_y):
    global MAX_X, MAX_Y
    y = start_y
    for row in source._data:
        if y < 0:
            y += 1
            continue
        x = start_x
        for fg, bg, ch in row[:source.width]:
            if x < 0:
                x += 1
                continue
            color = get_color(fg, bg)
            ch = uni(ch)
            #log.debug("x: %r y: %r ch: %r, w: %r h: %r", x, y, ch, buf.width, buf.height)
            scr.addstr(y, x, ch, color)
            x += 1
            if x >= MAX_X:
                #log.debug("Breaking line early (%r >= %r)", x, MAX_X)
                break
        y += 1
        if y >= MAX_Y:
            #log.debug("Breaking draw early (%r >= %r)", y, MAX_Y)
            break
            
    source.dirty = False
    return

def get_at(x, y):
    """
    This is incredibly unpleasant, but curses's inch() is completely worthless.
    It's supposed to return the character data in the low 8 bits and the color/attribute
    data in the remainder, but you can easily show that by writing multibyte unicode characters -
    ie "\xe2(...)" - the color area in inch() gets scribbled all over, such that it's impossible to
    tell, say, color pair #1 and color pair #3 apart.

    Therefore, we return None for color data in get_at. bleck.
    """
    if x < 0 or x >= MAX_X or y < 0 or y >= MAX_Y:
        raise ValueError("get_at: Invalid coordinate (%r, %r)" % (x,y))
    
    #instr can return multiple characters if unicode is going on, so we get to parse utf8 manually! OH BOY!
    chars = scr.instr(y, x, 4)
    
    #in utf8, a leading 1 means multibyte, 110 = total two bytes, 1110 = total three, 11110 = total four
    if not ord(chars[0]) & 0x80:
        ch = chars[0]
    elif (ord(chars[0]) & 0xE0) == 0xC0:
        ch = chars[0:2]
    elif (ord(chars[0]) & 0xF0) == 0xE0:
        ch = chars[0:3]
    else:
        ch = chars

    #log.debug('ch: %r', ch)
    return [None, None, ch]

def move_cursor(x, y):
    scr.move(y, x)

#--------------------------------------
#Input functions

class KeyReader:
    """
        The fakest file-like object you ever did see.
    """
    def read(self, n):
        key = scr.getkey()
        log.debug("read %r", key)
        return key
    
def raw_getkey():

    key = scr.getkey()
    log.debug("key is %r", key)
    if key == '\n':
        return 'enter'
    elif key == '\x1b':
        #ansi escape sequence, otherwise known as "ah crap"
        esc = ansi.parse_escape(KeyReader(), is_key=True)
        if esc.is_key:
            return esc.meaning
            log.warn("Unknown ansi key!: %r", esc.meaning)
            return None
        else:
            log.debug("got back a non-key on getkey! meaning=%r", esc.meaning)
            return None
    if key == 'c':
        key = '\x03'
    return key

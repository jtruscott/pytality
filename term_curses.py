import sys
import curses
import locale

import logging
log = logging.getLogger('pytality.term.curses')
    
#Curses requires this fairly magical invocation to support unicode correctly
locale.setlocale(locale.LC_ALL,"")

class colors:
    """
    Constants for the sixteen ANSI colors.
    On Curses, these are 2-tuples of (color, bold)
    """
    BLACK = (curses.COLOR_BLACK, False)
    BLUE = (curses.COLOR_BLUE, False)
    GREEN = (curses.COLOR_GREEN, False)
    CYAN = (curses.COLOR_CYAN, False)
    RED = (curses.COLOR_RED, False)
    MAGENTA = (curses.COLOR_MAGENTA, False)
    BROWN = (curses.COLOR_YELLOW, False)
    LIGHTGRAY = LIGHTGREY = (curses.COLOR_WHITE, False)

    DARKGRAY = DARKGREY = (curses.COLOR_BLACK, True)
    LIGHTBLUE = (curses.COLOR_BLUE, True)
    LIGHTGREEN = (curses.COLOR_GREEN, True)
    LIGHTCYAN = (curses.COLOR_CYAN, True)
    LIGHTRED = (curses.COLOR_RED, True)
    LIGHTMAGENTA = (curses.COLOR_MAGENTA, True)
    YELLOW = (curses.COLOR_YELLOW, True)
    WHITE = (curses.COLOR_WHITE, True)

def init():
    global scr
    scr = curses.initscr()
    curses.start_color()
    scr.keypad(False)
    curses.noecho()

def uni(c):
    """
        Convert a string from codepage 437 to unicode
    """
    return c.decode('cp437').encode('utf-8')

#----------------------------------------------------------------------------
#Screen functions

def flip():
    scr.noutrefresh()
    curses.doupdate()

def clear():
    scr.erase()
    scr.refresh()

def resize(width, height):
    """
        It's a little weird, but curses effectively demands an extra row and column
        or else you get "addstr() returned ERROR" nonesense.
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

def setcursortype(i):
    curses.curs_set(i)

color_pairs = {}
next_pair = 0
def get_color(fg, bg):
    '''
        Curses wants it's colors to be in preset "color pairs",
        so we have to translate each combination into one.
    '''
    global next_pair
    fg, bold = fg
    bg, _ = bg #backgrounds can't be bold

    if (fg, bg, bold) not in color_pairs:
        next_pair += 1
        #log.debug("creating pair %i: (%r, %r)", next_pair, fg, bg)


        curses.init_pair(next_pair, fg, bg)
        color_pair = curses.color_pair(next_pair)
        if bold:
            color_pair |= curses.A_BOLD
        
        color_pairs[(fg, bg, bold)] = color_pair

    return color_pairs[(fg, bg, bold)]
    
def draw_buffer(source, start_x, start_y):
    global MAX_X, MAX_Y
    y = start_y
    for row in source._data:
        x = start_x
        for fg, bg, ch in row[:source.width]:
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
    data = scr.inch(y, x)
    #inch returns attr in the high bits, char in the low bits
    ch = data & 0xFF
    attr = data & 0xFFFF00

    #and attr can be backwards lookedup and turned into a color set
    key_index = color_pairs.values().index(attr)
    cfg, cbg, cbold = color_pairs.keys()[key_index]
    #that can turn into a color in our world
    fg = (cfg, cbold)
    bg = (cbg, False)

    return [fg, bg, ch]

#--------------------------------------
#Input functions

_ansi = None #we have a circular reference with the 'ansi' module due to our colors

class KeyReader:
    """
        The fakest file-like object you ever did see.
    """
    def read(self, n):
        key = scr.getkey()
        log.debug("read %r", key)
        return key
    
def raw_getkey():
    global _ansi
    if not _ansi:
        import ansi
        _ansi = ansi

    key = scr.getkey()
    log.debug("key is %r", key)
    if key == '\n':
        return 'enter'
    elif key == '\x1b':
        #ansi escape sequence, otherwise known as "ah crap"
        esc = _ansi.parse_escape(KeyReader(), is_key=True)
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

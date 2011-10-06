import repl
from System.Threading import Thread
from System.Collections.Generic import List
window = repl.window
max_x = window.cols
max_y = window.rows

import time
import logging
log = logging.getLogger('pytality.term.silverlight')

class colors:
    """
    Constants for the sixteen ANSI colors.
    On Silverlight, we treat these as simple ints.
    (The browser does the hard work.)
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

cell_changes = []

def init(self, *args, **kwargs):
    window.set_message.InvokeSelf("Initializing Terminal...")
    clear()
    window.setup_input_handler.InvokeSelf()
    window.set_message.InvokeSelf("Terminal ready.")

def clear():
    global cell_changes
    global cell_info
    window.reset_cells.InvokeSelf()
    cell_info = [[[0, 0, ord(' ')] for c in range(max_x)] for r in range(max_y)]
    cell_changes = []

def resize(*args, **kwargs):
    """
        We don't support dynamic resizing, but our "terminal" should be
        correctly initialized from the start.
    """
    return

def reset(*args, **kwargs):
    """
        Since there's no command prompt to "go back to", resetting is pointless.
    """
    return

def set_title(title, *args, **kwargs):
    window.set_title.InvokeSelf(title)

def set_cursor_type(*args, **kwargs):
    """
        TODO: overlay a blinky cursor when this is enabled.
    """
    return

def draw_buffer(source, start_x, start_y):
    #log.debug("drawing a w=%r, h=%r buffer at x=%r, y=%r", source.width, source.height, start_x, start_y)
    #log.debug("firstfour: %r", source._data[0][:4])
    #render the buffer to our backing
    y = start_y
    for row in source._data:
        x = start_x
        for fg, bg, ch in row[:source.width]:
            if x >= max_x or y >= max_y:
                break
            current = cell_info[y][x]
            new = [bg, fg, ord(ch)]
            if current != new:
                cell_info[y][x] = new
                cell_changes.append([y, x, bg, fg, ord(ch)])
            x += 1
        y += 1

    source.dirty = False
    return

def flip():
    global cell_changes
    log.debug("flip: %r changes", len(cell_changes))

    #Passing a multidimensional array to JS is incredibly painful.
    #As icky as it is, window.Eval works solidly as an alternative.
    cell_changes_js = repr(cell_changes)
    window.Eval("window.cell_changes = %s;" % cell_changes_js)

    window.flip_cells.InvokeSelf()
    cell_changes = []

def raw_getkey():
    while True:
        length = window.input_queue.GetProperty('length')
        if not length:
            log.debug("no input, delaying 100ms")
            #Bizarrely, there's a massive difference between CurrentThread.Join()
            #and Sleep() in Silverlight. Sleep() freezes the entire UI thread, 
            #even making Firefox hang in all tabs until the plugin is killed.
            #Join() arbitrarily runs the message pumps, and everything works great.
            Thread.CurrentThread.Join(100)
            continue
        break

    which = window.input_queue.Invoke('pop')
    log.debug("which: %r", which)
    
    key = chr(which)
    if key in ('\r', '\n'):
        key = 'enter'
    if which ==  37:
        key = 'left'
    if which == 38:
        key = 'up'
    if which == 39:
        key = 'right'
    if which == 40:
        key = 'down'

    log.debug("key char: %r", key)

    return key

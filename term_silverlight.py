import repl
from System.Threading import Thread, ThreadStart
from System.Collections.Generic import List
window = repl.window
max_x = window.cols
max_y = window.rows

import time
import logging
log = logging.getLogger('pytality.term.silverlight')

cell_changes = []

def init(*args, **kwargs):
    window.set_message.InvokeSelf("Initializing Terminal...")
    clear()
    window.setup_input_handler.InvokeSelf()
    window.set_message.InvokeSelf("Terminal ready.")

def monkey_patch():
    """
        Patch the heck out of the standard library for various quirks
    """
    def sleep(amount):
        Thread.CurrentThread.Join(int(amount*100))
    time.sleep = sleep
   
    class PatchedThread(object):
        def __init__(self, target):
            self.target = target 

        def start(self):
            log.debug("starting new thread")
            t = Thread(ThreadStart(self.target))
            t.IsBackground = True
            t.Start()

    import threading
    threading.Thread = PatchedThread
    log.debug("patches applied")

monkey_patch()

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

def move_cursor(*args, **kwargs):
    """
        TODO: not relevant until we show cursors
    """
    return

def set_cursor_type(*args, **kwargs):
    """
        TODO: overlay a blinky cursor when this is enabled.
    """
    return

def draw_buffer(source, start_x, start_y):
    #render the buffer to our backing
    y = start_y
    for row in source._data:
        if y < 0:
            y += 1
            continue
        if y >= max_y:
            break

        x = start_x
        for fg, bg, ch in row[:source.width]:
            if x < 0:
                x += 1
                continue
            if x >= max_x:
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

def get_at(x, y):
    if x < 0 or x >= max_x or y < 0 or y >= max_y:
        raise ValueError("get_at: Invalid coordinate (%r, %r)" % (x,y))
    bg, fg, ch = cell_info[y][x]
    return [fg, bg, chr(ch)]

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

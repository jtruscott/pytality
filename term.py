import logging
import sys
class NoConsoleAvailableError(Exception):
    pass

log = logging.getLogger('pytality.term')

#-----------------------------------------------------------------------------
# Terminal setup/teardown

def _find_impl(choices):
    """
    Find a suitable terminal implementation.
    """

    success = False
    for choice in choices:
        if choice == 'pygame':
            try:
                import term_pygame as _impl
                log.debug("Imported term_pygame successfully")
                success = True
                break
            except ImportError, e:
                log.debug("Could not import term_pygame: %r", e)
                continue
        
        if choice == 'silverlight' and sys.platform == 'silverlight':
            import term_silverlight as _impl
            log.debug("Imported term_silverlight successfully")
            success = True
            break
        if choice == 'winconsole' and sys.platform == 'win32':
            try:
                import term_winconsole as _impl
                log.debug("Imported term_winconsole successfully")
                success = True
                break
            except ImportError, e:
                log.debug("Could not import term_winconsole: %r", e)
                continue
        if choice == 'curses':
            try:
                import term_curses as _impl
                log.debug("Imported term_curses successfully")
                success = True
                break
            except ImportError, e:
                log.debug("Could not import term_curses: %r", e)
                continue        
        
    if not success:
        raise NoConsoleAvailableError("Could not find any suitable console library. You may need a working curses implementation if you are on linux.")
    return _impl

#Our global terminal implementation
impl = None

class colors:
    """
    Constants for the sixteen ANSI colors.
    
    Note that background colors on some backends (curses) cannot be set as "bright".
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

def init(**kwargs):
    """
    Initialize the terminal and check that it's of an appropriate size.
    Also disables the cursor image to avoid flickery drawings. Use set_cursor_state
    to re-enable it when prompting for input.

    config:
        a dictionary of configuration options for Pytality.
        Supports the following keys:
        backends:
            A list of backends to try, in order.
            Defaults to ['silverlight', 'winconsole', 'pygame', 'curses']

        width:
        height:
            Minimum dimensions of the screen.
            Note that when using curses, a 1-row/column margin is added on the edge to prevent spurious failures.
            Defaults to 80 wide by 24 tall.

    """
    global impl, colors
    log.debug("init(): initializing terminal")

    default_config = dict(
        backends = ['silverlight', 'winconsole', 'pygame', 'curses'],
        width = 80,
        height = 24,
    )
    if kwargs:
        default_config.update(kwargs)
    config = default_config

    impl = _find_impl(config['backends'])

    impl.init()
    resize(config['width'], config['height'])

def reset():
    """
    Reset the terminal to a usable state.

    Enables the cursor image,
    clears the current line,
    and resets the current color.

    May also perform other cleanup, depending on implementation.
    You should call reset() unconditionally on all application exits.
    """
    log.debug("reset(): resetting terminal")
    if not impl:
        log.warn("reset(): no backend to reset!")
        return
    impl.reset()

def resize(width, height):
    """
    Resize the terminal.

    On Windows, this actually resizes the terminal.
    On Linux/Mac, this can only verify the terminal's size is sufficient
    and raises TerminalTooSmallError if it isn't.
    """
    log.debug("resize(): target width=%r, height=%r", width, height)
    impl.resize(width, height)

#-----------------------------------------------------------------------------
# Drawing functions

def clear():
    """
    Clear the screen to a blank state and home the cursor.
    Unlike buffer drawing, this renders immediately, and does not require flip().
    """
    impl.clear()

def draw_buffer(buf, x, y):
    """
    Draw a buffer to the backing buffer (if double-buffered) on the screen
    at the coordinates specified.

    After you have drawn all buffers for this "frame", call flip() to render
    the changes.
    """
    impl.draw_buffer(buf, x, y)

def flip():
    """
    Refresh the terminal, flushing all changes to the screen.

    Must be called to ensure changes (from drawing buffers)
    are actually rendered.
    """
    impl.flip()

def get_at(x, y):
    """
    Get a character from the screen at the specified coordinate.
    Generally, you shouldn't need this function, but uses come up from time to time,
    most notably testing.

    Returns [fg, bg, character]
    """
    return impl.get_at(x, y)

def move_cursor(x, y):
    """
    Position the text cursor at a coordinate on the screen.
    """
    return impl.move_cursor(x, y)

def set_cursor_type(cursor_type):
    """
    Change the terminal cursor graphic.
    
    There are three types of cursor available:
    "blank": Draw no flashing cursor. Set by default on init()
    "normal": Draw the standard cursor, usually a flashing "_".
    "block": Draw a blocky cursor, usually a full-character block

    Because most libraries refer to these three cursor types as 0, 1, and 2,
    that notation is allowed here as well.
    """
    cursor_type_map = dict(
        blank=0,
        normal=1,
        block=2
    )
    if cursor_type in cursor_type_map:
        cursor_type = cursor_type_map[cursor_type]
    impl.set_cursor_type(cursor_type)

def set_title(title):
    """
    Change the title of the terminal window.
    """
    impl.set_title(title)

#-----------------------------------------------------------------------------
# Keyboard functions

def raw_getkey():
    """
    Get a key of keyboard input.
    Returns None, 1 character, or the name of the special key.

    ^C is not converted into an exception.
    """
    return impl.raw_getkey()

def getkey():
    """
    Get a key of keyboard input, as per raw_getkey(), but doesn't return None,
    and perform some translations.

    ^C raises KeyboardInterrupt
    CTRL+<letter> key combinations return 'ctrl-<letter>'
    """
    while True:
        key = impl.raw_getkey()
        if key is None:
            continue
        
        if key == '\x03':
            #ctrl-c
            raise KeyboardInterrupt()
        
        if len(key) == 1 and  (1 <= ord(key) <= 26):
            #ctrl+letter, except tab (which is ctrl-i technically)
            if key == '\t':
                return key
                
            return "ctrl-%s" % chr(ord(key) + 96)
        return key

import os, os.path
import buffer, term

import logging
log = logging.getLogger("pytality.ansi")

#This module can get _really_ log-spammy if you turn it to debug
log.setLevel(logging.WARN)

class Escape(object):
    '''
        Container for an ANSI escape sequence.
        These can be used both for 'drawing' and keyboard input.

        
        meaning:
            a short string indicating what the escape wants to do.
            Other information will be provided based upon the contents of this field.

            right:
                move the cursor right <value> spaces
            left:
                move the cursor left <value> spaces
            up:
                move the cursor up <value> lines
            down:
                move the cursor down <value> lines

            color:
                one or both of the current colors have changed.
                fg: None or the new color
                bg: None or the new color

            unknown:
                the parser didn't know what this sequence was.
                <value> will be the escape command
                    
            invalid:
                the parser thinks this sequence was illegal
                <value> will be the full escape sequence that was provided.

            There are many other values that are mapped to straight key names.
            is_key will be True for these.


        args:
            a list of all arguments provided to the escape sequence

        fg:
        bg:
        value:
            Set for some commands.
            None if not applicable to the command type.

        is_key:
            if this is True, the escape sequence is known to represent
            a keypress.
            

        
    '''
    def __init__(self, meaning='unknown',args=None,
                value=None, fg=None, bg=None):
        if args is None:
            args = []
        self.meaning = meaning
        self.args = args
        self.value = value
        self.fg = fg
        self.bg = bg

        if meaning in (
            'left', 'up', 'down', 'right',
            'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
            'del', 'home', 'pgup', 'pgdn', 'end',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'enter',
            'esc',
        ):
            self.is_key = True 
        else:
            self.is_key = False        

#Mapping of the ANSI escape color codes to pytality.term colors
color_map = {
    (0, 30): term.colors.BLACK,
    (0, 31): term.colors.RED,
    (0, 32): term.colors.GREEN,
    (0, 33): term.colors.BROWN,
    (0, 34): term.colors.BLUE,
    (0, 35): term.colors.MAGENTA,
    (0, 36): term.colors.CYAN,
    (0, 37): term.colors.LIGHTGREY,

    (1, 30): term.colors.DARKGREY,
    (1, 31): term.colors.LIGHTRED,
    (1, 32): term.colors.LIGHTGREEN,
    (1, 33): term.colors.YELLOW,
    (1, 34): term.colors.LIGHTBLUE,
    (1, 35): term.colors.LIGHTMAGENTA,
    (1, 36): term.colors.LIGHTCYAN,
    (1, 37): term.colors.WHITE,
}

#Unfortunately, ANSI escapes fully expect you to keep global state
#around for color switching and bold toggling
last_color = 37
bold = 0

def lookup_color(bold, idx=None):
    global last_color
    log.debug('lookup_color: bold=%r, idx=%r, last_color=%r' % (bold, idx, last_color))
   
    if idx is None:
        #When changing bold state, the actual color is not provided
        idx = last_color

    elif idx >= 40:
        #ANSI background color IDs are the same as the foreground colors, but +10
        idx -= 10

    else:
        #However, ANSI only 'persists' foreground colors
        #(because you can toggle boldness without setting the color)
        last_color = idx

    #now, lookup the damn color
    color = color_map[(bold, idx)]
    return color

def read_escape(f):
    '''
        Read an ANSI escape code from a file-like object.
        You probably want parse_escape, which also interprets the values.

        Returns either an Escape object (if something went wrong), or (args, command identifier)
    '''
    
    all_chars = []
    def read():
        '''
            Read one character and save it in all_chars
        '''
        c = f.read(1)
        all_chars.append(c)
        if not c:
            #EOF!?
            log.error("parse_escape: recieved EOF while reading an escape. all_chars=%r", all_chars)
            return Escape('illegal', value=all_chars)
        return c

    c = read()

    #MOST, but not all, ANSI escapes start out with '['.
    if c == 'O':
        #but sometimes they start with O...
        #but we can just read another character and call that the command. not awful.
        c = c + read()
        return ([], c)
    
    elif c == '\x1b':
        #hitting ESC twice produces this. That's still a key.
        return Escape('esc')

    elif c != '[':
        log.error("parse_escape: Recieved %r while expecting '['. all_chars=%r", c, all_chars)
        return Escape('illegal', value=all_chars)

    args = []
    arg = []

    def end_arg():
        if len(arg):
            arg_int = int(''.join(arg))
            args.append(arg_int)

    while True:
        c = read()
        if c not in '01234567890;':
            #we're done parsing arguments
            break
        if c == ';':
            #that's the end of an argument
            #convert it into an int instead of a string
            end_arg()
            arg = []
        else:
            #a number, oh boy
            #add it to our current-argument info
            arg.append(c)
    end_arg()

    return (args, c)

def parse_escape(f, is_key=False):
    '''
        Read and parse an ANSI escape codefrom a file-like object.
        It is expected that you call this function after
        reading the chr(27) prelude marker.
        
        Returns an Escape instance.

        (Christ, I hate this "syntax")
    '''
    global bold
        
    #read the escape sequence
    data = read_escape(f)
    if isinstance(data, Escape):
        return data

    args, command = data

    def optional_arg(default=1):
        '''
            Many ANSI escapes have optional arguments with default values.
            optional_arg() produces such an argument from the data read.
        '''
        if len(args):
            return args.pop(0)
        return default

    #determine what the escape represents

    if command == 'A': return Escape('up', value=optional_arg())
    elif command == 'B': return Escape('down', value=optional_arg())
    elif command == 'C': return Escape('right', value=optional_arg())
    elif command == 'D': return Escape('left', value=optional_arg())
    
    elif command == 'H': return Escape('home')
    elif command == 'F': return Escape('end')

    elif command == 'm':
        #m: colorize things
        fg = None
        bg = None
        for arg in args:
            if arg == 1:
                #1 means we want to enable bold foreground colors (only)
                bold = 1
                log.debug("parse_escape: bolding")
                fg = lookup_color(bold, None)

            elif arg == 0:
                #0 means we want to disable bold
                #but removing bold sets the background to black!? wtf?
                #I don't make the rules around here.
                bold = 0
                log.debug("parse_escape: un-bolding")
                fg = lookup_color(bold, None)
                bg = term.colors.BLACK

            elif 30 <= arg <= 37:
                #30-37 means we want to change the foreground color
                log.debug("parse_escape: fg=%r" % arg)
                fg = lookup_color(bold, arg)

            elif 40 <= arg <= 47:
                #40-47 are the same as 30-37, but for the background color
                #oh, but backgrounds can't ever be bold. sorry.
                log.debug("parse_escape: bg=%r" % arg)
                bg = lookup_color(0, arg)

        return Escape('color', fg=fg, bg=bg)
    
    elif command == '~':
        idx = optional_arg(None)
        #Function key escapes
        #These are surprisingly poorly documented - best resource I've found is
        # http://aperiodic.net/phil/archives/Geekery/term-function-keys.html

        #this argument isn't optional, but we'll fallthrough to error anyway if it's missing
        if idx == 11: return Escape('f1')
        if idx == 12: return Escape('f2')
        if idx == 13: return Escape('f3')
        if idx == 14: return Escape('f4')
        if idx == 15: return Escape('f5')

        if idx == 17: return Escape('f6')
        if idx == 18: return Escape('f7')
        if idx == 19: return Escape('f8')
        if idx == 20: return Escape('f9')
        if idx == 21: return Escape('f10')
        if idx == 23: return Escape('f11')
        if idx == 24: return Escape('f12')

        # I saw these on rxvt and can't find any "proof" of them anywhere
        if idx == 3: return Escape('del')
        if idx == 5: return Escape('pgup')
        if idx == 6: return Escape('pgdn')
        if idx == 7: return Escape('home')
        if idx == 8: return Escape('end')
    
    # 'O' escapes are decently documented at
    # http://www.connectrf.com/documents/vt220.html
    
    elif command == 'OP': return Escape('f1')
    elif command == 'OQ': return Escape('f2')
    elif command == 'OR': return Escape('f3')
    elif command == 'OS': return Escape('f4')

    #numpad
    elif command == 'Op': return Escape('0')
    elif command == 'Oq': return Escape('1')
    elif command == 'Or': return Escape('2')
    elif command == 'Os': return Escape('3')
    elif command == 'Ot': return Escape('4')
    elif command == 'Ou': return Escape('5')
    elif command == 'Ov': return Escape('6')
    elif command == 'Ow': return Escape('7')
    elif command == 'Ox': return Escape('8')
    elif command == 'Oy': return Escape('9')
    elif command == 'OM': return Escape('enter')

    # these additional 'O' escapes were found at
    # http://real-world-systems.com/docs/ANSIcode.html
    elif command == 'OA': return Escape('up', value=optional_arg())
    elif command == 'OB': return Escape('down', value=optional_arg())
    elif command == 'OC': return Escape('right', value=optional_arg())
    elif command == 'OD': return Escape('left', value=optional_arg())
    
    #I saw these on evilvte and can't find any proof
    elif command == 'OH': return Escape('home')
    elif command == 'OF': return Escape('end')

    log.error("parse_escape: unknown escape sequence. command=%r, args=%r", command, args)
    return Escape('unknown', value=command)

def read_to_buffer(f, width=80, max_height=None, crop=False):
    """
        if crop, kill rows at :width
        otherwise, let them wrap into new rows.
        we need both :(
    """
    rows = []
    row = []
    fg = term.colors.WHITE
    bg = term.colors.BLACK
    def add(c, _fg=None, _bg=None):
        if _fg is not None:
            f = _fg
        else:
            f = fg
        if _bg is not None:
            b = _bg
        else:
            b = bg
        #log("f: %r b: %r c: %r (%r)" % (f, b, c, hex(ord(c))))
        row.append([f, b, c])

    def finish_row():
        log.debug("read_to_buffer: finishing row")
        while len(row) < width:
            add(' ')
        if crop:
            xrow = row[:width]
        else:
            xrow = row
        rows.append(xrow)
        fg = term.colors.WHITE

    while True:
        c = f.read(1)
        if not c:
            break
        if c == chr(27): #esc
            esc = parse_escape(f)
            if esc.meaning == 'right':
                [add(' ', term.colors.BLACK, term.colors.BLACK) for x in range(esc.value)]

            elif esc.meaning == 'color':
                if esc.fg is not None:
                    fg = esc.fg
                if esc.bg is not None:
                    bg = esc.bg
            else:
                log.warn("read_to_buffer: ignoring unknown meaning %r. This is probably bad.", esc.meaning)

        elif c in ('\r','\n'):
            finish_row()
            row = []
        else:
            add(c)
        if not crop and len(row) >= width:
            finish_row()
            row = []
    finish_row()
    if max_height:
        rows = rows[:max_height]
    buf = buffer.Buffer(
        width=width, height=len(rows),
        data=rows
    )
    return buf

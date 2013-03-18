from ctypes import *
from ctypes.wintypes import WCHAR, HANDLE, UINT, ULONG, WORD, DWORD, BOOL, LPCSTR, LPCWSTR, WinError
import time
import collections
import logging

__license__ = "BSD"
__all__ = ['colors', 'Console', 'ConsoleBuffer']

log = logging.getLogger('pytality.winconsole')

class colors:
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


LF_FACESIZE = 32
FONT_LUCIDA_CONSOLE = 48
FONT_TERMINAL = 54
ENABLE_MOUSE_INPUT = 0x10 

class CHAR_INFO(Structure):
    _fields_ = ('ascii', c_char), ('attr', c_uint16)

class SMALL_RECT(Structure):
    _fields_ = ('left', c_short), ('top', c_short), ('right', c_short), ('bottom', c_short)

class COORD(Structure):
    _fields_ = ('x', c_short), ('y', c_short)
    def __repr__(self):
        return "coord(x=%r, y=%r)" % (self.x, self.y)

class CONSOLE_SCREEN_BUFFER_INFO(Structure):
    _fields_ = [("size", COORD),
                ("cursor_position", COORD),
                ("attributes", c_short),
                ("rect", SMALL_RECT),
                ("max_size", COORD)]

class CONSOLE_CURSOR_INFO(Structure):
    _fields_ = [("size", c_int),
                ("visible", c_byte)]

class CONSOLE_FONT_INFO(Structure):
    _fields_ = [('size', ULONG),
                ('font_index', DWORD),
                ('font_size', COORD),
                ('font_family', UINT),
                ('font_weight', UINT),
                ('font_name', (WCHAR*LF_FACESIZE))
                ]

#all these to read mouse input! sheesh.
class CHAR_UNION(Union):
    _fields_ = [
        ('unicode', WCHAR),
        ('ascii', c_char),
    ]

class KEY_EVENT_RECORD(Structure):
    _fields_ = [
        ('key_down', BOOL),
        ('repeat_count', WORD),
        ('virtual_key_code', WORD),
        ('virtual_scan_code', WORD),
        ('char', CHAR_UNION),
        ('control_key_state', DWORD),
    ]

class MOUSE_EVENT_RECORD(Structure):
    _fields_ = [
        ('mouse_position', COORD),
        ('button_state', DWORD),
        ('control_key_state', DWORD),
        ('flags', DWORD),
    ]
    LEFT_BUTTON_PRESSED = 0x0001 
    RIGHT_BUTTON_PRESSED = 0x0002

class WINDOW_BUFFER_SIZE_RECORD(Structure):
    _fields_ = [
        ('dwSize', COORD),
    ]

class MENU_EVENT_RECORD(Structure):
    _fields_ = [
        ('dwCommandId', UINT),
    ]

class FOCUS_EVENT_RECORD(Structure):
    _fields_ = [
        ('bSetFocus', BOOL),
    ]

class INPUT_RECORD_UNION(Union):
    _fields_ = [
        ('key_event', KEY_EVENT_RECORD),
        ('mouse_event', MOUSE_EVENT_RECORD),
        ('window_event', WINDOW_BUFFER_SIZE_RECORD),
        ('menu_event', MENU_EVENT_RECORD),
        ('focus_event', FOCUS_EVENT_RECORD),
    ]

class INPUT_RECORD(Structure):
    _anonymous_ = ("event",)
    _fields_ = [
        ('event_type', WORD),
        ('event', INPUT_RECORD_UNION),
    ]
    FOCUS_EVENT = 0x0010
    KEY_EVENT = 0x0001
    MENU_EVENT = 0x0008
    MOUSE_EVENT = 0x0002
    WINDOW_BUFFER_SIZE_EVENT = 0x0004 

def check_winerror(result, func, args):
    if not result:
        raise WinError()
    return args

class Console(object):
    FILE_SHARE_READ = 1
    FILE_SHARE_WRITE = 2
    GENERIC_WRITE = 0x40000000
    GENERIC_READ = 0x80000000
    OPEN_EXISTING = 3
    Error = 0xFFFFFFFF
    NORM_CURSOR_SIZE = 10
    SOLID_CURSOR_SIZE = 99
    
    CreateFile = windll.kernel32.CreateFileA
    CreateFile.argtypes = (LPCSTR, DWORD, DWORD, c_void_p, DWORD, DWORD, HANDLE)
    CreateFile.restype = HANDLE

    WriteConsoleOutput = windll.kernel32.WriteConsoleOutputA
    WriteConsoleOutput.argtypes = (HANDLE, c_void_p, COORD, COORD, POINTER(SMALL_RECT))
    WriteConsoleOutput.restype = BOOL
    WriteConsoleOutput.errcheck = check_winerror

    GetConsoleScreenBufferInfo = windll.kernel32.GetConsoleScreenBufferInfo
    GetConsoleScreenBufferInfo.argtypes = (HANDLE, POINTER(CONSOLE_SCREEN_BUFFER_INFO))
    GetConsoleScreenBufferInfo.restype = BOOL
    GetConsoleScreenBufferInfo.errcheck = check_winerror

    SetConsoleWindowInfo = windll.kernel32.SetConsoleWindowInfo
    SetConsoleWindowInfo.argtypes = (HANDLE, BOOL, POINTER(SMALL_RECT))
    SetConsoleWindowInfo.restype = BOOL
    SetConsoleWindowInfo.errcheck = check_winerror
    
    FillConsoleOutputCharacter = windll.kernel32.FillConsoleOutputCharacterA
    FillConsoleOutputAttribute = windll.kernel32.FillConsoleOutputAttribute
    SetConsoleCursorPosition = windll.kernel32.SetConsoleCursorPosition
    SetConsoleTextAttribute = windll.kernel32.SetConsoleTextAttribute

    SetConsoleTitle = windll.kernel32.SetConsoleTitleW
    SetConsoleCursorInfo = windll.kernel32.SetConsoleCursorInfo
    SetConsoleCursorInfo.argtypes = (HANDLE, POINTER(CONSOLE_CURSOR_INFO))
    SetConsoleCursorInfo.errcheck = check_winerror

    ReadConsoleInput = windll.kernel32.ReadConsoleInputA
    ReadConsoleInput.argtypes = (HANDLE, POINTER(INPUT_RECORD), DWORD, POINTER(DWORD))
    ReadConsoleInput.restype = BOOL
    ReadConsoleInput.errcheck = check_winerror

    try:
        #These functions are only available on Vista and above
        GetCurrentConsoleFontEx = windll.kernel32.GetCurrentConsoleFontEx
        SetCurrentConsoleFontEx = windll.kernel32.SetCurrentConsoleFontEx
    except:
        GetCurrentConsoleFontEx = None
        SetCurrentConsoleFontEx = None
    else:
        GetCurrentConsoleFontEx.argtypes = (HANDLE, BOOL, POINTER(CONSOLE_FONT_INFO))
        GetCurrentConsoleFontEx.restype = BOOL
        GetCurrentConsoleFontEx.errcheck = check_winerror

        SetCurrentConsoleFontEx.argtypes = (HANDLE, BOOL, POINTER(CONSOLE_FONT_INFO))
        SetCurrentConsoleFontEx.restype = BOOL
        SetCurrentConsoleFontEx.errcheck = check_winerror

    SetConsoleOutputCP = windll.kernel32.SetConsoleOutputCP
    SetConsoleOutputCP.argtypes = (UINT,)
    SetConsoleOutputCP.restype = BOOL
    SetConsoleOutputCP.errcheck = check_winerror

    SetConsoleScreenBufferSize = windll.kernel32.SetConsoleScreenBufferSize
    SetConsoleScreenBufferSize.argtypes = (HANDLE, COORD)
    SetConsoleScreenBufferSize.restype = BOOL
    SetConsoleScreenBufferSize.errcheck = check_winerror

    GetConsoleMode = windll.kernel32.GetConsoleMode
    GetConsoleMode.argtypes = (HANDLE, POINTER(DWORD))
    GetConsoleMode.restype = BOOL
    GetConsoleMode.errcheck = check_winerror

    SetConsoleMode = windll.kernel32.SetConsoleMode
    SetConsoleMode.argtypes = (HANDLE, DWORD)
    SetConsoleMode.restype = BOOL
    SetConsoleMode.errcheck = check_winerror

    def __init__(self):
        self.input = self.get_console_handle('CONIN$')
        self.output = self.get_console_handle('CONOUT$')
        self.mouse_enabled = False

    def get_console_handle(self, name):
        """
        HANDLE WINAPI CreateFile(
          __in      LPCTSTR lpFileName,
          __in      DWORD dwDesiredAccess,
          __in      DWORD dwShareMode,
          __in_opt  LPSECURITY_ATTRIBUTES lpSecurityAttributes,
          __in      DWORD dwCreationDisposition,
          __in      DWORD dwFlagsAndAttributes,
          __in_opt  HANDLE hTemplateFile
        );
        """
        #log.info('Getting handle for %r', name)
        console_handle = self.CreateFile(
            create_string_buffer(name),
            self.GENERIC_WRITE | self.GENERIC_READ,
            self.FILE_SHARE_READ | self.FILE_SHARE_WRITE,
            None, #sa

            self.OPEN_EXISTING, #creation
            0, #dwflags
            0, #htemplate
            )
        if console_handle == self.Error:
            raise WinError()
        return console_handle
    
    def clear(self):
        csbi = self._get_screen_info()
        dummy = DWORD(0)
        coord = COORD(0, 0)
        self.FillConsoleOutputCharacter (
            self.output,
            c_char(' '), 
            csbi.size.x * csbi.size.y,
            coord,
            byref(dummy)
        )
        self.FillConsoleOutputAttribute(
            self.output,
            0, #attributes
            csbi.size.x * csbi.size.y,
            coord,
            byref(dummy)
        )
        self.SetConsoleCursorPosition (self.output, coord)
        return

    def clear_line(self):
        csbi = self._get_screen_info()
        dummy = DWORD(0)
        self.FillConsoleOutputCharacter (
            self.output,
            c_char(' '), 
            csbi.size.x - csbi.cursor_position.x,
            csbi.cursor_position,
            byref(dummy)
        )
        self.FillConsoleOutputAttribute(
            self.output,
            csbi.attributes,
            csbi.size.x - csbi.cursor_position.x,
            csbi.cursor_position,
            byref(dummy)
        )
        return

    def cursor_pos(self):
        csbi = self._get_screen_info()
        return csbi.cursor_position

    def get_color(self):
        csbi = self._get_screen_info()
        bg = (csbi.attributes & (0xF0)) >> 4
        fg = csbi.attributes & (0x0F)
        return collections.namedtuple('color', ('bg', 'fg'))(bg, fg)

    def get_font_info(self):
        if self.GetCurrentConsoleFontEx is None:
            log.warn("Unable to get the current console font; function not available before Windows Vista")
            return None
        cfi = CONSOLE_FONT_INFO()
        cfi.size = sizeof(cfi)
        self.GetCurrentConsoleFontEx(self.output, False, pointer(cfi))
        log.info("Font information: w=%r, h=%r, index=%r, name=%r",
                cfi.font_size.x, cfi.font_size.y,
                repr(cfi.font_index), repr(cfi.font_name))
        return cfi

    def _get_screen_info(self):
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        self.GetConsoleScreenBufferInfo(
            self.output,
            pointer(csbi)
        )
        return csbi

    def move_cursor(self, x, y):
        coord = COORD(x, y)
        self.SetConsoleCursorPosition(self.output, coord)
    

    def set_color(self, bg=None, fg=None):
        if bg is None or fg is None:
            csbi = self._get_screen_info()
            
        if bg is None:
            bg = csbi.attributes & (0xF0)
        else:
            bg = bg << 4

        if fg is None:
            fg = csbi.attributes & (0x0F)

        attr = bg + fg
        self.SetConsoleTextAttribute(self.output, WORD(attr))

    def set_code_page(self, code_page):
        #437: cp437
        #65001: utf-8?
        #only works for raster fonts.
        self.SetConsoleOutputCP(code_page)

    def set_cursor_type(self, newtype):
        cci = CONSOLE_CURSOR_INFO()
        if newtype == 0:
            cci.size = self.NORM_CURSOR_SIZE
            cci.visible = False
        elif newtype == 1:
            cci.size = self.NORM_CURSOR_SIZE
            cci.visible = True
        else:
            cci.size = self.SOLID_CURSOR_SIZE
            cci.visible = True
        self.SetConsoleCursorInfo(self.output, byref(cci))

    def set_font_info(self, x=8, y=12, font=FONT_TERMINAL):
        if self.SetCurrentConsoleFontEx is None:
            log.warn("Unable to set the console font; function not available before Windows Vista")
            return None
        cfi = self.get_font_info()
        cfi.font_size.x = x
        cfi.font_size.y = y
        cfi.font_family = font
        self.SetCurrentConsoleFontEx(self.output, False, pointer(cfi))

    def set_size(self, width, height):
        """
        Change the size of the console window.
        This is a little bizarre:
        - SetConsoleScreenBufferSize _cannot_ change to a size
            smaller than the current window size, but can increase the buffer size
            From MSDN:
            A COORD structure that specifies the new size of the console screen buffer, in character rows and columns. 
            The specified width and height cannot be less than the width and height of the console screen buffer's window. 
            The specified dimensions also cannot be less than the minimum size allowed by the system. 

        - SetConsoleWindowInfo _cannot_ increase the size of the window, but can decrease the size.
            From MSDN:
            The function fails if the specified window rectangle extends beyond the boundaries of the console screen buffer. 
            This means that the Top and Left members of the lpConsoleWindow rectangle cannot be less than zero.
            Similarly, the Bottom and Right members (or the calculated bottom and right coordinates)
            cannot be greater than (screen buffer height - 1) and (screen buffer width - 1), respectively. 

        If the window is going to grow on one axis and shrink on another, neither call will work directly.
        as far as I can tell, you have to do one call for the one axis, and the other for the other axis.
        """
        csbi = self._get_screen_info()
        current_width = csbi.size.x
        current_height = csbi.size.y
        log.debug("set_size: current_width = %r, current_height = %r", current_width, current_height)

        def shrink(new_width, new_height):
            #first, we're gonna need a smaller window
            self.SetConsoleWindowInfo(self.output, True, SMALL_RECT(0, 0, new_width-1, new_height-1))

            #then, we're gonna need a smaller buffer
            self.SetConsoleScreenBufferSize(self.output, COORD(new_width, new_height))

        def grow(new_width, new_height):
            #first, we're gonna need a bigger buffer
            self.SetConsoleScreenBufferSize(self.output, COORD(new_width, new_height))

            #then, we're gonna need a matching window size
            self.SetConsoleWindowInfo(self.output, True, SMALL_RECT(0, 0, new_width-1, new_height-1))
            
        if width > current_width:
            grow(width, current_height)
        elif width < current_width:
            shrink(width, current_height)

        #now width's been taken care of, hopefully
        if height > current_height:
            grow(width, height)
        elif height < current_height:
            shrink(width, height)
    
    def set_title(self, title):
        self.SetConsoleTitle(create_unicode_buffer(title))

    def enable_mouse_input(self):
        console_mode = DWORD()
        self.GetConsoleMode(self.input, console_mode)
        print 'mode', console_mode.value, console_mode.value & ENABLE_MOUSE_INPUT

        console_mode.value |= ENABLE_MOUSE_INPUT
        self.SetConsoleMode(self.input, console_mode)
        self.mouse_enabled = True

    def read_input(self):
        """
        BOOL WINAPI ReadConsoleInput(
          _In_   HANDLE hConsoleInput,
          _Out_  PINPUT_RECORD lpBuffer,
          _In_   DWORD nLength,
          _Out_  LPDWORD lpNumberOfEventsRead
        );
        """
        input_array = (INPUT_RECORD * 10)()
        
        if not self.mouse_enabled:
            self.enable_mouse_input()

        num_read = DWORD()
        self.ReadConsoleInput(self.input, input_array, len(input_array), num_read)
        console.move_cursor(0, 0)
        print num_read.value, 'events'
        for i in range(num_read.value):
            item = input_array[i]
            event_type = item.event_type
            print event_type
            if event_type == item.KEY_EVENT:
                key_event = item.key_event
                print 'key', key_event.virtual_scan_code, repr(key_event.char.ascii)
            elif event_type == item.MOUSE_EVENT:
                mouse_event = item.mouse_event
                left_pressed = bool(mouse_event.button_state & mouse_event.LEFT_BUTTON_PRESSED)
                right_pressed = bool(mouse_event.button_state & mouse_event.RIGHT_BUTTON_PRESSED)
                x = mouse_event.mouse_position.x
                y = mouse_event.mouse_position.y
                print 'mouse', mouse_event.button_state, mouse_event.flags, left_pressed, right_pressed, x, y
                console.move_cursor(x, y)
                return left_pressed


class ConsoleBuffer(object):
    def __init__(self, width, height):
        self.buffer = self.create_buffer(width, height)
        self.width = width
        self.height = height

    def create_buffer(self, width, height):
        console_array = CHAR_INFO * (width * height)
        return console_array()

    def draw(self, console, width, height, x, y):
        """
        BOOL WINAPI WriteConsoleOutput(
          __in     HANDLE hConsoleOutput,
          __in     const CHAR_INFO *lpBuffer,
          __in     COORD dwBufferSize,
          __in     COORD dwBufferCoord,
          __inout  PSMALL_RECT lpWriteRegion
        );

        WriteConsoleOutputA (hConOut, pCI, dwBufferSize, 
        dwBufferOrg, &srDest);

        While it's faster to use the lpWriteRegion parameter to only redraw the area that's changed, it's got weird bugs - 
        at least on Windows 7, when using it it leaves behind visible one-pixel "seams" along the edge of the region. I guess
        there's an off-by-one bug somewhere when calculating the margins?
        """
        if not width or not height or not len(self.buffer):
            return

        buffer_size = COORD(width, height)
        buffer_coord = COORD(0, 0)
        write_region = SMALL_RECT(
            x, 
            y,
            x + width - 1,
            y + height - 1
        )
        console.WriteConsoleOutput(console.output, byref(self.buffer), buffer_size, buffer_coord, byref(write_region))
        return

if __name__ == "__main__":
    def stats(times):
        print 'min:', min(times)
        print 'avg:', sum(times) / len(times), ' fps:', 1 / (sum(times) / len(times))
        print 'max:', max(times)
    
    def perf_test():
        lolbufs = []
        for start in range(16):
            i = start
            buf = console.create_buffer()
            for c in buf:
                c.ascii = ' '#chr(ord('a') + (i%16))
                c.attr = 1 #i % 16
                i += 1

        times = []
        for i in range(120):
            console.buffer = buf[i % 16]
            times.append(console.draw_buffer())
            #console.clear()
        #print 'times:', times
        stats(times)
    def clearing_test():
        print "a" * 60 * 120
        time.sleep(0.2)
        console.clear()
        print "b" * 60
        print "c" * 60
        print "d" * 60
        console.move_cursor(1, 1)
        console.clear_line()
        console.move_cursor(2, 2)
        console.clear_line()

    def cursor_test():
        console.set_cursor_type(0)
        time.sleep(1)
        console.set_cursor_type(1)
        time.sleep(1)
        console.set_cursor_type(2)
        time.sleep(1)
        console.set_cursor_type(1)

    def xy_test():
        console.clear()
        console.move_cursor(1, 2)
        print console.cursor_pos(), "one two"
        console.move_cursor(10, 20)
        print console.cursor_pos(), "ten twenty"
        console.move_cursor(0, 10)
        print console.cursor_pos(), "zero ten"
    
    def title_test():
        console.set_title("foo!")
        time.sleep(1)
        console.set_title("no, bar!")
        time.sleep(1)
    
    def font_test():
        console.set_font_info(x=16, y=12)

    def set_color_test():
        console.set_color(bg=colors.BLUE, fg=colors.WHITE)
        print 'white on blue', console.get_color()
        console.set_color(fg=colors.LIGHTGREEN)
        print 'lightgreen on imp blue', console.get_color()
        console.set_color(bg=colors.BROWN, fg=colors.YELLOW)
        print 'yellow on brown',
        console.set_color(bg=colors.MAGENTA, fg=colors.BLACK)
        print 'black on magenta',
        console.set_color(fg=colors.WHITE)
        print 'white on magenta imp',
        console.set_color(bg=colors.DARKGREY)
        print 'white imp on darkgrey',
        console.set_color()
        print 'white imp on darkgrey imp',
        console.set_color(bg=colors.BLACK, fg=colors.LIGHTGREY)
        print 'lightgrey on white'

    def read_input_test():
        while True:
            if console.read_input():
                break

    #----
    console = Console()
    read_input_test()
    #clearing_test()
    #cursor_test()
    #xy_test()
    #title_test()
    #font_test()
    #set_color_test()

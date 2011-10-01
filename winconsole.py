from ctypes import *
from ctypes.wintypes import WCHAR, HANDLE, UINT, ULONG, WORD, DWORD, BOOL, LPCSTR, LPCWSTR, WinError
import time
import collections
import logging

__license__ = "BSD"
__all__ = ['colors', 'Console', 'ConsoleBuffer']

log = logging.getLogger('library.winconsole')

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


class Console:
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

    GetConsoleScreenBufferInfo = windll.kernel32.GetConsoleScreenBufferInfo
    GetConsoleScreenBufferInfo.argtypes = (HANDLE, POINTER(CONSOLE_SCREEN_BUFFER_INFO))
    GetConsoleScreenBufferInfo.restype = BOOL
    
    FillConsoleOutputCharacter = windll.kernel32.FillConsoleOutputCharacterA
    FillConsoleOutputAttribute = windll.kernel32.FillConsoleOutputAttribute
    SetConsoleCursorPosition = windll.kernel32.SetConsoleCursorPosition
    SetConsoleTextAttribute = windll.kernel32.SetConsoleTextAttribute

    SetConsoleTitle = windll.kernel32.SetConsoleTitleW
    SetConsoleCursorInfo = windll.kernel32.SetConsoleCursorInfo
    SetConsoleCursorInfo.argtypes = (HANDLE, POINTER(CONSOLE_CURSOR_INFO))

    GetCurrentConsoleFontEx = windll.kernel32.GetCurrentConsoleFontEx
    GetCurrentConsoleFontEx.argtypes = (HANDLE, BOOL, POINTER(CONSOLE_FONT_INFO))
    GetCurrentConsoleFontEx.restype = BOOL

    SetCurrentConsoleFontEx = windll.kernel32.SetCurrentConsoleFontEx
    SetCurrentConsoleFontEx.argtypes = (HANDLE, BOOL, POINTER(CONSOLE_FONT_INFO))
    SetCurrentConsoleFontEx.restype = BOOL

    SetConsoleOutputCP = windll.kernel32.SetConsoleOutputCP
    SetConsoleOutputCP.argtypes = (UINT,)
    SetConsoleOutputCP.restype = BOOL

    SetConsoleScreenBufferSize = windll.kernel32.SetConsoleScreenBufferSize
    SetConsoleScreenBufferSize.argtypes = (HANDLE, COORD)
    SetConsoleScreenBufferSize.restype = BOOL

    def __init__(self):
        self.input = self.get_console_handle('CONIN$')
        self.output = self.get_console_handle('CONOUT$')

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
        print 'setting up handle', name
        console_handle = self.CreateFile(
            create_string_buffer(name),
            self.GENERIC_WRITE | self.GENERIC_READ,
            self.FILE_SHARE_READ | self.FILE_SHARE_WRITE,
            None, #sa

            self.OPEN_EXISTING, #creation
            0, #dwflags
            0, #htemplate
            )
        print 'got handle', console_handle
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
        cfi = CONSOLE_FONT_INFO()
        cfi.size = sizeof(cfi)
        ret = self.GetCurrentConsoleFontEx(self.output, False, pointer(cfi))
        if not ret:
            raise WinError()
        print cfi.font_size.x, cfi.font_size.y
        print repr(cfi.font_index), repr(cfi.font_name)
        return cfi

    def _get_screen_info(self):
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        ret = self.GetConsoleScreenBufferInfo(
            self.output,
            pointer(csbi)
        )
        if not ret:
            raise WinError()
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

    def set_code_page(code_page):
        #437: cp437
        #65001: utf-8?
        #only works for raster fonts.
        ret = self.SetConsoleOutputCP(code_page)
        if not ret:
            raise WinError()

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
        ret = self.SetConsoleCursorInfo(self.output, byref(cci))
        if not ret:
            raise WinError()

    def set_font_info(self, x=8, y=12, font=FONT_TERMINAL):
        cfi = self.get_font_info()
        cfi.font_size.x = x
        cfi.font_size.y = y
        cfi.font_family = font
        ret = self.SetCurrentConsoleFontEx(self.output, False, pointer(cfi))
        if not ret:
            raise WinError()

    def set_size(self, width, height):
        ret = self.SetConsoleScreenBufferSize(self.output, COORD(width, height))
        if not ret:
            raise WinError()
    
    def set_title(self, title):
        self.SetConsoleTitle(create_unicode_buffer(title))


class ConsoleBuffer:
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
        """
        if not width or not height or not len(self.buffer):
            #log.debug("drawing, x=%r, y=%r, w=%r, h=%r, len=%r", x, y, source.width, source.height, len(self.buffer))
            #log.debug("aborting a null draw")
            return
        #t = time.time()
        #print 'making args'
        buffer_size = COORD(width, height)
        buffer_coord = COORD(0, 0)
        write_region = SMALL_RECT(
            x, 
            y,
            x + width - 1,
            y + height - 1
        )
        #print 'writing'
        ret = console.WriteConsoleOutput(console.output, byref(self.buffer), buffer_size, buffer_coord, byref(write_region))
        if not ret: 
            raise WinError()
        #t = time.time() - t
        #print 'ret', ret
        #print 'took', t
        return #t

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

    #----
    console = Console()
    clearing_test()
    cursor_test()
    xy_test()
    title_test()
    font_test()
    set_color_test()

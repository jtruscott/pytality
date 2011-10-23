"""
    A simple ANSI file editor using Pytality.

    Useful if you're making maps or otherwise doing fancy drawing in an ansi terminal program.

"""
if __name__ == "__main__":
    #We're being run directly. that's fine, but the imports are a little wacky.
    import sys
    sys.path.append('../../')

import pytality
import re

import logging
log = logging.getLogger("pytality.editor")

class Editor(object):
    #state
    width = 100
    height = 50

    #panels
    main_window = None
    menu_window = None
    info_window = None

    def __init__(self, filename=None):
        self.resize_to(self.width, self.height)
        if filename:
            self.load_file(filename)
        self.setup_cursor()
    
    def setup_cursor(self):
        self.cursor_x = 0
        self.cursor_y = 0
        pytality.term.set_cursor_type('block')
        self.move_cursor()
                
    def setup_windows(self):
        bg = pytality.colors.DARKGREY
        fg = pytality.colors.BLACK
        self.menu_window = pytality.buffer.Box(
            x=0, y=0,
            width=self.width, height=3,
            border_fg=fg, border_bg=bg, interior_fg=fg, interior_bg=bg,
            draw_top=False
        )

        self.info_window = pytality.buffer.Box(
            x = 0, y = self.height - 5,
            width=self.width, height=5,
            border_fg=fg, border_bg=bg, interior_fg=fg, interior_bg=bg,
            draw_bottom=False
        )
        self.main_window = pytality.buffer.Box(
            x = 0, y = 3,
            width = self.width, height = self.height - 5 - 3,
            draw_left = False, draw_top = False, draw_right = False, draw_bottom = False,
            padding_x = 1, padding_y = 1,
        )
        self.root_window = pytality.buffer.Buffer(0, 0, children=[self.menu_window, self.info_window, self.main_window])

    def resize_to(self, w, h):
        pytality.term.resize(width=w, height=h)
        self.width = w
        self.height = h
        self.setup_windows()
    
    def load_file(self, filename):
        f = open(filename)
        line = f.readline()
        dimensions = re.match("width: (\d+)", line)
        if dimensions:
            width = dimensions.groups()[0]
        else:
            width = 80
            f.seek(0)
        
        self.data_buffer = pytality.ansi.read_to_buffer(f, width=width, max_height=self.main_window.inner_height, crop=False)
        self.data_view = pytality.buffer.BufferView(
            width=self.main_window.inner_width, height=self.main_window.inner_height,
            parent=self.data_buffer,
            view_x=0, view_y=0
        )
        self.main_window.children = [self.data_view]
        log.debug("data buffer: width=%r, height=%r", self.data_buffer.width, self.data_buffer.height)

    def mark_axes(self):
        view_x = self.data_view.view_x
        view_y = self.data_view.view_y
        top = self.main_window.padding_y
        left = self.main_window.padding_x

        bg = pytality.colors.DARKGREY
        fg = pytality.colors.BLACK
        #label the corner
        self.main_window.set_at(0, 0, ' ', bg=bg)
        self.main_window.set_at(0, 1, ' ', bg=bg)
        self.main_window.set_at(1, 0, ' ', bg=bg)

        #label the X axis
        for x in range(left, self.main_window.width):
            xm = (view_x + x - left) % 10
            cbg = bg
            if (view_x + x - left) == self.cursor_x:
                cbg = pytality.colors.WHITE

            if xm == 5 or xm == 0:
                self.main_window.set_at(x, 0, str(xm), fg=fg, bg=cbg)
            else:
                self.main_window.set_at(x, 0, ' ', fg=fg, bg=cbg)
        
        for y in range(top, self.main_window.height):
            ym = (view_y + y - top) % 10
            cbg = bg
            if (view_y + y - top) == self.cursor_y:
                cbg = pytality.colors.WHITE
            
            if ym == 5 or ym == 0:
                self.main_window.set_at(0, y, str(ym), fg=fg, bg=cbg)
            else:
                self.main_window.set_at(0, y,  ' ', fg=fg, bg=cbg)
                
        self.main_window.dirty = True

    def move_cursor(self, x=0, y=0):
        self.cursor_x = min(self.data_buffer.width-1, max(0, self.cursor_x + x))
        self.cursor_y = min(self.data_buffer.height-1, max(0, self.cursor_y + y))

        view_cursor_x = self.cursor_x - self.data_view.view_x
        if view_cursor_x < 0:
            self.data_view.scroll(x=-1)
            view_cursor_x = self.cursor_x - self.data_view.view_x
        elif view_cursor_x >= self.data_view.width:
            self.data_view.scroll(x=1)
            view_cursor_x = self.cursor_x - self.data_view.view_x

        view_cursor_y = self.cursor_y - self.data_view.view_y
        if view_cursor_y < 0:
            self.data_view.scroll(y=-1)
            view_cursor_y = self.cursor_y - self.data_view.view_y
        elif view_cursor_y >= self.data_view.height:
            self.data_view.scroll(y=1)
            view_cursor_y = self.cursor_y - self.data_view.view_y

        pytality.term.move_cursor(
            view_cursor_x+self.main_window.x+self.main_window.padding_x,
            view_cursor_y+self.main_window.y+self.main_window.padding_y
        )
        self.mark_axes()

    def read_input(self):
        key = pytality.term.getkey()
        if key in ['up', 'down', 'left', 'right']:
            if key == 'up':
                self.move_cursor(y=-1)
            if key == 'down':
                self.move_cursor(y=1)
            if key == 'left':
                self.move_cursor(x=-1)
            if key == 'right':
                self.move_cursor(x=1)
            self.mark_axes()

    def run(self):
        while True:
            self.root_window.draw()
            pytality.term.flip()
            self.read_input()

if __name__ == "__main__":
    try:
        pytality.term.init()
        e = Editor("../../data/Melimnor1")
        e.run()
    finally:
        pytality.term.reset()


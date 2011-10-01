import re
import collections
import logging
import boxtypes
import term

__license__ = "BSD"
__all__ = ['Buffer', 'BaseText', 'PlainText', 'RichText', 'Box']

log = logging.getLogger('screen')

class Buffer:
    """
    A buffer on the screen, representing a rectangular block of cells.
    Can have relatively-positioned children, which are drawn after (on top of) the parent.

    This class can be used directly if you want to manually manage the cell data.
    """
    def __init__(self, width, height,
                data=None,
                x=0, y=0,
                padding_x=0, padding_y=0,
                children=None):
        """
        Create a screen buffer.
        Mandatory arguments:
        width:
            the width of the buffer, in cells
        height:
            the height of the buffer, in cells

        Buffers have a large amount of optional arguments.
        data:
            The initial contents of the buffer, structured as:
            a list, of length height,
            of lists, of length width,
            of [fg, bg, character] lists.

            If not present, it will be initialized as blank cells (black, black, ' ')
        
        x:
        y:
            The X/Y offset to use when drawing, relative to the parent buffer,
            or (0,0) if drawn directly.
            Coordinates start at the top-left and increase in the direction of the bottom-right.

        padding_x:
        padding_y:
            The desired 'padding' of space for child buffers.
            Children see x/y coordinates with padding added, and if they set their
            width to parent.inner_width/parent.inner_height, the 'padded area' will
            not be overwritten by child draws. For example, a buffer which is a box
            having a border around they edge may want a padding of 1.

        children:
            A list of child buffers to draw after this buffer is drawn.
            
        """
        self.width = width
        self.height = height

        if data is None:
            self._reset_data()
        else:
            self._data = data
        self._check_data()
        
        self.padding_x = padding_x
        self.padding_y = padding_y
        self._x = x
        self._y = y
        self.dirty = True

        self.children = children or []

    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, value):
        self._x = x
        self.dirty = True

    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, value):
        self._y = y
        self.dirty = True

    @property
    def inner_width(self):
        return self.width - (self.padding_x*2)

    @property
    def inner_height(self):
        return self.height - (self.padding_y*2)

    def set_at(self, x, y, char=None, fg=None, bg=None):
        """
        Modify the properties of a cell at (x, y).
        Also dirties the buffer for the next draw.
        """
        cell = self._data[y][x]
        if fg is not None:
            cell[0] = fg
        if bg is not None:
            cell[1] = bg
        if char is not None:
            cell[2] = char
        self.dirty = True

    def draw(self, x_offset=0, y_offset=0, dirty=False):
        #xoff and yoff are screen offsets from our parent.
        x_offset = x_offset + self._x
        y_offset = y_offset + self._y
        dirty = dirty or self.dirty

        #put ourselves on the screen
        if dirty:
            term.draw_buffer(self, x_offset, y_offset)

        #have our children do similar
        for child in self.children:
            child.draw(x_offset + self.x_padding, y_offset + self.y_padding, dirty)

    def _reset_data(self):
        rows = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append((term.colors.BLACK, term.colors.BLACK, ' '))
            rows.append(row)
        self._data = rows
    
    def _check_data(self):
        """
        Prevent creating a data buffer which is malformed.
        If they do and this check is skipped, the resulting failure will be
        very far away from the source and hard to track down.
        """
        if not isinstance(self._data, collections.MutableSequence):
            raise ValueError("Buffer data must be a list (not a %r)" % type(self._data))

        if len(self._data) < self.height:
            raise ValueError("Buffer data has %r rows, but a specified height of %r" % (len(rows), self.height))

        for row in self._data:
            if not isinstance(row, collections.MutableSequence):
                raise ValueError("Buffer data rows must be lists (not a %r)" % type(row))
            if len(row) < self.width:
                raise ValueError("Buffer data row has %r cells, but a specified width of %r" % (len(row), self.width))
            
            for cell in row:
                if not isinstance(row, collections.MutableSequence):
                    raise ValueError("Buffer data cells must be lists (not a %r)" % type(cell))
                if len(cell) < 3:
                    raise ValueError("Buffer data cells must have 3 items (fg, bg, char), not %r" % (len(cell)))
        return True

#-----------------------------------------------------------------------------

class BaseText(Buffer):
    """
        A specialized buffer for displaying text.
        The PlainText subclass displays single-color text and can be justified.
        The RichText subclass displays a colorable form of markup.
    """
    def __init__(self, message, **kwargs):
        """
        message:
            The message to be displayed.
            Can be updated with .set(), and formatted with .format()

        """
        self.message = self.base_message = message
        self.update_data()
        Buffer.__init__(self, width=self.width, height=self.height, data=self._data, **kwargs)

    def set(self, message):
        self.message = self.base_message = message
        self.update_data()
    
    def format(self, fmt):
        #log.debug("formatting: (%r) into (%r)", fmt, self.base_message)
        self.message = self.base_message % fmt
        self.update_data()

    def update_data(self):
        """
        'render' the current message into buffer data.
        
        This function is expected to set self.width, self.height, self._data,
        and possibly set self.dirty.
        """
        raise NotImplemented()

class PlainText(BaseText):
    """
    A buffer representing simple text.
    No character conversion or parsing is performed, so any CP437 symbols can
    be used here.
    """
    def __init__(self, message,
                fg=term.colors.LIGHTGREY, bg=term.colors.BLACK,
                max_width=None, center_to=None,
                **kwargs):
        """
        fg:
        bg:
            Color for the foreground and background

        center_to:
            Center the text to N characters in width
            
        max_width:
            Crop the text at N characters in length
        """
        self.width = len(message)
        self.height = 1

        self.fg = fg
        self.bg = bg
        self.max_width = max_width
        self.center_to = center_to
        BaseText.__init__(self, message, **kwargs)

    def update_data(self):
        row = []
        msg = self.message
        if self.center_to:
            msg = msg.center(self.center_to)
        
        if self.max_width:
            msg = msg[:self.max_width]
        
        for c in msg:
           row.append([self.fg, self.bg, c])

        self.width = len(row)
        self.height = 1
        self._data = [row]
        self.dirty = True

class RichText(BaseText):
    """
    A buffer for 'rich' text messages.
    Richtext messages can change colors partway through via the use of markup.
    They can also be more than one line in height (using newlines as linebreaks)
    Example:
        "This text has a <GREEN>word</> inside it!"

    Markup commands are placed inside <> brackets, and should be the uppercase name
    of a Color in the terminal.
    The current colors are tracked in a stack; </> pops down the color stack.

    It might be interesting to implement other commands like <CENTER> later.
    """
    colorRE = re.compile(r'([^<]*)<([\w]*|/)>')

    def __init__(self, message, wrap_to=None, **kwargs):
        """
        wrap_to:
            Wrap the message at a maximum of N characters in width.
            No special logic is performed for tracking words or hyphenating.
        """
        self.wrap_to = wrap_to
        BaseText.__init__(self, message, **kwargs)

    def update_data(self):
        rows = []
        row = []
        message_parts = self.parse()
        
        #build
        for part_color, part_text in message_parts:
            for c in part_text:
                if c == '\n':
                    rows.append(row)
                    row = []
                    continue
                row.append((part_color, self.bg, c))
        
        rows.append(row)

        #wrap
        if self.wrap_to:
            width = self.wrap_to
            new_rows = []
            for row in rows:
                if len(row) > width:
                    wrapped_data = []
                    for i in range(0, len(row), width):
                        chunk = row[i:i+width]
                        new_rows.append(chunk)
                else:
                    new_rows.append(row)
            rows = new_rows

        #pad
        width = max([len(r) for r in rows])
        for row in rows:
            while len(row) < width:
                row.append((self.fg, self.bg, ' '))
        
        
        #finish
        self.width = width
        self.height = len(rows)
        self.data = rows
        self.dirty = True

    def parse(self):
        raw_msg = self.message.rstrip('\n')
        raw_parts = filter(None, self.colorRE.split(raw_msg))
        message_parts = []
        color_stack = [term.LIGHTGREY]
        for part in raw_parts:
            if part == '/':
                #go back a color
                color_stack.pop()
            elif hasattr(term.colors, part):
                #push a new color
                color_stack.append(getattr(term.colors, part))
            else:
                #it's a text component
                message_parts.append((color_stack[-1], part))
        #log.debug("len: %r parts: %r", total_len, message_parts)
        return message_parts


#-----------------------------------------------------------------------------

class Box(Buffer):
    """
    A subclass of Buffer for creating a rectangular box with borders.
    Note that because of the borders, padding_x/padding_y are automatically
    increased by 1.
    """
    def __init__(self,
                width, height,
                padding_x=0, padding_y=0,
                border_fg=term.colors.WHITE, border_bg=term.colors.BLACK,
                interior_fg=term.colors.WHITE, interior_bg=term.colors.BLACK,
                boxtype=boxtypes.BoxDouble,
                draw_top=True, draw_bottom=True, draw_left=True, draw_right=True,
                **kwargs):
        """
        width:
        height:
            The outer dimensions of the box, including the border.
        
        border_fg:
        border_bg:
        interior_fg:
        interior_bg:
            The colors to use for the box's border and interior, respectively.
        
        boxtype:
            A BoxType object with properties for the various border characters.

        draw_top:
        draw_bottom:
        draw_left:
        draw_right:
            Control drawing the border on each side of the box.
            Note that 'corner' characters will only be drawn if both relevant
            sides are enabled.
        """
        data = []
        (blank, horiz, vert, tl, tr, bl, br) = (boxtype.blank, boxtype.horiz, boxtype.vert, boxtype.tl, boxtype.tr, boxtype.bl, boxtype.br)
        vert_left = vert_right = vert
        if not draw_left:
            vert_left = boxtype.blank
            tl = bl = boxtype.horiz

        if not draw_right:
            vert_right = boxtype.blank
            tr = br = boxtype.horiz

        mid_rows = height
        if draw_top:
            mid_rows -= 1
            data.append([[border_fg, border_bg, tl]] + ([[border_fg, border_bg, horiz]]*(width-2)) + [[border_fg, border_bg, tr]])

        if draw_bottom:
            mid_rows -= 1

        for row in range(mid_rows):
            data.append([[border_fg, border_bg, vert_left]] + ([[interior_fg, interior_bg, blank]]*(width-2)) + [[border_fg, border_bg, vert_right]])

        if draw_bottom:
            data.append([[border_fg, border_bg, bl]] + ([[border_fg, border_bg, horiz]]*(width-2)) + [[border_fg, border_bg, br]])

        self._data = data
        Buffer.__init__(self,
                        width=width, height=height,
                        padding_x=padding_x+1, padding_y=padding_y+1,
                        **kwargs)

if __name__ == "__main__":
    left_pointer = PlainText(fg=term.colors.WHITE, bg=term.colors.BLACK, message=term.Pointer.left)
    right_pointer = PlainText(fg=term.colors.WHITE, bg=term.colors.BLACK, message=term.Pointer.right)

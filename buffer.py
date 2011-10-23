import re
import collections
import math
import logging
import boxtypes
import term

__license__ = "BSD"
__all__ = ['Buffer', 'BaseText', 'PlainText', 'RichText', 'Box', 'MessageBox']

log = logging.getLogger('pytality.buffer')

class Buffer(object):
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
        self._x = value
        self.dirty = True

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
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
        if self.dirty:
            dirty = True

        #log.debug("%r dirty? %r", self, dirty)
        #put ourselves on the screen
        if dirty:
            term.draw_buffer(self, x_offset, y_offset)

        #have our children do similar
        for child in self.children:
            child.draw(x_offset + self.padding_x, y_offset + self.padding_y, dirty)

    def _reset_data(self):
        rows = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append([term.colors.BLACK, term.colors.BLACK, ' '])
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

    def __init__(self, message, wrap_to=None, initial_color=term.colors.LIGHTGREY, bg=term.colors.BLACK, **kwargs):
        """
        wrap_to:
            Wrap the message at a maximum of N characters in width.
            No special logic is performed for tracking words or hyphenating.

        initial_color:
            The foreground color that the message will start out as.
            Defaults to LIGHTGREY.

        bg:
            The background color for the message.
            Defaults to BLACK.
        """
        self.wrap_to = wrap_to
        self.initial_color = initial_color
        self.bg = bg
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
                row.append([part_color, self.bg, c])
        
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
                row.append([self.bg, self.bg, ' '])
        
        
        #finish
        self.width = width
        self.height = len(rows)
        #log.debug("text w=%r, h=%r, part0=%r", self.width, self.height, message_parts[0] if message_parts else None)
        self._data = rows
        self.dirty = True

    def parse(self):
        raw_msg = self.message.rstrip('\n')
        raw_parts = filter(None, self.colorRE.split(raw_msg))
        message_parts = []
        color_stack = [self.initial_color]
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
        #log.debug("parts: %r", message_parts)
        return message_parts


#-----------------------------------------------------------------------------

class Box(Buffer):
    """
    A subclass of Buffer for creating a rectangular box with borders.
    Note that because of the borders, padding_x/padding_y default to 1
    """
    def __init__(self,
                width, height,
                padding_x=1, padding_y=1,
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

        #store variables
        self.boxtype = boxtype
        self.border_fg, self.border_bg = border_fg, border_bg
        self.interior_fg, self.interior_bg = interior_fg, interior_bg
        self.draw_top, self.draw_bottom = draw_top, draw_bottom
        self.draw_left, self.draw_right = draw_left, draw_right
        data = []
        
        #break out the boxtype constants we've been given
        blank, horiz, vert, tl, tr, bl, br = (boxtype.blank, boxtype.horiz, boxtype.vert, boxtype.tl, boxtype.tr, boxtype.bl, boxtype.br)

        #form cell descriptions
        tl_cell = [border_fg, border_bg, tl]
        tr_cell = [border_fg, border_bg, tr]
        bl_cell = [border_fg, border_bg, bl]
        br_cell = [border_fg, border_bg, br]

        horiz_cell = [border_fg, border_bg, horiz]
        left_cell = [border_fg, border_bg, vert]
        interior_cell = [interior_fg, interior_bg, blank]
        right_cell = [border_fg, border_bg, vert]
        
        #override sides we aren't drawing
        #(note that skipping 'top' and 'bottom' simply draws one more interior row
        if not draw_left:
            left_cell = interior_cell
            tl_cell = horiz_cell
            bl_cell = horiz_cell

        if not draw_right:
            right_cell = interior_cell
            tr_cell = horiz_cell
            br_cell = horiz_cell

        #create the buffer data
        interior_rows = height

        if draw_top:
            interior_rows -= 1
            data.append([tl_cell] + ([horiz_cell]*(width-2)) + [tr_cell])

        if draw_bottom:
            interior_rows -= 1

        for row in range(interior_rows):
            data.append([left_cell] + ([interior_cell]*(width-2)) + [right_cell])

        if draw_bottom:
            data.append([bl_cell] + ([horiz_cell]*(width-2)) + [br_cell])

        #put the buffer together
        Buffer.__init__(self,
                        width=width, height=height,
                        padding_x=padding_x, padding_y=padding_y,
                        data=data,
                        **kwargs)


class MessageBox(Box):
    """
    A MessageBox is a type of box that is designed to hold a stream of RichText
    messages and be "scrolled" up and down.

    MessageBuffers act as Box buffers that automatically manage their children. Consequently,
    modifications to .children will be lost.

    cursor_offset:
    cursor_boxtype:
    cursor_fg_color:
    autoscroll:
    """
    def __init__(self,
                width, height,
                padding_x=1, padding_y=1,
                scrollbar_type="edge", scrollbar_fg_color=term.colors.WHITE,
                auto_scroll=True,
                **kwargs):
        
        Box.__init__(self,
            width=width, height=height,
            padding_x=padding_x, padding_y=padding_y,
            **kwargs)
        
        self.messages = []
        self.offset = 0
        self.auto_scroll = auto_scroll

        #setup our sub-buffers
        #the scroll cursor
        if scrollbar_type == "edge":
            scroll_cursor = EdgeScrollbar(self.boxtype)
        else:
            scroll_cursor = BlockScrollbar(self.boxtype)

        self.scroll_cursor = scroll_cursor
        self.scrollbar_offset = scroll_cursor.right_margin

        #'partial' message buffers for linewrapped messages
        self.top_partial_message = Buffer(self.inner_width, 1)
        self.bottom_partial_message = Buffer(self.inner_width, 1)
        
        #update our positioning
        self.scroll(home=True)

    def add(self, msg, scroll=None):
        if scroll is None:
            scroll = self.auto_scroll

        message = RichText(msg, wrap_to=self.inner_width - max(0, self.scrollbar_offset))
        self.messages.append(message)

        if scroll:
            self.scroll(end=True)
        else:
            self.recalculate_buffers()

    def scroll(self, delta=0, home=False, end=False):
        """
        Scroll the message log.
        The amount to scroll can be specified in one of three possible ways.

        delta:
            Scroll down X lines (or up X lines if X is negative)
        home:
            Scroll to the top of the log (as in the home key)
        end:
            Scroll to the bottom of the log (as in the end key)
        """
        total_lines = sum([msg.height for msg in self.messages])

        if home:
            offset = 0
        elif end:
            offset = total_lines
        else:
            offset = self.offset + delta


        #maximum the last line on the screen
        if offset + self.inner_height > total_lines:
            offset = total_lines - self.inner_height
        
        #minimum 0
        if offset < 0:
            offset = 0
        self.offset = offset
        self.recalculate_buffers()

    def recalculate_buffers(self):
        """
        Recalculate the positioning and contents of message buffers for a new scroll offset.
        """
        def make_partial_message(msg, target, start=0, end=None, y=0):
            msg_data = msg._data
            if end is None:
                end = len(msg_data)

            msg_data = msg_data[start:end]
            target._data = msg_data
            target.height = len(msg_data)
            target.width = msg.width
            target.y = y

        top_offset = self.offset
        bottom_offset = top_offset + self.inner_height

        #make our partial-messages invisible unless needed
        self.top_partial_message.width = 0
        self.top_partial_message.height = 0
        self.bottom_partial_message.width = 0
        self.bottom_partial_message.height = 0

        child_list = []
        #Keep track of our current, cumulative Y offset
        lineno = 0
        for message in self.messages:
            bottom = lineno + message.height
            if bottom > top_offset > lineno:
                if bottom < bottom_offset:
                    #this message crosses the top edge - we need to split it
                    make_partial_message(message, self.top_partial_message,
                                        start=(message.height - (bottom - top_offset)), y=0)

                else:
                    #and it also crosses the bottom!
                    make_partial_message(message, self.top_partial_message, 
                                        start=(message.height - (bottom - top_offset)), end=(bottom_offset - lineno), y=0)

            elif bottom > bottom_offset > lineno:
                #this message crosses the bottom edge - we need to split it
                make_partial_message(message, self.top_partial_message, 
                                    end=(bottom_offset - lineno), y=(lineno - top_offset))

            else:
                if lineno >= top_offset and bottom <= bottom_offset:
                    #this message belongs in our list
                    new_y = (lineno - top_offset)
                    message.y = new_y
                    child_list.append(message)

                else:
                    #this message does not belong
                    if bottom > bottom_offset:
                        #no further messages will be appearing
                        break
                    
            lineno = bottom

        #update the scroll cursor
        total_height = sum([m.height for m in self.messages])
        self.scroll_cursor.reposition(top_offset, bottom_offset, total_height, self)


        self.children = [self.scroll_cursor, self.top_partial_message] + child_list + [self.bottom_partial_message]
        self.dirty = True

class Scrollbar(PlainText):
    right_margin = 0
    def __init__(self, boxtype):
        self.boxtype = boxtype
        PlainText.__init__(self, boxtype.scrollbar_top)

class EdgeScrollbar(Scrollbar):
    """
    A scrollbar designed to be placed on the right border of a Box.
    Occupies a 1x1 space.
    """
    def reposition(self, top_offset, bottom_offset, message_height, viewport):
        lowest_offset = message_height - viewport.inner_height
        if lowest_offset > 0:
            cur_pct = (float(top_offset) / lowest_offset)
            cur_y = cur_pct * (viewport.inner_height - 1)
            cur_y = int(round(cur_y))

        else:
            cur_y = 0

        self.y = cur_y
        self.x = viewport.inner_width + viewport.padding_x - 1

        if top_offset <= 0:
            self.set_at(0, 0, self.boxtype.scrollbar_top)
        elif bottom_offset >= message_height:
            self.set_at(0, 0, self.boxtype.scrollbar_bottom)
        else:
            self.set_at(0, 0, self.boxtype.scrollbar_center)

class BlockScrollbar(Scrollbar):
    """
    A scrollbar designed to be placed in the right margin of a Box.
    Occupies a variable amount of vertical space.
    """
    right_margin = 1
    def reposition(self, top_offset, bottom_offset, message_height, viewport):
        self.x = viewport.inner_width - viewport.padding_x

        if not message_height or (top_offset == 0 and bottom_offset >= message_height):
            #There's no need for scrolling at all
            self.height = 0
            self.width = 0
            self.y = 0
            return
           
        top_pct = (float(top_offset) / message_height)
        top_y = top_pct * (viewport.inner_height)

        bottom_pct = (float(bottom_offset) / message_height)
        bottom_y = bottom_pct * (viewport.inner_height)
        
        self.y = int(math.floor(top_y))
        self.height = int(math.ceil(bottom_y) - math.floor(top_y))
        self.width = 1

        data = []
        if (top_y % 1) > 0.5:
            data.append([[self.fg, self.bg, self.boxtype.scrollbar_bottom_block]])
        else:
            data.append([[self.fg, self.bg, self.boxtype.scrollbar_center_block]])

        for i in range(self.height-2):
            data.append([[self.fg, self.bg, self.boxtype.scrollbar_center_block]])
        
        if (bottom_y % 1) < 0.5:
            data.append([[self.fg, self.bg, self.boxtype.scrollbar_top_block]])
        else:
            data.append([[self.fg, self.bg, self.boxtype.scrollbar_center_block]])
        
        self._data = data

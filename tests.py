"""
    Unit tests for Pytality.
"""
import unittest
import setup_logging

import term
colors = term.colors

import buffer, boxtypes

import pprint
import random
import time
import logging
log = logging.getLogger("test")

class SPACE:
    pass

class PytalityCase(unittest.TestCase):
    force_backend = None
    width = 80
    height = 50
    #unittest core
    def setUp(self):
        if self.force_backend:
            term.init(backends=[self.force_backend], width=self.width, height=self.height)
        else:
            term.init(width=self.width, height=self.height)
        term.clear()
        term.set_title(self._testMethodName)

    def tearDown(self):
        term.move_cursor(x=0, y=max(0, self.height-8))
        term.reset()

    #helpers
    def check(self, x, y, ch=None, fg=None, bg=None):
        """
        Check that a cell's content is what it should be
        """
        tfg, tbg, tch = term.get_at(x, y)
        if ch is not None:
            if ch is SPACE:
                #some terminals use null and some use ' ' for blank space
                self.assertTrue(tch in ['\x00', ' '], "%r is not a blank space" % tch)
            else:
                #as usual, curses irritates me, because it has to translate strings to render them properly.
	        if hasattr(term.impl, 'uni'):
                    ch = term.impl.uni(ch)
                self.assertEqual(ch, tch, msg="Got %r '%s' instead of %r '%s'" % (tch, tch, ch, ch))
        
        #some platforms (curses) do not support colors in get_at
        if tfg is None or tbg is None:
            return

        if fg is not None:
            self.assertEqual(fg, tfg)
        if bg is not None:
            self.assertEqual(bg, tbg)

    def draw_box(self, box):
        """
        Draw a box, and check that it has drawn correctly
        """
        box.draw()
        term.flip()
        
        #check the border is blitting
        if box.draw_left and box.draw_top:
            self.check(box.x, box.y, box.boxtype.tl, fg=box.border_fg, bg=box.border_bg)
        if box.draw_right and box.draw_top:
            self.check(box.x + box.width - 1, box.y, box.boxtype.tr, fg=box.border_fg, bg=box.border_bg)
        if box.draw_right and box.draw_bottom:
            self.check(box.x + box.width - 1, box.y + box.height - 1, box.boxtype.br, fg=box.border_fg, bg=box.border_bg)
        if box.draw_left and box.draw_bottom:
            self.check(box.x, box.y + box.height - 1, box.boxtype.bl, fg=box.border_fg, bg=box.border_bg)
        
        if box.draw_left and box.inner_height:
            self.check(box.x, box.y+1, box.boxtype.vert, fg=box.border_fg, bg=box.border_bg)
        if box.draw_top and box.inner_width:
            self.check(box.x+1, box.y, box.boxtype.horiz, fg=box.border_fg, bg=box.border_bg)
        
        if box.inner_width and box.inner_height:
            self.check(box.x+1, box.y+1, SPACE, fg=box.interior_fg, bg=box.interior_bg)
            self.check(box.x+box.width-1-1, box.y+box.height-1-1, SPACE, fg=box.interior_fg, bg=box.interior_bg)


class Term(PytalityCase):
    def test_getch(self):
        x = 0; y = 0
        for bgcolor in (colors.BLACK, colors.GREEN, colors.RED):
            for fgcolor in (colors.BLACK, colors.DARKGREY, colors.LIGHTGREY, colors.WHITE, colors.RED, colors.LIGHTRED):
                x += 1; y += 1
                p = buffer.Buffer(width=1, height=1, x=x, y=y, data=[[[fgcolor, bgcolor, 'Q']]]); p.draw(); term.flip();
                self.check(x=x, y=y, fg=fgcolor, bg=bgcolor, ch='Q')
    #tests
    def test_clear(self):
        term.clear()
        self.check(0, 0, SPACE, colors.BLACK, colors.BLACK)
        self.check(self.width-1, self.height-1, SPACE, colors.BLACK, colors.BLACK)

    def test_repeat_setup(self):
        self.setUp()
        self.tearDown()

    def test_resize(self):
        #change both
        term.resize(80, 24)
        # try it twice to change nothing
        term.resize(80, 24)
        #grow both
        term.resize(120, 60)

        #shrink Y
        term.resize(120, 59)
        #grow Y
        term.resize(120, 61)

        #shrink X
        term.resize(118, 61)
        #grow X
        term.resize(120, 61)

        #grow one, shrink the other
        term.resize(121, 60)
        term.resize(119, 62)

        #change nothing
        term.resize(119, 62)

        #restore
        term.resize(self.width, self.height)

    def test_not_setup(self):
        _impl = term.impl
        try:
            term.impl = None
            term.reset()
        finally:
            term.impl = _impl
    
    def test_set_title(self):
        term.set_title("abcdefg")
        #how would I check this?

    def test_set_cursor_type(self):
        for val in ("blank", "normal", "block", 0, 1, 2, "normal"):
            term.set_cursor_type(val)
            #how would I check this?

    def skip_test_blink_timing(self):
        import time
        term.set_cursor_type(1)
        term.move_cursor(1, 1)
        t = buffer.PlainText("Time!", x=0, y=0)
        t.draw()

        start = time.time()
        while time.time() - start < 2:
            term.flip()
        
        t.set("Keys!")
        t.draw()
        term.flip()
        for i in range(10):
            term.getkey()


    def test_get_at(self):
        self.assertRaises(ValueError, term.get_at, x=-1, y=-1)
        self.assertRaises(ValueError, term.get_at, x=self.width, y=self.height)
        
    def test_getkey(self):
        raw_getkey = term.impl.raw_getkey
        def gk(*rets):
            #all of the yuck
            i = [0]
            def mock():
                if i[0] == len(rets):
                    return
                r = rets[i[0]]
                i[0] = i[0] + 1
                return r

            term.impl.raw_getkey = mock
        try:
            gk('a'); self.assertEqual(term.getkey(), 'a')
            gk('C'); self.assertEqual(term.getkey(), 'C')
            gk('pgdn'); self.assertEqual(term.getkey(), 'pgdn')
            gk(None, 'b'); self.assertEqual(term.getkey(), 'b')

            gk('\x01'); self.assertEqual(term.getkey(), 'ctrl-a')
            gk('\x03'); self.assertRaises(KeyboardInterrupt, term.getkey)
        finally:
            term.impl.getkey = raw_getkey


class Buffer(PytalityCase):
    def test_invalid_data(self):
        self.assertRaises(ValueError, buffer.Buffer, width=1, height=1, data=0)
        self.assertRaises(ValueError, buffer.Buffer, width=1, height=1, data=[])
        self.assertRaises(ValueError, buffer.Buffer, width=1, height=1, data=[0])
        self.assertRaises(ValueError, buffer.Buffer, width=1, height=1, data=[[]])
        self.assertRaises(ValueError, buffer.Buffer, width=1, height=1, data=[[0]])
        self.assertRaises(ValueError, buffer.Buffer, width=1, height=1, data=[[['a', 'b']]])
        self.assertTrue(buffer.Buffer(width=1, height=1, data=[[[0, 0, 0]]]))

    def test_oob_blit(self):
        nullbuff = buffer.Buffer(x=10, y=10, width=0, height=0)
        nullbuff.draw()
        
        whitebox = buffer.Box(x=10, y=10, width=5, height=5,interior_bg=colors.WHITE)
        redbox = buffer.Box(x=10, y=10, width=5, height=5,interior_bg=colors.RED)
        bluebox = buffer.Box(x=10, y=10, width=5, height=5,interior_bg=colors.BLUE)
        self.draw_box(whitebox)

        redbox.x = -1
        redbox.y = -1
        redbox.draw()
        term.flip()

        self.check(0, 0, bg=colors.RED)
        self.check(self.width-1, self.height-1, bg=colors.BLACK)

        bluebox.x = self.width - 2
        bluebox.y = self.height - 2
        bluebox.draw()
        term.flip()
        self.check(self.width-2, self.height-2, ch=boxtypes.BoxDouble.tl)
        self.check(self.width-1, self.height-1, bg=colors.BLUE)

    def test_large_random_blit(self):
        #let's make this test random yet deterministic
        r = random.Random()
        r.seed(1356317227)

        def make_box():
            return buffer.Buffer(width=self.width, height=self.height, data=[
                [
                    [int(r.triangular(0, 15)), int(r.triangular(0, 7)), chr(r.randint(0, 255))]
                    for x in range(self.width)
                ] for y in range(self.height)
            ])
        box = make_box()

        for i in range(10):
            for i in range(80):
                box.set_at(
                    x=r.randint(0, self.width-1), 
                    y=r.randint(0, self.height-1), 
                    char=chr(r.randint(0, 255)),
                    fg=int(r.triangular(0, 15)),
                    bg=int(r.triangular(0, 7)),
                )
            box.draw()
            term.flip()

        for i in range(15):
            box = make_box()
            box.draw()
            term.flip()

    def test_allcharacters(self):
        r = random.Random()
        r.seed(1356317227)

        def make_box(start_color):
            box = buffer.Buffer(width=self.width, height=self.height)
            i = 0
            bg = start_color
            fg = 0
            for x in range(self.width):
                for y in range(self.height):
                    fg += 1
                    if fg == 16:
                        fg = 0
                        bg += 1
                        if bg % 8 == 0:
                            bg = 0

                    box.set_at(
                        x=x, 
                        y=y, 
                        char=chr(i % 256), 
                        bg=bg,
                        fg=fg
                    )
                    i += 1
            return box
        boxes= [make_box(i) for i in range(16)]

        for i in range(30):
            r.choice(boxes).draw()
            term.flip()

class PlainText(PytalityCase):
    def test_make_text(self):
        msg = "abcdef"
        txt = buffer.PlainText(msg)
        self.assertEqual(msg, txt.message)
        self.assertEqual(msg, txt.base_message)

        msg2 = "abcdef %s"
        txt.set(msg2)
        self.assertEqual(msg2, txt.message)
        self.assertEqual(msg2, txt.base_message)

        part = "hats!"
        txt.format(part)
        self.assertEqual(msg2 % part, txt.message)
        self.assertEqual(msg2, txt.base_message)


    def test_draw_text(self):
        msg = "abcdef"
        txt = buffer.PlainText(msg)

        for i in range(10):
            txt.x = i
            txt.y = i
            txt.draw()
        term.flip()
        self.check(0, 0, 'a')
        self.check(1, 0, 'b')
        self.check(4, 2, 'c')

class Box(PytalityCase):
    def test_make_box(self):
        box = buffer.Box(x=10, y=10, width=4, height=4)
        self.draw_box(box)

        #check it isnt blitting where it shouldnt
        self.check(9, 9, SPACE)
        self.check(11, 11, SPACE)
        self.check(15, 15, SPACE)



        box2 = buffer.Box(x=12, y=12, width=6, height=6,
                        border_fg=colors.RED, border_bg=colors.LIGHTRED, interior_bg=colors.DARKGREY,
                        draw_left=False, draw_top=False)
        
        self.draw_box(box2)
        self.check(12, 12, SPACE, bg=colors.DARKGREY)
        self.check(12, 13, SPACE)
        self.check(13, 12, SPACE)
        self.check(17, 17, boxtypes.BoxDouble.br, fg=colors.RED, bg=colors.LIGHTRED)

    def test_nested(self):
        r = random.Random()
        r.seed(1356317227)

        root = buffer.Buffer(width=0, height=0)
        current = root
        all = []
        i = 0
        for sub in range(0, min(self.height, self.width), 4):
            h = self.height - sub
            w = self.width - sub
            i += 1
            b = buffer.Box(width=w, height=h, border_fg=(i % 16), border_bg=(i + 1) % 8)
            current.children.append(b)
            all.append(b)
            current = b

        for i in range(30):
            root.draw()
            b = r.choice(all)
            for j in range(20):
                b.set_at(
                    x=r.randint(0, b.width-1), 
                    y=r.randint(0, b.height-1),
                    char=chr(r.randint(0, 255)),
                    fg=int(r.triangular(0, 15)),
                    bg=int(r.triangular(0, 7)),
                )
            term.flip()

    def skip_test_permute(self):
        import cgitb
        try:
            for x in [0, 10]:
                for y in [0, 10]:
                    for width in [2, 10, 30]:
                        for height in [2, 10, 30]:
                            for border_fg in [colors.RED, colors.WHITE, colors.BLACK]:
                                for interior_fg in [colors.WHITE, colors.LIGHTGREY]:
                                    for border_bg in [colors.BLACK, colors.BLUE]:
                                        for interior_bg in [colors.BLACK, colors.DARKGREY]:
                                            for draw_left in [False, True]:
                                                for draw_right in [False, True]:
                                                    for draw_top in [False, True]:
                                                        for draw_bottom in [False, True]:
                                                            for boxtype in [boxtypes.BoxDouble, boxtypes.BoxSingle]:
                                                                self.draw_box(buffer.Box(x=x, y=y, width=width, height=height,border_fg=border_fg, interior_fg=interior_fg,border_bg=border_bg, interior_bg=interior_bg,draw_left=draw_left, draw_right=draw_right,draw_top=draw_top, draw_bottom=draw_bottom,boxtype=boxtype))
        except:
            #resize changes the scrollback buffer size...
            term.resize(width=self.width, height=300)
            cgitb.Hook(format="text").handle()
            raise
    
    def test_set_at(self):
        box = buffer.Box(x=10, y=10, width=6, height=6)
        self.draw_box(box)
        log.debug(pprint.pformat(box._data))
        box.set_at(2, 2, '0', colors.LIGHTGREY)
        log.debug(pprint.pformat(box._data))
        box.draw()
        term.flip()
        self.check(12, 12, '0')
        self.check(13, 13, ' ')
        self.check(12, 13, ' ')
        self.check(13, 12, ' ')

class MessageBox(PytalityCase):
    def add(self, msg, **kwargs):
        if isinstance(msg, list):
            for m in msg:
                self.box.add(m, **kwargs)
        else:
            self.box.add(msg, **kwargs)
        self.box.draw()
        term.flip()

    def scroll(self, *args, **kwargs):
        self.box.scroll(*args, **kwargs)
        self.box.draw()
        term.flip()

    def test_make_box(self):
        box = self.box = buffer.MessageBox(x=5, y=5, width=20, height=20,
                                padding_x=1, padding_y=1)
        self.draw_box(box)
        
        self.check(5, 5, boxtypes.BoxDouble.tl)
        self.check(6, 6, SPACE)

        self.add("a<RED>A")
        self.add("bb")
        self.add("ccc")
        self.add("dddd")
        self.check(6, 6, 'a')
        self.check(6, 7, 'b')
        
        self.add("twenty\n"*20, scroll=False)
        self.check(6, 7, 'b')
        
        self.add("eeeee")
        self.check(6, 6, 't')
        self.check(6, 23, 'e')

        box.scroll(home=True)
        box.draw()
        term.flip()
        self.check(6, 6, 'a')
        self.check(6, 23, 't')
        self.check(6, 24, boxtypes.BoxDouble.horiz)
        
        self.add('\n'.join([str(i) + "!" for i in range(30)]))
        self.check(6, 5, boxtypes.BoxDouble.horiz)
        self.check(6, 6, '1')
        self.check(7, 6, '2')
        self.check(6, 23, '2')
        self.check(7, 23, '9')
        self.check(6, 24, boxtypes.BoxDouble.horiz)
        
        box.scroll(-3)
        box.draw()
        term.flip()
        self.check(6, 6, '9')

    def test_edge_scrollbar(self):
        bt = boxtypes.BoxDouble
        box = self.box = buffer.MessageBox(x=1, y=20, width=20, height=20,
                                padding_x=3, padding_y=1, boxtype=bt)
        self.draw_box(box)
        self.check(1, 20, bt.tl)
        self.add(["line %s" % i for i in range(18)])

        #r = the right border where the scrollbar is
        r = box.x + box.width - 1
        #t = the top of the scrollbar area, b = the bottom of such
        t = box.y + 1
        b = box.y + box.height - box.padding_y*2

        #18/18 lines should not cause us to scroll
        self.check(r, t, bt.scrollbar_top)
        
        #and scroll commands should do nothing
        self.scroll(1); self.check(r, t, bt.scrollbar_top)
        self.scroll(-1); self.check(r, t, bt.scrollbar_top)

        #but with one line of overflow, it can be at the bottom or top
        self.add("overflow 1")
        self.check(r, b, bt.scrollbar_bottom)
        self.scroll(-1); self.check(r, t, bt.scrollbar_top)

        #and with two, there's a middle
        self.add("overflow 2")
        self.check(r, b, bt.scrollbar_bottom)
        self.scroll(-1); self.check(r, t+9, bt.scrollbar_center)
        self.scroll(-1); self.check(r, t, bt.scrollbar_top)
        self.scroll(+1); self.check(r, t+9, bt.scrollbar_center)
        self.scroll(end=True); self.check(r, b, bt.scrollbar_bottom)
        self.scroll(home=True); self.check(r, t, bt.scrollbar_top)

        #now we want to know what a bunch of lines (total of 10x inner height) does
        self.add(["spam line %s" % i for i in range(160)])
        self.check(r, b, bt.scrollbar_bottom)
        self.scroll(-1); self.check(r, b, bt.scrollbar_center)
        self.scroll(-5); self.check(r, b-1, bt.scrollbar_center)
        self.scroll(-60); self.check(r, b-7, bt.scrollbar_center)
        self.scroll(home=True); self.check(r, t, bt.scrollbar_top)
        self.scroll(10); self.check(r, t+1, bt.scrollbar_center)

        #and then let's make sure it never explodes while scrolling in a huge area
        #this also takes long enough to function as a graphical human test
        self.add(["thousand %s" % i for i in range(1000)])
        self.scroll(home=True); self.check(r, t, bt.scrollbar_top)
        for i in range(1180):
            self.scroll(1)
        self.check(r, b, bt.scrollbar_bottom)


class Microgames(PytalityCase):

    def test_waterfall(self):
        #make a silly little waterfall
        r = random.Random()
        r.seed(1356317227)

        center = 0
        def make_fall():
            color = random.choice([colors.WHITE, colors.LIGHTGREY, colors.LIGHTBLUE, colors.BLUE])
            x = int(random.triangular(0, self.width, mode=center))
            return buffer.Buffer(width=1, height=5, x=x, y=-4, data=[
                [[color, colors.BLACK, ' ']],
                [[color, colors.BLACK, '\xb0']],
                [[color, colors.BLACK, '\xb1']],
                [[color, colors.BLACK, '\xb2']],
                [[color, colors.BLACK, '\xdb']],
            ])
        items = [make_fall()]

        frames = 150
        start = time.time()
        for i in range(frames):
            if i < frames/2:
                center += 1
            else:
                center -= 1

            items.extend([make_fall() for _ in range(4)])
            for item in items:
                item.y += 1
                if item.y > self.height:
                    items.remove(item)
                else:
                    item.draw()
            term.flip()
        end = time.time()
        fps = frames / (end - start)
        log.debug("waterfall FPS: %.2f over %r frames", fps, frames)
        self.assertGreater(fps, 40)

    def test_pattern(self):
        #inspired by the space-filler algorithm at https://dl.dropbox.com/u/1094010/Projs/spacefill.html
        #designed to use a lot of little buffers as an alternate performance test
        #it flips a new frame on every 25 calculations, to be a little fair to poor slow-flip winconsole
        r = random.Random()
        r.seed(1356317227)
        seen = set()
        candidates = [(r.randint(0, self.width), r.randint(0, self.height), 0)]
        step = 0
        buffers = []
        
        start = time.time()

        # just count the last one now
        draws = 1  
        while candidates:
            next_index = step % len(candidates)
            x, y, depth = candidates.pop(next_index)
            step += 1
            for xoff, yoff in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
                nx = x + xoff
                ny = y + yoff
                if (nx, ny) in seen or nx < 0 or ny < 0 or nx > self.width or ny > self.height:
                    continue
                seen.add((nx, ny))
                candidates.append((nx, ny, depth+1))

            b = buffer.Buffer(x=x, y=y, width=1, height=1, data=[
                [
                    [step % 15 + 1, colors.BLACK, '\xb0']
                ]
            ])
            buffers.append(b)
            b.draw()
            if step % 25 == 0:
                term.flip()
                draws += 1

        term.flip()
        end = time.time()
        fps = draws / (end - start)
        log.debug("pattern FPS: %.2f over %r frames", fps, draws)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ['silverlight', 'pygame', 'winconsole', 'curses']:
        PytalityCase.force_backend = sys.argv.pop(1)

    if 'profile' in sys.argv:
        sys.argv.remove('profile')
        import cProfile
        cProfile.run("unittest.main()")

    else:
        unittest.main()

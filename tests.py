"""
    Unit tests for Pytality.
"""
import unittest
import setup_logging

import term
colors = term.colors

import buffer, boxtypes

class SPACE:
    pass

class PytalityCase(unittest.TestCase):
    width = 120
    height = 60
    #unittest core
    def setUp(self):
        term.init(width=self.width, height=self.height)

    def tearDown(self):
        term.reset()

    #helpers
    def check(self, x, y, ch=None, fg=None, bg=None):
        tfg, tbg, tch = term.get_at(x, y)
        if ch is not None:
            if ch is SPACE:
                #some terminals use null and some use ' ' for blank space
                self.assertTrue(tch in ['\x00', ' '], "%r is not a blank space" % tch)
            else:
                self.assertEqual(ch, tch)
        if fg is not None:
            self.assertEqual(fg, tfg)
        if bg is not None:
            self.assertEqual(bg, tbg)

class Term(PytalityCase):
    #tests
    def test_clear(self):
        term.clear()
        self.check(0, 0, SPACE, colors.BLACK, colors.BLACK)
        self.check(self.width-1, self.height-1, SPACE, colors.BLACK, colors.BLACK)

    def test_repeat_setup(self):
        self.setUp()
        self.tearDown()

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
        box.draw()
        term.flip()

        #check it isnt blitting where it shouldnt
        self.check(9, 9, SPACE)
        self.check(11, 11, SPACE)
        self.check(15, 15, SPACE)

        #check the border is blitting
        self.check(10, 10, boxtypes.BoxDouble.tl)
        self.check(13, 13, boxtypes.BoxDouble.br)
        self.check(11, 10, boxtypes.BoxDouble.horiz)
        self.check(10, 11, boxtypes.BoxDouble.vert)

        box2 = buffer.Box(x=6, y=6, width=6, height=6,
                        border_fg=colors.RED, border_bg=colors.LIGHTRED, interior_bg=colors.DARKGREY,
                        draw_left=False, draw_top=False)
        box.draw()
        term.flip()
        self.check(12, 12, SPACE, bg=colors.DARKGREY)
        self.check(12, 13, SPACE)
        self.check(13, 12, SPACE)
        self.check(17, 17, boxtypes.BoxDouble.br, fg=colors.RED, bg=colors.LIGHTRED)

class MessageBox(PytalityCase):
    def test_make_box(self):
        box = buffer.MessageBox(x=5, y=5, width=20, height=20,
                                padding_x=1, padding_y=1)
        box.draw()
        term.flip()
        
        self.check(5, 5, boxtypes.BoxDouble.tl)
        self.check(6, 6, SPACE)

        def add(*args, **kwargs):
            box.add(*args, **kwargs)
            box.draw()
            term.flip()
        add("a<RED>A")
        add("bb")
        add("ccc")
        add("dddd")
        self.check(6, 6, 'a')
        self.check(6, 7, 'b')
        
        add("twenty\n"*20, scroll=False)
        self.check(6, 7, 'b')
        
        add("eeeee")
        self.check(6, 6, 't')
        self.check(6, 23, 'e')

        box.scroll(home=True)
        box.draw()
        term.flip()
        self.check(6, 6, 'a')
        self.check(6, 23, 't')
        self.check(6, 24, boxtypes.BoxDouble.horiz)
        
        add('\n'.join([str(i) + "!" for i in range(30)]))
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
        raw_input()

if __name__ == "__main__":
    unittest.main()

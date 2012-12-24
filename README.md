#Pytality - It's terminal.

Pytality is a library for writing games that use the text console and all of it's features.
It was written as a reusable library after making two seperate terminal games for Ludum Dare and Pyweek.
It's been tested in compo conditions in a later Ludum Dare and occasionally improved.

Supported Features
------------------
* the 16 ANSI colors
* the 256 CP437 characters
* double-buffered rendering
* blitting of rectangular data regions
* managing of colorized "rich text"

Supported Platforms
-------------------
* windows (using ctypes wrappers to the Win32 APIs)
* linux/mac (using curses)
* inside the browser (via IronPython + Silverlight/Moonlight)
* windows/linux/mac (using pygame)

Requirements
------------
* Python 2.6+
* Nothing else!
    
Installation
------------
Just put the 'pytality' package in your python path. If you're writing something using Pytality, don't hesistate to include the folder with your game directly.

Usage
-----

Import Pytality and initialize the terminal:

    import pytality
    pytality.term.init()

Make a rectangular box:

    box = pytality.buffer.Box(x=1, y=2, width=10, height=20)

Draw it and flip the screen:

    box.draw()
    pytality.term.flip()

Finally, tear down the terminal.

    pytality.term.reset()

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
* (experimental) inside the browser (via IronPython + Silverlight/Moonlight)
* windows/linux/mac (using pygame)

Requirements
------------
* Python 2.6+
* Additional requirements depend on what backends you wish to use:
    * Pygame requres Pygame, of course
    * Curses requires curses, naturally
    
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
    
Stability
---------
Pytality was written to be lightweight and has a decent array of unit tests.
Most of the API functions have reasonably thorough docstrings, as well.

The level of support for the various backends does vary.
* The winconsole backend is very stable and works quite well.
    
    Using it will give you the true console experience.
* The pygame backend is also very stable, and actually runs significantly faster than winconsole does.

    It's pixel-for-pixel identical to the windows console in output, making it good for cross-platform use.

* The curses backend is, unfortunately, not recommended.

    When using it, you'll quickly find out that different terminal emulators have completely different ideas of what
    some characters should look like, resulting in all the fun font, margin, and sizing issues typically associated with HTML/CSS work.
    Additionally, it's not possible to portably resize a curses terminal from inside, leading to "my screen is too small!" bug reports.

* The ironpython+silverlight backend is as wacky as it sounds. It's a fascinating proof of concept, but I wouldn't rely on it.
* More backends are possible!
    
   The silverlight experiment was done to try running in-browser, which is desirable for Ludum Dare entries. 
   It may also be possible to use IronPython in Unity3d to accomplish that goal. Jython unfortunately doesn't support applets.

You can call `pytality.term.init(backends=["pygame", "winconsole"])` to specify what backends are allowed.

import os
import pygame
from pygame.locals import *

import logging
log = logging.getLogger('pytality.term.pygame')

log.debug("pygame version: %r", pygame.version.ver)

class colors:
    """
    Constants for the sixteen ANSI colors.
    For pygame, these are simple ints that map to which file to blit
    """
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

"""
    A mapping of special keycodes into representative strings.
    Based off the keymap in WConio, but with 'alt', 'ctrl', and 'shift'
    stripped in order to be portable with the other pytality backends.
"""
key_map = {
    K_RETURN: 'enter',
    K_F1 : 'f1',
    K_F2 : 'f2',
    K_F3 : 'f3',
    K_F4 : 'f4',
    K_F5 : 'f5',
    K_F6 : 'f6',
    K_F7 : 'f7',
    K_F8 : 'f8',
    K_F9 : 'f9',
    K_F10 : 'f10',

    K_INSERT : 'ins',
    K_DELETE : 'del',
    K_HOME : 'home',
    K_END : 'end',
    K_PAGEDOWN : 'pgdn',
    K_PAGEUP : 'pgup',

    K_DOWN : 'down',
    K_LEFT : 'left',
    K_RIGHT : 'right',
    K_UP : 'up',
}

#image path
#todo: figure out how I want to make this configurable
base_path = os.path.join(os.path.dirname(__file__), 'silverlight_html', 'images')

#pixel dimensions of each cell
W = 8
H = 12

#loaded sprite data
sprites = {}

#have we quit?
quit = False

def init(use_cp437=True):
    pygame.init()
    
    #There are several kinds of event we are patently not interested in
    pygame.event.set_blocked([
        MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP,
        JOYAXISMOTION, JOYBALLMOTION, JOYHATMOTION, JOYBUTTONDOWN, JOYBUTTONUP,

        #we only need KEYDOWN
        KEYUP
    ])

    #prepare the raw_getkey generator
    prepare_raw_getkey()

def convert_glyph(ordinal):
    return chr(ordinal)

def load_sprites():
    if 'bg' in sprites:
        #we only need to load once
        return
    
    def load_image(key_name, *filepath):
        full_path = os.path.join(base_path, *filepath)
        surface = pygame.image.load(full_path).convert_alpha()
        sprites[key_name] = surface
    
    load_image('bg', 'colors.png')
    for color_id in range(16):
        load_image(color_id, 'char', '%s.png' % color_id)

#----------------------------------------------------------------------------
#Actual functions

def flip():
    #keep the event queue happy

    for event in pygame.event.get([
        #this should be all the event types we aren't blocking
        #and aren't about keyboard input
        QUIT,
        ACTIVEEVENT,
        VIDEORESIZE,
        VIDEOEXPOSE,
        USEREVENT
    ]):
        if event.type == QUIT:
            raise KeyboardInterrupt()
        else:
            #we don't actually care
            pass

    #flip the screen
    pygame.display.flip()

def clear():
    if quit:
        return
    
    screen.fill((0, 0, 0))

    global cell_data
    cell_data = [
        [
            [0, 0, ' ']
            for cell in range(screen.get_width()/W)
        ]
        for row in range(screen.get_height()/H)
    ]

def resize(width, height):
    global screen
    screen = pygame.display.set_mode((width*W, height*H))
    
    #load the console images to blit later
    load_sprites()

    #set our max dimensions
    global max_x, max_y
    max_x, max_y = width, height

    clear()
    flip()
        
    
def reset():
    pygame.display.quit()
    global quit
    quit = True

def move_cursor(x, y):
    #todo
    pass

def set_title(title):
    pygame.display.set_caption(title)

def set_cursor_type(i):
    #todo
    pass

def draw_buffer(source, start_x, start_y):
    #log.debug("drawing a w=%r, h=%r buffer at x=%r, y=%r", source.width, source.height, start_x, start_y)
    #log.debug("firstfour: %r", source._data[0][:4])
    #render the buffer to our backing
    global cell_data

    y = start_y
    
    #lookups we can cache
    width, height = max_x, max_y
    bg_sprite = sprites['bg']

    for row in source._data:
        if y < 0:
            y += 1
            continue
        if y >= height:
            break
        x = start_x
        for fg, bg, ch in row[:source.width]:
            if x < 0:
                x += 1
                continue
            if x >= width:
                break

            fg_sprite = sprites[fg]
            index = ord(ch)

            #coordinates on the screen
            screen_x = x * W
            screen_y = y * H

            #coordinates on the bg sprite map
            bg_x = bg * W

            #coordinates on the fg sprite map
            fg_x = (index % 16) * W
            fg_y = int(index / 16) * H

            #blit the background and foreground to the screen
            screen.blit(bg_sprite, dest=(screen_x, screen_y), area=pygame.Rect(bg_x, 0, W, H))
            screen.blit(fg_sprite, dest=(screen_x, screen_y), area=pygame.Rect(fg_x, fg_y, W, H))

            #remember the info for get_at
            cell_data[y][x] = [fg, bg, ch]
            
            x += 1
        y += 1

    source.dirty = False
    return

def get_at(x, y):
    if x < 0 or x >= max_x or y < 0 or y >= max_y:
        raise ValueError("get_at: Invalid coordinate (%r, %r)" % (x,y))
    global cell_data
    return cell_data[y][x]


def prepare_raw_getkey():
    """
    It looks like pygame fully intends for you to process _all_ keyboard input at the moment you
    look at the event queue.

    That won't do here. so we turn raw_getkey into a generator.

    Worse, pygame.event.wait() can't filter by type and removes the event from the queue,
    so we have to keep re-adding events we didn't want in the first place. Ugh.
    """
    #this is weird - pygame turns off keyboard repeat by default, which you can re-enable
    #by setting a delay in ms, but "what the system normally does" is not an option.
    #it seems like 150ms delay and 15 keys-per-second is normalish.
    pygame.key.set_repeat(150, 1000 / 15)

    global raw_getkey
    def translate(event):
        log.debug("key event: %r", event.dict)
        if event.key in key_map:
            return key_map[event.key]
        return event.unicode

    def keypump():
        items = []
        while True:
            if not items:
                if pygame.event.peek(KEYDOWN):
                    #there's keyboard input pending! great!
                    items.extend(pygame.event.get(KEYDOWN))

                else:
                    #there's no keyboard input pending, so we need to take a nap until there is.

                    #if we get an event we dont care about, we have to put it back
                    #but if we put it back, .wait() will give it right back to us
                    #so we have to keep it around until we find what we want, then re-add it.
                    #ugh.
                    ignored_items = []
                    while True:
                        item = pygame.event.wait()
                        if item.type != KEYDOWN:
                            ignored_items.append(item)
                        else:
                            items.append(item)
                            break
                    
                    for ignored_item in ignored_items:
                        pygame.event.post(ignored_item)


            yield translate(items.pop(0))

    #assign the generator's next() method as raw_getkey
    raw_getkey = keypump().next


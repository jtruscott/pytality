import os
import pygame
import threading, time
from pygame.locals import *

import logging
log = logging.getLogger('pytality.term.pygame')

log.debug("pygame version: %r", pygame.version.ver)

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

#blinky cursor stuff
cursor_thread = None
replaced_character = None
cursor_x = 0
cursor_y = 0
cursor_type = None

class CursorThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(CursorThread, self).__init__(*args, **kwargs)
        self.quitEvent = threading.Event()

    def run(self):
        blink = True
        while True:
            blink = not blink
            try:
                pygame.event.post(pygame.event.Event(USEREVENT, blink=blink))
            except pygame.error:
                return

            if self.quitEvent.wait(timeout=0.5):
                break

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

    global quit
    quit = False

    #spawn a blinky-cursor manager
    global cursor_thread, replaced_character, cursor_x, cursor_y, cursor_type
    
    cursor_x = 0
    cursor_y = 0
    replaced_character = None
    cursor_type = None

    cursor_thread = CursorThread()
    cursor_thread.daemon = True
    cursor_thread.start()

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


def blink_cursor(event):
    global replaced_character
    if event.blink:
        replace_character()
    else:
        restore_character()

def replace_character():
    global replaced_character
    if not cursor_type:
        return

    fg, bg, ch = get_at(cursor_x, cursor_y)
    replaced_character = (cursor_x, cursor_y, fg, bg, ch)

    blit_at(cursor_x, cursor_y, 7, bg, cursor_type)
    pygame.display.flip()

def restore_character():
    global replaced_character
    if not replaced_character:
        return
    x, y, fg, bg, ch = replaced_character
    blit_at(x, y, fg, bg, ch)
    pygame.display.flip()
    replaced_character = None

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
        elif event.type == USEREVENT:
            blink_cursor(event)
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
            for cell in range(max_x)
        ]
        for row in range(max_y)
    ]

def resize(width, height):
    global screen
    screen = pygame.display.set_mode((width*W, height*H))
    #we don't use alpha, and turning it off makes it a tad faster
    screen.set_alpha(None)
    
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
    cursor_thread.quitEvent.set()
    cursor_thread.join()

def move_cursor(x, y):
    global cursor_x, cursor_y
    restore_character()
    cursor_x = x
    cursor_y = y

def set_title(title):
    pygame.display.set_caption(title)

def set_cursor_type(i):
    global cursor_type
    cursor_map = {
        0: None,
        1: '_',
        2: chr(0xDB)
    }
    restore_character()
    cursor_type = cursor_map[i]


def cache_sprite(fg, bg, ch):
    bg_sprite = sprites['bg']
    fg_sprite = sprites[fg]
    index = ord(ch)

    #coordinates on the bg sprite map
    bg_x = bg * W

    #coordinates on the fg sprite map
    fg_x = (index % 16) * W
    fg_y = int(index / 16) * H

    cell_sprite = pygame.Surface((W, H))
    #voodoo: this helps a little bit.
    cell_sprite.set_alpha(None)

    #blit the background and foreground to the cell
    cell_sprite.blit(bg_sprite, dest=(0, 0), area=pygame.Rect(bg_x, 0, W, H))
    cell_sprite.blit(fg_sprite, dest=(0, 0), area=pygame.Rect(fg_x, fg_y, W, H))
    sprites[(fg, bg, ch)] = cell_sprite
    return cell_sprite

def blit_at(x, y, fg, bg, ch):
    #blit one character to the screen.
    #because function calls are pricey, this is also inlined (ew) in draw_buffer, so the contents are kept short.

    #coordinates on the screen
    screen_x = x * W
    screen_y = y * H

    #cache each (bg, fg, index) cell we draw into a surface so it's easier to redraw.
    #it's a little bit of a memory waste, and takes longer on the first draw, but we're dealing with ascii here
    #so there's probably a lot of reuse.
    try:
        cell_sprite = sprites[(fg, bg, ch)]
    except KeyError:
        #make a new one
        cell_sprite = cache_sprite(fg, bg, ch)
    
    #blit the cell to the screen
    screen.blit(cell_sprite, dest=(screen_x, screen_y))
    
    
        

   
def draw_buffer(source, start_x, start_y):
    """
        render the buffer to our backing.

        This is a hotpath, and there's more microoptimization here than i'd like, but FPS is kindof important.
    """

    y = start_y
    
    #lookups we can cache into locals
    #i know, it's such a microoptimization, but this path qualifies as hot
    local_cell_data, local_sprites, local_screen = cell_data, sprites, screen
    local_W, local_H = W, H
    screen_width, screen_height = max_x, max_y
    source_width = source.width

    for row in source._data:
        if y < 0:
            y += 1
            continue
        if y >= screen_height:
            break
        x = start_x

        #do something analogous to row[:source.width]
        #but without the pointless copy that requires
        w = 0
        for fg, bg, ch in row:
            if x >= screen_width or w >= source_width:
                break

            if x >= 0:
                #no need to blit if it's already identical
                old_data = local_cell_data[y][x]
                new_data = [fg, bg, ch]

                if new_data != old_data:
                    #draw it and remember the info for our cache
                    #this used to call blit_at but now it's inline.
                    try:
                        cell_sprite = sprites[(fg, bg, ch)]
                    except KeyError:
                        #make a new one
                        cell_sprite = cache_sprite(fg, bg, ch)
                    
                    #blit the cell to the screen
                    local_screen.blit(cell_sprite, dest=(x*local_W, y*local_H))

                    #remember the info for the cache
                    local_cell_data[y][x] = new_data
                
            x += 1
            w += 1
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
                        if item.type == USEREVENT:
                            blink_cursor(item)
                        elif item.type != KEYDOWN:
                            ignored_items.append(item)
                        else:
                            items.append(item)
                            break
                    
                    for ignored_item in ignored_items:
                        pygame.event.post(ignored_item)


            yield translate(items.pop(0))

    #assign the generator's next() method as raw_getkey
    raw_getkey = keypump().next


import rayled

from time import time,sleep
import pygame
import pygame.gfxdraw

LEDSIZE = 6
class sdldisplay:
    def __init__(self):
        screensize = (LEDSIZE * 120, LEDSIZE * 7)
        self.display = pygame.display.set_mode(screensize)
        self.buf = [0] * 100
        self.bptr = 0
        self.nticks = 0
        self.rbuf = []
        self.stime=None
    def write(self, msg):
        if len(msg) == 1 and msg == "\x80" or msg == 0x80:
            self.rbuf.append(msg)
            return
        if self.stime is None:
            self.stime = time()
        a = time()
        if self.buf:
            msg=self.rbuf+msg
            self.rbuf=[]
        self.update(msg)
        if 0x80 in list(msg) or "\x80" in msg:
            self.render()
            pygame.display.flip()
            self.doevents()
        #self.nticks += len(msg)
        #ledclock = self.nticks * 8 / 38400.0
        #while time() - self.stime < ledclock:
        #    pass
        dur = time() - a
        ledtime = (len(msg) * 9 + 1) / 38400.0
        if ledtime > dur:
            sleep(ledtime - dur)
        else:
            print "WAT?? slow ass shit",len(msg),ledtime,dur


    def render(self):
        r = LEDSIZE / 2
        for y in range(7):
            ypix = y * LEDSIZE + LEDSIZE/2
            mask = 1 << y
            for x in range(100):
                group = x // 5
                ingrp = x % 5
                xx = 6 * group + ingrp
                xpix = xx * LEDSIZE + LEDSIZE/2
                px = self.buf[x] & mask
                color = (255,0,0) if px else (0,0,0)
                pygame.gfxdraw.filled_circle(self.display, xpix, ypix, r, color)
    def update(self, msg):
        for c in msg:
            if isinstance(c, basestring):
                c = ord(c)
            if c == 0x80:
                self.bptr = 0
            else:
                if self.bptr < 100: # lol bugs somewhere
                    self.buf[self.bptr] = c
                self.bptr += 1
    def doevents(self):
        while self.doevent(pygame.event.poll()):
            pass
    def doevent(self, ev):
        global playin
        if ev.type == pygame.NOEVENT:
            return False
        if ev.type == pygame.QUIT:
            playin = False
            raise KeyboardInterrupt
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            playin = False
            raise KeyboardInterrupt
        return True

rayled.s = sdldisplay()
rayled.main()

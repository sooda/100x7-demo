# -*- encoding: utf8 -*-
import serial
from PIL import Image
from time import sleep
import numpy as np
import wave
import struct
import pyaudio
from sys import stdout
from random import randint
from Queue import Queue
import threading

im = Image.open("font.png")
pix = im.load()

s = None

# 5x7

# fromgfx(row0,row1,row2,..) rows same len
def fromgfx(*text):
    cols = len(text[0])
    data = [0] * cols
    for y, row in enumerate(text):
        mask = 1 << y
        for x, v in enumerate(row):
            if v != " ":
                data[x] |= mask
    return data

def toasciiart(screen):
    rows = []
    for y in range(7):
        mask = 1 << y
        row = []
        for x in screen:
            if x & mask:
                row.append("x")
            else:
                row.append(" ")
        rows.append("".join(row))
    return rows

CHARS = 20

def empty():
    return ["\x00"] * 5

def bar(i):
    return chr(1 << i) * 5

def emptys(n):
    return empty() * n

def readimg(pix,xstart,xlen=5):
    cols = []
    for x in range(xstart,xstart+xlen):
        thiscol = 0
        for y in range(7):
            black = pix[x,6-y][0] == 0
            thiscol <<= 1
            thiscol |= int(black)
        cols.append(thiscol)
    return cols

def fromimg(pathname):
    img = Image.open(pathname)
    pix = img.load()
    return readimg(pix, 0, img.size[0])

_fontcache = {}
_fontcache["\r"] = ["\x7f"] * 5
_fontcache[u"å"] = fromgfx(
        " xx  ",
        " xx  ",
        " xxx ",
        "x  x ",
        "x xx ",
        " x x "
        )
_fontcache[u"Å"] = fromgfx(
        " xx  ",
        " xx  ",
        "x  x ",
        "xxxx ",
        "x  x ",
        "x  x "
        )
def glyph(ch):
    gfx = _fontcache.get(ch)
    if gfx is None:
        gfx = readimg(pix,(ord(ch)-ord(' ')) * 5)
        _fontcache[ch] = gfx
    return gfx

def text(tx):
    r = []
    for t in tx:
        r.extend(glyph(t))
    return r


def displol(row):
    s.write(["\x80"] + row)


def waves():
    r = []
    for x in range(7):
        r.append(0x7f - ((1 << x) - 1))
    for x in range(7):
        r.append(0x7f - ((1 << (6 - x)) - 1))
    return r

def dispmsg(n):
    msg1 = "DOT  *  DEMOKERHO  *  ALT  *  SKROLLI  *  HACKLAB  *  "
    # msg longer than CHARS plz
    msg = msg1 * 2
    totgfx = text(msg)
    totgfx = 10 * waves() + totgfx

    pos = 0
    for x in range(n * (len(msg1)*5 - CHARS)):
        s.write("\x80")
        #s.write(emptys(CHARS))
        ms = totgfx[pos:pos+CHARS*5+1]
        s.write(ms)
        pos += 1
        pos %= len(msg1*5)
        #sleep(0.08)
    return ms

def dispupdown():
    i = 0
    j = 0

    while True:
        s.write("\x80")
        #s.write(emptys(CHARS))
        s.write(text("[\\]^_`a"))
        #s.write(bar(i) * CHARS)
        if j == 0:
            i += 1
            if i == 7:
                j = 1
        else:
            i -= 1
            if i == 0:
                j = 0

def dispslideover(prev, blk=0x7f):
    msg = prev
    for x in range(CHARS * 5):
        msg[x] = blk
        s.write("\x80")
        s.write(msg)
        #sleep(0.01)

def dispslideoverb(prev):
    msg = prev
    for y in range(7):
        for x in range(CHARS * 5):
            msg[x] |= 1 << y
        s.write("\x80")
        s.write(msg)
        sleep(0.1)

def dispslideover2(prev):
    msg = prev
    s.write("\x80")
    s.write(msg)
    s.write("\x80")
    for x in range(CHARS * 5):
        s.write("\x7f")
        sleep(0.01)

def barof(height):
    return 0x7f - ((0x80 >> height) - 1)




def audlol(qu,au):
    while True:
        item = qu.get()
        if len(item) == 0:
            break
        au.write(item)
        qu.task_done()

def fft():
    p = pyaudio.PyAudio()
    qu = Queue()
    w = wave.open("../audio/dv9.wav")
    #w = wave.open("../audio/dv9_b.wav")
    f=w
    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                channels = f.getnchannels(),  
                rate = f.getframerate(),  
                output = True)
    th = threading.Thread(target=audlol,args=(qu,stream))
    th.start()
    rate = w.getframerate()
    nfr = w.getnframes()
    fftsz = 2048
    #dur = rate * 10 # in samples, 10 secs
    dur=nfr
    data = w.readframes(dur)
    #stream.write(data)
    spos = 0
    try:
        while True:
            datai = data[2*spos:2*spos+2*fftsz]
            #stream.write(datai)
            qu.join()
            qu.put(datai)
            frames = struct.unpack("h" * fftsz, datai) # shorts, i guess

            ft = np.fft.rfft(frames)[1:]
            nbins = 5*20
            perbin = int(np.ceil(fftsz/2.0 / nbins))
            #print nbins,perbin
            bins = [0.0] * nbins
            L = np.log10
            lol = nbins / L(fftsz/2)
            for i, v in enumerate(ft):
                #bini = i // perbin
                bini = int(L(1 + i) * lol)
                bini = min(bini,nbins-1)
                #print i,bini
                bins[bini] += abs(v)
            m = max(bins)
            bins = [np.log10(x/m+1) for x in bins]
            #print bins
            msg = [barof(min(7, int(100*x))) for x in bins]
            s.write(["\x80"] + msg)
            #s.write(["\x80"] + map(barof, range(8)))

            spos += fftsz
            if spos + fftsz > nfr:
                break
    except KeyboardInterrupt:
        pass
    qu.put([])

def nanana():
    im = Image.open("batman.png")
    pix = im.load()
    for starty in range(150):
        if starty & 1:
            continue
        cols = [0] * 100
        for y in range(7):
            for x in range(0,100):
                xblk = x // 5
                blkpos = x % 5
                sample = pix[6 * xblk + blkpos,starty+y]
                if sample[0] == 0:
                    cols[x] += 1 << y
                    stdout.write("*")
                else:
                    stdout.write(" ")
            stdout.write("\n")
        s.write(["\x80"] + cols)
        stdout.write("\n")
        stdout.write("\n")
        sleep(0.08)

def batana(pix,pers=2,matban=0.07):
    #im = Image.open("batarang.png")
    #pix = im.load()
    shit=-1
    for shitfuk in range(100):
        for starty in range(0,8*7,7):
            shit += pers
            cols = [0] * 100
            for y in range(7):
                for x in range(0,100):
                    xblk = x // 5
                    blkpos = x % 5
                    sample = pix[max(0,-shit + 6 * xblk + blkpos),starty+y]
                    if sample[0] == 0:
                        cols[x] += 1 << y
                        stdout.write("*")
                    else:
                        stdout.write(" ")
                stdout.write("\n")
            s.write(["\x80"] + cols)
            stdout.write("\n")
            stdout.write("\n")
            sleep(matban)

def splitscreen(src):
    dst = [0] * 100
    for i, v in enumerate(src):
        blkid = i // 6
        blksub = i % 6
        if blksub < 5:
            dst[5 * blkid + blksub] = v
    return dst

def blit(dst,src,x,y):
    for i,v in enumerate(src):
        if y >= 0:
            dst[x+i] |= v << y
        else:
            dst[x+i] |= v >> -y

def slideover(scr, slider, interdelay):
    target = [0] * len(scr)
    sz = len(slider)
    empty = [0] * sz
    for i, n in enumerate(scr):
        target[i:i+sz] = empty
        blit(target, slider, i, 0)
        displol(target)
        target[i] = scr[i]
        sleep(interdelay)

def invader():
    invagfx = fromgfx(
            "   x   x   ",
            "  xxxxxxx  ",
            " xx xxx xx ",
            "xxxxxxxxxxx",
            "x xxxxxxx x",
            "  x     x  ",
            "   xx xx   "
            )
    bigshipgfx = fromgfx(
            "xx   ",
            " xx  ",
            "  xx ",
            "   xx",
            "  xx ",
            " xx  ",
            "xx   "
            )
    plus = [0x2, 0x7, 0x2]
    ship = [5, 2]
    block = [3, 3]
    ammo = [1]
    blkcount = 20
    blks = [[randint(20,200),randint(0,5)] for _ in range(blkcount)]
    blks.sort()
    ammoflying = 0
    ammox = ammoy = 0
    shipy = 0
    startup = True
    while True:
        for bl in blks:
            bl[0] -= 1
        if ammoflying:
            ammox += 3
            if ammox >= blks[0][0]:
                ammoflying = 0
                blks = blks[1:]
                if len(blks) == 0:
                    break
        if ammoflying == 0 and shipy+1 == blks[0][1]:
            ammox = 1
            ammoy = shipy + 1
            ammoflying = 1

        nextshoot = 1 if ammoflying and len(blks) > 1 else 0
        if shipy + 1 > blks[nextshoot][1]:
            shipy -= 1
        elif shipy + 1 < blks[nextshoot][1]:
            shipy += 1

        xriin = [0] * 120
        blit(xriin, ship, 0, shipy)
        if ammoflying:
            blit(xriin, ammo, ammox, ammoy)
        for b in blks:
            if b[0] < 119:
                blit(xriin,block,b[0],b[1])
        #displol((xriin))
        if startup:
            startup = False
            slideover(splitscreen(xriin), invagfx, 0.1)
        else:
            displol(splitscreen(xriin))
        sleep(0.05)
    slideover([0]*100, bigshipgfx, 0.07)

def golneighs(game, x, y):
    n = 0
    for yi in range(-1, 2):
        yii = (7 + (y + yi)) % 7
        mask = 1 << yii
        for xi in range(-1, 2):
            xii = (100 + (x + xi)) % 100
            if game[xii] & mask and not (xi == 0 and yi == 0):
                n += 1
    return n

def golnext(game):
    newgame = [0] * 100
    for x, v in enumerate(game):
        for y in range(7):
            mask = 1 << y
            neighs = golneighs(game, x, y)
            if v & mask:
                if neighs == 2 or neighs == 3:
                    newgame[x] |= mask
            else:
                if neighs == 3:
                    newgame[x] |= mask
    return newgame

def gol(iters):
    game = [0] * 100
    glider = fromgfx(
            " x ",
            "  x",
            "xxx"
            )
    lwss = fromgfx(
            "x  x ",
            "    x",
            "x   x",
            " xxxx"
            )
    beacon = fromgfx(
            "xx  ",
            "xx  ",
            "  xx",
            "  xx"
            )
    toad = fromgfx(
            " xxx",
            "xxx "
            )
    blit(game, glider, 0, 0)
    blit(game, glider, 5, 0)
    blit(game, lwss, 10, 0)
    blit(game, beacon, 10*5, 0)
    blit(game, beacon, 12*5, 0)
    blit(game, toad, 14*5, 2)
    game[1+18*5] = 0x70
    game[5+18*5] = 0x07
    #game[2+19*5] = 0x77
    for n in range(iters):
        displol(game)
        game = golnext(game)
        sleep(0.2)

def wavings():
    freq1 = 2.0 * 2 * np.pi / 120
    spikes = 1.0 * 2 * np.pi / 120
    tt = 1.1111
    tt2=0
    for time in range(1000):
        asd = []
        for x in range(120):
            s1 = np.sin((x + tt*time) * freq1)
            s2 = np.sin((x - tt*time) * freq1)
            s3 = np.sin((x - tt2*time) * spikes)
            color= (s1+s2)/2*s3
            color /= 2
            color += 0.5
            asd.append(0x7f & (1 << (int(7*color))))
        displol(splitscreen(asd))

def padtext(txt, sz=20):
    return txt + " " * (sz - len(txt))

def centertext(txt):
    spos = 10 - len(txt)/2
    return padtext(" "*spos + txt)

def center(gfx):
    spos = 50 - len(gfx)/2
    empty = [0] * spos
    if len(gfx) & 1:
        empty2 = empty[:-1]
    else:
        empty2 = empty
    return empty + gfx + empty2

def disptext(msg):
    displol(text(msg))

def textwait(msg, delay):
    disptext(padtext(msg))
    sleep(delay)

def textswait(msgs, delay, cycles):
    n = 0
    for i in range(cycles):
        textwait(msgs[n], delay)
        n = (n + 1) % len(msgs)

def textscrollin(msg, delay, interdelay):
    for i in range(len(msg)):
        textwait(msg[:i+1],  interdelay)
    sleep(delay)

def c64boot():
    textscrollin("Loading shaders 0/0", 3, 0.1)
    #textswait(["oh wait", ""], 1, 5)
    textwait("?ERR DIVIDE BY ZERO", 3)
    textswait(["READY.\r", "READY."], 0.5, 10)
    textswait(["RUN\r", "RUN"], 0.5, 10)

def surround(buf, style, pos):
    style2 = style + style
    # strip top and bottom 0x3e = 0111110
    buf = [b & 0x3e for b in buf]
    # top
    buf = [b |
            (1 if style[(pos+i) % len(style)] != " " else 0)
            for i,b in enumerate(buf)]
    # right
    corner = (pos+len(buf)-1) % len(style)
    rows = style2[corner:corner+7]
    rows = rows[:7]
    buf[-1] = fromgfx(*list(rows))[0]

    # bottom
    buf = [b |
            (0x40 if style[(pos+len(buf)+1+7+i*(len(style)-1)) % len(style)] != " " else 0)
            for i,b in enumerate(buf)]

    # left
    corner = ((len(style)-1)*pos+len(buf)+1+7-len(buf)) % len(style)
    rows = style2[corner:corner+7]
    rows = rows[:7]
    buf[0] = fromgfx(*list(rows))[0]
    return buf

def suchdisco():
    #font = fromimg("festival.png")
    fest = fromgfx(
"                                        ",
"xxxx xxxx  xxx xxxxx xxx x  x  xx  x    ",
"x    x    x      x    x  x  x      x    ",
"xxx  xxx   xx    x    x  x  x  xx  x    ",
"x    x       x   x    x  x x  x xx x    ",
"x    xxxx xxx    x   xxx  x   x  x xxx  "
)
    asm = fromgfx(
"                                                ",
" xx   xxx  xxx xxx  x x  xxx  x     xx  x       ",
"x  x x    x    x   xxxxx x  x x    x  x x       ",
"xxxx  xx   xx  xxx x x x xxx  x    x  x x       ",
"x  x    x    x x   x   x x  x x    x  x x       ",
"x  x xxx  xxx  xxx x   x xxx  xxxx  xx  xxxx    "
)

    fest = center(fest)
    asm = center(asm)
    for i in range(200):
        thisfont = fest if i & 16 else asm
        scr = thisfont if i & 8 else [0] * 100
        scr = surround(scr, "xxx   xxx   ", i)
        #scr = surround(scr, "xxxxxxx       ", i)
        displol(scr)
        sleep(0.07)


def main():
    global s
    s = serial.Serial("/dev/ttyUSB0", 38400)
    s.write("\x80")
    s.write(emptys(CHARS))

    c64boot()
    dispslideover([0] * 100)
    dispslideover([0x7f] * 100, 0)

    #suchdisco()
    cubeanim = Image.open("cubeanim.png").load()
    #batana(cubeanim,1,0.07)

    bata = Image.open("batarang.png").load()
    #batana(bata, 2, 0.07)

    #invader()
    #1/0

    #nanana()
    #batana()
    #wavings()

    #gol(9999)

    #c64boot()
    #fft()


    return

    while True:
        m = dispmsg(2)
        dispslideover2(m)
        m = dispmsg(2)
        dispslideoverb(m)

if __name__ == "__main__":
    main()


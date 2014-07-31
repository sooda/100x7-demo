import serial
from PIL import Image
from time import sleep
import numpy as np
import wave
import struct
import pyaudio
from sys import stdout
from random import randint

im = Image.open("font.png")
pix = im.load()

def readimg(xstart):
    cols = []
    for x in range(xstart,xstart+5):
        thiscol = 0
        for y in range(7):
            black = pix[x,6-y][0] == 0
            thiscol <<= 1
            thiscol |= int(black)
        cols.append(thiscol)
    return cols

_fontcache = {}
def glyph(ch):
    gfx = _fontcache.get(ch)
    if gfx is None:
        gfx = readimg((ord(ch)-ord(' ')) * 5)
        _fontcache[ch] = gfx
    return gfx

def text(tx):
    r = []
    for t in tx:
        r.extend(glyph(t))
    return r
# 5x7

CHARS = 20

def empty():
    return ["\x00"] * 5

def bar(i):
    return chr(1 << i) * 5

def emptys(n):
    return empty() * n

s = serial.Serial("/dev/ttyUSB0", 38400)

s.write("\x80")
s.write(emptys(CHARS))

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

def dispslideover(prev):
    msg = prev
    for x in range(CHARS * 5):
        s.write("\x80")
        s.write(msg)
        msg[x] = 0x7f
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



from Queue import Queue
import threading

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

def batana():
    im = Image.open("batarang.png")
    pix = im.load()
    shit=-1
    for shitfuk in range(100):
        for starty in range(0,8*7,7):
            shit += 2
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
            sleep(0.07)

#fft()

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

def invader():
    plus = [0x2, 0x7, 0x2]
    ship = [5, 2]
    block = [3, 3]
    ammo = [1]
    blks = [[randint(5,95),randint(0,5)] for _ in range(10)]
    blks.sort()
    ammoflying = 0
    ammox = ammoy = 0
    shipy = 0
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

        xriin = [0] * 100
        blit(xriin, ship, 0, shipy)
        if ammoflying:
            blit(xriin, ammo, ammox, ammoy)
        for b in blks:
            blit(xriin,block,b[0],b[1])
        #displol((xriin))
        displol(splitscreen(xriin))
        sleep(0.05)

invader()

#nanana()
#batana()

1/0

while True:
    m = dispmsg(2)
    dispslideover2(m)
    m = dispmsg(2)
    dispslideoverb(m)


100x7 by perskarhunen bros.
===========================

* a real wild for assembly 2014 demoparty, ranked 1st
* code and some gfx by sooda, audio and some other gfx by Pete_K
* video capture in youtube_
* the display is recycled from somewhere; it'd be trivial to build one with shift registers and a microcontroller (this uses just them, has AT90S8515)
* serial protocol is 38400 baud 8N1, 0x80 for a cursor reset and then some bytes for the columns, topmost is least significant bit
* created mostly from scratch in ~15 hours incl. sleep and stuff, just before the compo deadline and recorded at the party
* original party version is at git tag ``party``
* the led matrix has 20 pieces of 5 by 7 pixel modules with a spacing of about one pixel between the modules; the demo takes the spaces into account in some scenes, should have fixed some scrollers for that...
* the demo is "synced" to the audio by relying on low level timings of the serial device and then some sleep() somewhere, not expected to be in sync with any other usb-serial-adapters than the cheapo model i happened to use
* ``demo-real.py`` is here the actual demo that uses the serial port
* ``demo-simulator.py`` tries to look kind of the led matrix with pygame rendering; timings are a bit off so the audio is not quite in sync especially in the end
* use python 2
* the music outputs with pyaudio and the hw is controlled obviously with pyserial
* the music thread is not interested in quitting, so plain ctrl+c is not enough
* tested only on linux

.. _youtube: http://www.youtube.com/watch?v=iQPL_22qzdo

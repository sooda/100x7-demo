import rayled
import sys

gfx = rayled.fromimg(sys.argv[1])
print "\n".join(rayled.toasciiart(gfx))

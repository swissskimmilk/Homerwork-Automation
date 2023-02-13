from PIL import Image 
import numpy

input = Image.open("Output/gcodeTestOutput.png")

pixel = input.load()

width, height = input.size

searched = numpy.zeros((width, height))

def createLine(x, y, pixel, width, height):


for x in range(width):
    for y in range(height):
        if pixel[x, y] == 255 and searched[y][x] == 0:
            createLine(x, y, pixel, width, height)

from ImageProcessor import *
import numpy
import PIL
import sys 

sys.setrecursionlimit(5000)

MINIMUM_VALUE = 40

imageProcessor = ImageProcessor("Images/MJ_Bird.png")
imageProcessor.greyscale()
imageProcessor.gaussianBlur()
imageProcessor.lapAdj()
pixel = imageProcessor.image.load()

width, height = imageProcessor.image.size

searched = numpy.zeros((width, height))


def isZeros(matrix):
    for row in matrix:
        for item in row:
            if item == 1:
                return False
    return True


# need a shitty temporary fix for skipping the starting pixel the first time
# this is probably causing a big chunk of the problems but idfk
# main thing is gaps in pixels, i assume it's this and some other issue causing it
def adjSearch(x, y, pixel, width, height):

    adjMatrix = numpy.zeros((3, 3))
    if (
        x > 0
        and y > 0
        and pixel[x - 1, y - 1] >= MINIMUM_VALUE
        and searched[y - 1][x - 1] == 0
    ):
        adjMatrix[0][0] = 1
    if y > 0 and pixel[x, y - 1] >= MINIMUM_VALUE and searched[y - 1][x] == 0:
        adjMatrix[0][1] = 1
    if (
        x < width - 1
        and y > 0
        and pixel[x + 1, y - 1] >= MINIMUM_VALUE
        and searched[y - 1][x + 1] == 0
    ):
        adjMatrix[0][2] = 1
    if x > 0 and pixel[x - 1, y] >= MINIMUM_VALUE and searched[y][x - 1] == 0:
        adjMatrix[1][0] = 1
    if x < width - 1 and pixel[x + 1, y] > MINIMUM_VALUE and searched[y][x + 1] == 0:
        adjMatrix[1][2] = 1
    if (
        x > 0
        and y < height - 1
        and pixel[x - 1, y + 1] >= MINIMUM_VALUE
        and searched[y + 1][x - 1] == 0
    ):
        adjMatrix[2][0] = 1
    if y < height - 1 and pixel[x, y + 1] >= MINIMUM_VALUE and searched[y + 1][x] == 0:
        adjMatrix[2][1] = 1
    if (
        x < width - 1
        and y < height - 1
        and pixel[x + 1, y + 1] >= MINIMUM_VALUE
        and searched[y + 1][x + 1] == 0
    ):
        adjMatrix[2][2] = 1

    for tempX in range(x - 1, x + 2):
        for tempY in range(y - 1, y + 2):
            if tempY >= 0 and tempY < height and tempX >= 0 and tempX < width:
                searched[tempY][tempX] = 1

    if isZeros(adjMatrix):
        return [(x, y)]

    returnMatrix = []
    for tempX in range(0, 3):
        for tempY in range(0, 3):
            newX = x + tempX - 1
            newY = y + tempY - 1
            if (
                adjMatrix[tempY][tempX] == 1
                and newY >= 0
                and newY < height
                and newX >= 0
                and newX < width
            ):
                returnMatrix.extend(adjSearch(newX, newY, pixel, width, height))
    return returnMatrix


outputPixelLocations = []

for x in range(width):
    for y in range(height):
        value = pixel[x, y]
        if value >= MINIMUM_VALUE and searched[y][x] == 0:
            outputPixelLocations.extend(adjSearch(x, y, pixel, width, height))

outputImageArr = [[(0, 0, 0) for x in range(width)] for y in range(height)]
for location in outputPixelLocations:
    outputImageArr[location[1]][location[0]] = (255, 255, 255)

outputImageArr = numpy.array(outputImageArr, dtype=numpy.uint8)

print(outputImageArr)

outputImage = Image.fromarray(outputImageArr)
greyscaleOuput = outputImage.convert("L")
greyscaleOuput.save("Output/gcodeTestOutput.png")

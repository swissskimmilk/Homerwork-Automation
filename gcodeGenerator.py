from ImageProcessor import * 
import numpy


imageProcessor = ImageProcessor("Images/MJ_Bird.png")
imageProcessor.greyscale()
imageProcessor.gaussianBlur()
imageProcessor.lapAdj()
pixel = imageProcessor.image.load()

width, height = imageProcessor.image.size

searched  = numpy.zeros((width, height))

def adjSearch(x, y, pixel):

    adjMatrix = numpy.zeros((3, 3))
    if pixel[x-1, y-1] != 0 and searched[x-1][y-1] == 0: 
        adjMatrix[0][0] = 1
    if pixel[x, y-1] != 0 and searched[x][y-1] == 0:
        adjMatrix[0][1] = 1
    if pixel[x+1, y-1] != 0 and searched[x+1][y-1] == 0:
        adjMatrix[0][2] = 1
    if pixel[x-1, y] != 0 and searched[x-1][y] == 0:
        adjMatrix[1][0] = 1
    if pixel[x+1, y] != 0 and searched[x+1][y] == 0:
        adjMatrix[1][2] = 1
    if pixel[x-1, y+1] != 0 and searched [x-1][y+1] == 0:
        adjMatrix[2][0] = 1
    if pixel[x, y+1] != 0 and searched [x][y+1] == 0:
        adjMatrix[2][1] = 1
    if pixel[x+1, y+1] != 0 and searched [x+1][y+1] == 0:
        adjMatrix[2][2] = 1
    
    for tempX in range(x-1, x+2):
        for tempY in range(y-1, y+2):
            searched[tempX][tempY] = 1

    # stupid fucking code kill me 
    for row in adjMatrix:
        for item in row:
            if item != 0:
                break
        return (x, y)
    
    returnMatrix = []
    for tempX in range(0, 3): 
        for tempY in range(0, 3): 
            if adjMatrix[x][y] == 1:
                returnMatrix.append(adjSearch(x + tempX - 1, y + tempY - 1, pixel))
    return returnMatrix

for x in range(width):
    for y in range (height):
        value = pixel[x, y]
        if value != 1 and searched[x][y] == 0: 
            print(adjSearch(x, y, pixel))

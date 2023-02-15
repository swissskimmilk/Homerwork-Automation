from PIL import Image, ImageFilter
import sys

# :trollface:
sys.setrecursionlimit(9999)

# Kernels
gaussianK = (1 / 16, 2 / 16, 1 / 16, 2 / 16, 4 / 16, 2 / 16, 1 / 16, 2 / 16, 1 / 16)
lapAdjK = (0, 1, 0, 1, -4, 1, 0, 1, 0)
lapAllK = (-1, -1, -1, -1, 8, -1, -1, -1, -1)

RETRACT_HEIGHT = 15
OPERATING_HEIGHT = 5
FEEDRATE = 1000


class ImageProcessor:
    def __init__(self, imageIn):
        self.image = Image.open(imageIn)

    # Converts to greyscale
    def greyscale(self):
        self.image = self.image.convert("L")

    # Blurs image
    def gaussianBlur(self):
        self.image = self.image.filter(ImageFilter.Kernel((3, 3), gaussianK, 1, 0))

    # Edgefinding using only four adjacent pixels
    def lapAdj(self):
        self.image = self.image.filter(ImageFilter.Kernel((3, 3), lapAdjK, 0.25, 0))

    # Edgefinding using eight surrounding pixels
    def lapAll(self):
        self.image = self.image.filter(ImageFilter.Kernel((3, 3), lapAllK, 1, 0))

    # Reduces the color in the image by rounding the color values based on steps
    def roundColors(self, steps):
        stepMult = 255 // steps
        img = self.image.load()
        width = self.image.width
        height = self.image.height

        for x in range(width):
            for y in range(height):
                pixel = img[x, y]
                # Type will be an integer if in greyscale
                # Rounds each pixel value
                if type(pixel) == int:
                    pixel = round(pixel / stepMult) * stepMult
                    img[x, y] = pixel
                else:
                    pixel = [round(i / stepMult) * stepMult for i in pixel]
                    img[x, y] = tuple(pixel)

    # Deletes pixels that are not touching other pixels
    # Image must be in greyscale (I think)
    def delPix(self):
        img = self.image.load()
        width = self.image.width
        height = self.image.height

        # Checks to see if the adjacent pixels
        for x in range(width):
            for y in range(height):
                tog = True
                if img[x, y] != 0:
                    if tog and x > 0 and y > 0 and img[x - 1, y - 1] != 0:
                        tog = False
                    if tog and y > 0 and img[x, y - 1] != 0:
                        tog = False
                    if tog and x < width - 1 and y > 0 and img[x + 1, y - 1] != 0:
                        tog = False
                    if tog and x > 0 and img[x - 1, y] != 0:
                        tog = False
                    if tog and x < width - 1 and img[x + 1, y] != 0:
                        tog = False
                    if tog and x > 0 and y < height - 1 and img[x - 1, y + 1] != 0:
                        tog = False
                    if tog and y < height - 1 and img[x, y + 1] != 0:
                        tog = False
                    if (
                        tog
                        and x < width - 1
                        and y < height - 1
                        and img[x + 1, y + 1] != 0
                    ):
                        tog = False
                    if tog:
                        img[x, y] = 0

    def toGCode(self):
        img = self.image.copy().load()
        width = self.image.width
        height = self.image.height
        turtleOutput = open("Output/turtle.txt", "w")
        gcodeOutput = open("Output/drawing.gcode", "w")

        # Magically finds lines and returns as a list of tuples
        # Todo: remove tog?
        def lineSearch(x, y, biasX, biasY):
            tog = False
            if img[x, y] != 0:
                tog = True
            # BL,BM,BR,ML,MM,MR,TL,TM,TR
            maxInd = -1
            maxPref = 0

            if x > 0 and y > 0 and img[x - 1, y - 1] != 0:
                a = abs(-1 + biasX) + abs(-1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 0
                tog = False
            if y > 0 and img[x, y - 1] != 0:
                a = abs(biasX) + abs(-1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 1
                tog = False
            if x < width - 1 and y > 0 and img[x + 1, y - 1] != 0:
                a = abs(1 + biasX) + abs(-1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 2
                tog = False
            if x > 0 and img[x - 1, y] != 0:
                a = abs(-1 + biasX) + abs(biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 3
                tog = False
            if x < width - 1 and img[x + 1, y] != 0:
                a = abs(1 + biasX) + abs(biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 5
                tog = False
            if x > 0 and y < height - 1 and img[x - 1, y + 1] != 0:
                a = abs(-1 + biasX) + abs(1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 6
                tog = False
            if y < height - 1 and img[x, y + 1] != 0:
                a = abs(biasX) + abs(1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 7
                tog = False
            if x < width - 1 and y < height - 1 and img[x + 1, y + 1] != 0:
                a = abs(1 + biasX) + abs(1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 8
                tog = False

            if maxInd == -1:
                # This probabally works
                return None
            newX = x + maxInd % 3 - 1
            newY = y + maxInd // 3 - 1
            img[newX, newY] = 0

            recur = lineSearch(newX, newY, maxInd % 3 - 1, maxInd // 3 - 1)
            if recur != None:
                currArr = [(newX, newY)]
                currArr.extend(recur)
                return currArr
            else:
                return [(newX, newY)]

        gcodeOutput.write("G28\n")
        gcodeOutput.write(f"G1 F{FEEDRATE}\n")
        for x in range(width):
            for y in range(height):
                if img[x, y] != 0:
                    linePixels = lineSearch(x, y, 0, 0)
                    turtleOutput.write(f"{x},{y}\n")
                    gcodeOutput.write(f"G1 X{x} Y{y} Z{RETRACT_HEIGHT}\n")
                    gcodeOutput.write(f"G1 Z{OPERATING_HEIGHT}\n")
                    if linePixels != None:
                        for pixel in linePixels:
                            turtleOutput.write(f"{pixel[0]},{pixel[1]}\n")
                            gcodeOutput.write(f"G1 X{pixel[0]} Y{pixel[1]}\n")
                    turtleOutput.write("stop\n")
                    gcodeOutput.write(f"G1 Z{RETRACT_HEIGHT}\n")
        turtleOutput.write("end\n")
        gcodeOutput.write("G1 X0 Y0\n")

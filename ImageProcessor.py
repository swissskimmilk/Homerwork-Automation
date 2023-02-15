from PIL import Image, ImageFilter
import sys

sys.setrecursionlimit(9999)

# Image inputs
astro = "DALLE_Astronaut.jpg"


# Kernels
gaussianK = (1 / 16, 2 / 16, 1 / 16, 2 / 16, 4 / 16, 2 / 16, 1 / 16, 2 / 16, 1 / 16)
lapAdjK = (0, 1, 0, 1, -4, 1, 0, 1, 0)
lapAllK = (-1, -1, -1, -1, 8, -1, -1, -1, -1)

aidanGoesToSleep = []


class ImageProcessor:
    def __init__(self, imageIn):
        self.image = Image.open(imageIn)

    def greyscale(self):
        self.image = self.image.convert("L")

    def gaussianBlur(self):
        self.image = self.image.filter(ImageFilter.Kernel((3, 3), gaussianK, 1, 0))

    def lapAdj(self):
        self.image = self.image.filter(ImageFilter.Kernel((3, 3), lapAdjK, 0.25, 0))

    def lapAll(self):
        self.image = self.image.filter(ImageFilter.Kernel((3, 3), lapAllK, 1, 0))

    def round(self, steps):
        stepMult = 255 // steps
        img = self.image.load()
        w = self.image.width
        h = self.image.height

        for x in range(w):
            for y in range(h):
                a = img[x, y]
                # print(a)
                if type(a) == int:
                    a = round(a / stepMult) * stepMult
                    img[x, y] = a
                else:
                    a = [round(i / stepMult) * stepMult for i in a]
                    img[x, y] = tuple(a)
                # print(a)
        print(type(img))
        print(type(self.image))

    def delPix(self):
        img = self.image.load()
        width = self.image.width
        height = self.image.height

        for x in range(width):
            for y in range(height):
                tog = False
                if img[x, y] != 0:
                    tog = True

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
                if tog and x < width - 1 and y < height - 1 and img[x + 1, y + 1] != 0:
                    tog = False
                if tog:
                    img[x, y] = 0

    def toGCode(self):
        img = self.image.load()
        width = self.image.width
        height = self.image.height
        output = open("Output/codering.txt", "w")

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
                aidanGoesToSleep.append((-1, -1))
                return "stop\n"
            newX = x + maxInd % 3 - 1
            newY = y + maxInd // 3 - 1
            img[newX, newY] = 0
            # print()
            # print(maxInd)
            # print(x, y)
            # print(newX, newY)
            aidanGoesToSleep.append((newX, newY))
            return f"g1 x{newX} y{newY}\n" + lineSearch(
                newX, newY, maxInd % 3 - 1, maxInd // 3 - 1
            )

        for x in range(width):
            for y in range(height):
                if img[x, y] == 255:
                    output.write(f"g1 x{x} y{y}\n" + lineSearch(x, y, 0, 0))
                    aidanGoesToSleep.append((x, y))
        output.write("end")
        print(aidanGoesToSleep)

# where most of the work is done

from PIL import Image, ImageFilter
import sys
import math

# :trollface:
sys.setrecursionlimit(9999)

# Kernels
gaussianK = (1 / 16, 2 / 16, 1 / 16, 2 / 16, 4 / 16, 2 / 16, 1 / 16, 2 / 16, 1 / 16)
lapAdjK = (0, 1, 0, 1, -4, 1, 0, 1, 0)
lapAllK = (-1, -1, -1, -1, 8, -1, -1, -1, -1)

maxGapSize = 3

RETRACT_HEIGHT = 0.5
OPERATING_HEIGHT = 0
# retract extra high up at the end in order to avoid hitting the clips while homing
AVOID_CLIP_HEIGHT = 10
FEEDRATE = 12000

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
    # like roundColors, but more balanced;
    # trys to make sure every sub-range of colors have similar pixel count
    def balancedRoundColors(self, numberOfSubranges):
        img = self.image.load()
        width = self.image.width
        height = self.image.height

        # first tally how many times a color shows up; its index is its color value
        colorCount = [0] * 256 
        for x in range(width):
            for y in range(height):
                pixel = img[x, y]
                colorCount[pixel] += 1

        # number of subranges is the number of colors there can be;
        # more subranges = less rounding/more colors, & vice-versa
        # this is for dividing into subranges; subrangeEnd is the limit and subrangeEnd-1 is the last term
        subrangeEnds = []
        # (totalPixels)/numberOfSubranges, rounded up
        pixelsInEachSubRange = math.ceil( (width * height) / numberOfSubranges )
        thisSubrangeSize = 0
        residue = 0
        # tries to divide the range of colors/colorCount into many subranges with similar numbers of pixels
        for thisIndex in range(len(colorCount)):
            numberOfThisColor = colorCount[thisIndex]

            # once this subrange *is about to be* filled up...
            if ( (thisSubrangeSize+numberOfThisColor) >= pixelsInEachSubRange):
                # see if it is better to under-include or over-include;
                # residue says if last subrange under-induded or over-included;
                # if last subrange under-included, then this one probably should over-include and vice-versa

                # includeResidue is how off it will be if we decide to include the last number
                includeResidue = thisSubrangeSize+numberOfThisColor+residue-pixelsInEachSubRange
                # excludeResidue is how off it will be if we decide to NOT include the last number
                excludeResidue = thisSubrangeSize-numberOfThisColor+residue-pixelsInEachSubRange
                if( abs(excludeResidue) <= abs(includeResidue) ):
                    # not including is better than including; but this will result in under-including
                    # roll over residue for next calculation
                    residue = excludeResidue
                    # note the end of the last subrange...
                    subrangeEnds.append(thisIndex)
                else:
                    # including is better than not including; but this will result in over-including
                    # roll over residue for next calculation
                    residue = includeResidue
                    # note the end of the last subrange...
                    subrangeEnds.append(thisIndex+1)
                # then start a new subrange
                thisSubrangeSize = 0
            else:
                # otherwise, keep filling
                thisSubrangeSize += numberOfThisColor
        # add a final end (if it isn't there already) and a beginning
        if (len(subrangeEnds) != numberOfSubranges):
            subrangeEnds.append(256)
        subrangeEnds.insert(0, 0)

        #print("Subrange ends: ", subrangeEnds)

        # take a weighted average of each subrange
        # this is used for averaging the colors in each subrange
        subrangeAverages = []
        for i in range(1, len(subrangeEnds)):
            thisSubrangeColorSum = 0
            thisSubrangePixelCount = 0
            for j in range(subrangeEnds[i-1], subrangeEnds[i]):
                thisSubrangeColorSum += colorCount[j] * j
                thisSubrangePixelCount += colorCount[j]
            if (thisSubrangePixelCount==0):
                subrangeAverages.append(0)
            else:
                subrangeAverages.append( math.ceil(thisSubrangeColorSum/thisSubrangePixelCount) )
            # print(thisSubrangePixelCount)
            
        #print("Subrange averages: ", subrangeAverages)

        # now we map each color to its subrange average
        subrangeTable = []
        for i in range(1, len(subrangeEnds)):
            for j in range(subrangeEnds[i-1], subrangeEnds[i]):
                subrangeTable.append(subrangeAverages[i-1])
        
        #print("Subrange table: ", subrangeTable)
        #print(len(subrangeTable))

        #max = 0
        #min = 300
        # set each pixel in the subranges to the average of its subrange
        for x in range(width):
            for y in range(height):
                pixel = img[x, y]

                #if(pixel>max):
                #    max=pixel
                #if(pixel<min):
                #    min=pixel

                img[x, y] = subrangeTable[pixel]
        #print("max: ", max)
        #print("min: ", min)

    # Deletes pixels that are not touching other pixels
    # Image must be in black and white
    def delPix(self):
        img = self.image.load()
        width = self.image.width
        height = self.image.height

        # loops through all pixels...
        for x in range(width):
            for y in range(height):

                isLonePixel = True

                # if there is a pixel there...
                if img[x, y] != 0:
                    # check all nearby spots to see if there are any touching pixels
                    if isLonePixel and x > 0 and y > 0 and img[x - 1, y - 1] != 0:
                        isLonePixel = False
                    if isLonePixel and y > 0 and img[x, y - 1] != 0:
                        isLonePixel = False
                    if isLonePixel and x < width - 1 and y > 0 and img[x + 1, y - 1] != 0:
                        isLonePixel = False
                    if isLonePixel and x > 0 and img[x - 1, y] != 0:
                        isLonePixel = False
                    if isLonePixel and x < width - 1 and img[x + 1, y] != 0:
                        isLonePixel = False
                    if isLonePixel and x > 0 and y < height - 1 and img[x - 1, y + 1] != 0:
                        isLonePixel = False
                    if isLonePixel and y < height - 1 and img[x, y + 1] != 0:
                        isLonePixel = False
                    if (
                        isLonePixel
                        and x < width - 1
                        and y < height - 1
                        and img[x + 1, y + 1] != 0
                    ):
                        isLonePixel = False

                    # if pixel is not touching any other, delete pixel
                    if isLonePixel:
                        img[x, y] = 0

    def toGCode(self, minChainLength, xOffset, yOffset, paperWidth, paperHeight):
        img = self.image.copy().load()
        width = self.image.width
        height = self.image.height

        # Magically finds lines and returns as a list of tuples
        def lineSearch(x, y, biasX, biasY):

            # BL,BM,BR,ML,MM,MR,TL,TM,TR
            maxInd = -1
            maxPref = 0

            if x > 0 and y > 0 and img[x - 1, y - 1] != 0:
                a = abs(-1 + biasX) + abs(-1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 0
            if y > 0 and img[x, y - 1] != 0:
                a = abs(biasX) + abs(-1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 1
            if x < width - 1 and y > 0 and img[x + 1, y - 1] != 0:
                a = abs(1 + biasX) + abs(-1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 2
            if x > 0 and img[x - 1, y] != 0:
                a = abs(-1 + biasX) + abs(biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 3
            if x < width - 1 and img[x + 1, y] != 0:
                a = abs(1 + biasX) + abs(biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 5
            if x > 0 and y < height - 1 and img[x - 1, y + 1] != 0:
                a = abs(-1 + biasX) + abs(1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 6
            if y < height - 1 and img[x, y + 1] != 0:
                a = abs(biasX) + abs(1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 7
            if x < width - 1 and y < height - 1 and img[x + 1, y + 1] != 0:
                a = abs(1 + biasX) + abs(1 + biasY)
                if a > maxPref:
                    maxPref = a
                    maxInd = 8

            if maxInd == -1:
                # This probabaly works
                return None
            newX = x + maxInd % 3 - 1
            newY = y + maxInd // 3 - 1
            img[newX, newY] = 0

            recur = lineSearch(
                newX,
                newY,
                (biasX) * 1 + (maxInd % 3 - 1) * 1,
                (biasY) * 1 + (maxInd // 3 - 1) * 1,
            )
            if recur != None:
                currArr = [(newX, newY)]
                currArr.extend(recur)
                return currArr
            else:
                return [(newX, newY)]

        turtleOutput = open("Output/turtle.txt", "w")
        gcodeOutput = open("Output/drawing.gcode", "w")
        
        gcodeOutput.write("G28\n")
        gcodeOutput.write(f"G1 F{FEEDRATE}\n")
        gcodeOutput.write(f"G1 Z{RETRACT_HEIGHT}\n")
        for x in range(width):
            for y in range(height):
                if img[x, y] != 0:
                    linePixels = lineSearch(x, y, 0, 0)
                    if linePixels == None or (minChainLength != 1 and len(linePixels) <= minChainLength):
                        continue
                    turtleOutput.write(f"{x},{y}\n")
                    if width > height:
                        gcodeOutput.write(
                            f"G1 X{x/width * paperWidth + xOffset} Y{paperHeight - y/width * paperHeight + yOffset}\n"
                        )
                    else: 
                        gcodeOutput.write(
                            f"G1 X{x/height * paperWidth + xOffset} Y{paperHeight - y/height * paperHeight + yOffset}\n"
                        )

                    gcodeOutput.write(f"G1 Z{OPERATING_HEIGHT}\n")
                    arrLen = len(linePixels)
                    for i in range(arrLen):
                        if False or i % 3 == 0:
                            turtleOutput.write(
                                f"{linePixels[i][0]},{linePixels[i][1]}\n"
                            )
                            if width > height: 
                                gcodeOutput.write(
                                    f"G1 X{linePixels[i][0]/width * paperWidth + xOffset} Y{paperHeight - linePixels[i][1]/width * paperHeight + yOffset}\n"
                                )
                            else:
                                gcodeOutput.write(
                                    f"G1 X{linePixels[i][0]/height * paperWidth + xOffset} Y{paperHeight - linePixels[i][1]/height * paperHeight + yOffset}\n"
                                )

                                
                    turtleOutput.write("stop\n")
                    gcodeOutput.write(f"G1 Z{RETRACT_HEIGHT}\n")
        turtleOutput.write("end\n")
        gcodeOutput.write("G1 Z5\nG28\n")

        turtleOutput.close()
        gcodeOutput.close()


    # note: dont remove gcodePurge, it now has extra functionality
    # preconditions:
    #    first five gcode commands are: homing, feedrate, first raising, going to first point coordinate, Z{OPERATING_HEIGHT} respectively
    #    last two gcode commands are: Z{RETRACT_HEIGHT}, extra raising, homing, repectively
    def gcodePurge(self):

        def smallGapPurge():
            gcodeRead = open("Output/drawing.gcode", "r")
            allGcodeCommands = gcodeRead.readlines()

            # indicies are integers, points are [x, y], [x, y], [x, y], ...
            raisingIndicies = []
            loweringIndicies = []
            raisingPoints = []
            loweringPoints = []

            # go through the valid commands and search for pairs of raisings and lowerings (gaps); ignore first gap and last gap
            for index in range(5, len(allGcodeCommands)-3 ):
                previousGcodeCommand = allGcodeCommands[index-1]
                previousGcodeCommandset = (previousGcodeCommand.strip("\n")).split(" ")
                thisGcodeCommand = allGcodeCommands[index]
                thisGcodeCommandset = (thisGcodeCommand.strip("\n")).split(" ")

                if( thisGcodeCommandset[-1]=="Z"+str(RETRACT_HEIGHT) ):
                    raisingIndicies.append(index)
                    raisingPoints.append([float(previousGcodeCommandset[1].strip("X")), float(previousGcodeCommandset[2].strip("Y"))])
                elif( thisGcodeCommandset[-1]=="Z"+str(OPERATING_HEIGHT) ):
                    loweringIndicies.append(index)
                    loweringPoints.append([float(previousGcodeCommandset[1].strip("X")), float(previousGcodeCommandset[2].strip("Y"))])
            
            # find the size of each gap, delete gap (let the pen write over it) if gap is too small
            for index in range(len(raisingIndicies)):
                gapSize = math.dist(raisingPoints[index], loweringPoints[index])
                if(gapSize<maxGapSize):
                    # set the lift and lower commands to "TODELETE" now and delete later
                    allGcodeCommands[raisingIndicies[index]] = "TODELETE"
                    allGcodeCommands[loweringIndicies[index]] = "TODELETE"
            for index in range(len(allGcodeCommands)-1, -1, -1):
                if(allGcodeCommands[index] == "TODELETE"):
                    del(allGcodeCommands[index])
                    
            gcodeRead.close()
            
            # wipe and write
            gcodeWrite = open("Output/drawing.gcode", "w")
            for command in allGcodeCommands:
                gcodeWrite.write(command)
            gcodeWrite.close()

        smallGapPurge()

        def smallSegmentPurge():
            gcodeRead = open("Output/drawing.gcode", "r")
            allGcodeCommands = gcodeRead.readlines()

            # indicies are integers, points are [x, y], [x, y], [x, y], ...
            loweringIndicies = []
            raisingIndicies = []

            # go through the valid commands and search for pairs of lowerings and raisings (segments)
            for index in range(4, len(allGcodeCommands)-2 ):
                thisGcodeCommand = allGcodeCommands[index]
                thisGcodeCommandset = (thisGcodeCommand.strip("\n")).split(" ")

                if( thisGcodeCommandset[-1]=="Z"+str(OPERATING_HEIGHT) ):
                    loweringIndicies.append(index)
                elif( thisGcodeCommandset[-1]=="Z"+str(RETRACT_HEIGHT) ):
                    raisingIndicies.append(index)
            
            # find the size of each segment, delete segment (let the pen skip it by connecting the two gaps around it) if segment is too small
            for index in range(len(raisingIndicies)):
                segmentSize = (raisingIndicies[index]-loweringIndicies[index]) - 1
                if(segmentSize<maxGapSize):
                    # set the segment and first gap commands to "TODELETE" now and delete later
                    for i in range(loweringIndicies[index]-1, raisingIndicies[index]+1):
                        allGcodeCommands[i] = "TODELETE"
            for index in range(len(allGcodeCommands)-1, -1, -1):
                if(allGcodeCommands[index] == "TODELETE"):
                    del(allGcodeCommands[index])
            
            gcodeRead.close()

            # wipe and write
            gcodeWrite = open("Output/drawing.gcode", "w")
            for command in allGcodeCommands:
                gcodeWrite.write(command)
            gcodeWrite.close()

        # smallSegmentPurge()

    
    # joins smaller lines into larger lines
    def lineJoiner(self):
        # note: ONLY WORKS WITH GCODE FOR NOW
        gcodeRead = open("Output/drawing.gcode", "r")
        allGcodeCommands = gcodeRead.readlines()

        def isXYPoint(commandToCheck):
            # a command is an XY point if it is [G1, X, Y];
            # in other words, if its split-up set is len 3
            commandToCheckSet = (commandToCheck.strip("\n")).split(" ")
            return (len(commandToCheckSet)==3)
        def isCheckablePoint(allGcodeCommands, indexToCheck):
            # a point is checkable if it, along with the previous & next (surrounding) points, are checkable
            return (isXYPoint(allGcodeCommands[indexToCheck-1]) and isXYPoint(allGcodeCommands[indexToCheck]) and isXYPoint(allGcodeCommands[indexToCheck+1]))
        # returns the old gcode command if it doesn't need to be erased, but returns "TODELETE" if command should be deleted
        def correctedCommand(allGcodeCommands, index):
            # only checked XY points can be removed, so all non-checkable points will automatically NOT be removed
            if not isCheckablePoint(allGcodeCommands, index):
                return allGcodeCommands[index]
            else:
                
                def haveSameXCommands(allGcodeCommands, index):
                    previousCommand = allGcodeCommands[index-1]
                    previousCommandSet = (previousCommand.strip("\n")).split(" ")
                    thisCommand = allGcodeCommands[index]
                    thisCommandSet = (thisCommand.strip("\n")).split(" ")
                    nextCommand = allGcodeCommands[index+1]
                    nextCommandSet = (nextCommand.strip("\n")).split(" ")
                    return ((previousCommandSet[1]==thisCommandSet[1]) and (thisCommandSet[1]==nextCommandSet[1]))
                
                def haveSameYCommands(allGcodeCommands, index):
                    previousCommand = allGcodeCommands[index-1]
                    previousCommandSet = (previousCommand.strip("\n")).split(" ")
                    thisCommand = allGcodeCommands[index]
                    thisCommandSet = (thisCommand.strip("\n")).split(" ")
                    nextCommand = allGcodeCommands[index+1]
                    nextCommandSet = (nextCommand.strip("\n")).split(" ")
                    return ((previousCommandSet[2]==thisCommandSet[2]) and (thisCommandSet[2]==nextCommandSet[2]))
                
                # erase middle points that line up with the line;
                # erase points that have the same X or same Y commands as their surrounding points
                if( haveSameXCommands(allGcodeCommands, index) or haveSameYCommands(allGcodeCommands, index) ):
                    return "TODELETE"
                else:
                    # otherwise, DONT delete the command
                    return allGcodeCommands[index]


        # to draw a straight line, we just need the endpoints;
        # we can ignore the middle points and still draw the same line
        toWrite = []

        # ignore the first command (homing command)
        toWrite.append(allGcodeCommands[0])

        # check each valid, checkable point/command
        for index in range(1, len(allGcodeCommands)-1):
            # correctedCommands() returns the old gcode command if it doesn't need to be erased,
            # but returns "TODELETE" if command should be deleted;
            # dont write commands that are to be deleted
            correctedCommandResult = correctedCommand(allGcodeCommands, index)
            if(correctedCommandResult != "TODELETE"):
                toWrite.append(correctedCommandResult)

        # ignore the last command too (XY homing command)
        toWrite.append(allGcodeCommands[-1])

        gcodeRead.close()
        
        # wipe and write
        gcodeWrite = open("Output/drawing.gcode", "w")
        for index in range(len(toWrite)):
            gcodeWrite.write(toWrite[index])
        gcodeWrite.close()


    # erases duplicate gcode commands
    def duplicateEraser(self):
        allGcodeCommands = open("Output/drawing.gcode", "r").readlines()

        toWrite = []
        # go through each valid command to be checked...
        for index in range(len(allGcodeCommands)-1):
            # ...if there is a duplicate ahead, delete/ignore this one...
            # ...if not, note this command to write later
            if(allGcodeCommands[index] != allGcodeCommands[index+1]):
                toWrite.append(allGcodeCommands[index])
        # append last command (no need to check it)
        toWrite.append(allGcodeCommands[-1])
        
        gcodeWrite = open("Output/drawing.gcode", "w")
        for index in range(len(toWrite)):
            gcodeWrite.write(toWrite[index])
        gcodeWrite.close()


    # note: work in progress
    # note: this function only works on gcode, not turtle yet
    # to be called after gcodePurge, lineJoiner, duplicateEraser
    # tries to connect chains whose endpoints are close to each other
    def nearestNeighbor(self, proximity):
        # 1. find endpoints
        #       a. add endpoint at beginning and end of command set if there arent already
        # 2. find coordinates at endpoints
        # 3. for first two coordinates, find the closest other coordiante and see if it is within proximity (proximity should be pretty small)
        #       a. if within proximity, join the chains;
        #       b. then check closest endpoints to the newly formed larger chain's own endpoints
        #       c. repeat until no other endpoint is within proximity of the endpoints of the large main chain


        # helper function to find endpoints
        # returns list of pairs of endpoint line numbers
        def findProximity():
            # first, finds endpoints of chains
            allGcodeCommands = open("Output/drawing.gcode", "r").readlines()
            thisGcodeCommand = allGcodeCommands[0]
            thisGcodeCommandHeight = int((((thisGcodeCommand.strip("\n")).split(" "))[-1]).strip("Z"))
            startIndicies = []
            endIndicies = []
            thisEndpoint = [-1, -2]
            lineIndex = 0

            #print(thisGcodeCommandHeight == 5)
            #print(thisEndpoint[1])

            print(allGcodeCommands[0])
            print(allGcodeCommands[-1])
            return 

        findProximity()
        return
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

RETRACT_HEIGHT = 1
OPERATING_HEIGHT = 0
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
        gcodeOutput.write("G1 X0 Y0\n")

        turtleOutput.close()
        gcodeOutput.close()


    # this is to be used AFTER the turtle/gcode files have already been written
    # just for turtle
    def turtlePurge(self, minChainLength):
        turtleRead = open("Output/turtle.txt", "r")
        # a chain is the number of commands between two stops
        # if a chain is too small, then it is just a piece of noise that needs to be gotten rid of; we only want the main chains
        currentChain = []
        toWrite = []
        for turtleCommand in turtleRead.readlines():
            strippedTurtleCommand = turtleCommand.strip("\n")
            
            if (strippedTurtleCommand != "stop") and (strippedTurtleCommand != "end"):
                # when we find a command, grow the chain
                currentChain.append(turtleCommand)
            else:
                # end of command chain;
                # if the last chain was large enough, note it down to write later;
                # if it was too small, then forget about it
                if len(currentChain) >= minChainLength:
                    currentChain.append(turtleCommand)
                    toWrite = toWrite + currentChain
                # finally, start a new chain
                currentChain = []
        toWrite.append("end")
        turtleRead.close()

        # wipe and write
        turtleWrite = open("Output/turtle.txt", "w")
        for turtleCommandToWrite in toWrite:
            turtleWrite.write(turtleCommandToWrite)
        turtleWrite.close()
    # DEPRECATED TO REMOVE 
    def gcodePurge(self, minChainLength):
        gcodeRead = open("Output/drawing.gcode", "r")
        # a chain is the number of commands between two stops
        # if a chain is too small, then it is just a piece of noise that needs to be gotten rid of; we only want the main chains
        currentChain = []
        toWrite = []

        # ignore the first two gcode lines
        gcodeCommands = gcodeRead.readlines()
        toWrite.append(gcodeCommands[0])
        toWrite.append(gcodeCommands[1])

        for index in range(2, len(gcodeCommands) ):
            gcodeCommand = gcodeCommands[index]
            gcodeCommandSet = (gcodeCommand.strip("\n")).split(" ")
            
            # last part of command set is z; if z is retracted height then it is retracted/stopped there
            if ( gcodeCommandSet[-1] != "Z"+str(RETRACT_HEIGHT) ):
                # when we find a command, grow the chain
                currentChain.append(gcodeCommand)
            else:
                # end of command chain;
                # if the last chain was large enough, note it down to write later;
                # if it was too small, then forget about it
                if len(currentChain) >= minChainLength:
                    currentChain.append(gcodeCommand)
                    toWrite = toWrite + currentChain
                # finally, start a new chain
                currentChain = []
        gcodeRead.close()

        # wipe and write
        gcodeWrite = open("Output/drawing.gcode", "w")
        for index in range(len(toWrite)):
            gcodeWrite.write(toWrite[index])
        gcodeWrite.close()

    
    # note: THIS MUST BE USED AFTER PURGE FUNCTION, DO NOT USE BEFORE PURGE FUNCTION
    # joins smaller lines into larger lines
    def lineJoiner(self):
        # note: ONLY WORKS WITH GCODE FOR NOW
        gcodeRead = open("Output/drawing.gcode", "r")
        gcodeCommands = gcodeRead.readlines()

        # ignore first two commands
        toWrite = []
        toWrite.append(gcodeCommands[0])
        toWrite.append(gcodeCommands[1])

        mode = "N/A"

        previousGcodeCommand = "N/A"
        thisGcodeCommand = gcodeCommands[2]

        startCommand = "NA"
        endCommand = "NA"
        # starts a new chain starting at THIS command
        def startNewChain():
            startCommand = thisGcodeCommand
            mode = "new"
        # ends the chain ending on the PREVIOUS command
        def endLastChain():
            endCommand = previousGcodeCommand
            toWrite.append(startCommand)
            toWrite.append(endCommand)
            startCommand = "NA"
            endCommand = "NA"
        
        #startNewChain()
        startCommand = thisGcodeCommand
        mode = "new"

        for index in range (3, len(gcodeCommands) ):
            previousGcodeCommand = gcodeCommands[index-1]
            previousGcodeCommandSet = (previousGcodeCommand.strip("\n")).split(" ")
            previousGcodeCommandX = previousGcodeCommandSet[1].strip("X")
            previousGcodeCommandY = previousGcodeCommandSet[2].strip("Y")
            previousGcodeCommandZ = previousGcodeCommandSet[3].strip("Z")

            thisGcodeCommand = gcodeCommands[index]
            thisGcodeCommandSet = (thisGcodeCommand.strip("\n")).split(" ")
            thisGcodeCommandX = thisGcodeCommandSet[1].strip("X")
            thisGcodeCommandY = thisGcodeCommandSet[2].strip("Y")
            thisGcodeCommandZ = thisGcodeCommandSet[3].strip("Z")

            # sees if THIS point is splitting off from last
            def splitOff():

                def inLine():

                    def xInline():
                        return ((mode=="X") or (mode=="new")) and (thisGcodeCommandX==previousGcodeCommandX)
                    def yInline():
                        return ((mode=="Y") or (mode=="new")) and (thisGcodeCommandY==previousGcodeCommandY)

                    return xInline() or yInline()
                def lastCommandWasStop():
                    return (previousGcodeCommandZ == str(RETRACT_HEIGHT) )
                
                return (not inLine()) or lastCommandWasStop()
            
            # if stopped, end last chain and append this stop command
            if(thisGcodeCommandZ == str(RETRACT_HEIGHT) ):
                #endLastChain()
                endCommand = previousGcodeCommand
                toWrite.append(startCommand)
                toWrite.append(endCommand)
                startCommand = "NA"
                endCommand = "NA"

                toWrite.append(thisGcodeCommand)
                mode = "stopped"
            elif( splitOff() ):
                # if this command is split off from last, start new chain with this current one;
                # no need to end last chain if it was already done
                if(mode == "stopped"):
                    #startNewChain()
                    startCommand = thisGcodeCommand
                    mode = "new"
                else:
                    # otherwise, we have to end the last chain ourselves
                    #endLastChain()
                    endCommand = previousGcodeCommand
                    toWrite.append(startCommand)
                    toWrite.append(endCommand)
                    startCommand = "NA"
                    endCommand = "NA"
                    #startNewChain()
                    startCommand = thisGcodeCommand
                    mode = "new"
            else:
                # not split off, continue chain
                if(thisGcodeCommandX==previousGcodeCommandX):
                    mode = "X"
                elif(thisGcodeCommandX==previousGcodeCommandX):
                    mode = "Y"
        gcodeRead.close()
        
        # wipe and write
        gcodeWrite = open("Output/drawing.gcode", "w")
        for index in range(len(toWrite)):
            gcodeWrite.write(toWrite[index])
        gcodeWrite.close()
    

    # erases duplicate gcode commands
    def duplicateEraser(self):
        gcodeCommands = open("Output/drawing.gcode", "r").readlines()

        toWrite = []
        # go through each valid command to be checked...
        for index in range(len(gcodeCommands)-1):
            # ...if there is a duplicate ahead, delete/ignore this one...
            # ...if not, note this command to write later
            if(gcodeCommands[index] != gcodeCommands[index+1]):
                toWrite.append(gcodeCommands[index])
        # append last command (no need to check it)
        toWrite.append(gcodeCommands[-1])
        
        gcodeWrite = open("Output/drawing.gcode", "w")
        for index in range(len(toWrite)):
            gcodeWrite.write(toWrite[index])
        gcodeWrite.close()

    # note: work in progress
    # note: this function only works on gcode, not turtle yet
    # to be called after gcodePurge, lineJoiner, duplicateEraser
    # tries to connect chains whose endpoints are close to each other
    def proximityJoin(self, proximity):
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
            gcodeCommands = open("Output/drawing.gcode", "r").readlines()
            thisGcodeCommand = gcodeCommands[0]
            thisGcodeCommandHeight = int((((thisGcodeCommand.strip("\n")).split(" "))[-1]).strip("Z"))
            startIndicies = []
            endIndicies = []
            thisEndpoint = [-1, -2]
            lineIndex = 0

            #print(thisGcodeCommandHeight == 5)
            #print(thisEndpoint[1])

            print(gcodeCommands[0])
            print(gcodeCommands[-1])
            return 

        findProximity()
        return
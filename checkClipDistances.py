import maya.cmds as cmds
import I3DExporter
import I3DUtils


# ratio from shell size in meters to min and max CD in m
# e.g. a 0.5m shell should have at least 30m, but not above 250m CD
shellSizeToMinClipDistanceFactor = 60
shellSizeToMaxClipDistanceFactor = 500

cdDifferenceThresholdInfo = 0.4  # minimum proportinal difference between current and new CD to display a info
cdDifferenceThresholdWarning = 0.8  # minimum proportinal difference between current and new CD to display a warning
cdDifferenceThresholdError = 1.3  # minimum proportinal difference between current and new CD to display an error

# ignore node in "CD too low" check if name contains any of these strings
nodeNameMinCdIgnoreList = ["interior", "effect", "mirror"]
# ignore node in "CD too high" check if name contains any of these strings
nodeNameMaxCdIgnoreList = ["light"]


def executeCheckCDs():
    nodes = cmds.ls(assemblies=True)
    for node in nodes:
        checkNodeRecursivley(node)


def checkNodeRecursivley(node):
    nodeType = I3DExporter.I3DGetNodeType(node)
    isNonRenderable = I3DExporter.I3DGetAttributeValue(node, 'i3D_nonRenderable', False)
    mergeGroup = I3DExporter.I3DGetAttributeValue(node, 'i3D_mergeGroup', 0)
    boundingVolume = I3DExporter.I3DGetAttributeValue(node, 'i3D_boundingVolume', '')
    visible = cmds.getAttr(node + '.visibility')

    if nodeType == 1 and not isNonRenderable and mergeGroup == 0 and boundingVolume == '' and visible:
        clipDistance, minimumNode = I3DUtils.getEffectiveClipDistance(node, True)

        if clipDistance > 0:
            sx, sy, sz, numFaces = getMaxShellSize(node)  #  nsx, nsy, nsz, numShells
            size = max(sx, sy, sz)

            # increase weight for very small sizes, decrease for bigger ones
            minimumClipDistance = size**0.8 * shellSizeToMinClipDistanceFactor
            maximumClipDistance = size**0.8 * shellSizeToMaxClipDistanceFactor

            text = ""
            targetClipDistance = None
            differenceTargetCurrent = 0
            if clipDistance < minimumClipDistance and not isStringIgnored(node, nodeNameMinCdIgnoreList):
                targetClipDistance = roundToStep(minimumClipDistance * 1.1, 20, True)
                differenceTargetCurrent = abs(targetClipDistance - clipDistance) / clipDistance
                text = None
                if node == minimumNode:
                    text = "Clip Distance TOO LOW (Actual %d, Target %d)" % (clipDistance, targetClipDistance)
                else:
                    text = "Parent Clip Distance TOO LOW (Actual %d, Target %d)" % (clipDistance, targetClipDistance)

            elif clipDistance > maximumClipDistance and not isStringIgnored(node, nodeNameMaxCdIgnoreList):
                targetClipDistance = roundToStep(maximumClipDistance * 0.9, 20, False)
                differenceTargetCurrent = abs(targetClipDistance - clipDistance) / max(targetClipDistance, clipDistance)
                text = "Clip Distance TOO HIGH (Actual %d, Target %d)" % (clipDistance, targetClipDistance)

            if targetClipDistance:
                if differenceTargetCurrent > cdDifferenceThresholdInfo:

                    # set serverity and error type based on difference of current and target cd
                    messageType = I3DExporter.MESSAGE_TYPE_INFO
                    if differenceTargetCurrent > cdDifferenceThresholdWarning:
                        messageType = I3DExporter.MESSAGE_TYPE_WARNING
                    if differenceTargetCurrent > cdDifferenceThresholdError:
                        messageType = I3DExporter.MESSAGE_TYPE_ERROR

                    I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, node, buttonText="Select Object", buttonFunc=I3DUtils.selectObject, buttonArgs=node)
                    I3DExporter.I3DAddMessage(messageType, text,
                                              margin=30,
                                              buttonText="Set CD from {:.0f} to {}".format(clipDistance, targetClipDistance),
                                              buttonFunc=setNodeCdButtonCallback,
                                              buttonArgs=[node, 'i3D_clipDistance', float(targetClipDistance)],
                                              buttonRemoveLine=True)
                    I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, "")

    # recurse to child nodes if visible
    if visible:
        nodes = cmds.listRelatives(node, fullPath=True)
        if nodes:
            for node in nodes:
                nodeType = cmds.objectType(node)
                if nodeType == 'transform' or nodeType == 'joint':
                    checkNodeRecursivley(node)


def getMaxShellSize(node):
    # gets the maximum size of a shell (= connected faces) and number of faces within the node

    shells = []
    maxShellSizeX, maxShellSizeY, maxShellSizeZ = 0, 0, 0
    faces = cmds.ls(node + ".f[*]", flatten=True)  # get nodes faces as individual items
    num_faces = len(faces)

    # create shells from faces
    while faces:
        face = faces.pop(0)

        # create shell (all connected faces for current face) as range
        shellFacesRange = cmds.polySelect(node, extendToShell=int(face.split("[")[1].rstrip("]")), ass=True, q=True)

        shells.append(shellFacesRange)

        # remove faces which are part of the found shell from faces to yet expand
        for shellFace in cmds.ls(shellFacesRange, flatten=True):  # convert faces range to individual items
            if shellFace in faces:
                faces.remove(shellFace)

    # calculcate size for each shell
    for shellFacesRange in shells:
        minX, minY, minZ, maxX, maxY, maxZ = 100000, 100000, 100000, -100000, -100000, -100000

        shellVertices = cmds.polyListComponentConversion(shellFacesRange, toVertex=True)  # get all vertices for faces range

        for vertexName in cmds.ls(shellVertices, flatten=True):
            x, y, z = cmds.pointPosition(vertexName, local=True)

            minX = min(minX, x)
            minY = min(minY, y)
            minZ = min(minZ, z)
            maxX = max(maxX, x)
            maxY = max(maxY, y)
            maxZ = max(maxZ, z)

        maxShellSizeX = max(maxShellSizeX, maxX - minX)
        maxShellSizeY = max(maxShellSizeY, maxY - minY)
        maxShellSizeZ = max(maxShellSizeZ, maxZ - minZ)

    return maxShellSizeX, maxShellSizeY, maxShellSizeZ, num_faces  # , maxX-minX, maxY-minY, maxZ-minZ, len(shells)


def roundToStep(number, step=25, ceil=True):
    if ceil:
        number += step / 2
    else:
        number -= step / 2

    value = int(step * round(float(number) / step))

    return max(value, step)  # make sure at least step is returned (value might be 0)


def isStringIgnored(string, ignoreList):
    string = string.upper()
    for ignore in ignoreList:
        if ignore.upper() in string:
            return True
    return False


def setNodeCdButtonCallback(args, unused):
    node, attribute, value = args
    I3DExporter.I3DSaveAttributeFloat(node, attribute, value)


def selectNodeButtonCallback(node, unused):
    cmds.select(node)
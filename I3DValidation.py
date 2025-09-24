#
# I3DValidation
# Class to handle the validation of the maya file and displaying warnings
#
# @created 24/01/2024
# @author Stefan Maurus
#
# Copyright (C) GIANTS Software GmbH, Confidential, All Rights Reserved.
#

import maya.cmds as cmds

import I3DExporter
import I3DUtils
import ShaderUtil
import os
import math

MAX_POLYCOUNT = 200000
MAX_OBJECTCOUNT = 150
MAX_MERGE_GROUP_JOINTS = 255

COLORS = [
    [0.0158, 0.3168, 0.0082],
    [0.0754, 0.1943, 0.2577],
    [0.3012, 0.0197, 0.2051],
    [0.0805, 0.1372, 0.0132],
    [0.3452, 0.0288, 0.0825],
    [0.0533, 0.2634, 0.3691],
    [0.3665, 0.2863, 0.3015],
    [0.1449, 0.2486, 0.2479],
    [0.3606, 0.3114, 0.2947],
    [0.0573, 0.2368, 0.0248],
    [0.1859, 0.1977, 0.3122],
    [0.1134, 0.3851, 0.2920],
    [0.3587, 0.2530, 0.1887],
    [0.1992, 0.1192, 0.1225],
    [0.3881, 0.1181, 0.0027],
]

MERGE_GROUP_SHAPE_ATTRIBUTES = [
    'i3D_nonRenderable', 
    'i3D_distanceBlending', 
    'i3D_oc', 
    'i3D_terrainDecal',
    'i3D_renderedInViewports',
    'i3D_doubleSided', 
    'i3D_materialHolder',
    'i3D_navMeshMask',
    'i3D_decalLayer']

class I3DValidation:
    def __init__(self, handler):
        self.handler = handler

        self.xmlFilename = ""

        self.objectCount = 0
        self.objectSpecies = "UNKNOWN"
        self.polyCount = 0

        self.warningCount = 0
        self.errorCount = 0

        self.objectErrorCount = 0
        self.objectWarningCount = 0
        self.objectInfoCount = 0

        self.messageBuffer = []
        self.objectMessageBuffer = []

        self.exportSkinnedMergeNodes = {}
        self.exportSkinnedMergeVolumes = {}
        self.exportSkinnedMergeRootNodes = {}
        self.numSkinnedMergeJoints = {}

        self.exportXMLIdentifiers = {}

        self.vertexColorNodes = []
        self.staticNodes = []
        self.decalCastShadowNodes = []

        self.mergeableMaterialCache = {}
        self.mergeableObjectCache = {}

        self.nodes = []

        transforms = cmds.ls(type="transform", l=True)
        if transforms is not None:
            self.nodes += transforms

        joints = cmds.ls(type="joint", l=True)
        if joints is not None:
            self.nodes += joints

        numNodes = 0
        for node in self.nodes:
            if "_ignore" not in node:
                numNodes += 1

        self.handler.addProgressSteps(numNodes)

    def doValidate(self):
        self.__checkScenegraph()

    def setXMLFilename(self, filename):
        self.xmlFilename = filename

    def __addMessageToBuffer(self, typeIndex, message, margin=0, color=None, buttonText="", buttonFunc=None, buttonArgs=[], buttonAnnotation=None, buttonRemoveLine=False, buttonColor=None, buffer=None):
        info = {}
        info["typeIndex"] = typeIndex
        info["message"] = message
        info["margin"] = margin
        info["color"] = color
        if buttonFunc is not None:
            info["buttonText"] = buttonText
            info["buttonFunc"] = buttonFunc
            info["buttonArgs"] = buttonArgs
            info["buttonAnnotation"] = buttonAnnotation
            info["buttonRemoveLine"] = buttonRemoveLine
            info["buttonColor"] = buttonColor

        if typeIndex == I3DExporter.MESSAGE_TYPE_WARNING:
            self.warningCount += 1
        elif typeIndex == I3DExporter.MESSAGE_TYPE_ERROR:
            self.errorCount += 1

        if buffer is None:
            buffer = self.messageBuffer
        buffer.append(info)

    def __addMessageToObjectBuffer(self, typeIndex, message, margin=0, color=None, buttonText="", buttonFunc=None, buttonArgs=[], buttonAnnotation=None, buttonRemoveLine=False, buttonColor=None, isHeader=False):
        self.__addMessageToBuffer(typeIndex, message, margin=margin, color=color, buttonText=buttonText, buttonFunc=buttonFunc, buttonArgs=buttonArgs, buttonAnnotation=buttonAnnotation, buttonRemoveLine=buttonRemoveLine, buttonColor=buttonColor, buffer=self.objectMessageBuffer)
        if isHeader:
            info = self.objectMessageBuffer[-1]
            self.objectMessageBuffer.pop(len(self.objectMessageBuffer) - 1)
            self.objectMessageBuffer.insert(0, info)

        if typeIndex == I3DExporter.MESSAGE_TYPE_WARNING:
            self.objectErrorCount += 1
        elif typeIndex == I3DExporter.MESSAGE_TYPE_ERROR:
            self.objectWarningCount += 1
        elif typeIndex == I3DExporter.MESSAGE_TYPE_INFO:
            self.objectInfoCount += 1

    def __addObjectBufferToMainBuffer(self, ):
        for info in self.objectMessageBuffer:
            self.messageBuffer.append(info)
        self.objectMessageBuffer = []

        self.objectErrorCount = 0
        self.objectWarningCount = 0
        self.objectInfoCount = 0

    def addMessageFunc(self, type, message, margin, buttonText="", buttonFunc=None, buttonArgs=[], buttonAnnotation=None, buttonRemoveLine=False, buttonColor=None):
        if type == "info":
            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_INFO, message, margin, buttonText=buttonText, buttonFunc=buttonFunc, buttonArgs=buttonArgs, buttonAnnotation=buttonAnnotation, buttonRemoveLine=buttonRemoveLine, buttonColor=buttonColor)
        elif type == "warning":
            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, message, margin, buttonText=buttonText, buttonFunc=buttonFunc, buttonArgs=buttonArgs, buttonAnnotation=buttonAnnotation, buttonRemoveLine=buttonRemoveLine, buttonColor=buttonColor)
        elif type == "error":
            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_ERROR, message, margin, buttonText=buttonText, buttonFunc=buttonFunc, buttonArgs=buttonArgs, buttonAnnotation=buttonAnnotation, buttonRemoveLine=buttonRemoveLine, buttonColor=buttonColor)

    def __getAreMaterialsMergeable(self, material1, material2):
        if material1 in self.mergeableMaterialCache:
            if material2 in self.mergeableMaterialCache[material1]:
                return self.mergeableMaterialCache[material1][material2]["mergeable"], self.mergeableMaterialCache[material1][material2]["mismatchData"]

        if material2 in self.mergeableMaterialCache:
            if material1 in self.mergeableMaterialCache[material2]:
                return self.mergeableMaterialCache[material2][material1]["mergeable"], self.mergeableMaterialCache[material2][material1]["mismatchData"]

        mergeable, mismatchData = I3DUtils.getAreMaterialsMergeable(material1, material2)

        cacheData = {}
        cacheData["mergeable"] = mergeable
        cacheData["mismatchData"] = mismatchData

        if material1 not in self.mergeableMaterialCache:
            self.mergeableMaterialCache[material1] = {}

        self.mergeableMaterialCache[material1][material2] = cacheData

        return mergeable, mismatchData

    def __getAreObjectsMergeable(self, object1, object2, checkFirstMaterial=False):
        if object1 in self.mergeableObjectCache:
            if object2 in self.mergeableObjectCache[object1]:
                return self.mergeableObjectCache[object1][object2]["mergeable"], self.mergeableObjectCache[object1][object2]["mismatchData"]

        if object2 in self.mergeableObjectCache:
            if object1 in self.mergeableObjectCache[object2]:
                return self.mergeableObjectCache[object2][object1]["mergeable"], self.mergeableObjectCache[object2][object1]["mismatchData"]

        mergeable = False
        mismatchData = None

        if I3DExporter.I3DGetAttributeValue(object1, 'i3D_decalLayer', 0) != I3DExporter.I3DGetAttributeValue(object2, 'i3D_decalLayer', 0):
            mergeable = False
            mismatchData = {"type": "Object", "object1": object1, "object2": object2, "attributeName": "decalLayer", "attribute1": I3DExporter.I3DGetAttributeValue(object1, 'i3D_decalLayer', 0), "attribute2": I3DExporter.I3DGetAttributeValue(object2, 'i3D_decalLayer', 0)}
        else:
            materials1 = I3DUtils.getObjectMaterials(object1)
            materials2 = I3DUtils.getObjectMaterials(object2)

            if materials1 is not None and materials2 is not None:
                mergeable = True
                if checkFirstMaterial:
                    mergeable, mismatchData = self.__getAreMaterialsMergeable(materials1[0], materials2[0])
                else:
                    for material1 in materials1:
                        for material2 in materials2:
                            mergeable, mismatchData = self.__getAreMaterialsMergeable(material1, material2)
                            if not mergeable:
                                break
                        if not mergeable:
                            break

        cacheData = {}
        cacheData["mergeable"] = mergeable
        cacheData["mismatchData"] = mismatchData

        if object1 not in self.mergeableObjectCache:
            self.mergeableObjectCache[object1] = {}

        self.mergeableObjectCache[object1][object2] = cacheData

        return mergeable, mismatchData

    def __getAreObjectMaterialsMergeable(self, object):
        materials = I3DUtils.getObjectMaterials(object)
        if materials is not None:
            for material1 in materials:
                for material2 in materials:
                    if material1 != material2:
                        mergeable, mismatchData = self.__getAreMaterialsMergeable(material1, material2)
                        if not mergeable:
                            return mergeable, mismatchData
        return True, None

    def __checkScenegraph(self):
        self.mergeableMaterialCache = {}
        self.mergeableObjectCache = {}

        self.messageBuffer = []

        nodes = cmds.ls(assemblies=True)

        self.objectSpecies = I3DUtils.getSpeciesFromXMLs(self.xmlFilename)

        for node in nodes:
            nodeType = cmds.objectType(node)
            if ((nodeType == 'transform' or nodeType == 'joint') and not I3DUtils.isDefaultCamera(node)):
                self.__checkTransfromGroup(node, self.objectSpecies)

        # provide a single button to remove all obsolete vertex colors
        if len(self.vertexColorNodes) > 0:
            def removeVertexColorsFromNodes(nodes, unused):
                for node in nodes:
                    I3DUtils.removeVertexColors(node, None)

            self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_NONE,
                                      'Remove all obsolete vertex colors',
                                      color="#FF8C00",
                                      buttonText="Remove all obsolete vertex colors",
                                      buttonFunc=removeVertexColorsFromNodes,
                                      buttonArgs=self.vertexColorNodes,
                                      buttonColor=COLORS[1])

        if len(self.staticNodes) > 0:
            def removeStaticFlagFromNodes(nodes, unused):
                for node in nodes:
                    I3DUtils.removeObjectStaticFlag(node, None)

            self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_NONE,
                                      'Remove all static flags',
                                      color="#FF8C00",
                                      buttonText="Remove all static flags from nodes",
                                      buttonFunc=removeStaticFlagFromNodes,
                                      buttonArgs=self.staticNodes,
                                      buttonColor=COLORS[2])

        if len(self.decalCastShadowNodes) > 0:
            def removeCastShadowFromNodes(nodes, unused):
                for node in nodes:
                    self.__removeCastShadow(node, None)

            self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_NONE,
                                      'Remove cast shadow from decal nodes',
                                      color="#FF8C00",
                                      buttonText="Remove cast shadow from decal nodes",
                                      buttonFunc=removeCastShadowFromNodes,
                                      buttonArgs=self.decalCastShadowNodes,
                                      buttonColor=COLORS[0])

        if self.polyCount > MAX_POLYCOUNT:
            self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING, 'Polycount %d is very high. This causes performance issues. Try to reduce polycount' % self.polyCount)
            self.errorCount = self.errorCount + 1

        if self.objectCount > MAX_OBJECTCOUNT:
            self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING, 'Objectcount %d is very high. This causes performance issues. Try to combine some objects' % self.objectCount)
            self.errorCount = self.errorCount + 1
            
        def getMergeGroupObjects(mergeGroupIndex):
            mergeGroupObjects = []
            objects = cmds.ls(o=True, long=True)
            for object in objects:
                if "_ignore" not in object:
                    mergeGroup = I3DExporter.I3DGetAttributeValue(object, 'i3D_mergeGroup', '')
                    if mergeGroup != '' and mergeGroup != 0 and mergeGroup == mergeGroupIndex:
                        mergeGroupObjects.append(object)

            return mergeGroupObjects
        
        def fixHexAttributeValue(node, val):
            # value is string type but in decimal format, convert to hex string
            if type(val) is str and not val.startswith('0x'):
                val = hex(int(val))
                I3DExporter.I3DSaveAttributeHex(node, attr, val)

            elif type(val) is int:
                if val != int(defaultValue, 16):  # only print warning if value is different from default
                    self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Warning: attribute '{}' in ma file has wrong type '{}' instead of 'str', converting".format(attr, type(val)))
                val = hex(val)  # convert int to hex str
                I3DExporter.I3DSaveAttributeHex(node, attr, val)

            return val
        
        def fixMergeGroupValues(mergeGroup, unused):
            rootNode = self.exportSkinnedMergeRootNodes[mergeGroup]
            mergeGroupObjects = getMergeGroupObjects(mergeGroup)
            for attr in MERGE_GROUP_SHAPE_ATTRIBUTES:
                rootVal = I3DExporter.I3DGetAttributeValue(rootNode, attr, defaultValue)

                for mergeGroupObject in mergeGroupObjects:
                    if mergeGroupObject == rootNode:
                        continue
                    
                    if 'type' not in I3DExporter.SETTINGS_ATTRIBUTES[attr]:
                        continue

                    I3DExporter.I3DSetAttributeValue(mergeGroupObject, attr, rootVal)

        for mergeGroup, numSkinnedMergeJoints in self.numSkinnedMergeJoints.items():
            if numSkinnedMergeJoints > MAX_MERGE_GROUP_JOINTS:
                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING, 'MergeGroup %d has %d joints. Maximum number of joints is %d. Use an additional mergegroup!' % (mergeGroup, numSkinnedMergeJoints, MAX_MERGE_GROUP_JOINTS))
                self.errorCount = self.errorCount + 1
            elif numSkinnedMergeJoints == 1:
                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING, 'MergeGroup %d has only one joint. Remove unnecessary MergeGroup!' % (mergeGroup))

            rootNode = None
            if mergeGroup in self.exportSkinnedMergeRootNodes:
                rootNode = self.exportSkinnedMergeRootNodes[mergeGroup]
            if rootNode is None:
                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "MergeGroup %d has no root node defined. Define a mesh or empty transform group as root node!" % (mergeGroup))
            else:
                hasDifferingShapeAttributes = False
                mergeGroupObjects = getMergeGroupObjects(mergeGroup)
                for attr in MERGE_GROUP_SHAPE_ATTRIBUTES:
                    defaultValue = I3DExporter.SETTINGS_ATTRIBUTES[attr]['defaultValue']
                    rootVal = I3DExporter.I3DGetAttributeValue(rootNode, attr, defaultValue)
                    
                    # Workaround for HEX values which used to be saved as int but are now stored
                    # as string.
                    if 'type' in I3DExporter.SETTINGS_ATTRIBUTES[attr] and I3DExporter.SETTINGS_ATTRIBUTES[attr]['type'] == I3DExporter.TYPE_HEX:
                        rootVal = fixHexAttributeValue(rootNode, rootVal)

                    for mergeGroupObject in mergeGroupObjects:
                        if mergeGroupObject == rootNode:
                            continue
                        
                        val = I3DExporter.I3DGetAttributeValue(mergeGroupObject, attr, defaultValue)

                        # Workaround for HEX values which used to be saved as int but are now stored
                        # as string.
                        if 'type' in I3DExporter.SETTINGS_ATTRIBUTES[attr] and I3DExporter.SETTINGS_ATTRIBUTES[attr]['type'] == I3DExporter.TYPE_HEX:
                            val = fixHexAttributeValue(mergeGroupObject, val)

                        if val != rootVal:
                            #self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_INFO, "Node %s, which is part of mergeGroup %d, has a value set for attribute %s which is different from the merge groups root node (%s). This value will be ignored." % (mergeGroupObject, mergeGroup, attr, rootNode))
                            hasDifferingShapeAttributes = True
                            break

                    if hasDifferingShapeAttributes:
                        break

                if hasDifferingShapeAttributes:
                    self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING, 'Merge group {} has shape attribute values which are different between the root node and other nodes. Shape attributes set on non-root nodes will be ignored. Do you want to match these values?'.format(mergeGroup), margin=15, buttonText="Match Values", buttonFunc=fixMergeGroupValues, buttonArgs=mergeGroup, buttonColor=COLORS[1])

        for boundingVolume, isDefined in self.exportSkinnedMergeVolumes.items():
            if not isDefined:
                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_INFO, 'No bounding-volume defined for ' + str(boundingVolume) + '. Automatically calculating bounding volume!')

        textures = cmds.ls(fl=True, textures=True)

        missing = []
        missingPath = []
        mayaFileName = cmds.file(query=True, sceneName=True)
        for texture in textures:
            p = cmds.getAttr(texture + ".fileTextureName")
            if ":" in str(p).split("/")[0]:
                # absolute path, contains drive
                if p.split("/")[0] == mayaFileName.split("/")[0]:
                    if not os.path.exists(p):
                        if texture not in missing:
                            missing.append(texture)
                            missingPath.append(p)
                elif str(cmds.filePathEditor(p, query=True, status=True)).rpartition(" ")[2] == "0":
                    if texture not in missing:
                        missing.append(texture)
                        missingPath.append(p)
            if not os.path.exists(p):
                if texture not in missing:
                    missing.append(texture)
                    missingPath.append(p)
        if len(missing) > 0:
            for index, texture in enumerate(missing):
                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING, 'Texture "' + str(texture) + '" is missing (' + missingPath[index] + ')!')
                self.errorCount = self.errorCount + 1

        def changeTextureGamePath(args, unused):
            cmds.setAttr(args[0] + ".fileTextureName", cmds.getAttr(args[0] + ".fileTextureName").replace(args[1], args[2]), type="string")

        def selectNode(node, unused):
            cmds.select(node)

        def selectMergeGroup(mergeGroupIndex, unused):
            mergeGroupObjects = getMergeGroupObjects(mergeGroupIndex)
            cmds.select(mergeGroupObjects)

        def changeAllTextureGamePath(args, unused):
            for textureData in args[0]:
                changeTextureGamePath(textureData, unused)

        workSpace = cmds.workspace(q=True, rd=True)
        binName = mayaFileName[len(workSpace):].split("/")[0]
        wronglySourcedTextures = []
        for texture in textures:
            path = cmds.getAttr(texture + ".fileTextureName")
            path = path.replace("//", "/")
            if workSpace in path:
                # in case the texure is loaded from a differently named "bin" folder inside the current project
                if "bin" in binName and os.path.isdir(workSpace + binName):
                    textureBinName = path[len(workSpace):].split("/")[0]
                    if textureBinName != binName:
                        textureData = [texture, workSpace + textureBinName + "/", workSpace + binName + "/"]
                        wronglySourcedTextures.append(textureData)
                        self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING,
                                                  'Texture loaded from different project directory "%s"!' % path,
                                                  3,
                                                  buttonText="Change to '%s'" % binName,
                                                  buttonFunc=changeTextureGamePath,
                                                  buttonArgs=textureData,
                                                  buttonRemoveLine=True,
                                                  buttonColor=COLORS[1])
            else:
                # in case the texture is laoded from another project but is available inside the current project as well
                if "/bin/" in path:
                    texturePath = path.split("bin/")
                    if len(texturePath) == 2:
                        newPath = workSpace + "/bin/" + texturePath[1]
                        if os.path.isfile(newPath):
                            textureData = [texture, cmds.getAttr(texture + ".fileTextureName"), newPath]
                            wronglySourcedTextures.append(textureData)
                            self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING,
                                                      'Texture loaded from different project directory "%s"!' % path,
                                                      3,
                                                      buttonText="Change to '%s'" % binName,
                                                      buttonFunc=changeTextureGamePath,
                                                      buttonArgs=textureData,
                                                      buttonRemoveLine=True,
                                                      buttonColor=COLORS[1])
                        else:
                            self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING,
                                                      'Texture loaded from outside the current project directory "%s"!' % path,
                                                      3,
                                                      buttonText="Select Texture",
                                                      buttonFunc=selectNode,
                                                      buttonArgs=texture,
                                                      buttonColor=COLORS[1])

        # check if all shader paths are valid
        mayaFileFolder = os.path.dirname(os.path.abspath(mayaFileName))

        def setMaterialShaderDir(args, unused):
            absPath = args[1] + '/' + args[2]
            relPath = I3DUtils.getRelativePath(absPath, mayaFileFolder)
            relPath = relPath.replace("\\", "/")
            I3DExporter.I3DAddAttribute(args[0], 'customShader', relPath)

        materials = cmds.ls(fl=True, materials=True)
        for material in materials:
            shaderDir = I3DExporter.I3DGetProjectSetting("GIANTS_SHADER_DIR")
            shaderPath = I3DExporter.I3DGetAttributeValue(material, 'customShader', None)
            if shaderPath is not None:
                if not shaderPath[:14] == "$data/shaders/":
                    shaderFile = os.path.basename(shaderPath)
                    if shaderPath[0] == "$":
                        gamePath = I3DExporter.I3DGetGamePath()
                        shaderPath = shaderPath.replace('$', gamePath + '/')
                    else:
                        shaderPath = I3DUtils.getMergePaths(mayaFileFolder, shaderPath)
                    if not os.path.exists(shaderPath):
                        shaderDirSet, foundInBasegame = I3DExporter.I3DSearchShaderInBasegame(shaderFile)
                        if shaderDirSet:
                            if foundInBasegame:
                                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING,
                                                          'Material "%s" customShader does not exist "%s"!' % (material, str(shaderPath)),
                                                          3,
                                                          buttonText="Use from Base Shader Dir",
                                                          buttonFunc=setMaterialShaderDir,
                                                          buttonArgs=[material, shaderDir, shaderFile],
                                                          buttonAnnotation="Use '%s'" % (shaderDir + "/" + shaderFile),
                                                          buttonColor=COLORS[1])
                            else:
                                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING, 'Material "%s" customShader does not exist "%s" and could not be found in basegame!' % (material, str(shaderPath)), margin=3)
                        else:
                            self.__addMessageToBuffer(self.messageBuffer, 'Material "%s" customShader does not exist "%s"!' % (material, str(shaderPath)), margin=3)
                else:
                    shaderFile = shaderPath[14:]
                    shaderDirSet, foundInBasegame = I3DExporter.I3DSearchShaderInBasegame(shaderFile)
                    if shaderDirSet:
                        if not foundInBasegame:
                            self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING, 'Material "%s" uses customShader from basegame "%s", but shader could not be found in set directory!' % (material, str(shaderPath)), margin=3)

            if "numbers_mat" in material:
                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_WARNING,
                                          'Obsolete numbers material found "%s"!' % material,
                                          3,
                                          buttonText="Remove Material",
                                          buttonFunc=I3DUtils.removeMaterial,
                                          buttonArgs=[material],
                                          buttonColor=COLORS[2])

            I3DExporter.pluginEvent("onMaterialCheck", material, self.addMessageFunc, [])

            if self.objectErrorCount > 0 or self.objectWarningCount > 0 or self.objectInfoCount > 0:
                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_NONE, material, buttonText="Select Material", margin=10, buttonFunc=I3DUtils.selectObject, buttonArgs=material, isHeader=True)
                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_NONE, '')

                self.__addObjectBufferToMainBuffer()

        if len(wronglySourcedTextures) > 0:
            self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_NONE,
                                      "Change all textures to be loaded from '%s'" % binName,
                                      color="#FF8C00",
                                      buttonText="Change all to '%s'" % binName,
                                      buttonFunc=changeAllTextureGamePath,
                                      buttonArgs=[wronglySourcedTextures],
                                      buttonColor=COLORS[0])

        # merge group info
        if len(self.numSkinnedMergeJoints) > 0:
            if not I3DExporter.I3DGetAttributeValue(I3DExporter.SETTINGS_PREFIX, 'i3D_exportMergeGroups', True):
                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_ERROR, "Merge groups defined but merge group export disabled!")

            self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_NONE, 'MergeGroup-Info:', margin=15)
            for mergeGroup in sorted(list(self.numSkinnedMergeJoints)):
                color = COLORS[1]
                displayLayer = "MERGEGROUP_%d" % mergeGroup
                if cmds.objExists(displayLayer):
                    color = cmds.colorIndex(cmds.getAttr(displayLayer + ".color"), q=True)

                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_NONE, 'MergeGroup ' + str(mergeGroup), margin=30, buttonText="Select Objects", buttonFunc=selectMergeGroup, buttonArgs=mergeGroup, buttonColor=color)

                if mergeGroup in self.exportSkinnedMergeNodes:
                    path = None
                    rootNode = None
                    if mergeGroup in self.exportSkinnedMergeRootNodes:
                        rootNode = self.exportSkinnedMergeRootNodes[mergeGroup]
                        path = I3DUtils.getIndexPath(rootNode)

                    if rootNode is None:
                        rootNode = self.exportSkinnedMergeNodes[mergeGroup]['node'] + ' (Default)'
                        path = I3DUtils.getIndexPath(self.exportSkinnedMergeNodes[mergeGroup]['node'])

                    self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_NONE, '- Root Node: ' + rootNode, margin=45, buttonText="Select Root", buttonFunc=selectNode, buttonArgs=rootNode, buttonColor=color)

                self.__addMessageToBuffer(I3DExporter.MESSAGE_TYPE_NONE, '- Joints: ' + str(self.numSkinnedMergeJoints[mergeGroup]), margin=45)

        I3DExporter.I3DAddMessages(self.messageBuffer)

    def __removeCastShadow(self, node, unused):
        if cmds.objExists(node + ".castsShadows"):
            cmds.setAttr(node + ".castsShadows", False)

    def __removeDecalLayer(self, node, unused):
        I3DExporter.I3DSaveAttributeInt(node, 'i3D_decalLayer', 0)

    def __checkTransfromGroup(self, node, objectSpecies):
        self.handler.updateProgress("Validation (%s)" % node[-30:])

        nodeName = cmds.ls(node, l=False)[0]
        loweredNodeName = nodeName.lower()
        nameParts = loweredNodeName.split("|")
        loweredNodeName = nameParts[len(nameParts) - 1]

        nodeType = I3DExporter.I3DGetNodeType(node)
        xmlIdentifier = I3DExporter.I3DGetAttributeValue(node, 'i3D_xmlIdentifier', "")

        if nodeType == I3DExporter.NODETYPE_MESH:
            isNonRenderable = I3DExporter.I3DGetAttributeValue(node, 'i3D_nonRenderable', False)
            mergeGroup = I3DExporter.I3DGetAttributeValue(node, 'i3D_mergeGroup', 0)
            boundingVolume = I3DExporter.I3DGetAttributeValue(node, 'i3D_boundingVolume', '')

            for object in cmds.listHistory(node):
                if 'skinCluster' in object and cmds.objectType(object) == 'skinCluster':
                    skinningMethod = I3DExporter.I3DGetAttributeValue(object, 'skinningMethod', 0)
                    if skinningMethod != 1:
                        skinningMethodStr = skinningMethod == 0 and "Classic Linear" or skinningMethod == 1 and "Dual Quaternion" or skinningMethod == 2 and "Weight Blended" or "Unknown"
                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node is skinned but uses unsupported skinning method '%s' on %s, use 'Dual Quaternion' instead." % (skinningMethodStr, object), margin=30, buttonText="Change Method", buttonFunc=I3DUtils.changeSkinningMethod, buttonArgs=object, buttonRemoveLine=True, buttonColor=COLORS[3])

                    if mergeGroup > 0:
                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "MergeGroup: Skinned node is added to a mergeGroup!", margin=30, buttonText="Remove from MergeGroup", buttonFunc=I3DUtils.removeObjectFromMergeGroup, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[3])

            trisCount = cmds.polyEvaluate(node, t=True)

            if trisCount > 0 and not isNonRenderable and mergeGroup == 0:
                self.objectCount = self.objectCount + 1
                if isinstance(trisCount, list):
                    count = 0
                    for fc in trisCount:
                        count += fc
                    trisCount = int(count)

                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Multiple shapes defined!", margin=30)

                self.polyCount = self.polyCount + trisCount

            hasCollision = I3DExporter.I3DGetAttributeValue(node, 'i3D_collision', True)  # TODO: get proper defaults from Exporter in case they change
            if hasCollision and (I3DExporter.I3DGetAttributeValue(node, 'i3D_static', True) or I3DExporter.I3DGetAttributeValue(node, 'i3D_dynamic', False) or I3DExporter.I3DGetAttributeValue(node, 'i3D_kinematic', False)):
                oldCollisionMask = I3DExporter.I3DGetAttributeValue(node, 'i3D_collisionMask', None)
                if oldCollisionMask is not None:
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_ERROR, "Node uses deprecated attribute 'i3d_collisionMask' with value {}!".format(oldCollisionMask), margin=30, buttonText="Convert Mask", buttonFunc=I3DUtils.updateObjectCollisionMask, buttonArgs=node, buttonRemoveLine=False, buttonColor=COLORS[4])
                else:
                    # shape has new masks but no proper values set
                    if I3DExporter.I3DGetAttributeValue(node, 'i3D_collisionFilterMask', "0xff") == "0xff":
                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_ERROR, "Node uses default value '0xff' for 'i3D_collisionFilterMask'. Please apply a fitting collision preset in Attributes -> Rigid Body!", margin=30)

                    if I3DExporter.I3DGetAttributeValue(node, 'i3D_collisionFilterGroup', "0xff") == "0xff":
                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_ERROR, "Node uses default value '0xff' for 'i3D_collisionFilterGroup'. Please apply a fitting collision preset in Attributes -> Rigid Body!", margin=30)

                colMaxTris = 1000
                if trisCount > colMaxTris:
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node is a rigid body with {} triangles. Please add a custom low poly collision mesh instead!".format(trisCount), margin=30)

            if I3DExporter.I3DGetAttributeValue(node, 'i3D_trigger', False) and not hasCollision:
                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_ERROR, "Node is a trigger but does not have collision enabled!", margin=30)

            if objectSpecies != "PLACEABLE":
                if I3DExporter.I3DGetAttributeValue(node, 'i3D_static', True):
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_INFO, "RigidBody: Node is marked as static!", margin=30, buttonText="Remove 'Static' flag", buttonFunc=I3DUtils.removeObjectStaticFlag, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[2])
                    self.staticNodes.append(node)
            else:
                if I3DExporter.I3DGetAttributeValue(node, 'i3D_static', True):
                    if not I3DExporter.I3DGetAttributeValue(node, 'i3D_nonRenderable', False):
                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_INFO, "Visual mesh has collision. Please use dedicated low-poly collision mesh!", margin=30, buttonText="Remove 'Static' flag", buttonFunc=I3DUtils.removeObjectStaticFlag, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[2])
                        self.staticNodes.append(node)

            if not isNonRenderable and mergeGroup == 0 and boundingVolume == '' and not I3DUtils.isCamera(node):
                if I3DUtils.getEffectiveClipDistance(node) == 0:
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_INFO, "Clipdistance: Node has no clipdistance set. This causes performance issues!", margin=30, buttonText="Set Clipdistance to '300'", buttonFunc=I3DUtils.setObjectDefaultClipDistance, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[5])

            if mergeGroup > 0:
                if mergeGroup not in self.numSkinnedMergeJoints:
                    self.numSkinnedMergeJoints[mergeGroup] = 0
                self.numSkinnedMergeJoints[mergeGroup] = self.numSkinnedMergeJoints[mergeGroup] + 1

                mergeGroupName = "MERGEGROUP_" + str(mergeGroup)
                if mergeGroupName not in self.exportSkinnedMergeVolumes:
                    self.exportSkinnedMergeVolumes[mergeGroupName] = False

            if boundingVolume != '':
                self.exportSkinnedMergeVolumes[boundingVolume] = True

            if "fillvolume" in loweredNodeName:
                if not I3DExporter.I3DGetIsVisible(node, overallVisibility=False):
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "FillVolume node is hidden! Use 'nonRenderable' instead of hiding the node!", margin=30, buttonText="Show FillVolume and hide mesh", buttonFunc=I3DUtils.showObjectAndHideMesh, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[6])
                if I3DExporter.I3DGetAttributeValue(node, 'i3D_cpuMesh', 0) == 0:
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "FillVolume is not marked as CPU-Mesh!", margin=30, buttonText="Add CPU-Mesh flag", buttonFunc=I3DUtils.addObjectCPUMeshFlag, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[7])

            shapes = cmds.listRelatives(node, shapes=True, fullPath=True)
            if shapes is not None:
                for shape in shapes:
                    intermediateObject = cmds.getAttr(shape + '.intermediateObject')
                    if intermediateObject:
                        hasSkinning = False
                        for object in cmds.listHistory(node):
                            if 'skinCluster' in object:
                                hasSkinning = True

                        if not hasSkinning:
                            shapeName = shape.split("|")
                            shapeName = shapeName[len(shapeName) - 1]

                            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has intermediate shape '%s' but is not skinned" % shapeName, margin=30, buttonText="Remove Shape", buttonFunc=I3DUtils.removeIntermediateShape, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[8])

            decalLayer = I3DExporter.I3DGetAttributeValue(node, 'i3D_decalLayer', 0)
            if decalLayer > 0 and cmds.objExists(node + ".castsShadows"):
                castsShadows = cmds.getAttr(node + ".castsShadows")
                if castsShadows:
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node with decalLayer set to '%s' has casts shadows set to TRUE" % decalLayer, margin=30, buttonText="Remove Cast Shadow", buttonFunc=self.__removeCastShadow, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[9])
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Remove decal layer attribute from '%s'" % nodeName, margin=30, buttonText="Remove Decal Layer", buttonFunc=self.__removeDecalLayer, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[12])
                    self.decalCastShadowNodes.append(node)

        elif nodeType == I3DExporter.NODETYPE_JOINT:
            if xmlIdentifier != "":  # check for joint orientations only if the joint is going to be used in the XML file. I3D animations support joint orientation and joints not used in xml do not matter.
                jointOrientX = cmds.getAttr(node + '.jointOrientX')
                jointOrientY = cmds.getAttr(node + '.jointOrientY')
                jointOrientZ = cmds.getAttr(node + '.jointOrientZ')
                if abs(jointOrientX) > 0.0001 or abs(jointOrientY) > 0.0001 or abs(jointOrientZ) > 0.0001:
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Joint has joint orientation set. This cannot be exported", margin=30, buttonText="Reset joint orientation", buttonFunc=I3DUtils.resetJointOrientation, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[10])

        if xmlIdentifier != "":
            if xmlIdentifier in self.exportXMLIdentifiers:
                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, 'XML-Identifier "%s" already used for node "%s"!' % (xmlIdentifier, self.exportXMLIdentifiers[xmlIdentifier].split("|")[-1]), margin=30, buttonText="Select Conflicted Object", buttonFunc=I3DUtils.selectObject, buttonArgs=[self.exportXMLIdentifiers[xmlIdentifier]], buttonColor=COLORS[11])
            else:
                self.exportXMLIdentifiers[xmlIdentifier] = node

        hasLod = I3DExporter.I3DGetAttributeValue(node, 'i3D_lod', False)
        if hasLod:
            if "lod" not in nodeName.lower():
                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "LOD root node '%s' should contain 'lod' in it's name" % (node), margin=30)

            numNodes = 0
            nodes = cmds.listRelatives(node, fullPath=True)
            if nodes is not None:
                numNodes = len(nodes)
                for i in range(0, numNodes):
                    if "lod%d" % i not in nodes[i].lower():
                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "LOD level %d node '%s' should contain '%s' in it's name" % (i, nodes[i], "lod%d" % i), margin=30)

            lod3Distance = I3DExporter.I3DGetAttributeValue(node, 'i3D_lod3', 0)
            if lod3Distance > 0:
                if numNodes != 4:
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has 4 lod levels defined, but %d child node(s) found" % numNodes, margin=30)
            else:
                lod2Distance = I3DExporter.I3DGetAttributeValue(node, 'i3D_lod2', 0)
                if lod2Distance > 0:
                    if numNodes != 3:
                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has 3 levels defined, but %d child node(s) found" % numNodes, margin=30)
                else:
                    lod1Distance = I3DExporter.I3DGetAttributeValue(node, 'i3D_lod1', 0)
                    if lod1Distance > 0:
                        if numNodes != 2:
                            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has 2 lod levels defined, but %d child node(s) found" % numNodes, margin=30)

        shear = cmds.getAttr(node + '.shear')
        if (shear[0][0] != 0.0 or shear[0][1] != 0.0 or shear[0][2] != 0.0):
            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Shear: Run 'FreezeTransformation'!", margin=30)

        rotatePivot = cmds.getAttr(node + '.rotatePivot')
        scalePivot = cmds.getAttr(node + '.scalePivot')
        if (math.fabs(rotatePivot[0][0]) > 1.0e-10 or math.fabs(rotatePivot[0][1]) > 1.0e-10 or math.fabs(rotatePivot[0][2]) > 1.0e-10 or math.fabs(scalePivot[0][0]) > 1.0e-10 or math.fabs(scalePivot[0][1]) > 1.0e-10 or math.fabs(scalePivot[0][2]) > 1.0e-10):
            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Pivot: Run 'FreezeToPivot'!", margin=30, buttonText="Run 'FreezeToPivot'", buttonFunc=I3DUtils.freezeObjectPivot, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[12])

        isScaled = I3DExporter.I3DGetAttributeValue(node, 'i3D_scaled', False)
        scale = cmds.getAttr(node + '.scale')
        if (math.fabs(1.0 - scale[0][0]) > 0.1e-10 or math.fabs(1.0 - scale[0][1]) > 0.1e-10 or math.fabs(1.0 - scale[0][2]) > 0.1e-10):
            if not isScaled:
                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Scaled: Run 'FreezeTransformation' or set node attribute 'scale' to true!", margin=30, buttonText="Freeze Scale", buttonFunc=I3DUtils.freezeObjectScale, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[13])
        elif isScaled:
            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Scaled: Node is marked as scaled but scaling is (1,1,1)", margin=30, buttonText="Remove 'scaled' flag", buttonFunc=I3DUtils.removeObjectScaleFlag, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[14])

        mergeGroup = I3DExporter.I3DGetAttributeValue(node, 'i3D_mergeGroup', 0)
        if mergeGroup > 0:
            isRootNode = I3DExporter.I3DGetAttributeValue(node, 'i3D_mergeGroupRoot', False)
            if isRootNode:
                if mergeGroup not in self.exportSkinnedMergeRootNodes:
                    self.exportSkinnedMergeRootNodes[mergeGroup] = node
                else:
                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "RootNode for MergeGroup_%s already set!" % str(mergeGroup), margin=30)

        if I3DExporter.I3DGetAttributeValue(node, 'i3D_referenceFilename', None):
            isValid = True

            children = cmds.listRelatives(node, children=True, fullPath=True)
            if children is not None and len(children) > 0:
                for child in children:
                    if "_ignore" not in child:
                        isValid = False
                        break

            if not isValid:
                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node should not have any child nodes when i3D_referenceFilename is set", margin=30)

        I3DExporter.pluginEvent("onTransformCheck", node, self.addMessageFunc, [nodeType, xmlIdentifier], objectSpecies)

        self.__checkMaterials(node)

        if self.objectErrorCount > 0 or self.objectWarningCount > 0 or self.objectInfoCount > 0:
            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_NONE, node, buttonText="Select Object", margin=10, buttonFunc=I3DUtils.selectObject, buttonArgs=node, isHeader=True)
            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_NONE, '')

            self.__addObjectBufferToMainBuffer()

        if not I3DExporter.I3DGetAttributeValue(node, 'i3D_mergeChildren', False):
            nodes = cmds.listRelatives(node, fullPath=True)
            if nodes is not None:
                for cnode in nodes:
                    nodeType = cmds.objectType(cnode)
                    if nodeType == 'transform' or nodeType == 'joint':
                        if "_ignore" not in cnode:
                            self.__checkTransfromGroup(cnode, objectSpecies)
        else:
            self.objectCount = self.objectCount + 1

    def __checkMaterials(self, node):
        checkVertexColors = cmds.checkBoxGrp(I3DExporter.UI_CONTROL_BOOL_ERROR_CHECK_SETTINGS, q=True, v1=True)
        checkUVSets = cmds.checkBoxGrp(I3DExporter.UI_CONTROL_BOOL_ERROR_CHECK_SETTINGS, q=True, v2=True)

        shapes = cmds.listRelatives(node, shapes=True)
        if shapes is not None:
            shape = node + '|' + shapes[0]

            materials = cmds.listConnections(shape, type='shadingEngine')
            if materials is not None:
                materials = list(set(materials))

                if len(materials) > 1:
                    mergable, mismatchData = self.__getAreObjectMaterialsMergeable(node)
                    if not mergable:
                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has %d material assigned to it, which cannot be merged. Make sure the materials have the same base attributes!" % len(materials), margin=30)

                        warning = I3DUtils.getWarningFromMismatchData(mismatchData)
                        if warning is not None:
                            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, warning, margin=30)

                        if mismatchData["type"] == "Material":
                            if "object1" in mismatchData:
                                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Material '%s'" % mismatchData["object1"], margin=30, buttonText="Select faces of '%s'" % mismatchData["object1"].split("|")[-1], buttonFunc=I3DUtils.selectMergeableFacesByMaterial, buttonArgs=[shape, mismatchData["object1"]])
                            if "object2" in mismatchData:
                                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Material '%s'" % mismatchData["object2"], margin=30, buttonText="Select faces of '%s'" % mismatchData["object2"].split("|")[-1], buttonFunc=I3DUtils.selectMergeableFacesByMaterial, buttonArgs=[shape, mismatchData["object2"]])

                        if mismatchData["type"] == "Object":
                            if "object1" in mismatchData:
                                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Object '%s'" % mismatchData["object1"], margin=30, buttonText="Select '%s'" % mismatchData["object1"].split("|")[-1], buttonFunc=I3DUtils.selectObject, buttonArgs=[mismatchData["object1"]])
                            if "object2" in mismatchData:
                                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Object '%s'" % mismatchData["object2"], margin=30, buttonText="Select '%s'" % mismatchData["object2"].split("|")[-1], buttonFunc=I3DUtils.selectObject, buttonArgs=[mismatchData["object2"]])

                mergeGroup = I3DExporter.I3DGetAttributeValue(node, 'i3D_mergeGroup', 0)
                if mergeGroup > 0:
                    if mergeGroup not in self.exportSkinnedMergeNodes:
                        self.exportSkinnedMergeNodes[mergeGroup] = {'node': node}

                    # check only the first material as we assume all materials of the object are already mergeable
                    # if not, there will be a different warning already indicating it
                    mergable, mismatchData = self.__getAreObjectsMergeable(node, self.exportSkinnedMergeNodes[mergeGroup]['node'], checkFirstMaterial=True)
                    if not mergable:
                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Merge group objects cannot be merged. Make sure the materials are mergable.", margin=30)

                        warning = I3DUtils.getWarningFromMismatchData(mismatchData)
                        if warning is not None:
                            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, warning, margin=30)

                        if mismatchData["type"] == "Material":
                            if "object1" in mismatchData:
                                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Material '%s'" % mismatchData["object1"], margin=30, buttonText="Select '%s'" % mismatchData["object1"].split("|")[-1], buttonFunc=I3DUtils.selectObject, buttonArgs=[mismatchData["object1"]])
                            if "object2" in mismatchData:
                                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Material '%s'" % mismatchData["object2"], margin=30, buttonText="Select '%s'" % mismatchData["object2"].split("|")[-1], buttonFunc=I3DUtils.selectObject, buttonArgs=[mismatchData["object2"]])

                        if mismatchData["type"] == "Object":
                            if "object1" in mismatchData:
                                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Object '%s'" % mismatchData["object1"], margin=30, buttonText="Select '%s'" % mismatchData["object1"].split("|")[-1], buttonFunc=I3DUtils.selectObject, buttonArgs=[mismatchData["object1"]])
                            if "object2" in mismatchData:
                                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Object '%s'" % mismatchData["object2"], margin=30, buttonText="Select '%s'" % mismatchData["object2"].split("|")[-1], buttonFunc=I3DUtils.selectObject, buttonArgs=[mismatchData["object2"]])

                if checkVertexColors or checkUVSets:
                    shaderVarUsesVertexColor = False
                    shaderVarUsedUvSets = dict()
                    isDefaultMat = False
                    for material in materials:
                        surfaceShader = cmds.listConnections(material + '.surfaceShader')
                        if surfaceShader is None:
                            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has no material assigned to it. Assign a material!", margin=30)
                        else:
                            # determine is material is default mat
                            file_node = cmds.listConnections(surfaceShader, type='file')
                            if not file_node:
                                # material has no specular map
                                bump_node = cmds.listConnections(surfaceShader, type='bump2d')
                                if bump_node is not None:
                                    normal_map = cmds.listConnections(bump_node, type='file')
                                    if normal_map is not None:
                                        normal_texture_name = cmds.getAttr(normal_map[0] + '.fileTextureName')
                                        if normal_texture_name.endswith('default_normal.png') or normal_texture_name.endswith('default_normal.dds'):
                                            isDefaultMat = True

                            # determine if custom shader + variation use vertex color
                            customShaderPath = ''
                            if cmds.nodeType(surfaceShader[0]) == 'GLSLShader':
                                # Check that the glsl shader has a corresponding xml counterpart
                                # This is not the case for e.g. BaseShader.ogsfx
                                glslShaderPath = I3DExporter.I3DGetAttributeValue(surfaceShader[0], 'shader', None)
                                xmlShaderPath = glslShaderPath.replace('.ogsfx', '.xml')
                                if os.path.exists(xmlShaderPath):
                                    customShaderPath = xmlShaderPath
                            else:
                                customShaderPath = I3DExporter.I3DGetAttributeValue(surfaceShader[0], 'customShader', None)
                                if customShaderPath is not None and ".xml" not in customShaderPath:
                                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Material '%s' has a non xml shader assigned '%s'" % (surfaceShader[0], customShaderPath), margin=30)

                            if customShaderPath:
                                # print(customShaderPath)
                                customShaderVariationName = I3DUtils.getAttributeValueAsStr(surfaceShader[0], 'customShaderVariation', 'base')
                                shader = ShaderUtil.getShader(customShaderPath, I3DExporter.I3DGetGamePath(), os.path.dirname(cmds.file(query=True, sceneName=True)))
                                if shader is not None:
                                    shaderVarUsesVertexColor = shader.getVariationUsesVertexAttribute(customShaderVariationName, "color")
                                    for uvIndex in range(1, 3):
                                        if shader.getVariationUsesVertexAttribute(customShaderVariationName, "uv{}".format(uvIndex)):
                                            shaderVarUsedUvSets[uvIndex] = True

                    if checkVertexColors:
                        # if shader variation does not use vertex color and is not using the default material (e.g. effect shapes) => check node for present vertex colors
                        if not shaderVarUsesVertexColor:
                            if not isDefaultMat and I3DExporter.I3DGetNodeHasVertexColors(node):
                                if customShaderPath:
                                    if shader:
                                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has vertex colors set which are not used by current shader '{}' variation:{}".format(customShaderPath, customShaderVariationName), margin=30, buttonText="Remove vertex colors", buttonFunc=I3DUtils.removeVertexColors, buttonArgs=node, buttonRemoveLine=True, buttonColor=COLORS[1])
                                        self.vertexColorNodes.append(node)
                                    else:
                                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has vertex colors and assigned custom shader '{}' could not be found. Please fix shader path first".format(customShaderPath), margin=30)
                                else:
                                    self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has vertex colors set but no custom shader assigned which uses them", margin=30, buttonText="Remove vertex colors", buttonFunc=I3DUtils.removeVertexColors, buttonArgs=node, buttonColor=COLORS[1])
                                    self.vertexColorNodes.append(node)

                        elif not I3DExporter.I3DGetNodeHasVertexColors(node):
                            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "missing vertex colors required by shader '{}' variation '{}'".format(customShaderPath, customShaderVariationName), margin=30)

                    if checkUVSets:
                        # check for obsolete uv sets
                        for uvSetIndex in range(1, 3):
                            if uvSetIndex not in shaderVarUsedUvSets:
                                # check if node has uvs not used by shader variation
                                nodeUvSet = I3DExporter.I3dGetNodeUvSetN(node, uvSetIndex)
                                if nodeUvSet and not isDefaultMat:
                                    if customShaderPath:
                                        if shader:
                                            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has additional uv set '{}' (index {}) is not used by current shader '{}' variation:{}".format(nodeUvSet, uvSetIndex, customShaderPath, customShaderVariationName), margin=30, buttonText="Remove uv set", buttonFunc=I3DUtils.removeUvSet, buttonArgs=(node, nodeUvSet), buttonRemoveLine=True, buttonColor=COLORS[3])
                                        else:
                                            self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has additional uv set '{}' (index {}) and assigned custom shader '{}' could not be found. Please fix shader path first".format(nodeUvSet, uvSetIndex, customShaderPath), margin=30)
                                    else:
                                        self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "Node has additional uv set '{}' (index {}) but no custom shader assigned which uses it".format(nodeUvSet, uvSetIndex), margin=30, buttonText="Remove uv set", buttonFunc=I3DUtils.removeUvSet, buttonArgs=(node, nodeUvSet), buttonRemoveLine=True, buttonColor=COLORS[4])


                            elif I3DExporter.I3dGetNodeUvSetN(node, uvSetIndex) is None:
                                self.__addMessageToObjectBuffer(I3DExporter.MESSAGE_TYPE_WARNING, "missing additional uv set {} required by shader '{}' variation '{}'".format(uvSetIndex, customShaderPath, customShaderVariationName), margin=30)

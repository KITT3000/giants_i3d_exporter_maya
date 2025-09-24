#
# I3DExport
# Handles the calling of the external mll exporter to do the conversion to i3d
#
# @created 24/01/2024
# @author Stefan Maurus
#
# Copyright (C) GIANTS Software GmbH, Confidential, All Rights Reserved.
#

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya

import I3DExporter
import datetime
import re
import os


class I3DExport:
    OPTION_NAME_TO_PARAMETER = {
        "filename": "file",
        "ik": "ik",
        "animation": "animation",
        "shapes": "shapes",
        "nurbscurves": "nurbscurves",
        "lights": "lights",
        "cameras": "cameras",
        "userattributes": "userattributes",
        "defaultcameras": "dcams",
        "particlesystems": "particlesystems",
        "exportBinaryFiles": "binaryfiles",
        "ignoreBindPoses": "ignoreBindPoses",
        "normals": "n",
        "colors": "c",
        "texCoords": "uvs",
        "skinWeights": "sw",
        "mergeGroups": "mg",
        "verbose": "v",
        "exportSelection": "selection",
        "relativePaths": "rp",
        "floatEpsilon": "fe",
        "gameRelativePath": "grp",
        "gamePath": "gp",
    }

    def __init__(self, handler):
        self.handler = handler
        self.handler.addProgressSteps(90)

        self.warningCount = 0
        self.errorCount = 0

        self.options = {}

        self.options["filename"] = ""
        self.options["ik"] = False
        self.options["animation"] = False
        self.options["shapes"] = False
        self.options["nurbscurves"] = False
        self.options["lights"] = False
        self.options["cameras"] = False
        self.options["userattributes"] = False
        self.options["defaultcameras"] = False
        self.options["particlesystems"] = False
        self.options["exportBinaryFiles"] = False
        self.options["ignoreBindPoses"] = False
        self.options["objectDataTexture"] = False
        self.options["normals"] = False
        self.options["colors"] = False
        self.options["texCoords"] = False
        self.options["skinWeights"] = False
        self.options["mergeGroups"] = False
        self.options["verbose"] = False
        self.options["exportSelection"] = False
        self.options["relativePaths"] = False
        self.options["floatEpsilon"] = False
        self.options["gameRelativePath"] = False
        self.options["gamePath"] = ""

    def setOption(self, optionName, value):
        if optionName in self.options:
            self.options[optionName] = value

    def doExport(self):
        global exportWarningCount, exportErrorCount
        exportWarningCount = 0
        exportErrorCount = 0

        I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, '')
        I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, 'Game')
        I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, 'Location: ' + self.options["gamePath"].replace("$", "/"), color="#C5C5C5", margin=15)
        I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, 'Relative Paths: ' + str(self.options["gameRelativePath"]), color="#C5C5C5", margin=15)
        I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, '')

        def callback(nativeMsg, messageType, data):
            global exportWarningCount, exportErrorCount
            # cut tailing white spaces
            if nativeMsg[-1:] == "\n":
                nativeMsg = nativeMsg[:-1]

            if messageType == OpenMaya.MCommandMessage.kWarning:
                exportWarningCount = exportWarningCount + 1
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_WARNING, nativeMsg)
            elif messageType == OpenMaya.MCommandMessage.kError:
                exportErrorCount = exportErrorCount + 1
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_ERROR, nativeMsg)

        command = 'I3DExporter'
        for optionName, value in self.options.items():
            if optionName in self.OPTION_NAME_TO_PARAMETER:
                if value is True:
                    command += ' -%s' % (self.OPTION_NAME_TO_PARAMETER[optionName])
                elif isinstance(value, str):
                    command += ' -%s "%s"' % (self.OPTION_NAME_TO_PARAMETER[optionName], value)
        print(command)

        try:
            fwrite = open(self.options["filename"], "w")
            fwrite.close()
        except IOError:
            I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_ERROR, 'Could not open file: ' + self.options["filename"])
            return 1

        if self.options["objectDataTexture"]:
            self.handler.updateProgress("Export Object Data...", steps=30)
            try:
                start = datetime.datetime.now()

                import exportObjectDataTexture
                exportObjectDataTexture.exportObjectDataTexture()

                end = datetime.datetime.now()
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, "Exported object data textures in %.3fsec" % (end - start).total_seconds())
            except:
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_ERROR, "Can't execute exportObjectDataTexture")

        self.handler.updateProgress("Start Export...", steps=30)

        callbackId = OpenMaya.MCommandMessage.addCommandOutputCallback(callback, None)
        mel.eval(command)
        OpenMaya.MMessage.removeCallback(callbackId)

        self.handler.updateProgress("Add custom attributes...", steps=30)
        self.__exportCustomAttributes(self.options["filename"])

        self.warningCount = exportWarningCount
        self.errorCount = exportErrorCount

        def buttonFuncExploreDir(unused, args):
            os.startfile(os.path.dirname(self.options["filename"]))
        I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, 'Export to: ' + self.options["filename"], buttonText="Explore Directory", buttonFunc=buttonFuncExploreDir)

        def buttonFuncOpenI3d(unused, args):
            os.startfile(self.options["filename"])
        I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, '', buttonText="Open exported i3d", buttonFunc=buttonFuncOpenI3d)

    def __exportCustomAttributes(self, filename):
        nodes = cmds.ls(assemblies=True)
        for node in nodes:
            nodeType = cmds.objectType(node)
            if (nodeType == 'transform' and node != 'top' and node != 'side' and node != 'front' and node != 'persp'):
                self.__exportCustomAttributesByNode(filename, node)

        return

    def __exportCustomAttributesByNode(self, filename, node):
        shapes = cmds.listRelatives(node)
        if shapes is not None:
            for i in range(0, len(shapes)):
                shapes[i] = node + '|' + shapes[i]

            materials = cmds.listConnections(shapes, type='shadingEngine')
            if materials is not None:
                materials = list(set(materials))
                for material in materials:
                    surfaceShader = cmds.listConnections(material + '.surfaceShader')
                    if surfaceShader is not None:
                        for shader in surfaceShader:
                            if I3DExporter.I3DAttributeExists(shader, 'i3D_reflectionMap_resolution'):
                                resolution = I3DExporter.I3DGetAttributeValue(shader, 'i3D_reflectionMap_resolution', '0')
                                self.__addCustomAttributeToMaterial(filename, shader, 'Reflectionmap', 'resolution', resolution)
                            if I3DExporter.I3DAttributeExists(shader, 'i3D_reflectionMap_wrap'):
                                state = I3DExporter.I3DGetAttributeValue(shader, 'i3D_reflectionMap_wrap', 'false')
                                self.__addCustomAttributeToMaterial(filename, shader, 'Reflectionmap', 'wrap', state)
                            if I3DExporter.I3DAttributeExists(shader, 'i3D_texture_wrap'):
                                state = I3DExporter.I3DGetAttributeValue(shader, 'i3D_texture_wrap', 'false')
                                self.__addCustomAttributeToMaterial(filename, shader, 'Texture', 'wrap', state)
                            if I3DExporter.I3DAttributeExists(shader, 'i3D_customMap_wrap'):
                                wrapText = I3DExporter.I3DGetAttributeValue(shader, 'i3D_customMap_wrap', 'false')
                                tokens = wrapText.split(' ')
                                if len(tokens) == 2:
                                    textureName = 'Custommap name="' + tokens[0] + '"'
                                    self.__addCustomAttributeToMaterial(filename, shader, textureName, 'wrap', tokens[1])
                                else:
                                    I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_ERROR, 'Invalid customMap_Wrap value. Syntax: <customMapName> <true/false>')

        nodes = cmds.listRelatives(node)
        if nodes is not None:
            for cnode in nodes:
                cnode = node + '|' + cnode
                nodeType = cmds.objectType(cnode)
                if nodeType == 'transform':
                    self.__exportCustomAttributesByNode(filename, cnode)

        return

    def __addCustomAttributeToMaterial(self, filename, materialName, textureType, attributeName, attributeValue):
        file = open(filename, 'r')
        content = file.readlines()
        file.close()

        material = '.*<Material.*name="' + materialName + '".*'
        texture = '<' + textureType + ' '
        pattern = attributeName + '="[a-zA-Z0-9]*"'
        textureReplacement = attributeName + '="' + attributeValue + '"'

        found = False

        for i in range(0, len(content)):
            line = content[i]
            materialMatch = re.match(material, line)

            if materialMatch is not None:
                found = True

            if found:
                textureMatch = re.match('.*' + texture + '.*', line)
                if textureMatch is not None:
                    result = re.match('.*(' + pattern + ').*', line)
                    if result is not None:
                        print('Attribute exist (' + str(i) + '): ' + line)
                        line = line.replace(result.group(1), textureReplacement)
                        print('Replaced attribute ' + str(i) + ': ' + line)
                    else:
                        newTexture = texture + textureReplacement + ' '
                        line = line.replace(texture, newTexture)
                        print('Added attribute (' + str(i) + '): ' + line)
                    found = False
            content[i] = line

        file = open(filename, 'w')
        for line in content:
            file.write(line)
        file.close()

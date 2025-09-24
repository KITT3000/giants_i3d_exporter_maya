#
# XMLParser.py
# Wrapper around python xml minidom xml parser to have simple access to xml elements
#
# @author   Stefan Maurus
# @date     30/05/2018
#

from maya import cmds
from xml.dom.minidom import parse

import os


def loadXMLFile(path):
    if path is not None:
        if os.path.isfile(path):
            return parse(path)


def getXMLValue(xmlFile, path, returnNum=False):
    elementToCheck = xmlFile
    parts = path.split("#")
    pathParts = parts[0].split(".")
    defaultRet = None

    for pathPart in pathParts:
        nodeIndex = 0

        if "(" in pathPart:
            start = pathPart.find("(")
            end = pathPart.find(")")
            nodeIndex = int(pathPart[start+1:end])
            pathPart = pathPart[0:start]

        nodes = []
        for childToCheck in elementToCheck.childNodes:
            if childToCheck.nodeType == childToCheck.ELEMENT_NODE:
                if childToCheck.tagName == pathPart:
                    nodes.append(childToCheck)

        # default return value is the number of children
        if returnNum:
            defaultRet = len(nodes)

        if len(nodes) > nodeIndex:
            elementToCheck = nodes[nodeIndex]

    if not returnNum:
        if len(parts) > 1:
            attributes = elementToCheck.attributes.keys()
            for a in attributes:
                if a == parts[1]:
                    object = elementToCheck.attributes[parts[1]]
                    return object.value
        else:
            if len(elementToCheck.childNodes) > 0:
                node = elementToCheck.childNodes[0]
                if node.nodeType == node.TEXT_NODE:
                    return node.data

    return defaultRet


def getElementExists(xmlFile, key):
    value = getXMLValue(xmlFile, key, True)
    return value is not None and value != 0


def getNumberOfElements(xmlFile, key):
    return getXMLValue(xmlFile, key, True)


def getXMLInt(xmlFile, key):
    value = getXMLValue(xmlFile, key)
    if value is None:
        return None
    else:
        return int(value)


def getXMLFloat(xmlFile, key):
    value = getXMLValue(xmlFile, key)
    if value is None:
        return None
    else:
        return float(value)


def getXMLNode(xmlFile, key, i3dMappings):
    value = getXMLValue(xmlFile, key)
    if value is None:
        return None
    else:
        if value in i3dMappings:
            if i3dMappings[value] is not None:
                return i3dMappings[value]

        return value


def getOverwrittenParameter(xmlFile, key1, key2, keyExt, func):
    if keyExt is None or key1 is None:
        return None

    if key2 is None:
        return func(xmlFile, key1 + keyExt)

    value1 = getXMLValue(xmlFile, key1 + keyExt)
    value2 = getXMLValue(xmlFile, key2 + keyExt)
    if value1 is not None:
        if value2 is None:
            return func(xmlFile, key1 + keyExt)
        if value2 == "-":
            return None
        if value2 is not None:
            return func(xmlFile, key2 + keyExt)

    if value2 is not None and value2 != "-":
        return func(xmlFile, key2 + keyExt)


def getVectorNFromXML(xmlFile, key, numValues=None):
    valueStr = getXMLValue(xmlFile, key)
    if valueStr is not None:
        values = str(valueStr).split(" ")
        for i in range(0, len(values)):
            try:
                values[i] = float(values[i])
            except ValueError:
                values[i] = 0

        if numValues is not None:
            if len(values) != numValues:
                return None

        return values

    return None


def loadI3DMappingsFromXML(xmlFile):
    i3dMappings = {}
    numElements = getNumberOfElements(xmlFile, "vehicle.i3dMappings.i3dMapping")
    for i in range(0, numElements):
        id = getXMLValue(xmlFile, "vehicle.i3dMappings.i3dMapping(%d)#id" % (i))
        node = getXMLValue(xmlFile, "vehicle.i3dMappings.i3dMapping(%d)#node" % (i))

        i3dMappings[id] = node

    return i3dMappings


def resolveWronglySavedMayaFile():
    sceneName = cmds.file(q=True, sceneName=True)
    if sceneName == "":
        filePath = cmds.file(q=True, expandName=True)
        if "untitled" not in filePath:
            cmds.file(rename=filePath)
            sceneName = cmds.file(q=True, sceneName=True)
            cmds.warning('Scene name not set. Setting it to current file location.')


def getAbsolutPathFromMayaFile(path):
    resolveWronglySavedMayaFile()

    mayaFilePath = str(os.path.dirname(cmds.file(q=True, sn=True)).replace('\\', '/'))

    return mayaFilePath + "/" + path


def getVehicleConfigFiles(raw=False):
    files = []
    if cmds.objExists("I3DExportSettings"):
        configFilesStr = cmds.getAttr('I3DExportSettings.i3D_exportXMLConfigFile')

        configFiles = configFilesStr.split(";")
        for configFile in configFiles:
            if raw:
                files.append(getAbsolutPathFromMayaFile(configFile))
            else:
                files.append(loadXMLFile(getAbsolutPathFromMayaFile(configFile)))

    return files


def getVehicleConfigFile():
    files = getVehicleConfigFiles()
    if len(files) > 0:
        return files[0]

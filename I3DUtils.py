import math
import os
import re
import fnmatch
import xml.etree.ElementTree as ET
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.mel as mel
import I3DExporter

def transformPoint(point, mat):
    return [mat[0]*point[0] + mat[4]*point[1] + mat[8]*point[2] + mat[12],
            mat[1]*point[0] + mat[5]*point[1] + mat[9]*point[2] + mat[13],
            mat[2]*point[0] + mat[6]*point[1] + mat[10]*point[2] + mat[14]]

def transformDirection(dir, mat):
    return [mat[0]*dir[0] + mat[4]*dir[1] + mat[8]*dir[2],
            mat[1]*dir[0] + mat[5]*dir[1] + mat[9]*dir[2],
            mat[2]*dir[0] + mat[6]*dir[1] + mat[10]*dir[2]]

def invertTransformationMatrix(m):
    ret = [m[0],m[4],m[8],0.0,
           m[1],m[5],m[9],0.0,
           m[2],m[6],m[10],0.0]

    ret.append(-(m[12]*ret[0]+m[13]*ret[4]+m[14]*ret[8]))
    ret.append(-(m[12]*ret[1]+m[13]*ret[5]+m[14]*ret[9]))
    ret.append(-(m[12]*ret[2]+m[13]*ret[6]+m[14]*ret[10]))
    return ret


def vectorLength(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

def vectorDot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def vectorCross(a, b):
    return [a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0]]

def vectorNorm(v):
    length = vectorLength(v)
    if length == 0:
        length = 1

    return [v[0]/length,
            v[1]/length,
            v[2]/length
           ]

def filterHex(str):
    '''Removes all non-hex characters from a string and ouputs a plain hex string without '0x' prefix'''
    str = str.replace("0x", "")
    allowedChars = "ABCDEFabcdef012345678"
    return "".join(filter(lambda x: x in allowedChars, str))

def filterHexToUpper(s):
    '''Removes all non-hex characters from a string and ouputs a plain uppercase hex string without '0x' prefix'''
    return filterHex(str(s)).upper()

def getFiles(path, filter):
    if filter is None:
        filter = '*'
    matches = []
    for root, dirnames, filenames in os.walk(path):
      for filename in fnmatch.filter(filenames, filter):
        matches.append(os.path.join(root, filename))
    return matches

def getFilesInDir(path, filter):
    if filter is None:
        filter = '*'
    matches = []
    for filename in fnmatch.filter(os.listdir(path), filter):
        matches.append(filename)

    return matches

def loadTemplateParameterFile(xmlPath, templateParameters):
    try:
        tree = ET.parse(xmlPath)
    except ET.ParseError as err:
        showWarning("Failed to load parameter templates from '%s': %s" % (xmlPath, err))
        return None

    templateParameters.append('parentTemplate')

    root = tree.getroot()
    result = {'id': root.get('id'), 'name': root.get('name'), 'parentTemplateFile': root.get('parentTemplateFilename'), 'templates': {template.get('name'): {templateParameter: template.get(templateParameter) for templateParameter in templateParameters} for template in root.findall('template')}}
    return result

def getShaderInfo(shaderPath):
    shaderInfo = {}
    tree = None
    try:
        tree = ET.parse(shaderPath)
    except ET.ParseError as err:
        cmds.warning("Failed to load shader '%s': %s" % (shaderPath, err))
        return None

    ogsfxShaderPath = shaderPath.replace('.xml', '.ogsfx')
    if (os.path.exists(ogsfxShaderPath)):
        shaderInfo['hasGLSLShader'] = True
    else:
        shaderInfo['hasGLSLShader'] = False

    root = tree.getroot()

    # Load parameter templates
    parameterTemplates = root.find('ParameterTemplates')
    templateNameToIndexMap = {}
    if not parameterTemplates is None:
        shaderInfo['parameterTemplates'] = []
        for parameterTemplate in parameterTemplates.findall('ParameterTemplate'):
            templateId = parameterTemplate.get('id')
            templateNameToIndexMap[templateId] = len(shaderInfo['parameterTemplates'])
            shaderInfo['parameterTemplates'].append({'id': templateId, 'templateFile': parameterTemplate.get('filename'), 'parameters': [], 'textures': []})

    # Load parameters
    parameters = root.find('Parameters')
    if not parameters is None:
        shaderInfo['parameters'] = []

        for parameter in parameters.findall('Parameter'):
            name = parameter.get('name')
            target = parameter.get('target')
            type = parameter.get('type')
            group = parameter.get('group')
            minValue = getNoNone(parameter.get('minValue'), '1 1 1 1')
            maxValue = getNoNone(parameter.get('maxValue'), '1 1 1 1')
            defaultValue = getNoNone(parameter.get('defaultValue'), '1 1 1 1')
            # TODO(jdellsperger): maybe set name = separateMaterialName if
            # separateMaterialName exists and the add attribute 'isSeparateMaterial'
            # or so, to indicate special treatment
            separateMaterialName = parameter.get('separateMaterialName')
            templateId = parameter.get('template')

            parameterInfo = {
                'name': name,
                'target': target,
                'minValue': minValue,
                'maxValue': maxValue,
                'defaultValue': defaultValue,
                'separateMaterialName': separateMaterialName,
                'group': group,
                'isTexture': False
            }

            if not templateId is None and not templateId in templateNameToIndexMap:
                showWarning("Template id '%s' on parameter '%s' has no corresponding ParameterTemplate defined" % (templateId, name))
                continue

            arraySize = parameter.get('arraySize')
            if not arraySize is None:
                defaults = {}
                for default in parameter.findall('Default'):
                    index = default.get('index')
                    defaults[int(index)] = default.text

                if separateMaterialName is None:
                    for i in range(0, int(arraySize)):
                        default = defaultValue
                        if i in defaults:
                            default = defaults[i]
                        # needs a copy, otherwise the same reference is used
                        arrayParameterInfo = parameterInfo.copy()
                        arrayParameterInfo['name'] = name + str(i)
                        arrayParameterInfo['defaultValue'] = default
                        if not templateId is None:
                            shaderInfo['parameterTemplates'][templateNameToIndexMap[templateId]]['parameters'].append(parameterInfo)
                        else:
                            shaderInfo['parameters'].append(arrayParameterInfo)
                else:
                    parameterInfo['separateDefaultValues'] = defaults
                    if not templateId is None:
                        shaderInfo['parameterTemplates'][templateNameToIndexMap[templateId]]['parameters'].append(parameterInfo)
                    else:
                        shaderInfo['parameters'].append(parameterInfo)
            else:
                if not templateId is None:
                    shaderInfo['parameterTemplates'][templateNameToIndexMap[templateId]]['parameters'].append(parameterInfo)
                else:
                    shaderInfo['parameters'].append(parameterInfo)

    textures = root.find('Textures')
    if not textures is None:
        shaderInfo['textures'] = []
        for texture in textures.findall('Texture'):
            name = texture.get('name')
            group = texture.get('group')
            separateMaterialName = texture.get('separateMaterialName')
            defaultColorProfile = texture.get('defaultColorProfile')
            defaultFilename = texture.get('defaultFilename')
            templateId = texture.get('template')
            textureInfo = {'name': name, 'defaultColorProfile': defaultColorProfile, 'defaultValue': defaultFilename, 'separateMaterialName': separateMaterialName, 'group': group, 'isTexture': True}

            if not templateId is None and not templateId in templateNameToIndexMap:
                showWarning("Template id '%s' on texture '%s' has no corresponding ParameterTemplate defined" % (templateId, name))
                continue

            if not templateId is None:
                shaderInfo['parameterTemplates'][templateNameToIndexMap[templateId]]['parameters'].append(textureInfo)
            else:
                shaderInfo['textures'].append(textureInfo)

    variations = root.find('Variations')
    if not variations is None:
        shaderInfo['variations'] = []
        for variation in variations.findall('Variation'):
            name = variation.get('name')
            groups = variation.get('groups')
            shaderInfo['variations'].append({'name': name, 'groups': groups})

    return shaderInfo

def getNoNone(value, default):
    if value is None:
        return default
    return value

def getRelativePath(root, path):
    return os.path.relpath(root, path)

def getMergePaths(root, path):
    return os.path.abspath(os.path.join(root, path))

def getRelativeShaderPath(shaderPath):
    '''Gets relative path to shader file starting from maya file'''
    result = ""
    mayaFile = cmds.file(q=True,sn=True)
    mayaFile = os.path.dirname(mayaFile)
    if ( not  mayaFile ):
        return result
    if ( not ( os.path.splitdrive(shaderPath)[0] == os.path.splitdrive(mayaFile)[0] ) ):
        return result
    result  = os.path.relpath( shaderPath, mayaFile )
    result  = result.replace( "\\","/")
    return result


def linearInternalToUIVector( linear ):
    return [linearInternalToUI(linear[0]), linearInternalToUI(linear[1]), linearInternalToUI(linear[2])]

def linearUIToInternal( linear ):
    factor = 1.0
    pref = cmds.currentUnit(q=True, l=True)
    if ( pref == 'mm' ): factor = 0.1
    if ( pref == 'm' ): factor = 100.0
    if ( pref == 'inch' ): factor = 2.54
    if ( pref == 'ft' ): factor = 30.48
    if ( pref == 'yard' ): factor = 91.44
    return (linear * factor)

def linearUIToInternalVector( linear ):
    return [linearUIToInternal(linear[0]), linearUIToInternal(linear[1]), linearUIToInternal(linear[2])]

def linearInternalToUI( linear ):
    factor = 1.0
    pref = cmds.currentUnit(q=True, l=True)
    if ( pref == 'mm' ): factor = 10.0
    if ( pref == 'm' ): factor = 0.01
    if ( pref == 'inch' ): factor = 0.3937007874
    if ( pref == 'ft' ): factor = 0.03280839895
    if ( pref == 'yard' ): factor = 0.01093613298
    return ( linear * factor )

def angleUIToInternal(angle):
    pref = cmds.currentUnit(q=True, a=True)
    if ( pref == 'deg' ):  angle = angle * 0.0174532925
    return angle

def angleInternalToUI(angle):
    pref = cmds.currentUnit(q=True, a=True)
    if ( pref == 'deg' ): angle = angle * 57.29577951308
    return angle

def getIndexPath(node):
    indexPath = str(getCurrentNodeIndex(node))

    currentNode = node
    while True:
        parent = cmds.listRelatives(currentNode, parent=True, fullPath=True)
        if parent is None:
            break
        indexPath = str(getCurrentNodeIndex(parent[0])) + '|' + indexPath
        currentNode = parent[0]

    if indexPath.find('|') != -1:
        indexPath = indexPath.replace('|', '>', 1)
    else:
        indexPath = indexPath + '>'

    return indexPath

def getObjectByIndex(indexPath, surpressWarning=False):
    def analyseIndexPath(path):
        if path.find(">") > -1:
            indexParts = path.split(">")
            component = indexParts[0]
            childs = indexParts[1].split("|")

            return component, childs
        else:
            childs = path.split("|")
            return childs[0], childs[1:]

    def getValidChilds(parent):
        valid = []
        childs = cmds.listRelatives(parent, c=True, f=True)
        if childs is not None:
            for child in childs:
                if cmds.nodeType(child) != "mesh":
                    valid.append(child)
        return valid

    component, childs = analyseIndexPath(indexPath)
    components = getComponents()
    component = components[int(component)]

    currentObject = component
    for child in childs:
        if child != '':
            currentChilds = getValidChilds(currentObject)
            if int(child) >= len(currentChilds):
                if not surpressWarning:
                    print("Could not find given index '" + indexPath + "'!")

                if len(currentChilds) > 0:
                    currentObject = currentChilds[len(currentChilds)-1]
                break
            currentObject = currentChilds[int(child)]

    return currentObject

def getCurrentNodeIndex(node):
    parent = cmds.listRelatives(node, parent=True, fullPath=True)
    elements = None
    if not parent is None:
        elements = cmds.listRelatives(parent, children=True, type='transform', fullPath=True)
    else:
        elements = cmds.ls(assemblies=True, long=True)
    i = -1
    if not elements is None:
        for elem in elements:
            if not isDefaultCamera(elem):
                i = i + 1
            if elem == node:
                break

    return i

def getParent(node):
    parents = cmds.listRelatives(node, p=True, pa=True, f=True)
    parent = None
    if not parents is None:
        parent = parents[0]

    return parent

def isDefaultCamera(node):
    try:
        return cmds.camera(node, q=True, startupCamera=True)
    except:
        return False

def isCamera(node):
    return cmds.nodeType(cmds.listRelatives(node, s=True, pa=True)) == 'camera'

def isShape(node):
    if node.find("Shape") > -1:
        return True
    else:
        return False

def getComponents():
    valid = []
    objects = cmds.ls(l=True)

    for object in objects:
        childs = object.split("|")
        if len(childs) == 2:
            if not isCamera(object) and not isShape(object):
                valid.append(object)

    return valid

def getMeshVolume(node):
    if cmds.listRelatives(node, shapes=True) is None:
        return 0

    selection = cmds.ls(selection=True)

    # based on http://www.vfxoverflow.com/questions/getting-the-volume-of-an-arbitrary-closed-mesh
    duplicate = cmds.duplicate(node, returnRootsOnly=True, renameChildren=True, inputConnections=False, upstreamNodes=False)
    children = cmds.listRelatives(duplicate, type='transform', fullPath=True)
    if not children is None:
        for child in children:
            # print("getMeshVolume() Delete " + child)
            cmds.delete(child)

    cmds.makeIdentity(duplicate, apply=True, t=True, r=True, s=True, n=False)
    cmds.polyTriangulate(duplicate)
    triangles = cmds.ls(duplicate[0]+'.f[*]', flatten=True)
    volume = 0
    for triangle in triangles:
        triVolume = 0
        triVertices = cmds.polyListComponentConversion(triangle, tv=True)
        triVertices = cmds.ls(triVertices, flatten=True)

        if len(triVertices) != 3:
            cmds.error(triangle + " is not a triangle")

        v1 = cmds.pointPosition(triVertices[0], w=True)
        v2 = cmds.pointPosition(triVertices[1], w=True)
        v3 = cmds.pointPosition(triVertices[2], w=True)

        res = cmds.polyInfo(triangle, fn=True)

        buff = res[0].split(":")
        buff = buff[1].split(" ")
        vector = [float(buff[1]), float(buff[2]), float(buff[3])]
        faceNormal = vectorNorm(vector)
        area = abs(((v1[0])*((v3[1])-(v2[1])))+((v2[0])*((v1[1])-(v3[1])))+((v3[0])*((v2[1])-(v1[1])))) *0.5
        triVolume = 0
        triVolume = ((v1[2] + v2[2] + v3[2]) / 3.0) * area
        if ((faceNormal[2]) < 0):
            triVolume = -triVolume

        volume = volume + triVolume

    cmds.delete(duplicate)

    cmds.select(selection)

    return volume

def getSelectedObjects():
    selection = []

    objects = cmds.ls(sl=True)
    for object in objects:
        object = object.split('.')[0]

        # get parent transform if we got only the mesh
        if cmds.objectType(object) == "mesh":
            object = cmds.listRelatives(object, type='transform', p=True)[0]

        if object not in selection:
            selection.append(object)

    return selection


def showWarning(text):
    if hasattr(cmds, 'warning'):
        cmds.warning(text)
    else:
        print(text)


def hasSkinning(object):
    connections = cmds.listConnections(object)
    if connections is not None:
        for connection in connections:
            if 'skinCluster' in connection:
                return True

    childObjects = cmds.listRelatives(object, c=True, f=True)
    if childObjects is not None:
        for childObject in childObjects:
            if hasSkinning(childObject):
                return True

    return False


def freezeToPivot(unused):
    nodes = getSelectedObjects()

    if(len(nodes) == 0):
        showWarning('Nothing selected!')
        return

    for node in nodes:
        doFreezeToPivot(node)


# helper function for freezeToPivot
def doFreezeToPivot(node):
    if not hasSkinning(node):
        localPivotPos = cmds.xform(node, q=True, sp=True, os=True)
        localPosition = cmds.xform(node, q=True, t=True, os=True)
        localRotation = cmds.xform(node, q=True, ro=True, eu=True)
        children = cmds.listRelatives(node, c=True, pa=True, ni=True, type='transform')

        matrix = []
        if children is not None:
            for child in children:
                localRotationChild = cmds.xform(child, q=True, ro=True, eu=True)
                matrix.append(localRotationChild)

        cmds.move(-localPivotPos[0], -localPivotPos[1], -localPivotPos[2], node, a=True, os=True, moveXYZ=True)

        try:
            cmds.makeIdentity(node, apply=True, t=True, r=False, s=False, n=False)
            cmds.xform(node, os=True, pivots=[0, 0, 0])
            cmds.move(localPosition[0]+localPivotPos[0], localPosition[1]+localPivotPos[1], localPosition[2]+localPivotPos[2], node, a=True, os=True, moveXYZ=True)

            if children is not None:
                i = 0
                for child in children:
                    cmds.rotate(matrix[i][0], matrix[i][1], matrix[i][2], child, a=True, eu=True)
                    i = i + 1

            cmds.rotate(localRotation[0], localRotation[1], localRotation[2], node, a=True, eu=True)

            if children is not None:
                for child in children:
                    doFreezeToPivot(child)
        except RuntimeError as err:
            showWarning("Error while freezingPivot of object '%s'!" % node)
            print(err)
    else:
        showWarning("Could not freezingPivot object '%s' or any children, because it is skinned or is a joint!" % node)


def getSpeciesFromXMLs(xmlFilesStr):
    types = ["VEHICLE", "PLACEABLE", "HANDTOOL"]
    if xmlFilesStr != "":
        xmlFiles = xmlFilesStr.split(';')
        for xmlFile in xmlFiles:
            mayaFilePath = str(os.path.dirname(cmds.file(q=True, sn=True)).replace('\\', '/'))
            xmlFile = getMergePaths(mayaFilePath, xmlFile)

            if os.path.isfile(xmlFile):
                file = open(xmlFile, 'r')
                if file is not None:
                    lines = file.readlines()
                    file.close()

                    for line in lines:
                        if line.find('<species>') >= 0:
                            for type in types:
                                if line.upper().find(type) >= 0:
                                    return type

    return "VEHICLE"


def changeSkinningMethod(node, unused):
    cmds.skinCluster(node, e=True, sm=1)  # dual quaternion


def removeObjectFromMergeGroup(node, unused):
    I3DExporter.I3DSaveAttributeInt(node, 'i3D_mergeGroup', 0)


def removeObjectStaticFlag(node, unused):
    I3DExporter.I3DSaveAttributeBool(node, 'i3D_static', False)
    I3DExporter.I3DSaveAttributeBool(node, 'i3D_collision', False)


def updateObjectCollisionMask(node, unused):
    '''
    Checks if node uses legacy "i3D_collisionMask" attribute and tries to find mapping defined in CollisionMaskFlags instance
    If mapping is found only attribute is removed and new ones are set.
    Returns success bool and message to use in UI, e.g. after pressing which invoked this function
    '''

    if I3DExporter.colMaskFlags is None:
        cmds.warning("I3DUtil: Unable to update collision mask, CollisionMaskFlags in I3DExporter is not loaded")
        return False, "Unable to update collision mask, CollisionMaskFlags in I3DExporter is not loaded"

    oldMask = I3DExporter.I3DGetAttributeValue(node, 'i3D_collisionMask', None)
    if oldMask is None:
        # old mask might be removed when button is pressed for instanced objects, check to avoid None error
        group = I3DExporter.I3DGetAttributeValue(node, 'i3D_collisionFilterGroup', None)
        mask = I3DExporter.I3DGetAttributeValue(node, 'i3D_collisionFilterMask', None)
        if group is not None and mask is not None:
            return True, "Was already updated to group {} and mask {}".format(group, mask)
        return False, "Attribute 'i3D_collisionMask' not set, unable to convert"

    rules = I3DExporter.colMaskFlags.getConversionRules(oldMask)
    if rules is None:
        cmds.warning("No conversion rule found for mask '{}'".format(oldMask))
        return False, "Error: No conversion rule for mask '{}'. Please set new collision masks in Attributes".format(oldMask)

    for rule in rules:
        # search for matching rule
        if rule['isTrigger'] and not I3DExporter.I3DGetAttributeValue(node, 'i3D_trigger', False):
            continue

        # replace old attribute with new one
        I3DExporter.I3DRemoveAttribute(node, 'i3D_collisionMask')

        groupHex = hex(rule['group'])
        I3DExporter.I3DSaveAttributeHex(node, 'i3D_collisionFilterGroup', groupHex)
        maskHex = hex(rule['mask'])
        I3DExporter.I3DSaveAttributeHex(node, 'i3D_collisionFilterMask', maskHex)

        # check if there is a matching preset to display for the user as reference/validation
        preset = I3DExporter.colMaskFlags.getPresetByMasks(rule['group'], rule['mask'])
        presetName = "(Preset {})".format(preset["name"]) if preset else ""

        print("updated {} old mask {} to group {} and mask {} {}".format(node, oldMask, groupHex, maskHex, presetName))

        return True, "updated old mask {} to group {} and mask {} {}".format(oldMask, groupHex, maskHex, presetName)


def setObjectDefaultClipDistance(node, unused):
    I3DExporter.I3DSaveAttributeFloat(node, 'i3D_clipDistance', 300)


def showObjectAndHideMesh(node, unused):
    for shape in cmds.listRelatives(node, c=True, pa=True):
        if cmds.nodeType(shape) == "mesh":
            cmds.setAttr(shape + ".visibility", False)

    cmds.setAttr(node + ".visibility", True)


def addObjectCPUMeshFlag(node, unused):
    I3DExporter.I3DSaveAttributeBool(node, 'i3D_cpuMesh', True)


def freezeObjectPivot(node, unused):
    doFreezeToPivot(node)


def freezeObjectScale(node, unused):
    selectedNodes = getSelectedObjects()
    cmds.select(node)
    cmds.makeIdentity(apply=True, s=True, n=False)
    cmds.select(selectedNodes)


def removeObjectScaleFlag(node, unused):
    I3DExporter.I3DSaveAttributeBool(node, 'i3D_scaled', False)


def selectObject(node, unused):
    cmds.select(node)


def removeObject(node, unused):
    cmds.delete(node)


def removeIntermediateShape(node, unused):
    # first we try to delete the history to remove it, so we are clear to not break anything
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True)
    if shapes is not None:
        for shape in shapes:
            if cmds.objExists(shape):
                cmds.delete(shape, ch=True)

    # if the object still exists we just remove it
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True)
    if shapes is not None:
        for shape in shapes:
            intermediateObject = cmds.getAttr(shape + '.intermediateObject')
            if intermediateObject:
                cmds.delete(shape)


def resetJointOrientation(node, unused):
    ox, oy, oz = cmds.getAttr(node + ".jointOrientX"), cmds.getAttr(node + ".jointOrientY"), cmds.getAttr(node + ".jointOrientZ")
    if ox != 0 or oy != 0 or oz != 0:
        print("Resetting joint orientation of '%s'" % node)

        cmds.setAttr(node + ".jointOrientX", 0)
        cmds.setAttr(node + ".jointOrientY", 0)
        cmds.setAttr(node + ".jointOrientZ", 0)

        rx, ry, rz = cmds.getAttr(node + ".rotateX"), cmds.getAttr(node + ".rotateY"), cmds.getAttr(node + ".rotateZ")
        cmds.setAttr(node + ".rotateX", rx + ox)
        cmds.setAttr(node + ".rotateY", ry + oy)
        cmds.setAttr(node + ".rotateZ", rz + oz)

        print("  - default rotation changed to '%.3f %.3f %.3f'" % (rx + ox, ry + oy, rz + oz))

        keyframes = cmds.keyframe(node, q=True)
        if keyframes is not None:
            keyframes = sorted(set(keyframes))

            for keyframe in keyframes:
                cmds.setKeyframe(node + ".rotateX", t=[keyframe], v=cmds.getAttr(node + ".rotateX", time=keyframe))
                cmds.setKeyframe(node + ".rotateY", t=[keyframe], v=cmds.getAttr(node + ".rotateY", time=keyframe))
                cmds.setKeyframe(node + ".rotateZ", t=[keyframe], v=cmds.getAttr(node + ".rotateZ", time=keyframe))

            for keyframe in keyframes:
                rx, ry, rz = cmds.getAttr(node + ".rotateX", time=keyframe), cmds.getAttr(node + ".rotateY", time=keyframe), cmds.getAttr(node + ".rotateZ", time=keyframe)
                cmds.setKeyframe(node + ".rotateX", t=[keyframe], v=rx + ox)
                cmds.setKeyframe(node + ".rotateY", t=[keyframe], v=ry + oy)
                cmds.setKeyframe(node + ".rotateZ", t=[keyframe], v=rz + oz)

                print("  - keyframe '%s' value changed to '%.3f %.3f %.3f'" % (keyframe, rx + ox, ry + oy, rz + oz))


def removeMaterial(args, unused):
    cmds.delete(args[0])
    mel.eval('MLdeleteUnused')


def removeVertexColors(node, unused):
    colorSets = cmds.polyColorSet(node, query=True, currentColorSet=True)
    if colorSets:
        cmds.polyColorSet(node, delete=True, colorSet=colorSets[0])


def removeUvSet(args, unused):
    node, uvSetName = args[0], args[1]
    if node and uvSetName:
        if uvSetName in cmds.polyUVSet(node, query=True, allUVSets=True):  # check if uv set is still there
            cmds.polyUVSet(node, uvSet=uvSetName, delete=True)


def getClipDistance(node):
    if cmds.listAttr(node, string="i3D_clipDistance") is not None:
        return cmds.getAttr(node + ".i3D_clipDistance") or 0
    return 0


def getEffectiveClipDistance(node, returnMinimumNode=False):
    # retrieves clip distance of node considering full parent hierarchy
    minimumNode = node
    clipDistance = getClipDistance(node)
    while True:
        parent = cmds.listRelatives(node, parent=True, fullPath=True)
        if parent is None:
            break
        node = parent[0]
        parentClipDistance = getClipDistance(node)
        if parentClipDistance != 0:
            if clipDistance != 0:
                if parentClipDistance <= clipDistance:
                    minimumNode = node
                    clipDistance = parentClipDistance
            else:
                clipDistance = parentClipDistance
    if returnMinimumNode:
        return clipDistance, minimumNode
    return clipDistance


def attributeExists(node, attribute):
    try:
        if cmds.attributeQuery(attribute, node=node, exists=True):
            return True
    except:
        if type(node) != str or type(attribute) != str:
            showWarning("Invalid attributes passed to 'attributeExists' '%s', '%s'" % (str(node), str(attribute)))

        if attribute and node:
            if not cmds.objExists(node):
                return False

            attributesShort = cmds.listAttr(node, shortNames=True)
            if attributesShort is not None:
                if attribute in attributesShort:
                    return True

            attributes = cmds.listAttr(node)
            if attributes is not None:
                if attribute in attributes:
                    return True

    return False

def getAttributeValueAndType(node, attribute, default, isTexture = False):
    fullname = node + '.' + attribute
    result = default
    type = None
    if attributeExists(node, attribute):
        type = cmds.getAttr(fullname, type=True)
        if isTexture:
            if (type == 'string'):
                result = cmds.getAttr(fullname)
            else:
                # Get texture connections
                connectedAttributes = cmds.listConnections(fullname)
                if connectedAttributes:
                    connectedAttribute = connectedAttributes[0]
                    if attributeExists(connectedAttribute, 'fileTextureName'):
                        fullname = '{}.{}'.format(connectedAttribute, 'fileTextureName')
                        result = cmds.getAttr(fullname)
                type = 'string'
        elif (type == 'TdataCompound'):
            # hardware shader vec4 attributes are stored as compound attributes
            subAttributes = cmds.listAttr('{}.{}'.format(node, attribute))
            requiredSubAttributes = [
               '{}X'.format(attribute),
               '{}Y'.format(attribute),
               '{}Z'.format(attribute),
               '{}W'.format(attribute)
            ]
            if all(subAttribute in subAttributes for subAttribute in requiredSubAttributes):
                type = 'float4'
                result = []
                for subAttribute in requiredSubAttributes:
                    result.append(cmds.getAttr('{}.{}.{}'.format(node, attribute, subAttribute)))
        else:
            result = cmds.getAttr(fullname)
    return result, type

def getAttributeValueAsStr(node, attribute, default, isTexture = False):
    result = default
    value, type = getAttributeValueAndType(node, attribute, default, isTexture)
    if value is not None:
        if (type == 'string'):
            result = value
        elif (type == 'float2'):
            # cmds.getAttr returns a list of tuples, with the first tuple holding the actual values
            floatValues = value[0]
            result = '{:.2f} {:.2f}'.format(floatValues[0], floatValues[1])
        elif (type == 'float3'):
            # cmds.getAttr returns a list of tuples, with the first tuple holding the actual values
            floatValues = value[0]
            result = '{:.2f} {:.2f} {:.2f}'.format(floatValues[0], floatValues[1], floatValues[2])
        elif (type == 'float4'):
            # float4 is a custom type not supported by maya
            result = '{:.2f} {:.2f} {:.2f} {:.2f}'.format(value[0], value[1], value[2], value[3])
        elif (type == 'long'):
            result = str(value)
        elif (type == 'float'):
            result = '{:.2f}'.format(value)
        elif (type == 'enum'):
            if (value == 0):
                result = None
            else:
                enumString = cmds.attributeQuery(attribute, node=node, listEnum=True)[0]
                enumList = enumString.split(':')
                result = enumList[value]
        elif (type == 'bool'):
            result = str(value)
        else:
            showWarning('Attribute {}.{} has unsupported type {}'.format(node, attribute, type))
    return result

def stringToFloatArray(s):
    floatValues = []
    splitValues = s.split(' ')
    for splitValue in splitValues:
        floatValues.append(float(re.sub('[^\d\.]', '', splitValue)))

    return floatValues

def getEnumAttrIndexByName(node, attribute, value):
    enumString = cmds.attributeQuery(attribute, node=node, listEnum=True)[0]
    enumList = enumString.split(":")
    # might be a case when value specified do not exists
    if value in enumList:
        return enumList.index(value)
    else:
        return 0

def getNameFromFilePath(filePath, type="short"):
    m_file = os.path.splitext(filePath)[0]
    m_file = os.path.split(m_file)[1]
    if "short" == type:
        m_strList = [ "_diffuse", "_normal", "_specular", "_vmask", "_alpha", "_height" ]
        for m_str in m_strList:
            m_strIndex = m_file.lower().find( m_str )
            if ( -1 != m_strIndex ):
                m_file = m_file[ :m_strIndex ]
    return m_file

def isFileNodeExists(filePath):
    m_iterator = OpenMaya.MItDependencyNodes( OpenMaya.MFn.kFileTexture )
    m_nodeFn   = OpenMaya.MFnDependencyNode()
    while not m_iterator.isDone():
        m_object = m_iterator.thisNode()
        m_nodeFn.setObject( m_object )
        if m_nodeFn.hasAttribute("fileTextureName"):
            value = cmds.getAttr("{}.fileTextureName".format(m_nodeFn.name()))
            if os.path.normpath(value) == os.path.normpath(filePath):
                return m_nodeFn.name()
        m_iterator.next()
    return None

def getFileNodeFromFilePath(filePath):
    filePath = os.path.normpath(filePath)
    # check if fileNode wuith this filePath exists
    fileNode = isFileNodeExists(filePath)
    if fileNode:
        print("Use existing {}.fileTextureName {}".format(fileNode,filePath))
        return fileNode
    else:
        texName = getNameFromFilePath(filePath,type="full")
        fileNode = cmds.shadingNode("file", name=texName , asTexture=True)
        print("Created: {}".format(fileNode))
        cmds.setAttr("{}.fileTextureName".format(fileNode), "{}".format(filePath), type='string')
        print("Set: {}.fileTextureName to {}".format(fileNode,filePath))
        return fileNode

def createAndConnectTexture(matInstance, filePath, attrName):
    texInstance = getFileNodeFromFilePath(filePath)
    outColor = "{}.outColor".format(texInstance)
    attribute = "{}.{}".format(matInstance, attrName)

    cmds.setAttr(attribute, lock=0)
    cmds.connectAttr(outColor, attribute, force=True)
    print("Connected: {}.outColor to {}.{}".format(texInstance, matInstance, attrName))
    return texInstance

def setAttributeValue(node, attribute, value, isTexture = False):
    fullname = '{}.{}'.format(node, attribute)
    if(not attributeExists(node, attribute)):
        cmds.addAttr(node, shortName=attribute, niceName=attribute, longName=attribute, dt='string')
        cmds.setAttr(fullname, edit=True, keyable=True)

    if isTexture:
        type = cmds.getAttr(fullname, type=True)
        # If its a string type, just store the value
        if (type == 'string'):
            cmds.setAttr(fullname, value, type='string')
        else:
            gamePath = I3DExporter.I3DGetGamePath()
            value = value.replace('$', gamePath + '/')

            # Always create a new texture, to avoid breaking other connections.
            createAndConnectTexture(node, value, attribute)
    else:
        type = cmds.getAttr(fullname, type=True)
        if (type == 'string'):
            cmds.setAttr(fullname, value, type='string')
        elif (type == 'float3'):
            floatValues = stringToFloatArray(value)
            cmds.setAttr(fullname, floatValues[0], floatValues[1], floatValues[2], type='float3')
        elif (type == 'float'):
            floatValue = float(re.sub('[^\d\.]', '', value))
            cmds.setAttr(fullname, floatValue)
        elif (type == 'enum'):
            value = getEnumAttrIndexByName(node, attribute, value)
            cmds.setAttr(fullname, value)
        elif (type == 'bool'):
            cmds.setAttr(fullname, value)
        else:
            showWarning('Attribute {} has unsupported type {}. Can not set attribute value.'.format(fullname, type))

def isGLSLvehicleShaderOnGeo(node):
    '''
    IN: node - str name of the object (OpenMaya.MFn.kMesh)
    OUT: True - if all assigned ShadingGroups connected to OpenMaya.MFn.kPluginHardwareShader with vehicleShader.ogsfx
    '''
    m_path = getMDagPathFromNodeName(node)
    if (m_path and m_path.hasFn(OpenMaya.MFn.kMesh)):
        # valid MDagPath to kMesh
        m_path.extendToShape() # in case we got kTransform
        m_listShadingGroups = getShapeShadingGroupsAsList(m_path)
        m_listVehicleShaders = []
        for m_sg in m_listShadingGroups:
            m_mat = getMaterialFromShadingGroup(m_sg)
            m_matObj = getMObjectFromNodeName(m_mat)
            if (m_matObj and m_matObj.hasFn(OpenMaya.MFn.kPluginHardwareShader)):
                # valid MObject to GLSL shader
                m_str = cmds.getAttr("{}.shader".format(m_mat))
                if (-1 !=m_str.find("vehicleShader.ogsfx")):
                    m_listVehicleShaders.append({m_sg:{'material':m_mat,'matObj':m_matObj}})
        if (len(m_listShadingGroups) == len(m_listVehicleShaders)):
            return True
    return False

def getMaterialFromSelection():
    m_matStr = 'lambert1'
    # check selection
    selection = cmds.ls( selection=True)
    if (0==len(selection)):
        # selection is in edit mode
        selection = cmds.ls( hilite=True )
        for s in selection:
            m_path = getMDagPathFromNodeName(s)
            if (m_path):
                m_sgStr = getShadingGroupNameFromPolygonIndex(m_path,0)
                m_matStr = getMaterialFromShadingGroup(m_sgStr)
    else:
        m_list = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList( m_list )
        m_listIt = OpenMaya.MItSelectionList( m_list )
        while not m_listIt.isDone():
            m_obj       = OpenMaya.MObject()
            m_path      = OpenMaya.MDagPath()   # will hold a path to the selected object
            m_component = OpenMaya.MObject()    # will hold a list of selected components
            # we retrieve a dag path to a transform or shape, and an MObject
            # to any components that are selected on that object (if any).
            m_listIt.getDependNode(m_obj)
            mfn_depNode = OpenMaya.MFnDependencyNode(m_obj)
            if  (OpenMaya.MItSelectionList.kDagSelectionItem==m_listIt.itemType()):
                # selected something in viewport
                m_listIt.getDagPath( m_path, m_component )
                m_polyIndex = getSelectedPolygonIndex(m_path,m_component)
                m_sgStr = getShadingGroupNameFromPolygonIndex(m_path,m_polyIndex)
                m_matStr = getMaterialFromShadingGroup(m_sgStr)
                #print(m_matStr,m_sgStr,m_polyIndex, m_obj.apiTypeStr(),m_path.fullPathName())
            elif (OpenMaya.MItSelectionList.kDNselectionItem==m_listIt.itemType()):
                # selected something like material, file etc
                if ( m_obj.hasFn(OpenMaya.MFn.kLambert) or
                     m_obj.hasFn(OpenMaya.MFn.kPluginHardwareShader) ):
                    m_matStr = mfn_depNode.name()
                #print(m_obj.apiTypeStr()))
            m_listIt.next()
    return m_matStr

def selectMaterialFaces(shader):
    shadingGroup = cmds.listConnections(shader, type="shadingEngine")
    if shadingGroup is not None and len(shadingGroup) > 0:
        selection = []
        faceGroups = cmds.sets(shadingGroup, q=True)
        if faceGroups is not None:
            for faces in faceGroups:
                selection.append(faces)
            cmds.select(selection)

def selectMergeableFacesByMaterial(args, *unused):
    shapeDAG, material = args[0], args[1]
    shadingGroup = cmds.listConnections(material, type="shadingEngine")
    if shadingGroup is not None and len(shadingGroup) > 0:
        selection = []
        faceGroups = cmds.sets(shadingGroup, q=True)
        if faceGroups is not None:
            for faces in faceGroups:
                faceShape = faces.split(".f")[0]
                if faceShape in shapeDAG:
                    selection.append(faces)
            cmds.select(selection)

def getLightFromTransformNode(node):
    dagNode = getMDagPathFromNodeName(node)
    lightNode = None
    for i in range( dagNode.childCount() ):
        m_obj = dagNode.child(i)
        if m_obj.hasFn(OpenMaya.MFn.kNonExtendedLight):
            lightNode = OpenMaya.MFnNonExtendedLight(m_obj)
            break

    return lightNode

def getMObjectFromNodeName( m_node_name ):
    m_selectionList = OpenMaya.MSelectionList()
    m_node = OpenMaya.MObject()
    try:
        m_selectionList.add(m_node_name)
        m_selectionList.getDependNode(0, m_node)
    except:
        return None
    return m_node

def getMDagPathFromNodeName( m_node_name ):
    m_selectionList = OpenMaya.MSelectionList()
    m_objPath = OpenMaya.MDagPath()
    try:
        m_selectionList.add( m_node_name )
        m_selectionList.getDagPath( 0, m_objPath )
    except:
        return None
    return m_objPath

def getShapeShadingGroupsAsList(m_path):
    # m_path is a OpenMaya.MDagPath() to OpenMaya.MFn.kMesh
    # make sure that we work with shape, otherwise we can't use OpenMaya.MFnMesh
    # m_path.extendToShape() should be done before
    m_listShadingGroups = []
    # ideally should always happen
    if ( m_path.apiType() == OpenMaya.MFn.kMesh ):
        m_meshFn = OpenMaya.MFnMesh( m_path )
        m_sets  = OpenMaya.MObjectArray()
        m_comps = OpenMaya.MObjectArray()
        m_instanceNumber = m_path.instanceNumber()
        m_renderableSetsOnly = 1
        # m_instanceNumber     - the instance number of the mesh to query
        # m_sets               - storage for the sets
        # m_comps              - storage for the components that are in the corresponding set
        # m_renderableSetsOnly - if true then this method will only return renderable sets
        m_meshFn.getConnectedSetsAndMembers( m_instanceNumber, m_sets, m_comps, m_renderableSetsOnly )
        if (0 == m_sets.length()):
            m_listShadingGroups.clear()
            m_listShadingGroups.append('initialShadingGroup')
            return m_listShadingGroups
        elif (1 == m_sets.length()):
            m_sefFn = OpenMaya.MFnSet( m_sets[0] )
            # return empty list if shape has only 1 ShadingGroup assigned
            # all polygons are in the same ShadingGroup
            m_listShadingGroups.clear()
            m_listShadingGroups.append(m_sefFn.name())
            return m_listShadingGroups
        else:
            m_listShadingGroups.clear()
            m_ind = 0
            while ( m_ind < m_sets.length()):
                m_sefFn = OpenMaya.MFnSet( m_sets[ m_ind ] )
                m_listShadingGroups.append(m_sefFn.name())
                m_ind += 1
            return m_listShadingGroups
    return m_listShadingGroups

def getMaterialFromShadingGroup(m_sgStr):
    m_obj = getMObjectFromNodeName(m_sgStr)
    if m_obj:
        m_nodeFn = OpenMaya.MFnDependencyNode(m_obj)
        if (m_nodeFn.hasAttribute("surfaceShader")):
            m_plug = m_nodeFn.findPlug( "surfaceShader" )
            m_plugArrayConnected = OpenMaya.MPlugArray()
            m_plug.connectedTo( m_plugArrayConnected, True, False )
            for i in range( m_plugArrayConnected.length() ):
                m_plugConnected   = m_plugArrayConnected[i]
                m_nodeConnected   = m_plugConnected.node()
                m_nodeFnConnected = OpenMaya.MFnDependencyNode( m_nodeConnected )
                return m_nodeFnConnected.name()
    return 'lambert1'

def getShadingGroupNameFromPolygonIndex(m_objPath,m_polyIndex):
    if (m_objPath.hasFn(OpenMaya.MFn.kMesh)):
        m_objPath.extendToShape() # in case we got kTransform
        if ( m_objPath.apiType() == OpenMaya.MFn.kMesh ):
            m_meshFn = OpenMaya.MFnMesh( m_objPath )
            m_sets  = OpenMaya.MObjectArray()
            m_comps = OpenMaya.MObjectArray()
            m_instanceNumber = m_objPath.instanceNumber()
            m_meshFn.getConnectedSetsAndMembers( m_instanceNumber, m_sets, m_comps, 1 )
            m_sets_len = m_sets.length()
            # if mesh have more then one ShadingGroup
            # last set contain all polygons, ignore it
            m_ind = 0
            while ( m_ind < m_sets_len):
                m_sefFn = OpenMaya.MFnSet( m_sets[ m_ind ] )
                m_tempFaceIt = OpenMaya.MItMeshPolygon( m_objPath, m_comps[ m_ind ] )
                while not m_tempFaceIt.isDone(): # iterate
                    if ( m_tempFaceIt.index() == m_polyIndex ):
                        return m_sefFn.name()
                    m_tempFaceIt.next()
                m_ind += 1
    return 'initialShadingGroup'

def getSelectedPolygonIndex(m_path, m_component):
    m_selectedPolygons = getSelectedPolygonComponents(m_path,m_component)
    m_polyIndex = 0
    if (0!=len(m_selectedPolygons)):
        # use last selected polygon
        m_polyIndex = m_selectedPolygons[-1]
    return m_polyIndex

def getSelectedPolygonComponents(m_path, m_component):
    '''
    Return list like [258, 259] if polygons were selected
    '''
    m_selectedPolygons = []
    if ( not m_component.isNull() ):
        if ( OpenMaya.MFn.kMeshPolygonComponent == m_component.apiType() ):
            m_itPoly = OpenMaya.MItMeshPolygon( m_path, m_component )
            while not m_itPoly.isDone():
                m_selectedPolygons.append(m_itPoly.index())
                m_itPoly.next()
    return m_selectedPolygons


def getObjectMaterials(object):
    shapes = cmds.listRelatives(object, s=True, f=True)
    if shapes is not None:
        shadingEngines = cmds.listConnections(shapes[0], type='shadingEngine')
        if shadingEngines is not None:
            materials = cmds.ls(cmds.listConnections(shadingEngines), mat=True)
            return list(set(materials))


def getAreObjectsMergeable(object1, object2):
    materials1 = getObjectMaterials(object1)
    materials2 = getObjectMaterials(object2)
    if materials1 is not None and materials2 is not None:
        mergeable = True
        mismatchData = None
        for material1 in materials1:
            for material2 in materials2:
                mergeable, mismatchData = getAreMaterialsMergeable(material1, material2)
                if not mergeable:
                    break
            if not mergeable:
                break

        return mergeable, mismatchData

    return False, None


def getWarningFromMismatchData(mismatchData):
    if mismatchData is not None:
        if "attributeName" in mismatchData:
            compareStr = ""
            if "attribute1" in mismatchData and "attribute2" in mismatchData:
                compareStr = " (%s vs %s)" % (mismatchData["attribute1"], mismatchData["attribute2"])
            elif "attribute1" in mismatchData:
                compareStr = " (%s vs %s)" % (mismatchData["attribute1"], "Not Found")
            elif "attribute2" in mismatchData:
                compareStr = " (%s vs %s)" % ("Not Found", mismatchData["attribute2"])

            return "Attribute '%s' on %s '%s' and '%s' is different.%s" % (mismatchData["attributeName"], mismatchData["type"].lower(), mismatchData["object1"].split("|")[-1], mismatchData["object2"].split("|")[-1], compareStr)
        if "textureName" in mismatchData:
            compareStr = ""
            if "texture1" in mismatchData and "texture2" in mismatchData:
                compareStr = " (%s vs %s)" % (mismatchData["texture1"], mismatchData["texture2"])
            return "Texture '%s' on %s '%s' and '%s' is different.%s" % (mismatchData["textureName"], mismatchData["type"].lower(), mismatchData["object1"].split("|")[-1], mismatchData["object2"].split("|")[-1], compareStr)
        if "differentType" in mismatchData:
            return "%s '%s' and '%s' have different types (%s vs %s)" % (mismatchData["type"], mismatchData["object1"].split("|")[-1], mismatchData["object2"].split("|")[-1], mismatchData["type1"], mismatchData["type2"])

    return None


def getAreObjectMaterialsMergeable(object):
    materials = getObjectMaterials(object)
    if materials is not None:
        for material1 in materials:
            for material2 in materials:
                if material1 != material2:
                    mergeable, mismatchData = getAreMaterialsMergeable(material1, material2)
                    if not mergeable:
                        return mergeable, mismatchData
    return True, None


MERGABLE_BASE_TEXTURES = ["specularMap", "normalMap", "diffuseMap"]
MERGABLE_BASE_ATTRIBUTES_DEFAULT = ["translucence", "customShader", "customShaderVariation", "shadingRate"]
MERGABLE_BASE_ATTRIBUTES_GLSL = ["technique", "shader", "customShaderVariation", "shadingRate"]


def getAreMaterialsMergeable(material1, material2):
    mergeable = True
    mismatchData = None

    if material1 == material2:
        return True, None

    nodeType = cmds.nodeType(material1)
    if nodeType != cmds.nodeType(material2):
        mismatchData = {"type": "Material", "object1": material1, "object2": material2, "differentType": True, "type1": cmds.nodeType(material1), "type2": cmds.nodeType(material2)}
        return False, mismatchData

    def getAttributeTexture(material, attribute):
        textures = cmds.ls(cmds.listConnections(material + "." + attribute), tex=True)
        if textures is not None and len(textures) > 0:
            return textures[0]

    for baseTexture in MERGABLE_BASE_TEXTURES:
        attrList1 = cmds.listAttr(material1, string=baseTexture)
        attrList2 = cmds.listAttr(material2, string=baseTexture)
        if attrList1 is not None and attrList2 is not None:
            if getAttributeTexture(material1, baseTexture) != getAttributeTexture(material2, baseTexture):
                mergeable = False
                mismatchData = {"type": "Material", "object1": material1, "object2": material2, "textureName": baseTexture, "texture1": getAttributeTexture(material1, baseTexture), "texture2": getAttributeTexture(material2, baseTexture)}
                break
        else:
            if attrList1 is not None or attrList2 is not None:
                mergeable = False
                mismatchData = {"type": "Material", "object1": material1, "object2": material2, "textureName": baseTexture}
                break

    if mergeable:
        attributes = MERGABLE_BASE_ATTRIBUTES_DEFAULT
        if nodeType == "GLSLShader":
            attributes = MERGABLE_BASE_ATTRIBUTES_GLSL

        for baseAttribute in attributes:
            attrList1 = cmds.listAttr(material1, string=baseAttribute)
            attrList2 = cmds.listAttr(material2, string=baseAttribute)
            if attrList1 is not None and attrList2 is not None:
                if cmds.getAttr(material1 + "." + baseAttribute) != cmds.getAttr(material2 + "." + baseAttribute):
                    mergeable = False
                    mismatchData = {"type": "Material", "object1": material1, "object2": material2, "attributeName": baseAttribute, "attribute1": cmds.getAttr(material1 + "." + baseAttribute), "attribute2": cmds.getAttr(material2 + "." + baseAttribute)}
                    break
            else:
                if attrList1 is not None:
                    mergeable = False
                    mismatchData = {"type": "Material", "object1": material1, "object2": material2, "attributeName": baseAttribute, "attribute1": cmds.getAttr(material1 + "." + baseAttribute)}
                    break

                if attrList2 is not None:
                    mergeable = False
                    mismatchData = {"type": "Material", "object1": material1, "object2": material2, "attributeName": baseAttribute, "attribute2": cmds.getAttr(material2 + "." + baseAttribute)}
                    break

    return mergeable, mismatchData


def fixHiddenMaterialsInScene():
    ''' Add all materials to the defaultShaderList1, otherwise they are not visible in the hypershader nor the exporter material tab -> cmds.ls(materials=True) would not return them '''

    types = ["phong", "lambert", "GLSLShader"]
    for type in types:
        materials = cmds.ls(typ=type)
        for material in materials:
            connections = cmds.listConnections(material)
            if connections is not None:
                isInDefaultShaderList = False
                for connection in connections:
                    if "defaultShaderList1" in connection:
                        isInDefaultShaderList = True

                if not isInDefaultShaderList:
                    cmds.connectAttr(material + ".msg", 'defaultShaderList1.s', na=True)
                    print("Added material '%s' to defaultShaderList1!" % material)


def getMergableMaterialList():
    materialGroups = []
    materials = cmds.ls(materials=True)
    materials.sort()

    while len(materials) >= 1:
        group = []
        group.append(materials[0])
        for j in range(len(materials) - 1, 1, -1):
            mergable, mismatchData = getAreMaterialsMergeable(materials[0], materials[j])
            if mergable:
                group.append(materials[j])
                materials.pop(j)
        materials.pop(0)
        group.sort()
        materialGroups.append(group)

    return materialGroups


def reloadModule(module):
    try:
        reload(module)
    except NameError:
        import importlib
        importlib.reload(module)

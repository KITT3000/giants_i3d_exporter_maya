import xml.etree.ElementTree as ET
import os


cachedShaders = dict()

def getShader(shaderXmlPath, gameDirectory=None, mayaFileDirectory=None):
    if ".xml" not in shaderXmlPath:
        print("Error: ShaderUtil.getShader: Unable to get shader from file '%s'. No xml file!" % shaderXmlPath)
        return None

    # game relative path
    if shaderXmlPath.startswith('$'):
        if not gameDirectory:
            print("Error: ShaderUtil.getShader: Unable to load shader xml '{}'. Game-relative path with no game directory given as second argument".format(shaderXmlPath))
            return None
        else:
            shaderXmlPath = "{}/{}".format(gameDirectory, shaderXmlPath[1:])

    # file relative path
    elif not os.path.exists(shaderXmlPath):
        if not mayaFileDirectory:
            print("Error: ShaderUtil.getShader: Unable to load shader xml '{}'. Relative path with no ma file directory given as third argument".format(shaderXmlPath))
            return None
        else:
            shaderXmlPath = "{}/{}".format(mayaFileDirectory, shaderXmlPath)

    if os.path.exists(shaderXmlPath):
        if shaderXmlPath not in cachedShaders:
            shader = Shader(shaderXmlPath)
            cachedShaders[shaderXmlPath] = shader
        return cachedShaders[shaderXmlPath]
    else:
        print("Error: ShaderUtil.getShader: Unable to load shader xml '{}'. File does not exist".format(shaderXmlPath))
    return None

class Shader:
    defaultGroup = "base"

    def __init__(self, shaderXmlPath):
        self.xmlRoot = ET.parse(shaderXmlPath).getroot()
        self.cachedCalls = dict()

    def getVertexAttributeGroups(self, vertexAttributeName): # -> list group names
        groups = set()
        vertexAttrElems = self.xmlRoot.findall("./VertexAttributes/VertexAttribute[@name='{}']".format(vertexAttributeName))
        if vertexAttrElems is not None:
            for vertexAttrElem in vertexAttrElems:
                groups.add(vertexAttrElem.get('group'))
        return list(groups)

    def getVariationGroups(self, variationName):  # -> list of groups
        groups = set([Shader.defaultGroup])  # base group is always present

        variationElem = self.xmlRoot.find("./Variations/Variation[@name='{}']".format(variationName))
        if variationElem is not None:
            groupsString = variationElem.get('groups').strip()
            if groupsString != "":
                groups.update(groupsString.split(" "))
        return list(groups)

    def getVariationUsesVertexAttribute(self, variationName, vertexAttributeName):  # -> bool
        key = "{}-{}".format(variationName, vertexAttributeName)
        if key not in self.cachedCalls:
            returnValue = False
            for group in self.getVertexAttributeGroups(vertexAttributeName):
                if group in self.getVariationGroups(variationName):
                    returnValue = True
                    break
            self.cachedCalls[key] = returnValue
        return self.cachedCalls[key]

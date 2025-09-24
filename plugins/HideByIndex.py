# -----------------------------------------------------------------------------------
#
#   SCRIPT      HideByIndex.py
#   AUTHORS     Marius Hofmann
#
#   Sets the 'hideByIndexMaxIndex' integer user attribute for nodes using 'i3D_mergeChildren' and custom shader pararameter 'hideByIndex' to the number of merged objects
#   The user attribute is to be loaded by script
#
# -----------------------------------------------------------------------------------

import maya.cmds as cmds
import I3DExporter


def getI3DExporterPlugin():
    return HideByIndex()


class HideByIndex:
    def __init__(self):
        self.name = "Hide By Index"
        self.page = "Tools"
        self.prio = 99

    def onPreExport(self, *args):
        nodes = cmds.ls(assemblies=True)
        for node in nodes:
            self.__updateNode(node)

    def __updateNode(self, node):
        if I3DExporter.I3DGetAttributeValue(node, 'i3D_mergeChildren', None):
            children = cmds.listRelatives(node, children=True, fullPath=True)
            if children is None or len(children) == 0:
                return

            isValid = False
            for child in children:
                shapes = cmds.listRelatives(child, fullPath=True)
                if shapes is not None and len(shapes) > 0:
                    materials = cmds.listConnections(shapes[0], type='shadingEngine')
                    if materials is not None and len(materials) > 0:
                        shaders = cmds.listConnections(materials[0] + '.surfaceShader')
                        if shaders is not None and len(shaders) > 0:
                            paramValue = I3DExporter.I3DGetAttributeValue(shaders[0], 'customParameter_hideByIndex', None)
                            if paramValue is not None:
                                isValid = True

            if isValid:
                maxIndex = len(children)
                I3DExporter.I3DSaveAttributeInt(node, 'hideByIndexMaxIndex', maxIndex)
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, "HideByIndex: {} updated user attribute 'hideByIndexMaxIndex'  to {}".format(node, maxIndex))

        else:
            # recursion
            nodes = cmds.listRelatives(node, fullPath=True)
            if nodes is not None:
                for cnode in nodes:
                    self.__updateNode(cnode)

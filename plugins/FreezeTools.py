#
# Freeze Tools Plugin for Maya I3D Exporter
# Includes tools to freeze translation, rotation and scale
#
# @created 12/04/2019
# Code imported from I3DExporter.py
#
# Copyright (c) 2008-2015 GIANTS Software GmbH, Confidential, All Rights Reserved.
# Copyright (c) 2003-2015 Christian Ammann and Stefan Geiger, Confidential, All Rights Reserved.
#

import maya.cmds as cmds
import I3DUtils


class FreezeTools:
    def __init__(self):
        self.name = "Freeze Transformation"
        self.page = "Tools"
        self.prio = 2

        self.shelfCommand = "import I3DUtils; import FreezeTools; I3DUtils.reloadModule(FreezeTools); plugin = FreezeTools.FreezeTools(); plugin.%s(); del plugin;"

        self.freezeTranslationInfo = {"name": "Freeze Translation",
                                      "category": self.name,
                                      "annotation": "Freezes translation",
                                      "button_function": self.executeFreezeTranslation,
                                      "shelf_label": "FrzTrans",
                                      "shelf_command": self.shelfCommand % "executeFreezeTranslation"}

        self.freezeRotationInfo = {"name": "Freeze Rotation",
                                   "category": self.name,
                                   "annotation": "Freezes rotation",
                                   "button_function": self.executeFreezeRotation,
                                   "shelf_label": "FrzRot",
                                   "shelf_command": self.shelfCommand % "executeFreezeRotation"}

        self.freezeScaleInfo = {"name": "Freeze Scale",
                                "category": self.name,
                                "annotation": "Freezes scale",
                                "button_function": self.executeFreezeScale,
                                "shelf_label": "FrzSca",
                                "shelf_command": self.shelfCommand % "executeFreezeScale"}

        self.freezeAllInfo = {"name": "Freeze All",
                              "category": self.name,
                              "annotation": "Freezes translation, rotation and scale",
                              "button_function": self.executeFreezeAll,
                              "shelf_label": "FrzAll",
                              "shelf_command": self.shelfCommand % "executeFreezeAll"}

    def getToolsButtons(self):
        return [self.freezeTranslationInfo, self.freezeRotationInfo,
                self.freezeScaleInfo, self.freezeAllInfo]

    def getShelfScripts(self):
        return [self.freezeTranslationInfo, self.freezeRotationInfo,
                self.freezeScaleInfo, self.freezeAllInfo]

    def executeFreezeTranslation(self, *args):
        nodes = cmds.ls(sl=True, o=True)
        if(len(nodes) == 0):
            I3DUtils.showWarning('Nothing selected!')
            return

        for node in nodes:
            worldPivots = [0, 0, 0]

            parent = I3DUtils.getParent(node)
            if parent is not None:
                worldPivots = cmds.xform(parent, q=True, ws=True, scalePivot=True)

            cmds.xform(node, worldSpace=True, preserve=True, pivots=worldPivots)
            I3DUtils.freezeToPivot(None)

    def freeze(self, t, r, s):
        def collectChildren(node, lst):
            children = cmds.listRelatives(node, children=True, fullPath=True)
            if children is not None:
                for child in children:
                    shapes = cmds.listRelatives(child, shapes=True, fullPath=True)
                    if shapes is not None and len(shapes) > 0:
                        lst[child] = True

                    collectChildren(child, lst)

        nodes = cmds.ls(sl=True, o=True, l=True)
        if len(nodes) == 0:
            I3DUtils.showWarning('Nothing selected!')
            return

        invertedNodes = {}
        for node in nodes:
            scaleX = cmds.getAttr(node + ".scaleX")
            scaleY = cmds.getAttr(node + ".scaleY")
            scaleZ = cmds.getAttr(node + ".scaleZ")
            if scaleX < 0 or scaleY < 0 or scaleZ < 0:
                invertedNodes[node] = True
                collectChildren(node, invertedNodes)

        if cmds.about(version=True) == '2016':
            cmds.makeIdentity(apply=True, t=t, r=r, s=s, n=False, pn=True)
        else:
            cmds.makeIdentity(apply=True, t=t, r=r, s=s, n=False)

        for node, _ in invertedNodes.items():
            cmds.polyNormal(node, normalMode=0, constructionHistory=False)

            shapes = cmds.listRelatives(node, shapes=True, fullPath=True)
            if shapes is not None and len(shapes) > 0:
                if cmds.getAttr(shapes[0] + ".opposite") == 1:
                    cmds.setAttr(shapes[0] + ".opposite", 0)

        I3DUtils.freezeToPivot(None)

        cmds.select(nodes)

    def executeFreezeRotation(self, *args):
        self.freeze(False, True, False)

    def executeFreezeScale(self, *args):
        self.freeze(False, False, True)

    def executeFreezeAll(self, *args):
        self.freeze(True, True, True)


def getI3DExporterPlugin():
    return FreezeTools()

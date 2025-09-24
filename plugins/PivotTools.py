#
# Pivot Tools Plugin for Maya I3D Exporter
# Basic tools for pivot operations (FreezeToPivot, EqualizeWorldPivots, ManipulatorToPivot, ManipulatorToGroup)
#
# @created 12/04/2019
# Code imported from I3DExporter.py
#
# Copyright (c) 2008-2015 GIANTS Software GmbH, Confidential, All Rights Reserved.
# Copyright (c) 2003-2015 Christian Ammann and Stefan Geiger, Confidential, All Rights Reserved.
#

import maya.cmds as cmds
import I3DUtils


class PivotTools:
    def __init__(self):
        self.name = "Pivot-Tools"
        self.page = "Tools"
        self.prio = 1

        self.shelfCommand = "import I3DUtils; import PivotTools; I3DUtils.reloadModule(PivotTools); plugin = PivotTools.PivotTools(); plugin.%s(); del plugin;"

        self.freezeToPivotInfo = {"name": "FreezeToPivot",
                                  "category": self.name,
                                  "annotation": None,
                                  "button_function": self.executeFreezePivot,
                                  "shelf_label": "FrzToPvt",
                                  "shelf_command": self.shelfCommand % "executeFreezePivot"}

        self.equalizeWorldPivotsInfo = {"name": "EqualizeWorldPivots",
                                        "category": self.name,
                                        "annotation": "Adjusts the selected node pivots. Sets the pivot of the first node to the second node\'s pivot position",
                                        "button_function": self.executeEqualizeWorldPivots,
                                        "shelf_label": "EqWoPvt",
                                        "shelf_command": self.shelfCommand % "executeEqualizeWorldPivots"}

        self.manipulatorToPivotInfo = {"name": "ManipulatorToPivot",
                                       "category": self.name,
                                       "annotation": "Sets the pivot of the node to the manipulator position",
                                       "button_function": self.executeManipulatorToPivot,
                                       "shelf_label": "ManToPvt",
                                       "shelf_command": self.shelfCommand % "executeManipulatorToPivot"}

        self.manipulatorToGroupInfo = {"name": "ManipulatorToGroup",
                                       "category": self.name,
                                       "annotation": "Creates a transform group based on current selection",
                                       "button_function": self.executeManipulatorToGroup,
                                       "shelf_label": "ManToGrp",
                                       "shelf_command": self.shelfCommand % "executeManipulatorToGroup"}

    def getToolsButtons(self):
        return [self.freezeToPivotInfo, self.equalizeWorldPivotsInfo,
                self.manipulatorToPivotInfo, self.manipulatorToGroupInfo]

    def getShelfScripts(self):
        return [self.freezeToPivotInfo, self.equalizeWorldPivotsInfo,
                self.manipulatorToPivotInfo, self.manipulatorToGroupInfo]

    def executeFreezePivot(self, *args):
        nodes = I3DUtils.getSelectedObjects()

        if(len(nodes) == 0):
            I3DUtils.showWarning('Nothing selected!')
            return

        for node in nodes:
            self.freezePivot(node)

    def freezePivot(self, node):
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
                self.freezePivot(child)

    def executeEqualizeWorldPivots(self, *args):
        nodes = cmds.ls(sl=True, o=True)
        if(len(nodes) < 2):
            I3DUtils.showWarning('You need to select a mesh and a target point!')
            return

        worldPivots = cmds.xform(nodes[1], q=True, ws=True, scalePivot=True)
        cmds.xform(nodes[0], worldSpace=True, preserve=True, pivots=worldPivots)

    def executeManipulatorToPivot(self, *args):
        objs = cmds.filterExpand(ex=True, sm=12)
        isValidSelection = objs is not None and len(objs) > 0
        if(not isValidSelection):
            objs = cmds.filterExpand(ex=True, sm=31)
            isValidSelection = objs is not None and len(objs) > 0
            if(not isValidSelection):
                objs = cmds.filterExpand(ex=True, sm=32)
                isValidSelection = objs is not None and len(objs) > 0
                if(not isValidSelection):
                    objs = cmds.filterExpand(ex=True, sm=34)
                    isValidSelection = objs is not None and len(objs) > 0

        if(isValidSelection):
            cmds.setToolTo('moveSuperContext')
            result = cmds.manipMoveContext('Move', q=True, p=True)
            result = I3DUtils.linearInternalToUIVector(result)
            origObjShape = cmds.listRelatives(objs[0], p=True, pa=True)
            origObj = cmds.listRelatives(origObjShape, p=True, pa=True)
            targetMesh = origObj[0]
            cmds.xform(targetMesh, worldSpace=True, preserve=True, pivots=[result[0], result[1], result[2]])
            cmds.select(targetMesh, r=True)
        else:
            I3DUtils.showWarning('Please select nodes, vertices, edges or faces')

    def executeManipulatorToGroup(self, *args):
        objs = cmds.filterExpand(ex=True, sm=12)
        isValidSelection = objs is not None and len(objs) > 0
        if(not isValidSelection):
            objs = cmds.filterExpand(ex=True, sm=31)
            isValidSelection = objs is not None and len(objs) > 0
            if(not isValidSelection):
                objs = cmds.filterExpand(ex=True, sm=32)
                isValidSelection = objs is not None and len(objs) > 0
                if(not isValidSelection):
                    objs = cmds.filterExpand(ex=True, sm=34)
                    isValidSelection = objs is not None and len(objs) > 0

        if(isValidSelection):
            cmds.setToolTo('moveSuperContext')
            result = cmds.manipMoveContext('Move', q=True, p=True)
            result = I3DUtils.linearInternalToUIVector(result)

            origObjShape = cmds.listRelatives(objs[0], p=True, pa=True)
            origObj = cmds.listRelatives(origObjShape, p=True, pa=True)
            targetMesh = origObj[0]

            newGroup = cmds.group(em=True, name=targetMesh+'PositionGroup')
            cmds.xform(newGroup, worldSpace=True, preserve=True, pivots=[result[0], result[1], result[2]])
            cmds.select(newGroup, r=True)

            self.freezePivot(newGroup)
        else:
            I3DUtils.showWarning('Please select nodes, vertices, edges or faces')


def getI3DExporterPlugin():
    return PivotTools()

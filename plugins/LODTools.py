#
# Plugin for easy handling of vehicle LODs
#
# @author Stefan Maurus
# @created 23/08/2021
#
# Copyright (c) 2008-2021 GIANTS Software GmbH, Confidential, All Rights Reserved.
# Copyright (c) 2003-2021 Christian Ammann and Stefan Geiger, Confidential, All Rights Reserved.
#

import maya.cmds as cmds
import I3DExporter as I3DExporter
from functools import partial


class LODTools:
    def __init__(self):
        self.name = "LODTools"
        self.page = "Tools"
        self.prio = 10

        self.customUI = {"category": "LOD-Tools",
                         "customUIFunc": self.__createCustomUI}

        self.validData = False

    def getToolsButtons(self):
        return []

    def getShelfScripts(self):
        return []

    def getToolsCustomUI(self):
        return [self.customUI]

    def onPreExport(self):
        if self.validData:
            self.__loadLODs(0)

    def __createCustomUI(self, parentFrame):
        self.__clearFrameLayout(parentFrame)

        self.parentFrame = parentFrame
        self.loadButton = cmds.button(parent=parentFrame, label="Load LODs", height=30, command=self.__loadLODs)

        if self.validData:
            self.__generateDynamicUI()
            self.__onSliderChange(0)

    def __generateDynamicUI(self):
        self.__clearFrameLayout(self.parentFrame)

        cmds.text(label='<span style="font-size: 11pt; font-weight: bold;">Change Draw Distance</span>', align="center", parent=self.parentFrame)
        self.slider = cmds.floatSlider(min=0, max=301, value=0, step=1, dragCommand=self.__onSliderChange, changeCommand=self.__onSliderChanged, parent=self.parentFrame)
        self.sliderValueText = cmds.text(label="Distance: %dm" % 0, align="center", parent=self.parentFrame)
        cmds.separator(style="doubleDash", parent=self.parentFrame)

        lodItems = cmds.columnLayout(rowSpacing=5, adj=True, parent=self.parentFrame)

        headerFormat = '<span style="font-size: 11pt; font-weight: bold;">%s</span>'
        headerRow = cmds.rowLayout(numberOfColumns=2, columnWidth2=[100, 300], columnAttach2=["both", "left"], ad2=2, parent=lodItems)

        cmds.text(label=headerFormat % "Root Object", align="center", parent=headerRow)

        levelHeader = cmds.columnLayout(adj=True, parent=headerRow)
        levelHeaderRow = cmds.rowLayout(numberOfColumns=5, columnWidth5=[160, 75, 75, 120, 75], columnAlign5=["center", "center", "center", "center", "center"], columnAttach5=["both", "both", "both", "both", "both"], ad5=1, parent=levelHeader)

        cmds.text(label=headerFormat % "Level Root", parent=levelHeaderRow)
        cmds.text(label=headerFormat % "Clip Dis.", parent=levelHeaderRow)
        cmds.text(label=headerFormat % "LOD Dis.", parent=levelHeaderRow)
        cmds.text(label=headerFormat % "Num. Objects", parent=levelHeaderRow)
        cmds.text(label=headerFormat % "Control", parent=levelHeaderRow)

        for lod in self.lodData:
            cmds.separator(parent=lodItems)
            lodRow = cmds.rowLayout(numberOfColumns=2, columnWidth2=[100, 300], columnAttach2=["both", "left"], ad2=2, parent=lodItems)

            cmds.text(label='<span style="font-size: 9pt; font-weight: bold;">%s</span>' % lod["name"], align="center", parent=lodRow)

            lodLevels = cmds.columnLayout(adj=True, parent=lodRow)

            for levelIndex in range(0, len(lod["levels"])):
                lodLevel = lod["levels"][levelIndex]
                lodLevelRow = cmds.rowLayout(numberOfColumns=5, columnWidth5=[160, 75, 75, 120, 75], columnAlign5=["center", "center", "center", "center", "center"], columnAttach5=["both", "both", "both", "both", "both"], ad5=1, parent=lodLevels)

                cmds.button(parent=lodLevelRow, label=lodLevel["rootName"], width=100, height=20, backgroundColor=[0.26, 0.26, 0.26], command=partial(self.__selectObject, lodLevel["root"]))
                cmds.text(label="%dm" % lodLevel["clipDistance"], parent=lodLevelRow)
                cmds.text(label="%dm" % lodLevel["distance"], parent=lodLevelRow)
                cmds.text(label="%d Object(s)" % (len(lodLevel["mergeGroupObjects"]) + 1), parent=lodLevelRow)
                lodLevel["button"] = cmds.button(parent=lodLevelRow, label="Enable", height=30, command=partial(self.__setLODLevel, lod, levelIndex))

        cmds.separator(parent=self.parentFrame)
        self.__generateToolsUI()
        cmds.separator(parent=self.parentFrame)

    def __generateToolsUI(self):
        cmds.text(label='Tools', align="center", parent=self.parentFrame)

        toolsRow = cmds.formLayout(parent=self.parentFrame)

        addPostfixButton = cmds.button(parent=toolsRow, label="Add Postfix", width=200, height=30, command=self.__setLODPostfix)
        reloadButton = cmds.button(parent=toolsRow, label="Reload Data", width=200, height=30, command=self.__loadLODs)

        if len(self.missingPostfixObjects) > 0:
            autoAddButton = cmds.button(parent=toolsRow, label="Auto Add Postfix to %d Objects" % len(self.missingPostfixObjects), width=200, height=30, command=self.__autoAddLODPostfix)

            cmds.formLayout(toolsRow, edit=True, attachPosition=((addPostfixButton, 'left', 0, 0),  (addPostfixButton, 'right', 5, 33),
                                                                 (reloadButton, 'left', 0, 33), (reloadButton, 'right', 5, 66),
                                                                 (autoAddButton, 'left', 0, 66), (autoAddButton, 'right', 0, 100)))
        else:
            cmds.formLayout(toolsRow, edit=True, attachPosition=((addPostfixButton, 'left', 0, 0),  (addPostfixButton, 'right', 5, 50),
                                                                 (reloadButton, 'left', 0, 50), (reloadButton, 'right', 0, 100)))

    def __generateProgressBar(self):
        self.__clearFrameLayout(self.parentFrame)
        self.progressBar = cmds.progressBar(maxValue=len(cmds.ls(transforms=True, long=True)), width=400, parent=self.parentFrame)
        self.progressBarValue = 0
        cmds.refresh()

    def __updateProgressBar(self):
        if self.progressBar is not None:
            self.progressBarValue = self.progressBarValue + 1
            if self.progressBarValue % 20 == 0:
                cmds.progressBar(self.progressBar, edit=True, step=20)
                cmds.refresh()

    def __loadLODs(self, *args):
        self.__generateProgressBar()

        self.lodData, self.distanceObjects, self.missingPostfixObjects = self.__reloadData()
        self.validData = True

        self.__generateDynamicUI()
        self.__onSliderChange(0)

        if hasattr(self, 'sceneScriptJob'):
            cmds.scriptJob(kill=self.sceneScriptJob, force=True)

        self.sceneScriptJob = cmds.scriptJob(runOnce=True, e=["SceneOpened", self.__onSceneChange])

    def __setLODLevel(self, lod, targetLevelIndex, *args):
        for levelIndex in range(0, len(lod["levels"])):
            lodLevel = lod["levels"][levelIndex]
            for object in lodLevel["mergeGroupObjects"]:
                self.__setShapeVisibility(object, levelIndex == targetLevelIndex)

            self.__setShapeVisibility(lodLevel["root"], levelIndex == targetLevelIndex)

            cmds.button(lodLevel["button"], e=True, enable=levelIndex != targetLevelIndex, label="Enable")

    def __selectObject(self, object, *args):
        cmds.select(object)

    def __setShapeVisibility(self, object, state):
        shapes = cmds.listRelatives(object, c=True, pa=True)
        if shapes is not None:
            for shape in shapes:
                if cmds.nodeType(shape) == "mesh":
                    cmds.setAttr(shape + ".visibility", state)
        else:
            cmds.warning("LOD node without any shapes:", object)

    def __onSliderChange(self, distance):
        for lod in self.lodData:
            for levelIndex in range(0, len(lod["levels"])):
                lodLevel = lod["levels"][levelIndex]
                if distance >= lodLevel["distance"]:
                    self.__setLODLevel(lod, levelIndex)

        for objectData in self.distanceObjects:
            cmds.setAttr(objectData["object"] + ".visibility", distance <= objectData["clipDistance"])

        cmds.text(self.sliderValueText, e=True, label="Distance: %dm" % distance)
        cmds.floatSlider(self.slider, e=True, value=distance)

    def __onSliderChanged(self, distance):
        # reset the slider again while player releases mouse button
        self.__onSliderChange(0)

    def __onSceneChange(self, *args):
        delattr(self, "sceneScriptJob")

        self.validData = False
        self.__createCustomUI(self.parentFrame)

    def __setLODPostfix(self, *args):
        objects = cmds.ls(transforms=True, sl=True, long=True)
        for object in objects:
            self.__setLODPostfixRecursively(object)

    def __setLODPostfixRecursively(self, object):
        if cmds.objExists(object):
            children = cmds.listRelatives(object, c=True, f=True, type="transform")
            if children is not None:
                for child in children:
                    self.__setLODPostfixRecursively(child)

            cmds.rename(object, object.split("|")[-1]+"_lod")

    def __autoAddLODPostfix(self, *args):
        if len(self.missingPostfixObjects) > 0:
            self.missingPostfixObjects.sort()
            for i in range(len(self.missingPostfixObjects)-1, -1, -1):
                object = self.missingPostfixObjects[i]
                cmds.rename(object, object.split("|")[-1]+"_lod")
            self.__loadLODs()

    def __reloadData(self, *args):
        lods = []
        distanceObjects = []
        missingPostfixObjects = []

        objects = cmds.ls(transforms=True, long=True)

        for object in objects:
            self.__updateProgressBar()
            if "_ignore" not in object:
                clipDistance = I3DExporter.I3DGetAttributeValue(object, 'i3D_clipDistance', 0)
                if clipDistance > 0:
                    if cmds.getAttr(object + ".visibility"):
                        distanceObjects.append({"object": object,
                                                "clipDistance": clipDistance})

                if I3DExporter.I3DGetAttributeValue(object, 'i3D_lod', ''):
                    lod = {}
                    lod["name"] = object.split("|")[-1]
                    lod["levels"] = []

                    lodObjects = cmds.listRelatives(object, c=True, f=True)
                    for i in range(0, len(lodObjects)):
                        lodObject = lodObjects[i]

                        lodLevel = {}
                        lodLevel["root"] = lodObject
                        lodLevel["rootName"] = lodObject.split("|")[-1]
                        if i > 0:
                            lodLevel["distance"] = I3DExporter.I3DGetAttributeValue(object, 'i3D_lod%d' % i, 0)
                        else:
                            lodLevel["distance"] = 0

                        lodLevel["clipDistance"] = I3DExporter.I3DGetAttributeValue(lodObject, 'i3D_clipDistance', 0)

                        mergeGroupIndex = I3DExporter.I3DGetAttributeValue(lodObject, 'i3D_mergeGroup', 0)
                        isMergeGroupRoot = I3DExporter.I3DGetAttributeValue(lodObject, 'i3D_mergeGroupRoot', False)

                        lodLevel["mergeGroup"] = mergeGroupIndex
                        lodLevel["mergeGroupObjects"] = []

                        if mergeGroupIndex > 0:
                            if isMergeGroupRoot:
                                for obj in objects:
                                    if "_ignore" not in obj:
                                        _mergeGroupIndex = I3DExporter.I3DGetAttributeValue(obj, 'i3D_mergeGroup', '')
                                        if _mergeGroupIndex == mergeGroupIndex:
                                            if obj != lodObject:
                                                lodLevel["mergeGroupObjects"].append(obj)

                                                if i > 0:
                                                    if "_lod" not in obj:
                                                        cmds.warning("Object '%s' has no '_lod' postfix!" % obj)
                                                        missingPostfixObjects.append(obj)

                            else:
                                cmds.warning("Object '%s' is part of lod and merge group, but not defined as merge group root!" % lodObject)

                        lod["levels"].append(lodLevel)

                    lods.append(lod)

        return lods, distanceObjects, missingPostfixObjects

    def __clearFrameLayout(self, layout):
        oldElements = cmds.frameLayout(layout, q=True, ca=True)
        if oldElements is not None:
            for elem in oldElements:
                cmds.deleteUI(elem)


def getI3DExporterPlugin():
    return LODTools()

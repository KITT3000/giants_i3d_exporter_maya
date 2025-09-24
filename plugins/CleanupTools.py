#
# Integration Tools - Cleanup
# Collection of scripts for the integration process
#
# @created 14/03/2022
# @author Stefan Maurus
#
# Copyright (C) GIANTS Software GmbH, Confidential, All Rights Reserved.
#

import maya.cmds as cmds
import maya.mel as mel
import I3DExporter
import I3DUtils
import vehicleShaderTools
import os
import time


class CleanupTools:
    DEFAULT_NAMESPACES = ["UI", "shared"]
    FS22_RENAMED_LIGHTS = {"frontLight_01": "frontLight01", "frontLightCone_01": "frontLight02", "frontLightOval_01": "frontLight03", "frontLightOval_02": "frontLight04", "frontLightOval_03": "frontLight05", "frontLightRectangle_01": "frontLight06White", "frontLightRectangle_01Orange": "frontLight06Orange", "frontLightRectangle_02": "frontLight07", "rear2ChamberLed_01": "rearLight01", "rear2ChamberLight_02": "rearLight02", "rear2ChamberLight_03": "rearLight03", "rear2ChamberLight_04": "rearLight04", "rear2ChamberLight_05": "rearLight05", "rear2ChamberLight_06": "rearLight06", "rear2ChamberLight_07": "rearLight07", "rear3ChamberLight_01": "rearLight08", "rear3ChamberLight_02": "rearLight09", "rear3ChamberLight_03": "rearLight10", "rear3ChamberLight_04": "rearLight11", "rear3ChamberLight_05": "rearLight12", "rear4ChamberLight_01": "rearLight13", "rear4ChamberLight_02": "rearLight14", "rear5ChamberLight_01": "rearLight15", "rear5ChamberLight_02": "rearLight16", "rearLEDLight_01": "rearLight17", "rearLight_01": "rearLight18", "rearLightCircle_01Orange": "rearLight19Orange", "rearLightCircle_01Red": "rearLight19Red", "rearLightCircleLEDRed_01": "rearLight20", "rearLightCircleOrange_01": "rearLight21Orange", "rearLightCircleRed_01": "rearLight21Red", "rearLightCircleWhite_02": "rearLight22White", "rearLightCircleRed_02": "rearLight22Red", "rearLightCircleOrange_02": "rearLight22Orange", "rearLightOvalLEDWhite_01": "rearLight22White", "rearLightOvalLEDRed_01": "rearLight23Red", "rearLightOvalLEDOrange_01": "rearLight23Orange", "rearLightOvalLEDChromeWhite_01": "rearLight24", "rearLightOvalLEDRed_02": "rearLight25", "rearLightOvalWhite_01": "rearLight26White", "rearLightOvalRed_01": "rearLight26Red", "rearLightOvalOrange_01": "rearLight26Orange", "rearLightSquare_01Orange": "rearLight27Orange", "rearMultipointLight_04": "rearLight28", "rearMultipointLight_05": "rearLight29", "rearMultipointLEDLight_01": "rearLight30", "rearMultipointLight_01": "rearLight31", "rearMultipointLight_02": "rearLight32", "rearMultipointLight_03": "rearLight33", "rear3ChamberLight_06": "rearLight34", "rear3ChamberLight_07": "rearLight35", "rear2ChamberLight_01": "rearLight36", "sideMarker_01": "sideMarker01", "sideMarker_02": "sideMarker02", "sideMarker_03": "sideMarker03", "sideMarker_04": "sideMarker04", "sideMarker_05": "sideMarker05", "sideMarker_06": "sideMarker06", "sideMarker_04White": "sideMarker05White", "sideMarker_04Red": "sideMarker05Red", "sideMarker_04Orange": "sideMarker05Orange", "sideMarker_05White": "sideMarker06White", "sideMarker_05Orange": "sideMarker06Orange", "sideMarker_05Red": "sideMarker06Red", "sideMarker_06White": "sideMarker07White", "sideMarker_06Orange": "sideMarker07Orange", "sideMarker_06Red": "sideMarker07Red", "sideMarker_07White": "sideMarker08White", "sideMarker_07Orange": "sideMarker08Orange", "sideMarker_08White": "sideMarker09White", "sideMarker_08Orange": "sideMarker09Orange", "sideMarker_09White": "sideMarker10White", "sideMarker_09Orange": "sideMarker10Orange", "sideMarker_09Red": "sideMarker10Red", "sideMarker_10Orange": "sideMarker11Orange", "sideMarker_10Red": "sideMarker11Red", "sideMarker_14White": "sideMarker14White", "turnLight_01": "turnLight01", "sideMarker_09Orange_turn": "turnLight02", "rear2ChamberTurnLed_01": "turnLight03", "workingLightCircle_01": "workingLight01", "workingLightCircle_02": "workingLight02", "workingLightOval_01": "workingLight03", "workingLightOval_02": "workingLight04", "workingLightOval_03": "workingLight05", "workingLightOval_04": "workingLight06", "workingLightOval_05": "workingLight07", "workingLightSquare_01": "workingLight08", "workingLightSquare_02": "workingLight09", "workingLightSquare_03": "workingLight10", "workingLightSquare_04": "workingLight11", "rearPlateNumberLight_01": "plateNumberLight01"}
    FS25_RENAMED_LIGHTS = {"rearLight23Orange": "rearLight23", "rearLight23Red": "rearLight23", "rearLight23White": "rearLight23", "rearLight24": "rearLight23", "rearLight26Orange": "rearLight26", "rearLight26Red": "rearLight26", "rearLight26White": "rearLight26", "rearLight60White": "rearLight60", "rearLight63White": "rearLight63", "sideMarker04Red": "sideMarker04", "sideMarker04White": "sideMarker04", "sideMarker07Orange": "sideMarker07", "sideMarker07Red": "sideMarker07", "sideMarker07White": "sideMarker07", "sideMarker08Orange": "sideMarker08", "sideMarker08White": "sideMarker08", "sideMarker09Orange": "sideMarker09", "sideMarker09White": "sideMarker09", "sideMarker11Orange": "sideMarker11", "sideMarker11Red": "sideMarker11", "sideMarker21Red": "sideMarker21", "sideMarker30Orange": "sideMarker30", "sideMarker30White": "sideMarker30", "sideMarker32Orange": "sideMarker32", "sideMarker32Red": "sideMarker32", "sideMarker33": "sideMarker31", "turnLight01": "rearLight18"}

    def __init__(self):
        self.name = "Cleanup Tools"
        self.page = "Tools"
        self.prio = 4

        self.shelfCommand = "import I3DUtils; import CleanupTools; I3DUtils.reloadModule(CleanupTools); plugin = CleanupTools.CleanupTools(); plugin.%s(); del plugin;"

        self.buttons = []
        self.buttons.append({"name": "Cleanup",
                             "category": self.name,
                             "annotation": "Cleanup the maya file",
                             "button_function": self.cleanup,
                             "shelf_label": "Clean",
                             "shelf_command": self.shelfCommand % "cleanup"})

        self.buttons.append({"name": "Reset Cameras",
                             "category": self.name,
                             "annotation": "Reset the cameras to the default state",
                             "button_function": self.resetCameras,
                             "shelf_label": "Clean",
                             "shelf_command": self.shelfCommand % "resetCameras"})

        self.customUI = {"category": self.name,
                         "customUIFunc": self.createCustomUI}

        self.cleanupUVsTextField = "ui_cleanupUVsTextField"

        self.steps = []
        self.steps.append(["Cleanup Namespaces", self.__cleanupNamespaces])
        self.steps.append(["Cleanup Mesh States", self.__cleanupMeshStates])
        self.steps.append(["Cleanup Collision Material", self.__cleanupCollisionMaterial])
        self.steps.append(["Cleanup Display Layers", self.__cleanupDisplayLayers])
        self.steps.append(["Cleanup UV Sets", self.__cleanupUVSets])
        self.steps.append(["Cleanup Color Sets", self.__cleanupColorSets])
        self.steps.append(["Cleanup 3DS Max Atributes", self.__cleanup3DSMAXAttributes])
        self.steps.append(["Cleanup Names", self._cleanupNames])
        self.steps.append(["Cleanup References", self.__cleanupReferences])
        self.steps.append(["Cleanup Project Paths", self.__cleanupProjectPaths])
        self.steps.append(["Cleanup Obsolete Nodes", self.__cleanupObsoleteNodes])
        self.steps.append(["Cleanup History", self.__cleanupHistory])
        self.steps.append(["Fix shader list", self.__materialShaderListFix])
        self.steps.append(["Fix material templates", self.__materialTemplateFix])
        self.steps.append(["Reset polygon display", self.__cleanupPolygonDisplay])
        self.steps.append(["Remove unused nodes", self.__removeUnusedNodes])
        self.steps.append(["Remove Expressions", self.__removeExpressions])
        self.steps.append(["Clear Object Sets", self.__clearObjectSets])
        self.steps.append(["Reset Grid", self.__resetGrid])
        self.steps.append(["Update Handle Display", self.__updateHandleDisplay])
        self.steps.append(["Cleanup Cameras", self.__cleanupCameras])

    def getToolsButtons(self):
        return self.buttons

    def getShelfScripts(self):
        return self.buttons

    def getToolsCustomUI(self):
        return [self.customUI]

    def onExporterOpen(self):
        if cmds.objExists("standardSurface1"):
            cmds.setAttr("standardSurface1.specularIOR",1.0) # cause specularIOR > 1.0 enables Realtime-reflection, by default this value is 1.5
        # set hardware renderer settings correctly, so the vehicle ogsfx shaders are correctly displayed
        try:
            cmds.setAttr("hardwareRenderingGlobals.defaultLightIntensity", 1)  # causes decal textures to be too bright
            cmds.setAttr("hardwareRenderingGlobals.transparencyAlgorithm", 1)  # causes vehicles to be invisible after conversion
        except Exception as e:
            print(e)

    def cleanup(self, *args):
        self.__createProgressWindow(len(self.steps) + 1)

        for step in self.steps:
            self.__nextStep(step[0])
            try:
                step[1]()
            except Exception as err:
                print("Error during '%s' step:" % step[0])
                print(str(err))

        self.__nextStep("")

    def __createProgressWindow(self, numSteps):
        self.window = cmds.progressWindow(title="Cleanup", progress=0, maxValue=numSteps, status="", isInterruptable=False)
        self.progressStep = 0
        self.progressMaxStep = numSteps
        self.progressStartTime = time.time()

    def __nextStep(self, title):
        self.progressStep = self.progressStep + 1
        cmds.progressWindow(self.window, edit=True, progress=self.progressStep, status=title)

        if hasattr(self, "progressStepStartTime"):
            self.__print("Step '%s' Time: %d ms" % (self.progressStepTitle, (time.time() - self.progressStepStartTime) * 1000))

        if self.progressStep >= self.progressMaxStep:
            cmds.progressWindow(self.window, endProgress=True)
            self.__print("Total Time: %d ms" % ((time.time() - self.progressStartTime) * 1000))

            delattr(self, "progressStepStartTime")
            delattr(self, "progressStepTitle")

        self.progressStepStartTime = time.time()
        self.progressStepTitle = title

    def __print(self, text):
        print("CleanupTools: " + text)

    def __onChangePrint(self, text):
        print("    CleanupTools: " + text)

    def __unlockAndSetAttribute(self, node, attribute, *args):
        cmds.setAttr(node + "." + attribute, lock=False)
        cmds.setAttr(node + "." + attribute, *args)

    def resetCameras(self, *args):
        ''' reset camera poses to the default values '''

        self.__removeExpressions()

        persp = "|persp"
        if cmds.objExists(persp):
            self.__unlockAndSetAttribute(persp, "t", 28, 21, 28)
            self.__unlockAndSetAttribute(persp, "r", -28, 45, 0)

        top = "|top"
        if cmds.objExists(top):
            self.__unlockAndSetAttribute(top, "t", 0, 1000.1, 0)
            self.__unlockAndSetAttribute(top, "r", -90, 0, 0)

        front = "|front"
        if cmds.objExists(front):
            self.__unlockAndSetAttribute(front, "t", 0, 0, 1000.1)
            self.__unlockAndSetAttribute(front, "r", 0, 0, 0)

        side = "|side"
        if cmds.objExists(side):
            self.__unlockAndSetAttribute(side, "t", 1000.1, 0, 0)
            self.__unlockAndSetAttribute(side, "r", 0, 90, 0)

    def __cleanupCameras(self, *args):
        ''' reset camera attributes to default values '''
        self.__removeExpressions()

        persp = "|persp"
        if cmds.objExists(persp):
            self.__unlockAndSetAttribute(persp, "v", False)
            self.__unlockAndSetAttribute(persp, "fl", 35)
            self.__unlockAndSetAttribute(persp, "coi", 38)
            self.__unlockAndSetAttribute(persp, "ncp", 0.1)
            self.__unlockAndSetAttribute(persp, "fcp", 10000)
            self.__unlockAndSetAttribute(persp, "o", False)
            self.__unlockAndSetAttribute(persp, "cs", 1)
            self.__unlockAndSetAttribute(persp, "cap", 1.417, 0.945)

        top = "|top"
        if cmds.objExists(top):
            self.__unlockAndSetAttribute(top, "v", False)
            self.__unlockAndSetAttribute(top, "ncp", 0.1)
            self.__unlockAndSetAttribute(top, "fcp", 10000)
            self.__unlockAndSetAttribute(top, "o", True)
            self.__unlockAndSetAttribute(top, "o", True)
            self.__unlockAndSetAttribute(top, "cs", 1)

        front = "|front"
        if cmds.objExists(front):
            self.__unlockAndSetAttribute(front, "v", False)
            self.__unlockAndSetAttribute(front, "ncp", 0.1)
            self.__unlockAndSetAttribute(front, "fcp", 10000)
            self.__unlockAndSetAttribute(front, "o", True)
            self.__unlockAndSetAttribute(front, "cs", 1)

        side = "|side"
        if cmds.objExists(side):
            self.__unlockAndSetAttribute(side, "v", False)
            self.__unlockAndSetAttribute(side, "ncp", 0.1)
            self.__unlockAndSetAttribute(side, "fcp", 10000)
            self.__unlockAndSetAttribute(side, "o", True)
            self.__unlockAndSetAttribute(side, "cs", 1)

        assemblies = cmds.ls(assemblies=True)
        for object in assemblies:
            children = cmds.listRelatives(object, f=True)
            if children is not None:
                for child in children:
                    if cmds.nodeType(child) == "camera":
                        if "persp" not in object and "top" not in object and "front" not in object and "side" not in object:
                            cmds.delete(object)
                            self.__onChangePrint("Removed top level camera '%s'" % (object))

    def __cleanupUVSets(self, *args):
        ''' removes uv sets without a name defined (they are also not visible in the Maya UI) '''

        shapes = cmds.ls(shapes=True)
        for shape in shapes:
            uvSets = cmds.ls(shape + ".uvst[*]", flatten=True)
            if uvSets is not None:
                for uvSet in uvSets:
                    uvSetName = cmds.getAttr(uvSet + ".uvsn")
                    if uvSetName is None:
                        cmds.removeMultiInstance(uvSet, b=True)
                        self.__onChangePrint("Removed hidden uv set from mesh '%s'" % (shape))

        for shape in shapes:
            cmds.select(shape)
            uvSets = cmds.polyUVSet(query=True, allUVSets=True)
            if uvSets is not None and len(uvSets) > 0:
                for i in range(0, len(uvSets)):
                    targetName = "map%d" % (i + 1)
                    if uvSets[i] != targetName:
                        self.__onChangePrint("Rename uvSet '%s' of shape '%s' to '%s'" % (uvSets[i], shape, targetName))
                        cmds.polyUVSet(rename=True, newUVSet=targetName, uvSet=uvSets[i])

        # rename TexCoord source for all glsl shaders
        shaders = cmds.ls(type="GLSLShader")
        for shader in shaders:
            for i in range(0, 3):
                attribute = shader + ".TexCoord%d_Source" % i
                targetName = "uv:map%d" % (i + 1)

                source = cmds.getAttr(attribute)
                if source != targetName:
                    cmds.setAttr(attribute, targetName, type="string")
                    self.__onChangePrint("Rename TexCoord%d_Source of shader '%s' to 'uv:map%d'" % (i, shader, (i + 1)))

    def __cleanupColorSets(self):
        ''' removes color sets without a name defined (they are also not visible in the Maya UI) '''

        shapes = cmds.ls(shapes=True)
        for shape in shapes:
            colorSets = cmds.ls(shape + ".clst[*]", flatten=True)
            if colorSets is not None:
                for colorSet in colorSets:
                    colorSetName = cmds.getAttr(colorSet + ".clsn")
                    if colorSetName is None:
                        cmds.removeMultiInstance(colorSet, b=True)
                        self.__onChangePrint("Removed hidden color set from mesh '%s'" % (shape))

    def __cleanupDisplayLayers(self):
        ''' removes all empty display layers and sorts the merge group objects (all objects with merge group 0 will be moved to 'MERGEGROUP_0') '''

        # if MERGEGROUP_0 display layer does not exit yet, we create it
        if not cmds.objExists('MERGEGROUP_0'):
            self.__onChangePrint("Created default 'MERGEGROUP_0' display layer")
            cmds.createDisplayLayer(n='MERGEGROUP_0', number=1, empty=True)
            cmds.setAttr('MERGEGROUP_0.displayType', 0)
            cmds.setAttr('MERGEGROUP_0.color', I3DExporter.MERGEGROUP_COLORS[0])

        layers = cmds.ls(type="displayLayer")
        for layer in layers:
            try:
                for index, colorIndex in I3DExporter.MERGEGROUP_COLORS.items():
                    if layer == "MERGEGROUP_%d" % index:
                        cmds.setAttr('MERGEGROUP_%d.color' % index, colorIndex)
            except:
                pass

            if layer != "defaultLayer" and layer != "MERGEGROUP_0":
                # remove all objects that should not be in the display layer
                objects = cmds.editDisplayLayerMembers(layer, query=True, fn=True)
                if objects is not None:
                    for object in objects:
                        mergeGroup = I3DExporter.I3DGetAttributeValue(object, 'i3D_mergeGroup', '')
                        if mergeGroup == "" or mergeGroup == 0:
                            cmds.editDisplayLayerMembers('MERGEGROUP_0', object, noRecurse=True)
                            self.__onChangePrint("Moved object '%s' from display layer '%s' to '%s'" % (object, layer, 'MERGEGROUP_0'))

                # remove display layer if it is empty
                if cmds.editDisplayLayerMembers(layer, query=True) is None:
                    try:
                        if not cmds.referenceQuery(layer, isNodeReferenced=True):
                            cmds.lockNode(layer, l=False)
                            cmds.delete(layer)
                            self.__onChangePrint("Removed empty display layer '%s'" % layer)
                    except:
                        self.__onChangePrint("Failed to delete display layer '%s'" % layer)

        # make sure the shapes are in the same display layer as the parent transform
        objects = cmds.ls(transforms=True)
        for object in objects:
            if ":" not in object:  # ignore references
                connections = cmds.listConnections(object)
                if connections is not None:
                    objectLayer = None
                    shapeLayer = None
                    shape = None
                    for connection in connections:
                        if "MERGEGROUP_" in str(connection):
                            objectLayer = str(connection)

                    shapes = cmds.listRelatives(object, s=1, f=True)
                    if shapes is not None:
                        shapeConnections = cmds.listConnections(shapes[0])
                        if shapeConnections is not None:
                            for shapeConnection in shapeConnections:
                                if "MERGEGROUP_" in str(shapeConnection):
                                    shapeLayer = str(shapeConnection)
                                    shape = shapes[0]

                    if objectLayer is not None and shapeLayer is not None:
                        if objectLayer != shapeLayer:
                            self.__onChangePrint("Object '%s' has difference display layer than shape! (Object '%s', Shape '%s')" % (object, objectLayer, shapeLayer))
                            cmds.editDisplayLayerMembers(objectLayer, shape)

                    if objectLayer is None:
                        self.__onChangePrint("Object '%s' has no display layer yet. Adding it to MERGEGROUP_0" % (object))
                        cmds.editDisplayLayerMembers('MERGEGROUP_0', object, noRecurse=True)
                else:
                    shapes = cmds.listRelatives(object, s=1, f=True)
                    if shapes is not None:
                        self.__onChangePrint("Object '%s' has no display layer yet. Adding it to MERGEGROUP_0" % (object))
                        cmds.editDisplayLayerMembers('MERGEGROUP_0', object, noRecurse=True)

        # reorder the display layers based on merge group index
        for displayLayer in cmds.ls(type="displayLayer"):
            if "MERGEGROUP_" in displayLayer:
                start = displayLayer.find("MERGEGROUP_")
                number = int(displayLayer[start + len("MERGEGROUP_"):])
                cmds.setAttr(displayLayer + ".displayOrder", 10 - number)

        mel.eval('reorderLayers -1')

    def __cleanupNamespaces(self):
        ''' removes all existing namespaces '''

        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        for namespace in namespaces:
            if namespace not in CleanupTools.DEFAULT_NAMESPACES:
                self._removeNamespace(namespace)

    def __getIsNonRenderableObject(self, object):
        foundAttributes = cmds.listAttr(object, ud=True, string="i3D*")
        if foundAttributes is not None:
            if "i3D_nonRenderable" in foundAttributes:
                if cmds.getAttr(object + ".i3D_nonRenderable") is True:
                    if "i3D_terrainDecal" not in foundAttributes or cmds.getAttr(object + ".i3D_terrainDecal") is False:
                        return True
        return False

    def __cleanupMeshStates(self):
        ''' check all bounding volumes and collisions if they are properly set up (hidden transform and visible shape) '''

        objects = cmds.ls(transforms=True)
        for object in objects:
            foundAttributes = cmds.listAttr(object, ud=True, string="i3D*")
            if foundAttributes is not None:
                # hide bounding volumes completely
                if "i3D_boundingVolume" in foundAttributes:
                    if cmds.getAttr(object + ".i3D_boundingVolume") != "":
                        if cmds.getAttr(object + ".visibility") is True:
                            cmds.setAttr(object + ".visibility", False)
                            self.__onChangePrint("Hide boundingVolume node '%s'" % (object))

                # hide the shapes of all nonRenderable nodes (collisions etc)
                if self.__getIsNonRenderableObject(object):
                    if cmds.getAttr(object + ".visibility") is False:
                        self.__onChangePrint("Show transform of nonRenderable node '%s'" % (object))
                        cmds.setAttr(object + ".visibility", True)

                    shapes = cmds.listRelatives(object, type="shape", f=True)
                    if shapes is not None:
                        for shape in shapes:
                            if cmds.getAttr(shape + ".visibility") is True:
                                cmds.setAttr(shape + ".visibility", False)
                                self.__onChangePrint("Hide shape of nonRenderable node '%s'" % (object))

                    # all "collisions" transform groups which have nonRenderables included should be visible as we just hide the shapes
                    parents = cmds.listRelatives(object, parent=True, f=True)
                    if parents is not None and len(parents) > 0:
                        if "collisions" in parents[0]:
                            cmds.setAttr(parents[0] + ".visibility", True)
                            self.__onChangePrint("Show collision transform group '%s'" % (parents[0]))

                # remove all template attributes
                if cmds.attributeQuery("template", node=object, exists=True):
                    if cmds.getAttr(object + ".template") is True:
                        cmds.setAttr(object + ".template", False)
                        self.__onChangePrint("Removed template attribute from '%s'" % (object))

    def __unlockAllNormals(self):
        objects = cmds.ls(shapes=True)
        for object in objects:
            vertices = cmds.ls(object + ".vtx[*]", flatten=True)
            if vertices is not None and len(vertices) > 0:
                numLockedVertices = 0

                allLocked = cmds.polyNormalPerVertex(vertices, query=True, allLocked=True)
                if not allLocked:
                    lockStates = cmds.polyNormalPerVertex(vertices, query=True, freezeNormal=True)
                    for i in range(0, len(lockStates)):
                        if lockStates[i]:
                            numLockedVertices += 1
                            break
                else:
                    numLockedVertices += 1

    def __getIsPhysicsShape(self, object):
        foundAttributes = cmds.listAttr(object, ud=True, string="i3D*")
        if foundAttributes is not None:
            if "i3D_boundingVolume" in foundAttributes:
                if cmds.getAttr(object + ".i3D_boundingVolume") != "":
                    return True

            if "i3D_trigger" in foundAttributes:
                if cmds.getAttr(object + ".i3D_trigger") is True:
                    return True

            if "i3D_collision" in foundAttributes:
                if cmds.getAttr(object + ".i3D_collision") is True:
                    if self.__getIsNonRenderableObject(object):
                        return True
        return False

    def __cleanupCollisionMaterial(self):
        if cmds.objExists("lambert1.color"):
            color = cmds.getAttr("lambert1.color")
            if color is not None:
                if color[0][0] != 0.5 or color[0][1] != 0.5 or color[0][1] != 0.5:
                    self.__onChangePrint("Reset color of lamber1")
                    cmds.setAttr("lambert1.color", 0.500, 0.500, 0.500, type="float3")

            foundAttributes = cmds.listAttr("lambert1", ud=True)
            if foundAttributes is not None:
                for attribute in foundAttributes:
                    self.__onChangePrint("Removed custom attribute '%s' from lambert1" % attribute)
                    cmds.deleteAttr("lambert1." + attribute)

        objects = cmds.ls(transforms=True)
        for object in objects:
            if self.__getIsPhysicsShape(object):
                self.__assignDefaultMaterial(object)

    def __assignDefaultMaterial(self, object):
        shapes = cmds.listRelatives(object, type="shape", f=True)
        if shapes is not None:
            shadingEngines = cmds.listConnections(shapes[0], type='shadingEngine')
            if shadingEngines is not None:
                materials = cmds.ls(cmds.listConnections(shadingEngines), mat=True)
                if len(materials) != 1 or materials[0] != "lambert1":
                    self.__onChangePrint("Assign lambert1 to '%s'" % (object))

                    faces = cmds.ls(shapes[0] + ".f[*]", flatten=True)
                    cmds.sets(shapes[0] + ".f[0:%d]" % len(faces), e=True, forceElement="initialShadingGroup")

    def _removeNamespace(self, namespace):
        ''' empties and removes given namespace and all it's child namespaces '''

        childNamespaces = cmds.namespaceInfo(namespace, lon=True)
        if childNamespaces is not None:
            for childNamespace in childNamespaces:
                self._removeNamespace(childNamespace)

        try:
            cmds.namespace(mv=(namespace, ":"), f=True)
            cmds.namespace(rm=str(namespace))

            self.__onChangePrint("Empty and remove namespace '%s'" % namespace)
        except RuntimeError as err:
            self.__onChangePrint("Could not remove namespace '%s' (%s)" % (namespace, str(err)))

    def _cleanupNames(self):
        ''' Remove 'pasted__' prefix from all nodes in the scene '''

        while True:
            renamed = False
            for node in cmds.ls(long=True):
                name = node.split("|")[-1]
                if "pasted__" in name:
                    newName = name.replace("pasted__", "")
                    self.__onChangePrint("Renamed node '%s' to '%s'" % (node, newName))

                    cmds.lockNode(node, lock=False)
                    cmds.rename(node, newName)

                    renamed = True
                    break
            if not renamed:
                break

    def __cleanup3DSMAXAttributes(self):
        ''' removes all attributes coming from FBX import '''
        attributes = ["mrFBXASC032displacementFBXASC032useFBXASC032globalFBXASC032settings",
                      "mrFBXASC032displacementFBXASC032viewFBXASC032dependent",
                      "mrFBXASC032displacementFBXASC032method",
                      "mrFBXASC032displacementFBXASC032smoothingFBXASC032on",
                      "mrFBXASC032displacementFBXASC032edgeFBXASC032length",
                      "mrFBXASC032displacementFBXASC032maxFBXASC032displace",
                      "mrFBXASC032displacementFBXASC032parametricFBXASC032subdivisionFBXASC032level",
                      "UDP3DSMAX",
                      "MaxHandle",
                      "paramrenderwidth",
                      "paramrenderheight",
                      "paramfacecolor",
                      "paramedgecolor",
                      "paramedgewidth",
                      "currentUVSet",
                      "fbxID",
                      "notes"]

        objects = cmds.ls(transforms=True)
        for object in objects:
            foundAttributes = cmds.listAttr(object, ud=True)
            if foundAttributes is not None:
                for foundAttribute in foundAttributes:
                    if foundAttribute in attributes:
                        cmds.deleteAttr(object + "." + foundAttribute)
                        self.__onChangePrint("Removed attribute '%s' from object '%s'" % (foundAttribute, object))

    def cleanupReferences(self):
        self.__cleanupReferences()

    def __cleanupReferences(self):
        ''' replaces old light references and removed corrupted references '''

        attributes = ["i3D_referenceFilename", "i3D_referencedLightPath"]

        runTimeReferencePaths = {
            "$data/shared/assets/lights/lizard/": False,
            "$data/shared/assets/reflectors/lizard/": True,
            "$data/shared/assets/lights/hella/": False,
            "$data/shared/assets/lights/krone/": False,
            "$data/shared/assets/wheelChocks/": False,
            "$data/shared/assets/beaconLights/lizard/": False,
            "$data/shared/assets/": True,
            "$data/shared/assets/skfLincoln/": True,
            "$data/shared/connectionHoses/": False,
            "$data/shared/assets/lights/rudolfHormann/": False,
            "$data/shared/assets/lights/terraLed/": False,
            "$data/shared/assets/lights/lizard/buildings/": False,
            "$data/shared/assets/carHitches/lizard/": False,
        }

        def getIsRuntimeReference(object):
            if self._attributeExists(object, "i3D_referenceFilename"):
                attribute = self._getAttributeValue(object, "i3D_referenceFilename", None)
                if attribute is not None:
                    filename = attribute.split("/")[-1]
                    parentDirectory = attribute.split(filename)[0]
                    if parentDirectory in runTimeReferencePaths:
                        return runTimeReferencePaths[parentDirectory]

            return True

        objects = cmds.ls(transforms=True)

        for object in objects:
            foundAttributes = cmds.listAttr(object, ud=True, string="i3*")
            if foundAttributes is not None:
                updateAttributes = False
                if "i3d_referencedLightPath" in foundAttributes:
                    cmds.renameAttr(object + ".i3d_referencedLightPath", "i3D_referencedLightPath")
                    self.__onChangePrint("Renamed attribute '%s' to start with 'i3D_' on object %s" % ("i3d_referencedLightPath", object))
                    updateAttributes = True

                if "i3d_refModel" in foundAttributes:
                    cmds.renameAttr(object + ".i3d_refModel", "i3D_refModel")
                    self.__onChangePrint("Renamed attribute '%s' to start with 'i3D_' on object %s" % ("i3d_refModel", object))
                    updateAttributes = True

                if "i3d_refBrand" in foundAttributes:
                    cmds.renameAttr(object + ".i3d_refBrand", "i3D_refBrand")
                    self.__onChangePrint("Renamed attribute '%s' to start with 'i3D_' on object %s" % ("i3d_refBrand", object))
                    updateAttributes = True

                if "i3d_locatorPrefix" in foundAttributes:
                    cmds.renameAttr(object + ".i3d_locatorPrefix", "i3D_locatorPrefix")
                    self.__onChangePrint("Renamed attribute '%s' to start with 'i3D_' on object %s" % ("i3d_locatorPrefix", object))
                    updateAttributes = True

                if updateAttributes:
                    updatedAttributes = cmds.listAttr(object, ud=True, string="i3*")
                    if updatedAttributes is not None:
                        foundAttributes = updatedAttributes

                for foundAttribute in foundAttributes:
                    if foundAttribute in attributes:
                        attribute = self._getAttributeValue(object, foundAttribute, None)
                        if attribute is not None:
                            for old, new in CleanupTools.FS22_RENAMED_LIGHTS.items():
                                if old in attribute:
                                    attribute = attribute.replace(old, new)
                                    cmds.setAttr(object + "." + foundAttribute, attribute, type='string')
                                    self.__onChangePrint("Replaced old reference: object %s oldRef %s newRef %s attribute %s (FS22)" % (object, old, new, foundAttribute))

                            for old, new in CleanupTools.FS25_RENAMED_LIGHTS.items():
                                if old in attribute:
                                    attribute = attribute.replace(old, new)
                                    cmds.setAttr(object + "." + foundAttribute, attribute, type='string')
                                    self.__onChangePrint("Replaced old reference: object %s oldRef %s newRef %s attribute %s (FS25)" % (object, old, new, foundAttribute))

                if "i3D_referencedLightPath" in foundAttributes:
                    if "i3D_referenceFilename" not in foundAttributes:
                        projectDirectory = cmds.workspace(q=True, rd=True)
                        attribute = self._getAttributeValue(object, "i3D_referencedLightPath", None)
                        if attribute is not None:
                            attribute = projectDirectory + attribute.replace(".ma", ".i3d")
                            if os.path.isfile(attribute):
                                parts = attribute.split("bin/data/")
                                if len(parts) == 2:
                                    gameRelativePath = "$data/" + parts[1]

                                    filename = gameRelativePath.split("/")[-1]
                                    parentDirectory = gameRelativePath.split(filename)[0]

                                    isRuntimeReference = False
                                    if parentDirectory in runTimeReferencePaths:
                                        isRuntimeReference = runTimeReferencePaths[parentDirectory]

                                    cmds.addAttr(object, shortName="i3D_referenceFilename", niceName="i3D_referenceFilename", longName="i3D_referenceFilename", dt="string")
                                    cmds.setAttr(object + ".i3D_referenceFilename", gameRelativePath, type="string")

                                    cmds.addAttr(object, shortName="i3D_referenceRuntimeLoaded", niceName="i3D_referenceRuntimeLoaded", longName="i3D_referenceRuntimeLoaded", attributeType="bool")
                                    cmds.setAttr(object + ".i3D_referenceRuntimeLoaded", isRuntimeReference)

                                    self.__onChangePrint("Converted light reference to real reference on object '%s' (runtimeReference: %s)" % (object, isRuntimeReference))
                                    continue

                if "i3D_referenceFilename" in foundAttributes:
                    if "i3D_referenceRuntimeLoaded" not in foundAttributes:
                        cmds.addAttr(object, shortName="i3D_referenceRuntimeLoaded", niceName="i3D_referenceRuntimeLoaded", longName="i3D_referenceRuntimeLoaded", attributeType="bool")

                        isRuntimeReference = getIsRuntimeReference(object)
                        cmds.setAttr(object + ".i3D_referenceRuntimeLoaded", isRuntimeReference)

                        self.__onChangePrint("Added runtime reference attribute for object '%s' with value '%s'" % (object, isRuntimeReference))

        for reference in cmds.ls(type="reference"):
            try:
                cmds.referenceQuery(reference, nodes=True)
            except:
                cmds.lockNode(reference, lock=False)
                cmds.delete(reference)
                self.__onChangePrint("Deleted corrupted reference node '%s'" % (reference))
                pass

    def __cleanupProjectPaths(self, includeShaders=True):
        ''' function tries to solve texture paths that are not existing and paths in wrong projects to relative paths in current project '''

        projectDirectory = cmds.workspace(q=True, rd=True)

        textures = cmds.ls(fl=True, textures=True)
        for texture in textures:
            attribute = "%s.fileTextureName" % texture
            if "fileTextureName" in cmds.listAttr(texture):
                filename = cmds.getAttr(attribute)

                newFilename = self._getFileInCurrentProject(projectDirectory, filename)
                if newFilename != filename:
                    cmds.setAttr(attribute, newFilename, type="string")
                    self.__onChangePrint("Fixed file path '%s' to project path '%s'" % (filename, newFilename))

        if includeShaders:
            materials = cmds.ls(fl=True, materials=True)
            for material in materials:
                if cmds.attributeQuery("customShader", node=material, exists=True):
                    filename = cmds.getAttr("%s.customShader" % material)
                    if "$data/shaders/" not in filename:
                        newFilename = self._getFileInCurrentProject(projectDirectory, filename)

                        try:
                            newFilename = os.path.relpath(newFilename, cmds.file(q=True, sn=True))[3:]  # abs path the shader to relative path outgoing from maya file
                            newFilename = newFilename.replace("\\", "/")
                            newFilename = newFilename.replace("//", "/")
                            if newFilename != filename:
                                cmds.setAttr("%s.customShader" % material, newFilename, type="string")
                                self.__onChangePrint("Fixed shader path '%s' to project path '%s'" % (filename, newFilename))
                        except ValueError as err:
                            self.__onChangePrint("Project file: %s | Maya File: %s" % (newFilename, cmds.file(q=True, sn=True)))
                            self.__onChangePrint(str(err))

    def __cleanupObsoleteNodes(self):
        ''' removes all obsolete nodes from the scene '''

        scriptNodes = cmds.ls(type="script")
        if scriptNodes is not None:
            for scriptNode in scriptNodes:
                if "I3DExportSettings" in scriptNode and scriptNode != "I3DExportSettings":
                    cmds.delete(scriptNode)
                    self.__onChangePrint("Removed obsolete script node '%s'" % scriptNode)

        # remove obsolete script nodes (gsMaterialStorageNode)
        scriptNodes = cmds.ls(type="script")
        if scriptNodes is not None:
            for scriptNode in scriptNodes:
                if "gsMaterialStorageNode" in scriptNode:
                    cmds.delete(scriptNode)
                    self.__onChangePrint("Removed obsolete script node '%s'" % scriptNode)

        # remove all trackInfoManager nodes
        nodes = cmds.ls(type=["trackInfoManager", "mayaUsdLayerManager"])
        if nodes is not None:
            for node in nodes:
                cmds.delete(node)
                self.__onChangePrint("Removed obsolete node '%s'" % node)

        # delete all polyExtrudeEdge, polyExtrudeFace, polyExtrudeVertex, polyMergeVert, polyMoveVertex, blindDataTemplate, polyUnite nodes which have no connections
        nodes = cmds.ls(type=["polyExtrudeEdge", "polyExtrudeFace", "polyExtrudeVertex", "polyMergeVert", "polyMoveVertex", "blindDataTemplate", "polyUnite"])
        if nodes is not None:
            for node in nodes:
                connections = cmds.listConnections(node)
                if connections is None:
                    cmds.delete(node)
                    self.__onChangePrint("Removed obsolete node '%s'" % node)

        # remove all groupId nodes without connection
        nodes = cmds.ls(type="groupId")
        if nodes is not None:
            for node in nodes:
                connections = cmds.listConnections(node)
                if connections is None:
                    cmds.delete(node)
                    self.__onChangePrint("Removed obsolete groupId node '%s'" % node)

    def __cleanupHistory(self):
        ''' removes all history from all objects '''

        shapes = cmds.ls(shapes=True)
        for shape in shapes:
            if cmds.objExists(shape) and cmds.objectType(shape) == "mesh":
                cmds.bakePartialHistory(shape, prePostDeformers=True)

    def __materialShaderListFix(self):
        ''' checks if all materials are in the default shader list, if not they will be added '''

        I3DUtils.fixHiddenMaterialsInScene()

    def __materialTemplateFix(self):
        numMaterialsChanged = 0
        materials = cmds.ls(typ="GLSLShader")
        for material in materials:
            if ":" not in material:  # exclude reference files
                brandMaterialTemplate = self._getAttributeValue(material, "customParameterTemplate_brandColor_brandColor", None)
                materialTemplate = self._getAttributeValue(material, "customParameterTemplate_brandColor_material", None)
                if brandMaterialTemplate is not None and materialTemplate is not None:
                    self.__onChangePrint("Double definition of brandMaterial and material found for '%s'. Keeping only the brandMaterial." % material)

                    cmds.deleteAttr(material + ".customParameterTemplate_brandColor_material")

                    numMaterialsChanged += 1

        if numMaterialsChanged > 0:
            vehicleShaderTools.synhronizeMaterialTemplates()

    def __cleanupPolygonDisplay(self):
        ''' resets the polygon display attributes on all shapes '''

        attributeList = ["displayVertices",
                         "displayBorders",
                         "displayMapBorders",
                         "displayEdges",
                         "displayCenter",
                         "displayTriangles",
                         "displayUVs",
                         "displayItemNumbers",
                         "displayNonPlanar",
                         # "displayInvisibleFaces",
                         "displayNormal",
                         "displayTangent",
                         "displaySmoothMesh",
                         "displaySubdComps",
                         "displayImmediate",
                         ]

        defaultValues = {
            "displayVertices": False,
            "displayBorders": False,
            "displayMapBorders": False,
            "displayEdges": 1,
            "displayCenter": False,
            "displayTriangles": False,
            "displayUVs": False,
            "displayItemNumbers": 0,
            "displayNonPlanar": False,
            # "displayInvisibleFaces": False,
            "displayNormal": False,
            "displayTangent": False,
            "displaySmoothMesh": False,
            "displaySubdComps": False,
            "displayImmediate": False,
        }

        shapes = cmds.ls(shapes=True)
        for shape in shapes:
            foundAttributes = cmds.listAttr(shape, string="display*")
            if foundAttributes is not None:
                for foundAttribute in foundAttributes:
                    if foundAttribute in attributeList:
                        value = cmds.getAttr(shape + "." + foundAttribute)
                        if value is not None and value != defaultValues[foundAttribute]:
                            cmds.setAttr(shape + "." + foundAttribute, defaultValues[foundAttribute])

            cullingAttributes = cmds.listAttr(shape, string="*Culling")
            if cullingAttributes is not None:
                for attribute in cullingAttributes:
                    if attribute == "backfaceCulling":
                        value = cmds.getAttr(shape + "." + attribute)
                        if value is not None and value > 0:
                            cmds.setAttr(shape + "." + attribute, 0)
                    elif attribute == "vertexBackfaceCulling":
                        value = cmds.getAttr(shape + "." + attribute)
                        if value is False:
                            cmds.setAttr(shape + "." + attribute, True)

    def __removeUnusedNodes(self):
        ''' removes unused nodes from hypershade '''

        mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')

        # delete unused nodes can for some reason not delete all unused materials
        # so we do a additional manual check if a shading group is not assigned to any face
        shadingEngines = cmds.ls(type="shadingEngine")
        if shadingEngines is not None:
            for shadingEngine in shadingEngines:
                if shadingEngine != "initialParticleSE" and shadingEngine != "initialShadingGroup":
                    numFaces = 0
                    faceGroups = cmds.sets(shadingEngine, q=True)
                    if faceGroups is not None:
                        for faces in faceGroups:
                            numFaces += 1

                    if numFaces == 0:
                        self.__onChangePrint("Remove shading group '%s' which is not assigned to anything." % (shadingEngine))
                        cmds.delete(shadingEngine)

                        # remove materials and textures after the shading group is gone
                        mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')

    def __removeExpressions(self, *args):
        ''' removes all expressions found in the file '''

        expressions = cmds.ls(type="expression")
        for expression in expressions:
            cmds.delete(expression)
            self.__onChangePrint("Remove expression '%s" % (expression))

    def __clearObjectSets(self, *args):
        ''' removes all empty objectSets and those with only mesh parts included '''

        def isDefaultSet(set):
            if cmds.objExists(set) is False:
                return True

            if cmds.getAttr(set + ".renderableOnlySet"):
                return True

            if "default" in set:
                return True

            if "skinCluster" in set:
                return True

            if "tweak" in set:
                return True

            if "textureEditor" in set:
                return True

            return False

        sets = cmds.ls(type="objectSet")
        for set in sets:
            if not isDefaultSet(set):
                members = cmds.sets(set, q=True)
                if members is None or len(members) == 0:
                    try:
                        cmds.lockNode(set, lock=False)
                        cmds.delete(set)
                        self.__onChangePrint("Remove empty objectSet '%s'" % set)
                    except RuntimeError as err:
                        self.__onChangePrint("Failed to remove empty objectSet '%s' (%s)" % (set, str(err)))
                else:
                    hasSubParts = False
                    for member in members:
                        if "[" in member:
                            hasSubParts = True
                            break
                    if hasSubParts:
                        cmds.delete(set)
                        self.__onChangePrint("Remove objectSet '%s' containing only mesh parts. Only full objects are allowed in sets!" % set)

    def __resetGrid(self, *args):
        cmds.grid(toggle=True)
        cmds.grid(reset=True)
        cmds.grid(spacing=10, divisions=10, size=10)

    def __updateHandleDisplay(self, *args):
        objects = cmds.ls(transforms=True, long=False)
        for object in objects:
            showHandle = None

            if "aiMarker" in object and "aiMarkers" != object.split("|")[-1]:
                showHandle = True

            if "workArea" in object and "workAreas" != object.split("|")[-1]:
                showHandle = True

            if "dropArea" in object and "dropAreas" != object.split("|")[-1]:
                showHandle = True

            if object == "attacherJoint":
                showHandle = True

            if object == "topReferenceNode":
                showHandle = True

            if "_ignore" in object:
                showHandle = False

            if showHandle is True:
                cmds.setAttr(object + ".displayHandle", True)
                cmds.setAttr(object + ".displayLocalAxis", True)
            elif showHandle is False:
                cmds.setAttr(object + ".displayHandle", False)
                cmds.setAttr(object + ".displayLocalAxis", False)

    def _attributeExists(self, node, attribute):
        node = str(node)
        attribute = str(attribute)

        if (attribute and node):
            if not cmds.objExists(node):
                return False
            if attribute in cmds.listAttr(node, shortNames=True):
                return True
            if attribute in cmds.listAttr(node):
                return True

        return False

    def _getAttributeValue(self, node, attribute, default):
        fullname = node + '.' + attribute
        if self._attributeExists(node, attribute):
            return cmds.getAttr(fullname)
        return default

    def _removeAttributeString(self, node, attribute):
        fullname = node + '.' + attribute
        if self._attributeExists(node, attribute):
            cmds.deleteAttr(fullname)
            return True
        return False

    def _getFileInCurrentProject(self, projectDirectory, filename):
        ''' returns the given file path is the file exists in current project directory (works only if starting with '/bin/data/') '''

        if "/bin/data" in filename:
            if "//" not in filename:
                # check if the file is loaded from a different 'project'
                if projectDirectory not in filename:
                    pos = filename.find("bin/data")
                    localFilename = filename[pos:]

                    projectFilePath = projectDirectory + "/" + localFilename
                    # if it is available in the current project we use this
                    if os.path.exists(projectFilePath):
                        return projectFilePath

        return filename


    def createCustomUI(self, parentFrame):
        uvItems = cmds.formLayout('uvItems', parent=parentFrame)
        textUVSet = cmds.textField(self.cleanupUVsTextField, parent=uvItems, height=30, editable=True)
        textUVClean = cmds.button(parent=uvItems, label='Cleanup UVs', height=30, command=self.cleanupUVs, annotation='Merge given UV-Set to default "map1" UV-Set')

        cmds.formLayout(uvItems, edit=True, attachPosition=((textUVSet, 'left', 0, 0), (textUVSet, 'right', 5, 50),
                                                            (textUVClean, 'left', 0, 50), (textUVClean, 'right', 0, 100)))

    def cleanupUVs(self, *args):
        nodes = cmds.ls(sl=True, o=True, long=True)
        uvMap = cmds.textField(self.cleanupUVsTextField, q=True, text=True)

        if uvMap != '':
            if nodes is not None:
                for node in nodes:
                    cmds.select(node)
                    nodeName = cmds.listRelatives(node)[0]
                    cmds.polyUVSet(node + '|' + nodeName, currentUVSet=True, uvSet=uvMap)
                    cmds.polyCopyUV(node, uvSetNameInput='', uvSetName='map1', ch=False)
                    cmds.select(node)
                    cmds.polyUVSet(node + '|' + nodeName, currentUVSet=True, uvSet=uvMap)
                    cmds.polyUVSet(delete=True)


def getI3DExporterPlugin():
    return CleanupTools()

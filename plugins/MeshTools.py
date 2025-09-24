#
# Mesh Tools Plugin for Maya I3D Exporter
# Basic tools for mesh operations (DetachFaces, SetMirrorAxis, AlignZAxis, AlignNegativeZAxis, Remove Namespace, ZAxisToManipulator, curveInfo, decal offset check)
#
# @created 15/04/2019
# Code imported from I3DExporter.py
#
# Copyright (c) 2008-2015 GIANTS Software GmbH, Confidential, All Rights Reserved.
# Copyright (c) 2003-2015 Christian Ammann and Stefan Geiger, Confidential, All Rights Reserved.
#

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import I3DExporter
import I3DUtils
import math
from functools import partial

if 'I3DExporterMeshToolWorldRotation' not in globals():
    I3DExporterMeshToolWorldRotation = [0, 0, 0]


class MeshTools:
    def __init__(self):
        self.name = "Mesh-Tools"
        self.page = "Tools"
        self.prio = 3

        self.shelfCommand = "import I3DUtils; import MeshTools; I3DUtils.reloadModule(MeshTools); plugin = MeshTools.MeshTools(); plugin.%s(); del plugin;"

        self.detachFacesInfo = {"name": "Detach Faces",
                                "category": self.name,
                                "annotation": "Detached the selected faces from the mesh",
                                "button_function": self.executeDetachFaces,
                                "shelf_label": "DetFcs",
                                "shelf_command": self.shelfCommand % "executeDetachFaces"}

        self.saveMergeInfo = {"name": "Combine Meshes",
                              "category": self.name,
                              "annotation": "Combines all selected meshes together to the first selected mesh, which keeps it's attributes. (works for skinned meshes as well)",
                              "button_function": self.saveMerge,
                              "shelf_label": "Merge",
                              "shelf_command": self.shelfCommand % "saveMerge"}

        self.setMirrorAxisInfo = {"name": "SetMirrorAxis",
                                  "category": self.name,
                                  "annotation": "Sets axis of mirror",
                                  "button_function": self.executeSetMirrorAxis,
                                  "shelf_label": "StMirrAxs",
                                  "shelf_command": self.shelfCommand % "executeSetMirrorAxis"}

        self.alignZAxisInfo = {"name": "AlignZAxis",
                               "category": self.name,
                               "annotation": "Aligns the z-axis of the node against the selected second node",
                               "button_function": self.executeAlignZAxis,
                               "shelf_label": "AlgnZAxs",
                               "shelf_command": self.shelfCommand % "executeAlignZAxis"}

        self.alignNegativeZAxisInfo = {"name": "AlignNegativeZAxis",
                                       "category": self.name,
                                       "annotation": "Aligns the negative z-axis of the node against the selected second node",
                                       "button_function": self.executeAlignNegativeZAxis,
                                       "shelf_label": "AlgnNZAxs",
                                       "shelf_command": self.shelfCommand % "executeAlignNegativeZAxis"}

        self.removeNamespaceInfo = {"name": "Remove Namespace",
                                    "category": self.name,
                                    "annotation": "Removes obsolte namespaces",
                                    "button_function": self.executeRemoveNamspace,
                                    "shelf_label": "RmNasp",
                                    "shelf_command": self.shelfCommand % "executeRemoveNamspace"}

        self.zAxisToManipulatorInfo = {"name": "ZAxisToManipulator",
                                       "category": self.name,
                                       "annotation": "Aligns the z-axis of the node against the selected manipulator",
                                       "button_function": self.executeZAxisToManipulator,
                                       "shelf_label": "ZAxToMani",
                                       "shelf_command": self.shelfCommand % "executeZAxisToManipulator"}

        self.curveInfo = {"name": "Get Curve Length",
                          "category": self.name,
                          "annotation": "Get the length of the selected curve in meters",
                          "button_function": self.executeCurveInfo,
                          "shelf_label": "CurvInf",
                          "shelf_command": self.shelfCommand % "executeCurveInfo"}

        self.decalOffsetCheckinfo = {"name": "Decal Offset Check",
                                     "category": self.name,
                                     "annotation": "Checks all decals in the scene for their correct offset to the faces below. (Runs on all decals with 'decal' or 'alpha' in the name or in the selected mesh.)",
                                     "button_function": self.decalOffsetCheck,
                                     "shelf_label": "DeOffCheck",
                                     "shelf_command": self.shelfCommand % "decalOffsetCheck"}

    def getToolsButtons(self):
        return [self.detachFacesInfo, self.saveMergeInfo,
                self.setMirrorAxisInfo, self.alignZAxisInfo,
                self.alignNegativeZAxisInfo, self.removeNamespaceInfo,
                self.zAxisToManipulatorInfo, self.curveInfo,
                self.decalOffsetCheckinfo]

    def getShelfScripts(self):
        return [self.detachFacesInfo, self.saveMergeInfo,
                self.setMirrorAxisInfo, self.alignZAxisInfo,
                self.alignNegativeZAxisInfo, self.removeNamespaceInfo,
                self.zAxisToManipulatorInfo, self.curveInfo,
                self.decalOffsetCheckinfo]

    def executeCurveInfo(self, *args):
        m_list = OpenMaya.MSelectionList()     # create selectionList
        OpenMaya.MGlobal.getActiveSelectionList(m_list)
        m_listIt = OpenMaya.MItSelectionList(m_list)
        while not m_listIt.isDone():
            m_path = OpenMaya.MDagPath()   # will hold a path to the selected object
            m_component = OpenMaya.MObject()    # will hold a list of selected components
            m_listIt.getDagPath(m_path, m_component)
            if (m_path.hasFn(OpenMaya.MFn.kNurbsCurve)):
                m_fnNurbs = OpenMaya.MFnNurbsCurve(m_path)
                OpenMaya.MGlobal.displayInfo("{} {:.2f} meters".format(m_path.fullPathName(), 0.01*m_fnNurbs.length()))
            m_listIt.next()

    def __unlockNode(self, node):
        cmds.setAttr(node + ".translateX", lock=0)
        cmds.setAttr(node + ".translateY", lock=0)
        cmds.setAttr(node + ".translateZ", lock=0)
        cmds.setAttr(node + ".rotateX", lock=0)
        cmds.setAttr(node + ".rotateY", lock=0)
        cmds.setAttr(node + ".rotateZ", lock=0)
        cmds.setAttr(node + ".scaleX", lock=0)
        cmds.setAttr(node + ".scaleY", lock=0)
        cmds.setAttr(node + ".scaleZ", lock=0)

    def __getSkinClusterByObject(self, object):
        skinClusters = cmds.ls(type="skinCluster")
        if skinClusters is not None:
            for skinCluster in skinClusters:
                geometry = cmds.skinCluster(skinCluster, query=True, geometry=True)
                objects = cmds.listRelatives(geometry, parent=True, fullPath=False)
                if objects is not None:
                    if objects[0] == object:
                        return skinCluster

    def executeDetachFaces(self, *args):
        selectedFaces = cmds.filterExpand(ex=1, sm=34)
        facesByObject = {}

        if selectedFaces is None:
            I3DUtils.showWarning('You need to select at least one face first!')
            return

        for face in selectedFaces:
            objectName = face.split('.')[0]
            if objectName not in facesByObject:
                facesByObject[objectName] = [face]
            else:
                facesByObject[objectName].append(face)

        newObjects = []

        for objectName, faceArray in facesByObject.items():
            origObjShape = cmds.listRelatives(faceArray, p=True, pa=True)
            origObj = cmds.listRelatives(origObjShape, p=True, pa=True)

            nameSplitSkip = []
            faceNum = []
            newFaceSel = []

            if faceArray is None:
                I3DUtils.showWarning('You need to select at least one face first!')
                return

            # get selected face numbers into faceNum
            for step in range(0, len(faceArray)):
                temp = faceArray[step].split('.')
                nameSplitSkip.append(temp[0])
                nameSplitSkip.append(temp[1])

            skip2 = 1
            for step2 in range(0, int(len(nameSplitSkip)/2)):
                faceNum.append(nameSplitSkip[skip2])
                skip2 = skip2 + 2

            # duplicate original object
            newObj = cmds.duplicate(origObj[0], un=False, rc=True)
            cmds.delete(newObj[0], ch=True)

            # copy the same skinning on the duplicated object
            skinCluster = self.__getSkinClusterByObject(origObj[0])
            if skinCluster is not None:
                joints = cmds.skinCluster(skinCluster, query=True, inf=True)
                skinClusterTarget = cmds.skinCluster(joints, newObj[0])
                if skinClusterTarget is not None:
                    cmds.copySkinWeights(ss=skinCluster, ds=skinClusterTarget[0], influenceAssociation="name", noMirror=True)

            # remove xml identifier from duplicated object
            if "i3D_xmlIdentifier" in cmds.listAttr(newObj[0], shortNames=True):
                cmds.deleteAttr(newObj[0] + ".i3D_xmlIdentifier")

            # remove merge group root since the source is root already
            if "i3D_mergeGroupRoot" in cmds.listAttr(newObj[0], shortNames=True):
                cmds.setAttr(newObj[0] + ".i3D_mergeGroupRoot", False)

            newAllFaces = cmds.ls(newObj[0] + '.f[*]')

            # make new array for face selection on newObj
            for step3 in range(0, len(faceNum)):
                newFaceSel.append(newObj[0] + '.' + faceNum[step3])

            # delete original face selection
            cmds.delete(faceArray)

            # delete inverse face selection on duplicate
            cmds.select(newAllFaces, r=True)
            cmds.select(newFaceSel, d=True)
            cmds.delete()

            # clear history of skinned meshes after the face removal
            cmds.bakePartialHistory(origObj[0], prePostDeformers=True)
            cmds.bakePartialHistory(newObj[0], prePostDeformers=True)

            newObjects.append(newObj[0])

            children = cmds.listRelatives(newObj[0], c=True, f=True, type='transform')
            if children is not None:
                for child in children:
                    cmds.delete(child)

        # center and freeze pivots afterwards when all sub objects has been removed
        # skinned meshes are excluded from pivot changes
        for newObject in newObjects:
            skinCluster = self.__getSkinClusterByObject(newObject)
            if skinCluster is None:
                cmds.xform(newObject, centerPivots=True)
                I3DUtils.doFreezeToPivot(newObject)

        cmds.select(newObjects, r=True)

    def _getObjectNameFromDAG(self, dag):
        dags = dag.split("|")
        return dags[len(dags) - 1]

    def _getAllI3DAttributes(self, node):
        attributes = {}

        for k, v in I3DExporter.SETTINGS_ATTRIBUTES.items():
            if "type" in v:
                if v['type'] == I3DExporter.TYPE_BOOL:
                    attributes[k] = I3DExporter.I3DGetAttributeValue(node, k, v['defaultValue'])
                elif v['type'] == I3DExporter.TYPE_INT:
                    attributes[k] = I3DExporter.I3DGetAttributeValue(node, k, v['defaultValue'])
                elif v['type'] == I3DExporter.TYPE_FLOAT:
                    attributes[k] = I3DExporter.I3DGetAttributeValue(node, k, v['defaultValue'])
                elif v['type'] == I3DExporter.TYPE_STRING or v['type'] == I3DExporter.TYPE_HEX:
                    attributes[k] = I3DExporter.I3DGetAttributeValue(node, k, v['defaultValue'])
                elif v['type'] == I3DExporter.TYPE_ENUM:
                    attributes[k] = I3DExporter.I3DGetAttributeValue(node, k, v['defaultValue'])

        return attributes

    def _setAllI3DAttributes(self, node, attributes):
        for k, v in I3DExporter.SETTINGS_ATTRIBUTES.items():
            if k in attributes and "type" in v:
                value = attributes[k]

                if v['type'] == I3DExporter.TYPE_BOOL:
                    I3DExporter.I3DSaveAttributeBool(node, k, value)
                elif v['type'] == I3DExporter.TYPE_INT:
                    I3DExporter.I3DSaveAttributeInt(node, k, value)
                elif v['type'] == I3DExporter.TYPE_FLOAT:
                    I3DExporter.I3DSaveAttributeFloat(node, k, value)
                elif v['type'] == I3DExporter.TYPE_STRING or v['type'] == I3DExporter.TYPE_HEX:
                    I3DExporter.I3DSaveAttributeString(node, k, value)
                elif v['type'] == I3DExporter.TYPE_ENUM:
                    I3DExporter.I3DSaveAttributeEnum(node, k, value, v['options'])

    def _removeDuplicatesFromList(self, oldList):
        newList = []
        for entry in oldList:
            if entry not in newList:
                newList.append(entry)
        return newList

    def _getObjectMaterials(self, object):
        shapes = cmds.listRelatives(object, s=True, f=True)
        if shapes is not None:
            shadingEngines = cmds.listConnections(shapes[0], type='shadingEngine')
            if shadingEngines is not None:
                materials = cmds.ls(cmds.listConnections(shadingEngines), mat=True)
                return self._removeDuplicatesFromList(materials)
        return []

    def _getChildIndex(self, objectName):
        parentObject = cmds.listRelatives(objectName, p=True, f=True)
        childObjects = None
        if parentObject is not None:
            childObjects = cmds.listRelatives(parentObject, c=True, f=True)
        else:
            childObjects = cmds.ls(assemblies=True, long=True)

        if childObjects is not None:
            # get index of old object
            maxIndex = len(childObjects)
            for i in range(0, len(childObjects)):
                name = childObjects[i]

                # if given objectName if not a DAG path we convert the 'name' from DAG to objectName
                if not objectName.startswith("|"):
                    name = self._getObjectNameFromDAG(name)

                if name == objectName:
                    return i, maxIndex

        return 0, 0

    def _createParentOfObject(self, object, tail):
        # get object name
        objectName = self._getObjectNameFromDAG(object)

        # create new transform as child of old object
        newObject = cmds.group(p=object, em=True, name=objectName + tail)

        # get parent
        parentObject = cmds.listRelatives(object, p=True, f=True)

        if parentObject is not None:
            # get index of old object
            index, maxIndex = self._getChildIndex(object)

            # put the new tranform on the same level
            cmds.parent(newObject, parentObject)

            # move it to the same position
            cmds.reorder(newObject, r=index - maxIndex)
        else:
            cmds.parent(newObject, world=True)

        # parent the old object under the new object
        cmds.parent(object, newObject)

        newChilds = cmds.listRelatives(newObject, c=True, f=True)

        return newObject, newChilds[0]

    def saveMerge(self, *args):
        # check if all selected objects have the same material
        sameMaterial = True
        objects = cmds.ls(sl=True, o=True, long=True)
        if len(objects) > 1:
            for j in range(1, len(objects)):
                mergable, mismatchData = I3DUtils.getAreObjectsMergeable(objects[0], objects[j])
                if not mergable:
                    warning = I3DUtils.getWarningFromMismatchData(mismatchData)
                    cmds.warning("Selected objects cannot be merged. (%s)" % (warning))
                    sameMaterial = False

        if sameMaterial:
            objects = cmds.ls(sl=True, o=True, long=True)
            if len(objects) > 1:
                rootObjectName = self._getObjectNameFromDAG(objects[0])
                attributes = self._getAllI3DAttributes(objects[0])
                xmlIdentifier = I3DExporter.I3DGetAttributeValue(objects[0], 'i3D_xmlIdentifier', '')
                castsShadows = None
                if cmds.objExists(objects[0] + ".castsShadows"):
                    castsShadows = cmds.getAttr(objects[0] + '.castsShadows')

                # check if a object to merge is the parent of the root node, if yes we cancel to operation
                parentObjects = cmds.listRelatives(objects[0], p=True, f=True)
                if parentObjects is not None:
                    for object in objects:
                        if object == parentObjects[0]:
                            cmds.warning("Try to merge the parent of object %s with one of its children as root! Please first select the parent and then select the child!" % object)
                            return

                # make sure all selected objects use the same names for there uv set, otherwise the material assignment will break after merging
                baseUVSets = cmds.polyUVSet(objects[0], q=True, auv=True)
                if baseUVSets is not None:
                    for i in range(0, len(objects)):
                        if i > 0:
                            uvSets = cmds.polyUVSet(objects[i], q=True, auv=True)
                            if uvSets is not None:
                                for j in range(0, min(len(uvSets), len(baseUVSets))):
                                    if uvSets[j] != baseUVSets[j]:
                                        shape = cmds.listRelatives(objects[i], f=True)[0]
                                        cmds.polyUVSet(shape, rename=True, uvSet=uvSets[j], newUVSet=baseUVSets[j])

                                        print("Renamed UVSet of object %s (%s to %s)" % (shape, uvSets[j], baseUVSets[j]))

                # create temp container transform and move all objects beside the root inside of it
                tempContainer = cmds.group(em=True, name="tempContainer")
                for i in range(0, len(objects)):
                    if i > 0:
                        # check if object still exists, if not it was a child of another object to merge and it is already inside of the container
                        if cmds.objExists(objects[i]):
                            cmds.parent(objects[i], tempContainer)

                # create a transformgroup at the posistion of the root node
                tempObject, root = self._createParentOfObject(objects[0], "Temp")

                # move all childs of the root node to the temporary tranform
                childObjects = cmds.listRelatives(root, c=True, f=True, type="transform")
                if childObjects is not None and len(childObjects) > 0:
                    for child in childObjects:
                        cmds.parent(child, tempObject)

                # move the root to the container
                cmds.parent(root, tempContainer)

                # merge all objects
                mergeObjects = cmds.listRelatives(tempContainer, c=True, f=True, type="transform")

                result = None
                if I3DUtils.hasSkinning(mergeObjects[0]):
                    result = cmds.polyUniteSkinned(mergeObjects)[0]
                    cmds.bakePartialHistory(result, prePostDeformers=True)
                else:
                    result = cmds.polyUnite(mergeObjects)[0]
                    cmds.delete(result, ch=True)

                if cmds.objExists(tempContainer):
                    cmds.delete(tempContainer)

                # set pivot of the merged object
                worldPivots = cmds.xform(tempObject, q=True, ws=True, scalePivot=True)
                cmds.xform(result, ws=True, preserve=True, pivots=worldPivots)

                # parent root under temp object and freeze pivot if not skinned
                result = cmds.parent(result, tempObject)[0]

                skinCluster = self.__getSkinClusterByObject(result)
                if skinCluster is None:
                    cmds.makeIdentity(result, apply=True, r=True, n=False)

                    # freeze translation
                    I3DUtils.doFreezeToPivot(result)

                # move the root to the same postion as the temp object
                # if we don't have a parent we leave the result on the root level
                parentObject = cmds.listRelatives(tempObject, p=True, f=True)
                if parentObject is not None:
                    index, maxIndex = self._getChildIndex(tempObject)

                    cmds.parent(result, parentObject)
                    cmds.reorder(result, r=index - maxIndex)
                else:
                    cmds.parent(result, world=True)

                # move the childs of the temp object to the root
                childObjects = cmds.listRelatives(tempObject, c=True, f=True, type="transform")
                if childObjects is not None and len(childObjects) > 0:
                    for child in childObjects:
                        cmds.parent(child, result)

                # delete temp object and container
                cmds.delete(tempObject)

                # set I3D attributes as on the source object
                self._setAllI3DAttributes(result, attributes)
                I3DExporter.I3DUpdateLayers(result)
                I3DExporter.I3DSaveAttributeString(result, 'i3D_xmlIdentifier', xmlIdentifier)

                if castsShadows is not None:
                    if cmds.objExists(result + ".castsShadows"):
                        cmds.setAttr(result + ".castsShadows", castsShadows)

                # rename container to old object name and select it
                cmds.select(cmds.rename(result, rootObjectName))
            else:
                cmds.warning("Please select at least 2 objects!")

    def executeSetMirrorAxis(self, *args):
        nodes = cmds.ls(selection=True, long=True, tr=True)

        for node in nodes:
            I3DUtils.doFreezeToPivot(node)

        if len(nodes) != 3:
            I3DUtils.showWarning('You need to select 3 nodes (camera, mirror, target) !')
            return

        camera = nodes[0]
        mirror = nodes[1]
        target = nodes[2]

        mirrorParent = I3DUtils.getParent(mirror)
        mirrorIndex = I3DUtils.getCurrentNodeIndex(mirror)

        mirrorAxisTarget = cmds.group(em=True, w=True)
        targetMirror = cmds.group(em=True, w=True)

        cameraPos = cmds.xform(camera, q=True, ws=True, t=True)
        mirrorPos = cmds.xform(mirror, q=True, ws=True, t=True)
        targetPos = cmds.xform(target, q=True, ws=True, t=True)

        v1 = I3DUtils.vectorNorm([mirrorPos[0]-cameraPos[0], mirrorPos[1]-cameraPos[1], mirrorPos[2]-cameraPos[2]])
        v2 = I3DUtils.vectorNorm([mirrorPos[0]-targetPos[0], mirrorPos[1]-targetPos[1], mirrorPos[2]-targetPos[2]])

        v3 = [v1[0]+v2[0], v1[1]+v2[1], v1[2]+v2[2]]

        cmds.move(mirrorPos[0], mirrorPos[1], mirrorPos[2], targetMirror, absolute=True, worldSpace=True)
        cmds.move(mirrorPos[0] - v3[0], mirrorPos[1] - v3[1], mirrorPos[2] - v3[2], mirrorAxisTarget, absolute=True, worldSpace=True)

        cmds.select(mirrorAxisTarget, targetMirror)
        constrain = cmds.aimConstraint(offset=[0, 0, 0], weight=1, aimVector=[0, 1, 0], upVector=[0, 0, 1], worldUpType='vector', worldUpVector=[0, 1, 0])

        mirror = cmds.parent(mirror, targetMirror)[0]

        cmds.makeIdentity(mirror, apply=True, t=False, r=True, s=False, n=False)

        if mirrorParent is not None:
            mirror = cmds.parent(mirror, mirrorParent)[0]
        else:
            mirror = cmds.parent(mirror, w=True)[0]

        newMirrorIndex = I3DUtils.getCurrentNodeIndex(mirror)

        cmds.reorder(mirror, relative=(mirrorIndex-newMirrorIndex))
        I3DUtils.doFreezeToPivot(mirror)

        cmds.delete(constrain)
        cmds.delete(targetMirror)
        cmds.delete(mirrorAxisTarget)

    def executeAlignZAxis(self, *args):
        I3DUtils.freezeToPivot(None)

        nodes = cmds.ls(sl=True, o=True)
        if len(nodes) != 2:
            I3DUtils.showWarning('You need to select a mesh and a target point!')
            return

        self.alignZAxisToTargetPoint(nodes[0], nodes[1], 1)

    def executeAlignNegativeZAxis(self, *args):
        I3DUtils.freezeToPivot(None)

        nodes = cmds.ls(sl=True, o=True)
        if len(nodes) != 2:
            I3DUtils.showWarning('You need to select a mesh and a target point!')
            return

        self.alignZAxisToTargetPoint(nodes[0], nodes[1], -1)

    def executeRemoveNamspace(self, *args):
        if len(args) == 1:
            nodes = cmds.ls(sl=True, o=True, long=True)
        else:
            nodes = args[1]

        if nodes is not None:
            for node in nodes:
                children = cmds.listRelatives(node, c=True, pa=True, type='transform')
                if children is not None:
                    self.executeRemoveNamspace(False, children)

                selectedNode = cmds.ls(node)
                name = selectedNode[0]
                pos = name.rfind(':')
                if pos != -1:
                    name = name[(pos+1):]
                    cmds.rename(node, name)

    def executeZAxisToManipulator(self, *args):
        I3DUtils.freezeToPivot(None)

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
            origObjShape = cmds.listRelatives(objs[0], p=True, pa=True)
            origObj = cmds.listRelatives(origObjShape, p=True, pa=True)
            rotationNode = origObj[0]

            cmds.setToolTo('moveSuperContext')
            result = cmds.manipMoveContext('Move', q=True, p=True)
            targetPosition = I3DUtils.linearInternalToUIVector(result)
            targetPoint = cmds.group(em=True, w=True)
            cmds.move(targetPosition[0], targetPosition[1], targetPosition[2], targetPoint, a=True, ws=True, moveXYZ=True)

            self.alignZAxisToTargetPoint(rotationNode, targetPoint, 1)

            cmds.delete(targetPoint)

    def alignZAxisToTargetPoint(self, rotationNode, targetPoint, direction):
        global I3DExporterMeshToolWorldRotation
        targetPosition = I3DUtils.linearUIToInternalVector(cmds.xform(targetPoint, q=True, t=True, ws=True))

        node = cmds.group(em=True, w=True)
        position = cmds.xform(rotationNode, q=True, t=True, ws=True)
        cmds.move(position[0], position[1], position[2], node, a=True, ws=True, moveXYZ=True)
        cmds.xform(node, ro=I3DExporterMeshToolWorldRotation)
        nodeMatrix = cmds.xform(node, q=True, m=True)
        invNodeMatrix = I3DUtils.invertTransformationMatrix(nodeMatrix)

        localTargetPosition = I3DUtils.transformPoint(targetPosition, invNodeMatrix)
        localTargetPosition[1] = 0

        zAxis = [0, 0, 1]
        if direction == -1:
            zAxis = [0, 0, -1]

        localTargetPositionLength = I3DUtils.vectorLength(localTargetPosition)

        if localTargetPositionLength > 0:
            yAngle = math.acos(I3DUtils.vectorDot(localTargetPosition, zAxis) / localTargetPositionLength)
            yAngle = I3DUtils.angleInternalToUI(yAngle)
            diffCrossZ = I3DUtils.vectorCross(localTargetPosition, zAxis)
            if diffCrossZ[1] > 0:
                yAngle = -yAngle
            cmds.rotate(0, yAngle, 0, node, r=True, os=True)

        nodeMatrix = cmds.xform(node, q=True, m=True)
        invNodeMatrix = I3DUtils.invertTransformationMatrix(nodeMatrix)

        localTargetPosition = I3DUtils.transformPoint(targetPosition, invNodeMatrix)
        localTargetPosition[0]
        localTargetPositionLength = I3DUtils.vectorLength(localTargetPosition)
        if localTargetPositionLength > 0:
            xAngle = math.acos(I3DUtils.vectorDot(localTargetPosition, zAxis) / localTargetPositionLength)
            xAngle = I3DUtils.angleInternalToUI(xAngle)
            diffCrossZ = I3DUtils.vectorCross(localTargetPosition, zAxis)
            if diffCrossZ[0] > 0:
                xAngle = -xAngle
            cmds.rotate(xAngle, 0, 0, node, r=True, os=True)

        currentParents = cmds.listRelatives(rotationNode, p=True, pa=True)
        currentParent = None
        nodeOrder = 0

        if currentParents is not None:
            currentParent = currentParents[0]
            currentParentChildren = cmds.listRelatives(currentParent, c=True, pa=True)
            if currentParentChildren is not None:
                for child in currentParentChildren:
                    if child == rotationNode:
                        break
                    nodeOrder = nodeOrder + 1

        newNames = cmds.parent(rotationNode, node)
        newName = newNames[0]
        cmds.makeIdentity(newName, apply=True, t=False, r=True, s=False, n=False)

        if currentParent is not None:
            names = cmds.parent(newName, currentParent)
            name = names[0]

            currentParentChildren = cmds.listRelatives(currentParent, c=True, pa=True)
            newNodeOrder = 0

            for child in currentParentChildren:
                if child == name:
                    break
                newNodeOrder = newNodeOrder + 1

            if newNodeOrder != nodeOrder:
                cmds.reorder(name, relative=(nodeOrder-newNodeOrder))
        else:
            cmds.parent(newName, w=True)

        cmds.delete(node)

    def setWorldRotationToFaceNormal(self):
        nodes = cmds.ls(selection=True, long=True)
        if nodes is not None and len(nodes) == 1:
            object = nodes[0].split(".")[0]
            if cmds.nodeType(object) == "mesh":
                object = cmds.listRelatives(object, p=True, pa=True)

            manipulatorPosition = cmds.manipMoveContext('Move', q=True, p=True)
            normal = cmds.polyInfo(faceNormals=True)[0]
            parts = normal.split(":")[1].split(" ")
            direction = [float(parts[1]), float(parts[2]), float(parts[3])]

            rootObject = cmds.group(em=True, w=True)
            cmds.parent(rootObject, object)
            cmds.xform(rootObject, t=manipulatorPosition, ws=True)

            targetObject = cmds.group(em=True, w=True)
            cmds.parent(targetObject, object)
            cmds.xform(targetObject, t=manipulatorPosition, ws=True)
            cmds.move(direction[0], direction[1], direction[2], targetObject, relative=True, ls=True, moveXYZ=True)

            cmds.select(targetObject, rootObject)
            constrain = cmds.aimConstraint(offset=[0, 0, 0], weight=1, aimVector=[0, 0, 1], upVector=[0, 1, 0], worldUpType='vector', worldUpVector=[0, 1, 0])

            global I3DExporterMeshToolWorldRotation
            I3DExporterMeshToolWorldRotation = cmds.xform(rootObject, ro=True, q=True, ws=True)

            cmds.delete(constrain)
            cmds.delete(rootObject)
            cmds.delete(targetObject)

    def resetWorldRotation(self):
        global I3DExporterMeshToolWorldRotation
        I3DExporterMeshToolWorldRotation = [0, 0, 0]

    def getWorldRotation(self):
        global I3DExporterMeshToolWorldRotation
        return I3DExporterMeshToolWorldRotation

    def decalOffsetCheck(self, *args):
        TARGET_OFFSET = 0.0002

        def showDialog(callback, text, title="Confirm", labels=["Yes", "No"]):
            WINDOW_ID = "MeshToolDialog"

            def __callback(value, *args):
                cmds.deleteUI(WINDOW_ID)
                callback(value)

            def __onClose(*args):
                callback("Close")

            if cmds.window(WINDOW_ID, exists=True):
                cmds.deleteUI(WINDOW_ID)

            UI_WIDTH = 350
            UI_HEIGHT = 80

            if cmds.windowPref(WINDOW_ID, exists=True):
                cmds.windowPref(WINDOW_ID, edit=True, widthHeight=(UI_WIDTH, UI_HEIGHT))

            cmds.window(WINDOW_ID, title=title, widthHeight=(UI_WIDTH, UI_HEIGHT), closeCommand=__onClose)

            baseLayout = cmds.scrollLayout()

            textLayout = cmds.gridLayout(numberOfColumns=1, cellWidthHeight=(346, 40), parent=baseLayout)
            cmds.text(label=text, width=346, align="center", parent=textLayout)

            columnWidth = []
            columnSpacing = []

            spacing = 20
            numLabels = len(labels)
            for i in range(1, numLabels + 1):
                columnWidth.append((i, ((UI_WIDTH - 4) - (spacing * (numLabels + 1))) / numLabels))
                columnSpacing.append((i, spacing))

            controlsGrid = cmds.rowColumnLayout(numberOfColumns=len(labels), columnWidth=columnWidth, columnSpacing=columnSpacing, parent=baseLayout)

            for label in labels:
                cmds.button(label=label, command=partial(__callback, label), parent=controlsGrid)

            cmds.showWindow()

        def raycast(x, y, z, dirX, dirY, dirZ, mesh, length=999):
            item = OpenMaya.MDagPath()
            selection = OpenMaya.MSelectionList()
            selection.add(mesh)
            selection.getDagPath(0, item)

            item.extendToShape()
            mfnMesh = OpenMaya.MFnMesh(item)

            hitPoint = OpenMaya.MFloatPoint()

            hit = mfnMesh.closestIntersection(
                OpenMaya.MFloatPoint(x * 100, y * 100, z * 100),
                OpenMaya.MFloatVector(dirX, dirY, dirZ),
                None, None,
                False,
                OpenMaya.MSpace.kWorld,
                length * 100,
                False,
                mfnMesh.autoUniformGridParams(),
                hitPoint,
                None, None, None, None, None,
                0.0001
            )

            if hit and hitPoint is not None:
                return hitPoint[0] * 0.01, hitPoint[1] * 0.01, hitPoint[2] * 0.01

            return None, None, None

        def vector3Length(x, y, z):
            return math.sqrt(x * x + y * y + z * z)

        def debugNode(name, x, y, z):
            cmds.xform(cmds.group(em=True, name=name), t=[x, y, z])

        def getMeshNormalArray(dagStr):
            selectionList = OpenMaya.MSelectionList()
            selectionList.add(dagStr)
            dagPath = OpenMaya.MDagPath()
            selectionList.getDagPath(0, dagPath)
            fnMesh = OpenMaya.MFnMesh(dagPath)
            array = OpenMaya.MFloatVectorArray()
            fnMesh.getNormals(array, OpenMaya.MSpace.kWorld)

            return array

        def isValidShape(shape):
            if "_ignore" in shape.lower():
                return False
            if "decal" in shape.lower():
                return False
            if "alpha" in shape.lower():
                return False
            if "effect" in shape.lower():
                return False
            if cmds.nodeType(shape) != "mesh":
                return False

            parent = cmds.listRelatives(shape, parent=True, fullPath=True)
            if parent is not None:
                if not cmds.getAttr(parent[0] + ".visibility"):
                    return False

            return cmds.getAttr(shape + ".visibility")

        def raycastVertexToObject(object, vertIndex, normalsArray, targetObject=None):
            position = cmds.pointPosition(object + ".vtx[%d]" % vertIndex, w=True)
            dx, dy, dz = normalsArray[vertIndex].x, normalsArray[vertIndex].y, normalsArray[vertIndex].z
            x, y, z = position[0] + dx * 0.01, position[1] + dy * 0.01, position[2] + dz * 0.01

            if targetObject is None:
                minDistance = 1
                minDistanceObject = None
                for targetObject in cmds.ls(shapes=True, long=True):
                    if isValidShape(targetObject):
                        hitX, hitY, hitZ = raycast(x, y, z, -dx, -dy, -dz, targetObject, length=0.05)
                        if hitX is not None:
                            distance = vector3Length(hitX - x, hitY - y, hitZ - z) - 0.01
                            if distance < minDistance:
                                # debugNode("ray", x, y, z)
                                # debugNode("hit", hitX, hitY, hitZ)

                                minDistance = distance
                                minDistanceObject = targetObject

                if minDistanceObject is not None:
                    return minDistance
            else:
                hitX, hitY, hitZ = raycast(x, y, z, -dx, -dy, -dz, targetObject, length=0.05)
                if hitX is not None:
                    # debugNode("ray", x, y, z)
                    # debugNode("hit", hitX, hitY, hitZ)
                    return vector3Length(hitX - x, hitY - y, hitZ - z) - 0.01

            return None

        def raycastFaceToObject(object, startVert, endVert, normalsArray, targetObject=None):
            x, y, z = 0, 0, 0
            dx, dy, dz = 0, 0, 0
            numVerts = endVert - startVert + 1
            for vertIndex in range(startVert, endVert + 1):
                position = cmds.pointPosition(object + ".vtx[%d]" % vertIndex, w=True)
                x, y, z = x + position[0], y + position[1], z + position[2]
                dx, dy, dz = dx + normalsArray[vertIndex].x, dy + normalsArray[vertIndex].y, dz + normalsArray[vertIndex].z

            x, y, z = x / numVerts, y / numVerts, z / numVerts
            dx, dy, dz = dx / numVerts, dy / numVerts, dz / numVerts
            x, y, z = x + dx * 0.001, y + dy * 0.001, z + dz * 0.001

            for targetObject in cmds.ls(shapes=True, long=True):
                if isValidShape(targetObject):
                    hitX, hitY, hitZ = raycast(x, y, z, -dx, -dy, -dz, targetObject, length=0.05)
                    if hitX is not None:
                        # debugNode("rayc", x, y, z)
                        # debugNode("hitc", hitX, hitY, hitZ)
                        return vector3Length(hitX - x, hitY - y, hitZ - z) - 0.001

        def getFaceVertices(face):
            edges = cmds.polyListComponentConversion(face, ff=True, te=True)
            otherFaces = cmds.polyListComponentConversion(edges, fe=True, tf=True, bo=True)
            if len(otherFaces) == 0:
                vertices = cmds.polyListComponentConversion(edges, toVertex=True)
                if vertices is not None and len(vertices) > 0:
                    vertices = vertices[0].split("[")[-1].split("]")[0].split(":")
                    if len(vertices) == 2:
                        return int(vertices[0]), int(vertices[1])
            return None, None

        def getFaceCenter(face):
            object = face.split(".")[0]

            x, y, z = 0, 0, 0
            dx, dy, dz = 0, 0, 0
            startVert, endVert = getFaceVertices(face)
            if startVert is not None:
                numVerts = endVert - startVert + 1
                if numVerts > 0:
                    normalsArray = getMeshNormalArray(object)

                    for vertIndex in range(startVert, endVert + 1):
                        position = cmds.pointPosition(object + ".vtx[%d]" % vertIndex, w=True)
                        x, y, z = x + position[0], y + position[1], z + position[2]
                        dx, dy, dz = dx + normalsArray[vertIndex].x, dy + normalsArray[vertIndex].y, dz + normalsArray[vertIndex].z

                    return x / numVerts, y / numVerts, z / numVerts, dx / numVerts, dy / numVerts, dz / numVerts

        def adjustFace(face, distance):
            object = face.split(".")[0]

            startVert, endVert = getFaceVertices(face)
            if startVert is not None:
                numVerts = endVert - startVert + 1
                if numVerts > 0:
                    dx, dy, dz = 0, 0, 0
                    normalsArray = getMeshNormalArray(object)
                    for vertIndex in range(startVert, endVert + 1):
                        dx, dy, dz = dx + normalsArray[vertIndex].x, dy + normalsArray[vertIndex].y, dz + normalsArray[vertIndex].z

                    dx, dy, dz = dx / numVerts, dy / numVerts, dz / numVerts

                    for vertIndex in range(startVert, endVert + 1):
                        vtx = object + ".vtx[%d]" % vertIndex
                        position = cmds.pointPosition(vtx, w=True)
                        x, y, z = position[0] + dx * distance, position[1] + dy * distance, position[2] + dz * distance

                        cmds.xform(vtx, translation=(x, y, z), worldSpace=True)

        def checkFace(face):
            startVert, endVert = getFaceVertices(face)
            if startVert is not None:
                object = face.split(".")[0]
                normalsArray = getMeshNormalArray(object)

                minDistance, numHits = 0.1, 0
                for vertIndex in range(startVert, endVert + 1):
                    distance = raycastVertexToObject(object, vertIndex, normalsArray)
                    if distance is not None:
                        minDistance = min(distance, minDistance)
                        numHits += 1

                cDistance = raycastFaceToObject(object, startVert, endVert, normalsArray)
                if cDistance is not None:
                    minDistance = min(cDistance, minDistance)
                    numHits += 1

                if numHits > 0:
                    return minDistance

        def checkShape(shape, foundIssues):
            faces = cmds.ls(shape + ".f[*]", flatten=True)
            for face in faces:
                cmds.progressWindow(window, edit=True, progress=cmds.progressWindow(window, query=True, progress=True) + 1, status=shape[-35:])
                if cmds.progressWindow(query=True, isCancelled=True):
                    return False

                distance = checkFace(face)
                if distance is not None:
                    doShow, color = False, [0, 1, 0]

                    # stuck in the mesh
                    if distance < 0:
                        doShow, color = True, [1, 0, 0]

                    # too far off
                    if distance > 0.005 and distance < 0.01:
                        doShow, color = True, [0, 1, 1]

                    # too close
                    if distance < TARGET_OFFSET - 0.00001 and distance > 0:
                        alpha = distance / TARGET_OFFSET * 0.75 + 0.25
                        doShow, color = True, [1 - alpha, alpha, 0]

                    if doShow:
                        tx = "%.5f" % (distance)
                        x, y, z, dx, dy, dz = getFaceCenter(face)
                        anno = cmds.annotate(shape, tx=tx, p=(x, y, z))
                        cmds.color(anno, rgbColor=color)
                        cmds.refresh()

                        foundIssues.append({"face": face, "position": (x, y, z), "normal": (dx, dy, dz), "distance": distance})

            return True

        cmds.progressWindow(endProgress=True)

        foundIssues = []

        selectedObject = cmds.ls(sl=True, long=True)
        if selectedObject is not None and len(selectedObject) > 0:
            shapes = cmds.listRelatives(selectedObject, shapes=True, fullPath=True)
            if shapes is not None:
                numFaces = len(cmds.ls(shapes[0] + ".f[*]", flatten=True))
                window = cmds.progressWindow(title="Decal Offset", progress=0, maxValue=numFaces, status="", isInterruptable=True)

                checkShape(shapes[0], foundIssues)

                cmds.progressWindow(endProgress=True)
        else:
            numSteps = 0
            shapes = cmds.ls(shapes=True, long=True)
            validShapes = []
            for shape in shapes:
                if "_ignore" not in shape.lower() and ("decal" in shape.lower() or "alpha" in shape.lower()):
                    validShapes.append(shape)
                    numSteps += len(cmds.ls(shape + ".f[*]", flatten=True))

            if numSteps == 0:
                cmds.warning("No decals found!")
                return

            window = cmds.progressWindow(title="Decal Offset", progress=0, maxValue=numSteps, status="", isInterruptable=True)

            for i in range(0, len(validShapes)):
                if not checkShape(validShapes[i], foundIssues):
                    break

            cmds.progressWindow(endProgress=True)

        def checkNextIssue(_foundIssues, _issueIndex):
            if _issueIndex >= len(_foundIssues):
                return

            issue = _foundIssues[_issueIndex]
            title = "Decal Offset Check (%d/%d)" % (_issueIndex + 1, len(_foundIssues))

            face = issue["face"]
            x, y, z = issue["position"][0], issue["position"][1], issue["position"][2]
            dx, dy, dz = issue["normal"][0], issue["normal"][1], issue["normal"][2]

            cmds.select(face)
            cmds.viewPlace(eyePoint=(x + dx + 0.5, y + dy + 0.5, z + dz))
            cmds.viewPlace(lookAt=(x, y, z))
            cmds.viewPlace(eyePoint=(x + dx * 0.15, y + dy * 0.3 + 0.1, z + dz * 0.15), animate=True)

            def onConfirm(value):
                if value == "Yes":
                    adjustmentDistance = TARGET_OFFSET - issue["distance"]
                    adjustFace(face, adjustmentDistance)
                    cmds.select(face)

                    def onConfirmAdjustment(_value):
                        if _value == "Confirm":
                            checkNextIssue(_foundIssues, _issueIndex + 1)
                        elif _value == "Undo":
                            adjustFace(face, -adjustmentDistance)
                            cmds.select(face)

                            def onNextDecal(__value):
                                if __value == "Next Decal":
                                    checkNextIssue(_foundIssues, _issueIndex + 1)

                            showDialog(onNextDecal, "Next Decal", title=title, labels=["Next Decal", "Cancel"])

                    showDialog(onConfirmAdjustment, "Decal adjust properly?", title=title, labels=["Confirm", "Undo"])

                elif value == "No":
                    checkNextIssue(_foundIssues, _issueIndex + 1)

            showDialog(onConfirm, "Do you want to adjust this decal?", title=title, labels=["Yes", "No"])

        checkNextIssue(foundIssues, 0)


def getI3DExporterPlugin():
    return MeshTools()

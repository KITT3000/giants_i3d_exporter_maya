#
# Skeletons Plugin for Maya I3D Exporter
# Offers skeletons for various vehicles
#
# @created 18/04/2019
# Code imported from I3DExporter.py
#
# Copyright (c) 2008-2015 GIANTS Software GmbH, Confidential, All Rights Reserved.
# Copyright (c) 2003-2015 Christian Ammann and Stefan Geiger, Confidential, All Rights Reserved.
#

import maya.cmds as cmds
import I3DExporter


class Skeletons:
    def __init__(self):
        self.name = "Skeletons"
        self.page = "Tools"
        self.prio = 6

        self.skeletons = []
        self.skeletons.append({'name': 'Tractor', 'func': self.createBaseVehicle})
        self.skeletons.append({'name': 'Combine', 'func': self.createBaseHarvester})
        self.skeletons.append({'name': 'Tool', 'func': self.createBaseTool})
        self.skeletons.append({'name': 'Attacher Joints', 'func': self.createAttacherJoints})
        self.skeletons.append({'name': 'Player', 'func': self.createPlayer})
        self.skeletons.append({'name': 'Lights', 'func': self.createLights})
        self.skeletons.append({'name': 'Placeable', 'func': self.createPlaceable})
        self.skeletons.append({'name': 'Husbandry', 'func': self.createAnimalHusbandry})
        self.skeletons.append({'name': 'Cameras (Tractor)', 'func': self.createCamerasVehicle})
        self.skeletons.append({'name': 'Cameras (Combine)', 'func': self.createCamerasHarvester})
        self.skeletons.append({'name': 'Traffic Vehicle', 'func': self.createTrafficVehicle})

        self.customUI = {"category": self.name,
                         "customUIFunc": self.createCustomUI}

        self.skeletonsDropDown = "ui_skeletonsDropDown"

    def getToolsButtons(self):
        return []

    def getShelfScripts(self):
        return []

    def getToolsCustomUI(self):
        return [self.customUI]

    def createCustomUI(self, parentFrame):
        skeletonItems = cmds.formLayout('skeletonItems', parent=parentFrame)
        menuSkeleton = cmds.optionMenu(self.skeletonsDropDown, parent=skeletonItems, height=31, annotation='Skeletons')
        for attribute in self.skeletons:
            cmds.menuItem(parent=menuSkeleton, label=attribute['name'])
        buttonCreate = cmds.button(parent=skeletonItems, label='Create', height=30, command=self.createSkeleton, annotation='Create skeleton')
        cmds.formLayout(skeletonItems, edit=True, attachPosition=((menuSkeleton, 'left', 0, 0), (menuSkeleton, 'right', 5, 70),
                                                                  (buttonCreate, 'left', 0, 70), (buttonCreate, 'right', 0, 100)))

    def createSkeleton(self, *args):
        skeletonIndex = cmds.optionMenu(self.skeletonsDropDown, query=True, sl=True)

        skeleton = self.skeletons[skeletonIndex - 1]
        if skeleton is not None:
            skeleton['func']()

    def createSkelNode(self, name, parent, displayHandle=False, translation=[0, 0, 0], rotation=['0', '0', '0']):
        node = cmds.group(em=True, name=name, parent=parent)
        if displayHandle:
            self.setDisplayHandle(node, 1)

        cmds.move(translation[0], translation[1], translation[2], node)
        cmds.rotate(rotation[0], rotation[1], rotation[2], node)

        return node

    def createBaseVehicle(self):
        vehicle = self.createBaseVec(False)
        cmds.select(vehicle)
        return

    def createBaseHarvester(self):
        vehicle = self.createBaseVec(True)
        cmds.select(vehicle)
        return

    def createAttacherJoints(self):
        return self.createVehicleAttacherJoints(False)

    def createBaseVec(self, isHarvester):
        vehicle = cmds.group(em=True, name='vehicleName_main_component1')
        vehicle_vis = cmds.group(em=True, name='vehicleName_root', parent=vehicle)

        self.createSkelNode("wheels", vehicle_vis)

        cameras = ""
        if isHarvester:
            cameras = self.createCamerasHarvester()
        else:
            cameras = self.createCamerasVehicle()
        cameras = cmds.parent(cameras, vehicle_vis)[0]

        cmds.parent(self.createLights(), vehicle_vis)[0]

        self.createSkelNode("exitPoint", vehicle_vis, True)

        cabin = self.createSkelNode("cabin_REPLACE_WITH_MESH", vehicle_vis)
        steeringBase = self.createSkelNode("steeringBase", cabin)
        steeringWheel = self.createSkelNode("steeringWheel_REPLACE_WITH_MESH", steeringBase)
        self.createSkelNode("playerRightHandTarget", steeringWheel, True, [-0.188, 0.03, -0.022], ['-10.518deg', '-4.708deg', '51.12deg'])
        self.createSkelNode("playerLeftHandTarget", steeringWheel, True, [0.189, 0.03, -0.023], ['-10.518deg', '-4.708deg', '-51.12deg'])

        seat = self.createSkelNode("seat_REPLACE_WITH_MESH", cabin)
        self.createSkelNode("playerSkin", seat, True)
        self.createSkelNode("lights", cabin)
        self.createSkelNode("wipers", cabin)
        self.createSkelNode("dashboards", cabin)
        self.createSkelNode("levers", cabin)
        self.createSkelNode("pedals", cabin)
        characterTargets = self.createSkelNode("characterTargets", cabin, False)
        self.createSkelNode("playerRightFootTarget", characterTargets, True)
        self.createSkelNode("playerLeftFootTarget", characterTargets, True)
        self.createSkelNode("mirrors", cabin)
        self.createSkelNode("visuals", cabin)

        cmds.parent(self.createVehicleAttacherJoints(isHarvester), vehicle_vis)

        ai = self.createSkelNode("ai", vehicle_vis)
        self.createSkelNode("aiCollisionTrigger_REPLACE_WITH_MESH", ai)
        exhaustParticles = None
        if isHarvester:
            exhaustParticles = self.createSkelNode("particles", vehicle_vis)
        else:
            exhaustParticles = self.createSkelNode("exhaustParticles", vehicle_vis)
        self.createSkelNode("exhaustParticle1", exhaustParticles, True)
        self.createSkelNode("exhaustParticle2", exhaustParticles, True)

        if isHarvester:
            self.createSkelNode("movingParts", vehicle_vis)

        self.createSkelNode("hydraulics", vehicle_vis)
        self.createSkelNode("mirrors", vehicle_vis)
        self.createSkelNode("configurations", vehicle_vis)

        if isHarvester:
            self.createSkelNode("fillVolume", vehicle_vis)
            workAreas = self.createSkelNode("workAreas", vehicle_vis)

            workAreaStraw = self.createSkelNode("workAreaStraw", workAreas)
            self.createSkelNode("workAreaStrawStart", workAreaStraw)
            self.createSkelNode("workAreaStrawWidth", workAreaStraw)
            self.createSkelNode("workAreaStrawHeight", workAreaStraw)

            workAreaChopper = self.createSkelNode("workAreaChopper", workAreas)
            self.createSkelNode("workAreaChopperStart", workAreaChopper)
            self.createSkelNode("workAreaChopperWidth", workAreaChopper)
            self.createSkelNode("workAreaChopperHeight", workAreaChopper)

        self.createSkelNode("visuals", vehicle_vis)
        self.createSkelNode("skinnedMeshes", vehicle)
        self.createSkelNode("collisions", vehicle)

        return vehicle

    def createBaseTool(self):
        tool = cmds.group(em=True, name='toolName_main_component1')

        vehicle_vis = self.createSkelNode("toolName_root", tool)

        attachable = self.createSkelNode("attachable", vehicle_vis)
        self.createSkelNode("attacherJoint", attachable)
        self.createSkelNode("topReferenceNode", attachable)
        self.createSkelNode("ptoInputNode", attachable)
        self.createSkelNode("support", attachable)
        self.createSkelNode("connectionHoses", attachable)
        self.createSkelNode("wheelChocks", attachable)

        self.createSkelNode("wheels", vehicle_vis)
        cmds.parent(self.createLights(), vehicle_vis)[0]
        self.createSkelNode("movingParts", vehicle_vis)
        self.createSkelNode("fillUnit", vehicle_vis)

        workArea = self.createSkelNode("workArea", vehicle_vis)
        self.createSkelNode("workAreaStart", workArea)
        self.createSkelNode("workAreaWidth", workArea)
        self.createSkelNode("workAreaHeight", workArea)

        self.createSkelNode("effects", vehicle_vis)

        ai = self.createSkelNode("ai", vehicle_vis)

        aiMarkers = self.createSkelNode("aiMarkers", ai)
        self.createSkelNode("aiMarkerLeft", aiMarkers)
        self.createSkelNode("aiMarkerRight", aiMarkers)
        self.createSkelNode("aiMarkerBack", aiMarkers)

        sizeMarkers = self.createSkelNode("sizeMarkers", ai)
        self.createSkelNode("sizeMarkerLeft", sizeMarkers)
        self.createSkelNode("sizeMarkerRight", sizeMarkers)
        self.createSkelNode("sizeMarkerBack", sizeMarkers)

        self.createSkelNode("aiCollisionNode", ai)

        self.createSkelNode("visuals", vehicle_vis)

        self.createSkelNode("skinnedMeshes", tool)
        self.createSkelNode("collisions", tool)

        return tool

    def createPlayer(self, steeringWheel=None):
        playerRoot = cmds.group(em=True, name='playerRoot')
        player_skin = cmds.group(em=True, name='playerSkin', parent=playerRoot)
        player_rightFoot = cmds.group(em=True, name='playerRightFootTarget', parent=playerRoot)
        player_leftFoot = cmds.group(em=True, name='playerLeftFootTarget', parent=playerRoot)

        cmds.move(-0.184, -0.514, 0.393, player_rightFoot)
        cmds.rotate('0', '-10deg', '0', player_rightFoot)
        cmds.move(0.184, -0.514, 0.393, player_leftFoot)
        cmds.rotate('0', '10deg', '0', player_leftFoot)
        self.setDisplayHandle(player_skin, 1)
        self.setDisplayHandle(player_rightFoot, 1)
        self.setDisplayHandle(player_leftFoot, 1)

        if steeringWheel is not None and steeringWheel is not False:
            rightHand = cmds.group(em=True, name='playerRightHandTarget', parent=steeringWheel)
            leftHand = cmds.group(em=True, name='playerLeftHandTarget', parent=steeringWheel)
            self.setDisplayHandle(rightHand, 1)
            self.setDisplayHandle(leftHand, 1)
            cmds.move(-0.188, 0.03, -0.022, rightHand)
            cmds.rotate('-10.518deg', '-4.708deg', '51.12deg', rightHand)
            cmds.move(0.189, 0.03, -0.023, leftHand)
            cmds.rotate('-10.518deg', '-4.708deg', '-51.12deg', leftHand)

        return playerRoot

    def setDisplayHandle(self, node, value):
        cmds.setAttr(node + '.displayHandle', value)
        cmds.setAttr(node + '.displayLocalAxis', value)

    def createCamerasVehicle(self):
        return self.createCameras(60)

    def createCamerasHarvester(self):
        return self.createCameras(75)

    def createCameras(self, fov):
        cameraGroup = cmds.group(em=True, name='cameras')
        outdoorCameraGroup = cmds.group(em=True, name='outdoorCameraTarget', parent=cameraGroup)
        outdoorCamera = cmds.camera(nearClipPlane=0.3, farClipPlane=5000, name='outdoorCamera')
        outdoorCamTransfromGroup = cmds.parent(outdoorCamera[0], outdoorCameraGroup)[0]
        I3DExporter.I3DSaveAttributeBool(outdoorCamTransfromGroup, 'i3D_collision', False)
        I3DExporter.I3DSaveAttributeBool(outdoorCamTransfromGroup, 'i3D_static', False)
        cmds.move(0, 0, 11, outdoorCamera)
        indoorCamera = cmds.camera(nearClipPlane=0.1, farClipPlane=5000, hfv=fov, name='indoorCamera')
        camTransformGroup = cmds.parent(indoorCamera[0], cameraGroup)[0]
        I3DExporter.I3DSaveAttributeBool(camTransformGroup, 'i3D_collision', False)
        I3DExporter.I3DSaveAttributeBool(camTransformGroup, 'i3D_static', False)
        cmds.rotate('-18deg', '180deg', '0', camTransformGroup)

        cmds.group(em=True, name='cameraRaycastNode1', parent=cameraGroup)
        cmds.group(em=True, name='cameraRaycastNode2', parent=cameraGroup)
        cmds.group(em=True, name='cameraRaycastNode3', parent=cameraGroup)

        cmds.rotate('-24deg', '180deg', '0', outdoorCameraGroup)

        return cameraGroup

    # vehicle
    def createLights(self):
        lightsGroup = cmds.group(em=True, name='lights')

        cmds.group(em=True, name='sharedLights', parent=lightsGroup)
        cmds.group(em=True, name='staticLights', parent=lightsGroup)

        # default lights
        defaultLights = cmds.group(em=True, name='defaultLights', parent=lightsGroup)
        self.createLight('frontLightLow', defaultLights, 80, 20, 3, [0.85, 0.85, 1], 70, rotation=['-15deg', '180deg', '0'])
        self.createLight('highBeamLow', defaultLights, 70, 30, 2, [0.85, 0.85, 1], 70, rotation=['-10deg', '180deg', '0'])

        # regular setup
        frontLightHigh = self.createLight('frontLightHigh', defaultLights, 70, 25, 3, [0.85, 0.85, 1], 100, rotation=['165deg', '-8deg', '180deg'], translation=[0.2, 0, 0])
        self.createLight('frontLightHigh1', frontLightHigh, 70, 25, 3, [0.85, 0.85, 1], 100, rotation=['165deg', '8deg', '180deg'], translation=[-0.2, 0, 0])
        highBeamHigh = self.createLight('highBeamHigh', defaultLights, 30, 60, 2.5, [0.85, 0.85, 1], 150, rotation=['170deg', '-5deg', '180deg'], translation=[0.2, 0, 0])
        self.createLight('highBeamHigh2', highBeamHigh, 30, 60, 2.5, [0.85, 0.85, 1], 150, rotation=['170deg', '5deg', '180deg'], translation=[-0.2, 0, 0])

        # top/bottom setup
        frontLightHigh = self.createLight('frontLightHighBottom', defaultLights, 70, 25, 3, [0.85, 0.85, 1], 100, rotation=['165deg', '-8deg', '180deg'], translation=[0.2, 0, 0])
        self.createLight('frontLightHighBottom1', frontLightHigh, 70, 25, 3, [0.85, 0.85, 1], 100, rotation=['165deg', '8deg', '180deg'], translation=[-0.2, 0, 0])
        highBeamHigh = self.createLight('highBeamHighBottom', defaultLights, 30, 60, 2.5, [0.85, 0.85, 1], 150, rotation=['170deg', '-5deg', '180deg'], translation=[0.2, 0, 0])
        self.createLight('highBeamHighBottom2', highBeamHigh, 30, 60, 2.5, [0.85, 0.85, 1], 150, rotation=['170deg', '5deg', '180deg'], translation=[-0.2, 0, 0])

        frontLightHigh = self.createLight('frontLightHighTop', defaultLights, 70, 25, 3, [0.85, 0.85, 1], 100, rotation=['165deg', '-8deg', '180deg'], translation=[0.75, 0, 0])
        self.createLight('frontLightHighTop1', frontLightHigh, 70, 25, 3, [0.85, 0.85, 1], 100, rotation=['165deg', '8deg', '180deg'], translation=[-0.75, 0, 0])
        highBeamHigh = self.createLight('highBeamHighTop', defaultLights, 30, 60, 2.5, [0.85, 0.85, 1], 150, rotation=['170deg', '-5deg', '180deg'], translation=[0.75, 0, 0])
        self.createLight('highBeamHighTop2', highBeamHigh, 30, 60, 2.5, [0.85, 0.85, 1], 150, rotation=['170deg', '5deg', '180deg'], translation=[-0.75, 0, 0])

        self.createLight('licensePlateLightHigh', defaultLights, 120, 0.5, 2, [1, 1, 1], 15, rotation=['0deg', '0deg', '0deg'])

        self.createPointLight(name="interiorScreenLight", parent=defaultLights, intensity=0.25, rgb=[0.59, 0.653079, 1], clipDistance=20)

        workLights = cmds.group(em=True, name='workLights', parent=lightsGroup)

        # work lights front
        self.createLight('workLightFrontLow', workLights, 130, 20, 2, [0.85, 0.85, 1], 50, rotation=['-20deg', '180deg', '0deg'])
        workLightFrontHigh1 = self.createLight('workLightFrontHigh', workLights, 90, 25, 2, [0.85, 0.85, 1], 50, rotation=['-15deg', '155deg', '0deg'])
        self.createLight('workLightFrontHigh2', workLightFrontHigh1, 90, 25, 2, [0.85, 0.85, 1], 50, rotation=['-15deg', '-155deg', '0deg'])

        # work lights back
        self.createLight('workLightBackLow', workLights, 130, 20, 2, [0.85, 0.85, 1], 50, rotation=['-20deg', '0deg', '0deg'])
        workLightBackHigh1 = self.createLight('workLightBackHigh', workLights, 90, 25, 2, [0.85, 0.85, 1], 50, rotation=['-20deg', '-20deg', '0deg'])
        self.createLight('workLightBackHigh2', workLightBackHigh1, 90, 25, 2, [0.85, 0.85, 1], 50, rotation=['-20deg', '20deg', '0deg'])

        # back lights
        backLights = cmds.group(em=True, name='backLights', parent=lightsGroup)
        backLightsHigh1 = self.createLight('backLightsHigh', backLights, 130, 2.5, 2, [0.5, 0, 0], 15, rotation=['-15deg', '0deg', '0deg'])
        self.createLight('backLightsHigh2', backLightsHigh1, 130, 2.5, 2, [0.5, 0, 0], 15, rotation=['-15deg', '-0deg', '0deg'])

        # turn lights
        turnLights = cmds.group(em=True, name='turnLights', parent=lightsGroup)
        turnLightLeftFront = self.createLight('turnLightLeftFront', turnLights, 120, 4, 3, [0.31, 0.14, 0], 20, rotation=['-15deg', '180deg', '0deg'])
        self.createLight('turnLightLeftBack', turnLightLeftFront, 120, 4, 3, [0.31, 0.14, 0], 20, rotation=['-15deg', '0deg', '0deg'])
        turnLightRightFront = self.createLight('turnLightRightFront', turnLights, 120, 4, 3, [0.31, 0.14, 0], 20, rotation=['-15deg', '180deg', '0deg'])
        self.createLight('turnLightRightBack', turnLightRightFront, 120, 4, 3, [0.31, 0.14, 0], 20, rotation=['-15deg', '0deg', '0deg'])

        # beacon lights
        beaconLights = cmds.group(em=True, name='beaconLights', parent=lightsGroup)
        cmds.group(em=True, name='beaconLight1', parent=beaconLights)

        # reverse lights
        reverseLights = cmds.group(em=True, name='reverseLights', parent=lightsGroup)
        reverseLight1 = self.createLight('reverseLightHigh', reverseLights, 130, 2.5, 3, [0.9, 0.9, 1], 30, rotation=['-15deg', '0deg', '0deg'])
        self.createLight('reverseLightHigh2', reverseLight1, 130, 2.5, 3, [0.9, 0.9, 1], 30, rotation=['-15deg', '0deg', '0deg'])

        cmds.select(lightsGroup)

        return lightsGroup

    # vehicle
    def createLight(self, name, parent, coneAngle, intensity, dropOff, rgb, locatorScale=50, rotation=['0deg', '0deg', '0deg'], translation=[0, 0, 0], castShadowMap=False, depthMapBias=0.001, depthMapResolution=256):
        light = cmds.spotLight(coneAngle=coneAngle, intensity=intensity, dropOff=dropOff, rgb=rgb)
        if castShadowMap and depthMapBias is not None and depthMapResolution is not None:
            cmds.setAttr(light + '.useDepthMapShadows', 1)
            cmds.setAttr(light + '.dmapResolution', depthMapResolution)
            cmds.setAttr(light + '.dmapBias', depthMapBias)

        cmds.setAttr(light + '.locatorScale', locatorScale)
        parents = cmds.listRelatives(light, fullPath=True, parent=True)
        I3DExporter.I3DSaveAttributeBool(parents[0], 'i3D_collision', False)
        I3DExporter.I3DSaveAttributeBool(parents[0], 'i3D_static', False)
        I3DExporter.I3DSaveAttributeFloat(parents[0], 'i3D_clipDistance', 75.0)

        cmds.rotate(rotation[0], rotation[1], rotation[2], parents[0])
        cmds.move(translation[0], translation[1], translation[2], parents[0])
        lightTransform = cmds.parent(parents[0], parent)[0]
        lightTransform = cmds.rename(lightTransform, name)
        cmds.setAttr(lightTransform + '.lodVisibility', 1)
        return lightTransform

    # placeable, low
    def createPointLight(self, name, parent, intensity=7, rgb=[0.44, 0.4, 0.4], clipDistance=75):
        lightShape = cmds.pointLight(intensity=intensity, rgb=rgb, useRayTraceShadows=False)
        light = cmds.parent(cmds.listRelatives(lightShape, fullPath=True, parent=True)[0], parent)[0]
        light = cmds.rename(light, name)

        I3DExporter.I3DSaveAttributeBool(light, 'i3D_collision', False)
        I3DExporter.I3DSaveAttributeBool(light, 'i3D_static', False)
        I3DExporter.I3DSaveAttributeFloat(light, 'i3D_clipDistance', clipDistance)

        return light

    # placeable, high
    def createSpotLight(self, name, parent, coneAngle=120, intensity=18, dropOff=4, rgb=[0.55, 0.5, 0.5], clipDistance=75):
        lightShape = cmds.spotLight(coneAngle=coneAngle, intensity=intensity, dropOff=dropOff, rgb=rgb, useRayTraceShadows=True)
        cmds.rotate('-90deg', '0deg', '0deg', lightShape)
        light = cmds.parent(cmds.listRelatives(lightShape, fullPath=True, parent=True)[0], parent)[0]
        light = cmds.rename(light, name)

        I3DExporter.I3DSaveAttributeBool(light, 'i3D_collision', False)
        I3DExporter.I3DSaveAttributeBool(light, 'i3D_static', False)
        I3DExporter.I3DSaveAttributeFloat(light, 'i3D_clipDistance', clipDistance)

        return light

    def createVehicleAttacherJoints(self, isHarvester):
        attacherJointGroup = cmds.group(em=True, name='attacherJoints')
        tools = cmds.group(em=True, name='tools', parent=attacherJointGroup)
        trailers = cmds.group(em=True, name='trailers', parent=attacherJointGroup)
        ptos = cmds.group(em=True, name='ptos', parent=attacherJointGroup)
        cmds.group(em=True, name='connectionHoses', parent=attacherJointGroup)

        if not isHarvester:
            # attacherjointbackrot
            attacherJointBackRot = cmds.group(em=True, name='attacherJointBackRot', parent=tools)
            attacherJointBackRot2 = cmds.group(em=True, name='attacherJointBackRot2', parent=attacherJointBackRot)
            attacherJointBack = cmds.group(em=True, name='attacherJointBack', parent=attacherJointBackRot2)
            self.setDisplayHandle(attacherJointBack, 1)
            cmds.xform(attacherJointBack, a=True, ro=['0', '90deg', '0'])
            cmds.xform(attacherJointBackRot2, r=True, ro=['13deg', '0', '0'])
            cmds.move(0, 0, -1, attacherJointBackRot2)
            cmds.xform(attacherJointBackRot, r=True, ro=['-13deg', '0', '0'])

            # attacherjointbackbottomarm
            attacherJointBackArmBottom = cmds.group(em=True, name='attacherJointBackArmBottom', parent=tools)
            attacherJointBackArmBottomTrans = cmds.group(em=True, name='attacherJointBackArmBottomTrans_REPLACE_WITH_MESH', parent=attacherJointBackArmBottom)
            referencePointBackBottom = cmds.group(em=True, name='referencePointBackBottom', parent=attacherJointBackArmBottomTrans)
            cmds.move(0, 0, -1, referencePointBackBottom)
            cmds.rotate('-13deg', '0', '0', attacherJointBackArmBottom)

            # attacherjointbacktoparm
            attacherJointBackArmTop = cmds.group(em=True, name='attacherJointBackArmTop', parent=tools)
            cmds.rotate('67deg', '0', '0', attacherJointBackArmTop)

        # attacherjointfrontrot
        attacherJointFrontRot = cmds.group(em=True, name='attacherJointFrontRot', parent=tools)
        attacherJointFrontRot2 = cmds.group(em=True, name='attacherJointFrontRot2', parent=attacherJointFrontRot)
        attacherJointFront = cmds.group(em=True, name='attacherJointFront', parent=attacherJointFrontRot2)
        self.setDisplayHandle(attacherJointFront, 1)
        cmds.xform(attacherJointFront, a=True, ro=['0', '-90deg', '0'])
        cmds.xform(attacherJointFrontRot2, r=True, ro=['13deg', '0', '0'])
        cmds.move(0, 0, 1, attacherJointFrontRot2)
        cmds.xform(attacherJointFrontRot, r=True, ro=['-13deg', '0', '0'])

        # attacherjointfrontbottomarm
        attacherJointFrontArmBottom = cmds.group(em=True, name='attacherJointFrontArmBottom', parent=tools)
        attacherJointFrontArmBottomTrans = cmds.group(em=True, name='attacherJointFrontArmBottomTrans_REPLACE_WITH_MESH', parent=attacherJointFrontArmBottom)
        referencePointFrontBottom = cmds.group(em=True, name='referencePointFrontBottom', parent=attacherJointFrontArmBottomTrans)
        cmds.move(0, 0, 1, referencePointFrontBottom)
        cmds.rotate('-26deg', '0', '0', attacherJointFrontArmBottom)

        # attacherjointfronttoparm
        attacherJointFrontArmTop = cmds.group(em=True, name='attacherJointFrontArmTop', parent=tools)
        cmds.rotate('-40deg', '0', '0', attacherJointFrontArmTop)
        self.setDisplayHandle(attacherJointFrontArmTop, 1)

        # trailer joints
        trailerAttacherJointBack = cmds.group(em=True, name='trailerAttacherJointBack', parent=trailers)
        cmds.rotate('0', '90deg', '0', trailerAttacherJointBack)
        self.setDisplayHandle(trailerAttacherJointBack, 1)

        if not isHarvester:
            trailerAttacherJointBackLow = cmds.group(em=True, name='trailerAttacherJointBackLow', parent=trailers)
            cmds.rotate('0', '90deg', '0', trailerAttacherJointBackLow)
            self.setDisplayHandle(trailerAttacherJointBackLow, 1)

        if not isHarvester:
            trailerAttacherJointFront = cmds.group(em=True, name='trailerAttacherJointFront', parent=trailers)
            cmds.rotate('0', '-90deg', '0', trailerAttacherJointFront)
            self.setDisplayHandle(trailerAttacherJointFront, 1)

        # ptos
        if not isHarvester:
            ptoBack = cmds.group(em=True, name='ptoBack', parent=ptos)
            cmds.rotate('0', '180deg', '0', ptoBack)
            self.setDisplayHandle(ptoBack, 1)

        ptoFront = cmds.group(em=True, name='ptoFront', parent=ptos)
        self.setDisplayHandle(ptoFront, 1)

        if not isHarvester:
            frontloader = cmds.group(em=True, name='frontloader', parent=attacherJointGroup)
            cmds.rotate('0', '0deg', '0', frontloader)
            self.setDisplayHandle(frontloader, 1)

        return attacherJointGroup

    def createTrafficVehicle(self):
        trafficVehicle = cmds.group(em=True, name='trafficVehicle01')

        self.createSkelNode("wheels", trafficVehicle)

        lights = self.createSkelNode("lights", trafficVehicle)
        self.createSkelNode("staticLights", lights)
        realLights = self.createSkelNode("realLights", lights)

        self.createLight('frontLightLow', realLights, 80, 20, 3, [0.85, 0.85, 1], 50, rotation=['165deg', '0deg', '-180deg'], translation=[0, 0.6, 3.5])
        frontLightHigh1 = self.createLight('frontLightHigh1', realLights, 70, 25, 3, [0.85, 0.85, 1], 50, rotation=['165deg', '8deg', '180deg'], translation=[-0.5, 0.6, 3.5])
        frontLightHigh2 = self.createLight('frontLightHigh2', realLights, 70, 25, 3, [0.85, 0.85, 1], 50, rotation=['165deg', '-8deg', '180deg'], translation=[0.5, 0.6, 3.5])
        cmds.parent(frontLightHigh2, frontLightHigh1)

        backLightHigh1 = self.createLight('backLightHigh1', realLights, 130, 2.5, 2, [0.5, 0, 0], 50, rotation=['-15deg', '0deg', '0deg'], translation=[-0.5, 0.8, -1])
        backLightHigh2 = self.createLight('backLightHigh2', realLights, 130, 2.5, 2, [0.5, 0, 0], 50, rotation=['-15deg', '0deg', '0deg'], translation=[0.5, 0.8, -1])
        cmds.parent(backLightHigh2, backLightHigh1)
        cmds.parent(backLightHigh1, frontLightHigh1)

        self.createSkelNode("trafficCollisionNode", trafficVehicle)
        self.createSkelNode("driver_TO_BE_REPLACED", trafficVehicle)
        self.createSkelNode("vehicle_vis", trafficVehicle)

        return trafficVehicle

    def createPlaceable(self):
        placeable = cmds.group(em=True, name='placeable')
        self.createPlaceableElements(placeable)

        return placeable

    def createAnimalHusbandry(self):
        animalHusbandry = cmds.group(em=True, name='animalHusbandry')

        self.createPlaceableElements(animalHusbandry)

        food = self.createSkelNode("food", animalHusbandry)
        self.createSkelNode("fillVolume", food)
        self.createExactFillRootNode("exactFillRootNodeFood", food)
        foodPlaces = self.createSkelNode("foodPlaces", food)
        self.createSkelNode("foodPlace01", foodPlaces)
        self.createSkelNode("foodPlace02", foodPlaces)
        self.createSkelNode("foodPlace03", foodPlaces)

        self.createSkelNode("storage", animalHusbandry)

        straw = self.createSkelNode("straw", animalHusbandry)
        self.createPlane("strawPlane", straw, 5, 5)
        self.createExactFillRootNode("exactFillRootNodeStraw", straw)

        milktank = self.createSkelNode("milktank", animalHusbandry)
        self.createTrigger("milktankTrigger", "VEHICLE_TRIGGER", milktank)

        lqiuidManureTank = self.createSkelNode("lqiuidManureTank", animalHusbandry)
        self.createTrigger("lqiuidManureTankTrigger", "VEHICLE_TRIGGER", lqiuidManureTank)

        waterPlaces = self.createSkelNode("waterPlaces", animalHusbandry)
        self.createSkelNode("waterPlace01", waterPlaces)
        self.createSkelNode("waterPlace02", waterPlaces)
        self.createSkelNode("waterPlace03", waterPlaces)

        palletAreas = self.createSkelNode("palletAreas", animalHusbandry)
        self.createTrigger("palletTrigger", "VEHICLE_TRIGGER", palletAreas)
        palletAreaStart01 = self.createSkelNode("palletAreaStart01", palletAreas)
        self.createSkelNode("palletAreaEnd01", palletAreaStart01)
        palletAreaStart02 = self.createSkelNode("palletAreaStart02", palletAreas)
        self.createSkelNode("palletAreaEnd02", palletAreaStart02)

        navRootNode = self.createSkelNode("navigationRootNode", animalHusbandry)
        self.createPlane("navigationMesh", navRootNode)
        walkingPlane = self.createPlane("walkingPlane", navRootNode)
        I3DExporter.I3DRemoveAttributes(walkingPlane)
        I3DExporter.I3DSaveAttributeBool(walkingPlane, 'i3D_collision', True)
        I3DExporter.I3DSaveAttributeBool(walkingPlane, 'i3D_static', True)
        I3DExporter.I3DSaveAttributeBool(walkingPlane, 'i3D_nonRenderable', True)
        self.setCollisionFilterFromPresetName(walkingPlane, "ANIMAL_POSITIONING_COL")

        fences = self.createSkelNode("fences", animalHusbandry)
        fence1 = self.createSkelNode("fence01", fences)
        self.createSkelNode("fence1Node01", fence1, True)
        self.createSkelNode("fence1Node02", fence1, True)
        self.createSkelNode("fence1Node03", fence1, True)
        self.createSkelNode("fence1Node04", fence1, True)

        self.createSkelNode("warningStripes", animalHusbandry)
        self.createTrigger("loadingTrigger", "PLAYER_VEHICLE_TRIGGER", animalHusbandry)


        return animalHusbandry

    def createPlaceableElements(self, parent):
        clearAreas = self.createSkelNode("clearAreas", parent)
        node = clearAreaStart01 = self.createSkelNode("clearAreaStart01", clearAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "clearAreaStart01")
        node = self.createSkelNode("clearAreaWidth01", clearAreaStart01, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "clearAreaWidth01")
        node = self.createSkelNode("clearAreaHeight01", clearAreaStart01, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "clearAreaHeight01")
        node = clearAreaStart02 = self.createSkelNode("clearAreaStart02", clearAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "clearAreaStart02")
        node = self.createSkelNode("clearAreaWidth02", clearAreaStart02, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "clearAreaWidth02")
        node = self.createSkelNode("clearAreaHeight02", clearAreaStart02, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "clearAreaHeight02")
        node = clearAreaStart03 = self.createSkelNode("clearAreaStart03", clearAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "clearAreaStart03")
        node = self.createSkelNode("clearAreaWidth03", clearAreaStart03, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "clearAreaWidth03")
        node = self.createSkelNode("clearAreaHeight03", clearAreaStart03, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "clearAreaHeight03")

        levelAreas = self.createSkelNode("levelAreas", parent)
        node = levelAreaStart01 = self.createSkelNode("levelAreaStart01", levelAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "levelAreaStart01")
        node = self.createSkelNode("levelAreaWidth01", levelAreaStart01, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "levelAreaWidth01")
        node = self.createSkelNode("levelAreaHeight01", levelAreaStart01, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "levelAreaHeight01")
        node = levelAreaStart02 = self.createSkelNode("levelAreaStart02", levelAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "levelAreaStart02")
        node = self.createSkelNode("levelAreaWidth02", levelAreaStart02, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "levelAreaWidth02")
        node = self.createSkelNode("levelAreaHeight02", levelAreaStart02, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "levelAreaHeight02")
        node = levelAreaStart03 = self.createSkelNode("levelAreaStart03", levelAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "levelAreaStart03")
        node = self.createSkelNode("levelAreaWidth03", levelAreaStart03, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "levelAreaWidth03")
        node = self.createSkelNode("levelAreaHeight03", levelAreaStart03, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "levelAreaHeight03")

        paintAreas = self.createSkelNode("paintAreas", parent)
        node = paintAreaStart01 = self.createSkelNode("paintAreaStart01", paintAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "paintAreaStart01")
        node = self.createSkelNode("paintAreaWidth01", paintAreaStart01, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "paintAreaWidth01")
        node = self.createSkelNode("paintAreaHeight01", paintAreaStart01, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "paintAreaHeight01")
        node = paintAreaStart02 = self.createSkelNode("paintAreaStart02", paintAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "paintAreaStart02")
        node = self.createSkelNode("paintAreaWidth02", paintAreaStart02, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "paintAreaWidth02")
        node = self.createSkelNode("paintAreaHeight02", paintAreaStart02, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "paintAreaHeight02")
        node = paintAreaStart03 = self.createSkelNode("paintAreaStart03", paintAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "paintAreaStart03")
        node = self.createSkelNode("paintAreaWidth03", paintAreaStart03, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "paintAreaWidth03")
        node = self.createSkelNode("paintAreaHeight03", paintAreaStart03, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "paintAreaHeight03")

        indoorAreas = self.createSkelNode("indoorAreas", parent)
        node = indoorAreaStart01 = self.createSkelNode("indoorAreaStart01", indoorAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "indoorAreaStart01")
        node = self.createSkelNode("indoorAreaWidth01", indoorAreaStart01, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "indoorAreaWidth01")
        node = self.createSkelNode("indoorAreaHeight01", indoorAreaStart01, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "indoorAreaHeight01")
        node = indoorAreaStart02 = self.createSkelNode("indoorAreaStart02", indoorAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "indoorAreaStart02")
        node = self.createSkelNode("indoorAreaWidth02", indoorAreaStart02, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "indoorAreaWidth02")
        node = self.createSkelNode("indoorAreaHeight02", indoorAreaStart02, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "indoorAreaHeight02")
        node = indoorAreaStart03 = self.createSkelNode("indoorAreaStart03", indoorAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "indoorAreaStart03")
        node = self.createSkelNode("indoorAreaWidth03", indoorAreaStart03, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "indoorAreaWidth03")
        node = self.createSkelNode("indoorAreaHeight03", indoorAreaStart03, True, [1, 0, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "indoorAreaHeight03")

        testAreas = self.createSkelNode("testAreas", parent)
        node = testAreaStart01 = self.createSkelNode("testAreaStart01", testAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "testAreaStart01")
        node = self.createSkelNode("testAreaEnd01", testAreaStart01, True, [1, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "testAreaEnd01")
        node = testAreaStart02 = self.createSkelNode("testAreaStart02", testAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "testAreaStart02")
        node = self.createSkelNode("testAreaEnd02", testAreaStart02, True, [1, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "testAreaEnd02")
        node = testAreaStart03 = self.createSkelNode("testAreaStart03", testAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "testAreaStart03")
        node = self.createSkelNode("testAreaEnd03", testAreaStart03, True, [1, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "testAreaEnd03")

        tipOcclusionUpdateAreas = self.createSkelNode("tipOcclusionUpdateAreas", parent)
        node = tipOcclusionUpdateAreaStart01 = self.createSkelNode("tipOcclusionUpdateAreaStart01", tipOcclusionUpdateAreas, True)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "tipOcclusionUpdateAreaStart01")
        node = self.createSkelNode("tipOcclusionUpdateAreaEnd01", tipOcclusionUpdateAreaStart01, True, [1, 0, 1])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "tipOcclusionUpdateAreaEnd01")

        lights = self.createSkelNode("lights", parent)
        realLights = self.createSkelNode("realLights", lights)
        node = realLightsLow = self.createSkelNode("realLightsLow", realLights)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "realLightsLow")
        self.createPointLight("pointLightLow", realLightsLow)
        node = realLightsHigh = self.createSkelNode("realLightsHigh", realLights)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "realLightsHigh")
        self.createSpotLight("spotLightHigh", realLightsHigh)
        self.createSkelNode("linkedLights", lights)
        node = self.createSkelNode("lightSwitch", lights)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "lightSwitch")
        node = self.createTrigger("lightTrigger", "PLAYER_VEHICLE_TRIGGER", lights, size=[2, 2, 2], translation=[0, 1, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "lightTrigger")

        doors = self.createSkelNode("doors", parent)
        node = self.createTrigger("doorTrigger", "PLAYER_VEHICLE_TRIGGER", doors, size=[2, 2, 2], translation=[0, 1, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "doorTrigger")

        node = self.createTrigger("infoTrigger", "PLAYER_TRIGGER", parent, size=[10, 5, 10])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "infoTrigger")

        sellingStation = self.createSkelNode("sellingStation", parent)
        I3DExporter.I3DSaveAttributeString(sellingStation, 'i3D_xmlIdentifier', "sellingStation")
        unloadTrigger = self.createExactFillRootNode("unloadTrigger", sellingStation)
        I3DExporter.I3DSaveAttributeString(unloadTrigger, 'i3D_xmlIdentifier', "unloadTrigger")
        node = self.createSkelNode("unloadTriggerMarker", sellingStation)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "unloadTriggerMarker")
        node = self.createSkelNode("unloadTriggerAINode", sellingStation)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "unloadTriggerAINode")

        productionPoint = self.createSkelNode("productionPoint", parent)
        node = self.createTrigger("playerTrigger", "PLAYER_TRIGGER", productionPoint, size=[2, 2, 2], translation=[0, 1, 0])
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "playerTrigger")
        node = self.createSkelNode("playerTriggerMarker", productionPoint)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "playerTriggerMarker")

        palletSpawner = self.createSkelNode("palletSpawner", parent)
        I3DExporter.I3DSaveAttributeString(node, 'i3D_xmlIdentifier', "palletSpawner")
        palletAreaStart01 = self.createSkelNode("palletAreaStart01", palletSpawner, True)
        I3DExporter.I3DSaveAttributeString(palletAreaStart01, 'i3D_xmlIdentifier', "palletAreaStart01")
        palletAreaEnd01 = self.createSkelNode("palletAreaEnd01", palletAreaStart01, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(palletAreaEnd01, 'i3D_xmlIdentifier', "palletAreaEnd01")
        palletAreaStart02 = self.createSkelNode("palletAreaStart02", palletSpawner, True)
        I3DExporter.I3DSaveAttributeString(palletAreaStart02, 'i3D_xmlIdentifier', "palletAreaStart02")
        palletAreaEnd02 = self.createSkelNode("palletAreaEnd02", palletAreaStart02, True, [0, 0, 1])
        I3DExporter.I3DSaveAttributeString(palletAreaEnd02, 'i3D_xmlIdentifier', "palletAreaEnd02")

        visuals = self.createSkelNode("visuals", parent)
        self.createSkelNode("seasons", visuals)

        collisions = self.createSkelNode("collisions", parent)
        self.createCollision("collision", "BUILDING", collisions, isCube=True)
        self.createCollision("tipCollision", "TIP_BLOCKING_COL", collisions)
        tipColWall = self.createCollision("tipCollisionWall", "TIP_BLOCKING_COL", collisions)
        I3DExporter.I3DSaveAttributeFloat(tipColWall, 'collisionHeight', 4)

    def createCollision(self, name, colFilterPresetName, parent, size=[1, 1, 1], isCube=False):
        colShape = None
        if isCube:
            colShape = cmds.polyCube(n=name, w=size[0], h=size[1], d=size[2])[0]
        else:
            colShape = cmds.polyPlane(n=name, width=size[0], height=size[1], subdivisionsX=1, subdivisionsY=1)[0]

        I3DExporter.I3DRemoveAttributes(colShape)
        I3DExporter.I3DSaveAttributeBool(colShape, 'i3D_collision', True)
        I3DExporter.I3DSaveAttributeBool(colShape, 'i3D_static', True)
        I3DExporter.I3DSaveAttributeBool(colShape, 'i3D_nonRenderable', True)
        self.setCollisionFilterFromPresetName(colShape, colFilterPresetName)

        colShape = cmds.parent(colShape, parent)[0]  # parent and return full name
        return colShape

    def createTrigger(self, name, colFilterPresetName, parent, size=[1, 1, 1], translation=[0, 1, 0]):
        trigger = cmds.polyCube(n=name, w=size[0], h=size[1], d=size[2])[0]
        cmds.move(translation[0], translation[1], translation[2], trigger)
        I3DExporter.I3DRemoveAttributes(trigger)
        I3DExporter.I3DSaveAttributeBool(trigger, 'i3D_collision', True)
        I3DExporter.I3DSaveAttributeBool(trigger, 'i3D_static', True)
        I3DExporter.I3DSaveAttributeBool(trigger, 'i3D_trigger', True)
        I3DExporter.I3DSaveAttributeBool(trigger, 'i3D_nonRenderable', True)
        self.setCollisionFilterFromPresetName(trigger, colFilterPresetName)

        trigger = cmds.parent(trigger, parent)[0]  # parent and return full name
        return trigger

    def createExactFillRootNode(self, name, parent):
        exactFillRootNode = cmds.polyCube(n=name, w=1, h=1, d=1)[0]
        I3DExporter.I3DRemoveAttributes(exactFillRootNode)
        I3DExporter.I3DSaveAttributeBool(exactFillRootNode, 'i3D_static', False)
        I3DExporter.I3DSaveAttributeBool(exactFillRootNode, 'i3D_kinematic', True)
        I3DExporter.I3DSaveAttributeBool(exactFillRootNode, 'i3D_compound', True)
        I3DExporter.I3DSaveAttributeBool(exactFillRootNode, 'i3D_collision', True)
        I3DExporter.I3DSaveAttributeBool(exactFillRootNode, 'i3D_nonRenderable', True)
        self.setCollisionFilterFromPresetName(exactFillRootNode, "EXACT_FILL_ROOT_NODE")

        exactFillRootNode = cmds.parent(exactFillRootNode, parent)[0]  # parent and return full name
        return exactFillRootNode

    def createPlane(self, name, parent, sx=1, sy=1):
        plane = cmds.polyPlane(n=name, w=1, h=1, sx=sx, sy=sy)[0]
        I3DExporter.I3DRemoveAttributes(plane)

        plane = cmds.parent(plane, parent)[0]  # parent and return full name

        return plane
    
    def setCollisionFilterFromPresetName(self, shape, presetName):
        groupHex, maskHex = I3DExporter.colMaskFlags.getPresetGroupAndMask(presetName, True)
        if groupHex is None:
            I3DExporter.I3DShowWarning("Skeletons setCollisionFilterFromPresetName(): Unable to find collision filter preset '{}'".format(presetName))
        else:
            I3DExporter.I3DSaveAttributeHex(shape, 'i3D_collisionFilterGroup', groupHex)
            I3DExporter.I3DSaveAttributeHex(shape, 'i3D_collisionFilterMask', maskHex)

        return shape

def getI3DExporterPlugin():
    return Skeletons()

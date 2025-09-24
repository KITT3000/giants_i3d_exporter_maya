#
# Shader Tools Plugin for Maya I3D Exporter
# Includes: exportObjectDataTexture, generateObjectDataFromCurve, generateObjectDataFromAnimations, morphTarget, jigglingVertexColor, generateObjectDataFromCurves
#
# @created 26/02/2020
# Code imported from I3DExporter.py
#
# Copyright (c) 2008-2015 GIANTS Software GmbH, Confidential, All Rights Reserved.
# Copyright (c) 2003-2015 Christian Ammann and Stefan Geiger, Confidential, All Rights Reserved.
#

import I3DUtils


import exportObjectDataTexture
import generateObjectDataFromCurve
import generateObjectDataFromAnimations
import morphTarget
import jigglingVertexColor
import generateObjectDataFromCurves
import vehicleShaderTools
I3DUtils.reloadModule(exportObjectDataTexture)
I3DUtils.reloadModule(generateObjectDataFromCurve)
I3DUtils.reloadModule(generateObjectDataFromAnimations)
I3DUtils.reloadModule(morphTarget)
I3DUtils.reloadModule(jigglingVertexColor)
I3DUtils.reloadModule(generateObjectDataFromCurves)
I3DUtils.reloadModule(vehicleShaderTools)


class ShaderTools:
    def __init__(self):
        self.name = "Shader-Tools"
        self.page = "Tools"
        self.prio = 8

        self.shelfCommand = "import I3DUtils; import ShaderTools; I3DUtils.reloadModule(ShaderTools); plugin = ShaderTools.ShaderTools(); plugin.%s(); del plugin;"

        self.generateObjectDataFromCurveInfo = {"name": "Object Data from Curve",
                                                "category": self.name,
                                                "annotation": "Creates equally distributed transforms along the curve",
                                                "button_function": self.executeGenerateObjectDataFromCurve,
                                                "shelf_label": "dataCurve",
                                                "shelf_command": self.shelfCommand % "executeGenerateObjectDataFromCurve"}

        self.generateObjectDataFromAnimationsInfo = {"name": "Object Data from Animations",
                                                     "category": self.name,
                                                     "annotation": "Creates equally distributed transforms along motion trails",
                                                     "button_function": self.executeGenerateObjectDataFromAnimations,
                                                     "shelf_label": "dataAnims",
                                                     "shelf_command": self.shelfCommand % "executeGenerateObjectDataFromAnimations"}

        self.exportObjectDataTextureInfo = {"name": "Export Object Data Texture",
                                            "category": self.name,
                                            "annotation": "Exports texture array with position, orientation and scale data stored into the pixels of the texture",
                                            "button_function": self.executeExportObjectDataTexture,
                                            "shelf_label": "expObjData",
                                            "shelf_command": self.shelfCommand % "executeExportObjectDataTexture"}

        self.morphTargetInfo = {"name": "Morph Target Vertex Color",
                                "category": self.name,
                                "annotation": "Bakes difference between source and target mesh into vertexColor (0..1 normalized). Used with some shaders",
                                "button_function": self.executeMorphTarget,
                                "shelf_label": "moTa",
                                "shelf_command": self.shelfCommand % "executeMorphTarget"}

        self.jigglingVertexColorInfo = {"name": "Jiggling Vertex Color",
                                        "category": self.name,
                                        "annotation": "Saves object space (compressed) positions into vertex colors. Used with vehicleShader",
                                        "button_function": self.executeJigglingVertexColor,
                                        "shelf_label": "jigVc",
                                        "shelf_command": self.shelfCommand % "executeJigglingVertexColor"}

        self.generateObjectDataFromCurveSInfo = {"name": "Object Data from CurveS",
                                                 "category": self.name,
                                                 "annotation": "Creates equally distributed transforms along the multiple curves",
                                                 "button_function": self.executeGenerateObjectDataFromCurveS,
                                                 "shelf_label": "dataCurveS",
                                                 "shelf_command": self.shelfCommand % "executeGenerateObjectDataFromCurveS"}

    def getToolsButtons(self):
        return [self.generateObjectDataFromCurveInfo,
                self.generateObjectDataFromAnimationsInfo,
                self.exportObjectDataTextureInfo,
                self.morphTargetInfo,
                self.jigglingVertexColorInfo,
                self.generateObjectDataFromCurveSInfo,]

    def getShelfScripts(self):
        return [self.generateObjectDataFromCurveInfo,
                self.generateObjectDataFromAnimationsInfo,
                self.exportObjectDataTextureInfo,
                self.morphTargetInfo,
                self.jigglingVertexColorInfo,
                self.generateObjectDataFromCurveSInfo,]

    def onExporterOpen(self):
        print("Synchronize material templates..")
        vehicleShaderTools.synhronizeMaterialTemplates()

    def executeExportObjectDataTexture(self, *args):
        exportObjectDataTexture.exportObjectDataTexture()

    def executeGenerateObjectDataFromCurve(self, *args):
        generateObjectDataFromCurve.generateObjectDataFromCurveWin()

    def executeGenerateObjectDataFromAnimations(self, *args):
        generateObjectDataFromAnimations.generateObjectDataFromAnimationsWin()

    def executeMorphTarget(self, *args):
        morphTarget.morphTargetWin()

    def executeJigglingVertexColor(self, *args):
        jigglingVertexColor.runOnSelection()

    def executeGenerateObjectDataFromCurveS(self, *args):
        generateObjectDataFromCurves.generateObjectDataFromCurvesWin()


def getI3DExporterPlugin():
    return ShaderTools()

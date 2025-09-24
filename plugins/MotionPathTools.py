#
# Toggle View Cube Plugin for Maya I3D Exporter
# Simple plugin to hide and show the view cube
#
# @author   Stefan Maurus
# @date     01/10/2020
#
# Copyright (c) 2008-2015 GIANTS Software GmbH, Confidential, All Rights Reserved.
# Copyright (c) 2003-2015 Christian Ammann and Stefan Geiger, Confidential, All Rights Reserved.
#

import I3DUtils
import MotionPathEffectAssembler


class MotionPathTools:
    def __init__(self):
        self.name = "Motion Path Tools"
        self.page = "Tools"
        self.prio = 7

        self.shelfCommand = "import I3DUtils; import MotionPathTools; I3DUtils.reloadModule(MotionPathTools); plugin = MotionPathTools.MotionPathTools(); plugin.%s(); del plugin;"

        self.motionPathToolsInfo = {"name": "Motion Path Effect Mesh Generator",
                                    "category": "Motion Path Tools",
                                    "annotation": "Tool to generate merged effect meshes based on effect configuration xml file",
                                    "button_function": self.showMotionPathMeshGenerator,
                                    "shelf_label": "ToViCu",
                                    "shelf_command": self.shelfCommand % "showMotionPathMeshGenerator"}

    def getToolsButtons(self):
        return [self.motionPathToolsInfo]

    def getShelfScripts(self):
        return [self.motionPathToolsInfo]

    def showMotionPathMeshGenerator(self, *args):
        I3DUtils.reloadModule(MotionPathEffectAssembler)
        MotionPathEffectAssembler.MotionPathEffectAssembler()


def getI3DExporterPlugin():
    return MotionPathTools()

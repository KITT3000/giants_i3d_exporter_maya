#
# Material Tools Plugin for Maya I3D Exporter
# Basic tools for material operations (Remove Duplicate Materials, Remove Duplicate Textures, Rename Materials, Get Component Shader)
#
# @created 18/04/2019
# Code imported from I3DExporter.py
#
# Copyright (c) 2008-2015 GIANTS Software GmbH, Confidential, All Rights Reserved.
# Copyright (c) 2003-2015 Christian Ammann and Stefan Geiger, Confidential, All Rights Reserved.
#
import I3DUtils

import deleteDuplicateMaterials
import deleteDuplicateTextures
import getComponentShader
import maya.cmds as cmds
import maya.mel as mel

I3DUtils.reloadModule(deleteDuplicateMaterials)
I3DUtils.reloadModule(deleteDuplicateTextures)
I3DUtils.reloadModule(getComponentShader)

class MaterialTools:
    def __init__(self):
        self.name = "Material-Tools"
        self.page = "Tools"
        self.prio = 4

        self.shelfCommand = "import I3DUtils; import MaterialTools; I3DUtils.reloadModule(MaterialTools); plugin = MaterialTools.MaterialTools(); plugin.%s(); del plugin;"

        self.removeDuplicateMaterialsInfo = {"name": "Remove Duplicate Materials",
                                             "category": self.name,
                                             "annotation": "Removes duplicate materials",
                                             "button_function": self.executeRemoveDuplicateMaterials,
                                             "shelf_label": "RmDpMat",
                                             "shelf_command": self.shelfCommand % "executeRemoveDuplicateMaterials"}

        self.removeDuplicateTexturesInfo = {"name": "Remove Duplicate Textures",
                                            "category": self.name,
                                            "annotation": "Removes duplicate textures",
                                            "button_function": self.executeRemoveDuplicateTextures,
                                            "shelf_label": "RmDpTex",
                                            "shelf_command": self.shelfCommand % "executeRemoveDuplicateTextures"}

        self.renameMaterialsInfo = {"name": "Rename Materials",
                                    "category": self.name,
                                    "annotation": "Renames materials based on GIANTS guidelines",
                                    "button_function": self.executeRenameMaterials,
                                    "shelf_label": "RenMats",
                                    "shelf_command": self.shelfCommand % "executeRenameMaterials"}

        self.renameTexturesInfo = {"name": "Rename Textures",
                                    "category": self.name,
                                    "annotation": "Renames only textures based on GIANTS guidelines",
                                    "button_function": self.executeRenameTextures,
                                    "shelf_label": "RenTexs",
                                    "shelf_command": self.shelfCommand % "executeRenameTextures"}

        self.getShaderComponentInfo = {"name": "Get Component Shader",
                                       "category": self.name,
                                       "annotation": "Gets the component shader",
                                       "button_function": self.executeGetShaderComponent,
                                       "shelf_label": "GetComSha",
                                       "shelf_command": self.shelfCommand % "executeGetShaderComponent"}

        self.createMirrorMaterialInfo = {"name": "Create Mirror Material",
                                         "category": self.name,
                                         "annotation": "Creates a mirror material",
                                         "button_function": self.executeCreateMirrorMaterial,
                                         "shelf_label": "MirrMat",
                                         "shelf_command": self.shelfCommand % "executeCreateMirrorMaterial"}

        self.selectMaterialFromSelection = {"name": "Select Material from selection",
                                         "category": self.name,
                                         "annotation": "Select material from polygon",
                                         "button_function": self.executeSelectMaterialFromSelection,
                                         "shelf_label": "SelFrom",
                                         "shelf_command": self.shelfCommand % "executeSelectMaterialFromSelection"}

    def getToolsButtons(self):
        return [self.removeDuplicateMaterialsInfo, self.removeDuplicateTexturesInfo,
                self.renameMaterialsInfo, self.renameTexturesInfo, self.getShaderComponentInfo,
                self.createMirrorMaterialInfo, self.selectMaterialFromSelection]

    def getShelfScripts(self):
        return [self.removeDuplicateMaterialsInfo, self.removeDuplicateTexturesInfo,
                self.renameMaterialsInfo, self.renameTexturesInfo, self.getShaderComponentInfo,
                self.createMirrorMaterialInfo, self.selectMaterialFromSelection]

    def executeRemoveDuplicateMaterials(self, *args):
        deleteDuplicateMaterials.duplicateMaterials("full")

    def executeRemoveDuplicateTextures(self, *args):
        deleteDuplicateTextures.duplicateTextures()

    def executeRenameMaterials(self, *args):
        ''' renames all materials to have a unique name '''

        def getTextureName(material, attribute, allowShared=False, allowDefault=False):
            if cmds.objExists(material + "." + attribute):
                textures = cmds.ls(cmds.listConnections(material + "." + attribute), tex=True)

                for texture in textures:
                    if cmds.nodeType(texture) == "bump2d":
                        textures = cmds.listConnections(textures, type="file")
                        break

                if textures is not None and len(textures) > 0:
                    filename = cmds.getAttr(textures[0] + ".fileTextureName")
                    if ("data/shared" not in filename and "data\\shared" not in filename) or allowShared:
                        if ("default" not in filename and "white" not in filename) or allowDefault:
                            name = filename.split("\\")[-1].split("/")[-1].split(".")[0].split("_")[0]
                            return name

        materialRenameData = []

        materials = cmds.ls(materials=True)
        for material in materials:
            if "lambert1" in material or "standardSurface1" in material or "particleCloud1" in material:
                continue

            if cmds.nodeType(material) == "GLSLShader":
                baseName = getTextureName(material, "diffuseMap", allowDefault=True)

                if baseName is None:
                    baseName = getTextureName(material, "normalMap", allowDefault=True)

                if baseName is None:
                    baseName = getTextureName(material, "specularMap", allowDefault=True)

                if baseName is None:
                    baseName = getTextureName(material, "diffuseMap", allowShared=True, allowDefault=False)

                if baseName is None:
                    baseName = getTextureName(material, "normalMap", allowShared=True, allowDefault=False)

                if baseName is None:
                    baseName = getTextureName(material, "specularMap", allowShared=True, allowDefault=False)

                if baseName is None:
                    baseName = getTextureName(material, "diffuseMap", allowShared=True, allowDefault=True)

                if baseName is None:
                    baseName = getTextureName(material, "normalMap", allowShared=True, allowDefault=True)

                if baseName is None:
                    baseName = getTextureName(material, "specularMap", allowShared=True, allowDefault=True)
            else:
                baseName = getTextureName(material, "color", allowDefault=True)

                if baseName is None:
                    baseName = getTextureName(material, "normal", allowDefault=True)

                if baseName is None:
                    baseName = getTextureName(material, "specular", allowDefault=True)

                if baseName is None:
                    baseName = getTextureName(material, "color", allowShared=True, allowDefault=False)

                if baseName is None:
                    baseName = getTextureName(material, "normal", allowShared=True, allowDefault=False)

                if baseName is None:
                    baseName = getTextureName(material, "specular", allowShared=True, allowDefault=False)

                if baseName is None:
                    baseName = getTextureName(material, "color", allowShared=True, allowDefault=True)

                if baseName is None:
                    baseName = getTextureName(material, "normal", allowShared=True, allowDefault=True)

                if baseName is None:
                    baseName = getTextureName(material, "specular", allowShared=True, allowDefault=True)

            if baseName is None:
                baseName = material.split("_")[0]

            requiredAdditionals = []
            optionalAdditionals = []

            trackArray = getTextureName(material, "customTexture_trackArray", allowShared=True, allowDefault=True)
            if trackArray is not None:
                requiredAdditionals.append(trackArray)

            loadAdditionals = True
            if cmds.objExists(material + ".slotName"):
                slotName = cmds.getAttr(material + ".slotName")
                if slotName != "":
                    if baseName.lower() not in slotName.lower():
                        baseName = baseName + "_" + slotName
                    else:
                        baseName = slotName

                    loadAdditionals = False

            if loadAdditionals:
                technique = "opaque"
                if cmds.nodeType(material) == "GLSLShader":
                    materialTemplateName = self.__getAttributeValue(material, "customParameterTemplate_brandColor_material", None)
                    if materialTemplateName is not None:
                        requiredAdditionals.append(materialTemplateName)

                    brandColorName = self.__getAttributeValue(material, "customParameterTemplate_brandColor_brandColor", None)
                    if brandColorName is None:
                        brandColorName = self.__getAttributeValue(material, "customParameter_template_colorScale", None)

                    if brandColorName is not None:
                        requiredAdditionals.append(brandColorName.split(" ")[0])

                    technique = cmds.getAttr(material + ".technique")
                else:
                    if cmds.objExists(material + ".translucence"):
                        if cmds.getAttr(material + ".translucence") > 0:
                            technique = "alphaBlended"

                optionalAdditionals.append(technique)

            materialData = {}
            materialData["material"] = material
            materialData["baseName"] = baseName
            materialData["requiredAdditionals"] = requiredAdditionals
            materialData["optionalAdditionals"] = optionalAdditionals

            materialData["name"] = baseName
            for additional in requiredAdditionals:
                materialData["name"] += "_" + additional

            materialRenameData.append(materialData)

        for materialData in materialRenameData:
            for materialData2 in materialRenameData:
                if materialData2 != materialData:
                    if materialData["name"] == materialData2["name"]:
                        for i in range(0, len(materialData["optionalAdditionals"])):
                            if materialData["optionalAdditionals"][i] != materialData2["optionalAdditionals"][i]:
                                materialData["name"] += "_" + materialData["optionalAdditionals"][i]
                                materialData2["name"] += "_" + materialData2["optionalAdditionals"][i]
                                materialData["optionalAdditionals"].pop(i)
                                materialData2["optionalAdditionals"].pop(i)
                                break

        indexByName = {}
        for materialData in materialRenameData:
            for materialData2 in materialRenameData:
                if materialData2 != materialData:
                    if materialData["name"] == materialData2["name"]:
                        if materialData["name"] not in indexByName:
                            indexByName[materialData["name"]] = 0

                        indexByName[materialData["name"]] += 1
                        materialData["renameIndex"] = indexByName[materialData["name"]]
                        break

        for materialData in materialRenameData:
            if "renameIndex" in materialData:
                materialData["name"] += "_%02d" % materialData["renameIndex"]

            if materialData["name"][-4:] != "_mat":
                materialData["name"] += "_mat"

        # do two passes in case we rename a material to a already existing name which is renamed in a later step
        for i in range(0, 2):
            for materialData in materialRenameData:
                if materialData["material"] != materialData["name"]:
                    try:
                        newName = cmds.rename(materialData["material"], materialData["name"])
                        print("Renamed material '%s' to '%s'" % (materialData["material"], newName))
                        materialData["material"] = newName
                    except:
                        print("Failed to rename '%s'" % materialData["material"])
                        pass

        materials = cmds.ls(materials=True)
        for material in materials:
            if "lambert1" in material or "standardSurface1" in material or "particleCloud1" in material:
                continue

            materialName = material
            if materialName[-4:] == "_mat":
                materialName = materialName[:-4]

            connections = cmds.listConnections(material)
            for connection in connections:
                if cmds.objExists(connection):
                    try:
                        if cmds.objectType(connection) == "shadingEngine":
                            if connection != materialName + "_s":
                                cmds.lockNode(connection, lock=False)
                                cmds.rename(connection, materialName + "_s")
                                print("Renamed shading engine '%s' to '%s'" % (connection, materialName + "_s"))
                        elif cmds.objectType(connection) == "materialInfo":
                            if connection != materialName + "_MatInfo":
                                cmds.lockNode(connection, lock=False)
                                cmds.rename(connection, materialName + "_MatInfo")
                                print("Renamed material info '%s' to '%s'" % (connection, materialName + "_MatInfo"))
                    except:
                        print("Failed to rename '%s'" % connection)
                        pass

    def executeRenameTextures(self, *args):
        ''' renames all textures to have a unique name '''

        textures = cmds.ls(fl=True, textures=True)
        for texture in textures:
            filename = cmds.getAttr(texture + ".fileTextureName")

            textureNameOnly = filename.split("\\")[-1].split("/")[-1].split(".")[0]

            connections = cmds.listConnections(texture, type="place2dTexture")
            if connections is not None:
                for connection in connections:
                    if cmds.objExists(connection):
                        if connection != textureNameOnly + "_place2dTexture":
                            try:
                                cmds.lockNode(connection, lock=False)
                                cmds.rename(connection, textureNameOnly + "_place2dTexture")
                                print("Renamed place2dTexture '%s' to '%s'" % (connection, textureNameOnly + "_place2dTexture"))
                            except:
                                print("Failed to rename '%s'" % connection)
                                pass

            connections = cmds.listConnections(texture, type="bump2d")
            if connections is not None:
                for connection in connections:
                    if cmds.objExists(connection):
                        if connection != textureNameOnly + "_bump2d":
                            try:
                                cmds.lockNode(connection, lock=False)
                                cmds.rename(connection, textureNameOnly + "_bump2d")
                                print("Renamed bump2d '%s' to '%s'" % (connection, textureNameOnly + "_bump2d"))
                            except:
                                print("Failed to rename '%s'" % connection)
                                pass

            newName = filename.split("\\")[-1].split("/")[-1].replace(".", "_")
            if texture != newName:
                try:
                    cmds.lockNode(texture, lock=False)
                    cmds.rename(texture, newName)
                    print("Renamed texture '%s' to '%s'" % (texture, newName))
                except:
                    print("Failed to rename '%s'" % texture)
                    pass

    def executeGetShaderComponent(self, *args):
        getComponentShader.getComponentShader()

    def executeCreateMirrorMaterial(self, *args):
        objects = cmds.ls(materials=True)
        for object in objects:
            if "mirror_mat" in object:
                cmds.warning("Mirror Material already created!")
                return

        material = cmds.shadingNode("phong", asShader=1, name="mirror_mat")
        cmds.setAttr(material + ".rfi", 10)
        cmds.setAttr(material + ".dc", 1)
        cmds.setAttr(material + ".c", 0, 0, 0)
        cmds.setAttr(material + ".tcf", 0)
        cmds.setAttr(material + ".trsd", 0)
        cmds.setAttr(material + ".sc", 0, 1, 1)
        cmds.setAttr(material + ".rfl", 1)
        cmds.setAttr(material + ".cp", 100)

        cmds.addAttr(material, shortName="customShader", longName="customShader", niceName="customShader", dataType="string")
        cmds.setAttr(material + ".customShader", "$data/shaders/mirrorShader.xml", type="string")

    def executeSelectMaterialFromSelection(self, *args):
        m_mat = I3DUtils.getMaterialFromSelection()
        mel.eval("changeSelectMode -object;")
        cmds.selectMode( object = True )
        cmds.select( clear=True )
        cmds.select( m_mat )

    def __attributeExists(self, node, attribute):
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

    def __getAttributeValue(self, node, attribute, default):
        fullname = node + '.' + attribute
        if self.__attributeExists(node, attribute):
            return cmds.getAttr(fullname)
        return default

def getI3DExporterPlugin():
    return MaterialTools()

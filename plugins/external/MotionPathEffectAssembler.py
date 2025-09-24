#
# @author   Stefan Maurus
# @date     01/10/2020
# @version  1.0.0
#


from maya import cmds
from functools import partial
import os
import random
import math
import string
import I3DExporter
import I3DUtils
import XMLParser

WINDOW_ID = "motionPathEffectAssemblerUI"
WINDOW_ID_PROGESS_BAR = "motionPathEffectAssemblerProgressUI"

UI_WIDTH = 555
UI_HEIGHT = 590


class MotionPathEffectAssembler:
    """Motion Path Effect Assembler"""

    def __init__(self):
        self.projectDirectory = cmds.workspace(q=True, rd=True)

        self.scenePath = cmds.file(query=True, sceneName=True, shortName=False)
        binPath = self.scenePath[len(self.projectDirectory):].split("/")[0]
        self.gamePath = self.scenePath[:len(self.projectDirectory)] + binPath

        self.configXMLPath = self.scenePath.replace(".ma", ".xml")
        self.configXMLPathValid = True
        if not os.path.exists(self.configXMLPath):
            self.configXMLPath = "Not Found!"
            self.configXMLPathValid = False

        self.foliageFolderPath = self.gamePath + "/data/foliage"
        self.foliageFolderPathValid = True
        if not os.path.exists(self.foliageFolderPath):
            self.foliageFolderPath = "Not Found!"
            self.foliageFolderPathValid = False

        self.effects = []
        if self.configXMLPathValid:
            self.__loadEffectsFromXML(self.configXMLPath)

        self.__createUI()

    def __createUI(self):
        if cmds.window(WINDOW_ID, exists=True):
            cmds.deleteUI(WINDOW_ID)

        if cmds.window(WINDOW_ID_PROGESS_BAR, exists=True):
            cmds.deleteUI(WINDOW_ID_PROGESS_BAR)

        if cmds.windowPref(WINDOW_ID, exists=True):
            cmds.windowPref(WINDOW_ID, edit=True, widthHeight=(UI_WIDTH, UI_HEIGHT))

        cmds.window(WINDOW_ID, title="Motion Path Effect Assembler", widthHeight=(UI_WIDTH, UI_HEIGHT), sizeable=False)

        baseLayout = cmds.scrollLayout()

        # file settings #
        filesFrame = cmds.frameLayout(label='Files', cll=False, parent=baseLayout, w=550, mh=5, mw=5)

        filesGrid = cmds.gridLayout(numberOfColumns=1, cellWidthHeight=(550, 20), parent=filesFrame)

        configXMLRows = cmds.rowLayout(w=400, h=20, cw3=(170, 350, 50), nc=3, cl3=("right", "center", "left"), parent=filesGrid)
        cmds.text(label='<span style="font-size: 9pt; font-weight: bold;">Effect Configuration XML:</span>', width=170, align="right", parent=configXMLRows)
        self.configXMLField = cmds.textField(text=self.configXMLPath, width=350, ed=False, parent=configXMLRows)
        cmds.symbolButton(image='navButtonBrowse.xpm', command=self.__selectEffectConfig, annotation='Choose Effect Configuration File', parent=configXMLRows)

        foliageRows = cmds.rowLayout(w=400, h=20, cw3=(170, 350, 50), nc=3, cl3=("right", "center", "left"), parent=filesGrid)
        cmds.text(label='<span style="font-size: 9pt; font-weight: bold;">Foliage Source Folder:</span>', width=170, align="right", parent=foliageRows)
        self.foliageFolderField = cmds.textField(text=self.foliageFolderPath, width=350, ed=False, parent=foliageRows)
        cmds.symbolButton(image='navButtonBrowse.xpm', command=self.__selectFoliageFolder, annotation='Choose Foliage Source Folder', parent=foliageRows)

        # effects #
        self.effectWidths = [(1, 125), (2, 125), (3, 100), (4, 75), (5, 75)]
        self.effectColumnSpacing = [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5)]
        self.effectRowSpacing = [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5)]

        effectsFrame = cmds.frameLayout(label='Effects', cll=False, parent=baseLayout, w=550, mh=5, mw=5)

        # header #
        self.effectsGridHeader = cmds.rowColumnLayout(numberOfColumns=5, columnWidth=self.effectWidths, cs=self.effectColumnSpacing, rs=self.effectRowSpacing, parent=effectsFrame)

        cmds.text(label='<span style="font-size: 9pt; font-weight: bold;">Type</span>', width=125, align="center", parent=self.effectsGridHeader)
        cmds.text(label='<span style="font-size: 9pt; font-weight: bold;">Info</span>', width=125, align="center", parent=self.effectsGridHeader)
        cmds.text(label='<span style="font-size: 9pt; font-weight: bold;">Dimensions</span>', width=100, align="center", parent=self.effectsGridHeader)
        cmds.text(label='<span style="font-size: 9pt; font-weight: bold;">Update</span>', width=75, align="center", parent=self.effectsGridHeader)
        cmds.text(label='<span style="font-size: 9pt; font-weight: bold;">Generate</span>', width=75, align="center", parent=self.effectsGridHeader)

        cmds.separator(parent=effectsFrame)

        # main scroll #
        self.effectsScroll = cmds.scrollLayout(height=400, width=545, parent=effectsFrame)
        self.effectsGrid = cmds.rowColumnLayout(numberOfColumns=5, columnWidth=self.effectWidths, cs=self.effectColumnSpacing, rs=self.effectRowSpacing, parent=self.effectsScroll)

        cmds.separator(parent=effectsFrame)

        # footer #
        self.effectsGridFooter = cmds.rowColumnLayout(numberOfColumns=5, columnWidth=self.effectWidths, cs=self.effectColumnSpacing, rs=self.effectRowSpacing, parent=effectsFrame)

        cmds.text(label="", parent=self.effectsGridFooter)
        cmds.text(label="", parent=self.effectsGridFooter)
        cmds.text(label="", parent=self.effectsGridFooter)

        cmds.button(label="Update All", command=lambda x: self.__updateAll(), ann="Load shape data from foliage file of all effects", parent=self.effectsGridFooter)
        cmds.button(label="Generate All", command=lambda x: self.__generateAll(), ann="Generate and export all merged shapes", parent=self.effectsGridFooter)

        self.__generateEffectUI()

        cmds.showWindow()

    def __selectEffectConfig(self, _):
        files = cmds.fileDialog2(fileMode=1, fileFilter='XML File (*.xml)', dialogStyle=2, caption='Choose Effect Config XML', okCaption='Choose')
        if files is not None and len(files) > 0:
            file = files[0]
            if ".xml" in file and os.path.exists(file):
                self.configXMLPath = file
                self.configXMLPathValid = True
                cmds.textField(self.configXMLField, e=True, text=self.configXMLPath)
                self.__loadEffectsFromXML(self.configXMLPath)
                self.__generateEffectUI()

    def __selectFoliageFolder(self, _):
        files = cmds.fileDialog2(fileMode=3, fileFilter='', dialogStyle=2, caption='Choose Foliage Folder', okCaption='Choose')
        if files is not None and len(files) > 0:
            directory = files[0]
            if os.path.isdir(directory):
                self.foliageFolderPath = directory
                self.foliageFolderPathValid = True
                cmds.textField(self.foliageFolderField, e=True, text=self.foliageFolderPath)

    def __createProgressBar(self, steps):
        if cmds.window(WINDOW_ID_PROGESS_BAR, exists=True):
            cmds.deleteUI(WINDOW_ID_PROGESS_BAR)

        tlc = cmds.window(WINDOW_ID, q=True, topLeftCorner=True)
        tlc = (tlc[0] + (UI_HEIGHT-70) / 2, tlc[1] + (UI_WIDTH-300) / 2)  # middle of main ui

        if cmds.windowPref(WINDOW_ID_PROGESS_BAR, exists=True):
            cmds.windowPref(WINDOW_ID_PROGESS_BAR, edit=True, widthHeight=(300, 70))
            cmds.windowPref(WINDOW_ID_PROGESS_BAR, edit=True, topLeftCorner=tlc)

        cmds.window(WINDOW_ID_PROGESS_BAR, title="Progress", widthHeight=(300, 70), topLeftCorner=tlc)

        layout = cmds.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 287)], cs=[(1, 5)], rs=[(1, 5)], parent=WINDOW_ID_PROGESS_BAR)

        cmds.text(label="", parent=layout)
        self.progressBarText = cmds.text(label="", parent=layout)
        self.progressBar = cmds.progressBar(maxValue=steps, parent=layout)

        cmds.showWindow(WINDOW_ID_PROGESS_BAR)

    def __updateProgressBar(self, steps, text):
        if self.progressBar is not None:
            if steps > 0:
                cmds.progressBar(self.progressBar, edit=True, step=steps)

            cmds.text(self.progressBarText, label=text, edit=True)

    def __removeProgressBar(self):
        if self.progressBar is not None:
            cmds.progressBar(self.progressBar, edit=True, endProgress=True)
            self.progressBar = None

        if cmds.window(WINDOW_ID_PROGESS_BAR, exists=True):
            cmds.deleteUI(WINDOW_ID_PROGESS_BAR)

    def __updateAll(self):
        for effect in self.effects:
            self.__updateEffect(effect)

    def __generateAll(self):
        numMeshes = 0
        for effect in self.effects:
            numMeshes = numMeshes + self.__getMeshesToGenerate(effect)

        self.__createProgressBar(numMeshes)

        for effect in self.effects:
            self.__generateEffectMesh(effect)

        self.__removeProgressBar()

    def __update(self, index, _):
        effect = self.effects[index]
        if effect is not None:
            self.__updateEffect(effect)

    def __generate(self, index, _):
        effect = self.effects[index]
        if effect is not None:
            self.__createProgressBar(self.__getMeshesToGenerate(effect))

            self.__generateEffectMesh(effect)

            self.__removeProgressBar()

    def __generateEffectUI(self):
        oldElements = cmds.rowColumnLayout(self.effectsGrid, q=True, ca=True)
        if oldElements is not None:
            for elem in oldElements:
                cmds.deleteUI(elem)

        index = 0
        for effect in self.effects:
            type = "Unknown"
            if effect["effectType"] is not None:
                type = effect["effectType"]
            cmds.text(label=type, width=125, align="center", parent=self.effectsGrid)

            info = "Unknown"
            if effect["fruitTypes"] is not None:
                info = "Fruit: " + effect["fruitTypes"]

                if effect["growthStates"] is not None:
                    info = info + " (Stage: " + effect["growthStates"] + ")"

            if effect["fillTypes"] is not None:
                info = "FillType: " + effect["fillTypes"]

            cmds.scrollField(text=info, wordWrap=True, editable=False, font="plainLabelFont", enableBackground=False, height=50, width=125, parent=self.effectsGrid)

            dimensions = ""
            numDimensions = 0
            for effectMesh in effect["effectMeshes"]:
                if numDimensions > 0:
                    dimensions = dimensions + "\n"
                dimensions = dimensions + "%d x %d skip %d" % (effectMesh["rowLength"], effectMesh["numRows"], effectMesh["skipPositions"])
                numDimensions = numDimensions + 1

            cmds.scrollField(text=dimensions, wordWrap=True, editable=False, font="plainLabelFont", enableBackground=False, height=numDimensions * 15, width=100, parent=self.effectsGrid)

            if effect["useFoliage"] is not None and effect["useFoliage"] != "":
                cmds.button(label="Update", height=25, command=partial(self.__update, index), ann="Load shape data from foliage file", parent=self.effectsGrid)
            else:
                cmds.text(label="", parent=self.effectsGrid)

            cmds.button(label="Generate", height=25, command=partial(self.__generate, index), ann="Generate and export merged shapes", parent=self.effectsGrid)

            index = index + 1

    def __loadEffectsFromXML(self, xmlFilename):
        self.effects = []
        xmlFile = XMLParser.loadXMLFile(xmlFilename)
        numMotionPathEffects = XMLParser.getNumberOfElements(xmlFile, "motionPathEffects.motionPathEffect")
        for i in range(0, numMotionPathEffects):
            effectKey = "motionPathEffects.motionPathEffect(%d)" % (i)
            effect = {}

            effect["index"] = i + 1
            effect["filename"] = XMLParser.getXMLValue(xmlFile, effectKey + "#filename")
            effect["effectType"] = XMLParser.getXMLValue(xmlFile, effectKey + "#effectType")

            effect["fruitTypes"] = XMLParser.getXMLValue(xmlFile, effectKey + ".typeDefinition#fruitTypes")
            effect["growthStates"] = XMLParser.getXMLValue(xmlFile, effectKey + ".typeDefinition#growthStates")
            effect["fillTypes"] = XMLParser.getXMLValue(xmlFile, effectKey + ".typeDefinition#fillTypes")

            effect["rootNode"] = XMLParser.getXMLValue(xmlFile, effectKey + ".effectGeneration#rootNode")
            if effect["rootNode"] is not None:
                effect["minRot"] = XMLParser.getVectorNFromXML(xmlFile, effectKey + ".effectGeneration#minRot")
                effect["maxRot"] = XMLParser.getVectorNFromXML(xmlFile, effectKey + ".effectGeneration#maxRot")
                effect["minScale"] = XMLParser.getVectorNFromXML(xmlFile, effectKey + ".effectGeneration#minScale")
                effect["maxScale"] = XMLParser.getVectorNFromXML(xmlFile, effectKey + ".effectGeneration#maxScale")

                effect["useFoliage"] = XMLParser.getXMLValue(xmlFile, effectKey + ".effectGeneration#useFoliage")
                effect["useFoliageStage"] = XMLParser.getXMLInt(xmlFile, effectKey + ".effectGeneration#useFoliageStage")
                effect["useFoliageLOD"] = XMLParser.getXMLInt(xmlFile, effectKey + ".effectGeneration#useFoliageLOD")

                effect["effectMeshes"] = []

                numEffectMeshes = XMLParser.getNumberOfElements(xmlFile, effectKey + ".effectMeshes.effectMesh")
                for j in range(0, numEffectMeshes):
                    meshKey = effectKey + ".effectMeshes.effectMesh(%d)" % (j)

                    effectMesh = {}

                    effectMesh["index"] = j + 1
                    effectMesh["node"] = XMLParser.getXMLValue(xmlFile, meshKey + "#node")
                    effectMesh["sourceNode"] = XMLParser.getXMLValue(xmlFile, meshKey + "#sourceNode")
                    effectMesh["rowLength"] = XMLParser.getXMLInt(xmlFile, meshKey + "#rowLength") or 0
                    effectMesh["numRows"] = XMLParser.getXMLInt(xmlFile, meshKey + "#numRows") or 0
                    effectMesh["skipPositions"] = XMLParser.getXMLInt(xmlFile, meshKey + "#skipPositions") or 0
                    effectMesh["numVariations"] = XMLParser.getXMLInt(xmlFile, meshKey + "#numVariations") or 1
                    effectMesh["boundingBox"] = XMLParser.getVectorNFromXML(xmlFile, meshKey + "#boundingBox")
                    effectMesh["boundingBoxCenter"] = XMLParser.getVectorNFromXML(xmlFile, meshKey + "#boundingBoxCenter")

                    if effectMesh["numVariations"] is None:
                        effectMesh["numVariations"] = 1

                    effectMesh["lods"] = []

                    numLods = XMLParser.getNumberOfElements(xmlFile, meshKey + ".lod")
                    for li in range(0, numLods):
                        lodKey = meshKey + ".lod(%d)" % (li)

                        lod = {}
                        lod["sourceNode"] = XMLParser.getXMLValue(xmlFile, lodKey + "#sourceNode")
                        lod["distance"] = XMLParser.getXMLInt(xmlFile, lodKey + "#distance")
                        lod["skipPositions"] = XMLParser.getXMLInt(xmlFile, lodKey + "#skipPositions")

                        effectMesh["lods"].append(lod)

                    effect["effectMeshes"].append(effectMesh)

                effect["materialRootNode"] = XMLParser.getXMLValue(xmlFile, effectKey + ".effectMaterials#rootNode")

                self.effects.append(effect)

        return self.effects

    def __updateEffect(self, effect):
        if self.foliageFolderPathValid:
            if effect["useFoliage"] is not None:
                rootNodePath = effect["rootNode"]

                objects = cmds.ls(assemblies=True)
                rootNodes = []
                for object in objects:
                    if not I3DUtils.isCamera(object):
                        rootNodes.append(object)

                rootNode = self.__getObjectByIndex(rootNodes, rootNodePath)
                if rootNode is not None:
                    availableMeshes = cmds.listRelatives(rootNode, c=True, f=True)
                    if availableMeshes is not None:
                        for mesh in availableMeshes:
                            cmds.delete(mesh)

                    self.__loadFoliageMesh(rootNode, self.foliageFolderPath, effect["useFoliage"], effect["useFoliageStage"], effect["useFoliageLOD"])

    def __loadFoliageMesh(self, linkNode, foliageBasePath, foliageName, growthState, lodIndex):
        foliageNameLower = foliageName.lower()

        foliagePath = foliageBasePath + "/" + foliageNameLower + "/" + foliageNameLower

        foliageXMLPath = foliagePath+".xml"
        foliageMAPath = foliagePath+".ma"

        if os.path.exists(foliageXMLPath) and os.path.exists(foliageMAPath):
            xmlFile = XMLParser.loadXMLFile(foliageXMLPath)
            numFoliageStates = XMLParser.getNumberOfElements(xmlFile, "foliageType.foliageLayer.foliageState")
            if numFoliageStates >= growthState:
                effectKey = "foliageType.foliageLayer.foliageState(%d)" % (growthState)

                numShapes = XMLParser.getNumberOfElements(xmlFile, effectKey + ".foliageShape")
                for i in range(0, numShapes):
                    foliageNode = XMLParser.getXMLValue(xmlFile, effectKey + ".foliageShape(%d).foliageLod(%s)#blockShape" % (i, lodIndex))
                    if foliageNode is not None:
                        self.__loadSingleFoliageMesh(linkNode, foliageMAPath, foliageNode, foliageNameLower)

    def __loadSingleFoliageMesh(self, linkNode, foliageMAPath, indexPath, foliageNameLower):
        randomKey = "".join(random.choice(string.ascii_lowercase) for i in range(0, 16))
        cmds.file(foliageMAPath, i=True, namespace=randomKey)

        foliageMesh = None

        objects = cmds.ls(assemblies=True)
        rootObjects = []
        for object in objects:
            if randomKey in object:
                rootObjects.append(object)

        foliageMesh = self.__getObjectByIndex(rootObjects, indexPath)
        if foliageMesh is not None:
            materials = cmds.ls(fl=True, materials=True)
            for material in materials:
                if I3DExporter.I3DAttributeExists(material, "customShader"):
                    customShader = cmds.getAttr("%s.customShader" % material)
                    if "fruitGrowthFoliageShader" in customShader:
                        customShader = customShader.replace("fruitGrowthFoliageShader", "motionPathShader")
                        I3DExporter.I3DSaveAttributeString(material, "customShader", customShader)

                        # replace the alpha map path by game relative path if it's just a local file name
                        if I3DExporter.I3DAttributeExists(material, "customTexture_alphaMap"):
                            alphaMapPath = cmds.getAttr("%s.customTexture_alphaMap" % material)
                            if "$data" not in alphaMapPath:
                                alphaMapPath = "$data/foliage/" + foliageNameLower + "/" + alphaMapPath
                                I3DExporter.I3DSaveAttributeString(material, "customTexture_alphaMap", alphaMapPath)

                                if I3DExporter.I3DAttributeExists(material, "customParameter_sickness"):
                                    cmds.deleteAttr(material + ".customParameter_sickness")
                                    if I3DExporter.I3DAttributeExists(material, "customParameter_windScale"):
                                        cmds.deleteAttr(material + ".customParameter_windScale")
                                        if I3DExporter.I3DAttributeExists(material, "customTexture_sicknessMask"):
                                            cmds.deleteAttr(material + ".customTexture_sicknessMask")

                                            I3DExporter.I3DSaveAttributeString(material, "customShaderVariation", "scaleByTexture_verticalOffsetCut_alphaMap")

            newMesh = cmds.duplicate(foliageMesh, rc=True)
            cmds.parent(newMesh, linkNode)

        objects = cmds.ls(assemblies=True)
        for object in objects:
            if randomKey in object:
                cmds.delete(object)

        cmds.namespace(mv=(randomKey, ":"), f=True)
        cmds.namespace(rm=randomKey)

    def __getObjectByIndex(self, rootNodes, indexPath):
        if indexPath is None or rootNodes is None:
            print("Could not find given index!")
            return None

        def getValidChilds(parent):
            valid = []
            if parent is not None:
                childs = cmds.listRelatives(parent, c=True, f=True)
                if childs is not None:
                    for child in childs:
                        if cmds.nodeType(child) != "mesh":
                            valid.append(child)
            return valid

        childs = []

        if ">" in indexPath:
            parts = indexPath.split(">")
            if len(parts) == 2:
                childs.append(parts[0])
                indexPath = parts[1]

        for child in indexPath.split("|"):
            if ">" not in child:
                childs.append(child)

        currentObject = rootNodes[int(childs[0])]

        childs = childs[1:len(childs)]

        foundObj = True
        for child in childs:
            if child != '':
                currentChilds = getValidChilds(currentObject)
                if int(child) >= len(currentChilds):
                    print("Could not find given index '"+indexPath+"'!")
                    foundObj = False
                    if len(currentChilds) > 0:
                        currentObject = currentChilds[len(currentChilds)-1]
                    break
                currentObject = currentChilds[int(child)]

        if foundObj:
            return currentObject
        else:
            return None

    def __getMeshesToGenerate(self, effect):
        numMeshes = 0
        for mesh in effect["effectMeshes"]:
            numLods = len(mesh["lods"]) + 1
            numMeshes = numMeshes + mesh["numRows"] * mesh["rowLength"] * mesh["numVariations"] * numLods
            numMeshes = numMeshes + 20 * mesh["numVariations"] * numLods  # bounding boxes
            numMeshes = numMeshes + 20 + 20 + 20

        return numMeshes

    def __createBoundingVolume(self, parent, mesh, meshName):
        if mesh["boundingBox"] is not None and len(mesh["boundingBox"]) == 3:
            boundingObject = cmds.polyCube(w=1, h=1, d=1)[0]
            cmds.xform(boundingObject, s=mesh["boundingBox"])
            cmds.makeIdentity(boundingObject, apply=True, s=True, n=False)

            # set I3D attributes
            I3DExporter.I3DRemoveAttributes(boundingObject)
            I3DExporter.I3DSaveAttributeBool(boundingObject, "i3D_static", False)
            I3DExporter.I3DSaveAttributeBool(boundingObject, "i3D_collision", False)

            I3DExporter.I3DSaveAttributeString(boundingObject, "i3D_boundingVolume", meshName)

            boundingObjectName = "boundingVolume_%s" % meshName

            cmds.parent(boundingObject, parent)

            if mesh["boundingBoxCenter"] is not None:
                cmds.xform(boundingObject, t=mesh["boundingBoxCenter"])

            cmds.rename(boundingObject, boundingObjectName)

    def __generateEffectGroupVariation(self, rootNodes, parent, rootName, effect, mesh, availableMeshes, variationIndex):

        if len(mesh["lods"]) == 0:
            self.__generateRandomEffectGroup(rootNodes, parent, rootName, effect, mesh, availableMeshes, variationIndex)
        else:
            meshName = "%s_nr%d_rl%d_v%d_LOD" % (rootName, mesh["numRows"], mesh["rowLength"], variationIndex + 1)
            meshRoot = cmds.group(em=True, name=meshName)

            meshRoot = cmds.parent(meshRoot, parent)
            I3DExporter.I3DSaveAttributeInt(meshRoot[0], "i3D_lod", 1)

            self.__generateRandomEffectGroup(rootNodes, meshRoot, rootName, effect, mesh, availableMeshes, variationIndex, lodIndex=0)
            for i in range(0, len(mesh["lods"])):
                lod = mesh["lods"][i]
                I3DExporter.I3DSaveAttributeInt(meshRoot[0], "i3D_lod%d" % (i+1), lod["distance"])
                self.__generateRandomEffectGroup(rootNodes, meshRoot, rootName, effect, mesh, availableMeshes, variationIndex, lod=lod, lodIndex=(i + 1))

    def __generateRandomEffectGroup(self, rootNodes, parent, rootName, effect, mesh, availableMeshes, variationIndex, lod=None, lodIndex=None):
        meshName = "%s_nr%d_rl%d_v%d" % (rootName, mesh["numRows"], mesh["rowLength"], variationIndex + 1)
        lodStr = ""
        if lodIndex is not None:
            meshName = "%s_LOD%d" % (meshName, lodIndex)
            lodStr = ", LOD %d" % (lodIndex + 1)

        meshRoot = cmds.group(em=True, name=meshName)
        I3DExporter.I3DSaveAttributeInt(meshRoot, "i3D_mergeChildren", 1)

        meshRoot = cmds.parent(meshRoot, parent)

        skipPositions = mesh["skipPositions"]
        if lod is not None:
            skipPositions = lod["skipPositions"]

            rootNode = self.__getObjectByIndex(rootNodes, lod["sourceNode"])
            if rootNode is not None:
                lodAvailableMeshes = cmds.listRelatives(rootNode, c=True, f=True)
                if lodAvailableMeshes is not None:
                    availableMeshes = lodAvailableMeshes

        usedMeshes = {}
        for row in range(0, mesh["numRows"]):
            skipOffset = math.floor(random.uniform(-skipPositions, skipPositions))
            for column in range(0, mesh["rowLength"]):
                if (column + skipOffset) % (skipPositions + 1) == 0:
                    randomIndex = random.uniform(0, len(availableMeshes) - 1)
                    randomIndex = int(randomIndex)

                    # try to randomly use all meshes and when all are used we start to use all again
                    attempts = 0
                    while randomIndex in usedMeshes:
                        randomIndex = randomIndex + 1
                        if randomIndex >= len(availableMeshes):
                            randomIndex = 0

                        attempts = attempts + 1
                        if attempts > len(availableMeshes):
                            usedMeshes = {}
                            break

                    if randomIndex not in usedMeshes:
                        usedMeshes[randomIndex] = 1

                    newMesh = cmds.duplicate(availableMeshes[randomIndex], rc=True)

                    if effect["minRot"] is not None and effect["maxRot"] is not None:
                        if len(effect["minRot"]) == 3 and len(effect["maxRot"]) == 3:
                            rot = (random.uniform(effect["minRot"][0], effect["maxRot"][0]),
                                   random.uniform(effect["minRot"][1], effect["maxRot"][1]),
                                   random.uniform(effect["minRot"][2], effect["maxRot"][2]))

                            cmds.xform(newMesh, a=True, ro=rot)

                    if effect["minScale"] is not None and effect["maxScale"] is not None:
                        if len(effect["minScale"]) == 3 and len(effect["maxScale"]) == 3:
                            scale = (random.uniform(effect["minScale"][0], effect["maxScale"][0]),
                                     random.uniform(effect["minScale"][1], effect["maxScale"][1]),
                                     random.uniform(effect["minScale"][2], effect["maxScale"][2]))

                            cmds.xform(newMesh, a=True, s=scale)

                    cmds.makeIdentity(newMesh, apply=True, r=True, s=True, n=False)

                    cmds.parent(newMesh, meshRoot)
                    cmds.rename(newMesh, "row%d_object%d" % (row + 1, column + 1))

                    self.__updateProgressBar(1, "Building Mesh (Type %d, Mesh %d, Var %d%s)..." % (effect["index"], mesh["index"], variationIndex + 1, lodStr))
                else:
                    spacer = cmds.group(em=True, name="row%d_object%d" % (row + 1, column + 1))
                    cmds.parent(spacer, meshRoot)

                    self.__updateProgressBar(1, "Building Mesh (Type %d, Mesh %d, Var %d%s)..." % (effect["index"], mesh["index"], variationIndex + 1, lodStr))

        self.__updateProgressBar(20, "Create Bounding Boxes...")
        self.__createBoundingVolume(parent, mesh, meshName)

    def __generateEffectMesh(self, effect):
        rootNodePath = effect["rootNode"]

        objects = cmds.ls(assemblies=True)
        rootNodes = []
        for object in objects:
            if not I3DUtils.isCamera(object):
                rootNodes.append(object)

        rootNode = self.__getObjectByIndex(rootNodes, rootNodePath)
        if rootNode is not None:
            availableMeshes = cmds.listRelatives(rootNode, c=True, f=True)
            if availableMeshes is not None:
                rootName = "effects"
                effectMeshRootName = "effects_unknownMeshes"
                effectMaterialsRootName = "effects_unknownMaterials"

                rootParts = rootNode.split("|")
                if len(rootParts) >= 3:
                    rootName = rootParts[1] + "_" + rootParts[2]
                    effectMeshRootName = rootName + "_meshes"
                    effectMaterialsRootName = rootName + "_materials"

                fileRoot = cmds.group(em=True, name=rootName)
                effectMeshRoot = cmds.group(em=True, name=effectMeshRootName)
                effectMeshRoot = cmds.parent(effectMeshRoot, fileRoot)

                for mesh in effect["effectMeshes"]:
                    effectAvailableMeshes = availableMeshes

                    if mesh["sourceNode"] is not None:
                        customRoot = self.__getObjectByIndex(rootNodes, mesh["sourceNode"])
                        if customRoot is not None:
                            customAvailableMeshes = cmds.listRelatives(customRoot, c=True, f=True)
                            if customAvailableMeshes is not None:
                                effectAvailableMeshes = customAvailableMeshes

                    meshName = "%s_nr%d_rl%d" % (rootName, mesh["numRows"], mesh["rowLength"])

                    if mesh["numVariations"] == 1:
                        self.__generateEffectGroupVariation(rootNodes, effectMeshRoot, rootName, effect, mesh, effectAvailableMeshes, 0)
                    else:
                        meshRoot = cmds.group(em=True, name=meshName+"_root")
                        meshRoot = cmds.parent(meshRoot, effectMeshRoot)
                        for variationIndex in range(0, mesh["numVariations"]):
                            self.__generateEffectGroupVariation(rootNodes, meshRoot, rootName, effect, mesh, effectAvailableMeshes, variationIndex)

                self.__updateProgressBar(20, "Copy Materials...")
                cmds.refresh()

                # just copy materials over to new file
                if effect["materialRootNode"] is not None:
                    materialRootNode = self.__getObjectByIndex(rootNodes, effect["materialRootNode"])
                    if materialRootNode is not None:
                        newMaterialRoot = cmds.duplicate(materialRootNode, rr=True)
                        newMaterialRoot = cmds.parent(newMaterialRoot, fileRoot)
                        cmds.rename(newMaterialRoot, effectMaterialsRootName)

                cmds.select(fileRoot, hi=True)

                self.__updateProgressBar(20, "Exporting...")
                cmds.refresh()

                path = effect["filename"]
                path = path.replace("$data", self.gamePath + "/data")
                I3DExporter.I3DExportSaveAsDialog(True, False, path, skipValidation=True)

                self.__updateProgressBar(20, "Save Maya File...")
                cmds.refresh()

                try:
                    cmds.file(path.replace(".i3d", ".ma"), force=True, options="v = 0", type="mayaAscii", exportSelected=True)
                except:
                    cmds.warning("Failed to export effects")

                cmds.delete(fileRoot)

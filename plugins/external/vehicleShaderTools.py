#
#   SCRIPT     vehicleShaderTools.py
#   AUTHOR     Evgen Zaitsev
#
'''
WITH UI:
import vehicleShaderTools; vehicleShaderTools.showUI();

WITHOUT UI:
import vehicleShaderTools; vehicleShaderTools.convertFS22toFS25();
import vehicleShaderTools; vehicleShaderTools.duplicateSelectedMaterial();
import vehicleShaderTools; vehicleShaderTools.synhronizeMaterialTemplates();
'''
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import xml.etree.ElementTree as xml_ET
import math, os
import I3DUtils
import I3DExporter
import I3DMaterialTemplateWindow

UI_WIDTH = 400
UI_HEIGHT = 200
GUI_ID = "vehicleShaderToolsUI"
FS22IDs_colorMask = [ 'metalPaintedGray','plasticPaintedBlack','chrome','copperScratched','metalGalvanized','rubberBlack','metalPaintedOldGray','fabric1Bluish',
                    'silverScratched','silverBumpy','fabric2Gray','fabric3Gray','leather1Brown','leather2Brown','wood1Cedar','dirt',
                    'metalPaintedBlack','plasticPaintedGray','silverRough','brassScratched','reflectorWhite','reflectorRed','reflectorOrange','reflectorOrangeDaylight',
                    'plasticGearShiftGrayDark','leather3GrayDark','perforatedSynthetic1Black','glassClear01','glassSquare01','glassLine01','palladiumScratched','bronzeScratched',
                    'metalPaintedGraphiteBlack','halfMetalNoise1Black','plasticPaintedShinyGray','goldScratched','metalPaintedRoughGray','perforatedSynthetic2Black','fellGray','steelTreadPlate',
                    'halfMetalNoise2','fabric4Beige','wood2Oak','silverScratchedShiny','reflectorYellow','silverCircularBrushed','fabric5Dark','glassClear02',
                    'glassClear03','fabric6Bluish']
FS22IDs  = ['metalPainted','plasticPainted','chrome','silverScratched','metalGalvanized','rubber','metalPaintedOld','fabric1',
                   'silverScratched','silverBumpy','fabric2','fabric3','leather1','leather2','wood1','dirt',
                   'metalPainted','plasticPainted','silverRough','silverScratched','reflectorWhite','reflectorWhite','reflectorWhite','reflectorOrangeDaylight',
                   'plasticGearShift','leather3','perforatedSynthetic1','glassClear01','glassSquare01','glassLine01','silverScratched','silverScratched',
                   'metalPaintedGraphite','halfMetalNoise1','plasticPaintedShinyGray','silverScratched','metalPaintedRough','perforatedSynthetic2','fell','steelTreadPlate',
                   'halfMetalNoise2','fabric4','wood2','silverScratchedShiny','reflectorWhite','silverCircularBrushed','fabric5','glassClear02',
                   'glassClear03','fabric6']
FS22customShaderVariation = {
                     'secondUV_colorMask':'vmaskUV2',
                               'secondUV':'vmaskUV2',
                                  'Decal':'vmaskUV2',
                        'Decal_colorMask':'vmaskUV2',
                    'Decal_normalThirdUV':'vmaskUV2_normalUV3',
          'Decal_normalThirdUV_colorMask':'vmaskUV2_normalUV3',
                               'uvScroll':'uvTransform',
                     'uvScroll_colorMask':'uvTransform',
                               'uvRotate':'uvTransform',
                     'uvRotate_colorMask':'uvTransform',
                                'uvScale':'uvTransform',
                      'uvScale_colorMask':'uvTransform',
                         'Decal_uvScroll':'uvTransform_vmaskUV2',
                'tirePressureDeformation':'tirePressureDeformation',
       'tirePressureDeformation_secondUV':'tirePressureDeformation_vmaskUV2',
                       'motionPathRubber':'motionPathRubber',
    'motionPathRubber_secondUV_colorMask':'motionPathRubber_vmaskUV2',
                             'motionPath':'motionPath',
          'motionPath_secondUV_colorMask':'motionPath_vmaskUV2',
                    'vtxRotate_colorMask':'vtxRotate',
                              'vtxRotate':'vtxRotate',
                             'meshScroll':'meshScroll',
                   'meshScroll_colorMask':'meshScroll',
                                    'rim':'rim',
                          'rim_colorMask':'rim',
          'rim_numberOfStatics_colorMask':'rim_numberOfStatics',
                      'rimDual_colorMask':'rimDual_numberOfStatics',
                      'hubDual_colorMask':'hubDual',
                               'windBend':'windBend',
                     'windBend_colorMask':'windBend',
            'windBend_colorMask_vtxColor':'windBend_vtxColor',
                'windBend_vtxColor_Decal':'windBend_vtxColor_vmaskUV2',
      'windBend_vtxColor_Decal_colorMask':'windBend_vtxColor_vmaskUV2',
                      'shaking_colorMask':'shaking',
                'shaking_colorMask_Decal':'shaking_vmaskUV2',
                     'jiggling_colorMask':'jiggling',
               'cableTrayChain_colorMask':'cableTrayChain',
                        'localCatmullRom':'localCatmullRom_uvTransform',
              'localCatmullRom_colorMask':'localCatmullRom_uvTransform',
      'localCatmullRom_colorMask_uvScale':'localCatmullRom_uvTransform',
                    'reflector_colorMask':'reflector',
                    'backLight_colorMask':'backLight',
                            }
FS22customParameter = {
    'customParameter_morphPosition'        :'customParameter_morphPos' ,
    'customParameter_scrollPosition'       :'customParameter_scrollPos',
    'customParameter_blinkOffset'          :'customParameter_blinkMulti',
    'customParameter_offsetUV'             :'customParameter_offsetUV' ,
    'customParameter_uvCenterSize'         :'customParameter_uvCenterSize' ,
    'customParameter_uvScale'              :'customParameter_uvScale' ,
    'customParameter_lengthAndRadius'      :'customParameter_lengthAndRadius',
    'customParameter_widthAndDiam'         :'customParameter_widthAndDiam',
    'customParameter_connectorPos'         :'customParameter_connectorPos',
    'customParameter_numberOfStatics'      :'customParameter_numberOfStatics',
    'customParameter_connectorPosAndScale' :'customParameter_connectorPosAndScale',
    'customParameter_lengthAndDiameter'    :'customParameter_lengthAndDiameter',
    'customParameter_backLightScale'       :'customParameter_backLightScale',
    'customParameter_amplFreq'             :'customParameter_amplFreq',
    'customParameter_shaking'              :'customParameter_shaking',
    'customParameter_rotationAngle'        :'customParameter_rotationAngle',
    'customParameter_directionBend'        :'customParameter_directionBend',
    'customParameter_controlPointAndLength':'customParameter_controlPointAndLength',
                      }
FS22customTexture = { 'customTexture_mTrackArray': 'customTexture_trackArray' }
FS25shaderVariations = "base:vmaskUV2:vmaskUV2_normalUV3:uvTransform:uvTransform_vmaskUV2:tirePressureDeformation:tirePressureDeformation_vmaskUV2:motionPathRubber:motionPathRubber_vmaskUV2:motionPath:motionPath_vmaskUV2:vtxRotate:meshScroll:rim:rim_numberOfStatics:rimDual_numberOfStatics:hubDual:windBend:windBend_vtxColor:windBend_vtxColor_vmaskUV2:shaking:shaking_vmaskUV2:jiggling:cableTrayChain:localCatmullRom_uvTransform:reflector:backLight:staticLight"
FS25shaderVariationsList = FS25shaderVariations.split(':') # FS25shaderVariationsList.index('vmaskUV2')
FS25customParameter = {
      'customParameter_colorScale'         :{'type':'color3x1','enablename':  'customParameter_enable_colorScale'},
    'templateParameter_colorScale'         :{'type':'color3x1','enablename':'templateParameter_enable_colorScale'},
      'customParameter_smoothnessScale'    :{'type':'float', 'enablename':  'customParameter_enable_smoothnessScale'},
    'templateParameter_smoothnessScale'    :{'type':'float', 'enablename':'templateParameter_enable_smoothnessScale'},
      'customParameter_metalnessScale'     :{'type':'float', 'enablename':  'customParameter_enable_metalnessScale'},
    'templateParameter_metalnessScale'     :{'type':'float', 'enablename':'templateParameter_enable_metalnessScale'},
      'customParameter_clearCoatIntensity' :{'type':'float', 'enablename':  'customParameter_enable_clearCoatIntensity'},
    'templateParameter_clearCoatIntensity' :{'type':'float', 'enablename':'templateParameter_enable_clearCoatIntensity'},
      'customParameter_clearCoatSmoothness':{'type':'float', 'enablename':  'customParameter_enable_clearCoatSmoothness'},
    'templateParameter_clearCoatSmoothness':{'type':'float', 'enablename':'templateParameter_enable_clearCoatSmoothness'},
      'customParameter_porosity'           :{'type':'float', 'enablename':  'customParameter_enable_porosity'},
    'templateParameter_porosity'           :{'type':'float', 'enablename':'templateParameter_enable_porosity'},
        'customTexture_detailDiffuse'      :{'type':'texture','enablename':  'customParameter_enable_detailDiffuse'},
    'templateParameter_detailDiffuse'      :{'type':'texture','enablename':'templateParameter_enable_detailDiffuse'},
        'customTexture_detailNormal'       :{'type':'texture','enablename':  'customParameter_enable_detailNormal'},
    'templateParameter_detailNormal'       :{'type':'texture','enablename':'templateParameter_enable_detailNormal'},
        'customTexture_detailSpecular'     :{'type':'texture','enablename':  'customParameter_enable_detailSpecular'},
    'templateParameter_detailSpecular'     :{'type':'texture','enablename':'templateParameter_enable_detailSpecular'},
    'customTexture_trackArray'                  :{'type':'texture', 'enablename':'customParameter_enable_trackArray'},
    'customTexture_lightsIntensity'             :{'type':'texture', 'enablename':'customParameter_enable_lightsIntensity'},
    'customParameter_alphaBlendingClipThreshold':{'type':'float',   'enablename':'customParameter_enable_alphaBlendingClipThreshold'},
    'customParameter_offsetUV'                  :{'type':'float3x1','enablename':'customParameter_enable_offsetUV'},
    'customParameter_uvCenterSize'              :{'type':'float4x1','enablename':'customParameter_enable_uvCenterSize'},
    'customParameter_uvScale'                   :{'type':'float4x1','enablename':'customParameter_enable_uvScale'},
    'customParameter_morphPos'                  :{'type':'float4x1','enablename':'customParameter_enable_morphPos'},
    'customParameter_scrollPos'                 :{'type':'float4x1','enablename':'customParameter_enable_scrollPos'},
    'customParameter_lengthAndRadius'           :{'type':'float4x1','enablename':'customParameter_enable_lengthAndRadius'},
    'customParameter_rotationAngle'             :{'type':'float',   'enablename':'customParameter_enable_rotationAngle'},
    'customParameter_widthAndDiam'              :{'type':'float2x1','enablename':'customParameter_enable_widthAndDiam'},
    'customParameter_connectorPos'              :{'type':'float4x1','enablename':'customParameter_enable_connectorPos'},
    'customParameter_numberOfStatics'           :{'type':'float' ,  'enablename':'customParameter_enable_numberOfStatics'},
    'customParameter_connectorPosAndScale'      :{'type':'float3x1','enablename':'customParameter_enable_connectorPosAndScale'},
    'customParameter_directionBend'             :{'type':'float4x1','enablename':'customParameter_enable_directionBend'},
    'customParameter_shaking'                   :{'type':'float4x1','enablename':'customParameter_enable_shaking'},
    'customParameter_amplFreq'                  :{'type':'float4x1','enablename':'customParameter_enable_amplFreq'},
    'customParameter_controlPointAndLength'     :{'type':'float3x1','enablename':'customParameter_enable_controlPointAndLength'},
    'customParameter_lengthAndDiameter'         :{'type':'float2x1','enablename':'customParameter_enable_lengthAndDiameter'},
    'customParameter_backLightScale'            :{'type':'float',   'enablename':'customParameter_enable_backLightScale'},
    'customParameter_blinkSimple'               :{'type':'float2x1','enablename':'customParameter_enable_blinkSimple'},
    'customParameter_blinkMulti'                :{'type':'float3x1','enablename':'customParameter_enable_blinkMulti'},
                    }
def showUI():
    vsTools = vehicleShaderTools()
    vsTools.uiCreate()

def convertFS22toFS25():
    vsTools = vehicleShaderTools()
    vsTools.convertFS22toFS25()

def duplicateSelectedMaterial():
    vsTools = vehicleShaderTools()
    vsTools.duplicateSelectedMaterial()

def synhronizeMaterialTemplates():
    vsTools = vehicleShaderTools()
    vsTools.synhronizeMaterialTemplates()

class vehicleShaderTools():
    def __init__(self):
        # Load the plugin if not loaded
        if not cmds.pluginInfo('glslShader',query=True,loaded=True):
            cmds.loadPlugin('glslShader')
        self._gamePath = I3DExporter.I3DGetGamePath()
        self._xmlFilenameMaterialTemplates = "{}/{}".format(self._gamePath,'data/shared/detailLibrary/materialTemplates.xml')
        self._xmlFilenameBrandMaterialTemplates = "{}/{}".format(self._gamePath,'data/shared/brandMaterialTemplates.xml')
        self._ogsfxFile = os.path.abspath("{}/data/shaders/vehicleShader.ogsfx".format(self._gamePath))
        self._materialTemplates = {}
        self._brandMaterialTemplates = {}
        self._defaultDiffuse,self._defaultNormal,self._defaultSpecular = self.__getDefaultTextures()
        self.__refreshMayaCurrentDir()
        self.__loadXML()

    def __refreshMayaCurrentDir(self):
        self._mayaCurrentDir = str(os.path.dirname(cmds.file(q=True, sn=True)).replace('\\', '/'))

    def __getDefaultTextures(self):
        defaultDiffuse  = "{}/data/shared/white_diffuse.png".format(self._gamePath)
        defaultNormal   = "{}/data/shared/default_normal.png".format(self._gamePath)
        defaultSpecular = "{}/data/shared/default_vmask.png".format(self._gamePath)

        if not os.path.exists(defaultDiffuse):
            ddsFile = defaultDiffuse.replace(".png", ".dds")
            if os.path.exists(ddsFile):
                defaultDiffuse = ddsFile

        if not os.path.exists(defaultNormal):
            ddsFile = defaultNormal.replace(".png", ".dds")
            if os.path.exists(ddsFile):
                defaultNormal = ddsFile

        if not os.path.exists(defaultSpecular):
            ddsFile = defaultSpecular.replace(".png", ".dds")
            if os.path.exists(ddsFile):
                defaultSpecular = ddsFile

        return (defaultDiffuse, defaultNormal, defaultSpecular)

    def __getTemplateItemByNiceName(self,templates,nicename):
        for item in templates:
            if (nicename==item['nicename']):
                return item
        return None

    def __getTemplateItemByColorScale(self,templates,colorScale):
        # try predict the color based on the maya filepath
        if (self._mayaCurrentDir):
            # first iteration on the brand
            for item in templates:
                m_brandName = item["category"].lower()
                m_str = self._mayaCurrentDir.lower()
                # found brandName somewhere in the filepath
                if (-1!=m_str.find(m_brandName)):
                    if(isEqualXYZ(colorScale,getXYZWFromStr(item['colorScale']))):
                        # return first found
                        return item['nicename']
            # second iteration on the shared,lizard
            for item in templates:
                if ('SHARED'==item["category"]):
                    if(isEqualXYZ(colorScale,getXYZWFromStr(item['colorScale']))):
                        return item['nicename']
                elif('LIZARD'==item["category"]):
                    if(isEqualXYZ(colorScale,getXYZWFromStr(item['colorScale']))):
                        return item['nicename']
        return None

    def _getMaterialTemplateItemByNiceName(self,nicename):
        return self.__getTemplateItemByNiceName(self._materialTemplates,nicename)

    def _getBrandMaterialTemplateItemByNiceName(self,nicename):
        return self.__getTemplateItemByNiceName(self._brandMaterialTemplates,nicename)

    def _resolveFilePath(self,m_filePah):
        self.__refreshMayaCurrentDir()
        m_out = m_filePah
        if (0 == m_filePah.find("$data")):
            # just remove $ char
            m_out = m_filePah[1:]
            # path relative to the basegame
            m_out = os.path.abspath("{}/{}".format(self._gamePath,m_out))
        else:
            # path relative to maya file
            m_out = os.path.abspath("{}/{}".format(self._mayaCurrentDir,m_out))
        return m_out

    def uiCreate(self):
        if cmds.window(GUI_ID, exists=True):
            cmds.deleteUI(GUI_ID)

        self._ui_window = cmds.window(GUI_ID, widthHeight=(UI_WIDTH, UI_HEIGHT), sizeable=True)
        self._ui_formLayout = cmds.formLayout(parent=self._ui_window )
        #
        self._ui_xmlTxtM = cmds.textField(parent=self._ui_formLayout, w=400, editable=False )
        self._ui_xmlBtnRefreshM = cmds.symbolButton(parent=self._ui_formLayout,image="refresh.xpm",w=25,
            command=lambda *args:self.__uiCallback("_ui_xmlBtnRefreshM_pressed",args) )
        self._ui_xmlBtnM = cmds.symbolButton(parent=self._ui_formLayout,image="navButtonBrowse.xpm",w=25,
            command=lambda *args:self.__uiCallback("_ui_xmlBtnM_pressed",args) )
        #
        self._ui_xmlTxtB = cmds.textField(parent=self._ui_formLayout, w=400, editable=False )
        self._ui_xmlBtnRefreshB = cmds.symbolButton(parent=self._ui_formLayout,image="refresh.xpm",w=25,
            command=lambda *args:self.__uiCallback("_ui_xmlBtnRefreshB_pressed",args) )
        self._ui_xmlBtnB = cmds.symbolButton(parent=self._ui_formLayout,image="navButtonBrowse.xpm",w=25,
            command=lambda *args:self.__uiCallback("_ui_xmlBtnB_pressed",args) )
        #
        self._ui_synhronizeBtn = cmds.button(label='Synchronize Material Templates',w=200,
            command=lambda *args:self.__uiCallback("_ui_synhronizeBtn_pressed",args) )
        #
        self._ui_duplicateBtn = cmds.button(label='Duplicate Selected GLSL',w=200,
            command=lambda *args:self.__uiCallback("_ui_duplicateBtn_pressed",args) )
        #
        self._ui_convertBtn = cmds.button(label='Convert FS22 to FS25',w=200,
            command=lambda *args:self.__uiCallback("_ui_convertBtn_pressed",args) )
        #
        cmds.formLayout(self._ui_formLayout, edit = True,
            attachForm =    [
                             ( self._ui_xmlTxtM, 'top', 4 ),
                             ( self._ui_xmlTxtM, 'left', 4 ),
                             ( self._ui_xmlBtnRefreshM, 'top', 4 ),
                             ( self._ui_xmlBtnM, 'top', 4 ),
                             ( self._ui_xmlBtnM, 'right', 4 ),
                             ( self._ui_xmlTxtB, 'left', 4 ),
                             ( self._ui_xmlBtnB, 'right', 4 ),
                             ( self._ui_synhronizeBtn, 'left', 4 ),
                             ( self._ui_convertBtn, 'left', 4 ),
                            ],
            attachControl = [
                             ( self._ui_xmlTxtM, 'right', 4, self._ui_xmlBtnRefreshM ),
                             ( self._ui_xmlBtnRefreshM, 'right', 4, self._ui_xmlBtnM ),
                             ( self._ui_xmlTxtB, 'right', 4, self._ui_xmlBtnRefreshB ),
                             ( self._ui_xmlTxtB, 'top', 4, self._ui_xmlTxtM ),
                             ( self._ui_xmlBtnRefreshB, 'right', 4, self._ui_xmlBtnB ),
                             ( self._ui_xmlBtnRefreshB, 'top', 4, self._ui_xmlBtnRefreshM ),
                             ( self._ui_xmlBtnB, 'top', 4, self._ui_xmlBtnM ),
                             ( self._ui_synhronizeBtn, 'top', 4, self._ui_xmlTxtB ),
                             ( self._ui_duplicateBtn, 'top', 4, self._ui_xmlTxtB ),
                             ( self._ui_duplicateBtn, 'left', 4, self._ui_synhronizeBtn ),
                             ( self._ui_convertBtn, 'top', 4, self._ui_synhronizeBtn ),
                            ],
            attachNone =    [
                             ( self._ui_xmlTxtM, 'bottom' ),
                             ( self._ui_xmlBtnRefreshM, 'left' ),
                             ( self._ui_xmlBtnRefreshM, 'bottom' ),
                             ( self._ui_xmlBtnM, 'left' ),
                             ( self._ui_xmlBtnM, 'bottom' ),
                             ( self._ui_xmlTxtB, 'bottom' ),
                             ( self._ui_xmlBtnRefreshB, 'left' ),
                             ( self._ui_xmlBtnRefreshB, 'bottom' ),
                             ( self._ui_xmlBtnB, 'left' ),
                             ( self._ui_xmlBtnB, 'bottom' ),
                             ( self._ui_synhronizeBtn, 'right' ),
                             ( self._ui_synhronizeBtn, 'bottom' ),
                             ( self._ui_duplicateBtn, 'right' ),
                             ( self._ui_duplicateBtn, 'bottom' ),
                             ( self._ui_convertBtn, 'right' ),
                             ( self._ui_convertBtn, 'bottom' ),
                            ])
        cmds.showWindow(self._ui_window)
        self.__uiRefresh()

    def __loadXML(self):
        print("Game Path: {}".format(self._gamePath))
        print("XML: {}".format(self._xmlFilenameMaterialTemplates))
        print("XML: {}".format(self._xmlFilenameBrandMaterialTemplates))
        if (not os.path.exists(self._xmlFilenameMaterialTemplates)):
            OpenMaya.MGlobal.displayWarning( "Can't find {}".format( self._xmlFilenameMaterialTemplates ) )
            self._xmlFilenameMaterialTemplates = ""
        else:
            self._materialTemplates = I3DMaterialTemplateWindow.loadXML(self._xmlFilenameMaterialTemplates,'template',self._gamePath)
        if (not os.path.exists(self._xmlFilenameBrandMaterialTemplates)):
            OpenMaya.MGlobal.displayWarning( "Can't find {}".format( self._xmlFilenameBrandMaterialTemplates ) )
            self._xmlFilenameBrandMaterialTemplates = ""
        else:
            self._brandMaterialTemplates = I3DMaterialTemplateWindow.loadXML(self._xmlFilenameBrandMaterialTemplates,'template',self._gamePath)

    def __fileDialog(self,mFilePath):
        mDir = os.path.dirname(mFilePath)
        if ("" == mFilePath):
            mDir = self._gamePath
        mResult = cmds.fileDialog2( fm=1,rf=True, startingDirectory = mDir )
        if ( mResult ):
            mResult = mResult[0]
            return mResult
        return None

    def __uiCallback(self, *args):
        """
        Callback for UI
        """
        if (len(args)>0):
            m_input = args[0]
            if ('_ui_xmlBtnRefreshM_pressed'==m_input):
                self.__loadXML()
                self.__uiRefresh()
            if ('_ui_xmlBtnM_pressed'==m_input):
                mResult = self.__fileDialog(self._xmlFilenameMaterialTemplates)
                if ( mResult ):
                    self._xmlFilenameMaterialTemplates = str( mResult )
                    self._gamePath = mResult.split("/data/")[0]
                    self.__loadXML()
                    self.__uiRefresh()
            if ('_ui_xmlBtnRefreshB_pressed'==m_input):
                self.__loadXML()
                self.__uiRefresh()
            if ('_ui_xmlBtnB_pressed'==m_input):
                mResult = self.__fileDialog(self._xmlFilenameBrandMaterialTemplates)
                if ( mResult ):
                    self._xmlFilenameBrandMaterialTemplates = str( mResult )
                    self._gamePath = mResult.split("/data/")[0]
                    self.__loadXML()
                    self.__uiRefresh()
            if ('_ui_synhronizeBtn_pressed'==m_input):
                self.synhronizeMaterialTemplates()
            if ('_ui_duplicateBtn_pressed'==m_input):
                self.duplicateSelectedMaterial()
            if ('_ui_convertBtn_pressed'==m_input):
                self.convertFS22toFS25()

    def __uiRefresh(self, *args):
        # Update part of UI without commands
        cmds.textField(self._ui_xmlTxtM,edit=True,text=self._xmlFilenameMaterialTemplates)
        cmds.textField(self._ui_xmlTxtB,edit=True,text=self._xmlFilenameBrandMaterialTemplates)

    def convertFS22toFS25(self):
        if self._xmlFilenameMaterialTemplates == "":
            cmds.confirmDialog(title="I3DExporter - Error", message="Material Templates XML file not found. Set up game directory first.", icon="critical", dismissString="Ok")
            return

        self.__refreshMayaCurrentDir()
        # iterate over all shadingGroups in Maya file
        # key   - shadingGroup as string
        # value - dict with material parameters strings as keys
        self.__sourceShadingGroups = {}
        #
        m_iterator = OpenMaya.MItDependencyNodes( OpenMaya.MFn.kShadingEngine )
        m_nodeFn   = OpenMaya.MFnDependencyNode()
        while not m_iterator.isDone():
            m_object = m_iterator.thisNode()
            m_nodeFn.setObject( m_object )
            if m_nodeFn.isFromReferencedFile():
                # Skipped from a reference
                pass
                #OpenMaya.MGlobal.displayWarning( "Skipped from a reference: {}".format( m_nodeFn.name() ) )
            else:
                m_mat = getMaterialFromShadingGroup(m_nodeFn.name())
                m_obj = getMObjectFromNodeName(m_mat)
                if (m_obj):
                    m_matFn = OpenMaya.MFnDependencyNode()
                    m_matFn.setObject( m_obj )
                    if m_matFn.hasAttribute('customShader'):
                        if ("vehicleShader.xml" == os.path.basename(cmds.getAttr('{}.customShader'.format(m_matFn.name())))):
                            self.__sourceShadingGroups[m_nodeFn.name()] = {
                                'material':m_mat,
                                'materialFn':m_matFn,
                                'shadingGroup':m_nodeFn.name(),
                                'shadingGroupFn':m_nodeFn,
                                'shapesData':[]
                                }
            m_iterator.next()
        #
        # iterate over all meshes in Maya file
        #
        # shapeFullPathNames - list of meshes (string) associated to the shadingGroup
        # shapeMDagPaths - list of meshes (OpenMaya.MDagPath()) associated to the shadingGroup
        #
        m_commonUVSetNames = commonUVSetNames() # collect the most common uvSet names
        m_iterator = OpenMaya.MItDag( OpenMaya.MItDag.kDepthFirst )
        while not m_iterator.isDone():
            m_object   = m_iterator.currentItem()
            m_nodeFn.setObject( m_object )
            if m_nodeFn.isFromReferencedFile():
                # Skipped from a reference
                pass
                #OpenMaya.MGlobal.displayWarning( "Skipped from a reference: {}".format( m_nodeFn.name() ) )
            else:
                m_path  = OpenMaya.MDagPath()
                m_iterator.getPath(m_path)
                if ( OpenMaya.MFn.kMesh == m_object.apiType() ):
                    m_path.extendToShape()
                    m_listShadingGroups = getShapeShadingGroupsAsList(m_path)
                    if (m_listShadingGroups and len(m_listShadingGroups)>0):
                        m_sg = m_listShadingGroups[0] # in FS22 we should have only 1 shadingGroup assigned to the mesh
                        # update __sourceShadingGroups with the meshes associated to this shadingGroup
                        # check only materials with vehicleShader.xml as a customShader
                        if (m_sg in self.__sourceShadingGroups):
                            item = {
                                    'fullPathName':m_path.fullPathName(),
                                    'MDagPath':m_path,
                                    'shapeUVIds':getShapeUVindexes(m_path) # get UDIM uv indexes from the shape with polygonIds
                                    }
                            self.__sourceShadingGroups[m_sg]['shapesData'].append(item)
                            m_commonUVSetNames.addNames(getShapeUVSetNames(m_path))
            m_iterator.next()
        #
        # iterate over __sourceShadingGroups and make a placeholders for the GLSL shaders based on shapeUVIds
        # should have something like that: {'colorMat0': {}, '18': {}, '1': {}, '16': {}, '8': {}}
        #
        for m_sg,m_sgItem in self.__sourceShadingGroups.items():
            m_glslIds = {}
            for m_data in m_sgItem['shapesData']:
                # m_data['shapeUVIds'] is like that: {'5': ['0:69', '126:195'], 'colorMat1': ['70:109', '196:235'], '2': ['110:125', '236:251']}
                for m_id,m_list in m_data['shapeUVIds'].items():
                    m_glslIds[m_id] = {}
            self.__sourceShadingGroups[m_sg]['glslIds'] = m_glslIds
        for m_sg,m_sgItem in self.__sourceShadingGroups.items():
            # placeholder is not empty so add '0' item for fallback case
            if (bool(m_sgItem['glslIds'])):
                self.__sourceShadingGroups[m_sg]['glslIds']['0'] = {}
        #
        # iterate over __sourceShadingGroups and collect materials data
        #
        for m_sg,m_sgItem in self.__sourceShadingGroups.items():
            self.__sourceShadingGroups[m_sg]['materialData'] = self.__getPhongAttributes(m_sgItem,m_commonUVSetNames)
        #
        # make GLSL materials
        #
        for m_sg,m_sgItem in self.__sourceShadingGroups.items():
            #print(m_sg,m_sgItem['material'],m_sgItem['glslIds'])
            # might be the case that material is not used
            if (('glslIds' in m_sgItem) and bool(m_sgItem['glslIds'])):
                for m_glslId,glslIdData in m_sgItem['glslIds'].items():
                    # name of the material
                    m_nameStr = I3DUtils.getNameFromFilePath(self.__sourceShadingGroups[m_sg]['materialData']['sharedAttributes']['specularMap']['value']['filePath'])
                    #
                    m_templateAttributes = {}
                    #print(m_glslId,glslIdData)
                    if (0==m_glslId.find("colorMat")):
                        #
                        # source do have colorMat definition
                        #
                        if ('colorMats' in self.__sourceShadingGroups[m_sg]['materialData']):
                            if (m_glslId in self.__sourceShadingGroups[m_sg]['materialData']['colorMats']):
                                #
                                # colorMat index
                                #
                                m_colorMat = self.__sourceShadingGroups[m_sg]['materialData']['colorMats'][m_glslId]
                                #print(m_glslId,m_colorMat)
                                if (('materialTemplateId' in m_colorMat) and not ('brandMaterialTemplateId' in m_colorMat)):
                                    # materialTemplateId
                                    # customParameterTemplate_brandColor_material
                                    m_templateAttributes = self._getAttributesFromMaterialTemplate(m_colorMat['materialTemplateId'])
                                    # add 'customParameter_colorScale' to the m_templateAttributes
                                    #print(m_colorMat)
                                    m_templateAttributes['customParameter_colorScale'] = m_colorMat
                                    #
                                    m_attributeStr = 'customParameterTemplate_brandColor_material'
                                    m_templateAttributes[m_attributeStr] = {'name':m_attributeStr,
                                                                            'type':'string',
                                                                           'value':m_colorMat['materialTemplateId']}
                                    m_nameStr = "{}_{}".format(m_nameStr,m_colorMat['materialTemplateId'])
                                    #print('materialTemplateId',m_templateAttributes)
                                if (('materialTemplateId' in m_colorMat) and ('brandMaterialTemplateId' in m_colorMat)):
                                    # materialTemplateId and brandMaterialTemplateId
                                    # customParameterTemplate_brandColor_material
                                    # customParameterTemplate_brandColor_brandColor
                                    m_templateAttributes = self._getAttributesFromBrandAndMaterial(m_colorMat['brandMaterialTemplateId'],m_colorMat['materialTemplateId'])
                                    #
                                    m_attributeStr = 'customParameterTemplate_brandColor_material'
                                    m_templateAttributes[m_attributeStr] = {'name':m_attributeStr,
                                                                            'type':'string',
                                                                           'value':m_colorMat['materialTemplateId']}
                                    m_attributeStr = 'customParameterTemplate_brandColor_brandColor'
                                    m_templateAttributes[m_attributeStr] = {'name':m_attributeStr,
                                                                            'type':'string',
                                                                           'value':m_colorMat['brandMaterialTemplateId']}
                                    m_nameStr = "{}_{}_{}".format(m_nameStr,m_colorMat['brandMaterialTemplateId'],m_colorMat['materialTemplateId'])
                                    #print('materialTemplateId','brandMaterialTemplateId',m_templateAttributes)
                                if (not ('materialTemplateId' in m_colorMat) and ('brandMaterialTemplateId' in m_colorMat)):
                                    # brandMaterialTemplateId
                                    # customParameterTemplate_brandColor_brandColor
                                    m_templateAttributes = self._getAttributesFromBrandMaterialTemplate(m_colorMat['brandMaterialTemplateId'])
                                    m_attributeStr = 'customParameterTemplate_brandColor_brandColor'
                                    m_templateAttributes[m_attributeStr] = {'name':m_attributeStr,
                                                                            'type':'string',
                                                                           'value':m_colorMat['brandMaterialTemplateId']}
                                    m_nameStr = "{}_{}".format(m_nameStr,m_colorMat['brandMaterialTemplateId'])
                                    #print('brandMaterialTemplateId',m_templateAttributes)
                        else:
                            #
                            # might be the case where source do not have colorMat definition
                            # later in the code we have to use 'fallback material'
                            #
                            pass
                    else:
                        #
                        # uv-based index
                        #
                        materialId = int(m_glslId)
                        materialTemplateIds = self.__sourceShadingGroups[m_sg]['materialData']['materialTemplateIds']
                        if materialId < len(materialTemplateIds):
                            m_materialTemplateId = materialTemplateIds[materialId]
                            m_templateAttributes = self._getAttributesFromMaterialTemplate(m_materialTemplateId)
                            m_attributeStr = 'customParameterTemplate_brandColor_material'
                            m_templateAttributes[m_attributeStr] = {'name':m_attributeStr,
                                                                    'type':'string',
                                                                    'value':m_materialTemplateId}
                            m_nameStr = "{}_{}".format(m_nameStr,m_materialTemplateId)
                        #print(m_glslId,m_materialTemplateId)
                    #
                    # here we should have everything prepared
                    #
                    if (bool(m_templateAttributes)):
                        self.__m_mat = {}
                        self.__m_mat.update(m_templateAttributes)
                        self.__m_mat.update(self.__sourceShadingGroups[m_sg]['materialData']['sharedAttributes'])
                        self.__matStr = m_nameStr
                        # make new GLSL instance
                        #print(self.__matStr,self.__m_mat)
                        self.__sourceShadingGroups[m_sg]['glslIds'][m_glslId] = self.__createGLSLVehicleMaterial()
                        #print(m_glslId, self.__sourceShadingGroups[m_sg]['glslIds'][m_glslId])
                    else:
                        # 'fallback material'
                        pass
        #
        # Assign created materials to the geometry
        #
        for m_sg,m_sgItem in self.__sourceShadingGroups.items():
            for m_data in m_sgItem['shapesData']:
                #print(m_data['MDagPath'].fullPathName(), m_data['shapeUVIds'])
                m_resultString = ""
                m_resultString += "select -clear;\n"
                for m_matId,m_polygonIds in m_data['shapeUVIds'].items():
                    m_str = ""
                    for m_aMember in m_polygonIds:
                        m_str += '{}.f[{}] '.format(m_data['MDagPath'].fullPathName(),m_aMember)
                    m_resultString += "select -r {};\n".format( m_str )
                    if (m_matId in self.__sourceShadingGroups[m_sg]['glslIds']):
                        m_glslMaterial = self.__sourceShadingGroups[m_sg]['glslIds'][m_matId]
                        if (not bool(m_glslMaterial)):
                            m_glslMaterial = self.__sourceShadingGroups[m_sg]['glslIds']['0'] # fallback material
                    else:
                        m_glslMaterial = self.__sourceShadingGroups[m_sg]['glslIds']['0'] # fallback material
                    m_resultString += "sets -e -forceElement {};\n".format(m_glslMaterial['shadingGroup'])
                #
                # Assign shadingGroup here
                #
                print(m_resultString)
                OpenMaya.MGlobal.executeCommand( m_resultString )
        #

    def __createGLSLVehicleMaterial(self):
        # make new GLSL
        print(" ")
        matInstance = cmds.shadingNode('GLSLShader',name="{}_mat".format(self.__matStr) , asShader=True)
        print("Created: {}".format(matInstance))
        # set shader path before anything else
        cmds.setAttr("{}.shader".format(matInstance), "{}".format(self._ogsfxFile), type='string')
        # make new shadingGroup
        sgInstance = cmds.sets(name="{}_s".format(self.__matStr),renderable=True,noSurfaceShader=True,empty=True)
        print("Created: {}".format(sgInstance))
        # connect material to shadingGroup
        cmds.connectAttr("{}.outColor".format(matInstance),"{}.surfaceShader".format(sgInstance),force=True)
        print("Connected: {}.outColor to {}.surfaceShader".format(matInstance,sgInstance))
        #
        self.__m_node = getMObjectFromNodeName(matInstance)
        sg_node = getMObjectFromNodeName(sgInstance)
        # this should always happen
        if (self.__m_node and sg_node):
            self.__m_nodeFn = OpenMaya.MFnDependencyNode()
            self.__m_nodeFn.setObject( self.__m_node )
            self.__matStr = self.__m_nodeFn.name()
            # assign attributes
            #print(self.__m_mat)
            for k,v in self.__m_mat.items():
                #
                # !!! set attribute here !!!
                #
                self.__setGLSLAttributeItem(v)
            # connect to the shadingGroup
            sg_nodeFn = OpenMaya.MFnDependencyNode()
            sg_nodeFn.setObject(sg_node)
            item = {  'material':self.__matStr,
                      'materialFn':self.__m_nodeFn,
                      'shadingGroup':sg_nodeFn.name(),
                      'shadingGroupFn':sg_nodeFn, }
            return item
        return None

    def __getPhongAttributes(self,m_sgItem,m_commonUVSetNames):
        # __m_node   - OpenMaya.MObject() to the material node
        # __m_nodeFn - OpenMaya.MFnDependencyNode() to the material node
        #
        self.__m_nodeFn = m_sgItem['materialFn']
        self.__m_node   = m_sgItem['materialFn'].object()
        self.__matStr   = m_sgItem['materialFn'].name()
        #
        m_material = {}
        # use FS22IDs by default
        m_material['materialTemplateIds'] = FS22IDs
        #
        m_attributes = {}
        # shader
        m_attributes['shader'] = {'name':'shader','type':'string','value':self._ogsfxFile}
        # alphaBlend
        m_attributes['technique'] = self.__getPhongAttrItemAlphaBlend()
        # if alphaBlending enabled we also set alphaBlendingClipThreshold to 0.0
        if ('alphaBlending' == m_attributes['technique']['value']):
            m_attributeStr = 'customParameter_alphaBlendingClipThreshold'
            m_attributes[m_attributeStr] = {
                      'name':m_attributeStr,
                'enablename':FS25customParameter[m_attributeStr]['enablename'],
                      'type':FS25customParameter[m_attributeStr]['type'],
                     'value':{'x':0.0,'y':0.0,'z':0.0,'w':0.0}
            }
        # color == diffuseMap
        m_attributes['diffuseMap'] = self.__getPhongAttrItemTexture('color','diffuseMap',self._defaultDiffuse)
        # normalCamera == normalMap
        m_attributes['normalMap'] = self.__getPhongAttrItemTexture('normalCamera','normalMap',self._defaultNormal)
        # specularColor == specularMap
        m_attributes['specularMap'] = self.__getPhongAttrItemTexture('specularColor','specularMap',self._defaultSpecular)
        # customShaderVariation
        if (self.__m_nodeFn.hasAttribute('customShaderVariation')):
            m_attributes['customShaderVariation'] = self.__getPhongAttrItemCustomShaderVariation()
            if ('oldValue' in m_attributes['customShaderVariation']):
                m_variationStr = m_attributes['customShaderVariation']['oldValue']
                if (-1!=m_variationStr.find("Decal")):
                    # alphaBlendingClipThreshold = 1 <- Decal shaderVariation
                    m_attributeStr = 'customParameter_alphaBlendingClipThreshold'
                    m_attributes[m_attributeStr] = {
                              'name':m_attributeStr,
                        'enablename':FS25customParameter[m_attributeStr]['enablename'],
                              'type':FS25customParameter[m_attributeStr]['type'],
                             'value':{'x':1.0,'y':1.0,'z':1.0,'w':1.0}
                    }
                if((-1!=m_variationStr.find("secondUV")) or (-1!=m_variationStr.find("Decal"))):
                    # map2 == uv1 TexCoord1_Source
                    m_attributeStr = 'TexCoord1_Source'
                    m_attributes[m_attributeStr] = {
                              'name':m_attributeStr,
                              'type':'string',
                             'value':"uv:{}".format(m_commonUVSetNames.uv1)
                    }
                if(-1!=m_variationStr.find("ThirdUV")):
                    # map3 == uv2 TexCoord2_Source
                    m_attributeStr = 'TexCoord2_Source'
                    m_attributes[m_attributeStr] = {
                              'name':m_attributeStr,
                              'type':'string',
                             'value':"uv:{}".format(m_commonUVSetNames.uv2)
                    }
                if(-1!=m_variationStr.find("colorMask")):
                    # we need to use FS22IDs_colorMask for this material
                    m_material['materialTemplateIds'] = FS22IDs_colorMask
                if(-1!=m_variationStr.find("tirePressureDeformation")):
                    # tirePressureDeformation was with colorMask activated by default
                    # we need to use FS22IDs_colorMask for this material
                    m_material['materialTemplateIds'] = FS22IDs_colorMask
                if(-1!=m_variationStr.find("staticLight")):
                    # staticLight was with colorMask activated by default
                    # we need to use FS22IDs_colorMask for this material
                    m_material['materialTemplateIds'] = FS22IDs_colorMask
        # customParameter_*, customTexture_*, colorMat*
        m_colorMat = {}
        for i in range( self.__m_nodeFn.attributeCount()):
            m_fnAttr = OpenMaya.MFnAttribute( self.__m_nodeFn.attribute(i) )
            m_attributeStr = m_fnAttr.name()
            if (0 == m_attributeStr.find("customParameter_")):
                m_nameShort = m_attributeStr.replace("customParameter_",'')
                if (0 == m_nameShort.find("colorMat")):
                    m_colorMat[m_nameShort] = self.__getPhongAttrItemColorMat(m_attributeStr)
                    #print(m_colorMat[m_nameShort])
                else:
                    m_res = self.__getPhongAttrItemCustomParameter(m_attributeStr)
                    if (m_res):
                        m_attributes[m_res['name']] = m_res
            elif(0 == m_attributeStr.find("customTexture_")):
                m_res = self.__getPhongAttrItemCustomTexture(m_attributeStr)
                if (m_res):
                    m_attributes[m_res['name']] = m_res
        if (bool(m_colorMat)):
            # do not export empty dict
            m_material['colorMats'] = m_colorMat
        #
        m_material['sharedAttributes'] = m_attributes
        return m_material

    def _getAttributesFromBrandMaterialTemplate(self,nicename):
        m_brandColor = self.__getTemplateItemByNiceName(self._brandMaterialTemplates,nicename)
        if (m_brandColor):
            if m_brandColor['parentTemplate']:
                m_brandColorTemplate = self.__getTemplateItemByNiceName(self._materialTemplates,m_brandColor['parentTemplate'])
            elif m_brandColor['parentTemplateDefault']:
                m_brandColorTemplate = self.__getTemplateItemByNiceName(self._materialTemplates,m_brandColor['parentTemplateDefault'])
            if (m_brandColorTemplate):
                m_attributesParentTemplate = self.__getAttributesFromTemplate(self._materialTemplates,m_brandColorTemplate['nicename'])
                m_attributesBrandColor = self.__getAttributesFromTemplate(self._brandMaterialTemplates,nicename)
                m_attributes = m_attributesParentTemplate
                for k,v in m_attributesBrandColor.items():
                    # override from brands
                    if (v):
                        m_attributes[k] = v
                if (bool(m_attributes)):
                    # do not export empty dict
                    return m_attributes
        return None

    def _getAttributesFromMaterialTemplate(self,nicename):
        return self.__getAttributesFromTemplate(self._materialTemplates,nicename)

    def _getAttributesFromBrandAndMaterial(self,brandColor,material):
        # in case we need to override 'material' on 'brandColor'
        # we keep only colorScale
        m_brandColor = self._getAttributesFromBrandMaterialTemplate(brandColor)
        m_material = self._getAttributesFromMaterialTemplate(material)
        if (m_brandColor and m_material):
            m_attributeStr = 'templateParameter_colorScale'
            if (m_attributeStr in m_brandColor):
                m_material[m_attributeStr] = m_brandColor[m_attributeStr]
            return m_material
        return None

    def __getAttributesFromTemplate(self,templates,nicename):
        #
        m_brandColor = self.__getTemplateItemByNiceName(templates,nicename)
        if (m_brandColor):
            m_attributes = {}
            m_items = ['colorScale','detailDiffuse','detailNormal','detailSpecular','smoothnessScale','metalnessScale','clearCoatIntensity','clearCoatSmoothness']
            for m_item in m_items:
                if (m_brandColor[m_item]):
                    m_attributeStr = "templateParameter_{}".format(m_item)
                    if (m_attributeStr in FS25customParameter):
                        m_attr = {}
                        m_attr['name'] = m_attributeStr
                        m_attr['type'] = FS25customParameter[m_attr['name']]['type']
                        m_attr['enablename'] = FS25customParameter[m_attr['name']]['enablename']
                        m_add = False
                        if ('texture'==m_attr['type']):
                            m_attr['value'] = {'filePath':m_brandColor[m_item]}
                            m_add = True
                        elif('color3x1'==m_attr['type'] or 'float3x1'==m_attr['type']):
                            m_attr['value'] = getXYZWFromStr(m_brandColor[m_item])
                            m_add = True
                        elif('float'==m_attr['type']):
                            m_attr['value'] = {'x':float(m_brandColor[m_item])}
                            m_add = True
                        else:
                            m_add = False
                        if (m_add):
                            m_attributes[m_attr['name']] = m_attr
            if (bool(m_attributes)):
                # do not export empty dict
                return m_attributes
        return None

    def __getPhongAttrItemCustomTexture(self,m_attributeStr):
        #
        if (m_attributeStr in FS22customTexture):
            m_attr = {}
            m_attr['name'] = FS22customTexture[m_attributeStr] # get the new name str
            m_attr['type'] = FS25customParameter[m_attr['name']]['type']
            m_attr['enablename'] = FS25customParameter[m_attr['name']]['enablename']
            #
            m_res = getAttr(self.__m_node,m_attributeStr)
            if (m_res and 'kString'==m_res['type']):
                m_attr['value'] = {'filePath':self._resolveFilePath(m_res['value'])}
                return m_attr
            else:
                return None
        else:
            return None

    def __getPhongAttrItemCustomParameter(self,m_attributeStr):
        #
        if (m_attributeStr in FS22customParameter):
            m_attr = {}
            m_attr['name'] = FS22customParameter[m_attributeStr] # get the new name str
            m_attr['type'] = FS25customParameter[m_attr['name']]['type']
            m_attr['enablename'] = FS25customParameter[m_attr['name']]['enablename']
            #
            m_res = getAttr(self.__m_node,m_attributeStr)
            if (m_res and 'kString'==m_res['type']):
                m_attr['value'] = getXYZWFromStr(m_res['value'])
                return m_attr
            else:
                return None
        else:
            return None

    def __getPhongAttrItemColorMat(self,m_attributeStr):
        #
        m_attr = {}
        #
        m_res = getAttr(self.__m_node,m_attributeStr)
        if (m_res and 'kString'==m_res['type']):
            m_attr['oldValue'] = m_res['value']
            # get 'x','y','z','w'
            m_xyzw = getXYZWFromStr(m_res['value'])
            # try to find brandColor
            m_brandColor = self.__getTemplateItemByColorScale(self._brandMaterialTemplates,m_xyzw)
            if (m_brandColor):
                m_attr['brandMaterialTemplateId'] = m_brandColor
            else:
                m_attr['name'] = 'customParameter_colorScale'
                m_attr['type'] = FS25customParameter[m_attr['name']]['type']
                m_attr['enablename'] = FS25customParameter[m_attr['name']]['enablename']
                m_attr['value'] = m_xyzw
            # load materialTemplateId
            m_index = 0
            if (('w' in m_xyzw) and m_xyzw['w']):
                if (m_xyzw['w'] < len(FS22IDs)):
                    m_index = int(m_xyzw['w'])
            m_attr['materialTemplateId'] = FS22IDs[m_index]
            #print(m_brandColor,m_attr['materialTemplateId'],m_xyzw)
        # {'oldValue': '0.02 0.02 0.02 37', 'name': 'customParameter_colorScale', 'type': 'color3x1', 'enablename': 'customParameter_enable_colorScale', 'value': {'x': 0.02, 'y': 0.02, 'z': 0.02, 'w': 37.0}, 'materialTemplateId': 'perforatedSynthetic2'}
        # {'oldValue': '0.7155 0.1636 0.0000 1', 'brandMaterialTemplateId': 'FENDT_ORANGE1', 'materialTemplateId': 'plasticPainted'}
        return m_attr

    def __getPhongAttrItemCustomShaderVariation(self):
        #
        m_attr = {}
        m_attr['name'] = 'customShaderVariation'
        m_attr['type'] = 'enum'
        m_attr['value'] = 0
        #
        m_res = getAttr(self.__m_node,'customShaderVariation')
        if (m_res and 'kString'==m_res['type']):
            # get the name for FS25
            m_attr['oldValue'] = m_res['value']
            if (m_res['value'] in FS22customShaderVariation):
                m_strName = FS22customShaderVariation[m_res['value']]
                if (m_strName in FS25shaderVariationsList):
                    # get the index from FS25 variations list
                    m_attr['value'] = FS25shaderVariationsList.index(m_strName)
        return m_attr

    def __getPhongAttrItemTexture(self,m_attrStrFrom,m_attrStrTo,m_defaultValue):
        #
        m_attr = {}
        m_attr['name'] = m_attrStrTo
        m_attr['type'] = 'texture'
        #
        m_res = getAttr(self.__m_node,m_attrStrFrom)
        # might the case that texture is not specified
        if(m_res and 'isDestination'==m_res['type'] and m_res['data']):
            m_attr['value'] = m_res['data']
        else:
            m_attr['value'] = {'filePath':m_defaultValue}
        return m_attr

    def __getPhongAttrItemAlphaBlend(self):
        #
        m_attr = {}
        m_attr['name'] = 'technique'
        m_attr['type'] = 'string'
        #
        m_res = getAttr(self.__m_node,'translucence')
        if (m_res and 'kFloat'==m_res['type'] and (1.0==m_res['value'])):
            m_attr['value'] = 'alphaBlending'
        else:
            m_attr['value'] = 'opaque'
        return m_attr

    def duplicateSelectedMaterial(self):
        # run on Selected
        m_list = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList( m_list )
        m_listIt = OpenMaya.MItSelectionList( m_list )
        while not m_listIt.isDone():
            # check if it's a material
            if (OpenMaya.MItSelectionList.kDNselectionItem==m_listIt.itemType()):
                m_obj = OpenMaya.MObject()
                m_listIt.getDependNode(m_obj)
                # check if we selected GLSL Shader
                if (m_obj.hasFn(OpenMaya.MFn.kPluginHardwareShader)):
                    # m_node   - OpenMaya.MObject() to the material node
                    # m_nodeFn - OpenMaya.MFnDependencyNode() to the material node
                    self.__m_node = m_obj
                    self.__m_nodeFn = OpenMaya.MFnDependencyNode()
                    self.__m_nodeFn.setObject( self.__m_node )
                    self.__matStr = self.__m_nodeFn.name()
                    self.__duplicateMaterialInstance()
            m_listIt.next()

    def synhronizeMaterialTemplates(self):
        # iterate over all GLSL Shaders in Maya file
        m_iterator = OpenMaya.MItDependencyNodes( OpenMaya.MFn.kPluginHardwareShader )
        while not m_iterator.isDone():
            # m_node   - OpenMaya.MObject() to the material node
            # m_nodeFn - OpenMaya.MFnDependencyNode() to the material node
            self.__m_node = m_iterator.thisNode()
            self.__m_nodeFn = OpenMaya.MFnDependencyNode()
            self.__m_nodeFn.setObject( self.__m_node )
            self.__matStr = self.__m_nodeFn.name()
            if ":" not in self.__matStr: # exclude reference files
                self.__synhronizeMaterialInstance()
            m_iterator.next()

    def __duplicateMaterialInstance(self):
        # dict with source data
        self.__m_mat = {}
        for i in range( self.__m_nodeFn.attributeCount()):
            m_atrr = self.__m_nodeFn.attribute(i)
            m_fnAttr = OpenMaya.MFnAttribute( m_atrr )
            m_attrPlug  = OpenMaya.MPlug( self.__m_node, m_atrr )
            m_attributeStr = m_fnAttr.name()
            fullname = '{}.{}'.format(self.__matStr,m_attributeStr)
            # collect attributes
            #print(m_attributeStr,getAttr(self.__m_node,m_attributeStr))
            m_res = self.__getGLSLAttributeItem(m_attributeStr)
            if (m_res):
                self.__m_mat[m_res['name']] = m_res
        #print(self.__m_mat)
        # make new GLSL shader and copy data
        self.__matStr = cmds.shadingNode('GLSLShader',name=self.__matStr , asShader=True)
        self.__m_node = getMObjectFromNodeName(self.__matStr)
        # this should always happen
        if (self.__m_node):
            self.__m_nodeFn = OpenMaya.MFnDependencyNode()
            self.__m_nodeFn.setObject( self.__m_node )
            self.__matStr = self.__m_nodeFn.name()
            for k,v in self.__m_mat.items():
                self.__setGLSLAttributeItem(v)

    def __setGLSLAttributeItem(self,m_av):
        #
        if ('customParameterTemplate_brandColor_brandColor' == m_av['name']):
            if (not self.__m_nodeFn.hasAttribute(m_av['name'])):
                cmds.addAttr(self.__matStr, shortName=m_av['name'], niceName=m_av['name'], longName=m_av['name'], dt='string')
        elif ('customParameterTemplate_brandColor_material' == m_av['name']):
            if (not self.__m_nodeFn.hasAttribute(m_av['name'])):
                cmds.addAttr(self.__matStr, shortName=m_av['name'], niceName=m_av['name'], longName=m_av['name'], dt='string')
        # all other attributes should be defined by the sahder
        self.__setGLSLAttributeItemType(m_av)
        if ('enablename' in m_av):
            setBoolAttr(self.__m_node,m_av['enablename'],True)

    def __getGLSLAttributeItem(self,m_attributeStr):
        #
        if ('shader' == m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'string')
        elif ('technique' == m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'string')
        elif ('customParameterTemplate_brandColor_brandColor' == m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'string')
        elif ('customParameterTemplate_brandColor_material' == m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'string')
        elif ('envMap' == m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'texture')
        elif ('diffuseMap' == m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'texture')
        elif ('normalMap' == m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'texture')
        elif ('specularMap' == m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'texture')
        elif ('customShaderVariation' == m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'enum')
        elif ('shadingRate' == m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'enum')
        elif ('Color0_Source'==m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'string')
        elif ('TexCoord0_Source'==m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'string')
        elif ('TexCoord1_Source'==m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'string')
        elif ('TexCoord2_Source'==m_attributeStr):
            return self.__getGLSLAttributeItemType(m_attributeStr,'string')
        # custom and template  parameters
        m_attr = {}
        m_params = [("customParameter_enable_","customParameter_","customTexture_"),("templateParameter_enable_","templateParameter_","")]
        for m_a1,m_a2,m_a3 in m_params:
            if (m_attributeStr.startswith(m_a1) and m_attributeStr.endswith("_Name")):
                m_nicename = m_attributeStr.replace(m_a1,"").replace("_Name","")
                # check the bool
                m_enablename = "{}{}".format(m_a1,m_nicename)
                m_res1 = getAttr(self.__m_node,m_enablename)
                # if bool is enabled, check the other attribute
                if (m_res1 and 'kBoolean'==m_res1['type'] and m_res1['value']):
                    # customParameter_enable_, templateParameter_enable_ is True
                    m_attr['shadername'] = m_nicename
                    m_fullname = "{}{}".format(m_a2,m_nicename)
                    # customParameter_, templateParameter_
                    if (self.__m_nodeFn.hasAttribute(m_fullname)):
                        m_attr['name'] = m_fullname
                    # customTexture_
                    m_fullname = "{}{}".format(m_a3,m_nicename)
                    if (self.__m_nodeFn.hasAttribute(m_fullname)):
                        m_attr['name'] = m_fullname
                    #
                    m_attr['enablename'] = m_enablename
                    # _Type
                    m_res2 = getAttr(self.__m_node,"{}_Type".format(m_attr['name']))
                    if (m_res2 and 'kString'==m_res2['type']):
                        m_attr['type'] = m_res2['value']
                        m_res = self.__getGLSLAttributeItemType(m_attr['name'],m_attr['type'])
                        if m_res:
                            m_res['shadername'] = m_attr['shadername']
                            m_res['enablename'] = m_attr['enablename']
                            return m_res
                        else:
                            return None
        return None

    def __setGLSLAttributeItemType(self,m_av):
        if ('string'==m_av['type']):
            setStringAttr(self.__m_node,m_av['name'],m_av['value'])
        elif('texture'==m_av['type']):
            if m_av['value']['filePath'] is not None:
                setTextureAttr(self.__m_node,m_av['name'],'',m_av['value']['filePath'])
        elif('enum'==m_av['type']):
            setEnumAttr(self.__m_node,m_av['name'],m_av['value'])
        elif('float'==m_av['type']):
            setFloatAttr(self.__m_node,m_av['name'],m_av['value']['x'])
        elif('float2x1'==m_av['type']):
            setFloatAttr(self.__m_node,"{}X".format(m_av['name']),m_av['value']['x'])
            setFloatAttr(self.__m_node,"{}Y".format(m_av['name']),m_av['value']['y'])
        elif('color3x1'==m_av['type'] or 'float3x1'==m_av['type']):
            setDouble3Attr(self.__m_node,m_av['name'],m_av['value'])
        elif('float4x1'==m_av['type']):
            setFloatAttr(self.__m_node,"{}X".format(m_av['name']),m_av['value']['x'])
            setFloatAttr(self.__m_node,"{}Y".format(m_av['name']),m_av['value']['y'])
            setFloatAttr(self.__m_node,"{}Z".format(m_av['name']),m_av['value']['z'])
            setFloatAttr(self.__m_node,"{}W".format(m_av['name']),m_av['value']['w'])
        elif('bool'==m_av['type']):
            setBoolAttr(self.__m_node,m_av['name'],m_av['value'])

    def __getGLSLAttributeItemType(self,m_attributeStr,m_type):
        #
        m_attr = {}
        m_attr['name'] = m_attributeStr
        m_attr['type'] = m_type
        #
        if ('string'==m_type):
            m_res = getAttr(self.__m_node,m_attributeStr)
            if (m_res and 'kString'==m_res['type']):
                m_attr['value'] = m_res['value']
                return m_attr
            else:
                return None
        elif('texture'==m_type):
            m_res = getAttr(self.__m_node,m_attributeStr)
            # might the case that texture is not specified
            if(m_res and 'isDestination'==m_res['type'] and m_res['data']):
                m_attr['value'] = m_res['data']
                return m_attr
            else:
                return None
        elif('enum'==m_type):
            m_res = getAttr(self.__m_node,m_attributeStr)
            if(m_res and 'kEnumAttribute'==m_res['type']):
                m_attr['value'] = m_res['value']
                m_attr['data'] = m_res['data']
                return m_attr
            else:
                return None
        elif('float'==m_type):
            m_res = getAttr(self.__m_node,m_attributeStr)
            if ('kFloat'==m_res['type']):
                m_attr['value'] = {'x':m_res['value']}
                return m_attr
            else:
                return None
        elif('float2x1'==m_type or 'color3x1'==m_type or 'float3x1'==m_type):
            m_res = getAttr(self.__m_node,m_attributeStr)
            if ('isCompound'==m_res['type']):
                m_attr['value'] = m_res['data']
                return m_attr
            else:
                return None
        elif('float4x1'==m_type):
            m_attr['value'] = {'x': None, 'y': None, 'z': None, 'w': None}
            m_x = getAttr(self.__m_node,"{}X".format(m_attributeStr))
            if ('kFloat'==m_x['type']):
                m_attr['value']['x'] = m_x['value']
            m_y = getAttr(self.__m_node,"{}Y".format(m_attributeStr))
            if ('kFloat'==m_y['type']):
                m_attr['value']['y'] = m_y['value']
            m_z = getAttr(self.__m_node,"{}Z".format(m_attributeStr))
            if ('kFloat'==m_z['type']):
                m_attr['value']['z'] = m_z['value']
            m_w = getAttr(self.__m_node,"{}W".format(m_attributeStr))
            if ('kFloat'==m_w['type']):
                m_attr['value']['w'] = m_w['value']
            # check all the values
            if (m_attr['value']['x'] and m_attr['value']['y'] and m_attr['value']['z'] and m_attr['value']['w']):
                return m_attr
            else:
                return None
        return None

    def __synhronizeMaterialInstance(self):
        #
        # Collect the data, self.__m_node - OpenMaya.MObject() to the material node
        #
        self.__m_mat = {}
        # customParameterTemplate_brandColor_brandColor
        m_res = getAttr(self.__m_node,'customParameterTemplate_brandColor_brandColor')
        if (m_res and 'kString'==m_res['type']):
            self.__m_mat['customParameterTemplate_brandColor_brandColor'] = m_res['value']
        # customParameterTemplate_brandColor_material
        m_res = getAttr(self.__m_node,'customParameterTemplate_brandColor_material')
        if (m_res and 'kString'==m_res['type']):
            self.__m_mat['customParameterTemplate_brandColor_material'] = m_res['value']
        # templateParameter_detailDiffuse
        m_res = getAttr(self.__m_node,'templateParameter_detailDiffuse')
        if (m_res and 'isDestination'==m_res['type'] and m_res['data']):
            self.__m_mat['templateParameter_detailDiffuse'] = m_res['data']
        # templateParameter_detailNormal
        m_res = getAttr(self.__m_node,'templateParameter_detailNormal')
        if (m_res and 'isDestination'==m_res['type'] and m_res['data']):
            self.__m_mat['templateParameter_detailNormal'] = m_res['data']
        # templateParameter_detailSpecular
        m_res = getAttr(self.__m_node,'templateParameter_detailSpecular')
        if (m_res and 'isDestination'==m_res['type'] and m_res['data']):
            self.__m_mat['templateParameter_detailSpecular'] = m_res['data']
        # templateParameter_colorScale
        m_res = getAttr(self.__m_node,'templateParameter_enable_colorScale')
        if (m_res and 'kBoolean'==m_res['type'] and m_res['value']):
            m_res = getAttr(self.__m_node,'templateParameter_colorScale')
            if ('isCompound'==m_res['type']):
                self.__m_mat['templateParameter_colorScale'] = m_res['data']
        # templateParameter_smoothnessScale
        m_res = getAttr(self.__m_node,'templateParameter_enable_smoothnessScale')
        if (m_res and 'kBoolean'==m_res['type'] and m_res['value']):
            m_res = getAttr(self.__m_node,'templateParameter_smoothnessScale')
            if ('kFloat'==m_res['type']):
                self.__m_mat['templateParameter_smoothnessScale'] = m_res['value']
        # templateParameter_metalnessScale
        m_res = getAttr(self.__m_node,'templateParameter_enable_metalnessScale')
        if (m_res and 'kBoolean'==m_res['type'] and m_res['value']):
            m_res = getAttr(self.__m_node,'templateParameter_metalnessScale')
            if ('kFloat'==m_res['type']):
                self.__m_mat['templateParameter_metalnessScale'] = m_res['value']
        # templateParameter_clearCoatIntensity
        m_res = getAttr(self.__m_node,'templateParameter_enable_clearCoatIntensity')
        if (m_res and 'kBoolean'==m_res['type'] and m_res['value']):
            m_res = getAttr(self.__m_node,'templateParameter_clearCoatIntensity')
            if ('kFloat'==m_res['type']):
                self.__m_mat['templateParameter_clearCoatIntensity'] = m_res['value']
        # templateParameter_clearCoatSmoothness
        m_res = getAttr(self.__m_node,'templateParameter_enable_clearCoatSmoothness')
        if (m_res and 'kBoolean'==m_res['type'] and m_res['value']):
            m_res = getAttr(self.__m_node,'templateParameter_clearCoatSmoothness')
            if ('kFloat'==m_res['type']):
                self.__m_mat['templateParameter_clearCoatSmoothness'] = m_res['value']
        # templateParameter_porosity
        m_res = getAttr(self.__m_node,'templateParameter_enable_porosity')
        if (m_res and 'kBoolean'==m_res['type'] and m_res['value']):
            m_res = getAttr(self.__m_node,'templateParameter_porosity')
            if ('kFloat'==m_res['type']):
                self.__m_mat['templateParameter_porosity'] = m_res['value']
        #
        # Find item which need to compare
        #
        self.__m_compareTo = {}
        m_itemsToCheck = ['detailDiffuse','detailNormal','detailSpecular','smoothnessScale','metalnessScale','clearCoatIntensity','clearCoatSmoothness','porosity']
        m_brandColor = None
        # brandColor
        # check if material has 'brandColor'
        if 'customParameterTemplate_brandColor_brandColor' in self.__m_mat:
            #
            # get 'brandColor' item from the library xml
            #
            #       {      'nicename': 'FENDT_NEWGREEN1',
            #              'category': 'FENDT',
            #              'fullname': 'FENDT/FENDT_NEWGREEN1',
            #          'iconFilename': '',
            #         'detailDiffuse': '',
            #          'detailNormal': '',
            #        'detailSpecular': '',
            #            'colorScale': '0.0519 0.1922 0.0196 1',
            #       'smoothnessScale': None,
            #        'metalnessScale': None,
            #    'clearCoatIntensity': None,
            #   'clearCoatSmoothness': None,
            #              'porosity': None,
            #        'parentTemplate': None,
            # 'parentTemplateDefault': 'metalPainted'    }
            #
            m_brandColor = self.__getTemplateItemByNiceName(self._brandMaterialTemplates,self.__m_mat['customParameterTemplate_brandColor_brandColor'])
            if (m_brandColor):
                self.__m_compareTo['colorScale'] = m_brandColor['colorScale']
                if m_brandColor['parentTemplate']:
                    m_brandColorTemplate = self.__getTemplateItemByNiceName(self._materialTemplates,m_brandColor['parentTemplate'])
                elif m_brandColor['parentTemplateDefault']:
                    m_brandColorTemplate = self.__getTemplateItemByNiceName(self._materialTemplates,m_brandColor['parentTemplateDefault'])
                # check parentTemplate
                for m_item in m_itemsToCheck:
                    if (not m_brandColor[m_item]):
                        self.__m_compareTo[m_item] = m_brandColorTemplate[m_item]
                    else:
                        self.__m_compareTo[m_item] = m_brandColor[m_item]
        # materialTemplate
        # check if material has 'materialTemplate'
        if 'customParameterTemplate_brandColor_material' in self.__m_mat:
            #
            # get 'material template' item from the library xml
            #

            m_brandColor = self.__getTemplateItemByNiceName(self._materialTemplates,self.__m_mat['customParameterTemplate_brandColor_material'])
            if (m_brandColor):
                for m_item in m_itemsToCheck:
                    if (m_brandColor[m_item]):
                        self.__m_compareTo[m_item] = m_brandColor[m_item]
                if ('colorScale' in self.__m_compareTo):
                    # if 'colorScale' already defined by brandColor.xml
                    # do nothing
                    pass
                else:
                    # if 'colorScale' not defined by brandColor.xml
                    if (m_brandColor['colorScale']):
                        self.__m_compareTo['colorScale'] = m_brandColor['colorScale']
        if ('colorScale' in self.__m_compareTo):
            self.__m_compareTo['colorScale'] = getXYZWFromStr(self.__m_compareTo['colorScale'])
        #
        # Update material based on the library info
        #
        if (m_brandColor):
            # colorScale
            self.__synhronizeTemplateParameter('colorScale','double3',{'x':1.0,'y':1.0,'z':1.0})
            # detailDiffuse
            self.__synhronizeTemplateParameter("detailDiffuse",'texture',None)
            # detailNormal
            self.__synhronizeTemplateParameter("detailNormal",'texture',None)
            # detailSpecular
            self.__synhronizeTemplateParameter("detailSpecular",'texture',None)
            # smoothnessScale
            self.__synhronizeTemplateParameter('smoothnessScale','float',1.0)
            # metalnessScale
            self.__synhronizeTemplateParameter('metalnessScale','float',1.0)
            # clearCoatIntensity
            self.__synhronizeTemplateParameter('clearCoatIntensity','float',0.0)
            # clearCoatSmoothness
            self.__synhronizeTemplateParameter('clearCoatSmoothness','float',0.0)
            # porosity
            self.__synhronizeTemplateParameter('porosity','float',0.0)
        else:
            if 'customParameterTemplate_brandColor_brandColor' in self.__m_mat:
                print("{} not in the library!".format(self.__m_mat['customParameterTemplate_brandColor_brandColor']))
            if 'customParameterTemplate_brandColor_material' in self.__m_mat:
                print("{} not in the library!".format(self.__m_mat['customParameterTemplate_brandColor_material']))

    def __synhronizeTemplateParameter(self,m_attrStr,m_type,m_default):
        # self.__m_node - OpenMaya.MObject() to the material node
        m_a1 = m_attrStr
        m_a2 = 'templateParameter_{}'.format(m_a1)
        m_a3 = 'templateParameter_enable_{}'.format(m_a1)
        m_a4 = 'customParameter_{}'.format(m_a1)
        connectedToStr = ''
        if (m_a1 in self.__m_compareTo and self.__m_compareTo[m_a1] is not None):
            enabledValue = getAttr(self.__m_node, m_a3)
            if enabledValue is None or enabledValue["value"] != True:
                setBoolAttr(self.__m_node, m_a3, True)

            m_update = False
            if (m_a2 in self.__m_mat):
                m_test = False
                if ('float'==m_type):
                    m_test = isEqualFloat(self.__m_mat[m_a2],self.__m_compareTo[m_a1])
                elif('double3'==m_type):
                    m_test = isEqualXYZ(self.__m_mat[m_a2],self.__m_compareTo[m_a1])
                elif('texture'==m_type):
                    connectedToStr = self.__m_mat[m_a2]['connectedTo']
                    m_test = isEqualFilePath(self.__m_mat[m_a2]['filePath'],self.__m_compareTo[m_a1])
                if (not m_test):
                    m_update = True
            else:
                m_update = True
            if (m_update):
                if ('float'==m_type):
                    setFloatAttr(self.__m_node,m_a2,self.__m_compareTo[m_a1])
                elif('double3'==m_type):
                    setDouble3Attr(self.__m_node,m_a2,self.__m_compareTo[m_a1])
                elif('texture'==m_type):
                    setTextureAttr(self.__m_node,m_a2,connectedToStr,self.__m_compareTo[m_a1])
        else:
            # this item do not exists in the library,
            # set default and turn it off
            enabledValue = getAttr(self.__m_node, m_a3)
            if enabledValue is None or enabledValue["value"] != False:
                setBoolAttr(self.__m_node, m_a3, False)

            if ('float'==m_type):
                if m_a2 in self.__m_mat and not isEqualFloat(self.__m_mat[m_a2], m_default):
                    setFloatAttr(self.__m_node, m_a2, m_default)
            elif('double3'==m_type):
                if m_a2 in self.__m_mat and not isEqualXYZ(self.__m_mat[m_a2], m_default):
                    setDouble3Attr(self.__m_node, m_a2, m_default)

        attributTemplate = getAttr(self.__m_node, "customParameter_template_" + m_attrStr)
        if attributTemplate is not None:
            attributTemplateName = attributTemplate["value"]
            materialTemplate = self.__getTemplateItemByNiceName(self._brandMaterialTemplates, attributTemplateName.split(" ")[0])
            if m_attrStr in materialTemplate:
                if ('float'==m_type):
                    curAttr = getAttr(self.__m_node, m_a4)
                    if curAttr is None or not isEqualFloat(curAttr["value"], materialTemplate[m_attrStr]):
                        setFloatAttr(self.__m_node, m_a4, materialTemplate[m_attrStr])
                elif('double3'==m_type):
                    attr = getXYZWFromStr(materialTemplate[m_attrStr])
                    curAttr = getAttr(self.__m_node, m_a4)
                    if curAttr is None or not isEqualXYZ(curAttr["data"], attr):
                        setDouble3Attr(self.__m_node, m_a4, attr)

class commonUVSetNames():
    def __init__(self):
        self.__dict = {} # __dict['uv0'], __dict['uv1'], __dict['uv2']

    def addNames(self,m_uvSetNames):
        for i in range(len(m_uvSetNames)):
            m_name = 'uv{}'.format(i)
            if not m_name in self.__dict:
                self.__dict[m_name] = {} # dict of the names
            m_uvs = self.__dict[m_name]
            m_str = m_uvSetNames[i]
            if (m_str in m_uvs):
                m_uvs[m_str] += 1
            else:
                m_uvs[m_str] = 1
            self.__dict[m_name] = m_uvs

    def __getItem(self,m_uvStr,m_uvDefStr):
        m_out = m_uvDefStr
        if (m_uvStr in self.__dict):
            m_amount = 0
            for k,v in self.__dict[m_uvStr].items():
                if (v > m_amount):
                    m_amount = v
                    m_out = k
        return m_out

    @property
    def uv0(self):
        return self.__getItem('uv0','map1')

    @property
    def uv1(self):
        return self.__getItem('uv1','map2')

    @property
    def uv2(self):
        return self.__getItem('uv2','map3')

    def __str__(self):
        # {'uv0': {'map1': 190}, 'uv1': {'uvSet': 40, 'uvSet1': 1}, 'uv2': {'uvSet1': 24, 'uvSet2': 1}, 'uv3': {'map4': 1}}
        return "{}".format(self.__dict)

def getShapeUVSetNames(m_path):
    # m_path is a OpenMaya.MDagPath() to OpenMaya.MFn.kMesh
    # make sure that we work with shape, otherwise we can't use OpenMaya.MFnMesh
    # m_path.extendToShape() should be done before
    m_uvSetNames = []
    if ( m_path.apiType() == OpenMaya.MFn.kMesh ):
        m_meshFn = OpenMaya.MFnMesh( m_path )
        m_meshFn.getUVSetNames(m_uvSetNames)
    return m_uvSetNames

def getShapeUVindexes(m_path):
    # m_path is a OpenMaya.MDagPath() to OpenMaya.MFn.kMesh
    # make sure that we work with shape, otherwise we can't use OpenMaya.MFnMesh
    # m_path.extendToShape() should be done before
    m_shapeUVs = {}
    if ( m_path.apiType() == OpenMaya.MFn.kMesh ):
        m_meshFn = OpenMaya.MFnMesh( m_path )
        m_uvSetNames = []
        m_meshFn.getUVSetNames(m_uvSetNames)
        if len(m_uvSetNames) > 0:
            m_uvSetName = m_uvSetNames[0] # use 0 uvSet name as source for the uv indexes
            m_tempFaceIt = OpenMaya.MItMeshPolygon( m_path )
            while not m_tempFaceIt.isDone(): # iterate
                '''
                for m_localVertId in range(m_tempFaceIt.polygonVertexCount()):
                    m_util = OpenMaya.MScriptUtil()
                    m_util.createFromList([0.0, 0.0], 2)
                    m_uvPoint = m_util.asFloat2Ptr()
                    m_tempFaceIt.getUV(m_localVertId,m_uvPoint,m_uvSetName)
                    m_u = OpenMaya.MScriptUtil.getFloat2ArrayItem(m_uvPoint, 0, 0) # x
                    m_v = OpenMaya.MScriptUtil.getFloat2ArrayItem(m_uvPoint, 0, 1) # y
                    print(m_tempFaceIt.index(),m_localVertId, m_u, m_v )
                '''
                # use default in case there is no uv's
                m_u = 0.5
                m_v = 0.5
                # try to get uv's, if not use default
                try:
                    # Tests whether this face has UV's mapped or not (either all the vertices for a face should have UV's, or none of them do, so the UV count for a face is either 0, or equal to the number of vertices).
                    if (m_tempFaceIt.hasUVs()):
                        m_util = OpenMaya.MScriptUtil()
                        m_util.createFromList([0.0, 0.0], 2)
                        m_uvPoint = m_util.asFloat2Ptr()
                        #
                        # use 0 local index
                        # assumption that all other vertices of the polygon in the same uv index
                        #
                        # MStatus MItMeshPolygon::getUV ( int vertex, float2 & uvPoint,const MString * uvSet = NULL)
                        # Return the texture coordinate for the given vertex.
                        # vertex  - The face-relative vertex index to get UV for, The vertex index must be less than polygonVertexCount() and must also be mapped by the specified uvSet.
                        # uvPoint - Storage for u and v values
                        # uvSet   - UV set to work with
                        m_tempFaceIt.getUV(0,m_uvPoint,m_uvSetName)
                        m_u = OpenMaya.MScriptUtil.getFloat2ArrayItem(m_uvPoint, 0, 0) # x
                        m_v = OpenMaya.MScriptUtil.getFloat2ArrayItem(m_uvPoint, 0, 1) # y
                except:
                    pass
                if (m_v < 0):
                    m_index = max(0, min(int(m_u), 7))
                    m_key = "colorMat{}".format(int(m_index))
                else:
                    m_index = max(0, math.floor(m_u) + 8*math.floor(m_v))
                    m_key = "{}".format(m_index)
                if (m_key in m_shapeUVs):
                    m_list = m_shapeUVs[m_key]
                else:
                    m_list = []
                m_list.append(m_tempFaceIt.index())
                m_shapeUVs[m_key] = m_list
                m_tempFaceIt.next()
    # m_shapeUVs == {'colorMat0': [0, 4, 5], '0': [1, 2, 3]}
    #
    # make a short List of strings instead of just a list of int indexes
    #
    m_out = {}
    for k,v in m_shapeUVs.items():
        m_aMemberList = polyIdListToStrList(m_shapeUVs[k])
        m_out[k] = m_aMemberList
    # m_out == {'colorMat0': ['0:0', '4:5'], '0': ['1:3']}
    return m_out

def polyIdListToStrList(m_list):
    m_aMemberList = []
    #m_aMember     = ''
    m_lastIndices = [ -1, -1 ]
    m_haveFace    = False
    for m_faceId in m_list:
        if ( -1 == m_lastIndices[0] ):
            m_lastIndices[0] = m_faceId
            m_lastIndices[1] = m_faceId
        else:
            m_currentIndex = m_faceId
            if ( m_currentIndex > m_lastIndices[1] + 1 ):
                #m_aMember += '{}.f[{}:{}] '.format( m_path.fullPathName(), m_lastIndices[0], m_lastIndices[1] )
                m_aMemberList.append('{}:{}'.format(m_lastIndices[0],m_lastIndices[1]))
                m_lastIndices[0] = m_currentIndex
                m_lastIndices[1] = m_currentIndex
            else:
                m_lastIndices[1] = m_currentIndex
        m_haveFace = True
    if ( m_haveFace ):
        #m_aMember += '{}.f[{}:{}] '.format( m_path.fullPathName(), m_lastIndices[0], m_lastIndices[1] )
        m_aMemberList.append('{}:{}'.format(m_lastIndices[0],m_lastIndices[1]))
    return m_aMemberList

def getShapeShadingGroupsAsList(m_path):
    # m_path is a OpenMaya.MDagPath() to OpenMaya.MFn.kMesh
    # make sure that we work with shape, otherwise we can't use OpenMaya.MFnMesh
    # m_path.extendToShape() should be done before
    m_listShadingGroups = []
    # ideally should always happen
    if ( m_path.apiType() == OpenMaya.MFn.kMesh ):
        try:
            m_meshFn = OpenMaya.MFnMesh( m_path )
            m_sets  = OpenMaya.MObjectArray()
            m_comps = OpenMaya.MObjectArray()
            m_instanceNumber = m_path.instanceNumber()
            m_renderableSetsOnly = 1
            # m_instanceNumber     - the instance number of the mesh to query
            # m_sets               - storage for the sets
            # m_comps              - storage for the components that are in the corresponding set
            # m_renderableSetsOnly - if true then this method will only return renderable sets
            m_meshFn.getConnectedSetsAndMembers( m_instanceNumber, m_sets, m_comps, m_renderableSetsOnly )
            if (0 == m_sets.length()):
                m_listShadingGroups.clear()
                m_listShadingGroups.append('initialShadingGroup')
                return m_listShadingGroups
            elif (1 == m_sets.length()):
                m_sefFn = OpenMaya.MFnSet( m_sets[0] )
                # return empty list if shape has only 1 ShadingGroup assigned
                # all polygons are in the same ShadingGroup
                m_listShadingGroups.clear()
                m_listShadingGroups.append(m_sefFn.name())
                return m_listShadingGroups
            else:
                m_listShadingGroups.clear()
                m_ind = 0
                while ( m_ind < m_sets.length()):
                    m_sefFn = OpenMaya.MFnSet( m_sets[ m_ind ] )
                    m_listShadingGroups.append(m_sefFn.name())
                    m_ind += 1
                return m_listShadingGroups
        except RuntimeError:
            print("Unable to get shading groups from object '%s'" % m_path.fullPathName())
    return m_listShadingGroups

def getMaterialFromShadingGroup(m_sgStr):
    # m_sgStr - string name of the shadingGroup
    m_obj = getMObjectFromNodeName(m_sgStr)
    if m_obj:
        m_nodeFn = OpenMaya.MFnDependencyNode(m_obj)
        if (m_nodeFn.hasAttribute("surfaceShader")):
            m_plug = m_nodeFn.findPlug( "surfaceShader" )
            m_plugArrayConnected = OpenMaya.MPlugArray()
            m_plug.connectedTo( m_plugArrayConnected, True, False )
            for i in range( m_plugArrayConnected.length() ):
                m_plugConnected   = m_plugArrayConnected[i]
                m_nodeConnected   = m_plugConnected.node()
                m_nodeFnConnected = OpenMaya.MFnDependencyNode( m_nodeConnected )
                return m_nodeFnConnected.name()
    return 'lambert1'

def getMObjectFromNodeName( m_node_name ):
    m_selectionList = OpenMaya.MSelectionList()
    m_node = OpenMaya.MObject()
    try:
        m_selectionList.add(m_node_name)
        m_selectionList.getDependNode(0, m_node)
    except:
        return None
    return m_node

def isEqualFilePath(a,b):
    # compare two filepaths
    a1 = os.path.normcase(os.path.normpath(str(a)))
    b1 = os.path.normcase(os.path.normpath(str(b)))
    if (a1 == b1):
        return True
    else:
        return False

def isEqualXYZ(a,b):
    # compare two dicts with 'x','y','z' float values
    m_out = True
    keys = ['x', 'y', 'z']
    for key in keys:
        if ((key in a) and (key in b)):
            if (not isEqualFloat(a[key],b[key])):
                m_out = False
        else:
            m_out = False
    return m_out

def isEqualFloat(a,b):
    return isCloseFloat(float(a),float(b),0.001)

def isCloseFloat(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def getXYZWFromStr(m_str):
    # m_str - string like: "0.027 0.025 0.023 1"
    # m_out - dict with 'x','y','z','w' as keys and floats as values
    m_out = {'x': 0, 'y': 0, 'z': 0, 'w': 0}
    if m_str is None:
        return m_out
    keys = ['x', 'y', 'z', 'w']
    value = str(m_str).split()
    m_out = {keys[i]: float(value[i]) for i in range(min(len(value), 4))}
    return m_out

def setTextureAttr(m_node,m_attrNameStr,connectedToStr,value):
    # m_node - OpenMaya.MObject() to the material node
    m_nodeFn = OpenMaya.MFnDependencyNode()
    m_nodeFn.setObject( m_node )
    matInstance = m_nodeFn.name()
    if (m_nodeFn.hasAttribute(m_attrNameStr)):
        if ('' == connectedToStr):
            # attribute exists but texture is not connected
            # do nothing
            pass
        else:
            # break already existing connection
            attribute = '{}.{}'.format(matInstance,m_attrNameStr)
            cmds.setAttr(attribute, lock=0)
            cmds.disconnectAttr(connectedToStr, attribute)
            #print("Disconnected: {} from {}.{}".format(connectedToStr,matInstance,m_attrNameStr))
        # 'create/use existing' fileTextureNode and connect it
        I3DUtils.createAndConnectTexture(matInstance,value,m_attrNameStr)

def setEnumAttr(m_node,m_attrNameStr,value):
    # m_node - OpenMaya.MObject() to the material node
    m_nodeFn = OpenMaya.MFnDependencyNode()
    m_nodeFn.setObject( m_node )
    matInstance = m_nodeFn.name()
    if (m_nodeFn.hasAttribute(m_attrNameStr)):
        cmds.setAttr("{}.{}".format(matInstance,m_attrNameStr),int(value))
        print("Set: {}.{} to {}".format(matInstance,m_attrNameStr,int(value)))

def setStringAttr(m_node,m_attrNameStr,value):
    # m_node - OpenMaya.MObject() to the material node
    m_nodeFn = OpenMaya.MFnDependencyNode()
    m_nodeFn.setObject( m_node )
    matInstance = m_nodeFn.name()
    if (m_nodeFn.hasAttribute(m_attrNameStr)):
        cmds.setAttr("{}.{}".format(matInstance,m_attrNameStr), str(value), type='string')
        print("Set: {}.{} to {}".format(matInstance,m_attrNameStr,str(value)))

def setDouble3Attr(m_node,m_attrNameStr,value):
    # m_node - OpenMaya.MObject() to the material node
    m_nodeFn = OpenMaya.MFnDependencyNode()
    m_nodeFn.setObject( m_node )
    matInstance = m_nodeFn.name()
    if (m_nodeFn.hasAttribute(m_attrNameStr)):
        cmds.setAttr("{}.{}".format(matInstance,m_attrNameStr),float(value['x']),float(value['y']),float(value['z']),type="double3")
        print("Set: {}.{} to {},{},{}".format(matInstance,m_attrNameStr,float(value['x']),float(value['y']),float(value['z'])))

def setBoolAttr(m_node,m_attrNameStr,value):
    # m_node - OpenMaya.MObject() to the material node
    m_nodeFn = OpenMaya.MFnDependencyNode()
    m_nodeFn.setObject( m_node )
    matInstance = m_nodeFn.name()
    if (m_nodeFn.hasAttribute(m_attrNameStr)):
        cmds.setAttr("{}.{}".format(matInstance,m_attrNameStr), bool(value))
        print("Set: {}.{} to {}".format(matInstance,m_attrNameStr,bool(value)))

def setFloatAttr(m_node,m_attrNameStr,value):
    # m_node - OpenMaya.MObject() to the material node
    m_nodeFn = OpenMaya.MFnDependencyNode()
    m_nodeFn.setObject( m_node )
    matInstance = m_nodeFn.name()
    if (m_nodeFn.hasAttribute(m_attrNameStr)):
        cmds.setAttr("{}.{}".format(matInstance,m_attrNameStr),float(value))
        print("Set: {}.{} to {}".format(matInstance,m_attrNameStr,float(value)))

def getAttr(m_node,m_attrNameStr):
    # m_node - OpenMaya.MObject() to the material node
    m_nodeFn = OpenMaya.MFnDependencyNode()
    m_nodeFn.setObject( m_node )
    if (m_nodeFn.hasAttribute(m_attrNameStr)):
        m_attrPlug = m_nodeFn.findPlug(m_attrNameStr)
        value = getValue(m_attrPlug)
        #value = cmds.getAttr("{}.{}".format(m_nodeFn.name(),m_attrNameStr))
        return value
    return None

def getBumpTextureStr( m_node ):
    # m_node - OpenMaya.MObject() to the bump2d node
    m_plugFn = OpenMaya.MFnDependencyNode(m_node)
    m_attrPlug = m_plugFn.findPlug("bumpValue")
    m_plugArrayConnected  = OpenMaya.MPlugArray()
    m_attrPlug.connectedTo( m_plugArrayConnected, True, True )
    for j in range( m_plugArrayConnected.length() ):
        m_plugConnected     = m_plugArrayConnected[j]
        m_plugConnectedNode = m_plugConnected.node()
        m_plugConnectedNodeFn = OpenMaya.MFnDependencyNode(m_plugConnectedNode)
        m_textureNamePlug = m_plugConnectedNodeFn.findPlug("fileTextureName")
        return m_textureNamePlug.asString()
    return None

def getValue( m_attrPlug ):
    # m_attrPlug - OpenMaya.MPlug() to OpenMaya.MObject() material and OpenMaya.MObject() attribute
    m_out = {}
    m_out['type'] = "kUnknown"
    m_out['value'] = None
    m_out['data'] = None
    try:
        m_atrr = m_attrPlug.attribute()
        #print(m_atrr.apiTypeStr(),m_attrPlug.name())
        if ( m_attrPlug.isDestination() ):
            m_list  = []
            m_plugArrayConnected = OpenMaya.MPlugArray()
            m_attrPlug.connectedTo( m_plugArrayConnected, True, True )
            for j in range( m_plugArrayConnected.length() ):
                m_plugConnected = m_plugArrayConnected[j]
                m_addStr1       = m_plugConnected.info()
                m_plugConnectedNode = m_plugConnected.node()
                m_plugConnectedNodeFn = OpenMaya.MFnDependencyNode(m_plugConnectedNode)
                m_addStr2 = ""
                if ('kBump' == m_plugConnectedNode.apiTypeStr() ):
                    m_addStr2 = getBumpTextureStr( m_plugConnectedNode )
                if ('kFileTexture' == m_plugConnectedNode.apiTypeStr()):
                    m_addStr2 = m_plugConnectedNodeFn.findPlug("fileTextureName").asString()
                m_list.append( (m_addStr1,m_addStr2) )
            m_out['type'] = "isDestination"
            m_out['value'] = m_list
            if (len(m_list)>0):
                m_strNode, m_strFilePath = m_list[0]
                m_out['data'] = {}
                m_out['data']['connectedTo'] = m_strNode
                m_out['data']['filePath'] = m_strFilePath
            return m_out
        elif ( m_attrPlug.isCompound() ):
            m_out['type'] = "isCompound"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            value = m_out['value'][0]
            m_out['data'] = {'x': None, 'y': None, 'z': None, 'w': None}
            keys = ['x', 'y', 'z', 'w']
            m_out['data'] = {keys[i]: float(value[i]) for i in range(min(len(value), 4))}
            return m_out
        elif ( m_attrPlug.isArray() ):
            m_out['type'] = "isArray"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kCompoundAttribute == m_atrr.apiType() ):
            m_out['type'] = "kCompoundAttribute"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kTimeAttribute == m_atrr.apiType() ):
            m_out['type'] = "kTimeAttribute"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kEnumAttribute          == m_atrr.apiType() ):
            m_fnEnum = OpenMaya.MFnEnumAttribute( m_atrr )
            m_util   = OpenMaya.MScriptUtil()
            m_ptr    = m_util.asShortPtr()
            m_fnEnum.getMin( m_ptr )
            m_min    = m_util.getShort( m_ptr )
            m_fnEnum.getMax( m_ptr )
            m_max    = m_util.getShort( m_ptr )
            m_list  = []
            for i in range( m_min, ( m_max + 1) ):
                m_list.append( m_fnEnum.fieldName(i) )
            m_out['type'] = "kEnumAttribute"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            m_out['data'] = m_list
            return m_out
        elif ( OpenMaya.MFn.kUnitAttribute == m_atrr.apiType() ):
            m_out['type'] = "kUnitAttribute"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kGenericAttribute == m_atrr.apiType() ):
            m_out['type'] = "kGenericAttribute"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kLightDataAttribute == m_atrr.apiType() ):
            m_out['type'] = "kLightDataAttribute"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kMatrixAttribute == m_atrr.apiType() ):
            m_out['type'] = "kMatrixAttribute"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kFloatMatrixAttribute == m_atrr.apiType() ):
            m_out['type'] = "kFloatMatrixAttribute"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kMessageAttribute == m_atrr.apiType() ):
            m_out['type'] = "kMessageAttribute"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kToonLineAttributes == m_atrr.apiType() ):
            m_out['type'] = "kToonLineAttributes"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kTransferAttributes == m_atrr.apiType() ):
            m_out['type'] = "kTransferAttributes"
            m_out['value'] = cmds.getAttr( m_attrPlug.info() )
            return m_out
        elif ( OpenMaya.MFn.kAttribute3Double == m_atrr.apiType() ):
            m_out['type'] = "kAttribute3Double"
            m_out['value'] = [ m_attrPlug.child(0).asDouble(), m_attrPlug.child(1).asDouble(), m_attrPlug.child(2).asDouble()]
            return m_out
        elif ( OpenMaya.MFn.kAttribute3Float == m_atrr.apiType() ):
            m_out['type'] = "kAttribute3Float"
            m_out['value'] = [ m_attrPlug.child(0).asFloat(), m_attrPlug.child(1).asFloat(), m_attrPlug.child(2).asFloat()]
            return m_out
        elif ( OpenMaya.MFn.kAttribute3Int == m_atrr.apiType() ):
            m_out['type'] = "kAttribute3Int"
            m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt(), m_attrPlug.child(2).asInt()]
            return m_out
        elif ( OpenMaya.MFn.kAttribute3Short == m_atrr.apiType() ):
            m_out['type'] = "kAttribute3Short"
            m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt(), m_attrPlug.child(2).asInt()]
            return m_out
        elif ( OpenMaya.MFn.kAttribute3Long == m_atrr.apiType() ):
            m_out['type'] = "kAttribute3Long"
            m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt(), m_attrPlug.child(2).asInt()]
            return m_out
        elif ( OpenMaya.MFn.kAttribute2Double == m_atrr.apiType() ):
            m_out['type'] = "kAttribute2Double"
            m_out['value'] = [ m_attrPlug.child(0).asDouble(), m_attrPlug.child(1).asDouble()]
            return m_out
        elif ( OpenMaya.MFn.kAttribute2Float == m_atrr.apiType() ):
            m_out['type'] = "kAttribute2Float"
            m_out['value'] = [ m_attrPlug.child(0).asFloat(), m_attrPlug.child(1).asFloat()]
            return m_out
        elif ( OpenMaya.MFn.kAttribute2Int == m_atrr.apiType() ):
            m_out['type'] = "kAttribute2Int"
            m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt() ]
            return m_out
        elif ( OpenMaya.MFn.kAttribute2Short == m_atrr.apiType() ):
            m_out['type'] = "kAttribute2Short"
            m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt() ]
            return m_out
        elif ( OpenMaya.MFn.kAttribute2Long == m_atrr.apiType() ):
            m_out['type'] = "kAttribute2Long"
            m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt() ]
            return m_out
        elif ( OpenMaya.MFn.kAttribute4Double == m_atrr.apiType() ):
            m_out['type'] = "kAttribute4Double"
            m_out['value'] = [ m_attrPlug.child(0).asDouble(), m_attrPlug.child(1).asDouble(), m_attrPlug.child(2).asDouble(), m_attrPlug.child(3).asDouble() ]
            return m_out
        elif ( OpenMaya.MFn.kDoubleLinearAttribute == m_atrr.apiType() ):
            m_out['type'] = "kDoubleLinearAttribute"
            m_out['value'] = m_attrPlug.asMDistance().asCentimeters()
            return m_out
        elif ( OpenMaya.MFn.kFloatLinearAttribute == m_atrr.apiType() ):
            m_out['type'] = "kFloatLinearAttribute"
            m_out['value'] = m_attrPlug.asMDistance().asCentimeters()
            return m_out
        elif ( OpenMaya.MFn.kDoubleAngleAttribute == m_atrr.apiType() ):
            m_out['type'] = "kDoubleAngleAttribute"
            m_out['value'] = m_attrPlug.asMAngle().asDegrees()
            return m_out
        elif ( OpenMaya.MFn.kFloatAngleAttribute == m_atrr.apiType() ):
            m_out['type'] = "kFloatAngleAttribute"
            m_out['value'] = m_attrPlug.asMAngle().asDegrees()
            return m_out
        elif ( OpenMaya.MFn.kTypedAttribute == m_atrr.apiType() ):
            m_fnType = OpenMaya.MFnTypedAttribute( m_atrr )
            if   ( OpenMaya.MFnData.kAny == m_fnType.attrType() ):
                m_out['type'] = "kAny"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kComponentList == m_fnType.attrType() ):
                m_out['type'] = "kComponentList"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kDoubleArray == m_fnType.attrType() ):
                m_out['type'] = "kDoubleArray"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kDynArrayAttrs == m_fnType.attrType() ):
                m_out['type'] = "kDynArrayAttrs"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kDynSweptGeometry == m_fnType.attrType() ):
                m_out['type'] = "kDynSweptGeometry"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kFloatArray == m_fnType.attrType() ):
                m_out['type'] = "kFloatArray"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kIntArray == m_fnType.attrType() ):
                m_out['type'] = "kIntArray"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kInvalid == m_fnType.attrType() ):
                m_out['type'] = "kInvalid"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kLast == m_fnType.attrType() ):
                m_out['type'] = "kLast"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kLattice == m_fnType.attrType() ):
                m_out['type'] = "kLattice"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kMatrix == m_fnType.attrType() ):
                m_out['type'] = "kMatrix"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                m_out['data'] = OpenMaya.MFnMatrixData( m_attrPlug.asMObject() ).matrix()
                return m_out
            elif ( OpenMaya.MFnData.kMatrixArray == m_fnType.attrType() ):
                m_out['type'] = "kMatrixArray"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kMesh == m_fnType.attrType() ):
                m_out['type'] = "kMesh"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kNId == m_fnType.attrType() ):
                m_out['type'] = "kNId"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kNObject == m_fnType.attrType() ):
                m_out['type'] = "kNObject"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kNumeric  == m_fnType.attrType() ):
                m_out['type'] = "kNumeric"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kNurbsCurve == m_fnType.attrType() ):
                m_out['type'] = "kNurbsCurve"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kNurbsSurface == m_fnType.attrType() ):
                m_out['type'] = "kNurbsSurface"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kPluginGeometry == m_fnType.attrType() ):
                m_out['type'] = "kPluginGeometry"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kPointArray == m_fnType.attrType() ):
                m_out['type'] = "kPointArray"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kSphere  == m_fnType.attrType() ):
                m_out['type'] = "kSphere"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kString == m_fnType.attrType() ):
                m_out['type'] = "kString"
                m_out['value'] = m_attrPlug.asString()
                return m_out
            elif ( OpenMaya.MFnData.kStringArray == m_fnType.attrType() ):
                m_out['type'] = "kStringArray"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kSubdSurface == m_fnType.attrType() ):
                m_out['type'] = "kSubdSurface"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnData.kVectorArray == m_fnType.attrType() ):
                m_out['type'] = "kVectorArray"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
        elif ( OpenMaya.MFn.kNumericAttribute == m_atrr.apiType() ):
            m_fnNum = OpenMaya.MFnNumericAttribute( m_atrr )
            if   ( OpenMaya.MFnNumericData.kInvalid == m_fnNum.unitType() ):
                m_out['type'] = "kInvalid"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
            elif ( OpenMaya.MFnNumericData.kBoolean == m_fnNum.unitType() ):
                m_out['type'] = "kBoolean"
                m_out['value'] = m_attrPlug.asBool()
                return m_out
            elif ( OpenMaya.MFnNumericData.kByte == m_fnNum.unitType() ):
                m_out['type'] = "kByte"
                m_out['value'] = m_attrPlug.asInt()
                return m_out
            elif ( OpenMaya.MFnNumericData.kChar == m_fnNum.unitType() ):
                m_out['type'] = "kChar"
                m_out['value'] = m_attrPlug.asChar()
                return m_out
            elif ( OpenMaya.MFnNumericData.kShort == m_fnNum.unitType() ):
                m_out['type'] = "kShort"
                m_out['value'] = m_attrPlug.asInt()
                return m_out
            elif ( OpenMaya.MFnNumericData.k2Short == m_fnNum.unitType() ):
                m_out['type'] = "k2Short"
                m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt() ]
                return m_out
            elif ( OpenMaya.MFnNumericData.k3Short == m_fnNum.unitType() ):
                m_out['type'] = "k3Short"
                m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt(), m_attrPlug.child(2).asInt()]
                return m_out
            elif ( OpenMaya.MFnNumericData.kLong == m_fnNum.unitType() ):
                m_out['type'] = "kLong"
                m_out['value'] = m_attrPlug.asInt()
                return m_out
            elif ( OpenMaya.MFnNumericData.kInt == m_fnNum.unitType() ):
                m_out['type'] = "kInt"
                m_out['value'] = m_attrPlug.asInt()
                return m_out
            elif ( OpenMaya.MFnNumericData.k2Long == m_fnNum.unitType() ):
                m_out['type'] = "k2Long"
                m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt() ]
                return m_out
            elif ( OpenMaya.MFnNumericData.k2Int == m_fnNum.unitType() ):
                m_out['type'] = "k2Int"
                m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt() ]
                return m_out
            elif ( OpenMaya.MFnNumericData.k3Long == m_fnNum.unitType() ):
                m_out['type'] = "k3Long"
                m_out['value'] = [ m_attrPlug.child(0).asInt(), m_attrPlug.child(1).asInt(), m_attrPlug.child(2).asInt() ]
                return m_out
            elif ( OpenMaya.MFnNumericData.k3Int == m_fnNum.unitType() ):
                m_out['type'] = "k3Int"
                m_out['value'] = [ m_attrPlug.child(0).asInt(),   m_attrPlug.child(1).asInt(), m_attrPlug.child(2).asInt() ]
                return m_out
            elif ( OpenMaya.MFnNumericData.kFloat == m_fnNum.unitType() ):
                m_out['type'] = "kFloat"
                m_out['value'] = m_attrPlug.asFloat()
                return m_out
            elif ( OpenMaya.MFnNumericData.k2Float == m_fnNum.unitType() ):
                m_out['type'] = "k2Float"
                m_out['value'] = [ m_attrPlug.child(0).asFloat(), m_attrPlug.child(1).asFloat() ]
                return m_out
            elif ( OpenMaya.MFnNumericData.k3Float == m_fnNum.unitType() ):
                m_out['type'] = "k3Float"
                m_out['value'] = [ m_attrPlug.child(0).asFloat(), m_attrPlug.child(1).asFloat(), m_attrPlug.child(2).asFloat() ]
                return m_out
            elif ( OpenMaya.MFnNumericData.kDouble == m_fnNum.unitType() ):
                m_out['type'] = "kDouble"
                m_out['value'] = m_attrPlug.asDouble()
                return m_out
            elif ( OpenMaya.MFnNumericData.k2Double == m_fnNum.unitType() ):
                m_out['type'] = "k2Double"
                m_out['value'] = [ m_attrPlug.child(0).asDouble(), m_attrPlug.child(1).asDouble() ]
                return m_out
            elif ( OpenMaya.MFnNumericData.k3Double == m_fnNum.unitType() ):
                m_out['type'] = "k3Double"
                m_out['value'] = [ m_attrPlug.child(0).asDouble(), m_attrPlug.child(1).asDouble(), m_attrPlug.child(2).asDouble() ]
                return m_out
            elif ( OpenMaya.MFnNumericData.k4Double == m_fnNum.unitType() ):
                m_out['type'] = "k4Double"
                m_out['value'] = [ m_attrPlug.child(0).asDouble(), m_attrPlug.child(1).asDouble(), m_attrPlug.child(2).asDouble(), m_attrPlug.child(3).asDouble()]
                return m_out
            elif ( OpenMaya.MFnNumericData.kAddr == m_fnNum.unitType() ):
                m_out['type'] = "kAddr"
                m_out['value'] = m_attrPlug.asDouble()
                return m_out
            elif ( OpenMaya.MFnNumericData.kLast == m_fnNum.unitType() ):
                m_out['type'] = "kLast"
                m_out['value'] = cmds.getAttr( m_attrPlug.info() )
                return m_out
        else:
            m_out['value'] = m_attrPlug.asMObject()
            return m_out
    except:
        m_out['type'] = 'kError'
        return m_out
    return m_out
#
#   SCRIPT     vehicleShaderDebug.py
#   AUTHOR     Evgen Zaitsev
#
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import os
import I3DUtils

UI_WIDTH = 400
UI_HEIGHT = 600
GUI_ID = "vehicleShaderDebugUI"

class materialDebugWin():
    def __init__(self):
        # Load the plugin if not loaded
        if not cmds.pluginInfo('glslShader',query=True,loaded=True):
            cmds.loadPlugin('glslShader')
        debugModes = "none:baseColor:diffuse:alpha:normal:tangentSpaceNormal:smoothness:ambientOcclusion:specularOcclusion:metalness:lighting:envMapDiffuseColor:envMapSpecularColor:indirectLighting:vtxColor:vtxAlpha:emissiveColor:isWetActivated"
        self._debugModesList = debugModes.split(':')
        self._lightStates = ['static','blinking','multiBlink','slide']
        self._lightColors = []
        for i in range(64):
            self._lightColors.append("{} / 64".format(i))
        self.__uiCreate()

    def __uiCreate(self):
        if cmds.window(GUI_ID, exists=True):
            cmds.deleteUI(GUI_ID)
        self._ui_window = cmds.window(GUI_ID, title="Vehicle Shader Debug", widthHeight=(UI_WIDTH, UI_HEIGHT), sizeable=True)
        self._ui_formLayout = cmds.formLayout(parent=self._ui_window )
        self._ui_scratches = cmds.floatSliderGrp(parent=self._ui_formLayout, label='scratches',field=True,minValue=0.0,maxValue=1.0,fieldMinValue=0.0,fieldMaxValue=1.0,value=0.0,step=0.01,
            changeCommand=lambda *args:self.__uiCallback("_ui_scratches_changed",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_scratches_changed",args))
        self._ui_dirt = cmds.floatSliderGrp(parent=self._ui_formLayout, label='dirt',field=True,minValue=0.0,maxValue=1.0,fieldMinValue=0.0,fieldMaxValue=1.0,value=0.0,step=0.01,
            changeCommand=lambda *args:self.__uiCallback("_ui_dirt_changed",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_dirt_changed",args))
        self._ui_snow = cmds.floatSliderGrp(parent=self._ui_formLayout, label='snow',field=True,minValue=0.0,maxValue=1.0,fieldMinValue=0.0,fieldMaxValue=1.0,value=0.0,step=0.01,
            changeCommand=lambda *args:self.__uiCallback("_ui_snow_changed",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_snow_changed",args))
        self._ui_scrollPosX = cmds.floatSliderGrp(parent=self._ui_formLayout, label='scrollPosX',field=True,minValue=-2.0,maxValue=2.0,fieldMinValue=-2.0,fieldMaxValue=2.0,value=0.0,step=0.01,
            changeCommand=lambda *args:self.__uiCallback("_ui_scrollPosX_changed",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_scrollPosX_changed",args))
        self._ui_debugMode = cmds.optionMenuGrp(parent=self._ui_formLayout, cw2=(140,140),label="debugMode",
            changeCommand=lambda *args:self.__uiCallback("_ui_debugMode_changed",args))
        for debugMode in self._debugModesList:
            cmds.menuItem(label=debugMode)
        # ---------------------------------------------------------------------------------------------------------------
        self._ui_export_lightIds0 = cmds.checkBoxGrp( parent=self._ui_formLayout, numberOfCheckBoxes=1, label='', label1='export lightIds0', v1=False,
            changeCommand=lambda *args:self.__uiCallback("_ui_export_lightIds0",args))
        self._ui_lightIds0 = cmds.floatFieldGrp( parent=self._ui_formLayout, numberOfFields=4, label='lightIds0', value=[0.0,0.0,0.0,0.0],step=0.01,
            changeCommand=lambda *args:self.__uiCallback("_ui_lightIds0",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_lightIds0",args))
        #
        self._ui_lightTypeBitMask_dscTxt0 = cmds.text( label='function', w=140, align="right" )
        self._ui_lightTypeBitMask_b1 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        self._ui_lightTypeBitMask_b2 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        self._ui_lightTypeBitMask_b3 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        self._ui_lightTypeBitMask_b4 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        #
        self._ui_lightUvOffsetBitMask_dscTxt0 = cmds.text( label='uv offset', w=140, align="right" )
        self._ui_lightUvOffsetBitMask_b1 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightUvOffsetBitMask_bits",args))
        for lightColor in self._lightColors:
            cmds.menuItem( label=lightColor )
        self._ui_lightUvOffsetBitMask_b2 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightUvOffsetBitMask_bits",args))
        for lightColor in self._lightColors:
            cmds.menuItem( label=lightColor )
        self._ui_lightUvOffsetBitMask_b3 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightUvOffsetBitMask_bits",args))
        for lightColor in self._lightColors:
            cmds.menuItem( label=lightColor )
        self._ui_lightUvOffsetBitMask_b4 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightUvOffsetBitMask_bits",args))
        for lightColor in self._lightColors:
            cmds.menuItem( label=lightColor )
        # ---------------------------------------------------------------------------------------------------------------
        self._ui_export_lightIds1 = cmds.checkBoxGrp( parent=self._ui_formLayout, numberOfCheckBoxes=1, label='', label1='export lightIds1', v1=False,
            changeCommand=lambda *args:self.__uiCallback("_ui_export_lightIds1",args))
        self._ui_lightIds1 = cmds.floatFieldGrp( parent=self._ui_formLayout, numberOfFields=4, label='lightIds1', value=[0.0,0.0,0.0,0.0],step=0.01,
            changeCommand=lambda *args:self.__uiCallback("_ui_lightIds1",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_lightIds1",args))
        #
        self._ui_lightTypeBitMask_dscTxt1 = cmds.text( label='function', w=140, align="right" )
        self._ui_lightTypeBitMask_b5 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        self._ui_lightTypeBitMask_b6 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        self._ui_lightTypeBitMask_b7 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        self._ui_lightTypeBitMask_b8 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        # ---------------------------------------------------------------------------------------------------------------
        self._ui_export_lightIds2 = cmds.checkBoxGrp( parent=self._ui_formLayout, numberOfCheckBoxes=1, label='', label1='export lightIds2', v1=False,
            changeCommand=lambda *args:self.__uiCallback("_ui_export_lightIds2",args))
        self._ui_lightIds2 = cmds.floatFieldGrp( parent=self._ui_formLayout, numberOfFields=4, label='lightIds2', value=[0.0,0.0,0.0,0.0],step=0.01,
            changeCommand=lambda *args:self.__uiCallback("_ui_lightIds2",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_lightIds2",args))
        #
        self._ui_lightTypeBitMask_dscTxt2 = cmds.text( label='function', w=140, align="right" )
        self._ui_lightTypeBitMask_b9 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        self._ui_lightTypeBitMask_b10 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        self._ui_lightTypeBitMask_b11 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        self._ui_lightTypeBitMask_b12 = cmds.optionMenu( parent=self._ui_formLayout, w=80,
                        changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask_bits",args))
        for lightState in self._lightStates:
            cmds.menuItem( label=lightState )
        # ---------------------------------------------------------------------------------------------------------------
        self._ui_export_lightIds3 = cmds.checkBoxGrp( parent=self._ui_formLayout, numberOfCheckBoxes=1, label='', label1='export lightIds3', v1=False,
            changeCommand=lambda *args:self.__uiCallback("_ui_export_lightIds3",args))
        self._ui_lightIds3 = cmds.floatFieldGrp( parent=self._ui_formLayout, numberOfFields=4, label='lightIds3', value=[0.0,0.0,0.0,0.0],step=0.01,
            changeCommand=lambda *args:self.__uiCallback("_ui_lightIds3",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_lightIds3",args))
        # ---------------------------------------------------------------------------------------------------------------
        self._ui_export_lightTypeBitMask = cmds.checkBoxGrp( parent=self._ui_formLayout, numberOfCheckBoxes=1, label='', label1='export lightTypeBitMask', v1=False,
            changeCommand=lambda *args:self.__uiCallback("_ui_export_lightTypeBitMask",args))
        #
        self._ui_lightTypeBitMask = cmds.intFieldGrp( parent=self._ui_formLayout, numberOfFields=1, label='lightTypeBitMask',value1=0,
            changeCommand=lambda *args:self.__uiCallback("_ui_lightTypeBitMask",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_lightTypeBitMask",args))
        # ---------------------------------------------------------------------------------------------------------------
        self._ui_export_lightUvOffsetBitMask = cmds.checkBoxGrp( parent=self._ui_formLayout, numberOfCheckBoxes=1, label='', label1='export lightUvOffsetBitMask', v1=False,
            changeCommand=lambda *args:self.__uiCallback("_ui_export_lightUvOffsetBitMask",args))
        #
        self._ui_lightUvOffsetBitMask = cmds.intFieldGrp( parent=self._ui_formLayout, numberOfFields=1, label='lightUvOffsetBitMask', value1=0,
            changeCommand=lambda *args:self.__uiCallback("_ui_lightUvOffsetBitMask",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_lightUvOffsetBitMask",args))
        # ---------------------------------------------------------------------------------------------------------------
        self._ui_export_blinkSimple = cmds.checkBoxGrp( parent=self._ui_formLayout, numberOfCheckBoxes=1, label='', label1='export blinkSimple', v1=False,
            changeCommand=lambda *args:self.__uiCallback("_ui_export_blinkSimple",args))
        self._ui_blinkSimple = cmds.floatFieldGrp( parent=self._ui_formLayout, numberOfFields=2,label='blinkSimple',value1=1.0,value2=0.0,step=0.01,
            changeCommand=lambda *args:self.__uiCallback("_ui_blinkSimple",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_blinkSimple",args))
        # ---------------------------------------------------------------------------------------------------------------
        self._ui_export_blinkMulti = cmds.checkBoxGrp( parent=self._ui_formLayout, numberOfCheckBoxes=1, label='', label1='export blinkMulti', v1=False,
            changeCommand=lambda *args:self.__uiCallback("_ui_export_blinkMulti",args))
        self._ui_blinkMulti = cmds.floatFieldGrp( parent=self._ui_formLayout, numberOfFields=4,label='blinkMulti',value1=2.0,value2=5.0,value3=50.0,value4=0.0,step=0.01,
            changeCommand=lambda *args:self.__uiCallback("_ui_blinkMulti",args),
            dragCommand  =lambda *args:self.__uiCallback("_ui_blinkMulti",args))
        # ---------------------------------------------------------------------------------------------------------------
        cmds.formLayout(self._ui_formLayout, edit = True,
            attachForm =    [
                             ( self._ui_scratches, 'top', 2 ),
                             ( self._ui_scratches, 'left', 2 ),
                             ( self._ui_scratches, 'right', 2 ),
                             ( self._ui_dirt, 'left', 2 ),
                             ( self._ui_dirt, 'right', 2 ),
                             ( self._ui_snow, 'left', 2 ),
                             ( self._ui_snow, 'right', 2 ),
                             ( self._ui_scrollPosX, 'left', 2 ),
                             ( self._ui_scrollPosX, 'right', 2 ),
                             ( self._ui_debugMode, 'left', 2 ),
                             ( self._ui_debugMode, 'right', 2 ),
                             ( self._ui_export_lightIds0, 'left', 2 ),
                             ( self._ui_export_lightIds0, 'right', 2 ),
                             ( self._ui_lightIds0, 'left', 2 ),
                             ( self._ui_lightTypeBitMask_dscTxt0, 'left', 2 ),
                             ( self._ui_lightUvOffsetBitMask_dscTxt0, 'left', 2 ),
                             ( self._ui_export_lightIds1, 'left', 2 ),
                             ( self._ui_export_lightIds1, 'right', 2 ),
                             ( self._ui_lightIds1, 'left', 2 ),
                             ( self._ui_lightTypeBitMask_dscTxt1, 'left', 2 ),
                             ( self._ui_export_lightIds2, 'left', 2 ),
                             ( self._ui_export_lightIds2, 'right', 2 ),
                             ( self._ui_lightIds2, 'left', 2 ),
                             ( self._ui_lightTypeBitMask_dscTxt2, 'left', 2 ),
                             ( self._ui_export_lightIds3, 'left', 2 ),
                             ( self._ui_export_lightIds3, 'right', 2 ),
                             ( self._ui_lightIds3, 'left', 2 ),
                             ( self._ui_export_lightTypeBitMask, 'left', 2 ),
                             ( self._ui_export_lightTypeBitMask, 'right', 2 ),
                             ( self._ui_lightTypeBitMask, 'left', 2 ),
                             ( self._ui_lightTypeBitMask, 'right', 2 ),
                             ( self._ui_export_lightUvOffsetBitMask, 'left', 2 ),
                             ( self._ui_export_lightUvOffsetBitMask, 'right', 2 ),
                             ( self._ui_lightUvOffsetBitMask, 'left', 2 ),
                             ( self._ui_lightUvOffsetBitMask, 'right', 2 ),
                             ( self._ui_export_blinkSimple, 'left', 2 ),
                             ( self._ui_export_blinkSimple, 'right', 2 ),
                             ( self._ui_blinkSimple, 'left', 2 ),
                             ( self._ui_blinkSimple, 'right', 2 ),
                             ( self._ui_export_blinkMulti, 'left', 2 ),
                             ( self._ui_export_blinkMulti, 'right', 2 ),
                             ( self._ui_blinkMulti, 'left', 2 ),
                             ( self._ui_blinkMulti, 'right', 2 ),
                            ],
            attachControl = [
                             ( self._ui_dirt, 'top', 2, self._ui_scratches ),
                             ( self._ui_snow, 'top', 2, self._ui_dirt ),
                             ( self._ui_scrollPosX, 'top', 2, self._ui_snow ),
                             ( self._ui_debugMode, 'top', 2, self._ui_scrollPosX ),
                             ( self._ui_export_lightIds0, 'top', 2, self._ui_debugMode ),
                             ( self._ui_lightIds0, 'top', 2, self._ui_export_lightIds0 ),
                             ( self._ui_lightTypeBitMask_dscTxt0, 'top', 2, self._ui_lightIds0 ),
                             ( self._ui_lightTypeBitMask_b1, 'top', 2, self._ui_lightIds0 ),
                             ( self._ui_lightTypeBitMask_b1, 'left', 2, self._ui_lightTypeBitMask_dscTxt0 ),
                             ( self._ui_lightTypeBitMask_b2, 'top', 2, self._ui_lightIds0 ),
                             ( self._ui_lightTypeBitMask_b2, 'left', 2, self._ui_lightTypeBitMask_b1 ),
                             ( self._ui_lightTypeBitMask_b3, 'top', 2, self._ui_lightIds0 ),
                             ( self._ui_lightTypeBitMask_b3, 'left', 2, self._ui_lightTypeBitMask_b2 ),
                             ( self._ui_lightTypeBitMask_b4, 'top', 2, self._ui_lightIds0 ),
                             ( self._ui_lightTypeBitMask_b4, 'left', 2, self._ui_lightTypeBitMask_b3 ),
                             ( self._ui_lightUvOffsetBitMask_dscTxt0, 'top', 2, self._ui_lightTypeBitMask_b1 ),
                             ( self._ui_lightUvOffsetBitMask_b1, 'top', 2, self._ui_lightTypeBitMask_b1 ),
                             ( self._ui_lightUvOffsetBitMask_b1, 'left', 2, self._ui_lightUvOffsetBitMask_dscTxt0 ),
                             ( self._ui_lightUvOffsetBitMask_b2, 'top', 2, self._ui_lightTypeBitMask_b1 ),
                             ( self._ui_lightUvOffsetBitMask_b2, 'left', 2, self._ui_lightUvOffsetBitMask_b1 ),
                             ( self._ui_lightUvOffsetBitMask_b3, 'top', 2, self._ui_lightTypeBitMask_b1 ),
                             ( self._ui_lightUvOffsetBitMask_b3, 'left', 2, self._ui_lightUvOffsetBitMask_b2 ),
                             ( self._ui_lightUvOffsetBitMask_b4, 'top', 2, self._ui_lightTypeBitMask_b1 ),
                             ( self._ui_lightUvOffsetBitMask_b4, 'left', 2, self._ui_lightUvOffsetBitMask_b3 ),
                             ( self._ui_export_lightIds1, 'top', 2, self._ui_lightUvOffsetBitMask_b1 ),
                             ( self._ui_lightIds1, 'top', 2, self._ui_export_lightIds1 ),
                             ( self._ui_lightTypeBitMask_dscTxt1, 'top', 2, self._ui_lightIds1 ),
                             ( self._ui_lightTypeBitMask_b5, 'top', 2, self._ui_lightIds1 ),
                             ( self._ui_lightTypeBitMask_b5, 'left', 2, self._ui_lightTypeBitMask_dscTxt1 ),
                             ( self._ui_lightTypeBitMask_b6, 'top', 2, self._ui_lightIds1 ),
                             ( self._ui_lightTypeBitMask_b6, 'left', 2, self._ui_lightTypeBitMask_b5 ),
                             ( self._ui_lightTypeBitMask_b7, 'top', 2, self._ui_lightIds1 ),
                             ( self._ui_lightTypeBitMask_b7, 'left', 2, self._ui_lightTypeBitMask_b6 ),
                             ( self._ui_lightTypeBitMask_b8, 'top', 2, self._ui_lightIds1 ),
                             ( self._ui_lightTypeBitMask_b8, 'left', 2, self._ui_lightTypeBitMask_b7 ),
                             ( self._ui_export_lightIds2, 'top', 2, self._ui_lightTypeBitMask_b5 ),
                             ( self._ui_lightIds2, 'top', 2, self._ui_export_lightIds2 ),
                             ( self._ui_lightTypeBitMask_dscTxt2, 'top', 2, self._ui_lightIds2 ),
                             ( self._ui_lightTypeBitMask_b9, 'top', 2, self._ui_lightIds2 ),
                             ( self._ui_lightTypeBitMask_b9, 'left', 2, self._ui_lightTypeBitMask_dscTxt2 ),
                             ( self._ui_lightTypeBitMask_b10, 'top', 2, self._ui_lightIds2 ),
                             ( self._ui_lightTypeBitMask_b10, 'left', 2, self._ui_lightTypeBitMask_b9 ),
                             ( self._ui_lightTypeBitMask_b11, 'top', 2, self._ui_lightIds2 ),
                             ( self._ui_lightTypeBitMask_b11, 'left', 2, self._ui_lightTypeBitMask_b10 ),
                             ( self._ui_lightTypeBitMask_b12, 'top', 2, self._ui_lightIds2 ),
                             ( self._ui_lightTypeBitMask_b12, 'left', 2, self._ui_lightTypeBitMask_b11 ),
                             ( self._ui_export_lightIds3, 'top', 2, self._ui_lightTypeBitMask_b9 ),
                             ( self._ui_lightIds3, 'top', 2, self._ui_export_lightIds3 ),
                             ( self._ui_export_lightTypeBitMask, 'top', 2, self._ui_lightIds3 ),
                             ( self._ui_lightTypeBitMask, 'top', 2, self._ui_export_lightTypeBitMask ),
                             ( self._ui_export_lightUvOffsetBitMask, 'top', 2, self._ui_lightTypeBitMask ),
                             ( self._ui_lightUvOffsetBitMask, 'top', 2, self._ui_export_lightUvOffsetBitMask ),
                             ( self._ui_export_blinkSimple, 'top', 2, self._ui_lightUvOffsetBitMask ),
                             ( self._ui_blinkSimple, 'top', 2, self._ui_export_blinkSimple ),
                             ( self._ui_export_blinkMulti, 'top', 2, self._ui_blinkSimple ),
                             ( self._ui_blinkMulti, 'top', 2, self._ui_export_blinkMulti ),
                            ],
            attachNone =    [
                             ( self._ui_scratches, 'bottom' ),
                             ( self._ui_dirt, 'bottom' ),
                             ( self._ui_snow, 'bottom' ),
                             ( self._ui_scrollPosX, 'bottom' ),
                             ( self._ui_debugMode, 'bottom' ),
                             ( self._ui_export_lightIds0, 'bottom' ),
                             ( self._ui_lightIds0, 'bottom' ),
                             ( self._ui_lightIds0, 'right' ),
                             ( self._ui_lightTypeBitMask_dscTxt0, 'bottom' ),
                             ( self._ui_lightTypeBitMask_dscTxt0, 'right' ),
                             ( self._ui_lightTypeBitMask_b1, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b1, 'right' ),
                             ( self._ui_lightTypeBitMask_b2, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b2, 'right' ),
                             ( self._ui_lightTypeBitMask_b3, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b3, 'right' ),
                             ( self._ui_lightTypeBitMask_b4, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b4, 'right' ),
                             ( self._ui_lightUvOffsetBitMask_dscTxt0, 'bottom' ),
                             ( self._ui_lightUvOffsetBitMask_dscTxt0, 'right' ),
                             ( self._ui_lightUvOffsetBitMask_b1, 'bottom' ),
                             ( self._ui_lightUvOffsetBitMask_b1, 'right' ),
                             ( self._ui_lightUvOffsetBitMask_b2, 'bottom' ),
                             ( self._ui_lightUvOffsetBitMask_b2, 'right' ),
                             ( self._ui_lightUvOffsetBitMask_b3, 'bottom' ),
                             ( self._ui_lightUvOffsetBitMask_b3, 'right' ),
                             ( self._ui_lightUvOffsetBitMask_b4, 'bottom' ),
                             ( self._ui_lightUvOffsetBitMask_b4, 'right' ),
                             ( self._ui_export_lightIds1, 'bottom' ),
                             ( self._ui_lightIds1, 'bottom' ),
                             ( self._ui_lightIds1, 'right' ),
                             ( self._ui_lightTypeBitMask_dscTxt1, 'bottom' ),
                             ( self._ui_lightTypeBitMask_dscTxt1, 'right' ),
                             ( self._ui_lightTypeBitMask_b5, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b5, 'right' ),
                             ( self._ui_lightTypeBitMask_b6, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b6, 'right' ),
                             ( self._ui_lightTypeBitMask_b7, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b7, 'right' ),
                             ( self._ui_lightTypeBitMask_b8, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b8, 'right' ),
                             ( self._ui_export_lightIds2, 'bottom' ),
                             ( self._ui_lightIds2, 'bottom' ),
                             ( self._ui_lightIds2, 'right' ),
                             ( self._ui_lightTypeBitMask_dscTxt2, 'bottom' ),
                             ( self._ui_lightTypeBitMask_dscTxt2, 'right' ),
                             ( self._ui_lightTypeBitMask_b9, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b9, 'right' ),
                             ( self._ui_lightTypeBitMask_b10, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b10, 'right' ),
                             ( self._ui_lightTypeBitMask_b11, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b11, 'right' ),
                             ( self._ui_lightTypeBitMask_b12, 'bottom' ),
                             ( self._ui_lightTypeBitMask_b12, 'right' ),
                             ( self._ui_export_lightIds3, 'bottom' ),
                             ( self._ui_lightIds3, 'bottom' ),
                             ( self._ui_lightIds3, 'right' ),
                             ( self._ui_export_lightTypeBitMask, 'bottom' ),
                             ( self._ui_lightTypeBitMask, 'bottom' ),
                             ( self._ui_export_lightUvOffsetBitMask, 'bottom' ),
                             ( self._ui_lightUvOffsetBitMask, 'bottom' ),
                             ( self._ui_export_blinkSimple, 'bottom' ),
                             ( self._ui_blinkSimple, 'bottom' ),
                             ( self._ui_export_blinkMulti, 'bottom' ),
                             ( self._ui_blinkMulti, 'bottom' ),
                            ])
        cmds.showWindow(self._ui_window)

    def __uiCallback(self, *args):
        if (len(args)>0):
            m_input = args[0]
            if ('_ui_scratches_changed'==m_input):
                value = cmds.floatSliderGrp(self._ui_scratches,query=True,value=True)
                setAttributeValueForAllGLSLShaders("uiScratches",value)
            if ('_ui_dirt_changed'==m_input):
                value = cmds.floatSliderGrp(self._ui_dirt,query=True,value=True)
                setAttributeValueForAllGLSLShaders("uiDirt",value)
            if ('_ui_snow_changed'==m_input):
                value = cmds.floatSliderGrp(self._ui_snow,query=True,value=True)
                setAttributeValueForAllGLSLShaders("uiSnow",value)
            if ('_ui_scrollPosX_changed'==m_input):
                value = cmds.floatSliderGrp(self._ui_scrollPosX,query=True,value=True)
                setAttributeValueForAllGLSLShaders("uiScrollPosX",value)
            if ('_ui_debugMode_changed'==m_input):
                value = cmds.optionMenuGrp(self._ui_debugMode,query=True,value=True)
                #print(value,self._debugModesList.index(value))
                setAttributeValueForAllGLSLShaders("debugMode",value,type="enum")
            if ('_ui_export_lightIds0'==m_input):
                value = cmds.checkBoxGrp(self._ui_export_lightIds0,query=True,value1=True)
                setAttributeValueForAllGLSLShaders("customParameter_enable_lightIds0",value,type="bool")
            if ('_ui_lightIds0'==m_input):
                value = cmds.floatFieldGrp(self._ui_lightIds0,query=True,value=True)
                setAttributeValueForAllGLSLShaders("customParameter_lightIds0",value,type="float4")
            if ('_ui_export_lightIds1'==m_input):
                value = cmds.checkBoxGrp(self._ui_export_lightIds1,query=True,value1=True)
                setAttributeValueForAllGLSLShaders("customParameter_enable_lightIds1",value,type="bool")
            if ('_ui_lightIds1'==m_input):
                value = cmds.floatFieldGrp(self._ui_lightIds1,query=True,value=True)
                setAttributeValueForAllGLSLShaders("customParameter_lightIds1",value,type="float4")
            if ('_ui_export_lightIds2'==m_input):
                value = cmds.checkBoxGrp(self._ui_export_lightIds2,query=True,value1=True)
                setAttributeValueForAllGLSLShaders("customParameter_enable_lightIds2",value,type="bool")
            if ('_ui_lightIds2'==m_input):
                value = cmds.floatFieldGrp(self._ui_lightIds2,query=True,value=True)
                setAttributeValueForAllGLSLShaders("customParameter_lightIds2",value,type="float4")
            if ('_ui_export_lightIds3'==m_input):
                value = cmds.checkBoxGrp(self._ui_export_lightIds3,query=True,value1=True)
                setAttributeValueForAllGLSLShaders("customParameter_enable_lightIds3",value,type="bool")
            if ('_ui_lightIds3'==m_input):
                value = cmds.floatFieldGrp(self._ui_lightIds3,query=True,value=True)
                setAttributeValueForAllGLSLShaders("customParameter_lightIds3",value,type="float4")
            if ('_ui_export_lightTypeBitMask'==m_input):
                value = cmds.checkBoxGrp(self._ui_export_lightTypeBitMask,query=True,value1=True)
                setAttributeValueForAllGLSLShaders("customParameter_enable_lightTypeBitMask",value,type="bool")
            if ('_ui_lightTypeBitMask_bits'==m_input):
                value1  = cmds.optionMenu(self._ui_lightTypeBitMask_b1, query=True,value=True)
                value2  = cmds.optionMenu(self._ui_lightTypeBitMask_b2, query=True,value=True)
                value3  = cmds.optionMenu(self._ui_lightTypeBitMask_b3, query=True,value=True)
                value4  = cmds.optionMenu(self._ui_lightTypeBitMask_b4, query=True,value=True)
                value5  = cmds.optionMenu(self._ui_lightTypeBitMask_b5, query=True,value=True)
                value6  = cmds.optionMenu(self._ui_lightTypeBitMask_b6, query=True,value=True)
                value7  = cmds.optionMenu(self._ui_lightTypeBitMask_b7, query=True,value=True)
                value8  = cmds.optionMenu(self._ui_lightTypeBitMask_b8, query=True,value=True)
                value9  = cmds.optionMenu(self._ui_lightTypeBitMask_b9, query=True,value=True)
                value10 = cmds.optionMenu(self._ui_lightTypeBitMask_b10,query=True,value=True)
                value11 = cmds.optionMenu(self._ui_lightTypeBitMask_b11,query=True,value=True)
                value12 = cmds.optionMenu(self._ui_lightTypeBitMask_b12,query=True,value=True)
                #print(value1,value2,value3,value4,value5,value6,value7,value8," ",
                #      self._lightStates.index(value1),self._lightStates.index(value2),self._lightStates.index(value3),self._lightStates.index(value4),self._lightStates.index(value5),self._lightStates.index(value6),self._lightStates.index(value7),self._lightStates.index(value8))
                value1  = self._lightStates.index(value1)
                value2  = self._lightStates.index(value2)
                value3  = self._lightStates.index(value3)
                value4  = self._lightStates.index(value4)
                value5  = self._lightStates.index(value5)
                value6  = self._lightStates.index(value6)
                value7  = self._lightStates.index(value7)
                value8  = self._lightStates.index(value8)
                value9  = self._lightStates.index(value9)
                value10 = self._lightStates.index(value10)
                value11 = self._lightStates.index(value11)
                value12 = self._lightStates.index(value12)
                bitsArray = []
                bitsArray.append(value1)
                bitsArray.append(value2)
                bitsArray.append(value3)
                bitsArray.append(value4)
                bitsArray.append(value5)
                bitsArray.append(value6)
                bitsArray.append(value7)
                bitsArray.append(value8)
                bitsArray.append(value9)
                bitsArray.append(value10)
                bitsArray.append(value11)
                bitsArray.append(value12)
                value = getFloatFromStates(2,bitsArray)
                cmds.intFieldGrp(self._ui_lightTypeBitMask,edit=True,v1=value)
                setAttributeValueForAllGLSLShaders("customParameter_lightTypeBitMask",value,type="int")
            if ('_ui_lightTypeBitMask'==m_input):
                value = cmds.intFieldGrp(self._ui_lightTypeBitMask,query=True,value1=True)
                setAttributeValueForAllGLSLShaders("customParameter_lightTypeBitMask",value,type="int")
            if ('_ui_lightUvOffsetBitMask_bits'==m_input):
                value1 = cmds.optionMenu(self._ui_lightUvOffsetBitMask_b1,query=True,value=True)
                value2 = cmds.optionMenu(self._ui_lightUvOffsetBitMask_b2,query=True,value=True)
                value3 = cmds.optionMenu(self._ui_lightUvOffsetBitMask_b3,query=True,value=True)
                value4 = cmds.optionMenu(self._ui_lightUvOffsetBitMask_b4,query=True,value=True)
                #print(value1,value2,value3,value4," ",
                #      self._lightColors.index(value1),self._lightColors.index(value2),self._lightColors.index(value3),self._lightColors.index(value4))
                value1 = self._lightColors.index(value1)
                value2 = self._lightColors.index(value2)
                value3 = self._lightColors.index(value3)
                value4 = self._lightColors.index(value4)
                bitsArray = []
                bitsArray.append(value1)
                bitsArray.append(value2)
                bitsArray.append(value3)
                bitsArray.append(value4)
                value = getFloatFromStates(6,bitsArray)
                cmds.intFieldGrp(self._ui_lightUvOffsetBitMask,edit=True,v1=value)
                setAttributeValueForAllGLSLShaders("customParameter_lightUvOffsetBitMask",value,type="int")
            if ('_ui_export_lightUvOffsetBitMask'==m_input):
                value = cmds.checkBoxGrp(self._ui_export_lightUvOffsetBitMask,query=True,value1=True)
                setAttributeValueForAllGLSLShaders("customParameter_enable_lightUvOffsetBitMask",value,type="bool")
            if ('_ui_lightUvOffsetBitMask'==m_input):
                value = cmds.intFieldGrp(self._ui_lightUvOffsetBitMask,query=True,value1=True)
                setAttributeValueForAllGLSLShaders("customParameter_lightUvOffsetBitMask",value,type="int")
            if ('_ui_export_blinkSimple'==m_input):
                value = cmds.checkBoxGrp(self._ui_export_blinkSimple,query=True,value1=True)
                setAttributeValueForAllGLSLShaders("customParameter_enable_blinkSimple",value,type="bool")
            if ('_ui_blinkSimple'==m_input):
                value = cmds.floatFieldGrp(self._ui_blinkSimple,query=True,value=True)
                setAttributeValueForAllGLSLShaders("customParameter_blinkSimple",value,type="float2")
            if ('_ui_export_blinkMulti'==m_input):
                value = cmds.checkBoxGrp(self._ui_export_blinkMulti,query=True,value1=True)
                setAttributeValueForAllGLSLShaders("customParameter_enable_blinkMulti",value,type="bool")
            if ('_ui_blinkMulti'==m_input):
                value = cmds.floatFieldGrp(self._ui_blinkMulti,query=True,value=True)
                setAttributeValueForAllGLSLShaders("customParameter_blinkMulti",value,type="float4")

def setAttributeValueForAllGLSLShaders(attribute, value, type="float"):
    # iterate over GLSL Shaders
    m_iterator = OpenMaya.MItDependencyNodes( OpenMaya.MFn.kPluginHardwareShader )
    m_nodeFn   = OpenMaya.MFnDependencyNode()
    while not m_iterator.isDone():
        m_object = m_iterator.thisNode()
        m_nodeFn.setObject( m_object )
        if m_nodeFn.hasAttribute(attribute):
            fullname = '{}.{}'.format(m_nodeFn.name(),attribute)
            if  ("float" == type):
                cmds.setAttr(fullname, value)
            elif("bool" == type):
                cmds.setAttr(fullname, value)
            elif("enum" == type):
                I3DUtils.setAttributeValue(m_nodeFn.name(),attribute,str(value))
            elif("float2" == type):
                cmds.setAttr('{}X'.format(fullname), value[0])
                cmds.setAttr('{}Y'.format(fullname), value[1])
            elif("float3" == type):
                cmds.setAttr('{}X'.format(fullname), value[0])
                cmds.setAttr('{}Y'.format(fullname), value[1])
                cmds.setAttr('{}Z'.format(fullname), value[2])
            elif("float4" == type):
                cmds.setAttr('{}X'.format(fullname), value[0])
                cmds.setAttr('{}Y'.format(fullname), value[1])
                cmds.setAttr('{}Z'.format(fullname), value[2])
                cmds.setAttr('{}W'.format(fullname), value[3])
            elif("int" == type):
                cmds.setAttr(fullname, value)
        m_iterator.next()

def getFloatFromStates(bitsPerValue,bitsArray):
    outValue = 0
    shift = 0
    for bitValue in bitsArray:
        outValue += ( bitValue  <<  shift * bitsPerValue )
        shift += 1
    return outValue
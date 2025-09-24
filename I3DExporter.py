#
# i3D Toolbox (.py)
#
# @author Christian Ammann, Stefan Geiger
# @modified Evgeniy Zaitsev, Manuel Leithner
# @created 03/05/03
# @modified 24/06/15
#
# Copyright (c) 2008-2015 GIANTS Software GmbH, Confidential, All Rights Reserved.
# Copyright (c) 2003-2015 Christian Ammann and Stefan Geiger, Confidential, All Rights Reserved.
#

import I3DUtils as I3DUtils

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya
import checkClipDistances as checkClipDistances
import ShaderUtil as ShaderUtil
import BitMaskWindow
import CollisionMaskFlags
import sys
import math
import os
import re
import io
import importlib
import datetime
import traceback
import I3DTemplateParameter
import I3DShader
import I3DExportHandler
import exporterUI.ErrorBox as ErrorBox
import exporterUI.ChangeLogDialog as ChangeLogDialog

try:
    # python 3
    from html import escape
except ImportError:
    # python 2
    from cgi import escape

try:
    # python 2
    reload(I3DUtils)
    reload(checkClipDistances)
    reload(ShaderUtil)
    reload(I3DTemplateParameter)
    reload(I3DShader)
    reload(CollisionMaskFlags)
    reload(BitMaskWindow)
    reload(I3DExportHandler)
    reload(ErrorBox)
    reload(ChangeLogDialog)
except NameError:
    # python 3
    from importlib import reload
    reload(I3DUtils)
    reload(checkClipDistances)
    reload(ShaderUtil)
    reload(I3DTemplateParameter)
    reload(I3DShader)
    reload(CollisionMaskFlags)
    reload(BitMaskWindow)
    reload(I3DExportHandler)
    reload(ErrorBox)
    reload(ChangeLogDialog)

VERSION = '10.0.0'
GAME_VERSION = '25'

# constants
TITLE = 'GIANTS I3D Exporter (Version ' + VERSION + ')'
SETTINGS_PREFIX = 'I3DExportSettings'
NODETYPE_GROUP = 0
NODETYPE_MESH = 1
NODETYPE_CAMERA = 2
NODETYPE_JOINT = 3
TYPE_BOOL = 1
TYPE_INT = 2
TYPE_FLOAT = 3
TYPE_STRING = 4
TYPE_ENUM = 5
TYPE_HEX = 6
MESSAGE_TYPE_INFO = 0
MESSAGE_TYPE_WARNING = 1
MESSAGE_TYPE_ERROR = 2
MESSAGE_TYPE_NONE = 3
TEXT_WIDTH = 150
DEFAULT_FIELD_WIDTH = 60
MASK_FIELD_WIDTH = 70
WINDOW_WIDTH = 460
UINT_MAX_AS_STRING = '4294967295'

# load collision mask/groups and presets from xml
COLLISION_FLAGS_XML_FILE = os.path.dirname(os.path.realpath(__file__)) + "/collisionMaskFlags.xml"
colMaskFlags = CollisionMaskFlags.CollisionMaskFlags(COLLISION_FLAGS_XML_FILE)

# prepare data for UI
g_collisionBitmaskAttributes = {
    'num_bits': 32,
    'bit_annotations': {bit: "{}: {}".format(data["name"], data["desc"]) for bit, data in colMaskFlags.flagsByBit.items()},
    'bit_names' : {bit: data["name"] for bit, data in colMaskFlags.flagsByBit.items()}
}  # merge name and desc to single string
g_collisionPresetNamesOptions = [""] + list(colMaskFlags.presetsByName.keys())  # add empty element as first option

g_objectMaskAttributes = {
    'num_bits': 32,
    'bit_names': {
        # TODO: load from XML
        # Shape bits visible in default view
        7:  "Shape visible in mirror (and main view)",

        # Shape bits not in default view
        8:  "Shape visible in water reflection (very high)",
        9:  "Shape visible in water reflection (high or lower)",
        15: "Shape visible in mirror (but not main view)",

        # Lights bits not in default view
        24: "Light visible in water reflection (very high)",
        25: "Light visible in water reflection (high or lower)",
        31: "Light visible in mirror",
    }
}

MERGEGROUP_COLORS = {
    0: 4,
    1: 2,
    2: 3,
    3: 7,
    4: 24,
    5: 25,
    6: 28,
    7: 29,
    8: 30,
    9: 31,
    10: 5,
    11: 16,
    12: 17,
    13: 22,
    14: 18,
    15: 11,
    16: 14,
}

UI_SETTINGS_LOAD_ON_SELECT = 'I3DExporter_LoadOnSelect'

UI_OPTIONS_PREDEFINED_VEHICLES_ATTRIBUTES = 'giants_optionsPredefinedVehicleAttributes'
UI_OPTIONS_PREDEFINED_MESH_ATTRIBUTES = 'giants_optionsPredefinedMeshAttributes'
UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES = 'giants_optionsPredefinedShaderAttributes'
UI_OPTIONS_PREDEFINED_PHYSICS = 'giants_optionsPredefinedPhysics'
UI_OPTIONS_PREDEFINED_BOUNDINGVOLUME = 'giants_optionsBoundingVolume'
UI_OPTIONS_SKELETONS = 'giants_optionsSkeletons'
UI_OPTIONS_SHELF_COMMAND = 'giants_optionsShelfCommand'

# UI_CONTROL_DOCK = 'giants_dockControl'
UI_CONTROL_WINDOW = 'i3DExport'
UI_CONTROL_EXPORT_1 = 'ExportParts'
UI_CONTROL_EXPORT_2 = 'ExportParts2'
UI_CONTROL_EXPORT_3 = 'ExportParts3'
UI_CONTROL_EXPORT_4 = 'ExportParts4'
UI_CONTROL_SHAPES_1 = 'ShapeIncludes'
UI_CONTROL_SHAPES_2 = 'ShapeIncludes2'
UI_CONTROL_MISC_1 = 'Misc'
UI_CONTROL_MISC_2 = 'Misc2'
UI_CONTROL_GAME_PATH = 'GamePath'
UI_CONTROL_BOOL_USE_MAYA_FILENAME = 'FilenameInfo'
UI_CONTROL_BOOL_ERROR_CHECK_SETTINGS = 'ErrorCheckSettings'
UI_CONTROL_VALIDATION_SCROLL = 'giants_validationScrollLayout'
UI_CONTROL_STRING_FILE_PATH = 'giants_outputFileLocationPath'
UI_CONTROL_STRING_XML_FILE_PATH = 'giants_xmlConfigFileLocationPath'
UI_CONTROL_STRING_GAME_PATH = 'giants_gameLocationPath'
UI_CONTROL_SELECT_GAME_PATH = 'giants_gameLocationSelect'
UI_CONTROL_STRING_LOADED_NODE_NAME = 'giants_attributeLoadedObjectName'
UI_CONTROL_BOOL_LOCKED_GROUP = 'giants_attributeObjectLockedGroup'
UI_CONTROL_STRING_NODE_NAME = 'giants_attributeObjectName'
UI_CONTROL_STRING_NODE_INDEX = 'giants_attributeObjectIndex'
UI_CONTROL_STRING_IDENTIFIER = 'giants_attributeStringXmlIdentifier'
UI_CONTROL_BOOL_STATIC = 'giants_attributeBoolStatic'
UI_CONTROL_BOOL_KINEMATIC = 'giants_attributeBoolKinematic'
UI_CONTROL_BOOL_DYNAMIC = 'giants_attributeBoolDynamic'
UI_CONTROL_BOOL_COMPOUND = 'giants_attributeBoolCompound'
UI_CONTROL_BOOL_COMPOUND_CHILD = 'giants_attributeBoolCompoundChild'
UI_CONTROL_BOOL_COLLISION = 'giants_attributeBoolCollision'
UI_CONTROL_BOOL_TERRAIN_DECAL = 'giants_attributeTerrainDecal'
UI_CONTROL_BOOL_CPUMESH = 'giants_attributeBoolCPUMesh'
UI_CONTROL_BOOL_MERGE_CHILDREN = 'giants_attributeBoolMergeChildren'
UI_CONTROL_BOOL_MERGE_CHILDREN_FREEZE_TRANS = 'giants_attributeBoolMergeChildrenFreezeTrans'
UI_CONTROL_BOOL_MERGE_CHILDREN_FREEZE_ROT = 'giants_attributeBoolMergeChildrenFreezeRot'
UI_CONTROL_BOOL_MERGE_CHILDREN_FREEZE_SCALE = 'giants_attributeBoolMergeChildrenFreezeScale'
UI_CONTROL_BOOL_LOD = 'giants_attributeBoolLOD'
UI_CONTROL_BOOL_LOD_BLENDING = 'giants_attributeBoolLODBlending'
UI_CONTROL_BOOL_CCD = 'giants_attributeBoolCCD'
UI_CONTROL_BOOL_TRIGGER = 'giants_attributeBoolTrigger'
UI_CONTROL_BOOL_JOINT = 'giants_attributeBoolJoint'
UI_CONTROL_BOOL_PROJECTION = 'giants_attributeBoolProjection'
UI_CONTROL_BOOL_XAXIS_DRIVE = 'giants_attributeBoolXAxisDrive'
UI_CONTROL_BOOL_YAXIS_DRIVE = 'giants_attributeBoolYAxisDrive'
UI_CONTROL_BOOL_ZAXIS_DRIVE = 'giants_attributeBoolZAxisDrive'
UI_CONTROL_BOOL_DRIVE_POSITION = 'giants_attributeBoolDrivePosition'
UI_CONTROL_BOOL_BREAKABLE = 'giants_attributeBoolBreakable'
UI_CONTROL_BOOL_OCCLUDER = 'giants_attributeBoolOccluder'
UI_CONTROL_BOOL_NON_RENDERABLE = 'giants_attributeBoolNonRenderable'
UI_CONTROL_BOOL_DISTANCE_BLENDING = 'giants_attributeBoolDistanceBlending'
UI_CONTROL_STRING_COLLISION_FILTER_PRESET = 'giants_attributeStringCollisionFilterPreset'
UI_CONTROL_STRING_COLLISION_FILTER_GROUP = 'giants_attributeStringCollisionFilterGroup'
UI_CONTROL_STRING_COLLISION_FILTER_MASK = 'giants_attributeStringCollisionFilterMask'
UI_CONTROL_INT_SOLVER_ITERATIONS = 'giants_attributeIntSolverIterations'
UI_CONTROL_INT_DECAL_LAYER = 'giants_attributeIntDecalLayer'
UI_CONTROL_INT_MERGE_GROUP = 'giants_attributeIntMergeGroup'
UI_CONTROL_BOOL_MERGE_GROUP_ROOT = 'giants_attributeBoolMergeGroupRoot'
UI_CONTROL_INT_SPLITTYPE = 'giants_attributeIntSplitType'
UI_CONTROL_FLOAT_SPLIT_MIN_U = 'giants_attributeFloatSplitMinU'
UI_CONTROL_FLOAT_SPLIT_MIN_V = 'giants_attributeFloatSplitMinV'
UI_CONTROL_FLOAT_SPLIT_MAX_U = 'giants_attributeFloatSplitMaxU'
UI_CONTROL_FLOAT_SPLIT_MAX_V = 'giants_attributeFloatSplitMaxV'
UI_CONTROL_FLOAT_SPLIT_UV_WORLD_SCALE = 'giants_attributeFloatSplitUvWorldScale'
UI_CONTROL_STRING_OBJECT_MASK = 'giants_attributeStringObjectMask'
UI_CONTROL_INT_NAV_MESH_MASK = 'giants_attributeFloatNavMeshMask'
UI_CONTROL_BOOL_DOUBLE_SIDED = 'giants_attributeBoolDoubleSided'
UI_CONTROL_BOOL_MATERIAL_HOLDER = 'giants_attributeBoolMaterialHolder'
UI_CONTROL_BOOL_CASTS_SHADOWS = 'giants_attributeBoolCastsShadows'
UI_CONTROL_BOOL_RECEIVE_SHADOWS = 'giants_attributeBoolReceiveShadows'
UI_CONTROL_BOOL_CASTS_SHADOWS_PER_INSTANCE = 'giants_attributeBoolCastsShadowsPerInstance'
UI_CONTROL_BOOL_RECEIVE_SHADOWS_PER_INSTANCE = 'giants_attributeBoolReceiveShadowsPerInstance'
UI_CONTROL_BOOL_RENDERED_IN_VIEWPORTS = 'giants_attributeBoolRenderedInViewports'
UI_CONTROL_FLOAT_PROJECTION_DISTANCE = 'giants_attributeFloatProjectionDistance'
UI_CONTROL_FLOAT_PROJECTION_ANGLE = 'giants_attributeFloatProjectionAngle'
UI_CONTROL_FLOAT_DRIVE_FORCE_LIMIT = 'giants_attributeFloatDriveForceLimit'
UI_CONTROL_FLOAT_DRIVE_SPRING = 'giants_attributeFloatDriveSpring'
UI_CONTROL_FLOAT_DRIVE_DAMPING = 'giants_attributeFloatDriveDamping'
UI_CONTROL_FLOAT_BREAK_FORCE = 'giants_attributeFloatBreakForce'
UI_CONTROL_FLOAT_BREAK_TORQUE = 'giants_attributeFloatBreakTorque'
UI_CONTROL_FLOAT_CLIP_DISTANCE = 'giants_attributeFloatClipDistance'
UI_CONTROL_FLOAT_RESTITUTION = 'giants_attributeFloatRestitution'
UI_CONTROL_FLOAT_STATIC_FRICTION = 'giants_attributeFloatStaticFriction'
UI_CONTROL_FLOAT_DYNAMIC_FRICTION = 'giants_attributeFloatDynamicFriction'
UI_CONTROL_FLOAT_LINEAR_DAMPING = 'giants_attributeFloatLinearDamping'
UI_CONTROL_FLOAT_ANGULAR_DAMPING = 'giants_attributeFloatAngularDamping'
UI_CONTROL_FLOAT_DENSITY = 'giants_attributeFloatDensity'
UI_CONTROL_FLOAT_MASS = 'giants_attributeFloatMass'
UI_CONTROL_STRING_MASS_NODE = 'giants_attributeStringMassNode'
UI_CONTROL_LABEL_MASS = 'giants_attributeLabelMass'
UI_CONTROL_FLOAT_CHILD_0_DISTANCE = 'giants_attributeFloatChild0Distance'
UI_CONTROL_FLOAT_CHILD_1_DISTANCE = 'giants_attributeFloatChild1Distance'
UI_CONTROL_FLOAT_CHILD_2_DISTANCE = 'giants_attributeFloatChild2Distance'
UI_CONTROL_FLOAT_CHILD_3_DISTANCE = 'giants_attributeFloatChild3Distance'
UI_CONTROL_BOOL_SCALED = 'giants_attributeBoolScaled'
UI_CONTROL_BUTTON_ATTRIBUTE_APPLY = 'giants_attributeApply'

UI_CONTROL_INT_MINUTE_OF_DAY_START = 'giants_attributeIntMinuteOfDayStart'
UI_CONTROL_INT_MINUTE_OF_DAY_END = 'giants_attributeIntMinuteOfDayEnd'
UI_CONTROL_INT_DAY_OF_YEAR_START = 'giants_attributeIntDayOfYearStart'
UI_CONTROL_INT_DAY_OF_YEAR_END = 'giants_attributeIntDayOfYearEnd'
UI_CONTROL_STRING_WEATHER_REQUIRED_MASK = 'giants_attributeStringWeatherRequiredMask'
UI_CONTROL_STRING_WEATHER_PREVENT_MASK = 'giants_attributeStringWeatherPreventMask'
UI_CONTROL_STRING_VIEWER_SPACIALITY_REQUIRED_MASK = 'giants_attributeStringViewerSpacialityRequiredMask'
UI_CONTROL_STRING_VIEWER_SPACIALITY_PREVENT_MASK = 'giants_attributeStringViewerSpacialityPreventMask'
UI_CONTROL_BOOL_RENDER_INVISIBLE = 'giants_attributeBoolRenderInvisible'
UI_CONTROL_FLOAT_VISIBLE_SHADER_PARAMETER = 'giants_attributeFloatVisibleShaderParameter'

UI_CONTROL_BOOL_FORCE_VISIBILITY_CONDITION = 'giants_attributeBoolForceVisibilityCondition'

UI_CONTROL_ENUM_VERTEX_COMPRESSION_RANGE = 'giants_attributeStringVertexCompressionRange'
UI_CONTROL_STRING_BOUNDINGVOLUME = 'giants_attributeStringBoundingVolume'
UI_CONTROL_SHADER_PARAMETERS_SCROLL = 'giants_shaderParametersScroll'
UI_CONTROL_SHADER_PARAMETERS = 'giants_shaderParameters'
UI_CONTROL_SHADER_TEXTURES = 'giants_shaderTextures'
UI_CONTROL_LAYOUT_PARAMETERS = 'giants_layoutShaderParameters'
UI_CONTROL_LAYOUT_TEXTURES = 'giants_layoutShaderTextures'
UI_CONTROL_MENU_SHADER_VARIATION = 'giants_shaderMenuVariation'
UI_CONTROL_MENU_MATERIAL_SHADING_RATE = 'giants_materialMenuShadingRate'
UI_CONTROL_BOOL_MATERIAL_ALPHA_BLENDING = 'giants_materialBoolAlphaBlending'
UI_CONTROL_STRING_MATERIAL_REFERENCE_MATERIAL = 'giants_materialReferenceMaterial'
UI_CONTROL_STRING_MATERIAL_SLOT_NAME = 'giants_materialSlotName'
UI_CONTROL_STRING_MATERIAL_REFLECTION_MAP_SHAPES_OBJECT_MASK = 'giants_materialStringReflectionMapShapesObjectMask'
UI_CONTROL_STRING_MATERIAL_REFLECTION_MAP_LIGHTS_OBJECT_MASK = 'giants_materialStringReflectionMapLightsObjectMask'
UI_CONTROL_BOOL_MATERIAL_REFRACTION_MAP_WITH_SSR_DATA = 'giants_materialBoolRefractionMapWithSSRData'
UI_CONTROL_STRING_SHADER_PATH = 'giants_shaderPath'
UI_CONTROL_SELECTED_MATERIAL = 'giants_selectedMaterial'
UI_CONTROL_DUPLICATE_MATERIAL = 'giants_duplicateMaterial'
UI_CONTROL_BUTTON_MATERIAL_APPLY = 'giants_materialApply'

UI_CONTROL_BOOL_USE_DEPTH_MAP_SHADOWS = 'giants_attributeBoolUseDepthMapShadows'
UI_CONTROL_FLOAT_SOFT_SHADOWS_LIGHT_SIZE = 'giants_attributeFloatSoftShadowsLightSize'
UI_CONTROL_FLOAT_SOFT_SHADOWS_LIGHT_DISTANCE = 'giants_attributeFloatSoftShadowsLightDistance'
UI_CONTROL_FLOAT_SOFT_SHADOWS_DEPTH_BIAS_FACTOR = 'giants_attributeFloatSoftShadowsDepthBiasFactor'
UI_CONTROL_FLOAT_SOFT_SHADOWS_MAX_PENUMBRA_SIZE = 'giants_attributeFloatSoftShadowsMaxPenumbraSize'
UI_CONTROL_STRING_IES_PROFILE_FILE = 'giants_attributeStringIESProfileFile'
UI_CONTROL_BOOL_LIGHT_SCATTERING = 'giants_attributeBoolLightScattering'
UI_CONTROL_FLOAT_LIGHT_SCATTERING_INTENSITY = 'giants_attributeFloatLightScatteringIntensity'
UI_CONTROL_FLOAT_LIGHT_SCATTERING_CONE_ANGLE = 'giants_attributeFloatLightScatteringConeAngle'

UI_CONTROL_STRING_OBJECT_DATA_FILEPATH                 = 'giants_attributeStringObjectDataFilePath'
UI_CONTROL_BOOL_OBJECT_DATA_EXPORT_POSITION            = 'giants_attributeBoolObjectDataExportPosition'
UI_CONTROL_BOOL_OBJECT_DATA_EXPORT_ORIENTATION         = 'giants_attributeBoolObjectDataExportOrientation'
UI_CONTROL_BOOL_OBJECT_DATA_EXPORT_SCALE               = 'giants_attributeBoolObjectDataExportScale'
UI_CONTROL_BOOL_OBJECT_DATA_HIDE_FIRST_AND_LAST_OBJECT = 'giants_attributeBoolObjectDataHideFirstAndLastObject'
UI_CONTROL_BOOL_OBJECT_DATA_HIERARCHICAL_SETUP         = 'giants_attributeBoolObjectDataHierarchicalSetup'

UI_CONTROL_FRAME_OPTIONS              = 'giants_frameOptions'
UI_CONTROL_FRAME_SHAPE_SUBPARTS       = 'giants_frameShapeSubparts'
UI_CONTROL_FRAME_MISC                 = 'giants_frameMisc'
UI_CONTROL_FRAME_GAME_PATH            = 'giants_frameGamePath'
UI_CONTROL_FRAME_XML_FILE             = 'giants_frameXmlFile'
UI_CONTROL_FRAME_OUTPUT_FILE          = 'giants_frameOutputFile'
UI_CONTROL_FRAME_EXPORT               = 'giants_frameExport'
UI_CONTROL_FRAME_ERRORS               = 'giants_frameErrors'
UI_CONTROL_FRAME_XML_IDENTIFIER       = 'giants_frameXmlIdentifier'
UI_CONTROL_FRAME_RIGID_BODY           = 'giants_frameRigidBody'
UI_CONTROL_FRAME_JOINT                = 'giants_frameJoint'
UI_CONTROL_FRAME_RENDERING            = 'giants_frameRendering'
UI_CONTROL_FRAME_VISIBILITY_CONDITION = 'giants_frameVisibilityCondition'
UI_CONTROL_FRAME_OBJECT_DATA_TEXTURE  = 'giants_frameObjectDataTexture'
UI_CONTROL_FRAME_LIGHT_ATTRIBUTES     = 'giants_frameLightAttributes'

def I3DLoadUseDepthMapShadows(k, v, node):
    lightNode = I3DUtils.getLightFromTransformNode(node)
    if lightNode is not None:
        I3DShowLightAttributesFrame(lightNode.useDepthMapShadows())
    else:
        cmds.frameLayout(UI_CONTROL_FRAME_LIGHT_ATTRIBUTES, edit=True, visible=False)

def I3DSaveUseDepthMapShadows(k, v, node):
    lightNode = I3DUtils.getLightFromTransformNode(node)
    if lightNode is not None:
        lightNode.setUseDepthMapShadows(cmds.checkBox(UI_CONTROL_BOOL_USE_DEPTH_MAP_SHADOWS, query=True, value=True))

def I3DResetUIUseDepthMapShadows(k, v):
    cmds.checkBox(UI_CONTROL_BOOL_USE_DEPTH_MAP_SHADOWS, edit=True, value=False)

def I3DLoadCastsShadows(k, v, node):
    options = v['options']
    perInstanceCastsShadows = options[I3DGetAttributeValue(node, k, v['defaultValue'])]

    castsShadows = True
    perInstance = False
    if perInstanceCastsShadows == 'Yes':
        castsShadows = True
        perInstance = True
    elif perInstanceCastsShadows == 'No':
        castsShadows = False
        perInstance = True
    else:
        # Use geometry case
        shape = I3DGetNonIntermediateShapeFromNode(node)
        if shape != None and cmds.objExists(shape + ".castsShadows"):
            castsShadows = cmds.getAttr(shape + '.castsShadows')

    cmds.checkBox(UI_CONTROL_BOOL_CASTS_SHADOWS, edit=True, value=castsShadows)
    cmds.checkBox(UI_CONTROL_BOOL_CASTS_SHADOWS_PER_INSTANCE, edit=True, value=perInstance)

def I3DSaveCastsShadows(k, v, node):
    perInstance = cmds.checkBox(UI_CONTROL_BOOL_CASTS_SHADOWS_PER_INSTANCE, query=True, value=True)
    castsShadows = cmds.checkBox(UI_CONTROL_BOOL_CASTS_SHADOWS, query=True, value=True)
    if perInstance:
        if castsShadows:
            I3DSaveAttributeEnum(node, k, v['options'].index('Yes'), v['options'])
        else:
            I3DSaveAttributeEnum(node, k, v['options'].index('No'), v['options'])
    else:
        I3DSaveAttributeEnum(node, k, v['options'].index('UseGeometry'), v['options'])

        shape = I3DGetNonIntermediateShapeFromNode(node)
        if shape != None and cmds.objExists(shape + ".castsShadows"):
            cmds.setAttr(shape + ".castsShadows", castsShadows)

def I3DSaveVertexCompressionRange(k, v, node):
    selectedVertexCompressionRangeCallback = cmds.optionMenu(UI_CONTROL_ENUM_VERTEX_COMPRESSION_RANGE, q=True, v=True)
    if selectedVertexCompressionRangeCallback == 'Auto':
        I3DRemoveAttribute(node, k)
    else:
        I3DSaveAttributeEnum(node, k, v['options'].index(selectedVertexCompressionRangeCallback), v['options'])

def I3DResetUICastsShadows(k, v):
    cmds.checkBox(UI_CONTROL_BOOL_CASTS_SHADOWS, edit=True, value=True)
    cmds.checkBox(UI_CONTROL_BOOL_CASTS_SHADOWS_PER_INSTANCE, edit=True, value=False)

def I3DLoadReceiveShadows(k, v, node):
    options = v['options']
    perInstanceReceiveShadows = options[I3DGetAttributeValue(node, k, v['defaultValue'])]

    receiveShadows = True
    perInstance = False
    if perInstanceReceiveShadows == 'Yes':
        receiveShadows = True
        perInstance = True
    elif perInstanceReceiveShadows == 'No':
        receiveShadows = False
        perInstance = True
    else:
        # Use geometry case
        shape = I3DGetNonIntermediateShapeFromNode(node)
        if shape != None and cmds.objExists(shape + ".receiveShadows"):
            receiveShadows = cmds.getAttr(shape + '.receiveShadows')

    cmds.checkBox(UI_CONTROL_BOOL_RECEIVE_SHADOWS, edit=True, value=receiveShadows)
    cmds.checkBox(UI_CONTROL_BOOL_RECEIVE_SHADOWS_PER_INSTANCE, edit=True, value=perInstance)

def I3DSaveReceiveShadows(k, v, node):
    perInstance = cmds.checkBox(UI_CONTROL_BOOL_RECEIVE_SHADOWS_PER_INSTANCE, query=True, value=True)
    receiveShadows = cmds.checkBox(UI_CONTROL_BOOL_RECEIVE_SHADOWS, query=True, value=True)
    if perInstance:
        if receiveShadows:
            I3DSaveAttributeEnum(node, k, v['options'].index('Yes'), v['options'])
        else:
            I3DSaveAttributeEnum(node, k, v['options'].index('No'), v['options'])
    else:
        I3DSaveAttributeEnum(node, k, v['options'].index('UseGeometry'), v['options'])

        shape = I3DGetNonIntermediateShapeFromNode(node)
        if shape != None and cmds.objExists(shape + ".receiveShadows"):
            cmds.setAttr(shape + ".receiveShadows", receiveShadows)

def I3DResetUIReceiveShadows(k, v):
    cmds.checkBox(UI_CONTROL_BOOL_RECEIVE_SHADOWS, edit=True, value=True)
    cmds.checkBox(UI_CONTROL_BOOL_RECEIVE_SHADOWS_PER_INSTANCE, edit=True, value=False)

def I3DLoadEnableScattering(k, v, node):
    lightNode = I3DUtils.getLightFromTransformNode(node)
    if lightNode is None:
        return

    if not lightNode.typeName() in ['spotLight', 'pointLight']:
        cmds.checkBox(UI_CONTROL_BOOL_LIGHT_SCATTERING, edit=True, enable=False)
        cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_INTENSITY, edit=True, enable=False)
        cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_CONE_ANGLE, edit=True, enable=False)
        return

    cmds.checkBox(UI_CONTROL_BOOL_LIGHT_SCATTERING, edit=True, enable=True)
    enabled = I3DGetAttributeValue(node, k, v['defaultValue'])
    cmds.checkBox(v['uiControl'], edit=True, v=enabled)
    I3DEnableScatteringAttributes(enabled)

def I3DLoadScatteringIntensity(k, v, node):
    cmds.floatField(v['uiControl'], edit=True, v=I3DGetAttributeValue(node, k, v['defaultValue']))
    I3DChangeLightScatteringIntensity(None)

def I3DLoadScatteringConeAngle(k, v, node):
    cmds.floatField(v['uiControl'], edit=True, v=I3DGetAttributeValue(node, k, v['defaultValue']))
    I3DChangeLightScatteringConeAngle(None)

def I3DGetSelectedSpotLight():
    nodes = cmds.selectedNodes(dagObjects=True)
    if not nodes is None:
        node = nodes[0]
        if cmds.objectType(node, isType='transform'):
            lightNode = I3DUtils.getLightFromTransformNode(node)
            if lightNode is not None and lightNode.typeName() in ['spotLight']:
                return lightNode
    return None

def I3DEnableScatteringAttributes(enable):
    cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_INTENSITY, edit=True, enable=enable)
    cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_CONE_ANGLE, edit=True, enable=enable)
    spotLightNode = I3DGetSelectedSpotLight()
    if (spotLightNode is None):
        cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_CONE_ANGLE, edit=True, enable=False)

def I3DChangeLightScatteringIntensity(unused):
    try:
        current_value = cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_INTENSITY, query=True, value=True)

        # Attempt to convert the input value to a float
        float_value = float(current_value)

        if float_value < 0:
            raise ValueError("Light scattering intensity value must be non-negative")

    except ValueError as e:
        cmds.warning("Invalid input: {}".format(e))
        cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_INTENSITY, edit=True, value=1)

def I3DChangeLightScatteringConeAngle(unused):
    spotLightNode = I3DGetSelectedSpotLight()
    if (spotLightNode is None):
        return

    cone_angle = cmds.getAttr("{}.coneAngle".format(spotLightNode.name()))
    try:
        current_value = cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_CONE_ANGLE, query=True, value=True)

        # Attempt to convert the input value to a float
        float_value = float(current_value)

        if float_value < 0 or float_value > cone_angle:
            raise ValueError("{} > {} Light scattering cone angle value must be non-negative and less then the spotLight cone angle.".format(float_value, cone_angle))

    except ValueError as e:
        cmds.warning("Invalid input: {}".format(e))
        cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_CONE_ANGLE, edit=True, value=cone_angle)


SETTINGS_VEHICLE_ATTRIBUTES = []
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Default'                             , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':0,   'nonRenderable':False, 'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})  # 'weatherRequiredMask': '0', 'viewerSpacialityRequiredMask': '0'
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Vehicle - Compound'                  , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':True,  'kinematic':False, 'compound':True,  'compoundChild':False, 'trigger':False, 'collision':True,  'colMaskPresetName':'VEHICLE',               'clipDistance':300, 'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})  # old collisionMask 2109442
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Vehicle - CompoundChild'             , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':True,  'kinematic':False, 'compound':False, 'compoundChild':True,  'trigger':False, 'collision':True,  'colMaskPresetName':'VEHICLE',               'clipDistance':0,   'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 0.001}})  # old collisionMask 2109442
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Vehicle - CC - NoTipAny'             , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':True,  'kinematic':False, 'compound':False, 'compoundChild':True,  'trigger':False, 'collision':True,  'colMaskPresetName':'VEHICLE_NO_TIP_ANY',    'clipDistance':0,   'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 0.001}})  # old collisionMask 2109442
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Vehicle - CC - Fork Front'           , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':True,  'kinematic':False, 'compound':False, 'compoundChild':True,  'trigger':False, 'collision':True,  'colMaskPresetName':"FORK_FRONT",            'clipDistance':0,   'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 0.001}})  # old collisionMask 134225920
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Vehicle - CC - Fork Back'            , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':True,  'kinematic':False, 'compound':False, 'compoundChild':True,  'trigger':False, 'collision':True,  'colMaskPresetName':"FORK_BACK",             'clipDistance':0,   'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 0.001}})  # old collisionMask 134225922
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'TrafficVehicle'                      , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':True,  'compound':True,  'compoundChild':False, 'trigger':False, 'collision':True,  'colMaskPresetName':"TRAFFIC_VEHICLE",       'clipDistance':350, 'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})  # old collisionMask 28704
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'FillVolume'                          , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':300, 'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':1, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'EmitterShape'                        , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':300, 'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':1, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'ShadowFocusBox'                      , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':150, 'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':1, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'ExactFillRootNode'                   , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':True,  'compound':True,  'compoundChild':False, 'trigger':False, 'collision':True,  'colMaskPresetName':"EXACT_FILL_ROOT_NODE",  'clipDistance':0,   'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})  # old collisionMask 1073741824
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Trigger - Discharge/Trailer Trigger' , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':True,  'compound':True,  'compoundChild':False, 'trigger':True,  'collision':True,  'colMaskPresetName':"FILL_TRIGGER",          'clipDistance':0,   'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})  # old collisionMask 1073741824
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Trigger - DynamicMountTrigger'       , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':True,  'compound':True,  'compoundChild':False, 'trigger':True,  'collision':True,  'colMaskPresetName':"DYN_OBJECT_TRIGGER",    'clipDistance':0,   'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})  # old collisionMask 18874368
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Trigger - Player'                    , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':True,  'compound':True,  'compoundChild':False, 'trigger':True,  'collision':True,  'colMaskPresetName':"PLAYER_TRIGGER",        'clipDistance':0,   'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})  # old collisionMask 1048576
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Trigger - Player & Vehicle'          , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':True,  'compound':True,  'compoundChild':False, 'trigger':True,  'collision':True,  'colMaskPresetName':"PLAYER_VEHICLE_TRIGGER",'clipDistance':0,   'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})  # old collisionMask 3145728
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Trigger - Vehicle'                   , 'isPhyiscObject':True,  'attributeValues':{'static':False, 'dynamic':False, 'kinematic':True,  'compound':True,  'compoundChild':False, 'trigger':True,  'collision':True,  'colMaskPresetName':"VEHICLE_TRIGGER",       'clipDistance':0,   'nonRenderable':True,  'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})  # old collisionMask 2097152
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Lights -  Real'                      , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':75,  'nonRenderable':False, 'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Lights -  Static'                    , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':75,  'nonRenderable':False, 'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Decals - Small'                      , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':30,  'nonRenderable':False, 'decalLayer': 1, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Decals - Big'                        , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':50,  'nonRenderable':False, 'decalLayer': 1, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Exterior'                            , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':300, 'nonRenderable':False, 'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Interior'                            , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':300, 'nonRenderable':False, 'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Mirrors'                             , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':20,  'nonRenderable':False, 'decalLayer': 1, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'WindowsInside'                       , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':20,  'nonRenderable':False, 'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'WindowsOutside'                      , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':200, 'nonRenderable':False, 'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Hair - Layer 1'                      , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':300, 'nonRenderable':False, 'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Hair - Layer 2'                      , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':10,  'nonRenderable':False, 'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})
SETTINGS_VEHICLE_ATTRIBUTES.append({'name': 'Hair - Layer 3'                      , 'isPhyiscObject':False, 'attributeValues':{'static':False, 'dynamic':False, 'kinematic':False, 'compound':False, 'compoundChild':False, 'trigger':False, 'collision':False,                                              'clipDistance':5,   'nonRenderable':False, 'decalLayer': 0, 'cpuMesh':0, 'density': 1.0}})


SETTINGS_ATTRIBUTES = {}
SETTINGS_ATTRIBUTES['i3D_lockedGroup']          = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_LOCKED_GROUP}
SETTINGS_ATTRIBUTES['i3D_static']               = {'type':TYPE_BOOL,  'defaultValue':True   , 'uiControl':UI_CONTROL_BOOL_STATIC, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_dynamic']              = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_DYNAMIC, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_kinematic']            = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_KINEMATIC, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_compound']             = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_COMPOUND, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_compoundChild']        = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_COMPOUND_CHILD, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_collision']            = {'type':TYPE_BOOL,  'defaultValue':True   , 'uiControl':UI_CONTROL_BOOL_COLLISION, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_collisionFilterGroup'] = {'type':TYPE_HEX,   'defaultValue':hex(colMaskFlags.defaultColFilterGroup), 'uiControl':UI_CONTROL_STRING_COLLISION_FILTER_GROUP, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_collisionFilterMask']  = {'type':TYPE_HEX,   'defaultValue':hex(colMaskFlags.defaultColFilterMask), 'uiControl':UI_CONTROL_STRING_COLLISION_FILTER_MASK, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_solverIterationCount'] = {'type':TYPE_INT,   'defaultValue':4      , 'uiControl':UI_CONTROL_INT_SOLVER_ITERATIONS, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_restitution']          = {'type':TYPE_FLOAT, 'defaultValue':0.0    , 'uiControl':UI_CONTROL_FLOAT_RESTITUTION, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_staticFriction']       = {'type':TYPE_FLOAT, 'defaultValue':0.5    , 'uiControl':UI_CONTROL_FLOAT_STATIC_FRICTION, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_dynamicFriction']      = {'type':TYPE_FLOAT, 'defaultValue':0.5    , 'uiControl':UI_CONTROL_FLOAT_DYNAMIC_FRICTION, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_linearDamping']        = {'type':TYPE_FLOAT, 'defaultValue':0.0    , 'uiControl':UI_CONTROL_FLOAT_LINEAR_DAMPING, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_angularDamping']       = {'type':TYPE_FLOAT, 'defaultValue':0.01   , 'uiControl':UI_CONTROL_FLOAT_ANGULAR_DAMPING, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_density']              = {'type':TYPE_FLOAT, 'defaultValue':1.0    , 'uiControl':UI_CONTROL_FLOAT_DENSITY, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_ccd']                  = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_CCD}
SETTINGS_ATTRIBUTES['i3D_trigger']              = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_TRIGGER, 'nodeTypeFilter':NODETYPE_MESH}
SETTINGS_ATTRIBUTES['i3D_splitType']            = {'type':TYPE_INT,   'defaultValue':0      , 'uiControl':UI_CONTROL_INT_SPLITTYPE}
SETTINGS_ATTRIBUTES['i3D_splitMinU']            = {'type':TYPE_FLOAT, 'defaultValue':0.0    , 'uiControl':UI_CONTROL_FLOAT_SPLIT_MIN_U}
SETTINGS_ATTRIBUTES['i3D_splitMinV']            = {'type':TYPE_FLOAT, 'defaultValue':0.0    , 'uiControl':UI_CONTROL_FLOAT_SPLIT_MIN_V}
SETTINGS_ATTRIBUTES['i3D_splitMaxU']            = {'type':TYPE_FLOAT, 'defaultValue':1.0    , 'uiControl':UI_CONTROL_FLOAT_SPLIT_MAX_U}
SETTINGS_ATTRIBUTES['i3D_splitMaxV']            = {'type':TYPE_FLOAT, 'defaultValue':1.0    , 'uiControl':UI_CONTROL_FLOAT_SPLIT_MAX_V}
SETTINGS_ATTRIBUTES['i3D_splitUvWorldScale']    = {'type':TYPE_FLOAT, 'defaultValue':1.0    , 'uiControl':UI_CONTROL_FLOAT_SPLIT_UV_WORLD_SCALE}
SETTINGS_ATTRIBUTES['i3D_joint']                = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_JOINT}
SETTINGS_ATTRIBUTES['i3D_projection']           = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_PROJECTION}
SETTINGS_ATTRIBUTES['i3D_projDistance']         = {'type':TYPE_FLOAT, 'defaultValue':0.01   , 'uiControl':UI_CONTROL_FLOAT_PROJECTION_DISTANCE}
SETTINGS_ATTRIBUTES['i3D_projAngle']            = {'type':TYPE_FLOAT, 'defaultValue':0.01   , 'uiControl':UI_CONTROL_FLOAT_PROJECTION_ANGLE}
SETTINGS_ATTRIBUTES['i3D_xAxisDrive']           = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_XAXIS_DRIVE}
SETTINGS_ATTRIBUTES['i3D_yAxisDrive']           = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_YAXIS_DRIVE}
SETTINGS_ATTRIBUTES['i3D_zAxisDrive']           = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_ZAXIS_DRIVE}
SETTINGS_ATTRIBUTES['i3D_drivePos']             = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_DRIVE_POSITION}
SETTINGS_ATTRIBUTES['i3D_driveForceLimit']      = {'type':TYPE_FLOAT, 'defaultValue':100000.0 , 'uiControl':UI_CONTROL_FLOAT_DRIVE_FORCE_LIMIT}
SETTINGS_ATTRIBUTES['i3D_driveSpring']          = {'type':TYPE_FLOAT, 'defaultValue':1.0    , 'uiControl':UI_CONTROL_FLOAT_DRIVE_SPRING}
SETTINGS_ATTRIBUTES['i3D_driveDamping']         = {'type':TYPE_FLOAT, 'defaultValue':0.01   , 'uiControl':UI_CONTROL_FLOAT_DRIVE_DAMPING}
SETTINGS_ATTRIBUTES['i3D_breakableJoint']       = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_BREAKABLE}
SETTINGS_ATTRIBUTES['i3D_jointBreakForce']      = {'type':TYPE_FLOAT, 'defaultValue':0.0    , 'uiControl':UI_CONTROL_FLOAT_BREAK_FORCE}
SETTINGS_ATTRIBUTES['i3D_jointBreakTorque']     = {'type':TYPE_FLOAT, 'defaultValue':0.0    , 'uiControl':UI_CONTROL_FLOAT_BREAK_TORQUE}
SETTINGS_ATTRIBUTES['i3D_oc']                   = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_OCCLUDER}
SETTINGS_ATTRIBUTES['i3D_nonRenderable']        = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_NON_RENDERABLE}
SETTINGS_ATTRIBUTES['i3D_distanceBlending']     = {'type':TYPE_BOOL,  'defaultValue':True   , 'uiControl':UI_CONTROL_BOOL_DISTANCE_BLENDING}
SETTINGS_ATTRIBUTES['i3D_clipDistance']         = {'type':TYPE_FLOAT, 'defaultValue':0.0    , 'uiControl':UI_CONTROL_FLOAT_CLIP_DISTANCE}
SETTINGS_ATTRIBUTES['i3D_objectMask']           = {'type':TYPE_HEX,   'defaultValue':"0xff" , 'uiControl':UI_CONTROL_STRING_OBJECT_MASK}
SETTINGS_ATTRIBUTES['i3D_navMeshMask']          = {'type':TYPE_HEX,   'defaultValue':"0xff" , 'uiControl':UI_CONTROL_INT_NAV_MESH_MASK}
SETTINGS_ATTRIBUTES['i3D_doubleSided']          = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_DOUBLE_SIDED}
SETTINGS_ATTRIBUTES['i3D_materialHolder']       = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_MATERIAL_HOLDER}
SETTINGS_ATTRIBUTES['i3D_castsShadows']         = {                   'defaultValue':0      , 'loadFunction':I3DLoadCastsShadows  , 'saveFunction':I3DSaveCastsShadows  , 'resetUIFunction':I3DResetUICastsShadows  , 'options':['UseGeometry','Yes','No']}
SETTINGS_ATTRIBUTES['i3D_receiveShadows']       = {                   'defaultValue':0      , 'loadFunction':I3DLoadReceiveShadows, 'saveFunction':I3DSaveReceiveShadows, 'resetUIFunction':I3DResetUIReceiveShadows, 'options':['UseGeometry','Yes','No']}
SETTINGS_ATTRIBUTES['i3D_renderedInViewports']  = {'type':TYPE_BOOL,  'defaultValue':True   , 'uiControl':UI_CONTROL_BOOL_RENDERED_IN_VIEWPORTS}
SETTINGS_ATTRIBUTES['i3D_decalLayer']           = {'type':TYPE_INT,   'defaultValue':0      , 'uiControl':UI_CONTROL_INT_DECAL_LAYER}
SETTINGS_ATTRIBUTES['i3D_mergeGroup']           = {'type':TYPE_INT,   'defaultValue':0      , 'uiControl':UI_CONTROL_INT_MERGE_GROUP}
SETTINGS_ATTRIBUTES['i3D_mergeGroupRoot']       = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_MERGE_GROUP_ROOT}
SETTINGS_ATTRIBUTES['i3D_boundingVolume']       = {'type':TYPE_STRING,'defaultValue':''     , 'uiControl':UI_CONTROL_STRING_BOUNDINGVOLUME}
SETTINGS_ATTRIBUTES['i3D_vertexCompressionRange'] = {'type':TYPE_ENUM, 'defaultValue':0, 'uiControl':UI_CONTROL_ENUM_VERTEX_COMPRESSION_RANGE, 'options': ['Auto', '0.5', '1', '2', '4', '8', '16', '32', '64', '128', '256'], 'saveFunction':I3DSaveVertexCompressionRange}

SETTINGS_ATTRIBUTES['i3D_isSoftShadow']               = {                   'defaultValue':False  , 'loadFunction':I3DLoadUseDepthMapShadows  , 'saveFunction':I3DSaveUseDepthMapShadows  , 'resetUIFunction':I3DResetUIUseDepthMapShadows  , 'options':['UseGeometry','Yes','No']}
SETTINGS_ATTRIBUTES['i3D_softShadowsLightSize']       = {'type':TYPE_FLOAT, 'defaultValue':0.05   , 'uiControl':UI_CONTROL_FLOAT_SOFT_SHADOWS_LIGHT_SIZE}
SETTINGS_ATTRIBUTES['i3D_softShadowsLightDistance']   = {'type':TYPE_FLOAT, 'defaultValue':15     , 'uiControl':UI_CONTROL_FLOAT_SOFT_SHADOWS_LIGHT_DISTANCE}
SETTINGS_ATTRIBUTES['i3D_softShadowsDepthBiasFactor'] = {'type':TYPE_FLOAT, 'defaultValue':5      , 'uiControl':UI_CONTROL_FLOAT_SOFT_SHADOWS_DEPTH_BIAS_FACTOR}
SETTINGS_ATTRIBUTES['i3D_softShadowsMaxPenumbraSize'] = {'type':TYPE_FLOAT, 'defaultValue':0.5    , 'uiControl':UI_CONTROL_FLOAT_SOFT_SHADOWS_MAX_PENUMBRA_SIZE}
SETTINGS_ATTRIBUTES['i3D_iesProfileFile']             = {'type':TYPE_STRING,'defaultValue':''     , 'uiControl':UI_CONTROL_STRING_IES_PROFILE_FILE}
SETTINGS_ATTRIBUTES['i3D_isLightScattering']          = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_LIGHT_SCATTERING, 'loadFunction':I3DLoadEnableScattering}
SETTINGS_ATTRIBUTES['i3D_lightScatteringIntensity']   = {'type':TYPE_FLOAT, 'defaultValue':1      , 'uiControl':UI_CONTROL_FLOAT_LIGHT_SCATTERING_INTENSITY, 'loadFunction':I3DLoadScatteringIntensity}
SETTINGS_ATTRIBUTES['i3D_lightScatteringConeAngle']   = {'type':TYPE_FLOAT, 'defaultValue':40     , 'uiControl':UI_CONTROL_FLOAT_LIGHT_SCATTERING_CONE_ANGLE, 'loadFunction':I3DLoadScatteringConeAngle}

SETTINGS_ATTRIBUTES['i3D_terrainDecal']         = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_TERRAIN_DECAL}
SETTINGS_ATTRIBUTES['i3D_cpuMesh']              = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_CPUMESH}
SETTINGS_ATTRIBUTES['i3D_mergeChildren']        = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_MERGE_CHILDREN}
SETTINGS_ATTRIBUTES['i3D_mergeChildrenFreezeTrans'] = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_MERGE_CHILDREN_FREEZE_TRANS}
SETTINGS_ATTRIBUTES['i3D_mergeChildrenFreezeRot'] = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_MERGE_CHILDREN_FREEZE_ROT}
SETTINGS_ATTRIBUTES['i3D_mergeChildrenFreezeScale'] = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_MERGE_CHILDREN_FREEZE_SCALE}
SETTINGS_ATTRIBUTES['i3D_lod']                  = {'type':TYPE_BOOL,  'defaultValue':False  , 'uiControl':UI_CONTROL_BOOL_LOD}
SETTINGS_ATTRIBUTES['i3D_lod1']                 = {'type':TYPE_FLOAT, 'defaultValue':0.0      , 'uiControl':UI_CONTROL_FLOAT_CHILD_1_DISTANCE}
SETTINGS_ATTRIBUTES['i3D_lod2']                 = {'type':TYPE_FLOAT, 'defaultValue':0.0      , 'uiControl':UI_CONTROL_FLOAT_CHILD_2_DISTANCE}
SETTINGS_ATTRIBUTES['i3D_lod3']                 = {'type':TYPE_FLOAT, 'defaultValue':0.0      , 'uiControl':UI_CONTROL_FLOAT_CHILD_3_DISTANCE}
SETTINGS_ATTRIBUTES['i3D_lodBlending']          = {'type':TYPE_BOOL,  'defaultValue':True   , 'uiControl':UI_CONTROL_BOOL_LOD_BLENDING}
SETTINGS_ATTRIBUTES['i3D_scaled']               = {'type':TYPE_BOOL,  'defaultValue':False      , 'uiControl':UI_CONTROL_BOOL_SCALED}

SETTINGS_ATTRIBUTES['i3D_objectDataFilePath']               = {'type':TYPE_STRING,'defaultValue':''    , 'uiControl':UI_CONTROL_STRING_OBJECT_DATA_FILEPATH}
SETTINGS_ATTRIBUTES['i3D_objectDataExportPosition']         = {'type':TYPE_BOOL,  'defaultValue':True  , 'uiControl':UI_CONTROL_BOOL_OBJECT_DATA_EXPORT_POSITION}
SETTINGS_ATTRIBUTES['i3D_objectDataExportOrientation']      = {'type':TYPE_BOOL,  'defaultValue':True  , 'uiControl':UI_CONTROL_BOOL_OBJECT_DATA_EXPORT_ORIENTATION}
SETTINGS_ATTRIBUTES['i3D_objectDataExportScale']            = {'type':TYPE_BOOL,  'defaultValue':False , 'uiControl':UI_CONTROL_BOOL_OBJECT_DATA_EXPORT_SCALE}
SETTINGS_ATTRIBUTES['i3D_objectDataHideFirstAndLastObject'] = {'type':TYPE_BOOL,  'defaultValue':False , 'uiControl':UI_CONTROL_BOOL_OBJECT_DATA_HIDE_FIRST_AND_LAST_OBJECT}
SETTINGS_ATTRIBUTES['i3D_objectDataHierarchicalSetup']      = {'type':TYPE_BOOL,  'defaultValue':False , 'uiControl':UI_CONTROL_BOOL_OBJECT_DATA_HIERARCHICAL_SETUP}

SETTINGS_ATTRIBUTES['i3D_minuteOfDayStart']             = {'type':TYPE_INT,     'defaultValue':0,       'uiControl':UI_CONTROL_INT_MINUTE_OF_DAY_START}
SETTINGS_ATTRIBUTES['i3D_minuteOfDayEnd']               = {'type':TYPE_INT,     'defaultValue':0,       'uiControl':UI_CONTROL_INT_MINUTE_OF_DAY_END}
SETTINGS_ATTRIBUTES['i3D_dayOfYearStart']               = {'type':TYPE_INT,     'defaultValue':0,       'uiControl':UI_CONTROL_INT_DAY_OF_YEAR_START}
SETTINGS_ATTRIBUTES['i3D_dayOfYearEnd']                 = {'type':TYPE_INT,     'defaultValue':0,       'uiControl':UI_CONTROL_INT_DAY_OF_YEAR_END}

SETTINGS_ATTRIBUTES['i3D_weatherRequiredMask']          = {'type':TYPE_HEX,     'defaultValue':'0x0',     'uiControl':UI_CONTROL_STRING_WEATHER_REQUIRED_MASK}
SETTINGS_ATTRIBUTES['i3D_weatherPreventMask']           = {'type':TYPE_HEX,     'defaultValue':'0x0',     'uiControl':UI_CONTROL_STRING_WEATHER_PREVENT_MASK}
SETTINGS_ATTRIBUTES['i3D_viewerSpacialityRequiredMask'] = {'type':TYPE_HEX,     'defaultValue':'0x0',     'uiControl':UI_CONTROL_STRING_VIEWER_SPACIALITY_REQUIRED_MASK}
SETTINGS_ATTRIBUTES['i3D_viewerSpacialityPreventMask']  = {'type':TYPE_HEX,     'defaultValue':'0x0',     'uiControl':UI_CONTROL_STRING_VIEWER_SPACIALITY_PREVENT_MASK}
SETTINGS_ATTRIBUTES['i3D_renderInvisible']              = {'type':TYPE_BOOL,    'defaultValue':False,   'uiControl':UI_CONTROL_BOOL_RENDER_INVISIBLE}
SETTINGS_ATTRIBUTES['i3D_visibleShaderParameter']       = {'type':TYPE_FLOAT,   'defaultValue':1.0,     'uiControl':UI_CONTROL_FLOAT_VISIBLE_SHADER_PARAMETER}
SETTINGS_ATTRIBUTES['i3D_forceVisibilityCondition']     = {'type':TYPE_BOOL,    'defaultValue':False,   'uiControl':UI_CONTROL_BOOL_FORCE_VISIBILITY_CONDITION}

SETTINGS_EXPORTER = {}
SETTINGS_EXPORTER['i3D_exportIK'] =                {'type':TYPE_BOOL,   'checkBoxGrpId':1, 'uiControl':UI_CONTROL_EXPORT_1}
SETTINGS_EXPORTER['i3D_exportAnimation'] =         {'type':TYPE_BOOL,   'checkBoxGrpId':2, 'uiControl':UI_CONTROL_EXPORT_1}
SETTINGS_EXPORTER['i3D_exportShapes'] =            {'type':TYPE_BOOL,   'checkBoxGrpId':3, 'uiControl':UI_CONTROL_EXPORT_1}
SETTINGS_EXPORTER['i3D_exportNurbsCurves'] =       {'type':TYPE_BOOL,   'checkBoxGrpId':1, 'uiControl':UI_CONTROL_EXPORT_2}
SETTINGS_EXPORTER['i3D_exportLights'] =            {'type':TYPE_BOOL,   'checkBoxGrpId':2, 'uiControl':UI_CONTROL_EXPORT_2}
SETTINGS_EXPORTER['i3D_exportCameras'] =           {'type':TYPE_BOOL,   'checkBoxGrpId':3, 'uiControl':UI_CONTROL_EXPORT_2}
SETTINGS_EXPORTER['i3D_exportParticleSystems'] =   {'type':TYPE_BOOL,   'checkBoxGrpId':1, 'uiControl':UI_CONTROL_EXPORT_3}
SETTINGS_EXPORTER['i3D_exportDefaultCameras'] =    {'type':TYPE_BOOL,   'checkBoxGrpId':2, 'uiControl':UI_CONTROL_EXPORT_3}
SETTINGS_EXPORTER['i3D_exportUserAttributes'] =    {'type':TYPE_BOOL,   'checkBoxGrpId':3, 'uiControl':UI_CONTROL_EXPORT_3}
SETTINGS_EXPORTER['i3D_exportBynaryFiles'] =       {'type':TYPE_BOOL,   'checkBoxGrpId':1, 'uiControl':UI_CONTROL_EXPORT_4}
SETTINGS_EXPORTER['i3D_exportIgnoreBindPoses'] =   {'type':TYPE_BOOL,   'checkBoxGrpId':2, 'uiControl':UI_CONTROL_EXPORT_4}
SETTINGS_EXPORTER['i3D_exportObjectDataTexture'] = {'type':TYPE_BOOL,   'checkBoxGrpId':3, 'uiControl':UI_CONTROL_EXPORT_4}
SETTINGS_EXPORTER['i3D_exportNormals'] =           {'type':TYPE_BOOL,   'checkBoxGrpId':1, 'uiControl':UI_CONTROL_SHAPES_1}
SETTINGS_EXPORTER['i3D_exportColors'] =            {'type':TYPE_BOOL,   'checkBoxGrpId':2, 'uiControl':UI_CONTROL_SHAPES_1}
SETTINGS_EXPORTER['i3D_exportTexCoords'] =         {'type':TYPE_BOOL,   'checkBoxGrpId':3, 'uiControl':UI_CONTROL_SHAPES_1}
SETTINGS_EXPORTER['i3D_exportSkinWeigths'] =       {'type':TYPE_BOOL,   'checkBoxGrpId':1, 'uiControl':UI_CONTROL_SHAPES_2}
SETTINGS_EXPORTER['i3D_exportMergeGroups'] =       {'type':TYPE_BOOL,   'checkBoxGrpId':2, 'uiControl':UI_CONTROL_SHAPES_2}
SETTINGS_EXPORTER['i3D_exportVerbose'] =           {'type':TYPE_BOOL,   'checkBoxGrpId':1, 'uiControl':UI_CONTROL_MISC_1}
SETTINGS_EXPORTER['i3D_exportRelativePaths'] =     {'type':TYPE_BOOL,   'checkBoxGrpId':2, 'uiControl':UI_CONTROL_MISC_1}
SETTINGS_EXPORTER['i3D_exportFloatEpsilon'] =      {'type':TYPE_BOOL,   'checkBoxGrpId':3, 'uiControl':UI_CONTROL_MISC_1}
SETTINGS_EXPORTER['i3D_exportUseProjectPath'] =    {'type':TYPE_BOOL,   'checkBoxGrpId':1, 'uiControl':UI_CONTROL_GAME_PATH}
SETTINGS_EXPORTER['i3D_exportBasegamePaths'] =     {'type':TYPE_BOOL,   'checkBoxGrpId':2, 'uiControl':UI_CONTROL_GAME_PATH}
SETTINGS_EXPORTER['i3D_exportUpdateXML'] =         {'type':TYPE_BOOL,   'checkBoxGrpId':1, 'uiControl':UI_CONTROL_MISC_2}
SETTINGS_EXPORTER['i3D_exportUseMayaFilename'] =   {'type':TYPE_BOOL,   'checkBoxGrpId':1, 'uiControl':UI_CONTROL_BOOL_USE_MAYA_FILENAME}
SETTINGS_EXPORTER['i3D_exportOutputFile'] =        {'type':TYPE_STRING,                    'uiControl':UI_CONTROL_STRING_FILE_PATH}
SETTINGS_EXPORTER['i3D_exportXMLConfigFile'] =     {'type':TYPE_STRING,                    'uiControl':UI_CONTROL_STRING_XML_FILE_PATH}
SETTINGS_EXPORTER['i3D_exportGamePath'] =          {'type':TYPE_STRING,                    'uiControl':UI_CONTROL_STRING_GAME_PATH}

SETTINGS_FRAMES = {}
SETTINGS_FRAMES['giants_frameOptions'] = {'uiControl':UI_CONTROL_FRAME_OPTIONS}
SETTINGS_FRAMES['giants_frameShapeSubparts'] = {'uiControl':UI_CONTROL_FRAME_SHAPE_SUBPARTS}
SETTINGS_FRAMES['giants_frameMisc'] = {'uiControl':UI_CONTROL_FRAME_MISC}
SETTINGS_FRAMES['giants_frameGamePath'] = {'uiControl':UI_CONTROL_FRAME_GAME_PATH}
SETTINGS_FRAMES['giants_frameXmlFile'] = {'uiControl':UI_CONTROL_FRAME_XML_FILE}
SETTINGS_FRAMES['giants_frameOutputFile'] = {'uiControl':UI_CONTROL_FRAME_OUTPUT_FILE}
SETTINGS_FRAMES['giants_frameExport'] = {'uiControl':UI_CONTROL_FRAME_EXPORT}
SETTINGS_FRAMES['giants_frameErrors'] = {'uiControl':UI_CONTROL_FRAME_ERRORS}
SETTINGS_FRAMES['giants_frameRigidBody'] = {'uiControl':UI_CONTROL_FRAME_RIGID_BODY}
SETTINGS_FRAMES['giants_frameJoint'] = {'uiControl':UI_CONTROL_FRAME_JOINT}
SETTINGS_FRAMES['giants_frameRendering'] = {'uiControl':UI_CONTROL_FRAME_RENDERING}
SETTINGS_FRAMES['giants_frameVisibilityCondition'] = {'uiControl':UI_CONTROL_FRAME_VISIBILITY_CONDITION}
SETTINGS_FRAMES['giants_frameObjectDataTexture'] = {'uiControl':UI_CONTROL_FRAME_OBJECT_DATA_TEXTURE}
SETTINGS_FRAMES['giants_frameLightAttributes'] = {'uiControl':UI_CONTROL_FRAME_LIGHT_ATTRIBUTES}

SETTINGS_SHADERS = {}
SETTINGS_SHADER_PARAMETERS = {}
SETTINGS_SHADER_TEXTURES = {}
SETTINGS_SHADER_PARAMETER_TEMPLATES = {}

# plugins
g_loadedPlugins = []
g_loadedPluginsByPage = {}
g_loadedPluginCommands = {}

def pluginEvent(eventName, *args):
    global g_loadedPlugins
    for plugin in g_loadedPlugins:
        if hasattr(plugin, eventName):
            func = getattr(plugin, eventName)
            try:
                func(args)
            except TypeError as err:
                func()


def loadPlugin(file):
    if file[-3:] == ".py":
        try:
            pluginModule = importlib.import_module(file[:-3])
            I3DUtils.reloadModule(pluginModule)

            plugin = pluginModule.getI3DExporterPlugin()
            g_loadedPlugins.append(plugin)

            if hasattr(plugin, "page"):
                if plugin.page not in g_loadedPluginsByPage:
                    g_loadedPluginsByPage[plugin.page] = []
                g_loadedPluginsByPage[plugin.page].append(plugin)

            print("Loaded I3DExporter Plugin '%s'" % plugin.name)
        except ImportError as e:
            print("Failed to load plugin '%s'" % file[:-3])
            print(e)
        except SyntaxError as e:
            print("Failed to load plugin '%s'" % file[:-3])
            print(e)

def loadPluginsFromDirectory(directory):
    sys.path.append(directory)
    sys.path.append(directory+"/external")

    for file in os.listdir(directory):
        if file != "external" and os.path.isdir(directory+"/"+file):
            fullPath = directory+"/"+file

            sys.path.append(fullPath+"/external")
            sys.path.append(fullPath)
            for subFile in os.listdir(fullPath):
                loadPlugin(subFile)

        loadPlugin(file)

EXPORTER_PLUGINS_PATH = os.path.dirname(os.path.abspath(__file__)) + "/plugins"
loadPluginsFromDirectory(EXPORTER_PLUGINS_PATH)

if "g_userSetup" in sys.modules:
    for directory in sys.modules["g_userSetup"].additionalPluginDirectories:
        loadPluginsFromDirectory(directory)

g_loadedPlugins = sorted(g_loadedPlugins, key=lambda plugin: plugin.prio)

for name, plugins in g_loadedPluginsByPage.items():
    g_loadedPluginsByPage[name] = sorted(g_loadedPluginsByPage[name], key=lambda plugin: plugin.prio)

def I3DLoadSettings(unused):
    if cmds.objExists(SETTINGS_PREFIX):
        # load export settings
        for k,v in SETTINGS_EXPORTER.items():
            if v['type'] == TYPE_BOOL:
                if I3DAttributeExists(SETTINGS_PREFIX, k):
                    value = cmds.getAttr(SETTINGS_PREFIX+'.'+k)
                    if v['checkBoxGrpId'] == 1:
                        cmds.checkBoxGrp(v['uiControl'], edit=True, v1=value)
                    elif v['checkBoxGrpId'] == 2:
                        cmds.checkBoxGrp(v['uiControl'], edit=True, v2=value)
                    elif v['checkBoxGrpId'] == 3:
                        cmds.checkBoxGrp(v['uiControl'], edit=True, v3=value)
                    elif v['checkBoxGrpId'] == 4:
                        cmds.checkBoxGrp(v['uiControl'], edit=True, v4=value)

        # output file
        outputFileLocationPath = ''
        if I3DAttributeExists(SETTINGS_PREFIX, 'i3D_exportOutputFile'):
            outputFileLocationPath = cmds.getAttr(SETTINGS_PREFIX+'.i3D_exportOutputFile')
        if(outputFileLocationPath == 0 or outputFileLocationPath == ''):
            outputFileLocationPath = 'C:/myExport.i3d'
        cmds.textField(UI_CONTROL_STRING_FILE_PATH, edit=True, text=outputFileLocationPath)

        # xml config file
        xmlConfigFilePath = ''
        if I3DAttributeExists(SETTINGS_PREFIX, 'i3D_exportXMLConfigFile'):
            xmlConfigFilePath = cmds.getAttr(SETTINGS_PREFIX+'.i3D_exportXMLConfigFile')
        if(xmlConfigFilePath == 0 or xmlConfigFilePath == ''):
            xmlConfigFilePath = ''
        cmds.textField(UI_CONTROL_STRING_XML_FILE_PATH, edit=True, text=xmlConfigFilePath)

        if I3DAttributeExists(SETTINGS_PREFIX, 'i3D_exportGamePath'):
            gamePath = cmds.getAttr(SETTINGS_PREFIX+'.i3D_exportGamePath')
            cmds.textField(UI_CONTROL_STRING_GAME_PATH, edit=True, text=gamePath)

    # update all nodes
    dagObjects = cmds.ls(dag=True, l=True, tr=True)
    for node in dagObjects:
        I3DUpdateLayers(node)

def I3DSaveSettings(unused):
    selectedNodes = I3DUtils.getSelectedObjects()

    if cmds.objExists(SETTINGS_PREFIX):
        # delete old settings node
        cmds.delete(SETTINGS_PREFIX)

    # add new settings node
    cmds.createNode('script', name=SETTINGS_PREFIX)

    # add export settings
    for k,v in SETTINGS_EXPORTER.items():
        if v['type'] == TYPE_BOOL:
            cmds.addAttr(sn=k, ln=k, nn=k, at='bool')
            if v['checkBoxGrpId'] == 1:
                cmds.setAttr(SETTINGS_PREFIX+'.'+k, cmds.checkBoxGrp(v['uiControl'], q=True, v1=True))
            elif v['checkBoxGrpId'] == 2:
                cmds.setAttr(SETTINGS_PREFIX+'.'+k, cmds.checkBoxGrp(v['uiControl'], q=True, v2=True))
            elif v['checkBoxGrpId'] == 3:
                cmds.setAttr(SETTINGS_PREFIX+'.'+k, cmds.checkBoxGrp(v['uiControl'], q=True, v3=True))
            elif v['checkBoxGrpId'] == 4:
                cmds.setAttr(SETTINGS_PREFIX+'.'+k, cmds.checkBoxGrp(v['uiControl'], q=True, v4=True))
        elif v['type'] == TYPE_STRING:
            cmds.addAttr(sn=k, ln=k, nn=k, dt='string')
            cmds.setAttr(SETTINGS_PREFIX+'.'+k, cmds.textField(v['uiControl'], q=True, text=True), type='string')

    # select previous selected nodes again
    cmds.select(selectedNodes)

def I3DShowChangeLog(unused):
    ChangeLogDialog.show_modal_dialog()

def I3DSetShaderPath(folderPath):
    cmds.textField(UI_CONTROL_STRING_SHADER_PATH, edit=True, text=folderPath)
    if folderPath != '' and os.path.exists(folderPath):
        I3DUpdateShaderList(folderPath)
        I3DSetProjectSetting("GIANTS_SHADER_DIR", folderPath)

    return

def I3DOnSelectionChanged():
    if cmds.window(UI_CONTROL_WINDOW, exists=True):
        shader = None
        obj = cmds.ls(sl=True, long=True)
        if not obj is None and len(obj) > 0:
            index = I3DUtils.getIndexPath(obj[0])
            cmds.textField(UI_CONTROL_STRING_NODE_INDEX, edit=True, text=index)
            cmds.textField(UI_CONTROL_STRING_NODE_NAME, edit=True, text=obj[0])
            cmds.textField(UI_CONTROL_STRING_IDENTIFIER, edit=True, text=I3DGetAttributeValue(obj[0], 'i3D_xmlIdentifier', ''))

            matList = I3DUtils.getObjectMaterials(obj[-1])
            if matList == None or len(matList) == 0:
                mat = I3DUtils.getMaterialFromSelection()
                if mat != None:
                    matList = [mat]

            if matList != None and len(matList) > 0:
                shader = matList[0]

        if shader != None:
            try:
                cmds.optionMenu(UI_CONTROL_SELECTED_MATERIAL, edit=True, v=shader)
            except RuntimeError:
                I3DReloadMaterialList()
                cmds.optionMenu(UI_CONTROL_SELECTED_MATERIAL, edit=True, v=shader)
                #I3DShowWarning("Material {} is not in selected material dropdown.".format(shader))
        else:
            cmds.optionMenu(UI_CONTROL_SELECTED_MATERIAL, edit=True, sl=1)

        selectedShader = I3DGetSelectedShader()
        cmds.button(UI_CONTROL_DUPLICATE_MATERIAL, e=True, enable=(selectedShader is not None and cmds.nodeType(selectedShader) == 'GLSLShader'))

        if I3DGetProjectSetting(UI_SETTINGS_LOAD_ON_SELECT) == "True":
            I3DLoadMaterial(shader)
            I3DLoadObjectAttributes(None)

def I3DOnSceneOpened():
    if cmds.window(UI_CONTROL_WINDOW, exists=True):
        I3DReloadMaterialList()

    I3DLoadSettings(None)

def I3DCloseExporter():
    I3DRemoveSelectionChangedListener()
    cmds.optionVar( intValue=('GIANTS_EXPORTER_WIDTH', cmds.window(UI_CONTROL_WINDOW, q=True, width=True)))
    cmds.optionVar( intValue=('GIANTS_EXPORTER_HEIGHT', cmds.window(UI_CONTROL_WINDOW, q=True, height=True)))
    cmds.deleteUI(UI_CONTROL_WINDOW, window=True)

def I3DExport():
    # if hasattr(cmds, 'dockControl'):
        # if cmds.dockControl(UI_CONTROL_DOCK, exists=True):
            # cmds.optionVar( intValue=('GIANTS_EXPORTER_WIDTH', cmds.window(UI_CONTROL_WINDOW, q=True, width=True)))
            # cmds.optionVar( intValue=('GIANTS_EXPORTER_HEIGHT', cmds.window(UI_CONTROL_WINDOW, q=True, height=True)))
            # cmds.deleteUI(UI_CONTROL_DOCK)

    if cmds.window(UI_CONTROL_WINDOW, exists=True):
        I3DCloseExporter()

# Handle legacy locked groups
    legacyLockedGroupAttributeName = 'i3D_exportLockedGroup'
    if I3DAttributeExists(SETTINGS_PREFIX, legacyLockedGroupAttributeName):
        if I3DGetAttributeValue(SETTINGS_PREFIX, legacyLockedGroupAttributeName, False):
            it = OpenMaya.MItDag(OpenMaya.MItDag.kDepthFirst)
            if not it.isDone():
                dagNode = OpenMaya.MFnDagNode(it.currentItem())
                for i in range(0, dagNode.childCount()):
                    child = dagNode.child(i)
                    if child.hasFn(OpenMaya.MFn.kTransform):
                        transform = OpenMaya.MFnTransform(dagNode.child(i))

                        if transform.isDefaultNode() or transform.inUnderWorld():
                            continue

                        pathName = transform.fullPathName()
                        pathParts = pathName.split('|')
                        if len(pathParts) != 2:
                            continue

                        I3DSaveAttributeBool(pathName, 'i3D_lockedGroup', True)

        I3DRemoveAttribute(SETTINGS_PREFIX, legacyLockedGroupAttributeName)
# End handle legacy locked groups

    def onClose(*args):
        pluginEvent("onExporterClose")

    pluginEvent("onExporterPreOpen")

    tabLabels = []

    mainWindow = cmds.window(UI_CONTROL_WINDOW, title=TITLE, maximizeButton=False, menuBar=True, closeCommand=onClose)
# MAIN MENU
    editMenu = cmds.menu(parent=mainWindow, label='Edit')
    cmds.menuItem(parent=editMenu, label='Load Options', command=I3DLoadSettings)
    cmds.menuItem(parent=editMenu, label='Save Options', command=I3DSaveSettings)
    settingsMenu = cmds.menu(parent=mainWindow, label='Settings')
    cmds.menuItem(parent=settingsMenu, label='Load on Selection', checkBox=I3DGetProjectSetting(UI_SETTINGS_LOAD_ON_SELECT) == 'True', command=I3DOnLoadOnSelectionMenuCallback)
    helpMenu = cmds.menu(parent=mainWindow, label='Help', helpMenu=True )
    cmds.menuItem(parent=helpMenu, label='GDN Homepage...', image='help.png', command=('cmds.showHelp(\'http://gdn.giants-software.com/index.php\', absolute=True )'))
    cmds.menuItem(parent=helpMenu, label='Change Log', command=I3DShowChangeLog)

    form = cmds.formLayout(parent=mainWindow)
    curSelectionFrame = cmds.frameLayout(parent=form, label='Current selection', cll=False, mh=5, mw=5 )
    curSelectionLayout = cmds.rowLayout('curSelectionLayout', parent=curSelectionFrame, adjustableColumn=3, numberOfColumns=3)
    cmds.text(parent=curSelectionLayout, label='Node', width=60, align='left', annotation='')
    cmds.textField(UI_CONTROL_STRING_NODE_INDEX, parent=curSelectionLayout, text='', editable=True, width=145, enterCommand=I3DSelectIndex)
    cmds.textField(UI_CONTROL_STRING_NODE_NAME, parent=curSelectionLayout, text='', editable=False)

    # xml identifier
    xmlIdItems = cmds.rowLayout(UI_CONTROL_FRAME_XML_IDENTIFIER, parent=form, adjustableColumn=4, numberOfColumns=4)
    cmds.text(parent=xmlIdItems, label='Identifier', width=60, align='left', annotation='')
    cmds.textField(UI_CONTROL_STRING_IDENTIFIER, parent=xmlIdItems, text='', annotation='XMl-Config identifier. Valid characters [A-Z0-9_]', editable=True, width=145)
    cmds.button(parent=xmlIdItems, label='Set', height=17, width=110, command=I3DSetIdentifier)
    cmds.button(parent=xmlIdItems, label='Remove', height=17, command=I3DRemoveIdentifier)

    tabs = cmds.tabLayout(parent=form, innerMarginWidth=5, innerMarginHeight=5, height=700)
    cmds.formLayout(form, edit=True, attachForm=((curSelectionFrame, 'top', 5), (curSelectionFrame, 'left', 5), (curSelectionFrame, 'right', 5),
                                                 (xmlIdItems, 'top', 55), (xmlIdItems, 'left', 10), (xmlIdItems, 'right', 10),
                                                 (tabs, 'top', 90), (tabs, 'left', 5), (tabs, 'right', 5), (tabs, 'bottom', 5)))

# TAB EXPORT
    tabExport = cmds.formLayout()
    exportColums = cmds.columnLayout(parent=tabExport, adjustableColumn=True)

    # export options
    exportOptionsFrame = cmds.frameLayout(UI_CONTROL_FRAME_OPTIONS, parent=exportColums, label='Options', w=390, cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    exportOptionsItems = cmds.columnLayout(parent=exportOptionsFrame)
    cmds.checkBoxGrp(UI_CONTROL_EXPORT_1, parent=exportOptionsItems, height=28, numberOfCheckBoxes=3, v1=False, v2=True, v3=True, labelArray3=['IK', 'Animation', 'Shapes'], cc=I3DSaveSettings )
    cmds.checkBoxGrp(UI_CONTROL_EXPORT_2, parent=exportOptionsItems, height=28, numberOfCheckBoxes=3, v1=False, v2=True, v3=True, labelArray3=['Nurbs Curves', 'Lights', 'Cameras'], cc=I3DSaveSettings )
    cmds.checkBoxGrp(UI_CONTROL_EXPORT_3, parent=exportOptionsItems, height=28, numberOfCheckBoxes=3, v1=False, v2=False, v3=True, labelArray3=['Particle System', 'Default Cameras', 'User Attributes'], cc=I3DSaveSettings )
    cmds.checkBoxGrp(UI_CONTROL_EXPORT_4, parent=exportOptionsItems, height=28, numberOfCheckBoxes=3, v1=True,  v2=False, v3=False, labelArray3=['Binary Files', 'Ignore Bind Poses', 'Object Data Texture'], cc=I3DSaveSettings )

    # shape export subparts
    exportSubpartsFrame = cmds.frameLayout(UI_CONTROL_FRAME_SHAPE_SUBPARTS, parent=exportColums, label='Shape Subparts', cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    exportSubpartsItems = cmds.columnLayout(parent=exportSubpartsFrame)
    cmds.checkBoxGrp(UI_CONTROL_SHAPES_1, parent=exportSubpartsItems, height=28, numberOfCheckBoxes=3, v1=True, v2=True, v3=True, labelArray3=['Normals', 'Vertex Colors', 'UVs'], cc=I3DSaveSettings )
    cmds.checkBoxGrp(UI_CONTROL_SHAPES_2, parent=exportSubpartsItems, height=28, numberOfCheckBoxes=2, v1=True, v2=True, labelArray2=['Skin Weights', 'Merge Groups'], cc=I3DSaveSettings )

    # miscellaneous
    exportMiscFrame = cmds.frameLayout(UI_CONTROL_FRAME_MISC, parent=exportColums, label='Miscellaneous', cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState)
    exportMiscItems = cmds.columnLayout(parent=exportMiscFrame)
    cmds.checkBoxGrp(UI_CONTROL_MISC_1, parent=exportMiscItems, height=28, numberOfCheckBoxes=3, v1=True, v2=True, v3=True, labelArray3=['Verbose', 'Relative Paths', 'Float Epsilon'], cc=I3DSaveSettings )

    # game path
    gamePathFrame = cmds.frameLayout(UI_CONTROL_FRAME_GAME_PATH, parent=exportColums, label='Game Location', w=390, cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    gamePathItems = cmds.columnLayout('gamepathColumnItem', parent=gamePathFrame, adjustableColumn=True)
    cmds.checkBoxGrp(UI_CONTROL_GAME_PATH, parent=gamePathItems, height=28, numberOfCheckBoxes=2, v1=True, v2=True, labelArray2=['Use Project Path', 'Use Game Relative Path'], cc=I3DSaveSettings)

    fileLayout = cmds.formLayout('fileLayout', parent=gamePathItems)
    textGamePath = cmds.text('textGamePath', parent=fileLayout, label='Game Location')
    textFieldGamePath = cmds.textField(UI_CONTROL_STRING_GAME_PATH, parent=fileLayout, width=250, editable=False)
    buttonSelectGamePath = cmds.symbolButton(UI_CONTROL_SELECT_GAME_PATH, parent=fileLayout, image='navButtonBrowse.xpm', command=I3DOpenSelectGamePath, annotation='Set Game Location')

    cmds.formLayout(fileLayout, edit=True, attachForm=((textGamePath, 'top', 4), (textGamePath, 'left', 2),
                                                         (textFieldGamePath, 'top', 0), (textFieldGamePath, 'left', 80), (textFieldGamePath, 'right', 35),
                                                         (buttonSelectGamePath, 'top', 0), (buttonSelectGamePath, 'right', 5), (buttonSelectGamePath, 'bottom', 5)))

    # xml config file
    xmlFileFrame = cmds.frameLayout(UI_CONTROL_FRAME_XML_FILE, parent=exportColums, label='XML Config File(s)', w=390, cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    fileItems = cmds.columnLayout('xmlFileColumnItem', parent=xmlFileFrame, adjustableColumn=True)
    cmds.checkBoxGrp(UI_CONTROL_MISC_2, parent=fileItems, height=28, numberOfCheckBoxes=1, v1=True, label1='Update XML on Export', cc=I3DSaveSettings )

    xmlFileItems = cmds.formLayout('xmlFileItems', parent=fileItems)
    textXmlFolder = cmds.text('textXmlFolder', parent=xmlFileItems, label='XML Location' )
    textFieldXmlFolder = cmds.textField(UI_CONTROL_STRING_XML_FILE_PATH, parent=xmlFileItems, width=200, editable=False)
    buttonAddXml = cmds.symbolButton('buttonAddXml', parent=xmlFileItems, image='menuIconAdd.xpm', command=I3DOpenAddXmlConfigDialog, annotation='Add another Vehicle XML-Config file')
    buttonRemoveXml = cmds.symbolButton('buttonRemoveXml', parent=xmlFileItems, image='setEdRemoveCmd.xpm', command=I3DRemoveXmlConfig, annotation='Remove last added Vehicle XML-Config file')
    buttonSelectXml = cmds.symbolButton('buttonSelectXml', parent=xmlFileItems, image='navButtonBrowse.xpm', command=I3DOpenSetXmlConfigDialog, annotation='Set Vehicle XML-Config file')

    cmds.formLayout(xmlFileItems, edit=True, attachForm=((textXmlFolder, 'top', 4), (textXmlFolder, 'left', 2),
                                                         (textFieldXmlFolder, 'top', 0), (textFieldXmlFolder, 'left', 80), (textFieldXmlFolder, 'right', 80),
                                                         (buttonAddXml, 'top', 0), (buttonAddXml, 'right', 40),
                                                         (buttonRemoveXml, 'top', 0), (buttonRemoveXml, 'right', 25),
                                                         (buttonSelectXml, 'top', 0), (buttonSelectXml, 'right', 5)
                                                         ))

    # output file
    fileFrame = cmds.frameLayout(UI_CONTROL_FRAME_OUTPUT_FILE, parent=exportColums, label='Output File', w=390, cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    fileItems = cmds.columnLayout('fileItems', parent=fileFrame, adjustableColumn=True)

    cmds.checkBoxGrp(UI_CONTROL_BOOL_USE_MAYA_FILENAME, parent=fileItems, height=28, numberOfCheckBoxes=1, v1=False, label1='Use maya filename', cc=I3DSaveSettings )

    fileLayout = cmds.formLayout('fileLayout', parent=fileItems)
    textI3dFile = cmds.text('textI3dFile', parent=fileLayout, label='File Location' )
    textFieldI3dFile = cmds.textField(UI_CONTROL_STRING_FILE_PATH, parent=fileLayout, width=250, editable=False)
    buttonSelectI3dFile = cmds.symbolButton('buttonSelectI3dFile', parent=fileLayout, image='navButtonBrowse.xpm', command=I3DOpenExportDialog, annotation='Set Export file' )

    cmds.formLayout(fileLayout, edit=True, attachForm=((textI3dFile, 'top', 4), (textI3dFile, 'left', 2),
                                                         (textFieldI3dFile, 'top', 0), (textFieldI3dFile, 'left', 80), (textFieldI3dFile, 'right', 35),
                                                         (buttonSelectI3dFile, 'top', 0), (buttonSelectI3dFile, 'right', 5), (buttonSelectI3dFile, 'bottom', 5)))


    # EXPORT
    # buttons
    buttonFrame = cmds.frameLayout(UI_CONTROL_FRAME_EXPORT, parent=exportColums, label='Export', cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState)

    checkForErrorsSettings = cmds.checkBoxGrp(UI_CONTROL_BOOL_ERROR_CHECK_SETTINGS, parent=buttonFrame, height=28, columnWidth=(1, 150), numberOfCheckBoxes=2, v1=True, v2=False, labelArray2=['Check Vertex Colors', 'Check UV Sets'])

    buttonColumns = cmds.columnLayout('buttonColumns', parent=buttonFrame, adjustableColumn=True, rowSpacing=5)
    buttonItems1 = cmds.formLayout('buttonItems1', parent=buttonColumns)
    buttonCheck = cmds.button(parent=buttonItems1, label='Check for Errors', height=30, command=I3DErrorCheck)
    buttonCheckCD = cmds.button(parent=buttonItems1, label='Check ClipDistances', height=30, command=I3DCheckClipDistances, annotation="Check ClipDinstance of all nodes based on the size of the biggest connected mesh.\nProvide buttons for quick fixing")
    buttonUpdate = cmds.button(parent=buttonItems1, label='Update XML', height=30, command=I3DUpdateXML)
    cmds.formLayout(buttonItems1, edit=True,
                            attachPosition=((buttonCheck, 'left', 0, 0),  (buttonCheck, 'right', 5, 33),
                                            (buttonCheckCD, 'left', 0, 33), (buttonCheckCD, 'right', 5, 66),
                                            (buttonUpdate, 'left', 0, 66), (buttonUpdate, 'right', 0, 100)))

    buttonItems2 = cmds.formLayout('buttonItems2', parent=buttonColumns)
    buttonExport = cmds.button(parent=buttonItems2, label='Export Selected', height=30, command=I3DExportSelected)
    buttonExportAll = cmds.button(parent=buttonItems2, label='Export All', height=30, command=I3DExportAll)
    cmds.formLayout(buttonItems2, edit=True,
                           attachPosition=((buttonExport, 'left', 0, 0),  (buttonExport, 'right', 5, 50),
                                           (buttonExportAll, 'left', 0, 50), (buttonExportAll, 'right', 0, 100)))

    # errors
    errorFrame = cmds.frameLayout(UI_CONTROL_FRAME_ERRORS, parent=tabExport, label='Validation & Errors', cll=False, mh=0, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState)

    global g_errorBox
    g_errorBox = ErrorBox.ErrorBox(UI_CONTROL_VALIDATION_SCROLL, errorFrame)

    cmds.formLayout(tabExport, edit=True, attachForm=((exportColums, 'top', 1), (exportColums, 'left', 1), (exportColums, 'right', 1), (errorFrame, 'left', 2), (errorFrame, 'right', 2), (errorFrame, 'bottom', 2)), attachControl=((errorFrame, 'top', 0, exportColums)))

    tabLabels.append((tabExport, 'Export'))

# TAB ATTRIBUTES
    tabAttributes = cmds.formLayout('TabAttributes', parent=tabs)

    # selected node
    loadedNodeFrame = cmds.frameLayout('loadedNodeFrame', parent=tabAttributes, label='Loaded Node', w=390, cll=False, mh=2, mw=2 )
    loadedNodeItems = cmds.columnLayout('loadedNodeItems', parent=loadedNodeFrame)
    loadedNodeNameItems = cmds.rowLayout('loadedNodeNameItems', parent=loadedNodeItems, adjustableColumn=2, numberOfColumns=2)
    cmds.text(parent=loadedNodeNameItems, label='Node Name', width=TEXT_WIDTH, align='left')
    cmds.textField(UI_CONTROL_STRING_LOADED_NODE_NAME, parent=loadedNodeNameItems, editable=False, width=245)

    I3DAddCheckBoxElement(loadedNodeItems, 'Locked group', UI_CONTROL_BOOL_LOCKED_GROUP, False)

    # predefined
    predefinedFrame = cmds.frameLayout(parent=tabAttributes, label='Predefined', w=390, cll=False, mh=2, mw=2 )
    predefinedItems = cmds.rowColumnLayout(parent=predefinedFrame, numberOfRows=1)
    vehicleAttributes = cmds.optionMenu(UI_OPTIONS_PREDEFINED_VEHICLES_ATTRIBUTES, parent=predefinedItems, annotation='Vehicle physics', changeCommand=I3DSetAttributePreset)
    for attribute in SETTINGS_VEHICLE_ATTRIBUTES:
        if attribute['isPhyiscObject']:
            cmds.menuItem(parent=vehicleAttributes, label=attribute['name'])
    meshAttributes = cmds.optionMenu(UI_OPTIONS_PREDEFINED_MESH_ATTRIBUTES, parent=predefinedItems, annotation='Mesh attributes', changeCommand=I3DSetAttributePreset)
    for attribute in SETTINGS_VEHICLE_ATTRIBUTES:
        if not attribute['isPhyiscObject']:
            cmds.menuItem(parent=meshAttributes, label=attribute['name'])

    # attributes
    attributesFrame = cmds.frameLayout(parent=tabAttributes, label='Attributes', w=390, cll=False, mh=2, mw=2 )
    scrollAttributes = cmds.scrollLayout('scrollAttributes', parent=attributesFrame, cr=True, verticalScrollBarAlwaysVisible=False)

    # rigid body
    rigidBodyFrame = cmds.frameLayout(UI_CONTROL_FRAME_RIGID_BODY, parent=scrollAttributes, label='Rigid Body', cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    rigidBodyItems = cmds.columnLayout('rigidBodyItems', parent=rigidBodyFrame)
    I3DAddCheckBoxElement(rigidBodyItems, 'Static', UI_CONTROL_BOOL_STATIC, False, 'passive Rigid Body non movable')
    I3DAddCheckBoxElement(rigidBodyItems, 'Kinematic', UI_CONTROL_BOOL_KINEMATIC, False, 'passive Rigid Body moveable')
    I3DAddCheckBoxElement(rigidBodyItems, 'Dynamic', UI_CONTROL_BOOL_DYNAMIC, False, 'active Rigid Body simulated')
    I3DAddCheckBoxElement(rigidBodyItems, 'Compound', UI_CONTROL_BOOL_COMPOUND, False, 'group of Rigid Bodies')
    I3DAddCheckBoxElement(rigidBodyItems, 'Compound child', UI_CONTROL_BOOL_COMPOUND_CHILD, False, 'part of a group of Rigid Bodies')
    I3DAddCheckBoxElement(rigidBodyItems, 'Collision', UI_CONTROL_BOOL_COLLISION)

    I3DAddDropDownElement(rigidBodyItems, "Collision Preset", UI_CONTROL_STRING_COLLISION_FILTER_PRESET, g_collisionPresetNamesOptions, width=200, maxVisibleItems=20, changeCommand=I3DCollisionFilterPresetSelected)
    I3DAddStringBitmaskFieldElement(rigidBodyItems, 'Collision Filter Group (Hex)', UI_CONTROL_STRING_COLLISION_FILTER_GROUP, colMaskFlags.defaultColFilterGroup, maskAttributes=g_collisionBitmaskAttributes, changeCommand=I3DCollisionUpdatePresetSelection)
    I3DAddStringBitmaskFieldElement(rigidBodyItems, 'Collision Filter Mask (Hex)', UI_CONTROL_STRING_COLLISION_FILTER_MASK, colMaskFlags.defaultColFilterMask, maskAttributes=g_collisionBitmaskAttributes, changeCommand=I3DCollisionUpdatePresetSelection)

    I3DAddRestitution(rigidBodyItems)
    I3DAddFloatFieldElement(rigidBodyItems, 'Static Friction', UI_CONTROL_FLOAT_STATIC_FRICTION, 0.5, 'The force that resists motion between two non-moving surfaces')
    I3DAddFloatFieldElement(rigidBodyItems, 'Dynamic Friction', UI_CONTROL_FLOAT_DYNAMIC_FRICTION, 0.5, 'The force that resists motion between two moving surfaces')
    I3DAddFloatFieldElement(rigidBodyItems, 'Linear Damping', UI_CONTROL_FLOAT_LINEAR_DAMPING, 0.0, 'Defines the slowdown factor for linear movement, affecting speed')
    I3DAddFloatFieldElement(rigidBodyItems, 'Angular Damping', UI_CONTROL_FLOAT_ANGULAR_DAMPING, 0.01, 'Defines the slowdown factor for angular movement, affecting spin')
    I3DAddMass(rigidBodyItems)
    I3DAddIntFieldElement(rigidBodyItems, 'Solver Iterations', UI_CONTROL_INT_SOLVER_ITERATIONS, 4, '')
    I3DAddCheckBoxElement(rigidBodyItems, 'CCD', UI_CONTROL_BOOL_CCD)
    I3DAddCheckBoxElement(rigidBodyItems, 'Trigger', UI_CONTROL_BOOL_TRIGGER)
    I3DAddIntFieldElement(rigidBodyItems, 'Split Type', UI_CONTROL_INT_SPLITTYPE, 0, '')
    I3DAddFloatFieldElements(rigidBodyItems, 'Split Uvs', [UI_CONTROL_FLOAT_SPLIT_MIN_U, UI_CONTROL_FLOAT_SPLIT_MIN_V, UI_CONTROL_FLOAT_SPLIT_MAX_U, UI_CONTROL_FLOAT_SPLIT_MAX_V, UI_CONTROL_FLOAT_SPLIT_UV_WORLD_SCALE], [0, 0, 1, 1, 1], ['', 'Min U', 'Min V', 'Max U', 'Max V', 'Uv World Scale'])

    # joint
    jointFrame = cmds.frameLayout(UI_CONTROL_FRAME_JOINT, parent=scrollAttributes, label='Joint', cll=1, mh=2, mw=2, cl=True, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    jointItems = cmds.columnLayout('jointItems', parent=jointFrame)
    I3DAddCheckBoxElement(jointItems, 'Joint', UI_CONTROL_BOOL_JOINT)
    I3DAddCheckBoxElement(jointItems, 'Projection', UI_CONTROL_BOOL_PROJECTION)
    I3DAddFloatFieldElement(jointItems, 'Projection distance', UI_CONTROL_FLOAT_PROJECTION_DISTANCE, 0, '')
    I3DAddFloatFieldElement(jointItems, 'Projection angle', UI_CONTROL_FLOAT_PROJECTION_ANGLE, 0, '')
    I3DAddCheckBoxElement(jointItems, 'X-Axis Drive', UI_CONTROL_BOOL_XAXIS_DRIVE)
    I3DAddCheckBoxElement(jointItems, 'Y-Axis Drive', UI_CONTROL_BOOL_YAXIS_DRIVE)
    I3DAddCheckBoxElement(jointItems, 'Z-Axis Drive', UI_CONTROL_BOOL_ZAXIS_DRIVE)
    I3DAddCheckBoxElement(jointItems, 'Drive Position', UI_CONTROL_BOOL_DRIVE_POSITION)
    I3DAddFloatFieldElement(jointItems, 'Drive Force Limit', UI_CONTROL_FLOAT_DRIVE_FORCE_LIMIT, 0, '')
    I3DAddFloatFieldElement(jointItems, 'Drive Spring', UI_CONTROL_FLOAT_DRIVE_SPRING, 0, '')
    I3DAddFloatFieldElement(jointItems, 'Drive Damping', UI_CONTROL_FLOAT_DRIVE_DAMPING, 0, '')
    I3DAddCheckBoxElement(jointItems, 'Breakable', UI_CONTROL_BOOL_BREAKABLE)
    I3DAddFloatFieldElement(jointItems, 'Break Force', UI_CONTROL_FLOAT_BREAK_FORCE, 0, '')
    I3DAddFloatFieldElement(jointItems, 'Break Torque', UI_CONTROL_FLOAT_BREAK_TORQUE, 0, '')

    # rendering
    renderingFrame = cmds.frameLayout(UI_CONTROL_FRAME_RENDERING, parent=scrollAttributes, label='Rendering', cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    renderingItems = cmds.columnLayout('renderingItems', parent=renderingFrame)
    I3DAddCheckBoxElement(renderingItems, 'Occluder', UI_CONTROL_BOOL_OCCLUDER)
    I3DAddCheckBoxElement(renderingItems, 'Non Renderable', UI_CONTROL_BOOL_NON_RENDERABLE)
    I3DAddFloatFieldElement(renderingItems, 'Clip Distance', UI_CONTROL_FLOAT_CLIP_DISTANCE, 0, '')
    I3DAddCheckBoxElement(renderingItems, 'Distance Blending', UI_CONTROL_BOOL_DISTANCE_BLENDING, True)

    I3DAddStringBitmaskFieldElement(renderingItems, 'Object Mask (Hex)', UI_CONTROL_STRING_OBJECT_MASK, SETTINGS_ATTRIBUTES['i3D_objectMask']['defaultValue'], maskAttributes=g_objectMaskAttributes)
    navMeshMaskAttributes = {'num_bits': 8}
    I3DAddStringBitmaskFieldElement(renderingItems, 'Nav Mesh Mask (Hex)', UI_CONTROL_INT_NAV_MESH_MASK, "0xff", '', maskAttributes=navMeshMaskAttributes)
    I3DAddCheckBoxElement(renderingItems, 'Double Sided', UI_CONTROL_BOOL_DOUBLE_SIDED)
    I3DAddCheckBoxElement(renderingItems, 'Material Holder', UI_CONTROL_BOOL_MATERIAL_HOLDER)
    layoutCastsShadows = cmds.rowLayout(parent=renderingItems, adjustableColumn=5, numberOfColumns=5)
    cmds.text(parent=layoutCastsShadows, label='Casts Shadows', width=TEXT_WIDTH, align='left')
    cmds.checkBox(UI_CONTROL_BOOL_CASTS_SHADOWS, parent=layoutCastsShadows, label='', align='left', value=True, annotation='', editable=True)
    cmds.text(parent=layoutCastsShadows, label='Per Instance', width=TEXT_WIDTH, align='right')
    cmds.checkBox(UI_CONTROL_BOOL_CASTS_SHADOWS_PER_INSTANCE, parent=layoutCastsShadows, label='', align='left', value=False, annotation='', editable=True)

    layoutReceiveShadows = cmds.rowLayout(parent=renderingItems, adjustableColumn=5, numberOfColumns=5)
    cmds.text(parent=layoutReceiveShadows, label='Receive Shadows', width=TEXT_WIDTH, align='left')
    cmds.checkBox(UI_CONTROL_BOOL_RECEIVE_SHADOWS, parent=layoutReceiveShadows, label='', align='left', value=True, annotation='', editable=True)
    cmds.text(parent=layoutReceiveShadows, label='Per Instance', width=TEXT_WIDTH, align='right')
    cmds.checkBox(UI_CONTROL_BOOL_RECEIVE_SHADOWS_PER_INSTANCE, parent=layoutReceiveShadows, label='', align='left', value=False, annotation='', editable=True)

    I3DAddCheckBoxElement(renderingItems, 'Rendered in Viewports', UI_CONTROL_BOOL_RENDERED_IN_VIEWPORTS, True)

    I3DAddIntFieldElement(renderingItems, 'Decal Layer', UI_CONTROL_INT_DECAL_LAYER, 0, '')
    I3DAddMergeGroup(renderingItems)
    I3DAddBoundVolume(renderingItems)
    I3DAddCheckBoxElement(renderingItems, 'Merge Children', UI_CONTROL_BOOL_MERGE_CHILDREN)
    I3DAddCheckBoxElement(renderingItems, 'Mrg Ch Freeze Translation', UI_CONTROL_BOOL_MERGE_CHILDREN_FREEZE_TRANS)
    I3DAddCheckBoxElement(renderingItems, 'Mrg Ch Freeze Rotation', UI_CONTROL_BOOL_MERGE_CHILDREN_FREEZE_ROT)
    I3DAddCheckBoxElement(renderingItems, 'Mrg Ch Freeze Scale', UI_CONTROL_BOOL_MERGE_CHILDREN_FREEZE_SCALE)
    I3DAddCheckBoxElement(renderingItems, 'Terrain Decal', UI_CONTROL_BOOL_TERRAIN_DECAL)
    I3DAddCheckBoxElement(renderingItems, 'CPU Mesh', UI_CONTROL_BOOL_CPUMESH)
    I3DAddCheckBoxElement(renderingItems, 'LOD', UI_CONTROL_BOOL_LOD)
    I3DAddFloatFieldElement(renderingItems, 'Child 0 Distance', UI_CONTROL_FLOAT_CHILD_0_DISTANCE, 0, '', False)
    I3DAddFloatFieldElement(renderingItems, 'Child 1 Distance', UI_CONTROL_FLOAT_CHILD_1_DISTANCE, 0, '')
    I3DAddFloatFieldElement(renderingItems, 'Child 2 Distance', UI_CONTROL_FLOAT_CHILD_2_DISTANCE, 0, '')
    I3DAddFloatFieldElement(renderingItems, 'Child 3 Distance', UI_CONTROL_FLOAT_CHILD_3_DISTANCE, 0, '')
    I3DAddCheckBoxElement(renderingItems, 'LOD Blending', UI_CONTROL_BOOL_LOD_BLENDING, True)
    I3DAddCheckBoxElement(renderingItems, 'Scaled', UI_CONTROL_BOOL_SCALED)
    I3DAddDropDownElement(renderingItems, 'Vertex Compression Range', UI_CONTROL_ENUM_VERTEX_COMPRESSION_RANGE, SETTINGS_ATTRIBUTES['i3D_vertexCompressionRange']['options'], 1, 'Vertex Compression Range', width=300, maxVisibleItems=40)

    # visibility condition / environment
    visCondFrame = cmds.frameLayout(UI_CONTROL_FRAME_VISIBILITY_CONDITION, parent=scrollAttributes, label='Visibility Condition', cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    visCondFrame = cmds.columnLayout('visibilityConditionItems', parent=visCondFrame)
    I3DAddIntFieldElement(visCondFrame,     'Minute Of Day Start',          UI_CONTROL_INT_MINUTE_OF_DAY_START, 0, '[1, 1441] the Nth minute of the day (0 to ignore)')
    I3DAddIntFieldElement(visCondFrame,     'Minute Of Day End',            UI_CONTROL_INT_MINUTE_OF_DAY_END,   0, '[1, 1441] the Nth minute of the day (0 to ignore)')
    I3DAddIntFieldElement(visCondFrame,     'Day Of Year Start',            UI_CONTROL_INT_DAY_OF_YEAR_START,   0, '[1, 365] the Nth day of the year (0 to ignore)')
    I3DAddIntFieldElement(visCondFrame,     'Day Of Year End',              UI_CONTROL_INT_DAY_OF_YEAR_END,     0, '[1, 365] the Nth day of the year (0 to ignore)')

    weatherMaskAttributes = {'bit_names': {0: "Sun", 1: "Rain", 2:"Hail", 3:"Snow", 4:"Cloudy", 5:"Day", 6:"Night", 7:"Spring", 8:"Summer", 9:"Autumn", 10:"Winter"}}
    I3DAddStringBitmaskFieldElement(visCondFrame, 'Weather Req. Mask (Hex)', UI_CONTROL_STRING_WEATHER_REQUIRED_MASK, '0x0', maskAttributes=weatherMaskAttributes)
    I3DAddStringBitmaskFieldElement(visCondFrame, 'Weather Prevent Mask (Hex)', UI_CONTROL_STRING_WEATHER_PREVENT_MASK, '0x0', maskAttributes=weatherMaskAttributes)

    viewerSpacialityAttributes = {'bit_names': {0: "INTERIOR", 1: "EXTERIOR", 2:"IN_VEHICLE", 3:"OUT_VEHICLE", 4:"LIGHTS_PROFILE_LOW", 5:"LIGHTS_PROFILE_HIGH"}}
    I3DAddStringBitmaskFieldElement(visCondFrame, 'View Space Req. Mask (Hex)', UI_CONTROL_STRING_VIEWER_SPACIALITY_REQUIRED_MASK, '0x0', maskAttributes=viewerSpacialityAttributes)
    I3DAddStringBitmaskFieldElement(visCondFrame, 'View Space Req. Mask (Hex)', UI_CONTROL_STRING_VIEWER_SPACIALITY_PREVENT_MASK, '0x0', maskAttributes=viewerSpacialityAttributes)

    I3DAddCheckBoxElement(visCondFrame,    'Render Invisible',              UI_CONTROL_BOOL_RENDER_INVISIBLE,               False,  annotation='If set, the object is always rendered and "visibility" must be controlled in the shader using the visible shader parameter')
    I3DAddFloatFieldElement(visCondFrame,  'Visible Shader Param',          UI_CONTROL_FLOAT_VISIBLE_SHADER_PARAMETER,      1.0,    annotation='This value is applied to the "visibility" shader parameter when the object is visible. If conditions are not met, 0 is passed to the shader.')

    I3DAddCheckBoxElement(visCondFrame,    'Force Visibility Condition',    UI_CONTROL_BOOL_FORCE_VISIBILITY_CONDITION,     False,  annotation='If all settings are default, the scenegraph parent in the game will define the visibility condition. Set this to force using the default settings.')

    # object data texture
    objectDataTextureFrame = cmds.frameLayout(UI_CONTROL_FRAME_OBJECT_DATA_TEXTURE, parent=scrollAttributes, label='Object Data Texture', cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    objectDataTextureItems = cmds.columnLayout('objectDataTextureItems', parent=objectDataTextureFrame)
    I3DAddTextFieldElement(objectDataTextureItems, 'FilePath', UI_CONTROL_STRING_OBJECT_DATA_FILEPATH,width=250)
    I3DAddCheckBoxElement(objectDataTextureItems, 'Export Position', UI_CONTROL_BOOL_OBJECT_DATA_EXPORT_POSITION,True)
    I3DAddCheckBoxElement(objectDataTextureItems, 'Export Orientation', UI_CONTROL_BOOL_OBJECT_DATA_EXPORT_ORIENTATION,True)
    I3DAddCheckBoxElement(objectDataTextureItems, 'Export Scale', UI_CONTROL_BOOL_OBJECT_DATA_EXPORT_SCALE,False)
    I3DAddCheckBoxElement(objectDataTextureItems, 'Hide First and Last', UI_CONTROL_BOOL_OBJECT_DATA_HIDE_FIRST_AND_LAST_OBJECT,False)
    I3DAddCheckBoxElement(objectDataTextureItems, 'Hierarchical Setup', UI_CONTROL_BOOL_OBJECT_DATA_HIERARCHICAL_SETUP,False)

    I3DAddLightAttributesFrame(scrollAttributes)

    # buttons
    attributeButtonItems = cmds.formLayout('ToolButtons', parent=tabAttributes)
    buttonLoad = cmds.button(UI_CONTROL_BUTTON_ATTRIBUTE_APPLY, parent=attributeButtonItems, label='Load', height=30, width=126, command=I3DLoadObjectAttributesLoadBtn)
    buttonApply = cmds.button(parent=attributeButtonItems, label='Apply', height=30, width=126, command=I3DApplySelectedAttributes)
    buttonRemove = cmds.button(parent=attributeButtonItems, label='Remove', height=30, width=126, command=I3DRemoveObjectAttributes)
    cmds.formLayout(attributeButtonItems, edit=True,
                                   attachPosition=((buttonLoad, 'left', 0, 0),  (buttonLoad, 'right', 5, 33),
                                                   (buttonApply, 'left', 0, 33), (buttonApply, 'right', 5, 66),
                                                   (buttonRemove, 'left', 0, 66), (buttonRemove, 'right', 0, 100)))



    cmds.formLayout(tabAttributes, edit=True, attachForm=((loadedNodeFrame, 'top', 2), (loadedNodeFrame, 'left', 2), (loadedNodeFrame, 'right', 2),
                                                          (predefinedFrame, 'top', 67), (predefinedFrame, 'left', 2), (predefinedFrame, 'right', 2),
                                                          (attributesFrame, 'top', 117), (attributesFrame, 'left', 2), (attributesFrame, 'right', 2), (attributesFrame, 'bottom', 32),
                                                          (attributeButtonItems, 'left', 2), (attributeButtonItems, 'right', 2), (attributeButtonItems, 'bottom', 2)))

    tabLabels.append((tabAttributes, 'Attributes'))

# TAB TOOLS

    def addPluginTab(title, plugins):
        tabPlugins = cmds.formLayout(parent=tabs)
        scrollPlugins = cmds.scrollLayout(parent=tabPlugins, cr=True, verticalScrollBarAlwaysVisible=False)
        scrollPluginsLayout = cmds.columnLayout(parent=scrollPlugins, adjustableColumn=True, columnOffset=('right', 1))

        # load all buttons from all plugins
        categorys = {}
        sortedCategorys = []
        for plugin in plugins:
            if hasattr(plugin, "getToolsButtons"):
                func = getattr(plugin, "getToolsButtons")
                buttons = func()
                for button in buttons:
                    category = button["category"]
                    if category not in categorys:
                        categorys[category] = {"name": category, "buttons": [], "customUIs": [], "prio": plugin.prio, "initialCollapseState": False}
                        sortedCategorys.append(categorys[category])
                    categorys[category]["buttons"].append(button)

                    if "categoryDefaultCollapsed" in button and button["categoryDefaultCollapsed"] is True:
                        categorys[category]["initialCollapseState"] = True

            if hasattr(plugin, "getToolsCustomUI"):
                func = getattr(plugin, "getToolsCustomUI")
                customUIs = func()
                for customUI in customUIs:
                    category = customUI["category"]
                    if category not in categorys:
                        categorys[category] = {"name": category, "buttons": [], "customUIs": [], "prio": plugin.prio, "initialCollapseState": False}
                        sortedCategorys.append(categorys[category])
                    categorys[category]["customUIs"].append(customUI)

                    if "categoryDefaultCollapsed" in customUI and customUI["categoryDefaultCollapsed"] is True:
                        categorys[category]["initialCollapseState"] = True

        sortedCategorys = sorted(sortedCategorys, key=lambda category: category["prio"])

        # create categorys from plugins
        categoryIndex = 0
        for category in sortedCategorys:

            uiControl = "toolsCategory_%d" % categoryIndex
            SETTINGS_FRAMES['giants_'+uiControl] = {'uiControl': uiControl}

            categoryFrame = cmds.frameLayout(uiControl, parent=scrollPluginsLayout, label=category["name"], cll=True, mh=2, mw=2, collapse=category["initialCollapseState"], expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState)

            buttons = category["buttons"]
            categoryColumns = None
            if len(buttons) > 0:
                categoryColumns = cmds.columnLayout('categoryColumns'+str(categoryIndex), parent=categoryFrame, adjustableColumn=True, rowSpacing=5)

            for i in range(0, len(buttons), 2):
                button1 = buttons[i]

                categoryItems = cmds.formLayout('categoryItems'+str(categoryIndex)+"_"+str(i), parent=categoryColumns)
                visButton1 = cmds.button(parent=categoryItems, label=button1["name"], height=30, command=button1["button_function"], annotation=button1["annotation"])
                attachPosition = ((visButton1, 'left', 0, 0), (visButton1, 'right', 5, 50))

                if i+1 < len(buttons):
                    button2 = buttons[i+1]
                    visButton2 = cmds.button(parent=categoryItems, label=button2["name"], height=30, command=button2["button_function"], annotation=button2["annotation"])
                    attachPosition = attachPosition + ((visButton2, 'left', 0, 50), (visButton2, 'right', 0, 100))

                cmds.formLayout(categoryItems, edit=True, attachPosition=attachPosition)

            customUIs = category["customUIs"]
            for i in range(0, len(customUIs)):
                customUIs[i]["customUIFunc"](categoryFrame)

            categoryIndex += 1

        # add plugin command to shelf
        global g_loadedPluginCommands

        optionMenuId = title.replace(" ", "_") + UI_OPTIONS_SHELF_COMMAND

        pluginShelfItems = cmds.formLayout(parent=tabPlugins)
        separator = cmds.separator(height=40, style='in', parent=pluginShelfItems)
        menuCommands = cmds.optionMenu(optionMenuId, parent=pluginShelfItems, height=31, annotation='Plugin Commands')

        for plugin in plugins:
            if hasattr(plugin, "getShelfScripts"):
                func = getattr(plugin, "getShelfScripts")
                pluginCommands = func()
                for command in pluginCommands:
                    label = "%s - %s" % (command['category'], command['name'])
                    g_loadedPluginCommands[label] = command
                    cmds.menuItem(parent=menuCommands, label=label)

        buttonCreate = cmds.button(parent=pluginShelfItems, label='Add to Shelf', height=30, command=lambda x: I3DAddPluginCommandToShelf(optionMenuId), annotation='Add the Plugin Command to shelf')
        cmds.formLayout(pluginShelfItems, edit=True, attachPosition=((separator, 'top', 0, 0), (separator, 'left', 0, 0),     (separator, 'right', 0, 100),
                                                                     (menuCommands, 'top', 0, 47), (menuCommands, 'left', 0, 0),   (menuCommands, 'right', 5, 70),
                                                                     (buttonCreate, 'top', 0, 47), (buttonCreate, 'left', 0, 70),  (buttonCreate, 'right', 0, 100)))

        cmds.formLayout(tabPlugins, edit=True, attachForm=((scrollPlugins, 'top', 0), (scrollPlugins, 'left', 0), (scrollPlugins, 'right', 0), (scrollPlugins, 'bottom', 45),
                                                           (pluginShelfItems, 'right', 2), (pluginShelfItems, 'left', 2), (pluginShelfItems, 'bottom', 0)))

        tabLabels.append((tabPlugins, title))

    global g_loadedPluginsByPage
    for name, plugins in g_loadedPluginsByPage.items():
        addPluginTab(name, g_loadedPluginsByPage[name])

# TAB MATERIAL
    tabShader = cmds.formLayout('TabShader', parent=tabs)
    tabShaderScroll = cmds.scrollLayout(parent=tabShader, cr=True)

    shaderFolderFrame = cmds.frameLayout('shaderFolderFrame', parent=tabShaderScroll, label='Shaders Folder', cll=False, mh=2, mw=2)
    shaderFolderItems = cmds.formLayout('shaderFolderItems', parent=shaderFolderFrame)
    textShaderFolder = cmds.text('textShaderFolder', parent=shaderFolderItems, label='Path' )
    textFieldShaderFolder = cmds.textField(UI_CONTROL_STRING_SHADER_PATH, parent=shaderFolderItems, width=250, editable=False)
    buttonSelectShader = cmds.symbolButton('buttonSelectShader', parent=shaderFolderItems, image='navButtonBrowse.xpm', command=I3DOpenShaderDialog, annotation='Set shader path' )
    cmds.formLayout(shaderFolderItems, edit=True, attachForm=((textShaderFolder, 'top', 4), (textShaderFolder, 'left', 2),
                                                              (textFieldShaderFolder, 'top', 0), (textFieldShaderFolder, 'left', 45), (textFieldShaderFolder, 'right', 35),
                                                              (buttonSelectShader, 'top', 0), (buttonSelectShader, 'right', 5)))

    # selected materials dropdown
    materialsFrame = cmds.frameLayout('materialsFrame', parent=tabShaderScroll, label='Materials', cll=False, mh=2, mw=2)
    materialRowLayout = cmds.rowLayout(parent=materialsFrame, adjustableColumn=4, numberOfColumns=4)
    I3DAddDropDownElement(materialRowLayout, 'Selected Material', UI_CONTROL_SELECTED_MATERIAL, ['None'], 1, 'Selected Material', changeCommand=I3DChangeMaterialSelectionCallback, width=300, maxVisibleItems=40)

    cmds.button(UI_CONTROL_DUPLICATE_MATERIAL, parent=materialRowLayout, label="Duplicate Material", height=20, command=I3DDuplicateMaterial, annotation="Duplicate the selected material.", enable=False)

    # shader section (contains shader xml, parameters, textures and variation)
    shaderFrame = cmds.frameLayout('shaderFrame', parent=tabShaderScroll, label='Material', cll=False, mh=2, mw=2)
    shaderScrollLayout = cmds.columnLayout('shaderScrollLayout', parent=shaderFrame, adjustableColumn=True)

    shaderSelectionLayout = cmds.rowLayout(parent=shaderScrollLayout, adjustableColumn=2, numberOfColumns=4)
    cmds.text(parent=shaderSelectionLayout, label="Shader", width=75, align='left', annotation="Custom Shader")
    cmds.optionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, width=200, parent=shaderSelectionLayout, changeCommand=I3DChangeCustomShaderCallback)
    cmds.text(parent=shaderSelectionLayout, label="Variation", width=50, align='right', annotation="Custom Shader Variation")
    cmds.optionMenu(UI_CONTROL_MENU_SHADER_VARIATION, parent=shaderSelectionLayout, width=200, changeCommand=I3DUpdateShaderVariationUI)

    parameterFrame = cmds.frameLayout(UI_CONTROL_LAYOUT_PARAMETERS, parent=shaderScrollLayout, label='Parameters', cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
    parameterScroll = cmds.scrollLayout(UI_CONTROL_SHADER_PARAMETERS_SCROLL, parent=parameterFrame, cr=True)
    cmds.columnLayout(UI_CONTROL_SHADER_PARAMETERS, parent=parameterScroll, adjustableColumn=True)

    texturesFrame = cmds.frameLayout(UI_CONTROL_LAYOUT_TEXTURES, parent=shaderScrollLayout, label='Textures', cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState)
    cmds.columnLayout(UI_CONTROL_SHADER_TEXTURES, parent=texturesFrame, adjustableColumn=True)


    # other attributes
    materialAttributesFrame = cmds.frameLayout('materialAttributesFrame', parent=shaderFrame, label='Attributes', cll=False, mh=2, mw=2)
    materialAttributesCol = cmds.columnLayout('materialAttributesCol', parent=materialAttributesFrame)

    I3DAddStringFieldElement(materialAttributesCol, 'Reference Material', UI_CONTROL_STRING_MATERIAL_REFERENCE_MATERIAL, '', width=200)

    slotNameLayout = cmds.rowLayout(parent=materialAttributesCol, adjustableColumn=2, numberOfColumns=3)
    cmds.text(parent=slotNameLayout, label="Slot Name", width=TEXT_WIDTH, align='left', annotation="Material slot name to be refered in the vehicle xml file")
    cmds.textField(UI_CONTROL_STRING_MATERIAL_SLOT_NAME, parent=slotNameLayout, text="", editable=True, width=150)
    buttonSetSlotName = cmds.button(parent=slotNameLayout, label="Use Material Name", height=20, command=I3DSlotNameUseMaterialName)

    I3DAddDropDownElement(materialAttributesCol, 'Shading Rate', UI_CONTROL_MENU_MATERIAL_SHADING_RATE, ['1x1', '1x2', '2x1', '2x2', '2x4', '4x2', '4x4'], 1, 'Shading rate to use on low profiles')
    I3DAddCheckBoxElement(materialAttributesCol, 'Alpha Blending', UI_CONTROL_BOOL_MATERIAL_ALPHA_BLENDING, False, 'Alpha blending')
    I3DAddStringFieldElement(materialAttributesCol, 'Refl. Shapes Object Mask', UI_CONTROL_STRING_MATERIAL_REFLECTION_MAP_SHAPES_OBJECT_MASK, '4294967295', width=MASK_FIELD_WIDTH)
    I3DAddStringFieldElement(materialAttributesCol, 'Refl. Lights Object Mask', UI_CONTROL_STRING_MATERIAL_REFLECTION_MAP_LIGHTS_OBJECT_MASK, '4294967295', width=MASK_FIELD_WIDTH)
    I3DAddCheckBoxElement(materialAttributesCol, 'With SSR Data', UI_CONTROL_BOOL_MATERIAL_REFRACTION_MAP_WITH_SSR_DATA)

    # tools
    toolsFrame = cmds.frameLayout(parent=tabShaderScroll, label='Tools', cll=False, mh=2, mw=2)
    toolsLayout = cmds.rowLayout(parent=toolsFrame, numberOfColumns=4)
    cmds.button(parent=toolsLayout, label="Convert Materials (FS22 to FS25)", height=25, command=I3DConvertMaterials, annotation="Convert old FS22 to the new FS25 material system")
    cmds.button(parent=toolsLayout, label="Vehicle Shader Debug", height=25, command=I3DVehicleShaderDebug, annotation="Debug UI for the vehicle shader.")
    cmds.button(parent=toolsLayout, label="Vehicle Shader Material Templates", height=25, command=I3DVehicleShaderTemplates, annotation="Material templates UI.")
    cmds.button(parent=toolsLayout, label="Set Material Attributes from XML", height=25, command=I3DSetMaterialAttributesFromXML, annotation="Set custom shader attributes from XML.")

    # load/apply/remove buttons
    buttonApply = cmds.button(parent=tabShader, label='Apply', height=30, command=I3DApplyMaterial, annotation='Stored the attributes to the selected material')
    buttonLoad = cmds.button(UI_CONTROL_BUTTON_MATERIAL_APPLY, parent=tabShader, label='Load', height=30, command=I3DLoadMaterialButtonCallback, annotation='Loads the attributes from the selected material')
    buttonRemove = cmds.button(parent=tabShader, label='Remove', height=30, command=I3DRemoveMaterial, annotation='Removes the custom attributes from the selected material')

    cmds.formLayout(tabShader, edit=True, attachForm=((tabShaderScroll, 'top', 2), (tabShaderScroll, 'left', 2), (tabShaderScroll, 'right', 2), (tabShaderScroll, 'bottom', 40)))

    cmds.formLayout(tabShader, edit=True, attachPosition=((buttonLoad, 'left', 2, 0), (buttonLoad, 'right', 2, 33), (buttonLoad, 'bottom', 5, 100),
                                                          (buttonApply, 'left', 2, 33), (buttonApply, 'right', 2, 66), (buttonApply, 'bottom', 5, 100),
                                                          (buttonRemove, 'left', 2, 66), (buttonRemove, 'right', 2, 100), (buttonRemove, 'bottom', 5, 100)))


    tabLabels.append((tabShader, 'Material'))

    cmds.tabLayout(tabs, edit=True, parent=form, cr=True, tabLabel=tabLabels, width=WINDOW_WIDTH)

    # if hasattr(cmds, 'dockControl'):
        # width = cmds.optionVar( q='GIANTS_EXPORTER_WIDTH' )
        # height = cmds.optionVar( q='GIANTS_EXPORTER_HEIGHT' )
        # if width == 0:
            # width = 470
        # if height == 0:
            # height = 760
        # cmds.dockControl(UI_CONTROL_DOCK, label=TITLE, floating=True, area='right', content=UI_CONTROL_WINDOW, width=width, height=height, allowedArea=['left', 'right'])
    # else:

    pluginEvent("onUILoaded", UI_CONTROL_WINDOW)

    cmds.showWindow(UI_CONTROL_WINDOW)

    I3DLoadSettings(None)
    I3DLoadFrameState()

    shaderDir = I3DGetProjectSetting("GIANTS_SHADER_DIR")
    if ( shaderDir ):
        I3DSetShaderPath(str(shaderDir))

    I3DClearOptionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES)
    cmds.menuItem(parent=UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, label='None')
    for shaderName, _ in SETTINGS_SHADERS.items():
        cmds.menuItem(parent=UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, label=shaderName)

    I3DReloadMaterialList()

    I3DRemoveSelectionChangedListener()

    pluginEvent("onExporterOpen", UI_CONTROL_WINDOW)

    # add onSelectionChange listener
    jobNum = cmds.scriptJob( e= ['SelectionChanged', I3DOnSelectionChanged], protected=False)
    jobNum = cmds.scriptJob( e= ['SceneOpened', I3DOnSceneOpened], protected=False)

    I3DOnSelectionChanged()

    # show ChangeLog if something has changed
    if ChangeLogDialog.getHasChangedAnythingSinceLastView():
        I3DShowChangeLog(None)

    return 0

def I3DRemoveSelectionChangedListener():
    # remove old onSelectionChange listener
    jobs = cmds.scriptJob( listJobs=True )
    for job in sorted(jobs):
        pos = job.find('I3DOnSelectionChanged')
        if pos != -1:
            id = int(job[:job.find(':')])
            cmds.scriptJob( kill=id, force=True)
        pos = job.find('I3DOnSceneOpened')
        if pos != -1:
            id = int(job[:job.find(':')])
            cmds.scriptJob(kill=id, force=True)

def I3DLoadFrameState():
    global SETTINGS_FRAMES

    for k,v in SETTINGS_FRAMES.items():
        collapsed = cmds.optionVar( q=k )
        if collapsed == 1:
            cmds.frameLayout(v['uiControl'], edit=True, collapse=True)
    return

def I3DSaveFrameState():
    global SETTINGS_FRAMES

    for k,v in SETTINGS_FRAMES.items():
        collapsed = cmds.frameLayout(v['uiControl'], q=True, collapse=True)
        value = 0
        if collapsed:
            value = 1
        cmds.optionVar( intValue=(k, value ))
    return

def I3DOnLoadOnSelectionMenuCallback(enabled):
    I3DSetProjectSetting(UI_SETTINGS_LOAD_ON_SELECT, enabled)

    cmds.button(UI_CONTROL_BUTTON_ATTRIBUTE_APPLY, edit=True, enable=not enabled)
    cmds.button(UI_CONTROL_BUTTON_MATERIAL_APPLY, edit=True, enable=not enabled)

def I3DValidateHexTextField(textField, num_digits=8):
    value = cmds.textField(textField, query=True, text=True)

    value = I3DUtils.filterHexToUpper(value)  # remove 0x prefix, remove non hex characters

    if len(value) > num_digits:  # remove excess characters
        value = value[:num_digits]

    if value == "":  # ensure field is not empty
        value = "0"

    cmds.textField(textField, edit=True, text=value)

def I3DCollisionFilterPresetSelected(unused):
    optionValue = cmds.optionMenu(UI_CONTROL_STRING_COLLISION_FILTER_PRESET, query=True, v=True)
    groupHex, maskHex = colMaskFlags.getPresetGroupAndMask(optionValue, asHex=True)
    if groupHex is not None:
        # update group and mask fields based on preset
        cmds.textField(UI_CONTROL_STRING_COLLISION_FILTER_GROUP, edit=True, text=I3DUtils.filterHexToUpper(groupHex))
        cmds.textField(UI_CONTROL_STRING_COLLISION_FILTER_MASK, edit=True, text=I3DUtils.filterHexToUpper(maskHex))

def I3DCollisionUpdatePresetSelection():
    "Updates Collision Filter Preset dropdown based on set filter and group"
    try:
        group = int(cmds.textField(UI_CONTROL_STRING_COLLISION_FILTER_GROUP, q=True, text=True), 16)  # hex to dec
        mask = int(cmds.textField(UI_CONTROL_STRING_COLLISION_FILTER_MASK, q=True, text=True), 16)  # hex to dec
        preset = colMaskFlags.getPresetByMasks(group, mask)
        if preset is not None:
            index = g_collisionPresetNamesOptions.index(preset["name"])
            cmds.optionMenu(UI_CONTROL_STRING_COLLISION_FILTER_PRESET, edit=True, select=index + 1)  # optionsMenu select is 1-based
        else:
            cmds.optionMenu(UI_CONTROL_STRING_COLLISION_FILTER_PRESET, edit=True, select=1)
    except ValueError:
        # filter masks for invalid chars
        groupHex = cmds.textField(UI_CONTROL_STRING_COLLISION_FILTER_GROUP, q=True, text=True)
        cmds.textField(UI_CONTROL_STRING_COLLISION_FILTER_GROUP, edit=True, text=I3DUtils.filterHexToUpper(groupHex))

        maskHex = cmds.textField(UI_CONTROL_STRING_COLLISION_FILTER_MASK, q=True, text=True)
        cmds.textField(UI_CONTROL_STRING_COLLISION_FILTER_MASK, edit=True, text=I3DUtils.filterHexToUpper(maskHex))

def I3DDoubleSidedOn(unused):
    nodes = cmds.selectedNodes(dagObjects=True)
    if not nodes is None:
        node = nodes[0]
        if cmds.objectType(node, isType='transform'):
            cmds.setAttr(node + ".doubleSided", True)

def I3DDoubleSidedOff(unused):
    nodes = cmds.selectedNodes(dagObjects=True)
    if not nodes is None:
        node = nodes[0]
        if cmds.objectType(node, isType='transform'):
            cmds.setAttr(node + ".doubleSided", False)

def I3DOpenExportDialog(unused):
    file = None
    if hasattr(cmds, 'fileDialog2'):
        files = cmds.fileDialog2(fileMode=0, fileFilter='GIANTS i3D File (*.i3d)', dialogStyle=2, caption='Choose Export File', okCaption='Set File')
        if not files is None:
            file = files[0]
    else:
        file = cmds.fileDialog(m=1, dm='*.i3d', title='Choose Export File')
        if not file is None:
            if not file.endswith('.i3d'):
                file = file + '.i3d'

    if not file is None:
        cmds.textField(UI_CONTROL_STRING_FILE_PATH, edit=True, text=file)
        I3DSaveSettings(None)

def I3DOpenSelectGamePath(unused):
    file = None
    if hasattr(cmds, 'fileDialog2'):
        files = cmds.fileDialog2(fileMode=3, fileFilter='', dialogStyle=2, caption='Choose Game Location', okCaption='Set Location')
        if not files is None:
            file = files[0]
    else:
        file = cmds.fileDialog(m=1, dm='*', title='Choose Game Location')

    if not file is None:
        cmds.textField(UI_CONTROL_STRING_GAME_PATH, edit=True, text=file)
        I3DSaveSettings(None)


def I3DGetGamePath():
    gamePath = None

    workSpace = cmds.workspace(q=True, rd=True)
    if workSpace is not None:
        scenePath = cmds.file(query=True, sceneName=True, shortName=False)
        binName = scenePath[len(workSpace):].split("/")[0]
        if "bin" in binName and os.path.isdir(workSpace + binName):
            gamePath = workSpace + binName
        elif os.path.isdir(workSpace + "bin"):
            gamePath = workSpace + "bin"  # use default bin in case the file is from a non game subdirectory (e.g. dlc)

    if gamePath is None:
        gamePath = I3DSearchForGamePath()

    return gamePath

def I3DSearchForGamePath():
    gamePath = ''
    if I3DAttributeExists(SETTINGS_PREFIX, 'i3D_exportGamePath'):
        gamePath = cmds.getAttr(SETTINGS_PREFIX+'.i3D_exportGamePath')
    if(gamePath == 0 or gamePath == ''):
        directories = ["D:/code/lsim20%s_trunk/bin" % GAME_VERSION, "D:/code/lsim20%s/bin" % GAME_VERSION, "C:/Program Files (x86)/Farming Simulator 20%s" % GAME_VERSION]
        for dir in directories:
            if os.path.isdir(dir):
                gamePath = dir
                break

    return gamePath

def I3DOpenSetXmlConfigDialog(unused):
    paths = I3DOpenXmlConfigDialog()

    cmds.textField(UI_CONTROL_STRING_XML_FILE_PATH, edit=True, text=paths)
    I3DSaveSettings(None)

def I3DOpenAddXmlConfigDialog(unused):
    newPaths = I3DOpenXmlConfigDialog()

    oldPaths = cmds.textField(UI_CONTROL_STRING_XML_FILE_PATH, q=True, text=True)
    if len(oldPaths) > 0 and oldPaths[len(oldPaths)-1] != ";":
        oldPaths += ";"

    cmds.textField(UI_CONTROL_STRING_XML_FILE_PATH, edit=True, text=oldPaths+newPaths)
    I3DSaveSettings(None)

def I3DOpenXmlConfigDialog():
    files = []
    if hasattr(cmds, 'fileDialog2'):
        files = cmds.fileDialog2(fileMode=4, fileFilter='Vehicle XML-File(s) (*.xml)', dialogStyle=2, caption='Choose XML-Config File(s)', okCaption='Set File(s)')
    else:
        file = cmds.fileDialog(m=1, dm='*.xml', title='Choose XML-Config File(s)')
        if not file is None:
            if not file.endswith('.xml'):
                file = file + '.xml'
                files.append(file)

    if files is not None and len(files) > 0:
        paths = None
        for file in files:
            mayaFilePath = str(os.path.dirname(cmds.file(q=True, sn=True)).replace('\\', '/'))
            xmlFile = str(file.replace('\\', '/'))
            relPath = I3DUtils.getRelativePath(xmlFile, mayaFilePath)
            if paths is None:
                paths = relPath
            else:
                paths = paths + ';' + relPath

        return paths

    return ""


def I3DRemoveXmlConfig(unused):
    oldPaths = cmds.textField(UI_CONTROL_STRING_XML_FILE_PATH, q=True, text=True)

    if len(oldPaths) > 0:
        oldPathParts = oldPaths.split(";")
        lastLength = len(oldPathParts[len(oldPathParts)-1])
        cmds.textField(UI_CONTROL_STRING_XML_FILE_PATH, edit=True, text=oldPaths[:-lastLength-1])
        I3DSaveSettings(None)

def I3DOpenShaderDialog(unused):
    shaderDir =  I3DGetProjectSetting("GIANTS_SHADER_DIR")
    if not shaderDir:
        shaderDir = None

    if hasattr(cmds, 'fileDialog2'):
        folders = cmds.fileDialog2(fileMode=3, dialogStyle=2, caption='Set the current project path', okCaption='Set project path', startingDirectory=shaderDir)
        if not folders is None:
            shaderDir = folders[0]
    else:
        shaderDir = cmds.fileDialog(m=0, title='Set the current project path', dm='*.xml')
        if not shaderDir is None:
            shaderDir = os.path.dirname(shaderDir)

    if not shaderDir is None:
        I3DSetShaderPath(shaderDir)

    I3DClearOptionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES)
    cmds.menuItem(parent=UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, label='None')
    for shaderName, _ in SETTINGS_SHADERS.items():
        cmds.menuItem(parent=UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, label=shaderName)

def I3DOpenIESFileDialog(unused):
    gamePath = I3DGetGamePath()
    iesFilePaths = None
    if (hasattr(cmds, 'fileDialog2')):
        iesFilePaths = cmds.fileDialog2(fileMode=1, dialogStyle=2, caption='Select the IES Profile File', okCaption='OK', fileFilter='*.ies', startingDirectory=gamePath)
    else:
        iesFilePaths = cmds.fileDialog(mode=0, title='Select the IES Profile File', directoryMask='*.ies')

    if not iesFilePaths is None:
        iesFilePath = iesFilePaths[0]
        iesFilePath = iesFilePath.replace(gamePath + '/', '$')
        cmds.textField(UI_CONTROL_STRING_IES_PROFILE_FILE, edit=True, text=iesFilePath)

def I3DUpdateXML(unused):
    xmlFilename = cmds.textField(UI_CONTROL_STRING_XML_FILE_PATH, q=True, text=True)

    exportHandler = I3DExportHandler.I3DExportHandler()
    exportHandler.execute(export=False, validation=False, updateXML=True, xmlFilename=xmlFilename)

def I3DErrorCheck(unused):
    xmlFilename = cmds.textField(UI_CONTROL_STRING_XML_FILE_PATH, q=True, text=True)

    exportHandler = I3DExportHandler.I3DExportHandler()
    exportHandler.execute(export=False, validation=True, updateXML=False, xmlFilename=xmlFilename)

def I3DCheckClipDistances(unused):
    I3DClearErrors()

    I3DAddMessage(MESSAGE_TYPE_NONE, 'Checking Clip Distances')

    cmds.waitCursor( state=True )
    checkClipDistances.executeCheckCDs()
    cmds.waitCursor( state=False )

    I3DAddMessage(MESSAGE_TYPE_NONE, 'Done checking Clip Distances\n')

def I3DExportAll(unused):
    I3DExportSaveAsDialog(False, True, None)
    I3DSaveSettings(None)

def I3DExportSelected(unused):
    I3DExportSaveAsDialog(True, True, None)
    I3DSaveSettings(None)

def I3DExportSingleFiles(unused):
    sceneName = cmds.file(q=True, sceneName=True)
    file = cmds.file(q=True, sceneName=True, shortName=True)
    path = sceneName[:len(sceneName)-len(file)]

    nodes = cmds.selectedNodes(dagObjects=True)
    if not nodes is None:
        for node in nodes:
            cmds.select(node)
            filePath = path + node[1:] + ".i3d"
            I3DExportSaveAsDialog(True, False, filePath)

def I3DExportSaveAsDialog(exportSelection, clearErrors, path, skipValidation=False):
    gamePath = cmds.textField(UI_CONTROL_STRING_GAME_PATH, q=True, text=True)
    if cmds.checkBoxGrp(UI_CONTROL_GAME_PATH, q=True, v1=True):
        gamePath = I3DGetGamePath()

    outputFile = ''
    if path is None:
        outputFile = cmds.textField(UI_CONTROL_STRING_FILE_PATH, q=True, text=True)

        if(cmds.checkBoxGrp(UI_CONTROL_BOOL_USE_MAYA_FILENAME, q=True, v1=True)):
            sceneName = cmds.file(q=True, sceneName=True)
            if sceneName == "":
                filePath = cmds.file(q=True, expandName=True)
                if "untitled" not in filePath:
                    cmds.file(rename=filePath)
                    sceneName = cmds.file(q=True, sceneName=True)
                    I3DAddMessage(MESSAGE_TYPE_INFO, 'Scene name not set. Setting it to current file location.')

            outputFile, fileExtension = os.path.splitext(sceneName)
            if sceneName == "":
                cmds.confirmDialog(title="Error", message="Failed to use maya filename as export filename. Maya file not saved!")
                return

        # add extension if missing
        fileName, fileExtension = os.path.splitext(outputFile)
        if(fileExtension != '.i3d'):
            outputFile = outputFile + '.i3d'

        # cancel export if no path is given
        if(outputFile == ''):
            I3DAddMessage(MESSAGE_TYPE_ERROR, 'No output path given. Canceled exporting!')
            return outputFile
    else:
        outputFile = path

    exportHandler = I3DExportHandler.I3DExportHandler()

    exportHandler.setOption("filename", str(outputFile))
    exportHandler.setOption("scenegraph", cmds.checkBoxGrp(UI_CONTROL_EXPORT_1, q=True, v1=True))
    exportHandler.setOption("animation", cmds.checkBoxGrp(UI_CONTROL_EXPORT_1, q=True, v2=True))
    exportHandler.setOption("shapes", cmds.checkBoxGrp(UI_CONTROL_EXPORT_1, q=True, v3=True))
    exportHandler.setOption("nurbscurves", cmds.checkBoxGrp(UI_CONTROL_EXPORT_2, q=True, v1=True))
    exportHandler.setOption("lights", cmds.checkBoxGrp(UI_CONTROL_EXPORT_2, q=True, v2=True))
    exportHandler.setOption("cameras", cmds.checkBoxGrp(UI_CONTROL_EXPORT_2, q=True, v3=True))
    exportHandler.setOption("particlesystems", cmds.checkBoxGrp(UI_CONTROL_EXPORT_3, q=True, v1=True))
    exportHandler.setOption("defaultcameras", cmds.checkBoxGrp(UI_CONTROL_EXPORT_3, q=True, v2=True))
    exportHandler.setOption("userattributes", cmds.checkBoxGrp(UI_CONTROL_EXPORT_3, q=True, v3=True))
    exportHandler.setOption("exportBinaryFiles", cmds.checkBoxGrp(UI_CONTROL_EXPORT_4, q=True, v1=True))
    exportHandler.setOption("ignoreBindPoses", cmds.checkBoxGrp(UI_CONTROL_EXPORT_4, q=True, v2=True))
    exportHandler.setOption("objectDataTexture", cmds.checkBoxGrp(UI_CONTROL_EXPORT_4, q=True, v3=True))
    exportHandler.setOption("normals", cmds.checkBoxGrp(UI_CONTROL_SHAPES_1, q=True, v1=True))
    exportHandler.setOption("colors", cmds.checkBoxGrp(UI_CONTROL_SHAPES_1, q=True, v2=True))
    exportHandler.setOption("texCoords", cmds.checkBoxGrp(UI_CONTROL_SHAPES_1, q=True, v3=True))
    exportHandler.setOption("skinWeights", cmds.checkBoxGrp(UI_CONTROL_SHAPES_2, q=True, v1=True))
    exportHandler.setOption("mergeGroups", cmds.checkBoxGrp(UI_CONTROL_SHAPES_2, q=True, v2=True))
    exportHandler.setOption("verbose", cmds.checkBoxGrp(UI_CONTROL_MISC_1, q=True, v1=True))
    exportHandler.setOption("relativePaths", cmds.checkBoxGrp(UI_CONTROL_MISC_1, q=True, v2=True))
    exportHandler.setOption("templates", cmds.checkBoxGrp(UI_CONTROL_MISC_1, q=True, v3=True))
    exportHandler.setOption("floatEpsilon", cmds.checkBoxGrp(UI_CONTROL_MISC_1, q=True, v3=True))
    exportHandler.setOption("gameRelativePath", cmds.checkBoxGrp(UI_CONTROL_GAME_PATH, q=True, v2=True))
    exportHandler.setOption("exportSelection", exportSelection)

    if gamePath is not None and os.path.isdir(gamePath):
        exportHandler.setOption("gamePath", gamePath.replace('\\', '$').replace('/', '$'))

    updateXML = cmds.checkBoxGrp(UI_CONTROL_MISC_2, q=True, v1=True)
    xmlFilename = cmds.textField(UI_CONTROL_STRING_XML_FILE_PATH, q=True, text=True)

    exportHandler.execute(export=True, validation=not skipValidation, updateXML=updateXML, xmlFilename=xmlFilename)

    return outputFile

def I3DGetNodeHasVertexColors(node):
    return cmds.polyColorSet(node, query=True, allColorSets=True) != None

def I3dGetNodeUvSetN(node, uvSetIndex):
    uvSets = cmds.polyUVSet(node, query=True, allUVSets=True)
    if uvSets == None:
        return None
    if len(uvSets) <= uvSetIndex:
        return None
    return uvSets[uvSetIndex]


def I3DGetNodeType(node):
    if I3DUtils.isCamera(node):
        return NODETYPE_CAMERA

    if type(cmds.polyEvaluate(node, t=True)) == int:
        return NODETYPE_MESH

    if cmds.objectType(node) == "joint":
        return NODETYPE_JOINT

    return NODETYPE_GROUP

def I3DClearErrors():
    global g_errorBox
    g_errorBox.clear()

def I3DSetIdentifier(unused):
    nodes = cmds.ls(sl=True, o=True, sn=True, long=True)
    if not nodes is None:
        for node in nodes:
            splittedNames = node.split('|')
            nodeName = splittedNames[len(splittedNames)-1]
            cmds.textField(UI_CONTROL_STRING_IDENTIFIER, edit=True, text=nodeName)
            I3DSaveAttributeString(node, 'i3D_xmlIdentifier', nodeName)

def I3DRemoveIdentifier(unused):
    nodes = cmds.ls(sl=True, o=True, sn=True, long=True)
    if not nodes is None:
        for node in nodes:
            I3DRemoveAttribute(node, 'i3D_xmlIdentifier')
            cmds.textField(UI_CONTROL_STRING_IDENTIFIER, edit=True, text='')

def I3DAddMessage(typeIndex, msg, margin=3, color=None, buttonText="", buttonFunc=None, buttonArgs=[], buttonAnnotation=None, buttonRemoveLine=False, buttonColor=None):
    global g_errorBox
    g_errorBox.addMessage(typeIndex, msg, margin=margin, color=color, buttonText=buttonText, buttonFunc=buttonFunc, buttonArgs=buttonArgs, buttonAnnotation=buttonAnnotation, buttonRemoveLine=buttonRemoveLine, buttonColor=buttonColor)

def I3DAddMessages(messageData):
    global g_errorBox
    g_errorBox.addMessages(messageData)

def I3DAddStringFieldElement(parent, label, stringFieldName, defaultValue, annotation='', editable=True, width=DEFAULT_FIELD_WIDTH, changeCommand=None):
    numberOfColumns = 2

    layout = cmds.rowLayout(parent=parent, adjustableColumn=numberOfColumns, numberOfColumns=numberOfColumns)
    cmds.text(parent=layout, label=label, width=TEXT_WIDTH, align='left', annotation=annotation)

    if changeCommand is not None:
        cmds.textField(stringFieldName, parent=layout, text=defaultValue, annotation=annotation, editable=editable, width=width, changeCommand=changeCommand)
    else:
        cmds.textField(stringFieldName, parent=layout, text=defaultValue, annotation=annotation, editable=editable, width=width)

    return

def I3DAddStringBitmaskFieldElement(parent, label, stringFieldName, defaultValue, annotation=None, maskAttributes={}, editable=True, width=None, changeCommand=None):
    '''
    Adds a labeled bitmask text element with a button to open a dialog for managing individual bits
    maskAttributes = {'num_bits': 32, 'bit_names': {1: "NAME1", 2: "NAME2", ...}, 'bit_annotations': {1: "desc 1", 2: "desc 2", ...}}
    '''
    num_bits = maskAttributes.get('num_bits', 32)
    num_hex_digits = math.ceil(num_bits / 4)
    width = width or (15 + num_hex_digits * 7)

    annotation = annotation or label or ''
    annotation = annotation + " ({} Bits)".format(num_bits)

    numberOfColumns = 3
    layout = cmds.rowLayout(parent=parent, adjustableColumn=numberOfColumns, numberOfColumns=numberOfColumns)
    cmds.text(parent=layout, label=label, width=TEXT_WIDTH, align='left', annotation=annotation)

    if type(defaultValue) is int:
        defaultValue = '{:X}'.format(defaultValue)
    else:
        defaultValue = I3DUtils.filterHexToUpper(defaultValue)

    def onBitmaskChanged(Unused):
        I3DValidateHexTextField(stringFieldName, num_digits=num_hex_digits)
        if changeCommand is not None:
            changeCommand()

    cmds.textField(stringFieldName, parent=layout, text=defaultValue, annotation=annotation, editable=editable, width=width, font="fixedWidthFont", changeCommand=onBitmaskChanged)

    def onOpenBitmaskDialog(unused):
        bitmaskStr = cmds.textField(stringFieldName, q=True, text=True)
        def onCloseBitmaskDialog(newBitmask):
            if editable:
                cmds.textField(stringFieldName, edit=True, text='{:X}'.format(newBitmask))
                onBitmaskChanged(None)
        BitMaskWindow.BitMaskWindow(num_bits, bitmaskStr, onCloseBitmaskDialog, maskAttributes, window_title="Edit Bitmask", editable=editable)

    cmds.button(parent=layout, label='...', annotation='Open BitMask Dialog', height=17, command=onOpenBitmaskDialog)

def I3DAddCheckBoxElement(parent, label, checkboxName, defaultValue=False, checkboxLabel='', annotation='', editable=True, width=DEFAULT_FIELD_WIDTH):
    layout = cmds.rowLayout(parent=parent, adjustableColumn=2, numberOfColumns=2)
    cmds.text(parent=layout, label=label, width=TEXT_WIDTH, align='left', annotation=annotation)
    cmds.checkBox(checkboxName, parent=layout, label=checkboxLabel, align='left', value=defaultValue, annotation=annotation, editable=editable)
    return

def I3DAddIntFieldElement(parent, label, intFieldName, defaultValue, annotation='', editable=True, width=DEFAULT_FIELD_WIDTH):
    layout = cmds.rowLayout(parent=parent, adjustableColumn=2, numberOfColumns=2)
    cmds.text(parent=layout, label=label, width=TEXT_WIDTH, align='left', annotation=annotation)
    cmds.intField(intFieldName, parent=layout, value=defaultValue, annotation=annotation, editable=editable, width=width)
    return

def I3DAddDropDownElement(parent, label, fieldName, options, defaultSelection=1, annotation='', width=DEFAULT_FIELD_WIDTH, maxVisibleItems=10, changeCommand=None):
    layout = cmds.rowLayout(parent=parent, adjustableColumn=2, numberOfColumns=2)
    cmds.text(parent=layout, label=label, width=TEXT_WIDTH, align='left', annotation=annotation)
    if changeCommand is not None:
        menu = cmds.optionMenu(fieldName, parent=layout, width=width, maxVisibleItems=maxVisibleItems, changeCommand=changeCommand)
    else:
        menu = cmds.optionMenu(fieldName, parent=layout, width=width, maxVisibleItems=maxVisibleItems)
    for option in options:
        cmds.menuItem(parent=menu, label=option)  # TODO: add annotation support, e.g. for colMaskPresets
    cmds.optionMenu(menu, edit=True, select=defaultSelection)

def I3DAddMergeGroup(parent):
    layout = cmds.rowLayout('mergeGroupLayout', parent=parent, adjustableColumn=4, numberOfColumns=4)
    cmds.text(parent=layout, label='Merge Group', width=TEXT_WIDTH, align='left', annotation='')
    cmds.intField(UI_CONTROL_INT_MERGE_GROUP, parent=layout, value=0, annotation='', editable=True, width=DEFAULT_FIELD_WIDTH)
    cmds.text(parent=layout, label='Root', width=50, align='right')
    cmds.checkBox(UI_CONTROL_BOOL_MERGE_GROUP_ROOT, parent=layout, label='', align='left', value=False, annotation='', editable=True)
    return

def I3DAddBoundVolume(parent):
    layout = cmds.rowLayout('boundingVolumeLayout', parent=parent, adjustableColumn=3, numberOfColumns=3)
    cmds.text(parent=layout, label='Bounds Of', width=TEXT_WIDTH, align='left')
    cmds.textField(UI_CONTROL_STRING_BOUNDINGVOLUME, parent=layout, text='', annotation='Bounding volume for given shape name or merge group', editable=True, width=TEXT_WIDTH)
    menu = cmds.optionMenu(UI_OPTIONS_PREDEFINED_BOUNDINGVOLUME, parent=layout, changeCommand=I3DBoundingVolumeOptionMenu, width=115)
    cmds.menuItem(parent=menu, label=' ')
    cmds.menuItem(parent=menu, label='MERGEGROUP_1')
    cmds.menuItem(parent=menu, label='MERGEGROUP_2')
    cmds.menuItem(parent=menu, label='MERGEGROUP_3')
    cmds.menuItem(parent=menu, label='MERGEGROUP_4')
    cmds.menuItem(parent=menu, label='MERGEGROUP_5')
    cmds.menuItem(parent=menu, label='MERGEGROUP_6')
    cmds.menuItem(parent=menu, label='MERGEGROUP_7')
    cmds.menuItem(parent=menu, label='MERGEGROUP_8')
    cmds.menuItem(parent=menu, label='MERGEGROUP_9')
    return

def I3DAddLightAttributesFrame(parent):
    lightAttributesFrame = cmds.frameLayout(UI_CONTROL_FRAME_LIGHT_ATTRIBUTES, parent=parent, label='Light', cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState, visible=False )
    lightAttributeItems = cmds.columnLayout('lightAttributesItems', parent=lightAttributesFrame)
    I3DAddCheckBoxElement(lightAttributeItems, 'Use Depth Map Shadows', UI_CONTROL_BOOL_USE_DEPTH_MAP_SHADOWS)
    I3DAddFloatFieldElement(lightAttributeItems, 'Soft Shadow Light Size', UI_CONTROL_FLOAT_SOFT_SHADOWS_LIGHT_SIZE, 0.05, '')
    I3DAddFloatFieldElement(lightAttributeItems, 'Soft Shadow Light Distance', UI_CONTROL_FLOAT_SOFT_SHADOWS_LIGHT_DISTANCE, 15, '')
    I3DAddFloatFieldElement(lightAttributeItems, 'Soft Shadow Depth Bias Factor', UI_CONTROL_FLOAT_SOFT_SHADOWS_DEPTH_BIAS_FACTOR, 5, '')
    I3DAddFloatFieldElement(lightAttributeItems, 'Soft Shadow Max Penumbra Size', UI_CONTROL_FLOAT_SOFT_SHADOWS_MAX_PENUMBRA_SIZE, 0.5, '')

    # IES Profile File with file selection dialog button
    layout = cmds.rowLayout(parent=lightAttributeItems, adjustableColumn=2, numberOfColumns=3)
    cmds.text(parent=layout, label='IES Profile File', width=TEXT_WIDTH, align='left', annotation='')
    cmds.textField(UI_CONTROL_STRING_IES_PROFILE_FILE, parent=layout, text='', annotation='', editable=True, width=250)
    cmds.symbolButton('giants_buttonSelectIESProfileFile', parent=layout, image='navButtonBrowse.xpm', command=I3DOpenIESFileDialog, annotation='Select IES Profile File' )

    I3DAddCheckBoxElement(lightAttributeItems, 'Use Light Scattering', UI_CONTROL_BOOL_LIGHT_SCATTERING)
    cmds.checkBox(UI_CONTROL_BOOL_LIGHT_SCATTERING, edit=True, changeCommand=I3DEnableScatteringAttributes)
    I3DAddFloatFieldElement(lightAttributeItems, 'Light Scattering Intensity', UI_CONTROL_FLOAT_LIGHT_SCATTERING_INTENSITY, 10, '')
    cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_INTENSITY, edit=True, changeCommand=I3DChangeLightScatteringIntensity)
    I3DAddFloatFieldElement(lightAttributeItems, 'Light Scattering Cone Angle', UI_CONTROL_FLOAT_LIGHT_SCATTERING_CONE_ANGLE, 40, '')
    cmds.floatField(UI_CONTROL_FLOAT_LIGHT_SCATTERING_CONE_ANGLE, edit=True, changeCommand=I3DChangeLightScatteringConeAngle)

def I3DEnableSoftShadowAttributes(enable):
    cmds.floatField(UI_CONTROL_FLOAT_SOFT_SHADOWS_LIGHT_SIZE, edit=True, enable=enable)
    cmds.floatField(UI_CONTROL_FLOAT_SOFT_SHADOWS_LIGHT_DISTANCE, edit=True, enable=enable)
    cmds.floatField(UI_CONTROL_FLOAT_SOFT_SHADOWS_DEPTH_BIAS_FACTOR, edit=True, enable=enable)
    cmds.floatField(UI_CONTROL_FLOAT_SOFT_SHADOWS_MAX_PENUMBRA_SIZE, edit=True, enable=enable)

def I3DShowLightAttributesFrame(lightCastsShadows):
    cmds.frameLayout(UI_CONTROL_FRAME_LIGHT_ATTRIBUTES, edit=True, visible=True)
    cmds.checkBox(UI_CONTROL_BOOL_USE_DEPTH_MAP_SHADOWS, edit=True, value=lightCastsShadows, changeCommand=I3DEnableSoftShadowAttributes)
    I3DEnableSoftShadowAttributes(lightCastsShadows)

def I3DHideLightAttributesFrame():
    cmds.frameLayout(UI_CONTROL_FRAME_LIGHT_ATTRIBUTES, edit=True, visible=False)
    cmds.checkBox(UI_CONTROL_BOOL_USE_DEPTH_MAP_SHADOWS, edit=True, value=False, changeCommand=None)

def I3DAddRestitution(parent):
    layout = cmds.rowLayout('restitutionLayout', parent=parent, adjustableColumn=4, numberOfColumns=4)
    cmds.text(parent=layout, label='Restitution', width=TEXT_WIDTH, align='left')
    cmds.floatField(UI_CONTROL_FLOAT_RESTITUTION, parent=layout, value=0, annotation='Bouncyness of the surface')
    menu = cmds.optionMenu(UI_OPTIONS_PREDEFINED_PHYSICS, parent=layout, changeCommand=I3DPhysicsOptionMenu, width=100)
    cmds.menuItem(parent=menu, label='Default')
    cmds.menuItem(parent=menu, label='Rubber')
    cmds.menuItem(parent=menu, label='Concrete')
    cmds.menuItem(parent=menu, label='Wood')
    cmds.menuItem(parent=menu, label='Metal')
    cmds.menuItem(parent=menu, label='Glass')
    return

def I3DAddMass(parent):
    layout = cmds.rowLayout('massLayout', parent=parent, adjustableColumn=2, numberOfColumns=2)
    cmds.text(parent=layout, label='Density', width=TEXT_WIDTH, align='left', annotation='Used with the shape of the object to calculate mass. The higher the number, the heavier the object')
    cmds.floatField(UI_CONTROL_FLOAT_DENSITY, parent=layout, value=0, annotation='Used with the shape of the object to calculate mass. The higher the number, the heavier the object', editable=True, width=DEFAULT_FIELD_WIDTH)
    layoutMass = cmds.rowLayout(parent=parent, adjustableColumn=3, numberOfColumns=3)
    cmds.text(UI_CONTROL_LABEL_MASS, parent=layoutMass, label='Mass', width=TEXT_WIDTH, align='left', visible=True)
    cmds.floatField(UI_CONTROL_FLOAT_MASS, parent=layoutMass, value=0, annotation='Total mass of the compound node', editable=False, width=DEFAULT_FIELD_WIDTH, visible=True)
    cmds.textField(UI_CONTROL_STRING_MASS_NODE, parent=layoutMass, text='', annotation='Name of the compound node', editable=False, width=150, visible=True)
    return


def I3DAddTextFieldElement(parent, label, textFieldName, defaultValue='', annotation='', editable=True, width=DEFAULT_FIELD_WIDTH):
    layout = cmds.rowLayout(parent=parent, adjustableColumn=2, numberOfColumns=2)
    cmds.text(parent=layout, label=label, width=TEXT_WIDTH, align='left', annotation=annotation)
    cmds.textField(textFieldName, parent=layout, text=defaultValue, annotation=annotation, editable=editable, width=width)
    return

def I3DAddFloatFieldElement(parent, label, floatFieldName, defaultValue, annotation='', editable=True, width=DEFAULT_FIELD_WIDTH):
    layout = cmds.rowLayout(parent=parent, adjustableColumn=2, numberOfColumns=2)
    cmds.text(parent=layout, label=label, width=TEXT_WIDTH, align='left', annotation=annotation)
    cmds.floatField(floatFieldName, parent=layout, value=defaultValue, annotation=annotation, editable=editable, width=width)
    return

def I3DAddFloatFieldElements(parent, label, floatFieldNames, defaultValues, annotations=[''], editable=True, width=DEFAULT_FIELD_WIDTH):
    layout = cmds.rowLayout(parent=parent,adjustableColumn=len(floatFieldNames)+1, numberOfColumns=len(floatFieldNames)+1)
    cmds.text(parent=layout, label=label, width=TEXT_WIDTH, align='left', annotation=annotations[0])
    for i in range(len(floatFieldNames)):
        annotation = ''
        if i+1 < len(annotations):
            annotation = annotations[i+1]
        cmds.floatField(floatFieldNames[i], parent=layout, value=defaultValues[i], annotation=annotation, editable=editable, width=width)
    return

def I3DResetAttributesScreen(unused):
    for k,v in SETTINGS_ATTRIBUTES.items():
        if 'resetUIFunction' in v:
            v['resetUIFunction'](k, v)
        else:
            if v['type'] == TYPE_BOOL:
                cmds.checkBox(v['uiControl'], edit=True, v=v['defaultValue'])
            elif v['type'] == TYPE_INT:
                cmds.intField(v['uiControl'], edit=True, v=v['defaultValue'])
            elif v['type'] == TYPE_FLOAT:
                cmds.floatField(v['uiControl'], edit=True, v=v['defaultValue'])
            elif v['type'] == TYPE_STRING:
                cmds.textField(v['uiControl'], edit=True, text=v['defaultValue'])
            elif v['type'] == TYPE_ENUM:
                cmds.optionMenu(v['uiControl'], edit=True, v=v['options'][v['defaultValue']])
            elif v['type'] == TYPE_HEX:
                cmds.textField(v['uiControl'], edit=True, text=I3DUtils.filterHexToUpper(v['defaultValue']))

def I3DPhysicsOptionMenu(selectedItem):
    if selectedItem == 'Default':
        I3DSetPhysicsAttributes(0.0, 0.5, 0.5, 0.0, 0.01, 0.5)
    elif selectedItem == 'Rubber':
        I3DSetPhysicsAttributes(1.0, 0.7, 0.7, 0.0, 0.01, 1.0)
    elif selectedItem == 'Concrete':
        I3DSetPhysicsAttributes(1.0, 0.7, 0.7, 0.0, 0.01, 1.0)
    elif selectedItem == 'Wood':
        I3DSetPhysicsAttributes(0.3, 0.7, 0.7, 0.0, 0.01, 0.6)
    elif selectedItem == 'Metal':
        I3DSetPhysicsAttributes(0.1, 0.6, 0.7, 0.0, 0.01, 1.6)
    elif selectedItem == 'Glass':
        I3DSetPhysicsAttributes(0.1, 0.05, 0.05, 0.0, 0.01, 1.0)

def I3DSetPhysicsAttributes(restitution, staticFriction, dynamicFriction, linearDamping, angularDamping, density):
    cmds.floatField(UI_CONTROL_FLOAT_RESTITUTION, edit=True, value=restitution)
    cmds.floatField(UI_CONTROL_FLOAT_STATIC_FRICTION, edit=True, value=staticFriction)
    cmds.floatField(UI_CONTROL_FLOAT_DYNAMIC_FRICTION, edit=True, value=dynamicFriction)
    cmds.floatField(UI_CONTROL_FLOAT_LINEAR_DAMPING, edit=True, value=linearDamping)
    cmds.floatField(UI_CONTROL_FLOAT_ANGULAR_DAMPING, edit=True, value=angularDamping)
    cmds.floatField(UI_CONTROL_FLOAT_DENSITY, edit=True, value=density)

def I3DBoundingVolumeOptionMenu(selectedItem):
    if not selectedItem == ' ':
        cmds.textField(UI_CONTROL_STRING_BOUNDINGVOLUME, edit=True, text=selectedItem)

def I3DGetShaderNode(node):
    shapes = cmds.listRelatives(node)
    for i in range(len(shapes)):
        shapes[i] = node + '|' + shapes[i]

    materials = list(set(cmds.listConnections(shapes, type='shadingEngine')))
    if(len(materials) > 1):
        I3DShowWarning(node + ' has more than 1 material assigned to it\n')

    surfaceShader = cmds.listConnections(materials[0] + '.surfaceShader')
    if(len(surfaceShader) == 0):
        I3DShowWarning(node + ' has no material assigned to it\n')

    return surfaceShader[0]

def I3DAddAttribute(node, name, value):
    I3DUtils.setAttributeValue(node, name, value)

def I3DSetAttributePreset(selectedItemName):
    '''
    Populates attributes panels input elements with values from selected preset
    '''
    I3DResetAttributesScreen(False)

    for preset in SETTINGS_VEHICLE_ATTRIBUTES:
        if preset['name'] == selectedItemName:
            attributeValues = preset['attributeValues']

            # get collision filter group and mask for defined preset
            colMaskPresetName = attributeValues.get('colMaskPresetName')
            if colMaskPresetName is not None:
                groupHex, maskHex = colMaskFlags.getPresetGroupAndMask(colMaskPresetName, True)
                if groupHex is not None:
                    cmds.textField(UI_CONTROL_STRING_COLLISION_FILTER_GROUP, edit=True, text=I3DUtils.filterHexToUpper(groupHex))
                    cmds.textField(UI_CONTROL_STRING_COLLISION_FILTER_MASK, edit=True, text=I3DUtils.filterHexToUpper(maskHex))
                else:
                    I3DShowWarning("Unknown colMaskPresetName '{}' in preset '{}'".format(colMaskPresetName, selectedItemName))

            for key, attribute in SETTINGS_ATTRIBUTES.items():
                presetKey = key.replace('i3D_', '')
                if presetKey not in attributeValues:
                    continue

                if attribute['type'] == TYPE_BOOL:
                    cmds.checkBox(attribute['uiControl'], edit=True, value=attributeValues[presetKey])
                elif attribute['type'] == TYPE_INT:
                    cmds.intField(attribute['uiControl'], edit=True, value=attributeValues[presetKey])
                elif attribute['type'] == TYPE_FLOAT:
                    cmds.floatField(attribute['uiControl'], edit=True, value=attributeValues[presetKey])
                elif attribute['type'] == TYPE_STRING:
                    cmds.textField(attribute['uiControl'], edit=True, text=attributeValues[presetKey])
                elif attribute['type'] == TYPE_ENUM:
                    cmds.optionMenu(attribute['uiControl'], edit=True, value=attributeValues[presetKey])
                elif attribute['type'] == TYPE_HEX:
                    cmds.textField(attribute['uiControl'], edit=True, text=I3DUtils.filterHexToUpper(attributeValues[presetKey]))

            I3DCollisionUpdatePresetSelection()
            return

def I3DRemoveObjectAttributes(unused):
    objectName = cmds.textField(UI_CONTROL_STRING_LOADED_NODE_NAME, q=True, text=True)
    if(len(objectName) > 0):
        I3DRemoveAttributes(objectName)
        I3DLoadObjectAttributes(objectName)

def I3DApplySelectedAttributes(unused):
    nodes = cmds.selectedNodes(dagObjects=True)
    if not nodes is None:
        for node in nodes:
            if(cmds.objectType(node, isType='transform')):
                I3DSaveAttributes(node)
        I3DUpdateMass(nodes[0])
    else:
        I3DShowWarning('Nothing selected')

def I3DLoadObjectAttributesLoadBtn(unused):
    nodes = cmds.selectedNodes(dagObjects=True)
    if not nodes is None:
        node = nodes[0]

        # check if light shape is selected when pressing the Load button (then select the parent)
        if cmds.objectType(node) in ['ambientLight',
                                    'directionalLight',
                                    'pointLight',
                                    'spotLight',
                                    'areaLight',
                                    'volumeLight']:
            # Get the parent of the light shape
            parents = cmds.listRelatives(node, parent=True)

            if parents:
                cmds.select(parents[0], replace=True)
    I3DLoadObjectAttributes(unused)


def I3DLoadObjectAttributes(unused):
    nodes = cmds.selectedNodes(dagObjects=True)
    if not nodes is None:
        node = nodes[0]
        if cmds.objectType(node, isType='transform'):
            cmds.textField(UI_CONTROL_STRING_LOADED_NODE_NAME, edit=True, text=node)
            for k,v in SETTINGS_ATTRIBUTES.items():
                if 'loadFunction' in v:
                    v['loadFunction'](k, v, node)
                else:
                    if v['type'] == TYPE_BOOL:
                        cmds.checkBox(v['uiControl'], edit=True, v=I3DGetAttributeValue(node, k, v['defaultValue']))
                    elif v['type'] == TYPE_INT:
                        cmds.intField(v['uiControl'], edit=True, v=I3DGetAttributeValue(node, k, v['defaultValue']))
                    elif v['type'] == TYPE_FLOAT:
                        cmds.floatField(v['uiControl'], edit=True, v=I3DGetAttributeValue(node, k, v['defaultValue']))
                    elif v['type'] == TYPE_STRING:
                        cmds.textField(v['uiControl'], edit=True, text=I3DGetAttributeValue(node, k, v['defaultValue']))
                    elif v['type'] == TYPE_ENUM:
                        options = v['options']
                        cmds.optionMenu(v['uiControl'], edit=True, v=options[I3DGetAttributeValue(node, k, v['defaultValue'])])
                    elif v['type'] == TYPE_HEX:
                        value = I3DGetAttributeValue(node, k, v['defaultValue'])

                        # value is string type but in decimal format, convert to hex string
                        if type(value) is str and not value.startswith('0x'):
                            value = hex(int(value))
                            I3DSaveAttributeHex(node, k, value)

                        elif type(value) is int:
                            if value != int(v['defaultValue'], 16):  # only print warning if value is different from default
                                I3DShowWarning("Warning: attribute '{}' in ma file has wrong type '{}' instead of 'str', converting".format(k, type(value)))
                            value = hex(value)  # convert int to hex str
                            I3DSaveAttributeHex(node, k, value)

                        cmds.textField(v['uiControl'], edit=True, text=I3DUtils.filterHexToUpper(value))

        I3DUpdateMass(node)
        I3DCollisionUpdatePresetSelection()
    elif I3DGetProjectSetting("I3DExporter_Internal_LoadOnSelect") != "True":
        I3DShowWarning('Nothing selected')

def I3DSaveAttributes(node):
    nodeType = I3DGetNodeType(node)
    for k, v in SETTINGS_ATTRIBUTES.items():
        # skip saving attribute for this node if nodeType does not match the filter for this setting, e.g. do not save 'collisionFilterMask' for anything but meshes
        if 'nodeTypeFilter' in v:
            if v['nodeTypeFilter'] != nodeType:
                continue

        if 'saveFunction' in v:
            v['saveFunction'](k, v, node)
        else:
            if v['type'] == TYPE_BOOL:
                I3DSaveAttributeBool(node, k, cmds.checkBox(v['uiControl'], q=True, v=True), default=v['defaultValue'])
            elif v['type'] == TYPE_INT:
                I3DSaveAttributeInt(node, k, cmds.intField(v['uiControl'], q=True, v=True))
            elif v['type'] == TYPE_FLOAT:
                I3DSaveAttributeFloat(node, k, cmds.floatField(v['uiControl'], q=True, v=True))
            elif v['type'] == TYPE_STRING:
                I3DSaveAttributeString(node, k, cmds.textField(v['uiControl'], q=True, text=True))
            elif v['type'] == TYPE_ENUM:
                I3DSaveAttributeEnum(node, k, cmds.optionMenu(v['uiControl'], q=True, sl=True) - 1, v['options']) #options menu is 1 based, enums are 0 based
            elif v['type'] == TYPE_HEX:
                I3DSaveAttributeHex(node, k, cmds.textField(v['uiControl'], q=True, text=True))

    I3DMigrateAttributes(node)
    I3DUpdateMayaAttributes(node)
    I3DUpdateLayers(node)
    I3DUpdateMass(node)

def I3DMigrateAttributes(node):
    # check if both legacy i3D_collisionMask and new i3D_collisionFilterGroup + i3D_collisionFilterMask are set
    oldMask = I3DGetAttributeValue(node, 'i3D_collisionMask', None)
    if oldMask is not None:
        groupHex = I3DGetAttributeValue(node, 'i3D_collisionFilterGroup', None)
        maskHex = I3DGetAttributeValue(node, 'i3D_collisionFilterMask', None)

        if groupHex is not None and maskHex is not None:
            I3DRemoveAttribute(node, 'i3D_collisionMask')
            print("Removed old 'i3D_collisionMask' {} since new 'i3D_collisionFilterGroup' is present".format(oldMask))

    # remove i3D_collisionFilterMask if node is not a shape or has no physics
    nodeType = I3DGetNodeType(node)
    if nodeType != NODETYPE_MESH or not (I3DGetAttributeValue(node, 'i3D_static', None) or I3DGetAttributeValue(node, 'i3D_kinematic', None) or I3DGetAttributeValue(node, 'i3D_dynamic', None)):
        I3DRemoveAttribute(node, 'i3D_collisionFilterMask')
        # print("Removed 'i3D_collisionFilterMask' from {} since node is not a shape or has no physics".format(node))

def I3DUpdateMayaAttributes(node):
    isDoubleSided = I3DGetAttributeValue(node, "i3D_doubleSided", None)
    if not isDoubleSided is None:
        shape = I3DGetNonIntermediateShapeFromNode(node)
        if shape != None and cmds.objExists(shape + ".doubleSided"):
            cmds.setAttr(shape + ".doubleSided", isDoubleSided)

def I3DRemoveAttributes(node):
    for k, v in SETTINGS_ATTRIBUTES.items():
        I3DRemoveAttribute(node, k)
    I3DUpdateLayers(node)
    I3DUpdateMass(node)

def I3DSaveAttributeString(node, attribute, value):
    fullname = node + '.' + attribute
    I3DRemoveAttribute(node, attribute) # in case the attribute's type changed
    cmds.addAttr(node, shortName=attribute, niceName=attribute, longName=attribute, dt='string')
    cmds.setAttr(fullname, value, type='string')

def I3DSaveAttributeHex(node, attribute, value):
    fullname = node + '.' + attribute
    I3DRemoveAttribute(node, attribute) # in case the attribute's type changed
    cmds.addAttr(node, shortName=attribute, niceName=attribute, longName=attribute, dt='string')
    if type(value) is not str:
        I3DShowWarning("I3DSaveAttributeHex: Trying to save value which is not a string: {}".format(value))
        return
    if not value.startswith("0x"):
        value = "0x" + value
    cmds.setAttr(fullname, value.lower(), type='string')

def I3DSaveAttributeEnum(node, attribute, value, options):
    fullname = node + '.' + attribute
    I3DRemoveAttribute(node, attribute) # in case the attribute's type changed
    cmds.addAttr(node, shortName=attribute, niceName=attribute, longName=attribute, at='enum', en=':'.join(options))
    cmds.setAttr(fullname, value)

def I3DSaveAttributeInt(node, attribute, value):
    fullname = node + '.' + attribute
    I3DRemoveAttribute(node, attribute) # in case the attribute's type changed
    cmds.addAttr(node, shortName=attribute, niceName=attribute, longName=attribute, at='long')
    cmds.setAttr(fullname, value)

def I3DSaveAttributeFloat(node, attribute, value):
    fullname = node + '.' + attribute
    I3DRemoveAttribute(node, attribute) # in case the attribute's type changed
    cmds.addAttr(node, shortName=attribute, niceName=attribute, longName=attribute, at='float')
    cmds.setAttr(fullname, value)

def I3DSaveAttributeBool(node, attribute, value, default=False):
    fullname = node + '.' + attribute
    I3DRemoveAttribute(node, attribute) # in case the attribute's type changed
    cmds.addAttr(node, shortName=attribute, niceName=attribute, longName=attribute, at='bool', defaultValue=default)
    cmds.setAttr(fullname, value)

def I3DGetAttributeValue(node, attribute, default):
    value, _ = I3DUtils.getAttributeValueAndType(node, attribute, default)
    return value

def I3DSetAttributeValue(node, attributeName, value):
    attribute = SETTINGS_ATTRIBUTES[attributeName]
    if 'saveFunction' in attribute:
        attribute['saveFunction'](attributeName, attribute, node)
    else:
        if attribute['type'] == TYPE_BOOL:
            I3DSaveAttributeBool(node, attributeName, value, default=attribute['defaultValue'])
        elif attribute['type'] == TYPE_INT:
            I3DSaveAttributeInt(node, attributeName, value)
        elif attribute['type'] == TYPE_FLOAT:
            I3DSaveAttributeFloat(node, attributeName, value)
        elif attribute['type'] == TYPE_STRING:
            I3DSaveAttributeString(node, attributeName, value)
        elif attribute['type'] == TYPE_ENUM:
            I3DSaveAttributeEnum(node, attributeName, value, attribute['options']) #options menu is 1 based, enums are 0 based
        elif attribute['type'] == TYPE_HEX:
            I3DSaveAttributeHex(node, attributeName, value)

def I3DRemoveAttribute(node, attribute):
    fullname = node + '.' + attribute
    if I3DAttributeExists(node, attribute):
        cmds.deleteAttr(fullname)

def I3DAttributeExists(node, attribute):
    return I3DUtils.attributeExists(node, attribute)

def I3DCombineMeshes(unused):
    nodes = cmds.ls(sl=True, o=True, l=True)
    if len(nodes) < 2:
        I3DShowWarning('You need to select at least 2 meshes!')
        return

    firstNode = nodes[0]

    parent = I3DUtils.getParent(firstNode)
    index = 0
    if not parent is None:
        index = I3DUtils.getCurrentNodeIndex(firstNode)
        firstNode = cmds.parent(firstNode, w=True)[0]
        nodes[0] = firstNode

    placeholder = cmds.group(em=True, name='placeholder', parent=firstNode)
    placeholder = cmds.parent(placeholder, w=True)

    newMesh = cmds.polyUnite(*nodes, name=firstNode, mergeUVSets=True, ch=False)
    newMesh = cmds.parent(newMesh, placeholder)
    worldPivots = cmds.xform(placeholder, q=True, ws=True, scalePivot=True)
    cmds.xform(newMesh, worldSpace=True, preserve=True, pivots=worldPivots)
    cmds.makeIdentity(newMesh, apply=True, t=True, r=True, s=True, n=False)
    newMesh = cmds.parent(newMesh, w=True)
    cmds.delete(placeholder)

    I3DRemoveNodeFromDisplayLayer(newMesh)

def I3DSelectIndex(unused):
    indexPath = cmds.textField(UI_CONTROL_STRING_NODE_INDEX, q=True, text=True)
    object = I3DUtils.getObjectByIndex(indexPath)
    if not object is None:
        cmds.select(object)

def I3DAddPluginCommandToShelf(optionMenuId):
    global g_loadedPluginCommands

    commandTitle = cmds.optionMenu(optionMenuId, query=True, v=True)

    command = g_loadedPluginCommands[commandTitle]
    if command is not None:
        layout = mel.eval('$gShelfTopLevel = $gShelfTopLevel;')
        active_shelf = cmds.shelfTabLayout(layout, q=True, selectTab=True)

        cmds.shelfButton(imageOverlayLabel=command["shelf_label"],
                         label=command["shelf_label"],
                         sourceType='python',
                         annotation=command["annotation"],
                         image1='pythonFamily.png',
                         fwv=32,
                         width=35,
                         command=command["shelf_command"],
                         parent=active_shelf)

def I3DClearOptionMenu(optionMenu):
    menuItems = cmds.optionMenu(optionMenu, q=True, itemListLong=True)
    if menuItems:
        cmds.deleteUI(menuItems)

def I3DUpdateShaderList(root):
    global SETTINGS_SHADERS
    shaderFiles = I3DUtils.getFilesInDir(root, '*Shader*.xml')
    if shaderFiles is not None:
        SETTINGS_SHADERS = {}
        for shader in shaderFiles:
            shaderClean = shader.replace(root, '')
            I3DParseShader(SETTINGS_SHADERS, shaderClean, root, shader)
            #cmds.menuItem(parent=UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, label=shaderClean)

    I3DUpdateShaderUI('None', 'None')
    return

def I3DParseShader(data, name, rootPath, shaderPath):
    shaderInfo = I3DUtils.getShaderInfo(rootPath+'/'+shaderPath)
    if shaderInfo is not None:
        data[name] = shaderInfo

def I3DUpdateShaderUI(selectedCustomShader, shaderVariationName):
    global SETTINGS_SHADER_PARAMETERS, SETTINGS_SHADER_TEXTURES, SETTINGS_SHADER_PARAMETER_TEMPLATES

    # Remove existing elements for parameters, textures and templates
    for k,v in SETTINGS_SHADER_PARAMETERS.items():
        parameter = v
        parameter.deleteUI()
    SETTINGS_SHADER_PARAMETERS.clear()

    for k,v in SETTINGS_SHADER_TEXTURES.items():
        parameter = v
        parameter.deleteUI()
    SETTINGS_SHADER_TEXTURES.clear()

    for parameterTemplate in SETTINGS_SHADER_PARAMETER_TEMPLATES:
        if cmds.frameLayout(SETTINGS_SHADER_PARAMETER_TEMPLATES[parameterTemplate]['frame'], exists=True):
            cmds.deleteUI(SETTINGS_SHADER_PARAMETER_TEMPLATES[parameterTemplate]['frame'])
    SETTINGS_SHADER_PARAMETER_TEMPLATES.clear()

    foundShader = I3DGetSelectedShader()

    # Find shader info of selected shader
    shaderInfo = None

    if selectedCustomShader in SETTINGS_SHADERS:
        shaderInfo = SETTINGS_SHADERS[selectedCustomShader]

    # Find groups to show based on selected shader variation
    showGroups = None
    if shaderInfo is not None:
        for v in shaderInfo['variations']:
            showGroups = ['base']
            if v['name'] == shaderVariationName:
                showGroups = v['groups'].split()
                break

    if shaderInfo is not None:
        referenceMaterial = I3DGetAttributeValue(str(foundShader), 'referenceMaterial', None)

        if 'parameters' in shaderInfo:
            numParams = 0
            for v in shaderInfo['parameters']:
                if showGroups is not None and v['group'] not in showGroups:
                    continue

                isSeparateMaterialParameter = not v['separateMaterialName'] is None

                parameter = I3DShader.I3DCustomShaderParameter(v['name'], 'customParameter_{}'.format(v['name']), v['defaultValue'], v['group'], isSeparateMaterialParameter, False)
                parameter.createUI(foundShader, UI_CONTROL_SHADER_PARAMETERS, referenceMaterial)
                SETTINGS_SHADER_PARAMETERS[v['name']] = parameter
                numParams += 1

            # Show all parameters up to 20, start scrolling if we have more
            numParams = min(numParams, 20)
            cmds.layout(UI_CONTROL_SHADER_PARAMETERS_SCROLL, edit=True, h=numParams*24 + 2 + 4)

        if 'textures' in shaderInfo:
            numTextures = 0
            for v in shaderInfo['textures']:
                if showGroups is not None and v['group'] not in showGroups:
                    continue

                isSeparateMaterialParameter = not v['separateMaterialName'] is None

                parameter = I3DShader.I3DCustomShaderParameter(v['name'], 'customTexture_{}'.format(v['name']), v['defaultValue'], v['group'], isSeparateMaterialParameter, True)
                parameter.createUI(foundShader, UI_CONTROL_SHADER_TEXTURES, referenceMaterial)
                SETTINGS_SHADER_TEXTURES[v['name']] = parameter
                numTextures += 1

            # Show all parameters up to 20, start scrolling if we have more
            numTextures = min(numTextures, 20)
            cmds.layout(UI_CONTROL_SHADER_TEXTURES, edit=True, h=numTextures*24 + 2 + 4)

        if 'parameterTemplates' in shaderInfo:
            gamePath = I3DGetGamePath()

            for parameterTemplate in shaderInfo['parameterTemplates']:
                templateFilePath = parameterTemplate['templateFile']
                templateFilePath = templateFilePath.replace('$', gamePath + '/')
                templateFile = I3DTemplateParameter.I3DTemplateParameterFile(templateFilePath, [v['name'] for v in parameterTemplate['parameters']])

                parameterFrame = cmds.frameLayout('giants_layoutTemplatedParameters_%s' % parameterTemplate['id'], parent='shaderScrollLayout', label=templateFile._name, cll=True, mh=2, mw=2, expandCommand=I3DSaveFrameState, collapseCommand=I3DSaveFrameState )
                parameterLayout = cmds.columnLayout('giants_templatedParameters_%s' % parameterTemplate['id'], parent=parameterFrame, adjustableColumn=True)

                #TODO(jdellsperger): rename 'frame' to 'layout'
                SETTINGS_SHADER_PARAMETER_TEMPLATES[parameterTemplate['id']] = {'frame': parameterFrame, 'parameters': parameterTemplate['parameters'] + parameterTemplate['textures'], 'rootSubTemplate': templateFile._id, 'subTemplates': {}}

                numParams = 0
                selectedParentTemplate = None
                while not templateFile is None and templateFile._isValid:
                    parentTemplateFile = None
                    if templateFile._parentTemplateFile is not None:
                        parentTemplateFilePath = templateFile._parentTemplateFile
                        parentTemplateFilePath = parentTemplateFilePath.replace('$', gamePath + '/')
                        parentTemplateFile = I3DTemplateParameter.I3DTemplateParameterFile(parentTemplateFilePath, [v['name'] for v in parameterTemplate['parameters']])

                    parentTemplateId = None
                    if parentTemplateFile is not None and parentTemplateFile._isValid:
                        parentTemplateId = parentTemplateFile._id
                    subTemplate = I3DTemplateParameter.I3DTemplateParameterSubTemplate(parameterTemplate['id'], templateFile, parameterLayout, I3DShaderParameterTemplateSelectCallback(parameterTemplate['id'], templateFile._id), parentSubTemplateId=parentTemplateId, defaultParentTemplate=templateFile._defaultParentTemplate, templates=templateFile._templates)

                    name = subTemplate.getAttributeName()
                    templateName = I3DGetAttributeValue(str(foundShader), name, None)
                    if templateName is not None and templateName in subTemplate._templates:
                        subTemplate.selectTemplate(templateName)
                        subTemplate.setActive(True)
                    elif selectedParentTemplate is not None:
                        templateName = selectedParentTemplate
                        subTemplate.selectTemplate(selectedParentTemplate)

                    if templateName in subTemplate._templates and 'parentTemplate' in subTemplate._templates[templateName] and subTemplate._templates[templateName]['parentTemplate'] is not None:
                        selectedParentTemplate = subTemplate._templates[templateName]['parentTemplate']
                    elif subTemplate._defaultParentTemplate is not None:
                        selectedParentTemplate = subTemplate._defaultParentTemplate
                    else:
                        selectedParentTemplate = None

                    numParams += 1

                    SETTINGS_SHADER_PARAMETER_TEMPLATES[parameterTemplate['id']]['subTemplates'][templateFile._id] = subTemplate

                    templateFile = parentTemplateFile

                rootSubTemplate = SETTINGS_SHADER_PARAMETER_TEMPLATES[parameterTemplate['id']]['rootSubTemplate']
                for v in parameterTemplate['parameters']:
                    if showGroups is not None and v['group'] not in showGroups:
                        continue

                    templateOptions = {}
                    for template, values in SETTINGS_SHADER_PARAMETER_TEMPLATES[parameterTemplate['id']]['subTemplates'][rootSubTemplate]._templates.items():
                        label = template
                        if values['description'] is not None:
                            label = label + " (%s)" % values['description']

                        templateOptions[template] = {"templateName": template, "label": label, "value": values[v['name']]}

                    prefix = 'customParameter_'
                    if v['isTexture']:
                        prefix = 'customTexture_'

                    isSeparateMaterialParameter = not v['separateMaterialName'] is None

                    parameter = I3DShader.I3DCustomShaderParameter(v['name'], '{}{}'.format(prefix, v['name']), v['defaultValue'], v['group'], isSeparateMaterialParameter, v['isTexture'], parameterTemplate['id'], templateOptions=templateOptions)
                    parameter.createUI(foundShader, parameterLayout, referenceMaterial)
                    SETTINGS_SHADER_PARAMETERS[v['name']] = parameter
                    numParams += 1

                numParams = min(numParams, 20)
                cmds.layout(parameterLayout, edit=True, h=numParams*24 + 2 + 4)

def I3DCustomParameterCheckboxCallback(textField):
    return lambda checked : I3DmakeCustomParameterEditable(textField, checked)

def I3DmakeCustomParameterEditable(textField, checked):
    if checked:
        cmds.textField(textField, edit=True, ed=True)
    else:
        cmds.textField(textField, edit=True, ed=False)

def I3DGetSelectedShader():
    shader = cmds.optionMenu(UI_CONTROL_SELECTED_MATERIAL, q=True, value=True)
    if shader != "None":
        return shader
    return None

def I3DChangeMaterialSelectionCallback(unused):
    shader = I3DGetSelectedShader()
    if shader is not None:
        I3DLoadMaterial(shader)
        I3DUtils.selectMaterialFaces(shader)
    else:
        cmds.select(clear=True)
        I3DLoadMaterial(None)

def I3DChangeCustomShaderCallback(customShader):
    global SETTINGS_SHADERS, UI_CONTROL_MENU_SHADER_VARIATION

    shader = I3DUtils.getMaterialFromSelection()

    cleanShaderName = os.path.basename(os.path.normpath(customShader))
    shaderInfo = None
    if cleanShaderName in SETTINGS_SHADERS:
        shaderInfo = SETTINGS_SHADERS[cleanShaderName]

    # Clear shader variations menu and rebuild
    I3DClearOptionMenu(UI_CONTROL_MENU_SHADER_VARIATION)
    cmds.menuItem(parent=UI_CONTROL_MENU_SHADER_VARIATION, label='None')
    cmds.optionMenu(UI_CONTROL_MENU_SHADER_VARIATION, edit=True, sl=1)

    shaderVariationName = ''
    if shaderInfo is not None:
        for v in shaderInfo['variations']:
            cmds.menuItem(parent=UI_CONTROL_MENU_SHADER_VARIATION, label=v["name"])

        shaderVariationName = I3DGetAttributeValue(str(shader), "customShaderVariation", None)
        if shaderVariationName is not None and shaderInfo is not None:
            for i in range(0, len(shaderInfo['variations'])):
                if shaderInfo['variations'][i]['name'] == shaderVariationName:
                    cmds.optionMenu(UI_CONTROL_MENU_SHADER_VARIATION, edit=True, sl=i+2) # +2 because 1 based and first entry is for 'None'
                    break

    # update ui elements
    I3DUpdateShaderUI(cleanShaderName, shaderVariationName)

def I3DUpdateShaderVariationUI(selectedVariationItemName):
    customShader = cmds.optionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, query=True, value=True)
    if customShader is not None:
        cleanShaderName = os.path.basename(os.path.normpath(customShader))
        cleanShaderName = cleanShaderName.replace('.ogsfx', '.xml')
        I3DUpdateShaderUI(cleanShaderName, selectedVariationItemName)

def I3DShaderParameterTemplateSelectCallback(parameterTemplateId, subTemplateId):
    return lambda a : I3DShaderParameterTemplateSelected(parameterTemplateId, subTemplateId, a)

def I3DShaderParameterTemplateSelected(parameterTemplateId, subTemplateId, selectedItem):
    global SETTINGS_SHADER_PARAMETER_TEMPLATES

    selectedParameterTemplate = SETTINGS_SHADER_PARAMETER_TEMPLATES[parameterTemplateId]
    rootSubTemplate = selectedParameterTemplate['subTemplates'][selectedParameterTemplate['rootSubTemplate']]

    for _, subTemplate in selectedParameterTemplate['subTemplates'].items():
        subTemplate.setActive(subTemplate._id == subTemplateId)

    # Set the selected parent sub templates, unless they are overriden
    currentSubTemplate = rootSubTemplate
    while not currentSubTemplate is None:
        parentSubTemplateId = currentSubTemplate._parentSubTemplateId

        # If there is no more parent template file, stop
        if parentSubTemplateId is None:
            break

        parentSubTemplate = selectedParameterTemplate['subTemplates'][parentSubTemplateId]

        # If the parent sub template has a custom value set, don't
        # override it and continue up the ancestry chain.
        if cmds.checkBox(parentSubTemplate._checkbox, q=True, v=True):
            currentSubTemplate = parentSubTemplate
            continue

        # Retrieve the selected template of the current sub template
        selectedParentTemplate = None
        templateName = currentSubTemplate.getSelectedTemplate()

        if templateName == '': #TODO(jdellsperger): change to 'None'
            selectedParentTemplate = '' #TODO(jdellsperger): change to 'None'

        # If the selected template is not 'None', try to find the parent template to select
        if selectedParentTemplate is None and templateName in currentSubTemplate._templates:
            template = currentSubTemplate._templates[templateName]
            if 'parentTemplate' in template:
                selectedParentTemplate = template['parentTemplate']

            # If no parent template is selected, use the default parent template
            if selectedParentTemplate is None and currentSubTemplate._defaultParentTemplate is not None:
                selectedParentTemplate = currentSubTemplate._defaultParentTemplate

        # Make sure the selected parent template actually exists
        if selectedParentTemplate is not None and (selectedParentTemplate in parentSubTemplate._templates or selectedParentTemplate == ''):
            parentSubTemplate.selectTemplate(selectedParentTemplate)
        currentSubTemplate = parentSubTemplate

    for v in selectedParameterTemplate['parameters']:
        name = v['name']
        if name not in SETTINGS_SHADER_PARAMETERS:
            continue

        parameter = SETTINGS_SHADER_PARAMETERS[name]
        if parameter.hasCustomValue():
            continue

        # The value of the parameter is loaded from the first subtemplate
        # in the ancestry chain that has it set.
        currentSubTemplate = rootSubTemplate
        while not currentSubTemplate is None:
            templateName = currentSubTemplate.getSelectedTemplate()
            template = None
            if templateName in currentSubTemplate._templates:
                template = currentSubTemplate._templates[templateName]

            if not template is None and name in template and not template[name] is None:
                parameter.setUIValue(template[name])
                break
            elif not currentSubTemplate._parentSubTemplateId is None:
                currentSubTemplate = selectedParameterTemplate['subTemplates'][currentSubTemplate._parentSubTemplateId]
            else:
                currentSubTemplate = None

def I3DGetTemplateParameterValue(materialNodeId, parameterTemplateId, parameterName, getStored = False):
    global SETTINGS_SHADER_PARAMETER_TEMPLATES
    if parameterTemplateId not in SETTINGS_SHADER_PARAMETER_TEMPLATES:
        return None

    selectedParameterTemplate = SETTINGS_SHADER_PARAMETER_TEMPLATES[parameterTemplateId]

    # The value of the parameter is loaded from the first subtemplate
    # in the ancestry chain that has it set.
    currentSubTemplateId = selectedParameterTemplate['rootSubTemplate']
    currentSubTemplate = selectedParameterTemplate['subTemplates'][currentSubTemplateId]
    while not currentSubTemplate is None:
        if getStored:
            attrName = 'customParameterTemplate_{}_{}'.format(parameterTemplateId, currentSubTemplateId)
            templateName = I3DGetAttributeValue(materialNodeId, attrName, None)
        else:
            templateName = currentSubTemplate.getSelectedTemplate()

        # Retrieve the currently selected template
        template = None
        if templateName in currentSubTemplate._templates:
            template = currentSubTemplate._templates[templateName]

        if not template is None and parameterName in template and template[parameterName] is not None:
            # Check if the searched parameter is defined in the template and if yes,
            # return it
            return template[parameterName]
        elif not currentSubTemplate._parentSubTemplateId is None:
            # Otherwise continue to the parent subtemplate if there is one
            currentSubTemplateId = currentSubTemplate._parentSubTemplateId
            currentSubTemplate = selectedParameterTemplate['subTemplates'][currentSubTemplateId]
        else:
            # If no more subtemplates exist in the hierarchy, the parameter was not defined
            currentSubTemplate = None

def I3DGetNodeShaders():
    # get selected nodes:
    nodes = cmds.ls(selection=True, dag=True)
    shadingGroups = []
    shaders = []

    # get shading groups from shapes:
    if len(nodes) >= 1:
        shadingGroups = cmds.listConnections(nodes, t='shadingEngine')
        # get the shaders:
        if shadingGroups is not None and len(shadingGroups) >= 1:
            shaders = cmds.ls(cmds.listConnections(shadingGroups), materials=1)

    # this makes sure that if we've only selected a shader, the button will still work
    if len(shaders) == 0:
        nodes = cmds.ls(selection=True)
        for node in nodes:
            if cmds.nodeType(node, inherited=True)[0] == 'shadingDependNode':
                shaders.append(node)

    # graph shaders to the network in the hypershade:
    if len(shaders) >= 1:
        cmds.hyperShade(shaders)

    return shaders

def I3DDuplicateMaterial(unused):
    selectedShader = I3DGetSelectedShader()
    cmds.select(selectedShader)
    import vehicleShaderTools
    reload(vehicleShaderTools)
    vehicleShaderTools.duplicateSelectedMaterial();

def I3DConvertMaterials(unused):
    import vehicleShaderTools
    reload(vehicleShaderTools)
    vehicleShaderTools.convertFS22toFS25();

    import MaterialTools
    reload(MaterialTools)
    plugin = MaterialTools.MaterialTools()
    plugin.executeRemoveDuplicateTextures()
    plugin.executeRemoveDuplicateMaterials()
    plugin.executeRenameMaterials()
    plugin.executeRenameTextures()
    del plugin

    import CleanupTools
    reload(CleanupTools)
    plugin = CleanupTools.CleanupTools()
    plugin.cleanup()
    del plugin

def I3DVehicleShaderDebug(unused):
    import vehicleShaderDebug
    reload(vehicleShaderDebug)
    vehicleShaderDebug.materialDebugWin()

def I3DVehicleShaderTemplates(unused):
    import vehicleShaderMaterialTemplates
    reload(vehicleShaderMaterialTemplates)
    vehicleShaderMaterialTemplates.main()

def I3DSetMaterialAttributesFromXMLCallback(callbackData):
    '''
    Sets material parameters according to the material name and values passed in callbackData.
    Expects callbackdata in the form of: {'matName': matName, 'customParameters': {'paramName': paramValue}}
    '''
    applySuccessful = True
    if 'matName' not in callbackData:
        applySuccessful = False

    shader = None
    if applySuccessful:
        shader = callbackData['matName']

        try:
            cmds.optionMenu(UI_CONTROL_SELECTED_MATERIAL, edit=True, v=shader)
        except RuntimeError:
            I3DReloadMaterialList()
            try:
                cmds.optionMenu(UI_CONTROL_SELECTED_MATERIAL, edit=True, v=shader)
            except RuntimeError:
                I3DShowWarning("Material \"{}\" not found. Cannot apply material parameters.\n".format(shader))
                applySuccessful = False
    
    if applySuccessful:
        I3DLoadMaterial(shader)
        I3DUtils.selectMaterialFaces(shader)

        for customParamName, customParamValue in callbackData['customParameters'].items():
            try:
                param = SETTINGS_SHADER_PARAMETERS[customParamName]
            except KeyError:
                I3DShowWarning("Material \"{}\" has no parameter \"{}\", skipping.".format(shader, customParamName))
                continue
            param.setCustomValue(customParamValue)

    return applySuccessful

def I3DSetMaterialAttributesFromXML(unused):
    import ImportMaterialAttributesFromXML
    reload(ImportMaterialAttributesFromXML)
    ImportMaterialAttributesFromXML.ImportMaterialAttributesFromXML(
        guiId='ImportMaterialAttributesFromXMLUI',
        guiTitle='Import Material Attributes from XML',
        callbackFunction=I3DSetMaterialAttributesFromXMLCallback
    )

# List of material attribute names. Does not include customParameter_ or customTexture_ because only the prefix is checked
KNOWN_MATERIAL_ATTRIBUTE_NAMES = ['customShader', 'customShaderVariation', 'shadingRate', 'reflectionMapShapesObjectMask', 'reflectionMapLightsObjectMask', 'refractionMapWithSSRData', ]
def getIsKnownMaterialAttribute(attr):
    attr = str(attr)
    return attr.startswith('customParameter_') or attr.startswith('customTexture_') or attr.startswith('customParameterTemplate_') or (attr in KNOWN_MATERIAL_ATTRIBUTE_NAMES)

def I3DApplyMaterial(unused):
    shader = I3DGetSelectedShader()

    if shader == None:
        return

    shaderAttributes = cmds.listAttr(shader, userDefined=True)
    if shaderAttributes is not None:
        for shaderAttribute in shaderAttributes:
            attr = shaderAttribute
            categories = cmds.attributeQuery(attr, node=str(shader), categories=True)
            if 'HW_shader_parameter' in categories:
                # Don't remove HW shader parameters
                continue

            if (attr.replace('customParameter_', '') not in SETTINGS_SHADER_PARAMETERS and attr.startswith('customParameter_')):
                I3DRemoveAttribute(str(shader), attr)
                continue
            elif (attr.replace('customTexture_', '') not in SETTINGS_SHADER_TEXTURES and attr.startswith('customTexture_')):
                I3DRemoveAttribute(str(shader), attr)
                continue
            elif (attr.replace('customParameterTemplate_', '') not in SETTINGS_SHADER_PARAMETER_TEMPLATES and attr.startswith('customParameterTemplate_')):
                I3DRemoveAttribute(str(shader), attr)
                continue

    shaderPath = ''
    shaderName = cmds.optionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, query=True, value=True)
    if shaderName is not None and shaderName != '' and shaderName != 'None':
        root = cmds.textField(UI_CONTROL_STRING_SHADER_PATH, query=True, text=True)
        shaderPath = I3DUtils.getRelativeShaderPath(root+'/'+shaderName)
        if (-1!=root.find('data/shaders')):
            shaderPath = '$data/shaders/'+shaderName

    if shaderPath != '':
        if cmds.nodeType(str(shader)) != 'GLSLShader':
            I3DAddAttribute(str(shader), 'customShader', shaderPath)

        #TODO(jdellsperger): handle setting of 'customShader' attribute for GLSLShaders

        for k,v in SETTINGS_SHADER_PARAMETER_TEMPLATES.items():
            for subTemplateId,subTemplate in v['subTemplates'].items():
                name = 'customParameterTemplate_%s_%s' % (k,subTemplateId)
                if cmds.checkBox(subTemplate._checkbox, query=True, value=True):
                    value = subTemplate.getSelectedTemplate()
                    I3DAddAttribute(str(shader), name, value)
                else:
                    I3DRemoveAttribute(str(shader), name)

        for k,v in SETTINGS_SHADER_PARAMETERS.items():
            parameter = v
            parameter.apply(shader)

        for k,v in SETTINGS_SHADER_TEXTURES.items():
            parameter = v
            parameter.apply(shader)

        variation = cmds.optionMenu(UI_CONTROL_MENU_SHADER_VARIATION, query=True, value=True)
        if not variation is None and variation != '' and variation != 'None' and (cmds.nodeType(str(shader)) == 'GLSLShader' or variation != 'base'):
            I3DAddAttribute(str(shader), 'customShaderVariation', variation)
        else:
            if cmds.nodeType(str(shader)) == 'GLSLShader':
                I3DAddAttribute(str(shader), 'customShaderVariation', 'base')
            else:
                I3DRemoveAttribute(str(shader), 'customShaderVariation')
    else:
        if cmds.nodeType(str(shader)) == 'GLSLShader':
            I3DAddAttribute(str(shader), 'shader', 'baseShader.ogsfx')
        else:
            I3DRemoveAttribute(str(shader), 'customShader')

    shadingRate = cmds.optionMenu(UI_CONTROL_MENU_MATERIAL_SHADING_RATE, query=True, value=True)
    if shadingRate is not None and shadingRate != '':
        if cmds.nodeType(str(shader)) != 'GLSLShader' and shadingRate == '1x1':
            I3DRemoveAttribute(str(shader), 'shadingRate')
        else:
            I3DAddAttribute(str(shader), 'shadingRate', shadingRate)

    reflectionMapShapesObjectMask = cmds.textField(UI_CONTROL_STRING_MATERIAL_REFLECTION_MAP_SHAPES_OBJECT_MASK, query=True, text=True)
    if reflectionMapShapesObjectMask is not None and reflectionMapShapesObjectMask != "" and reflectionMapShapesObjectMask != '4294967295':
        I3DAddAttribute(str(shader), 'reflectionMapShapesObjectMask', reflectionMapShapesObjectMask)

    reflectionMapLightsObjectMask = cmds.textField(UI_CONTROL_STRING_MATERIAL_REFLECTION_MAP_LIGHTS_OBJECT_MASK, query=True, text=True)
    if reflectionMapLightsObjectMask is not None and reflectionMapLightsObjectMask != "" and reflectionMapLightsObjectMask != '4294967295':
        I3DAddAttribute(str(shader), 'reflectionMapLightsObjectMask', reflectionMapLightsObjectMask)

    refractionMapWithSSRData = cmds.checkBox(UI_CONTROL_BOOL_MATERIAL_REFRACTION_MAP_WITH_SSR_DATA, query=True, value=True)
    if refractionMapWithSSRData:
        I3DAddAttribute(str(shader), 'refractionMapWithSSRData', "true")
    else:
        I3DRemoveAttribute(str(shader), 'refractionMapWithSSRData')

    if cmds.nodeType(str(shader)) == 'GLSLShader':
        alphaBlending = cmds.checkBox(UI_CONTROL_BOOL_MATERIAL_ALPHA_BLENDING, query=True, value=True)
        technique = 'base'
        if alphaBlending:
            technique = 'alphaBlending'
        I3DAddAttribute(str(shader), 'technique', technique)

    referenceMaterial = cmds.textField(UI_CONTROL_STRING_MATERIAL_REFERENCE_MATERIAL, query=True, text=True)
    if referenceMaterial == '':
        I3DRemoveAttribute(shader, 'referenceMaterial')
    else:
        I3DAddAttribute(shader, 'referenceMaterial', referenceMaterial)

    slotName = cmds.textField(UI_CONTROL_STRING_MATERIAL_SLOT_NAME, query=True, text=True)
    if slotName == '':
        I3DRemoveAttribute(shader, 'slotName')
    else:
        I3DAddAttribute(shader, 'slotName', slotName)

    # Select the material again - otherwise in case of a GLSL shader where new texture nodes were created
    # these will be selected
    cmds.select(str(shader))

def I3DLoadGLSLMaterial(materialNode):
    for shaderName, shaderCand in SETTINGS_SHADERS.items():
        if shaderCand['hasGLSLShader'] == True:
            shaderClean = shaderName.replace('.xml', '.ogsfx')
            cmds.menuItem(parent=UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, label=shaderClean)
    shaderFilename = I3DGetAttributeValue(str(materialNode), 'shader', '')
    selectionName = os.path.basename(os.path.normpath(shaderFilename))

    try:
        cmds.optionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, edit=True, value=selectionName)
    except:
        if cmds.optionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, q=True, numberOfItems=True) > 0:
            cmds.optionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, edit=True, sl=1)

        shaderPath = I3DGetProjectSetting("GIANTS_SHADER_DIR")
        cmds.confirmDialog(title="Error", message="Shader '%s' was not found in the set shader directory '%s'" % (selectionName.replace(".ogsfx", ".xml"), shaderPath))

    customShader = shaderFilename.replace('.ogsfx', '.xml')
    cleanShaderName = os.path.basename(os.path.normpath(customShader))

    # Retrieve shader info
    shaderInfo = None
    if cleanShaderName in SETTINGS_SHADERS:
        shaderInfo = SETTINGS_SHADERS[cleanShaderName]

    # Rebuild shader variation drop down
    cmds.menuItem(parent=UI_CONTROL_MENU_SHADER_VARIATION, label='base')
    if shaderInfo is not None:
        for v in shaderInfo['variations']:
            cmds.menuItem(parent=UI_CONTROL_MENU_SHADER_VARIATION, label=v["name"])

    cmds.optionMenu(UI_CONTROL_MENU_SHADER_VARIATION, edit=True, sl=1)
    shaderVariationName = I3DUtils.getAttributeValueAsStr(str(materialNode), 'customShaderVariation', 'base')
    if shaderVariationName == None:
        shaderVariationName = 'base'
    cmds.optionMenu(UI_CONTROL_MENU_SHADER_VARIATION, edit=True, value=shaderVariationName)

    # Load selected shading rate
    shadingRateId = I3DGetAttributeValue(str(materialNode), "shadingRate", None)
    if shadingRateId is not None:
        # GLSL shaders return shadingRate as int, phong shaders as string
        if isinstance(shadingRateId, int):
            cmds.optionMenu(UI_CONTROL_MENU_MATERIAL_SHADING_RATE, edit=True, sl=shadingRateId+1)
        else:
            cmds.optionMenu(UI_CONTROL_MENU_MATERIAL_SHADING_RATE, edit=True, v=shadingRateId)
    else:
        cmds.optionMenu(UI_CONTROL_MENU_MATERIAL_SHADING_RATE, edit=True, sl=1)

    # Set alpha blending checkbox
    technique = I3DGetAttributeValue(str(materialNode), 'technique', None)
    alphaBlending = (technique == 'alphaBlending')
    cmds.checkBox(UI_CONTROL_BOOL_MATERIAL_ALPHA_BLENDING, edit=True, value=alphaBlending)
    alphaBlendingRow = cmds.checkBox(UI_CONTROL_BOOL_MATERIAL_ALPHA_BLENDING, query=True, parent=True)
    cmds.rowLayout(alphaBlendingRow, edit=True, visible=True)

    return cleanShaderName, shaderVariationName

def I3DLoadPhongMaterial(materialNode):
    # Populate custom shader dropdown
    cmds.menuItem(parent=UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, label='None')
    for shaderName, _ in SETTINGS_SHADERS.items():
        cmds.menuItem(parent=UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, label=shaderName)
    cmds.menuItem(parent=UI_CONTROL_MENU_SHADER_VARIATION, label='None')

    shaderFilename = I3DGetAttributeValue(str(materialNode), 'customShader', None)

    cleanShaderName = ''
    shaderVariationName = ''
    if shaderFilename is not None:
        customShader = shaderFilename.replace('.ogsfx', '.xml')
        cleanShaderName = os.path.basename(os.path.normpath(customShader))

        shaderMenuItems = cmds.optionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, q=True, itemListLong=True)
        shaderMenuItemIndex = 1
        for shaderMenuItem in shaderMenuItems:
            label = cmds.menuItem(shaderMenuItem, query=True, label=True)
            if label == cleanShaderName:
                cmds.optionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, edit=True, value=cleanShaderName)
                break
            shaderMenuItemIndex = shaderMenuItemIndex + 1

        # Retrieve shader info
        shaderInfo = None
        if cleanShaderName in SETTINGS_SHADERS:
            shaderInfo = SETTINGS_SHADERS[cleanShaderName]

        # Rebuild shader variation drop down
        if shaderInfo is not None and 'variations' in shaderInfo:
            for v in shaderInfo['variations']:
                cmds.menuItem(parent=UI_CONTROL_MENU_SHADER_VARIATION, label=v["name"])

        cmds.optionMenu(UI_CONTROL_MENU_SHADER_VARIATION, edit=True, sl=1)
        shaderVariationName = I3DGetAttributeValue(str(materialNode), "customShaderVariation", None)
        if shaderVariationName is not None and shaderInfo is not None:
            found = False
            for i in range(0, len(shaderInfo['variations'])):
                if shaderInfo['variations'][i]['name'] == shaderVariationName:
                    cmds.optionMenu(UI_CONTROL_MENU_SHADER_VARIATION, edit=True, sl=i+2) # +2 because 1 based and first entry is for 'None'
                    found = True
                    break
            if not found:
                I3DShowWarning('Custom shader variation "' + str(shaderVariationName) + '" in "' + str(materialNode) + '" not found')

    # Load selected shading rate
    selectedShadingRate = I3DGetAttributeValue(str(materialNode), "shadingRate", None)
    if selectedShadingRate is not None:
        cmds.optionMenu(UI_CONTROL_MENU_MATERIAL_SHADING_RATE, edit=True, value=selectedShadingRate)
    else:
        cmds.optionMenu(UI_CONTROL_MENU_MATERIAL_SHADING_RATE, edit=True, sl=1)

    alphaBlendingRow = cmds.checkBox(UI_CONTROL_BOOL_MATERIAL_ALPHA_BLENDING, query=True, parent=True)
    cmds.rowLayout(alphaBlendingRow, edit=True, visible=False)

    return cleanShaderName, shaderVariationName

def I3DSlotNameUseMaterialName(unused):
    customShader = cmds.optionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES, query=True, value=True)
    if customShader is not None:
        shader = I3DGetSelectedShader()

        slotName = str(shader)
        I3DSaveAttributeString(str(shader), "slotName", slotName)
        cmds.textField(UI_CONTROL_STRING_MATERIAL_SLOT_NAME, edit=True, text=slotName)

def I3DLoadMaterialButtonCallback(unused):
    shader = I3DGetSelectedShader()
    I3DLoadMaterial(shader)

def I3DLoadMaterial(shader):
    # Clear custom shader and variation drop down
    I3DClearOptionMenu(UI_OPTIONS_PREDEFINED_SHADER_ATTRIBUTES)
    I3DClearOptionMenu(UI_CONTROL_MENU_SHADER_VARIATION)

    # Load custom shader and variation according to material node type
    if shader is not None and cmds.nodeType(str(shader)) == 'GLSLShader':
        cleanShaderName, shaderVariationName = I3DLoadGLSLMaterial(shader)
    else:
        cleanShaderName, shaderVariationName = I3DLoadPhongMaterial(shader)

    # update ui elements
    I3DUpdateShaderUI(cleanShaderName, shaderVariationName)

    value = I3DGetAttributeValue(str(shader), "reflectionMapShapesObjectMask", '4294967295')
    cmds.textField(UI_CONTROL_STRING_MATERIAL_REFLECTION_MAP_SHAPES_OBJECT_MASK, edit=True, text=value)

    value = I3DGetAttributeValue(str(shader), "reflectionMapLightsObjectMask", '4294967295')
    cmds.textField(UI_CONTROL_STRING_MATERIAL_REFLECTION_MAP_LIGHTS_OBJECT_MASK, edit=True, text=value)

    refractionMapWithSSRData = I3DGetAttributeValue(str(shader), "refractionMapWithSSRData", False)
    cmds.checkBox(UI_CONTROL_BOOL_MATERIAL_REFRACTION_MAP_WITH_SSR_DATA, edit=True, value=bool(refractionMapWithSSRData))

    referenceMaterial = I3DGetAttributeValue(str(shader), 'referenceMaterial', None)
    cmds.textField(UI_CONTROL_STRING_MATERIAL_REFERENCE_MATERIAL, edit=True, text=referenceMaterial)

    slotName = I3DGetAttributeValue(str(shader), 'slotName', None)
    cmds.textField(UI_CONTROL_STRING_MATERIAL_SLOT_NAME, edit=True, text=slotName)

def I3DRemoveMaterial(unused):
    shaders = I3DGetNodeShaders()
    if len(shaders) > 0:
        shader = shaders[0]

        # TODO(jdellsperger): Fix this for glsl shaders
        if cmds.nodeType(str(shader)) == 'GLSLShader':
            return

        currentAttributes = cmds.listAttr(str(shader), userDefined=True)

        # delete all attributes we are changing with the material gui
        if currentAttributes is not None:
            for attr in currentAttributes:
                if getIsKnownMaterialAttribute(attr):
                    cmds.deleteAttr(str(shader)+'.'+str(attr))

        cmds.setAttr(str(shader) + '.translucence', 0.0)

        I3DLoadMaterial(None)

def I3DReloadMaterialList():
    # TODO: make this a generic "clear" and "populate" functions which also support annotations
    I3DClearOptionMenu(UI_CONTROL_SELECTED_MATERIAL)
    cmds.menuItem(parent=UI_CONTROL_SELECTED_MATERIAL, label='None')

    I3DUtils.fixHiddenMaterialsInScene()

    materialGroup = I3DUtils.getMergableMaterialList()
    for group in materialGroup:
        cmds.menuItem(parent=UI_CONTROL_SELECTED_MATERIAL, divider=True)
        for material in group:
            cmds.menuItem(parent=UI_CONTROL_SELECTED_MATERIAL, label=material)

def I3DShowWarning(text):
    if hasattr(cmds, 'warning'):
        cmds.warning(text)
    else:
        print(text)

def I3DUpdateLayers(node):
    I3DRemoveNodeFromDisplayLayer(node)

    mergeGroup = I3DGetAttributeValue(node, 'i3D_mergeGroup', 0)
    layer = I3DCreateDisplayLayer('MERGEGROUP_'+str(mergeGroup), mergeGroup)
    I3DAddNodeToDisplayLayer(node, layer)

def I3DAddNodeToDisplayLayer(node, layer):
    cmds.editDisplayLayerMembers(layer, node, noRecurse=True)

def I3DRemoveNodeFromDisplayLayer(node):
    if cmds.objExists("defaultLayer"):
        cmds.editDisplayLayerMembers("defaultLayer", node, noRecurse=True)

def I3DCreateDisplayLayer(name, mergeGroup):
    displayLayers = cmds.ls(name, type='displayLayer')
    if not len(displayLayers):
        colorIndex = 4
        if mergeGroup in MERGEGROUP_COLORS:
            colorIndex = MERGEGROUP_COLORS[mergeGroup]

        cmds.createDisplayLayer(name=name, number=1, empty=True)
        cmds.setAttr(name+'.displayType', 0)
        cmds.setAttr(name+'.color', colorIndex)
        cmds.setAttr(name+'.visibility', True)
    return name


def I3DGetIsVisible(node, overallVisibility=True):
    if not cmds.getAttr(node+'.visibility'):
        return False
    elif overallVisibility:
        parent = I3DUtils.getParent(node)
        if not parent is None:
            return I3DGetIsVisible(parent, overallVisibility=overallVisibility)

    return True

def I3DFindCompound(node):
    if node is None:
        return None

    isCompound = I3DGetAttributeValue(node, 'i3D_compound', False)
    if isCompound:
        return node
    else:
        parentNode = I3DUtils.getParent(node)
        if not parentNode is None:
            return I3DFindCompound(parentNode)
        else:
            return None

def I3DGetCompoundMass(node, isCompoundNode):
    if node is None:
        return 0

    mass = 0

    isDynamic = I3DGetAttributeValue(node, 'i3D_dynamic', False)
    isCompound = I3DGetAttributeValue(node, 'i3D_compound', False)
    isCompoundChild = I3DGetAttributeValue(node, 'i3D_compoundChild', False)

    if isDynamic and (isCompoundNode and isCompound) or (not isCompoundNode and isCompoundChild):
        mass = I3DUtils.getMeshVolume(node) * I3DGetAttributeValue(node, 'i3D_density', 0)

    children = cmds.listRelatives(node, type='transform', fullPath=True)
    if not children is None:
        for child in children:
            mass = mass + I3DGetCompoundMass(child, False)

    return mass

def I3DGetNonIntermediateShapeFromNode(node):
    selectedShape = None
    shapes = cmds.listRelatives(node, shapes=True)
    try:
        for shape in shapes:
            if shape.endswith("Orig"):
                continue

            if cmds.getAttr(shape + '.intermediateObject'):
                continue
            
            selectedShape = shape
            break
    except:
        # No shape children, just return None
        pass

    return selectedShape

def I3DUpdateMass(node):

    isDynamic = I3DGetAttributeValue(node, 'i3D_dynamic', False)
    cmds.text(UI_CONTROL_LABEL_MASS, edit=True, visible=isDynamic)
    cmds.floatField(UI_CONTROL_FLOAT_MASS, edit=True, visible=isDynamic)
    cmds.textField(UI_CONTROL_STRING_MASS_NODE, edit=True, visible=isDynamic)
    if isDynamic:
        compoundNode = node

        isCompound = I3DGetAttributeValue(node, 'i3D_compound', False)
        if not isCompound:
            compoundNode = I3DFindCompound(node)
        if not compoundNode is None:
            cmds.textField(UI_CONTROL_STRING_MASS_NODE, edit=True, text=compoundNode)
            mass = I3DGetCompoundMass(compoundNode, True)
            cmds.floatField(UI_CONTROL_FLOAT_MASS, edit=True, value=mass)
        else:
            cmds.textField(UI_CONTROL_STRING_MASS_NODE, edit=True, text='Compound-Node not found!')
            return

def I3DSetProjectSetting(name, value):
    cmds.workspace(variable=(name, value))
    cmds.workspace(s=True)

def I3DGetProjectSetting(name):
    return cmds.workspace(variableEntry=name) or cmds.optionVar(q=name)  # still have fallback to global variables

def I3DSearchShaderInBasegame(shaderFile):
    foundInBasegame = False
    shaderDir = I3DGetProjectSetting("GIANTS_SHADER_DIR")

    try:
        if isinstance(shaderDir, unicode):
            shaderDir = shaderDir.encode('ascii', 'ignore')
    except NameError:
        pass

    if isinstance(shaderDir, str):
        if os.path.isdir(shaderDir):
            for r, d, f in os.walk(shaderDir):
                for file in f:
                    if shaderFile in file:
                        foundInBasegame = True

            return (True, foundInBasegame)

    return (False, False)

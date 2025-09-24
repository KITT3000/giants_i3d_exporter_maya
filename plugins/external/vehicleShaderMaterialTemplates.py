#
#   SCRIPT     vehicleShaderMaterialTemplates.py
#   AUTHOR     Evgen Zaitsev
#
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import os
import I3DUtils
import I3DMaterialTemplateWindow

def createVehicleMaterial(uiInstance,item):
    '''
    Creates GLSL Maya preview vehicleShader
    '''
    # should be relative to basegame
    ogsfxFile = os.path.abspath("{}/data/shaders/vehicleShader.ogsfx".format(uiInstance._gamePath))
    #
    # create GLSLShader material
    #
    matName = "{}_{}_mat".format(I3DUtils.getNameFromFilePath(uiInstance._diffuse),item['nicename'])
    matInstance = cmds.shadingNode('GLSLShader',name=matName , asShader=True)
    print("Created: {}".format(matInstance))
    # set shader to the vehicleShader
    cmds.setAttr("{}.shader".format(matInstance), "{}".format(ogsfxFile), type='string')
    #cmds.addAttr(matInstance, shortName='customShader', niceName='customShader', longName='customShader', dt='string')
    #cmds.setAttr("{}.customShader".format(matInstance), '$data/shaders/vehicleShader2.xml', type='string')
    #
    I3DUtils.setAttributeValue(matInstance, "customParameterTemplate_{}_{}".format('brandColor', uiInstance._templateId), item['nicename'])
    print("Set: {}.shader to {}".format(matInstance,ogsfxFile))
    #
    # create shadingGroup
    #
    sgName = "{}_{}_s".format(I3DUtils.getNameFromFilePath(uiInstance._diffuse),item['nicename'])
    mStr = "Created: {}".format(sgName)
    sgInstance = cmds.sets(name=sgName,renderable=True,noSurfaceShader=True,empty=True)
    print("Created: {}".format(sgInstance))
    # connect material to shadingGroup
    cmds.connectAttr("{}.outColor".format(matInstance),"{}.surfaceShader".format(sgInstance),force=True)
    print("Connected: {}.outColor to {}.surfaceShader".format(matInstance,sgInstance))
    # create diffuse texture
    if uiInstance._diffuse:
        texDiffuseInstance = I3DUtils.createAndConnectTexture(matInstance,uiInstance._diffuse,"diffuseMap")
    # create normal texture
    if uiInstance._normal:
        texNormalInstance = I3DUtils.createAndConnectTexture(matInstance,uiInstance._normal,"normalMap")
    # create specular texture
    if uiInstance._specular:
        texSpecularInstance = I3DUtils.createAndConnectTexture(matInstance,uiInstance._specular,"specularMap")
    # detailDiffuse
    if item["detailDiffuse"]:
        texDetailDiffuseInstance = I3DUtils.createAndConnectTexture(matInstance,item["detailDiffuse"],"templateParameter_detailDiffuse")
        I3DMaterialTemplateWindow.setBoolAttr(matInstance,"templateParameter_enable_detailDiffuse",True)
    # detailNormal
    if item["detailNormal"]:
        texDetailNormalInstance = I3DUtils.createAndConnectTexture(matInstance,item["detailNormal"],"templateParameter_detailNormal")
        I3DMaterialTemplateWindow.setBoolAttr(matInstance,"templateParameter_enable_detailNormal",True)
    # detailSpecular
    if item["detailSpecular"]:
        texDetailSpecularInstance = I3DUtils.createAndConnectTexture(matInstance,item["detailSpecular"],"templateParameter_detailSpecular")
        I3DMaterialTemplateWindow.setBoolAttr(matInstance,"templateParameter_enable_detailSpecular",True)
    if item["colorScale"]:
        I3DMaterialTemplateWindow.setDouble3Attr(matInstance,"templateParameter_colorScale",item["colorScale"])
        I3DMaterialTemplateWindow.setBoolAttr(matInstance,"templateParameter_enable_colorScale",True)
    if item["smoothnessScale"]:
        I3DMaterialTemplateWindow.setFloatAttr(matInstance,"templateParameter_smoothnessScale",item["smoothnessScale"])
        I3DMaterialTemplateWindow.setBoolAttr(matInstance,"templateParameter_enable_smoothnessScale",True)
    if item["metalnessScale"]:
        I3DMaterialTemplateWindow.setFloatAttr(matInstance,"templateParameter_metalnessScale",item["metalnessScale"])
        I3DMaterialTemplateWindow.setBoolAttr(matInstance,"templateParameter_enable_metalnessScale",True)
    if item["clearCoatIntensity"]:
        I3DMaterialTemplateWindow.setFloatAttr(matInstance,"templateParameter_clearCoatIntensity",item["clearCoatIntensity"])
        I3DMaterialTemplateWindow.setBoolAttr(matInstance,"templateParameter_enable_clearCoatIntensity",True)
    if item["clearCoatSmoothness"]:
        I3DMaterialTemplateWindow.setFloatAttr(matInstance,"templateParameter_clearCoatSmoothness",item["clearCoatSmoothness"])
        I3DMaterialTemplateWindow.setBoolAttr(matInstance,"templateParameter_enable_clearCoatSmoothness",True)
    if item["porosity"]:
        I3DMaterialTemplateWindow.setFloatAttr(matInstance,"templateParameter_porosity",item["porosity"])
        I3DMaterialTemplateWindow.setBoolAttr(matInstance,"templateParameter_enable_porosity",True)
    cmds.select(clear=True)
    return matInstance,sgInstance

def uiCallbackMaterials(uiInstance, callbackData, callbackId,selectItemFullname):
    '''
    Main Callback Function
    '''
    item = uiInstance.getItemByFullname(selectItemFullname)
    #print(callbackId,selectItemFullname)
    #print(uiInstance._materialTemplates)
    #print(uiInstance._diffuse,uiInstance._normal,uiInstance._specular)
    #print(uiInstance._materialTemplatesXML)
    if item:
        if ('leftClick' == callbackId):
            # just print the info
            print("\n")
            for key, value in item.items():
                print('{:<22} : {}'.format(key,value))
        elif ('popupMenuCreate' == callbackId):
            matInstance,sgInstance = createVehicleMaterial(uiInstance,item)
            cmds.select(matInstance)
        elif ('popupMenuAssign' == callbackId):
            selection = cmds.ls(selection=True)
            matInstance,sgInstance = createVehicleMaterial(uiInstance,item)
            #print("Selected: {}".format(selection))
            cmds.select(selection)
            print("Assigned: {}".format(sgInstance))
            cmds.sets( edit=True, forceElement = sgInstance )
    else:
        print("item do not exists")

def main():
    '''
    Run this from your script
    '''
    # Load the plugin if not loaded
    if not cmds.pluginInfo('glslShader',query=True,loaded=True):
        cmds.loadPlugin('glslShader')
    # init UI with callbacks
    rightClickOptions = [
        {'label': 'Assign New Material', 'callbackId': 'popupMenuAssign'},
        {'label': 'Create New Material', 'callbackId': 'popupMenuCreate'}
    ]
    uiInstance = I3DMaterialTemplateWindow.materialTemplatesWin( 
        guiId='vehicleShaderMaterialTemplatesUI', 
        guiTitle='Vehicle Shader Material Templates',
        templateXmlFilename='$data/shared/detailLibrary/materialTemplates.xml',
        xmlElementName='template',
        callbackFunction=uiCallbackMaterials,
        rightClickOptions=rightClickOptions,
        defaultTexturesUI=True
    )

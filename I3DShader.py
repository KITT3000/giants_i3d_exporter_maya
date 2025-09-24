import maya.cmds as cmds
import I3DUtils
import I3DExporter


class I3DCustomShaderParameter:
    def __init__(self, name, attrName, defaultValue, uiGroup, isSeparateMaterialParameter, isTexture, parameterTemplateId=None, templateOptions=None):
        self.name = name
        self.attrName = attrName
        self.defaultValue = defaultValue
        self.uiGroup = uiGroup
        self.uiDropdown = None
        self.parameterTemplateId = parameterTemplateId
        self.isSeparateMaterialParameter = isSeparateMaterialParameter
        self.materialNode = None
        self.referenceMaterialNode = None
        self.isTexture = isTexture
        self.templateOptions = templateOptions

    def createUI(self, materialNode, uiParentLayout, referenceMaterialNode):
        self.materialNode = materialNode

        if not self.isSeparateMaterialParameter:
            self.referenceMaterialNode = referenceMaterialNode

        numberOfColumns = (self.parameterTemplateId is not None) and 4 or 3

        self.uiLayout = cmds.rowLayout('shaderSettingsParams{}'.format(self.name), parent=uiParentLayout, adjustableColumn=3, numberOfColumns=numberOfColumns)

        self.uiCheckbox = cmds.checkBox(label='', h=20, width=18, parent=self.uiLayout, value=self.isUnlocked(), changeCommand=self.checkboxCallback)
        self.uiLabel = cmds.text(label=self.name, align="left", h=20, width=170, parent=self.uiLayout)
        self.uiTextField = cmds.textField(text=self.defaultValue, h=20, parent=self.uiLayout)
        if self.parameterTemplateId is not None:
            self.uiTemplateSelect = cmds.optionMenu('giants_templatedParameterTemplateMenu_%s_%s' % (self.parameterTemplateId, self.name), parent=self.uiLayout, changeCommand=self.onTemplateSelected, width=180)

            cmds.menuItem(parent=self.uiTemplateSelect, label='None')
            for _, templateData in self.templateOptions.items():
                cmds.menuItem(parent=self.uiTemplateSelect, label=templateData["label"])

            selectedTemplate = None
            if materialNode is not None:
                selectedTemplate = I3DUtils.getAttributeValueAsStr(materialNode, 'customParameter_template_{}'.format(self.name), None)
            if selectedTemplate is not None:
                selectedTemplate = selectedTemplate.split(" ")[0]  # fix old assignments with description included
                if selectedTemplate in self.templateOptions:
                    templateData = self.templateOptions[selectedTemplate]
                    cmds.optionMenu(self.uiTemplateSelect, edit=True, value=templateData["label"])
        else:
            self.uiTemplateSelect = None

        self.checkboxCallback(self.isUnlocked())

        # TODO(jdellsperger): handle groups
        return True

    def deleteUI(self):
        if cmds.rowLayout(self.uiLayout, exists=True):
            cmds.deleteUI(self.uiLayout)
        self.materialNode = None
        self.referenceMaterialNode = None

    def isUnlocked(self):
        if self.materialNode is not None and I3DUtils.attributeExists(self.materialNode, self.attrName):
            if cmds.nodeType(self.materialNode) == 'GLSLShader':
                customParameterSet, _ = I3DUtils.getAttributeValueAndType(self.materialNode, 'customParameter_enable_{}'.format(self.name), False)
                return bool(customParameterSet)
            return True
        return False

    def hasCustomValue(self):
        return cmds.checkBox(self.uiCheckbox, query=True, value=True)

    def getCurrentValue(self):
        value = None

        # Try to load the value from a selected template.
        if self.uiTemplateSelect is not None:
            templateData = self.getSelectedTemplateData()
            if templateData is not None:
                value = templateData["value"]

        # If no vaue was loaded from a template, use the custom value.
        if value is None:
            value = I3DUtils.getAttributeValueAsStr(self.materialNode, self.attrName, None, self.isTexture)

        # If still no value was found, use the default one.
        if value is None:
            value = self.getDefaultValue()
        return value

    def apply(self, materialNode):
        attrExists = I3DUtils.attributeExists(materialNode, self.attrName)

        if cmds.nodeType(materialNode) == 'GLSLShader':
            # Check if the attribute has a custom value set. If yes, update the value stored
            # in the material node.
            if self.hasCustomValue():
                value = None

                # If a template is selected, load the value from there. Otherwise use the entered value.
                if self.uiTemplateSelect is not None:
                    templateData = self.getSelectedTemplateData()
                    if templateData is not None:
                        value = templateData["value"]
                        I3DUtils.setAttributeValue(materialNode, 'customParameter_template_{}'.format(self.name), templateData["templateName"])

                if value is None:
                    value = cmds.textField(self.uiTextField, query=True, text=True)

                I3DUtils.setAttributeValue(materialNode, self.attrName, value, self.isTexture)

                # Set the checkbox to indicate to the GLSL shader that it should use the custom
                # value.
                I3DUtils.setAttributeValue(materialNode, 'customParameter_enable_{}'.format(self.name), True)
            # If no custom value is set, the value is taken either from:
            # - a selected template
            # - the reference material
            # - or the default in the shader
            elif attrExists:
                categories = cmds.attributeQuery(self.attrName, node=materialNode, categories=True)
                if 'HW_shader_parameter' in categories:
                    # Indicate to the GLSL shader that it should not use a custom value.
                    I3DUtils.setAttributeValue(materialNode, 'customParameter_enable_{}'.format(self.name), False)

                    valueFound = False

                    # If this is a templated parameter, try to get a value from the template hierarchy.
                    if self.parameterTemplateId is not None:
                        templateValue = I3DExporter.I3DGetTemplateParameterValue(materialNode, self.parameterTemplateId, self.name)
                        if templateValue is not None:
                            I3DUtils.setAttributeValue(materialNode, 'templateParameter_enable_{}'.format(self.name), True)
                            I3DUtils.setAttributeValue(materialNode, 'templateParameter_{}'.format(self.name), templateValue, self.isTexture)
                            valueFound = True

                    # TODO(jdellsperger): handle reference material case

                    # If no value has been found in either a template or the reference material, then the default value of
                    # the shader should be used.
                    if not valueFound:
                        I3DUtils.setAttributeValue(materialNode, 'templateParameter_enable_{}'.format(self.name), False)
                else:
                    cmds.deleteAttr(materialNode, attribute=self.attrName)
        else:
            if self.hasCustomValue():
                value = None

                # If a custom value is set, store it as extra attribute of the material node
                # If a template is selected, store the value from there. Otherwise use the entered value.
                if self.uiTemplateSelect is not None:
                    templateData = self.getSelectedTemplateData()
                    if templateData is not None:
                        value = templateData["value"]
                        I3DUtils.setAttributeValue(materialNode, 'customParameter_template_{}'.format(self.name), templateData["templateName"])

                if value is None:
                    value = cmds.textField(self.uiTextField, query=True, text=True)

                I3DUtils.setAttributeValue(materialNode, self.attrName, value, self.isTexture)
            elif attrExists:
                # If no custom value is set but the attribute exists, remove the attribute
                cmds.deleteAttr(materialNode, attribute=self.attrName)

    def getDefaultValue(self):
        value = None

        # If this is a templated parameter, try to get a value from the template hierarchy.
        if self.parameterTemplateId is not None:
            templateValue = I3DExporter.I3DGetTemplateParameterValue(self.materialNode, self.parameterTemplateId, self.name)
            if templateValue is not None:
                value = templateValue

        # If no value has been found and a reference material is defined,
        # try to get the value from there.
        if self.referenceMaterialNode is not None and value is None:
            value = I3DUtils.getAttributeValueAsStr(self.referenceMaterialNode, self.name, None, self.isTexture)

            if value is None and self.parameterTemplateId is not None:
                templateValue = I3DExporter.I3DGetTemplateParameterValue(self.referenceMaterialNode, self.parameterTemplateId, self.name, getStored=True)
                if templateValue is not None:
                    value = templateValue

        # If still no value is found use the default one defined in the shader.
        if value is None:
            value = self.defaultValue

        return value

    # Sets the value of the textfield without updating the custom parameter saved in the material node
    def setUIValue(self, value):
        cmds.textField(self.uiTextField, edit=True, text=value)

    def setCustomValue(self, customValue=None):
        hasCustomValue = customValue is not None
        cmds.checkBox(self.uiCheckbox, edit=True, value=hasCustomValue)
        if hasCustomValue:
            self.setUIValue(customValue)

    def checkboxCallback(self, checked):
        cmds.textField(self.uiTextField, edit=True, enable=checked)
        if self.uiTemplateSelect is not None:
            cmds.optionMenu(self.uiTemplateSelect, edit=True, enable=checked)

        if not checked:
            self.setUIValue(self.getDefaultValue())

            if self.uiTemplateSelect is not None:
                cmds.optionMenu(self.uiTemplateSelect, edit=True, sl=1)
        else:
            self.setUIValue(self.getCurrentValue())

    def getSelectedTemplateData(self):
        selectedTemplateLabel = cmds.optionMenu(self.uiTemplateSelect, query=True, value=True)
        if selectedTemplateLabel != 'None':
            for _, templateData in self.templateOptions.items():
                if selectedTemplateLabel == templateData["label"]:
                    return templateData

    def onTemplateSelected(self, selectedTemplateLabel):
        for _, templateData in self.templateOptions.items():
            if selectedTemplateLabel == templateData["label"]:
                value = templateData["value"]
                cmds.textField(self.uiTextField, edit=True, text=value)
                break

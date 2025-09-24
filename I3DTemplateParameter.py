import maya.cmds as cmds
import xml.etree.ElementTree as ET
import I3DMaterialTemplateWindow

try:
    reload(I3DMaterialTemplateWindow)
except NameError:
    from importlib import reload
    reload(I3DMaterialTemplateWindow)

class I3DTemplateParameterFile:
    def __init__(self, xmlFileName, templateParameters):
        try:
            tree = ET.parse(xmlFileName)
        except ET.ParseError as err:
            cmds.warning("Failed to load parameter templates from '%s': %s" % (xmlFileName, err))
            self._isValid = False

        templateParameters.append('parentTemplate')
        templateParameters.append('description')

        root = tree.getroot()
        self._id = root.get('id')
        self._name = root.get('name')
        self._xmlFileName = xmlFileName
        self._parentTemplateFile = root.get('parentTemplateFilename')
        self._defaultParentTemplate = root.get('parentTemplateDefault')
        self._templates = {template.get('name'): {templateParameter: template.get(templateParameter) for templateParameter in templateParameters} for template in root.findall('template')}
        self._isValid = True


class I3DTemplateParameterSubTemplate:
    def __init__(self, templateParameterId, templateFile, parentLayout, templateSelectedCallback, parentSubTemplateId, defaultParentTemplate, templates):
        #TODO error checking parameterFile._isValid

        self._templateParameterId = templateParameterId # The ID of the template parameter this sub-template is a part of
        self._id = templateFile._id
        self._parentSubTemplateId = parentSubTemplateId
        self._templates = templates
        self._templateSelectedCallback = templateSelectedCallback
        self._xmlFileName = templateFile._xmlFileName
        self._defaultParentTemplate = defaultParentTemplate

        self._layout = cmds.formLayout('giants_templatedParameterMenuLayout_%s_%s' % (templateParameterId, templateFile._id), parent=parentLayout)
        self._menuLabel = cmds.text(label=templateFile._name, h=20, parent=self._layout)
        self._menu = cmds.optionMenu('giants_templatedParameterMenu_%s_%s' % (templateParameterId, templateFile._id), parent=self._layout, changeCommand=templateSelectedCallback, enable=False)
        self._checkbox = cmds.checkBox(label="", h=20, parent=self._layout, changeCommand=self.checkboxChangeCallback)
        self._openMaterialSelectionWindowButton = cmds.button(parent=self._layout, label='...', annotation='Open Material Template Dialog', h=19, command=self.openMaterialTemplateWindow)

        self._templateToLabel = {}

        cmds.menuItem(parent=self._menu, label='')
        for template, templateData in templateFile._templates.items():
            label = template
            if "description" in templateData and templateData["description"] is not None and templateData["description"] != "":
                label = label + " (%s)" % templateData["description"]

            self._templateToLabel[template] = label
            cmds.menuItem(parent=self._menu, label=label)

        cmds.formLayout(self._layout, edit=True, attachForm=((self._menuLabel, 'left', 20), (self._menu, 'left', 190), (self._menu, 'right', 20), (self._openMaterialSelectionWindowButton, 'right', 0)))

    def checkboxChangeCallback(self, checked):
        cmds.optionMenu(self._menu, edit=True, enable=checked)

        if not checked:
            cmds.optionMenu(self._menu, edit=True, value='')

        self._templateSelectedCallback(None)

    def setActive(self, active):
        cmds.checkBox(self._checkbox, e=True, v=active)

        cmds.optionMenu(self._menu, edit=True, enable=active)

        if not active:
            cmds.optionMenu(self._menu, edit=True, value='')

    def selectTemplate(self, templateName):
        if templateName in self._templateToLabel:
            label = self._templateToLabel[templateName]
            cmds.optionMenu(self._menu, edit=True, value=label)

    def getSelectedTemplate(self):
        label = cmds.optionMenu(self._menu, q=True, value=True)
        for templateName, _label in self._templateToLabel.items():
            if label == _label:
                return templateName

    def openMaterialTemplateWindow(self, unused):
        rightClickOptions = [
            #{'label': 'Assign New Material', 'callbackId': 'popupMenuAssign'},
            #{'label': 'Create New Material', 'callbackId': 'popupMenuCreate'}
        ]
        I3DMaterialTemplateWindow.materialTemplatesWin(
            guiId='i3dToolBox_vehicleShaderMaterialTemplatesUI',
            guiTitle='Vehicle Shader Material Templates',
            templateXmlFilename=self._xmlFileName,
            xmlElementName='template',
            callbackFunction=self.materialTemplateSelectionCallback,
            rightClickOptions=rightClickOptions,
            defaultTexturesUI=False
        )

    def materialTemplateSelectionCallback(self, uiInstance, callbackData, callbackId, selectItemFullname):
        item = uiInstance.getItemByFullname(selectItemFullname)
        self.selectTemplate(item['nicename'])
        self._templateSelectedCallback(None)
        cmds.deleteUI('i3dToolBox_vehicleShaderMaterialTemplatesUI')

    def getAttributeName(self):
        return ('customParameterTemplate_%s_%s' % (self._templateParameterId, self._id))

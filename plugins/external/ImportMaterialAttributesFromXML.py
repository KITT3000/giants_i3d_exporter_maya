import maya.cmds as cmds
import xml.etree.ElementTree as xml_ET
import I3DUtils

UI_WIDTH = 800
UI_HEIGHT = 600

class ImportMaterialAttributesFromXML():
    def __init__(self, guiId, guiTitle, callbackFunction):
        self._guiId = guiId
        self._guiTitle = guiTitle
        self._callbackFunction = callbackFunction

        self.__uiCreate()

    def __uiCreate(self):
        if cmds.window(self._guiId, exists=True):
            cmds.deleteUI(self._guiId)
        uiWindow = cmds.window(self._guiId, title=self._guiTitle, widthHeight=(UI_WIDTH, UI_HEIGHT), sizeable=True)
        formLayout = cmds.formLayout('I3D_importMaterialAttributesFromXMLFormLayout', parent=uiWindow)
        self._xmlTxt = cmds.scrollField('I3D_importMaterialAttributesFromXMLText', parent=formLayout, w=500, h=500)
        okBtn = cmds.button('I3D_importMaterialAttributesFromXMLOKBtn', parent=formLayout, label="OK", height=25, command=self.apply, annotation="Parse the provided XML and set the attributes accordingly.")
        cancelBtn = cmds.button('I3D_importMaterialAttributesFromXMLCancelBtn', parent=formLayout, label="Cancel", height=25, command=self.cancel, annotation="Close the window without applying the attributes.")
        cmds.formLayout(formLayout, edit=True, attachForm=[(self._xmlTxt, 'top', 5), (self._xmlTxt, 'left', 5), (self._xmlTxt, 'right', 5), (self._xmlTxt, 'bottom', 35)])
        cmds.formLayout(formLayout, edit=True, attachPosition=[(okBtn, 'bottom', 5, 100), (okBtn, 'left', 5, 0), (okBtn, 'right', 5, 50),
                                                               (cancelBtn, 'bottom', 5, 100), (cancelBtn, 'left', 5, 50), (cancelBtn, 'right', 5, 100)])
        cmds.showWindow(uiWindow)

    def apply(self, unused):
        xml = cmds.scrollField(self._xmlTxt, text=True, query=True)
        parseSuccessful = True
        try:
            root = xml_ET.fromstring(xml)
        except xml_ET.ParseError as e:
            cmds.warning("Could not parse XML:")
            cmds.warning(e.msg)
            parseSuccessful = False

        if parseSuccessful:
            matName = root.get('name')
            customParams = root.findall('CustomParameter')
            customParameters = {}
            for param in customParams:
                paramName = param.get('name')
                paramVal = param.get('value')
                customParameters[paramName] = paramVal
            callbackData = {'matName': matName, 'customParameters': customParameters}
            parseSuccessful = self._callbackFunction(callbackData)

        if parseSuccessful:
            cmds.deleteUI(self._guiId)

    def cancel(self, unused):
        cmds.deleteUI(self._guiId)

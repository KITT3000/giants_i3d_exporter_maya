#
#   SCRIPT     I3DMaterialTemplateWindow.py
#   AUTHORS    Stefan Geiger , Evgen Zaitsev
#
'''
import sys
import maya.cmds as cmds
path = 'd:/code/lsim2025/tools/exporter/maya/'
if path not in sys.path:
    sys.path.append(path)
import I3DMaterialTemplateWindow
try:
    reload(I3DMaterialTemplateWindow)
except NameError:
    from importlib import reload
    reload(I3DMaterialTemplateWindow)

def uiCallbackMaterials(uiInstance, callbackData, callbackId,selectItemFullname):
    print('Materials code')
    #print(uiInstance.getItemByFullname(selectItemFullname))
    print(uiInstance, callbackData, callbackId,selectItemFullname)

def uiCallbackColors(uiInstance, callbackData, callbackId,selectItemFullname):
    print('Brand Colors code')
    print(uiInstance, callbackData, callbackId,selectItemFullname)

rightClickOptions = [
    {'label': 'Assign New Material', 'callbackId': 'popupMenuAssign'},
    {'label': 'Create New Material', 'callbackId': 'popupMenuCreate'}
]
I3DMaterialTemplateWindow.materialTemplatesWin(
    guiId='vehicleShaderMaterialTemplatesUI',
    guiTitle='Vehicle Shader Material Templates',
    templateXmlFilename='data/shared/detailLibrary/materialTemplates.xml',
    xmlElementName='template',
    callbackFunction=uiCallbackMaterials,
    rightClickOptions=rightClickOptions,
    defaultTexturesUI=True
)
I3DMaterialTemplateWindow.materialTemplatesWin(
    guiId='brandColorsUI',
    guiTitle='Brand Colors',
    templateXmlFilename='data/shared/brandColors.xml',
    xmlElementName='color',
    callbackFunction=uiCallbackColors,
    rightClickOptions=[],
)
'''
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import xml.etree.ElementTree as xml_ET
import os
import I3DExporter

CURRENT_PY_FILE = __file__
CURRENT_DIR = os.path.dirname(os.path.abspath(CURRENT_PY_FILE))
DEFAULT_PNG = '{}/mat_default.png'.format(CURRENT_DIR)
UI_WIDTH = 800
UI_HEIGHT = 600

class materialTemplatesWin():
    """
    Main UI window class definition
    """
    def __init__(self, guiId, guiTitle, templateXmlFilename, xmlElementName, callbackFunction, callbackData=None, rightClickOptions=[], defaultTexturesUI=False ):
        """
        Initialize window
        """
        self._guiId = guiId
        self._guiTitle = guiTitle
        self._callbackFunction = callbackFunction
        self._callbackData = callbackData
        self._rightClickOptions = rightClickOptions
        self._templateXmlFilename = templateXmlFilename
        self._xmlElementName = xmlElementName
        self._defaultTexturesUI = defaultTexturesUI

        self._gamePath = I3DExporter.I3DGetGamePath().replace('\\', '/')
        # Jeśli ścieżka zaczyna się od $, podmień na pełną. Jeśli nie, a jest relatywna, dodaj folder gry.
        temp_xml = templateXmlFilename
        if temp_xml.startswith('$'):
            self._materialTemplatesXML = temp_xml.replace('$', self._gamePath + '/')
        elif not ":" in temp_xml: # jeśli nie ma litery dysku, dodaj gamePath
            self._materialTemplatesXML = (self._gamePath.rstrip('/') + '/' + temp_xml.lstrip('/')).replace('//', '/')
        else:
            self._materialTemplatesXML = temp_xml
        
        self._materialTemplatesXML = self._materialTemplatesXML.replace('\\', '/')
        self._diffuse,self._normal,self._specular = self.__getDefaultTextures()
        self._ui_diffuseState = False # is _diffuse already changed by user or not

        #print("Current Python File: {}".format(CURRENT_PY_FILE))
        print("Game Path: {}".format(self._gamePath))
        print("XML: {}".format(self._materialTemplatesXML))

        self._ui_btnSize = 128 # size of the materialTemplate button
        self._ui_btnColumns = 2  # amount of columns of the buttons inside _ui_gridLayout
        self._ui_btnList = [] # list of dynamically created buttons
        self._ui_btnPopupsList = [] # list of dynamically created popup ui's attached to the buttons
        self._materialTemplates = [] # list with templates
        self._materialCategories = categoryTree() # instance of the class to handle material categories
        self._selectedCategory = None # currently selected category
        self.__uiCreate()

    def __uiCreate(self):
        if cmds.window(self._guiId, exists=True):
            cmds.deleteUI(self._guiId)
        self._ui_window = cmds.window(self._guiId, title=self._guiTitle, widthHeight=(UI_WIDTH, UI_HEIGHT), sizeable=True)
        self._ui_formLayout = cmds.formLayout(parent=self._ui_window )
        self._ui_xmlTxt = cmds.textField(parent=self._ui_formLayout, w=500, editable=False )
        self._ui_xmlBtnRefresh = cmds.symbolButton(parent=self._ui_formLayout,image="refresh.xpm",w=25,
            command=lambda *args:self.__uiCallback("_ui_xmlBtnRefresh_pressed",args) )
        self._ui_xmlBtn = cmds.symbolButton(parent=self._ui_formLayout,image="navButtonBrowse.xpm",w=25,
            command=lambda *args:self.__uiCallback("_ui_xmlBtn_pressed",args) )
        # Some extra UI which is needed for materials
        self._ui_extraColumn = cmds.columnLayout( parent=self._ui_formLayout,adjustableColumn=True,visible=True)
        # check if extra UI is needed
        if self._defaultTexturesUI:
            self._ui_diffuse_rowLayout = cmds.rowLayout(parent=self._ui_extraColumn,numberOfColumns=3,adjustableColumn=2)
            self._ui_diffuse_text = cmds.text(parent=self._ui_diffuse_rowLayout, label='diffuse',w=50,align="right" )
            self._ui_diffuse_textField = cmds.textField(parent=self._ui_diffuse_rowLayout,h=20,w=600,visible=True,editable=False)
            self._ui_diffuseBtn = cmds.symbolButton(parent=self._ui_diffuse_rowLayout,image="navButtonBrowse.xpm",w=25,
                command=lambda *args:self.__uiCallback("_ui_diffuseBtn_pressed",args))
            self._ui_normal_rowLayout = cmds.rowLayout(parent=self._ui_extraColumn,numberOfColumns=3,adjustableColumn=2)
            self._ui_normal_text = cmds.text(parent=self._ui_normal_rowLayout, label='normal',w=50,align="right" )
            self._ui_normal_textField = cmds.textField(parent=self._ui_normal_rowLayout,h=20,w=600,visible=True,editable=False)
            self._ui_normalBtn = cmds.symbolButton(parent=self._ui_normal_rowLayout,image="navButtonBrowse.xpm",w=25,
                command=lambda *args:self.__uiCallback("_ui_normalBtn_pressed",args))
            self._ui_specular_rowLayout = cmds.rowLayout(parent=self._ui_extraColumn,numberOfColumns=3,adjustableColumn=2)
            self._ui_specular_text = cmds.text(parent=self._ui_specular_rowLayout, label='specular',w=50,align="right" )
            self._ui_specular_textField = cmds.textField(parent=self._ui_specular_rowLayout,h=20,w=600,visible=True,editable=False)
            self._ui_specularBtn = cmds.symbolButton(parent=self._ui_specular_rowLayout,image="navButtonBrowse.xpm",w=25,
                command=lambda *args:self.__uiCallback("_ui_specularBtn_pressed",args))
        #
        self._ui_matScrollList = cmds.textScrollList(parent=self._ui_formLayout,numberOfRows=40,w=200,allowMultiSelection=False,
            selectCommand=lambda *args:self.__uiCallback("_ui_matScrollList_pressed",args))
        self._ui_btnSizeSlider = cmds.intSlider(parent=self._ui_formLayout, min=0, max=3, value=1, step=1,
            dragCommand=lambda *args:self.__uiCallback("_ui_btnSizeSlider_dragged",args))
        self._ui_scrollLayout = cmds.scrollLayout(parent=self._ui_formLayout,childResizable=True,horizontalScrollBarThickness=16,verticalScrollBarThickness=16,
            resizeCommand=lambda *args:self.__uiCallback("_ui_scrollLayout_resized",args))
        self._ui_gridLayout = cmds.gridLayout(parent=self._ui_scrollLayout,cellWidthHeight=(self._ui_btnSize,self._ui_btnSize), allowEmptyCells=False )
        cmds.formLayout(self._ui_formLayout, edit = True,
            attachForm =    [
                             ( self._ui_xmlTxt, 'top', 4 ),
                             ( self._ui_xmlTxt, 'left', 4 ),
                             ( self._ui_xmlBtnRefresh, 'top', 4 ),
                             ( self._ui_xmlBtn, 'top', 4 ),
                             ( self._ui_xmlBtn, 'right', 4 ),
                             ( self._ui_extraColumn, 'left', 4 ),
                             ( self._ui_extraColumn, 'right', 4 ),
                             ( self._ui_matScrollList, 'left', 4 ),
                             ( self._ui_matScrollList, 'bottom', 4 ),
                             ( self._ui_btnSizeSlider, 'right', 4 ),
                             ( self._ui_scrollLayout, 'right', 4 ),
                             ( self._ui_scrollLayout, 'bottom', 4 ),
                            ],
            attachControl = [
                             ( self._ui_xmlBtnRefresh, 'right', 4, self._ui_xmlBtn ),
                             ( self._ui_xmlTxt, 'right', 4, self._ui_xmlBtnRefresh ),
                             ( self._ui_extraColumn, 'top', 4, self._ui_xmlTxt ),
                             ( self._ui_matScrollList, 'top', 4, self._ui_extraColumn ),
                             ( self._ui_btnSizeSlider, 'top', 4, self._ui_extraColumn ),
                             ( self._ui_btnSizeSlider, 'left', 4, self._ui_matScrollList ),
                             ( self._ui_scrollLayout, 'left', 4, self._ui_matScrollList ),
                             ( self._ui_scrollLayout, 'top', 4, self._ui_btnSizeSlider ),
                            ],
            attachNone =    [
                             ( self._ui_xmlTxt, 'bottom' ),
                             ( self._ui_xmlBtnRefresh, 'left' ),
                             ( self._ui_xmlBtnRefresh, 'bottom' ),
                             ( self._ui_xmlBtn, 'left' ),
                             ( self._ui_xmlBtn, 'bottom' ),
                             ( self._ui_extraColumn, 'bottom' ),
                             ( self._ui_btnSizeSlider, 'bottom' ),
                             ( self._ui_matScrollList, 'right' ),
                            ])
        cmds.showWindow(self._ui_window)
        self.__loadXML()
        self.__uiRefresh('_ui_matScrollList_refresh')

    def __loadXML(self):
        if (not os.path.exists(self._materialTemplatesXML)):
            self._materialTemplatesXML = ""

            cmds.confirmDialog(title="I3DExporter - Error", message="Material Templates XML file not found. Set up game directory first.", icon="critical", dismissString="Ok")
        else:
            # clear the categoryTree
            # in case we loaded updated/different xml
            self._materialCategories.clearTree()
            #
            self._materialTemplates = loadXML(self._materialTemplatesXML,self._xmlElementName,self._gamePath)

            mTree = xml_ET.parse(self._materialTemplatesXML)
            mRoot = mTree.getroot()
            self._templateId = mRoot.get('id')

            for item in self._materialTemplates:
                # populate category tree
                # this class handles internal structure, sorting, duplicates etc
                self._materialCategories.populateTree(item["category"])

    def __fileDialog(self,mFilePath):
        mDir = os.path.dirname(mFilePath)
        if ("" == mFilePath):
            mDir = self._gamePath
        mResult = cmds.fileDialog2( fm=1,rf=True, startingDirectory = mDir )
        if ( mResult ):
            mResult = mResult[0]
            return mResult
        return None

    def __fileDialog2(self,filePath):
        mFilePath = cmds.file(q=True,sn=True) # maya file path
        if "" == mFilePath:
            mFilePath = filePath
        return self.__fileDialog(mFilePath)

    def __uiCallback(self, *args):
        """
        Callback for UI
        """
        #print(args)
        if (len(args)>0):
            m_input = args[0]
            if ('_ui_diffuseBtn_pressed'==m_input):
                mResult = self.__fileDialog2(self._diffuse)
                if ( mResult ):
                    self._diffuse = mResult
                    self.__uiRefresh()
            if ('_ui_normalBtn_pressed'==m_input):
                mResult = self.__fileDialog2(self._normal)
                if ( mResult ):
                    self._normal = mResult
                    self.__uiRefresh()
            if ('_ui_specularBtn_pressed'==m_input):
                mResult = self.__fileDialog2(self._specular)
                if ( mResult ):
                    self._specular = mResult
                    self.__uiRefresh()
            if ('_ui_xmlBtn_pressed'==m_input):
                mResult = self.__fileDialog(self._materialTemplatesXML)
                if ( mResult ):
                    self._materialTemplatesXML = str( mResult )
                    # update gamePath in case user selected different materialTemplates.xml from different folder
                    self._gamePath = mResult.split("/data/")[0]
                    I3DExporter.I3DSetGamePath(self._gamePath)
                    print("Game Path: {}".format(self._gamePath))
                    print("XML: {}".format(self._materialTemplatesXML))
                    #
                    self.__loadXML()
                    # update the list based on processed data from xml
                    self._selectedCategory = None
                    self.__uiRefresh('_ui_matScrollList_refresh')
            if ('_ui_xmlBtnRefresh_pressed'==m_input):
                self.__loadXML()
                self._selectedCategory = None
                self.__uiRefresh('_ui_matScrollList_refresh')
            if ('_ui_matScrollList_pressed'==m_input):
                # we keep fullname in the tag filed of the scrolllist item, which is hidden and nicename is displaed instead
                mSelectedCategory = cmds.textScrollList( self._ui_matScrollList, query=True, selectUniqueTagItem=True)
                # Maya returns a list (multiselection support)
                # update currently selected category
                #
                if mSelectedCategory:
                    self._selectedCategory = mSelectedCategory[0]
                else:
                    self._selectedCategory = None
                # remove old and create new buttons
                # based on currently selected category
                self.__uiRefresh('_ui_gridLayout_refresh')
                #
            if ('_ui_btnSizeSlider_dragged'==m_input):
                mSizes = [64,128,256,512]
                mIndex = cmds.intSlider(self._ui_btnSizeSlider,query=True,value=True)
                if (mIndex<0 or mIndex>3):
                    mIndex = 1
                self._ui_btnSize = mSizes[mIndex]
                self.__uiCallback('_ui_scrollLayout_resized')
            # resize the window
            # recalculate buttons in the _ui_gridLayout
            if ('_ui_scrollLayout_resized'==m_input):
                #print(self._ui_btnSize)
                mWidth = cmds.scrollLayout(self._ui_scrollLayout,query=True,width=True)
                mHeight = cmds.scrollLayout(self._ui_scrollLayout,query=True,height=True)
                numberOfColumns = int(float(mWidth)/float(self._ui_btnSize))
                if (numberOfColumns<1):
                    numberOfColumns = 1
                self._ui_btnColumns = numberOfColumns
                # remove old and create new buttons
                self.__uiRefresh('_ui_gridLayout_refresh')

    def __uiRefresh(self, *args):
        """
        Refresh existing UI and generate new if necessary
        """
        # print(args)
        # Update part of UI without commands
        cmds.textField(self._ui_xmlTxt,edit=True,text=self._materialTemplatesXML)
        # Update extra UI
        if self._defaultTexturesUI:
            cmds.textField(self._ui_diffuse_textField,edit=True,text=self._diffuse)
            cmds.textField(self._ui_normal_textField,edit=True,text=self._normal)
            cmds.textField(self._ui_specular_textField,edit=True,text=self._specular )
        #
        if (len(args)>0):
            m_input = args[0]
            if ('_ui_matScrollList_refresh'==m_input):
                # update the list based on processed data from xml
                cmds.textScrollList(self._ui_matScrollList,edit=True,removeAll=True)
                #print(self._materialCategories)
                #print(self._materialTemplates)
                for item in self._materialCategories.categoryNames:
                    # store fullname in uniqueTag of the textScrollList
                    cmds.textScrollList(self._ui_matScrollList,edit=True,append=[item["nicename"]],uniqueTag=[item["fullname"]])
                # remove old and create new buttons
                self.__uiRefresh('_ui_gridLayout_refresh')
            if ('_ui_gridLayout_refresh'==m_input):
                """
                Dynamically generated UI
                """
                # remove existing popups and buttons
                for mUI in self._ui_btnPopupsList:
                    cmds.deleteUI(mUI)
                for mUI in self._ui_btnList:
                    cmds.deleteUI(mUI)
                # adjust columns of the _ui_gridLayout
                # and cellWidthHeight
                cmds.gridLayout(self._ui_gridLayout,edit=True,numberOfColumns=self._ui_btnColumns)
                cmds.gridLayout(self._ui_gridLayout,edit=True,cellWidthHeight=(self._ui_btnSize,self._ui_btnSize))
                #
                self._ui_btnList = []
                self._ui_btnPopupsList = []
                # generate buttons
                if (self._selectedCategory):
                    materialTemplatesSelected = self.__getMaterialTemplatesSelected()
                    #print(self._selectedCategory)
                    #print(materialTemplatesSelected)
                    for item in materialTemplatesSelected:
                        # create buttons
                        tmpColor = getRGBfromString(item["colorScale"])
                        tmpLabel = "{}\n{}".format(item["nicename"],tmpColor)
                        if item["iconFilename"] == "":
                            tmpButton = cmds.button(parent=self._ui_gridLayout,w=self._ui_btnSize,h=self._ui_btnSize,
                                annotation=self.__getItemAnnotation(item),label=tmpLabel,backgroundColor=tmpColor,
                                command=makeCallbackFunction(self,self._callbackData,'leftClick',item["fullname"])
                            )
                        else:
                            tmpButton = cmds.iconTextButton(parent=self._ui_gridLayout,w=self._ui_btnSize,h=self._ui_btnSize,
                                image1=item["iconFilename"],annotation=self.__getItemAnnotation(item),label=tmpLabel,style="iconAndTextCentered",scaleIcon=True,
                                command=makeCallbackFunction(self,self._callbackData,'leftClick',item["fullname"])
                            )
                        # append it to the Buttons list, will be used later
                        self._ui_btnList.append(tmpButton)
                        # create popups if they are exists
                        if len(self._rightClickOptions) > 0:
                            # create popups
                            tmpPopupList = cmds.popupMenu( parent=tmpButton )
                            # append it to the Popups list, will be used later
                            self._ui_btnPopupsList.append( tmpPopupList )
                            #
                            for option in self._rightClickOptions:
                                cmds.menuItem( parent=tmpPopupList, label=option['label'],
                                    command=makeCallbackFunction(self,self._callbackData,option['callbackId'],item["fullname"]))

    def __getItemAnnotation(self,item):
        m_str = ""
        for key, value in item.items():
            m_str += '{}: {} \n'.format(key,value)
        return m_str

    def __getDefaultTextures(self):
        gPath = self._gamePath if self._gamePath else ""
        defaultDiffuse  = (gPath.rstrip('/') + "/data/shared/white_diffuse.png").replace('//', '/')
        defaultNormal   = (gPath.rstrip('/') + "/data/shared/default_normal.png").replace('//', '/')
        defaultSpecular = (gPath.rstrip('/') + "/data/shared/default_vmask.png").replace('//', '/')

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

    def __getMaterialTemplatesSelected(self):
        result = []
        if (self._selectedCategory):
            for item in self._materialTemplates:
                if (0 == item["category"].find(self._selectedCategory)):
                    result.append(item)
        # list of dicts sorted by 'fullname'
        result = sorted(result, key=lambda item: item['fullname'])
        return result

    def getItemByFullname(self,fullname):
        for item in self._materialTemplates:
            if (fullname==item['fullname']):
                return item
        return None

def getRGBfromString(m_str):
    if m_str:
        m_list = m_str.split(" ")
        return (float(m_list[0]),float(m_list[1]),float(m_list[2]))
    else:
        return (1.0,1.0,1.0)

def makeCallbackFunction(owner, callbackData, callbackId,itemFullname):
    '''
    Dynamic callback Function
    '''
    return lambda *args:owner._callbackFunction(owner, callbackData, callbackId,itemFullname)

def getImgFilePath(gamePath,relativeFilePath,type="noticon"):
    if relativeFilePath == None or relativeFilePath == "":
        return ""
    m_str = relativeFilePath
    if (0 == relativeFilePath.find("$data")):
        # just remove $ char
        m_str = relativeFilePath[1:]
    m_str = os.path.abspath("{}/{}".format(gamePath,m_str))
    if (not os.path.exists(m_str)):
        if "icon" == type:
            return DEFAULT_PNG
        else:
            ddsFile = m_str.replace(".png", ".dds")
            if os.path.exists(ddsFile):
                return ddsFile

    return m_str

def setDouble3Attr(matInstance,attrName,value):
    r,g,b = getRGBfromString(value)
    cmds.setAttr("{}.{}".format(matInstance,attrName), r, g, b, type="double3")
    print("Set: {}.{} to {},{},{}".format(matInstance,attrName,r,g,b))

def setBoolAttr(matInstance,attrName,value):
    cmds.setAttr("{}.{}".format(matInstance,attrName), value)
    print("Set: {}.{} to {}".format(matInstance,attrName,value))

def setFloatAttr(matInstance,attrName,value):
    cmds.setAttr("{}.{}".format(matInstance,attrName),float(value))
    print("Set: {}.{} to {}".format(matInstance,attrName,value))

def loadXML(xmlPath,xmlElementName,gamePath):
    '''
    Return list of material parameters from XML file
    brandColors.xml and materialTemplates.xml contain material parameters
    '''
    mTree = xml_ET.parse(xmlPath)
    mRoot = mTree.getroot()
    result = []
    for mTemplate in mRoot.findall(xmlElementName):
        item = {}
        #
        item["nicename"]       = mTemplate.get('name')
        item["category"]       = mTemplate.get('category')
        #
        if item["category"] is None or item["category"] == "":
            item["category"] = item["nicename"].split('_')[0]
        item["fullname"]       = "{}/{}".format(item["category"],item["nicename"])
        #
        item["iconFilename"]   = getImgFilePath( gamePath=gamePath, relativeFilePath=mTemplate.get('iconFilename'), type="icon" )
        item["detailDiffuse"]  = getImgFilePath( gamePath=gamePath, relativeFilePath=mTemplate.get('detailDiffuse') )
        item["detailNormal"]   = getImgFilePath( gamePath=gamePath, relativeFilePath=mTemplate.get('detailNormal') )
        item["detailSpecular"] = getImgFilePath( gamePath=gamePath, relativeFilePath=mTemplate.get('detailSpecular') )
        item["colorScale"]            = mTemplate.get('colorScale')
        item["smoothnessScale"]       = mTemplate.get('smoothnessScale') or 1
        item["metalnessScale"]        = mTemplate.get('metalnessScale') or 1
        item["clearCoatIntensity"]    = mTemplate.get('clearCoatIntensity') or 0
        item["clearCoatSmoothness"]   = mTemplate.get('clearCoatSmoothness') or 0
        item["porosity"]              = mTemplate.get('porosity') or 0
        item["parentTemplate"]        = mTemplate.get('parentTemplate')
        item["parentTemplateDefault"] = mRoot.get('parentTemplateDefault')
        result.append(item)
    return result

class categoryTree():
    """
    Class to handle material categories described as strings like  "metallic/clear"
        items=['nonMetallic/test/test/bla',
               'metallic/clear/chrome',
               'metallic/scratched/silverScratched',
               'nonMetallic/rubber/rubber',
               'nonMetallic/wood/wood1',
               'metallic/scratched/brassScratched',
               'nonMetallic/wood/wood1']
        ct = categoryTree()
        ct.populateTree(items)
        ct.populateTree('metallic/scratched/silver')
        print(ct)
    """
    def __init__(self, items=[]):
        self.tree = {}
        self.populateTree(items)

    def __populateItem(self,path):
        parts = path.split("/")
        current_node = self.tree
        for part in parts:
            if part not in current_node:
                current_node[part] = {}
            current_node = current_node[part]

    def populateTree(self,items=[]):
        if (isinstance(items, str)):
            self.__populateItem(items)
        if isinstance(items, list):
            for path in items:
                self.__populateItem(path)

    def clearTree(self):
        self.tree = {}

    def __str__(self):
        cats = sorted(set(self.__getMembers(self.tree)))
        result = ''
        for cat in cats:
            parts = cat.split("/")
            fullname = cat
            depth = (len(parts)-1)
            nicename = "    "*depth + parts[-1]
            result += "{} {}\n".format(depth,nicename)
        return result

    def __getPaths(self,node,prefix=""):
        paths = []
        for key, value in node.items():
            new_prefix = prefix + "/" + key if prefix else key
            if value:
                paths.extend(self.__getPaths(value, new_prefix))
            else:
                paths.append(new_prefix)
        return paths

    def __getMembers(self,node,prefix=""):
        members = []
        for key, value in node.items():
            new_prefix = prefix + "/" + key if prefix else key
            members.append(new_prefix)
            if value:
                sub_members = self.__getMembers(value, new_prefix)
                members.extend(sub_members)
        return members

    @property
    def paths(self):
        return sorted(set(self.__getPaths(self.tree)))

    @property
    def categories(self):
        return sorted(set(self.__getMembers(self.tree)))

    @property
    def categoryNames(self):
        cats = sorted(set(self.__getMembers(self.tree)))
        result = []
        for cat in cats:
            parts = cat.split("/")
            item = {}
            item["fullname"] = cat
            item["depth"] = (len(parts)-1)
            item["nicename"] = "    "*item["depth"] + parts[-1]
            result.append(item)
        return result
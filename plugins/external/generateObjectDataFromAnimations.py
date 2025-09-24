#-----------------------------------------------------------------------------------
#
#   SCRIPT      generateObjectDataFromAnimations.py
#   AUTHORS     Evgen Zaitsev, Michael Keller
#
#-----------------------------------------------------------------------------------


import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import math, os

from timeit import default_timer as timer


# startCurveLengthTime = 0
# endCurveLengthTime = 0

# startLengthLoop = 0
# endLengthLoop = 0

# startCalcLoop = 0
# endCalcLoop = 0

gWinGuiID = 'w_generateObjectDataFromAnimationsGuiID'

def main():
    m_win = generateObjectDataFromAnimationsWin()

class generateObjectDataFromAnimationsWin():
    """
    Main UI window class definition
    """
    def __init__(self):
        """
        Initialize window
        """
        self.m_startFrame = 1
        self.m_endFrame = 64
        self.m_amountRel = 32
        self.m_amountFix = 32
        self.m_amountFixDist = 0.0
        self.m_distance = 0.2
        self.m_distanceAmount = 0
        self.m_status = "COUNT"
        self.m_objects  = []
        self.m_indices  = []
        self.m_x = 0
        self.m_y = 0
        self.i3D_objectDataGroup = None
        self.m_arrayName = "shapeArray.dds"
        # delete ui window if opened
        if cmds.window( gWinGuiID, exists = True ):
            cmds.deleteUI( gWinGuiID, window = True )
        # create the window
        self.m_window = cmds.window( gWinGuiID, title = 'Generate MotionPath Transforms From Animated Objects', width = 400, height = 80 )
        self.m_formLayout = cmds.formLayout( parent = self.m_window ) 
        # --------------------------
        self.m_text1      = cmds.text( parent = self.m_formLayout, label = 'ANIMATED', align = 'right', width = 120, height = 20 )
        self.m_text2      = cmds.text( parent = self.m_formLayout, label = 'TRANSFORMS', align = 'right', width = 120, height = 20 )
        self.m_ts1 = cmds.textScrollList(parent = self.m_formLayout, width = 200, height = 200, ams=True )
        self.m_button1    = cmds.button( parent = self.m_formLayout,width = 160,height = 20,
                                                  label = "Load Selected",
                                                  annotation = "Load Animated Transforms",
                                                  command = lambda *args: self.uiCallback( "m_button1", args ) )
        self.m_button2    = cmds.button( parent = self.m_formLayout,width = 160,height = 20,
                                                  label = "Clear ScrollList",
                                                  annotation = "Clear ScrollList",
                                                  command = lambda *args: self.uiCallback( "m_button2", args ) )
        # --------------------------
        self.m_textArray = cmds.text( parent = self.m_formLayout, label = 'TEXTURE NAME', align = 'right', width = 120, height = 20 )
        self.m_textFieldArray = cmds.textField( parent = self.m_formLayout, 
                                            editable = True,
                                            width = 200,
                                            height = 20,
                                            annotation = 'Enter array name',
                                            changeCommand = lambda *args: self.uiCallback( "m_textFieldArray", args )) 
        # --------------------------
        self.m_text3       = cmds.text( parent = self.m_formLayout, label = 'AMOUNT RELATIVE', align = 'right', width = 120, height = 20 )
        self.m_textFieldCount  = cmds.textField( parent = self.m_formLayout, 
                                            editable = True,
                                            width = 200,
                                            height = 20,
                                            annotation = 'Enter the amount of points',
                                            changeCommand = lambda *args: self.uiCallback( "m_textFieldCount", args ))
        self.m_buttonCount     = cmds.button( parent = self.m_formLayout,
                                                  label = "Create by Amount Relative",
                                                  annotation = "Create by Amount with Relative Distance",
                                                  height = 20,
                                                  width = 160,
                                                  command = lambda *args: self.uiCallback( "m_buttonCount", args ) )
        # --------------------------
        self.m_textFix         = cmds.text( parent = self.m_formLayout, label = 'AMOUNT FIXED', align = 'right', width = 120, height = 20 )
        self.m_textFieldFix1   = cmds.textField( parent = self.m_formLayout, 
                                            editable = True,
                                            width = 80,
                                            height = 20,
                                            annotation = 'Enter the amount of points',
                                            changeCommand = lambda *args: self.uiCallback( "m_textFieldFix1", args ))
        self.m_textFieldFix2   = cmds.textField( parent = self.m_formLayout, 
                                            editable = False,
                                            width = 100,
                                            height = 20)
        self.m_buttonCountFix     = cmds.button( parent = self.m_formLayout,
                                                  label = "Create by Amount Fixed",
                                                  annotation = "Create by Amount with Fixed Distance",
                                                  height = 20,
                                                  width = 160,
                                                  command = lambda *args: self.uiCallback( "m_buttonCountFix", args ) )
        # --------------------------
        self.m_text4       = cmds.text( parent = self.m_formLayout, label = 'DISTANCE', align = 'right', width = 120, height = 20 )
        self.m_textFieldDistance  = cmds.textField( parent = self.m_formLayout, 
                                            editable = True,
                                            width = 80,
                                            height = 20,
                                            annotation = 'Enter the amount of points',
                                            changeCommand = lambda *args: self.uiCallback( "m_textFieldDistance", args ))
        self.m_textFieldDistance2   = cmds.textField( parent = self.m_formLayout, 
                                            editable = False,
                                            width = 100,
                                            height = 20)
        self.m_buttonDistance     = cmds.button( parent = self.m_formLayout,
                                                  label = "Create by Distance",
                                                  annotation = "Create by Distance",
                                                  height = 20,
                                                  width = 160,
                                                  command = lambda *args: self.uiCallback( "m_buttonDistance", args ) )
        # --------------------------
        self.m_text5 = cmds.text( parent = self.m_formLayout, label = 'KEYFRAMES', align = 'right', width = 120, height = 20 )
        self.m_textFieldKeyframes1 = cmds.textField( parent = self.m_formLayout, 
                                            editable = False,
                                            width = 60,
                                            height = 20,
                                            text="Ranges calculated from the keyframes itself")
        self.m_buttonKeyframes = cmds.button( parent = self.m_formLayout,
                                                  label = "Create by Keyframes",
                                                  annotation = "Create by Keyframes",
                                                  height = 20,
                                                  width = 160,
                                                  command = lambda *args: self.uiCallback( "m_buttonKeyframes", args ) )
        # --------------------------
        cmds.formLayout( self.m_formLayout, edit = True,
                    attachForm =    [    
                                         ( self.m_text1, 'top', 2 ),
                                         ( self.m_text1, 'left', 2 ),
                                         ( self.m_text2, 'left', 2 ),
                                         ( self.m_ts1, 'top', 2 ),
                                         ( self.m_button1, 'top', 2 ),
                                         ( self.m_button1, 'right', 2 ),
                                         ( self.m_button2, 'right', 2 ),
                                         ( self.m_textArray, 'left', 2 ),
                                         ( self.m_text3, 'left', 2 ),
                                         ( self.m_buttonCount, 'right', 2 ),
                                         ( self.m_textFix, 'left', 2 ),
                                         ( self.m_buttonCountFix, 'right', 2 ),
                                         ( self.m_text4, 'left', 2 ),
                                         ( self.m_buttonDistance, 'right',  2 ),
                                         ( self.m_text5, 'left', 2 ),
                                         ( self.m_buttonKeyframes, 'right',  2 ),
                                    ], 
                    attachControl = [
                                         ( self.m_text2, 'top', 2, self.m_text1 ),
                                         ( self.m_ts1, 'left',  2, self.m_text1 ),
                                         ( self.m_ts1, 'right', 2, self.m_button1 ),
                                         ( self.m_button2, 'top', 2, self.m_button1 ),
                                         ( self.m_textArray, 'top', 2, self.m_ts1 ),
                                         ( self.m_textFieldArray, 'top', 2, self.m_ts1 ),
                                         ( self.m_textFieldArray, 'left', 2, self.m_textArray ),
                                         ( self.m_textFieldArray, 'right', 2, self.m_button2 ),
                                         ( self.m_text3, 'top', 2, self.m_textArray ),
                                         ( self.m_textFieldCount, 'top', 2, self.m_textFieldArray ),
                                         ( self.m_textFieldCount, 'left', 2, self.m_text3 ),
                                         ( self.m_textFieldCount, 'right', 2, self.m_buttonCount ),
                                         ( self.m_buttonCount, 'top', 2, self.m_textFieldArray ),
                                         ( self.m_textFix, 'top', 2, self.m_text3 ),
                                         ( self.m_buttonCountFix, 'top', 2, self.m_buttonCount ),
                                         ( self.m_textFieldFix1, 'top', 2, self.m_textFieldCount ),
                                         ( self.m_textFieldFix2, 'top', 2, self.m_textFieldCount ),
                                         ( self.m_textFieldFix2, 'right', 2, self.m_buttonCountFix ),
                                         ( self.m_textFieldFix1, 'left', 2, self.m_textFix ),
                                         ( self.m_textFieldFix1, 'right', 2, self.m_textFieldFix2 ),
                                         ( self.m_text4, 'top', 2, self.m_textFix ),
                                         ( self.m_textFieldDistance, 'top', 2, self.m_textFieldFix1 ),
                                         ( self.m_textFieldDistance, 'left', 2, self.m_text4 ),
                                         ( self.m_textFieldDistance, 'right', 2, self.m_textFieldDistance2 ),
                                         ( self.m_textFieldDistance2, 'top', 2, self.m_textFieldFix2 ),
                                         ( self.m_textFieldDistance2, 'right', 2, self.m_buttonDistance ),
                                         ( self.m_buttonDistance, 'top', 2, self.m_buttonCountFix ),
                                         ( self.m_text5, 'top', 2, self.m_text4 ),
                                         ( self.m_textFieldKeyframes1, 'top', 2, self.m_textFieldDistance ),
                                         ( self.m_textFieldKeyframes1, 'left', 2, self.m_text5 ),
                                         ( self.m_textFieldKeyframes1, 'right', 2, self.m_buttonKeyframes ),
                                         ( self.m_buttonKeyframes, 'top', 2, self.m_buttonDistance ),
                                    ],
                    attachNone =    [    
                                         ( self.m_text1, 'bottom' ),
                                         ( self.m_text1, 'right' ),
                                         ( self.m_text2, 'bottom' ),
                                         ( self.m_text2, 'right' ),
                                         ( self.m_textArray, 'bottom' ),
                                         ( self.m_textArray, 'right' ),
                                         ( self.m_textFieldArray, 'bottom' ),
                                         ( self.m_text3, 'bottom' ),
                                         ( self.m_text3, 'right' ),
                                         ( self.m_textFix, 'bottom' ),
                                         ( self.m_textFix, 'right' ),
                                         ( self.m_text4, 'bottom' ),
                                         ( self.m_text4, 'right' ),
                                         ( self.m_ts1, 'bottom' ),
                                         ( self.m_textFieldCount, 'bottom' ),
                                         ( self.m_textFieldDistance, 'bottom' ),
                                         ( self.m_textFieldDistance2, 'left' ),
                                         ( self.m_textFieldDistance2, 'bottom' ),
                                         ( self.m_button1, 'left' ),
                                         ( self.m_button1, 'bottom' ),
                                         ( self.m_button2, 'left' ),
                                         ( self.m_button2, 'bottom' ),
                                         ( self.m_buttonCount, 'left' ),
                                         ( self.m_buttonCount, 'bottom' ),
                                         ( self.m_buttonCountFix, 'left' ),
                                         ( self.m_buttonCountFix, 'bottom' ),
                                         ( self.m_textFieldFix1, 'bottom' ),
                                         ( self.m_textFieldFix2, 'left' ),
                                         ( self.m_textFieldFix2, 'bottom' ),
                                         ( self.m_buttonDistance, 'left' ),
                                         ( self.m_buttonDistance, 'bottom' ),
                                         ( self.m_text5, 'bottom' ),
                                         ( self.m_text5, 'right' ),
                                         ( self.m_textFieldKeyframes1, 'bottom' ),
                                         ( self.m_buttonKeyframes, 'left' ),
                                         ( self.m_buttonKeyframes, 'bottom' ),
                                    ])
        # ---
        cmds.showWindow( gWinGuiID )
        self.uiRefresh()
        
    def uiRefresh( self ):
        cmds.textScrollList(self.m_ts1,e=True,removeAll=True )
        m_list = []
        for m_path in self.m_objects:
            m_list.append(m_path.fullPathName())
        cmds.textScrollList(self.m_ts1,e=True, append=m_list )
        m_str = "{}".format( self.m_arrayName )
        cmds.textField( self.m_textFieldArray, edit = True, fileName = m_str )
        m_str = "{}".format( self.m_amountRel )
        cmds.textField( self.m_textFieldCount, edit = True, fileName = m_str )
        m_str = "{}".format( self.m_amountFix )
        cmds.textField( self.m_textFieldFix1, edit = True, fileName = m_str )
        m_str = "{}".format( self.m_amountFixDist )
        cmds.textField( self.m_textFieldFix2, edit = True, fileName = m_str )
        m_str = "{}".format( self.m_distance )
        cmds.textField( self.m_textFieldDistance, edit = True, fileName = m_str )
        m_str = "{}".format( self.m_distanceAmount )
        cmds.textField( self.m_textFieldDistance2, edit = True, fileName = m_str )
    
    def uiAddObjects( self, *args ):
        m_list = cmds.ls(selection=True)
        if m_list:
            for m_obj in m_list:
                # all keyframes, like tx, ty, tz, rx, ry, rz, sx, sy, sz
                # represented in the one list, one after another 
                m_keyframes = cmds.keyframe( m_obj, query=True, timeChange=True )
                # sorted list of keyframes without duplicates
                m_keyframes = list(dict.fromkeys(m_keyframes))
                if m_keyframes:
                    if len(m_keyframes)>=2:
                        m_path = getMDagPathFromNodeName(m_obj)
                        if m_path not in self.m_objects:
                            self.m_objects.append(m_path)
                        
    def calculateDistances( self, *args ):
        if (len(self.m_objects)>0):
            self.getTextureSize()
            cmds.select( clear=True )
                        
    def generate( self, *args ):
        if (len(self.m_objects)>0):
            # start = timer()
            # endText = timer()
            self.calculateIndicesFromAnimationData()
            # endCalcInd = timer()
            self.get_i3D_objectDataGroup()
            # endMergeChild = timer()
            self.createTransforms()
            # endCreate = timer()
            cmds.select(self.i3D_objectDataGroup.fullPathName(),r=True)
            # end = timer()
            # print("Elapsed times for {} points\ngetTextureSite: {}s {}%\tcalcIndex: {}s {}%\tmergeChild: {}s {}%\tcreateTrans: {}s {}%\t total: {}s".format(self.m_x,endText -start,round((endText -start)/(end-start)*100,2),
                                                                                                                                                                        # endCalcInd-endText,round((endCalcInd-endText)/(end-start)*100,2),
                                                                                                                                                                        # endMergeChild-endCalcInd,round((endMergeChild-endCalcInd)/(end-start)*100,2),
                                                                                                                                                                        # endCreate-endMergeChild,round((endCreate-endMergeChild)/(end-start)*100,2),
                                                                                                                                                                        # end-start))
            # print("Avg Curve Length: {}, total curve length calc: {}".format(endCurveLengthTime - startCurveLengthTime,self.m_x*(endCurveLengthTime - startCurveLengthTime)))
            # print("Calc Index details\curveLength loop: {}s {}%, calcLoop: {}s {}%".format(endLengthLoop - startLengthLoop,(endLengthLoop - startLengthLoop)/(endCalcInd-endText)*100,
                                                                                            # endCalcLoop - startCalcLoop,( endCalcLoop - startCalcLoop)/(endCalcInd-endText)*100,
                                                                                           # endCalcInd-endText))
    
    def generateByKeyframes( self, *args ):
        if (len(self.m_objects)>0):
            self.calculateIndicesFromAnimationKeyframes()
            self.get_i3D_objectDataGroup()
            self.createTransforms()
            cmds.select(self.i3D_objectDataGroup.fullPathName(),r=True)
    
    def createTransforms( self, *args ):
        m_parent = self.i3D_objectDataGroup.fullPathName()
        m_z = cmds.createNode( 'transform', n="pose1", p=m_parent )
        for y in range(len(self.m_objects)):
            m_path = self.m_objects[y]
            if y >= len(self.m_indices):
                #invalid index
                return
            m_y = cmds.createNode( 'transform', n="y{}".format(y), p=m_z )
            m_pIndices = self.m_indices[y]
            for x in range(len(m_pIndices)):
                n_name = 'y{}_x{}'.format(y,x)
                m_transform = cmds.createNode( 'transform', n=n_name, p=m_y )
                cmds.setAttr("{}.translateX".format(m_transform),m_pIndices[x]["translate"][0])
                cmds.setAttr("{}.translateY".format(m_transform),m_pIndices[x]["translate"][1])
                cmds.setAttr("{}.translateZ".format(m_transform),m_pIndices[x]["translate"][2])
                cmds.setAttr("{}.rotateX".format(m_transform),m_pIndices[x]["rotate"][0])
                cmds.setAttr("{}.rotateY".format(m_transform),m_pIndices[x]["rotate"][1])
                cmds.setAttr("{}.rotateZ".format(m_transform),m_pIndices[x]["rotate"][2])
                cmds.setAttr("{}.scaleX".format(m_transform),m_pIndices[x]["scale"][0])
                cmds.setAttr("{}.scaleY".format(m_transform),m_pIndices[x]["scale"][1])
                cmds.setAttr("{}.scaleZ".format(m_transform),m_pIndices[x]["scale"][2])
                cmds.setAttr("{}.displayLocalAxis".format(m_transform),1)
                cmds.setAttr("{}.displayHandle".format(m_transform),1)
    
    def get_i3D_objectDataGroup(self, *args):
        # self.m_arrayName - dds texture name with extension
        # like "shapeArray.dds"
        m_dds = str(self.m_arrayName)
        n_short_name = os.path.splitext(os.path.basename(m_dds))[0]
        m_name = "{}_ignore".format(n_short_name)
        m_arrayPath = getMDagPathFromNodeName(m_name)
        if (m_arrayPath):
            removeChilds(m_arrayPath)
            self.i3D_objectDataGroup = m_arrayPath
        else:
            m_transform = cmds.createNode( 'transform', n=m_name )
            self.i3D_objectDataGroup = getMDagPathFromNodeName(m_transform)
        addAttribute(self.i3D_objectDataGroup.fullPathName(),"i3D_objectDataFilePath",'string',m_dds)
        addAttribute(self.i3D_objectDataGroup.fullPathName(),"i3D_objectDataExportPosition",         'bool',True)
        addAttribute(self.i3D_objectDataGroup.fullPathName(),"i3D_objectDataExportOrientation",      'bool',True)
        addAttribute(self.i3D_objectDataGroup.fullPathName(),"i3D_objectDataExportScale",            'bool',False)
        addAttribute(self.i3D_objectDataGroup.fullPathName(),"i3D_objectDataHideFirstAndLastObject", 'bool',True)
        addAttribute(self.i3D_objectDataGroup.fullPathName(),"i3D_objectDataHierarchicalSetup",      'bool',True)

    def getMObject(self,m_path):
        '''
        Return MObject from MDagPath
        or MObject from regular string path
        '''
        if isinstance(m_path, OpenMaya.MDagPath):
            return m_path.node()
        else:
            m_selectionList = OpenMaya.MSelectionList()
            m_node = OpenMaya.MObject() 
            try:            
                m_selectionList.add(m_path)
                m_selectionList.getDependNode(0, m_node)
            except:
                return None
            return m_node
            

    def calculateIndicesFromAnimationKeyframes(self):
        self.m_indices  = []
        self.m_y = len(self.m_objects)
        for path in self.m_objects:
            pathName = path.fullPathName()
            # all keyframes, like tx, ty, tz, rx, ry, rz, sx, sy, sz
            # represented in the one list, one after another 
            m_keyframes = cmds.keyframe( pathName, query=True, timeChange=True )
            # sorted list of keyframes without duplicates
            m_keyframes = list(dict.fromkeys(m_keyframes))
            m_pIndices = []
            m_curr_eulerRot = OpenMaya.MEulerRotation(0.0,0.0,0.0)
            m_prev_eulerRot = OpenMaya.MEulerRotation(0.0,0.0,0.0)
            
            for i in range(len(m_keyframes)):
                m_key = m_keyframes[i]
                m_pIndex = {}
                try:
                    m_tx = cmds.getAttr("{}.translateX".format(pathName), time=m_key)
                    m_ty = cmds.getAttr("{}.translateY".format(pathName), time=m_key)
                    m_tz = cmds.getAttr("{}.translateZ".format(pathName), time=m_key)
                    m_pIndex["translate"] = [m_tx,m_ty,m_tz]
                except:
                    m_pIndex["translate"] = [0,0,0]
                try:
                    m_rx = cmds.getAttr("{}.rotateX".format(pathName), time=m_key)
                    m_ry = cmds.getAttr("{}.rotateY".format(pathName), time=m_key)
                    m_rz = cmds.getAttr("{}.rotateZ".format(pathName), time=m_key)
                except:
                    m_rx = 0.0
                    m_ry = 0.0
                    m_rz = 0.0
                m_curr_eulerRot = OpenMaya.MEulerRotation(math.radians(m_rx),math.radians(m_ry),math.radians(m_rz))
                # fix the rotation
                if (0==i):
                    m_prev_eulerRot = m_curr_eulerRot
                else:
                    # makes quaternion "compatible" with previous point quaternion
                    # using closestSolution() function from MEulerRotation class
                    m_closest_eulerRot = m_curr_eulerRot.closestSolution(m_prev_eulerRot)
                    m_curr_eulerRot = m_closest_eulerRot
                #
                m_pIndex["rotate"] = [math.degrees(m_curr_eulerRot.x),math.degrees(m_curr_eulerRot.y),math.degrees(m_curr_eulerRot.z)]
                m_prev_eulerRot = m_curr_eulerRot
                try:
                    m_sx = cmds.getAttr("{}.scaleX".format(pathName), time=m_key)
                    m_sy = cmds.getAttr("{}.scaleY".format(pathName), time=m_key)
                    m_sz = cmds.getAttr("{}.scaleZ".format(pathName), time=m_key)
                    m_pIndex["scale"] = [m_sx,m_sy,m_sz]
                except:
                    m_pIndex["scale"] = [1,1,1]
                m_pIndices.append(m_pIndex)
                # print(m_pIndex)
            self.m_indices.append(m_pIndices)
        #print(self.m_indices)

    def calculateIndicesFromAnimationData(self):
    
        # global startLengthLoop, endLengthLoop,startCalcLoop, endCalcLoop

        self.m_indices  = []
        curveLengthDict = {}
        # startLengthLoop = timer()
        #integrated Texture Size calculation for optimization
        self.m_y = len(self.m_objects)
        curveLength = 0
        for path in self.m_objects:
            #print(path)
            pathName = path.fullPathName()
            curveLengthDict[pathName] = self.getCurveLength(path)
            curveLength = max(curveLength, curveLengthDict[pathName][-1][0])
            
        curveLength *= 0.01
        self.m_amountFixDist = float(curveLength)/float(self.m_amountFix)
        self.m_distanceAmount = int(round(float(curveLength)/self.m_distance))
        if "COUNT" == self.m_status:
            self.m_x = self.m_amountRel
        if "COUNT_FIX" == self.m_status:
            self.m_x = self.m_amountFix
        if "DISTANCE" == self.m_status:
            # find amount of points by longest curve
            self.m_x = self.m_distanceAmount

        # endLengthLoop = timer()
        # startCalcLoop = timer()
        util = OpenMaya.MScriptUtil()
        util.createFromDouble(0.0)
        ptrDouble = util.asDoublePtr()
        for path in self.m_objects:
            pathName = path.fullPathName()
            animationCurves = self.getAnimationCurves(path)
            curveLength = curveLengthDict[pathName][-1][0]
            distToFrame = curveLengthDict[pathName]
            
            emptyCount = 0
            if "COUNT" == self.m_status:
                emptyCount = int(self.m_amountRel)
            elif "COUNT_FIX" == self.m_status:
                if curveLength > 0:
                    emptyCount = int(round(0.01*curveLength/self.m_amountFixDist))
            elif "DISTANCE" == self.m_status:
                if(curveLength > 0 and self.m_distance != 0):
                    emptyCount = int(round(0.01*curveLength/self.m_distance))
            if emptyCount <= 0:
                print("No Objects to place")
                return
       
            m_pIndices = []
            currentLengthIndex = 0
            # distanceKeys = sorted(list(distToFrame.keys())) #List of distances
            m_curr_eulerRot = OpenMaya.MEulerRotation(0.0,0.0,0.0)
            m_prev_eulerRot = OpenMaya.MEulerRotation(0.0,0.0,0.0)
            #
            for i in range(emptyCount):
                currentPosition = curveLength/(emptyCount-1)*i  #target value
                currentLengthIndex = self.find_index(distToFrame,currentPosition, lowerBound = currentLengthIndex-1)
                
                lsp = distToFrame[max(currentLengthIndex-1,0)]
                usp = distToFrame[min(currentLengthIndex, len(distToFrame)-1)]
                if usp[0] - lsp[0] > 0:
                    alpha = (currentPosition - lsp[0]) / (usp[0] - lsp[0])
                elif usp[0] - lsp[0] == 0:
                    alpha = 1
                else:
                    return
                frame = lsp[1] + alpha * (usp[1] - lsp[1])

                if frame == -1:
                    print("something wrong")
                    
                frameResults = {}
                for fcKey, fcrv in animationCurves.items():
                    #call values by the 'frame'

                    fcrv.evaluate(frame,ptrDouble)
                    value = util.getDouble(ptrDouble)
                    frameResults[fcKey] = value
                    
                if ('m' == cmds.currentUnit( query=True, linear=True )):
                    unitScale = 0.01
                else:
                    unitScale = 1.0
                #
                m_pIndex = {}
                try:
                    m_pIndex["translate"] = [unitScale*frameResults['translateX'],unitScale*frameResults['translateY'],unitScale*frameResults['translateZ']]
                except:
                    m_pIndex["translate"] = [0,0,0]
                try:
                    m_rx = frameResults['rotateX']
                    m_ry = frameResults['rotateY']
                    m_rz = frameResults['rotateZ']
                except:
                    m_rx = 0.0
                    m_ry = 0.0
                    m_rz = 0.0
                    
                m_curr_eulerRot = OpenMaya.MEulerRotation(m_rx,m_ry,m_rz)
                # fix the rotation
                if (0==i):
                    m_prev_eulerRot = m_curr_eulerRot
                if (i>0):
                    # makes quaternion "compatible" with previous point quaternion
                    # using closestSolution() function from MEulerRotation class
                    m_closest_eulerRot = m_curr_eulerRot.closestSolution(m_prev_eulerRot)
                    m_curr_eulerRot = m_closest_eulerRot
                #
                m_pIndex["rotate"] = [math.degrees(m_curr_eulerRot.x),math.degrees(m_curr_eulerRot.y),math.degrees(m_curr_eulerRot.z)]
                m_prev_eulerRot = m_curr_eulerRot
                try:
                    m_pIndex["scale"] = [frameResults['scaleX'],frameResults['scaleY'],frameResults['scaleZ']]
                except:
                    m_pIndex["scale"] = [1,1,1]
                m_pIndices.append(m_pIndex)
                # print(m_pIndex)
            '''
            if "DISTANCE" == self.m_status or "COUNT_FIX" == self.m_status:
                if emptyCount < self.m_x:
                    m_pIndexLast = m_pIndices[-1]
                    m_diff = self.m_x - emptyCount
                    for i in range(m_diff):
                        m_pIndices.append(m_pIndexLast)
            '''
            self.m_indices.append(m_pIndices)
        # endCalcLoop = timer()
     
    def getAnimationCurves(self,path):
        """ Returns a dictionary with all attribute curves for the given object path """
        animCurveDict = {}
        mobj = OpenMaya.MObject()
        node = self.getMObject(path)
        fn = OpenMaya.MFnDependencyNode(node)
        for plugName in ["translateX", "translateY", "translateZ", "rotateX" , "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"]:
            plug = fn.findPlug(plugName,False)
            connections = OpenMaya.MPlugArray()
            plug.connectedTo(connections,True,False)
            if connections.length() > 1:
                print("something wrong")
            for i in range(connections.length()):
                connected = connections[i].node()
                if connected.hasFn(OpenMaya.MFn.kAnimCurve):
                    animCurve = OpenMayaAnim.MFnAnimCurve(connected)
                    animCurveDict[plugName] = animCurve
        return animCurveDict
    
    def find_index(self, elementList, value, lowerBound = 0):
        """ Binary search to find index to closest value in a sorted list, floors value if not exactly found """
        if lowerBound >= len(elementList):
            lowerBound = 0
        left, right = lowerBound, len(elementList) - 1
        while left <= right:
            middle = (left + right) // 2
            if elementList[middle][0] < value:
                left = middle + 1
            elif elementList[middle][0] > value:
                right = middle - 1
            else:
                return middle
        return left 
    
    def getCurveLength(self,path):
        """ Returns a dictionary with the distance as key and the frame as value, for the given action's fcurves """
        
        # global startCurveLengthTime, endCurveLengthTime
        
        
        # startGetCurveLength = timer() 
        # startCurveLengthTime = (startCurveLengthTime+timer())/2;
        codeToFps = {'game': 15, 'film': 24, 'pal':25, 'ntsc': 30, 'show':48, 'palf': 50, 'ntscf':60}

        kfpCount = 1
        timeStart = 0
        timeEnd = 0
        fps = cmds.currentUnit(query=True, time=True)
        if fps in codeToFps:
            fps = codeToFps[fps]
        else:
            fps = float(fps.replace("fps",""))
        animCurveDict = {}
        mobj = OpenMaya.MObject()
        node = self.getMObject(path)
        fn = OpenMaya.MFnDependencyNode(node)   
        for plugName in ["translateX", "translateY", "translateZ"]:     #to query the distance
            plug = fn.findPlug(plugName,False)
            connections = OpenMaya.MPlugArray()
            plug.connectedTo(connections,True,False)
            for i in range(connections.length()):
                connected = connections[i].node();
                if connected.hasFn(OpenMaya.MFn.kAnimCurve):
                    animCurve = OpenMayaAnim.MFnAnimCurve( connected )
                    animCurveDict[plugName] = animCurve     
                    kfpCount = max(kfpCount,animCurve.numKeys())
                    timeStart = min(timeStart, animCurve.time(0).value())
                    if animCurve.numKeys() >= 1:
                        timeEnd = max(timeEnd, animCurve.time(animCurve.numKeys()-1).value())
                    else:
                        timeEnd = max(timeEnd, timeStart)
                    
        resolution = kfpCount * 100
        frameStep = ((timeEnd/fps) - (timeStart/fps))/resolution    #get seconds
        distance = 0
        distToFrame = []
        previousFrame = 0
        
        util = OpenMaya.MScriptUtil()
        util.createFromDouble(0.0)
        ptr1 = util.asDoublePtr()
        # endSetup = timer()
        #list iteration is faster than dict view iteration
        dictView = animCurveDict.items()
        dictList = list(dictView)
        for i in range(resolution):
            frame = frameStep*i
            localDistance = 0
            for item in dictList:  #euclidian distance (x2-x1^2 + y2-y1^2 + z2-z1^2)^0.5
                item[1].evaluate(previousFrame,ptr1)
                x1 = util.getDouble(ptr1)
                item[1].evaluate(frame,ptr1)
                x2 = util.getDouble(ptr1)
                localDistance += (x1-x2)**2
            distance += localDistance**0.5
            distToFrame.append((distance,frame))
            previousFrame = frame
        # endIntegration = timer()
        # endCurveLengthTime = (endCurveLengthTime+timer())/2;
        # print("Run of getCurve Length:\n Setup: {}s {}%, Integration: {}s {}%, total {}s".format(endSetup - startGetCurveLength,(endSetup - startGetCurveLength)/(endIntegration - startGetCurveLength)*100,
                                                                                                # endIntegration - endSetup,(endIntegration - endSetup)/(endIntegration - startGetCurveLength)*100,
                                                                                                # endIntegration - startGetCurveLength))
        return distToFrame
                 
    def getTextureSize( self, *args ):
        """ used for UI callback """
        self.m_y = len(self.m_objects)
        if "COUNT" == self.m_status:
            self.m_x = self.m_amountRel
            return
        m_len = 0
        for path in self.m_objects:
            m_len = max(m_len, self.getCurveLength(path)[-1][0])
        m_len *= 0.01
        self.m_amountFixDist = float(m_len)/float(self.m_amountFix)
        self.m_distanceAmount = int(round(float(m_len)/self.m_distance))  
        if "COUNT_FIX" == self.m_status:
            self.m_x = self.m_amountFix
        if "DISTANCE" == self.m_status:
            # find amount of points by longest spline
            self.m_x = self.m_distanceAmount
         
    def uiCallback( self, *args ):
        """
        Callback for UI
        """   
        m_input = args[0]
        if ( 'm_button1' == m_input ):
            self.uiAddObjects()
            self.calculateDistances()
        if ( 'm_button2' == m_input ):
            self.m_objects  = []
            self.m_indices  = []
        if ( 'm_buttonCount' == m_input ):
            self.m_status = "COUNT"
            self.generate()
        if ( 'm_buttonCountFix' == m_input ):
            self.m_status = "COUNT_FIX"
            self.generate()
        if ( 'm_buttonDistance' == m_input ):
            self.m_status = "DISTANCE"
            self.generate()
        if ( 'm_buttonKeyframes' == m_input ):
            self.generateByKeyframes()
        if ( 'm_textFieldArray' == m_input ):
            self.m_arrayName = str(cmds.textField( self.m_textFieldArray, q = True, text=True ))
        if ( 'm_textFieldCount' == m_input ):
            self.m_amountRel = int(cmds.textField( self.m_textFieldCount, q = True, text=True ))
        if ( 'm_textFieldFix1' == m_input ):
            self.m_amountFix = int(cmds.textField( self.m_textFieldFix1, q = True, text=True ))
            self.calculateDistances()
        if ('m_textFieldDistance' == m_input):
            self.m_distance = float(cmds.textField( self.m_textFieldDistance, q = True, text=True ))
            self.calculateDistances()
        self.uiRefresh()

def addAttribute(m_node,m_attrName,m_attrType,m_attrValue):
    if (not cmds.objExists("{}.{}".format(m_node,m_attrName)) ):
        if ('bool'==m_attrType):
            cmds.addAttr(m_node, ln=m_attrName, nn=m_attrName, at='bool')
        elif('string'==m_attrType):
            cmds.addAttr(m_node, ln=m_attrName, nn=m_attrName, dt='string')
        elif('float'==m_attrType):
            cmds.addAttr(m_node, ln=m_attrName, nn=m_attrName, at='float')
        elif('int'==m_attrType):
            cmds.addAttr(m_node, ln=m_attrName, nn=m_attrName, at='long')
    if ('bool'==m_attrType):
        cmds.setAttr("{}.{}".format(m_node,m_attrName), bool(m_attrValue))
    elif('string'==m_attrType):
        cmds.setAttr("{}.{}".format(m_node,m_attrName), "{}".format(m_attrValue), type='string')
    elif('float'==m_attrType):
        cmds.setAttr("{}.{}".format(m_node,m_attrName), float(m_attrValue))
    elif('int'==m_attrType):
        cmds.setAttr("{}.{}".format(m_node,m_attrName), int(m_attrValue))
    
def removeChilds(m_path):
    m_str = ""
    for i in range(m_path.childCount()):
        m_child = m_path.child(i)
        m_objFn = OpenMaya.MFnDagNode( m_child )
        if (OpenMaya.MFn.kTransform == m_child.apiType()):
            m_str += " {}".format(m_objFn.fullPathName())
    if ( ""!= m_str):
        m_strCommand = "select -clear;\n"
        m_strCommand = "select -r {};\n".format(m_str)
        m_strCommand += "doDelete;\n"
        OpenMaya.MGlobal.executeCommand( m_strCommand )

def getMObjectFromSelection():
    m_selectionList = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList( m_selectionList )
    m_node = OpenMaya.MObject() 
    try:
        m_selectionList.getDependNode( 0, m_node )
        if ( m_node.isNull() ): return None
    except:
        return None
    return m_node

def getMObjectFromNodeName( m_node_name ):
    m_selectionList = OpenMaya.MSelectionList()
    m_node = OpenMaya.MObject() 
    try:            
        m_selectionList.add(m_node_name)
        m_selectionList.getDependNode(0, m_node)
    except:
        return None
    return m_node

def getMDagPathFromNodeName( m_node_name ):
    m_selectionList = OpenMaya.MSelectionList()
    m_objPath = OpenMaya.MDagPath()
    try:            
        m_selectionList.add( m_node_name )
        m_selectionList.getDagPath( 0, m_objPath )
    except:
        return None
    return m_objPath 
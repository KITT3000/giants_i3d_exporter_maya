#-----------------------------------------------------------------------------------
#
#   SCRIPT      generateObjectDataFromCurves.py
#   AUTHORS     Evgen Zaitsev, Michael Keller
#
#-----------------------------------------------------------------------------------


import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import math, os

gWinGuiID = 'w_generateObjectDataFromCurvesGuiID'

def main():
    m_win = generateObjectDataFromCurvesWin()

class generateObjectDataFromCurvesWin():
    """
    Main UI window class definition
    """
    def __init__(self):
        """
        Initialize window
        """
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
        # 1 - align to X
        # 2 - align to Y
        # 3 - align to Z
        self.m_alignTo = 3
        self.m_arrayName = "shapeArray.dds"
        # delete ui window if opened
        if cmds.window( gWinGuiID, exists = True ):
            cmds.deleteUI( gWinGuiID, window = True )
        # create the window
        self.m_window = cmds.window( gWinGuiID, title = 'Generate MotionPath Transforms From multiple Curves', width = 400, height = 80 )
        self.m_formLayout = cmds.formLayout( parent = self.m_window )
        # --------------------------
        self.m_text1      = cmds.text( parent = self.m_formLayout, label = 'CURVES', align = 'right', width = 120, height = 20 )
        self.m_text2      = cmds.text( parent = self.m_formLayout, label = 'kNurbsCurve', align = 'right', width = 120, height = 20 )
        self.m_ts1 = cmds.textScrollList(parent = self.m_formLayout, width = 200, height = 200, ams=True )
        self.m_button1    = cmds.button( parent = self.m_formLayout,width = 160,height = 20,
                                                  label = "Load Selected",
                                                  annotation = "Load Curves",
                                                  command = lambda *args: self.uiCallback( "m_button1", args ) )
        self.m_button2    = cmds.button( parent = self.m_formLayout,width = 160,height = 20,
                                                  label = "Clear ScrollList",
                                                  annotation = "Clear ScrollList",
                                                  command = lambda *args: self.uiCallback( "m_button2", args ) )
        # --------------------------
        self.m_textAlign = cmds.text( parent = self.m_formLayout, label = 'Align TO', align = 'right', width = 120, height = 20 )
        self.m_rbgAlign  = cmds.radioButtonGrp( parent = self.m_formLayout,
                                                    numberOfRadioButtons=3,
                                                    labelArray3=['X', 'Y', 'Z'],
                                                    changeCommand = lambda *args: self.uiCallback( "m_rbgAlign", args ))
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
                                                  label = "Create by Amount Rel",
                                                  annotation = "Distance between points (in all curves) are relative (equally redistributed along the curve)",
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
                                                  label = "Create by Amount Fix",
                                                  annotation = "Distance between points (in all curves) are fixed (some curves will have more or less points, depends on the length of the curve)",
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
                                                  annotation = "Distance between points (in all curves) are fixed, amount of points calculated by distance",
                                                  height = 20,
                                                  width = 160,
                                                  command = lambda *args: self.uiCallback( "m_buttonDistance", args ) )
        # --------------------------
        self.m_text5       = cmds.text( parent = self.m_formLayout, label = 'EDIT POINTS', align = 'right', width = 120, height = 20 )
        self.m_textFieldEditPoints = cmds.textField( parent = self.m_formLayout, 
                                            editable = False,
                                            width = 60,
                                            height = 20,
                                            text="Ranges calculated from edit points of the curves")
        self.m_buttonEditPoints = cmds.button( parent = self.m_formLayout,
                                                  label = "Create by Edit Points",
                                                  annotation = "Points added exactly in Edit Points of the curves",
                                                  height = 20,
                                                  width = 160,
                                                  command = lambda *args: self.uiCallback( "m_buttonEditPoints", args ) )
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
                                         ( self.m_textAlign, 'left', 2 ),
                                         ( self.m_textArray, 'left', 2 ),
                                         ( self.m_text3, 'left', 2 ),
                                         ( self.m_buttonCount, 'right', 2 ),
                                         ( self.m_textFix, 'left', 2 ),
                                         ( self.m_buttonCountFix, 'right', 2 ),
                                         ( self.m_text4, 'left', 2 ),
                                         ( self.m_buttonDistance, 'right',  2 ),
                                         ( self.m_text5, 'left', 2 ),
                                         ( self.m_buttonEditPoints, 'right',  2 ),
                                    ],
                    attachControl = [
                                         ( self.m_text2, 'top', 2, self.m_text1 ),
                                         ( self.m_ts1, 'left',  2, self.m_text1 ),
                                         ( self.m_ts1, 'right', 2, self.m_button1 ),
                                         ( self.m_button2, 'top', 2, self.m_button1 ),
                                         ( self.m_textAlign, 'top', 2, self.m_ts1 ),
                                         ( self.m_rbgAlign, 'top', 2, self.m_ts1 ),
                                         ( self.m_rbgAlign, 'left', 2, self.m_textAlign ),
                                         ( self.m_rbgAlign, 'right', 2, self.m_button2 ),
                                         ( self.m_textArray, 'top', 2, self.m_textAlign ),
                                         ( self.m_textFieldArray, 'top', 2, self.m_rbgAlign ),
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
                                         ( self.m_textFieldEditPoints, 'top', 2, self.m_textFieldDistance ),
                                         ( self.m_textFieldEditPoints, 'left', 2, self.m_text5 ),
                                         ( self.m_textFieldEditPoints, 'right', 2, self.m_buttonEditPoints ),
                                         ( self.m_buttonEditPoints, 'top', 2, self.m_buttonDistance ),
                                    ],
                    attachNone =    [
                                         ( self.m_text1, 'bottom' ),
                                         ( self.m_text1, 'right' ),
                                         ( self.m_text2, 'bottom' ),
                                         ( self.m_text2, 'right' ),
                                         ( self.m_textAlign, 'bottom' ),
                                         ( self.m_textAlign, 'right' ),
                                         ( self.m_rbgAlign, 'bottom' ),
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
                                         ( self.m_textFieldEditPoints, 'bottom' ),
                                         ( self.m_buttonEditPoints, 'left' ),
                                         ( self.m_buttonEditPoints, 'bottom' ),
                                    ])
        # ---
        cmds.showWindow( gWinGuiID )
        self.uiRefresh()

    def uiRefresh( self ):
        cmds.textScrollList(self.m_ts1,e=True,removeAll=True )
        m_list = []
        for item in self.m_objects:
            m_path = item[0]
            m_list.append(m_path.fullPathName())
        cmds.textScrollList(self.m_ts1,e=True, append=m_list )
        #
        cmds.radioButtonGrp(self.m_rbgAlign,e=True,sl=self.m_alignTo)
        #
        m_str = "{}".format( self.m_arrayName )
        cmds.textField( self.m_textFieldArray, edit = True, fileName = m_str )
        #
        m_str = "{}".format( self.m_amountRel )
        cmds.textField( self.m_textFieldCount, edit = True, fileName = m_str )
        #
        m_str = "{}".format( self.m_amountFix )
        cmds.textField( self.m_textFieldFix1, edit = True, fileName = m_str )
        #
        m_str = "{}".format( self.m_amountFixDist )
        cmds.textField( self.m_textFieldFix2, edit = True, fileName = m_str )
        #
        m_str = "{}".format( self.m_distance )
        cmds.textField( self.m_textFieldDistance, edit = True, fileName = m_str )
        #
        m_str = "{}".format( self.m_distanceAmount )
        cmds.textField( self.m_textFieldDistance2, edit = True, fileName = m_str )

    def uiAddObjects( self, *args ):
        m_list = cmds.ls(selection=True)
        for m_obj in m_list:
            m_path = getMDagPathFromNodeName(m_obj)
            # add only splines
            if m_path.hasFn( OpenMaya.MFn.kNurbsCurve ):
                m_fnNurbs = OpenMaya.MFnNurbsCurve(m_path)
                self.m_objects.append((m_path,m_fnNurbs))

    def calculateDistances( self, *args ):
        if (len(self.m_objects)>0):
            self.getTextureSize()
            cmds.select( clear=True )

    def generate( self, *args ):
        if (len(self.m_objects)>0):
            self.calculateIndicesFromCurves()
            self.get_i3D_objectDataGroup()
            self.createTransforms()
            cmds.select(self.i3D_objectDataGroup.fullPathName(),r=True)

    def createTransforms( self, *args ):
        m_parent = self.i3D_objectDataGroup.fullPathName()
        m_z = cmds.createNode( 'transform', n="pose1", p=m_parent )
        for y in range(len(self.m_objects)):
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
                cmds.setAttr("{}.displayLocalAxis".format(m_transform),1)
                cmds.setAttr("{}.displayHandle".format(m_transform),1)

    def get_i3D_objectDataGroup(self, *args):
        # self.m_arrayName - dds texture name with extension
        # like "shapeArray.dds"
        m_dds = str(self.m_arrayName)
        n_short_name = os.path.splitext(os.path.basename(m_dds))[0]
        m_name = "{}_ignore".format(n_short_name)
        #
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

    def calculateIndicesFromCurves(self):
        #
        self.m_indices  = []
        self.m_y = len(self.m_objects)
        #
        curveLength = 0
        for item in self.m_objects:
            m_path = item[0]
            m_fnNurbs = item[1]
            curveLength = max(curveLength, m_fnNurbs.length())
        #
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
        #
        # iterate over all curves
        #
        for item in self.m_objects:
            m_path = item[0]
            m_fnNurbs = item[1]
            # Return the arc length of this curve or 0.0 if it cannot be computed.
            curveLength = m_fnNurbs.length()
            # Return the number of knots for this curve. If the number of knots cannot be determined then 0 is returned.
            m_numKnots = m_fnNurbs.numKnots()

            parentTransform = cmds.listRelatives(item[1].fullPathName(), type='transform', p=True, fullPath=True)
            originalTranslation = cmds.xform(parentTransform, r=True, q=True, t=True)
            originalRotation = cmds.xform(parentTransform, r=True, q=True, ro=True)
            cmds.xform(parentTransform, ws=True, t=cmds.xform(parentTransform, r=True, q=True, ws=False, t=True))
            cmds.xform(parentTransform, ws=True, ro=cmds.xform(parentTransform, r=True, q=True, ws=False, ro=True))

            emptyCount = 0
            if "EDIT_POINTS" != self.m_status:
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
            #
            m_pIndices = []
            m_pIndices2 = []
            # create helping curve in order to calculate tangent vector
            # need to be removed afterwards
            m_offsetCurve = cmds.offsetCurve( m_path.fullPathName(), d=0.01)
            m_obj2 = getMObjectFromNodeName(m_offsetCurve[0])
            m_path2, m_fnNurbs2 = getFnNurbs(m_obj2)
            #
            #
            #
            def getIndices(m_param,m_param2):
                m_point = OpenMaya.MPoint()
                m_point2 = OpenMaya.MPoint()
                # position
                m_fnNurbs.getPointAtParam(m_param,m_point,OpenMaya.MSpace.kWorld)
                m_fnNurbs2.getPointAtParam(m_param2,m_point2,OpenMaya.MSpace.kWorld)
                # intendent to be used in meters, so no centimeters support
                m_pIndex = {}
                m_pIndex["point"]     = m_point
                m_pIndex["translate"] = [0.01*m_point.x,0.01*m_point.y,0.01*m_point.z]
                m_pIndices.append(m_pIndex)
                m_pIndex2 = {}
                m_pIndex2["point"]     = m_point2
                m_pIndex2["translate"] = [0.01*m_point2.x,0.01*m_point2.y,0.01*m_point2.z]
                m_pIndices2.append(m_pIndex2)
                return m_pIndices, m_pIndices2
            #
            #
            #
            if "EDIT_POINTS" == self.m_status:
                #
                # iterate over all edit points
                #
                for i in range(m_numKnots):
                    # Get the parameter value of the specified knot for this curve. Knot indices range from 0 to numKnots() - 1
                    m_param = m_fnNurbs.knot(i)
                    m_param2 = m_fnNurbs2.knot(i)
                    m_pIndices, m_pIndices2 = getIndices(m_param,m_param2)
            else:
                # case: COUNT, COUNT_FIX, DISTANCE
                #
                # iterate over divisions, equal distance between points
                #
                for i in range(emptyCount):
                    currentPosition = curveLength/(emptyCount-1)*i  #target value
                    m_param = m_fnNurbs.findParamFromLength(currentPosition)
                    m_param2 = m_fnNurbs2.findParamFromLength(currentPosition)
                    m_pIndices, m_pIndices2 = getIndices(m_param,m_param2)
            #
            #
            #
            getRotationsEff2(m_pIndices,m_pIndices2,self.m_alignTo)
            cmds.delete(m_path2.fullPathName())
            self.m_indices.append(m_pIndices)

            cmds.xform(parentTransform, t=originalTranslation)
            cmds.xform(parentTransform, ro=originalRotation)

    def getTextureSize( self, *args ):
        """ used for UI callback """
        if "COUNT" == self.m_status:
            self.m_x = self.m_amountRel
            return
        self.m_y = len(self.m_objects)
        m_len = 0
        for item in self.m_objects:
            m_fnNurbs = item[1]
            m_len = max(m_len, m_fnNurbs.length())
        m_len *= 0.01
        self.m_amountFixDist = float(m_len)/float(self.m_amountFix)
        self.m_distanceAmount = int(round(float(m_len)/self.m_distance))
        if "COUNT_FIX" == self.m_status:
            self.m_x = self.m_amountFix
        if "DISTANCE" == self.m_status:
            # find amount of points by longest spline
            self.m_x = self.m_distanceAmount
        if "EDIT_POINTS" == self.m_status:
            # find amount of points by highest number of EditPoints in the curve
            self.m_x = 0
            for item in self.m_objects:
                m_fnNurbs = item[1] # OpenMaya.MFnNurbsCurve
                # Return the number of knots for this curve. If the number of knots cannot be determined then 0 is returned.
                m_numKnots = m_fnNurbs.numKnots()
                if self.m_x < m_numKnots:
                    self.m_x = m_numKnots

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
        if ( 'm_buttonEditPoints' == m_input):
            self.m_status = "EDIT_POINTS"
            self.generate()
        if ( 'm_rbgAlign' == m_input):
            self.m_alignTo = cmds.radioButtonGrp(self.m_rbgAlign,sl=True,q=True)
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

def getRotationsEff2(m_pIndices,m_pIndices2,m_alignTo=3):
    # calculate using transformation matrix
    m_prev = OpenMaya.MQuaternion()
    for i in range(len(m_pIndices)):
        m_pIndex = m_pIndices[i]
        m_pIndex2 = m_pIndices2[i]
        m_vector = OpenMaya.MVector(0.0,0.0,0.0)
        m_tangent = OpenMaya.MVector(0.0,0.0,0.0)
        m_up = OpenMaya.MVector(0.0,0.0,0.0)
        if( (len(m_pIndices)-1) == i):
            # last item
            m_p1 = m_pIndices[i-1]["point"]
            m_p2 = m_pIndices[i]["point"]
        else:
            m_p1 = m_pIndices[i]["point"]
            m_p2 = m_pIndices[i+1]["point"]
        m_vector = OpenMaya.MVector( (m_p2-m_p1) )
        m_vector.normalize()
        # ----------------------------------------
        # calculate tangent
        m_pCurr = m_pIndices[i]["point"]
        m_pTang = m_pIndices2[i]["point"]
        m_tangent = OpenMaya.MVector( (m_pTang-m_pCurr) )
        m_tangent.normalize()
        # calculate up vector
        m_up = m_vector^m_tangent
        m_up.normalize()
        # re-adjust tangent
        m_tangent = m_up^m_vector
        m_tangent.normalize()
        #----------------------------------------
        # dancing around API
        m_matrix = OpenMaya.MMatrix()
        m_util = OpenMaya.MScriptUtil()
        # 1 - align to X
        # 2 - align to Y
        # 3 - align to Z
        m_list = [  m_tangent.x,m_tangent.y,m_tangent.z,0.0,
                    m_up.x,m_up.y,m_up.z,0.0,
                    m_vector.x,m_vector.y,m_vector.z,0.0,
                    0.0,0.0,0.0,0.0]
        if (1==m_alignTo):
            m_list = [  m_vector.x,m_vector.y,m_vector.z,0.0,
                        m_up.x,m_up.y,m_up.z,0.0,
                        m_tangent.x,m_tangent.y,m_tangent.z,0.0,
                        0.0,0.0,0.0,0.0]
        if (2==m_alignTo):
            m_list = [  m_up.x,m_up.y,m_up.z,0.0,
                        m_vector.x,m_vector.y,m_vector.z,0.0,
                        m_tangent.x,m_tangent.y,m_tangent.z,0.0,
                        0.0,0.0,0.0,0.0]
        m_util.createMatrixFromList(m_list,m_matrix)
        m_matrixTr = OpenMaya.MTransformationMatrix(m_matrix)
        #
        # THIS PART IS IMPORTANT
        #
        # makes quaternion "compatible" with previous point quaternion
        # in order to make use of linear interpolation in the shader
        #
        m_curr_eulerRot = m_matrixTr.eulerRotation()
        if (0==i):
            m_prev_eulerRot = m_curr_eulerRot
        if (i>0):
            m_closest_eulerRot = m_curr_eulerRot.closestSolution(m_prev_eulerRot)
            m_curr_eulerRot = m_closest_eulerRot
        m_pIndex["rotate"] = [math.degrees(m_curr_eulerRot.x),math.degrees(m_curr_eulerRot.y),math.degrees(m_curr_eulerRot.z)]
        m_prev_eulerRot = m_curr_eulerRot

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

def getFnNurbs(m_obj):
    m_path  = OpenMaya.MDagPath()
    if m_obj:
        if m_obj.hasFn( OpenMaya.MFn.kDagNode ):
            OpenMaya.MDagPath.getAPathTo( m_obj, m_path )
            if m_path.hasFn( OpenMaya.MFn.kNurbsCurve ):
                m_fnNurbs = OpenMaya.MFnNurbsCurve(m_path)
                return (m_path, m_fnNurbs)
    return (None, None)

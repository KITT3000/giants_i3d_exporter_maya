#-----------------------------------------------------------------------------------
#
#   SCRIPT      generateObjectDataFromCurve.py
#   AUTHORS     Evgen Zaitsev
#
#   Creates equally distributed transforms along the curve
#   made to work in conjunction with texture based vertex animation shader
#   rotation values uniquely calculated
#
#-----------------------------------------------------------------------------------

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import math
gWinGuiID = 'w_generateObjectDataFromCurveGuiID'

def main():
    #m_obj = getMObjectFromSelection()
    #placeTransforms(m_obj,"COUNT",m_amount=64)
    #placeTransforms(m_obj,"DISTANCE",m_distance=0.1)
    m_win = generateObjectDataFromCurveWin()

class generateObjectDataFromCurveWin():
    """
    Main UI window class definition
    """
    def __init__(self):
        """
        Initialize window
        """
        self.m_amount = 64
        self.m_distance = 0.1
        self.m_obj  = None
        self.m_path = None
        self.m_type = 1
        # delete ui window if opened
        if cmds.window( gWinGuiID, exists = True ):
            cmds.deleteUI( gWinGuiID, window = True )
        # create the window
        self.m_window = cmds.window( gWinGuiID, title = 'Generate MotionPath Transforms from single Curve', width = 150, height = 40 )
        self.m_formLayout = cmds.formLayout( parent = self.m_window ) 
        # --------------------------
        self.m_textNurbs      = cmds.text( parent = self.m_formLayout, label = 'NURBS', align = 'right', width = 80, height = 20 )
        self.m_textFieldNurbs = cmds.textField( parent = self.m_formLayout, 
                                            editable = False,
                                            width = 200,
                                            height = 20,
                                            annotation = 'Load OpenMaya.MFn.kNurbsCurve')
        self.m_buttonNurbs    = cmds.button( parent = self.m_formLayout,
                                                  label = "Load",
                                                  annotation = "Load OpenMaya.MFn.kNurbsCurve",
                                                  height = 20,
                                                  width = 120,
                                                  command = lambda *args: self.uiCallback( "m_buttonNurbs", args ) )
        # --------------------------
        self.m_textType      = cmds.text( parent = self.m_formLayout, label = 'TYPE', align = 'right', width = 80, height = 20 )
        self.m_rbgType       = cmds.radioButtonGrp( numberOfRadioButtons=2, labelArray2=['MOTION_PATH', 'EFFECT'] )
        cmds.radioButtonGrp(self.m_rbgType,e=True,sl=self.m_type)
        self.m_textType2     = cmds.text( parent = self.m_formLayout, label = ' ', align = 'right', width = 80, height = 20 )
        # --------------------------
        self.m_textCount       = cmds.text( parent = self.m_formLayout, label = 'AMOUNT', align = 'right', width = 80, height = 20 )
        self.m_textFieldCount  = cmds.textField( parent = self.m_formLayout, 
                                            editable = True,
                                            width = 200,
                                            height = 20,
                                            annotation = 'Enter the amount of points',
                                            changeCommand = lambda *args: self.uiCallback( "m_textFieldCount", args ))
        self.m_buttonCount     = cmds.button( parent = self.m_formLayout,
                                                  label = "Create by Amount",
                                                  annotation = "Create by Amount",
                                                  height = 20,
                                                  width = 120,
                                                  command = lambda *args: self.uiCallback( "m_buttonCount", args ) )
        # --------------------------
        self.m_textDistance       = cmds.text( parent = self.m_formLayout, label = 'DISTANCE', align = 'right', width = 80, height = 20 )
        self.m_textFieldDistance  = cmds.textField( parent = self.m_formLayout, 
                                            editable = True,
                                            width = 200,
                                            height = 20,
                                            annotation = 'Enter the amount of points',
                                            changeCommand = lambda *args: self.uiCallback( "m_textFieldDistance", args ))
        self.m_buttonDistance     = cmds.button( parent = self.m_formLayout,
                                                  label = "Create by Distance",
                                                  annotation = "Create by Distance",
                                                  height = 20,
                                                  width = 120,
                                                  command = lambda *args: self.uiCallback( "m_buttonDistance", args ) )
        # --------------------------
        cmds.formLayout( self.m_formLayout, edit = True,
                    attachForm =    [    
                                         ( self.m_textNurbs,      'top',    2 ), 
                                         ( self.m_textNurbs,      'left',   2 ),
                                         ( self.m_textFieldNurbs, 'top',    2 ),
                                         ( self.m_buttonNurbs,    'top',    2 ),
                                         ( self.m_buttonNurbs,    'right',  2 ),
                                         ( self.m_textType,       'left',   2 ),
                                         ( self.m_textType2,      'top',    2 ),
                                         ( self.m_textType2,      'right',  2 ),
                                         ( self.m_textCount,      'left',   2 ),
                                         ( self.m_buttonCount,    'right',  2 ),
                                         ( self.m_textDistance,   'left',   2 ),
                                         ( self.m_buttonDistance, 'right',  2 ),
                                    ], 
                    attachControl = [
                                         ( self.m_textFieldNurbs,  'left',  2, self.m_textNurbs      ), 
                                         ( self.m_textFieldNurbs,  'right', 2, self.m_buttonNurbs    ), 
                                         ( self.m_textType,        'top',   2, self.m_textNurbs      ),
                                         ( self.m_rbgType,         'top',   2, self.m_textFieldNurbs      ),
                                         ( self.m_rbgType,         'left',  2, self.m_textType      ),
                                         ( self.m_textCount,       'top',   2, self.m_textType      ),
                                         ( self.m_textType2,       'top',   2, self.m_buttonNurbs    ),
                                         ( self.m_textFieldCount,  'top',   2, self.m_rbgType ),
                                         ( self.m_textFieldCount,  'left',  2, self.m_textCount      ),
                                         ( self.m_textFieldCount,  'right', 2, self.m_buttonCount    ),
                                         ( self.m_buttonCount,     'top',   2, self.m_textType2    ),
                                         ( self.m_textDistance,      'top',   2, self.m_textCount      ),
                                         ( self.m_textFieldDistance, 'top',   2, self.m_textFieldCount ),
                                         ( self.m_textFieldDistance, 'left',  2, self.m_textDistance      ),
                                         ( self.m_textFieldDistance, 'right', 2, self.m_buttonDistance    ),
                                         ( self.m_buttonDistance,    'top',   2, self.m_buttonCount    ),
                                    ],
                    attachNone =    [    
                                         ( self.m_textNurbs,     'bottom' ),
                                         ( self.m_textNurbs,     'right'  ),
                                         ( self.m_textType,     'bottom' ),
                                         ( self.m_textType,     'right'  ),
                                         ( self.m_rbgType,  'bottom' ),
                                         ( self.m_rbgType,  'right'  ),
                                         ( self.m_textCount,     'bottom' ),
                                         ( self.m_textCount,     'right'  ),
                                         ( self.m_textDistance,  'bottom' ),
                                         ( self.m_textDistance,  'right'  ),
                                         ( self.m_textFieldNurbs,    'bottom' ),
                                         ( self.m_textFieldCount,    'bottom' ),
                                         ( self.m_textFieldDistance, 'bottom' ),
                                         ( self.m_buttonNurbs,    'left'   ),
                                         ( self.m_buttonNurbs,    'bottom' ),
                                         ( self.m_textType2,    'left'   ),
                                         ( self.m_textType2,    'bottom' ),
                                         ( self.m_buttonCount,    'left'   ),
                                         ( self.m_buttonCount,    'bottom' ),
                                         ( self.m_buttonDistance, 'left'   ),
                                         ( self.m_buttonDistance, 'bottom' ),
                                    ])
        # ---
        cmds.showWindow( gWinGuiID )
        self.uiRefresh()
        
    def uiRefresh( self ):
        if self.m_path and self.m_obj:
            m_str = "{}".format( self.m_path.fullPathName() )
        else:
            m_str = ""
        cmds.textField( self.m_textFieldNurbs, edit = True, fileName = m_str )
        m_str = "{}".format( self.m_amount )
        cmds.textField( self.m_textFieldCount, edit = True, fileName = m_str )
        m_str = "{}".format( self.m_distance )
        cmds.textField( self.m_textFieldDistance, edit = True, fileName = m_str )
        
    def getType( self ):
        m_type = cmds.radioButtonGrp(self.m_rbgType,sl=True,q=True)
        if (1==m_type):
            return 'MOTION_PATH'
        if (2==m_type):
            return 'EFFECT'
        return 'MOTION_PATH'
        
    def uiCallback( self, *args ):
        """
        Callback for UI
        """   
        m_input = args[0]
        if ( 'm_buttonNurbs' == m_input ):
            self.m_obj = getMObjectFromSelection()
            if self.m_obj:
                self.m_path, m_fnNurbs = getFnNurbs(self.m_obj)
        if ( 'm_buttonCount' == m_input ):
            if self.m_path:
                placeTransforms(self.m_obj,"COUNT",self.getType(),m_amount=self.m_amount)
        if ( 'm_buttonDistance' == m_input ):
            if self.m_path:
                placeTransforms(self.m_obj,"DISTANCE",self.getType(),m_distance=self.m_distance)
        if ( 'm_textFieldCount' == m_input ):
            self.m_amount = int(cmds.textField( self.m_textFieldCount, q = True, text=True ))
        if ('m_textFieldDistance' == m_input):
            self.m_distance = float(cmds.textField( self.m_textFieldDistance, q = True, text=True ))
        self.uiRefresh()
#-----------------------------------------------------------------------------------
#
#-----------------------------------------------------------------------------------
def get_i3D_objectDataGroup(m_path):
    m_name = m_path.fullPathName()
    m_textureName = "{}Array.dds".format(m_name)
    m_textureName = m_textureName.split("|")[-1]
    # ------------
    m_name = "{}Array_ignore".format(m_name)
    m_niceName = m_name.split("|")[-1]
    # ------------
    m_arrayPath = getMDagPathFromNodeName(m_name)
    if (m_arrayPath):
        removeChilds(m_arrayPath)
        return m_arrayPath
    else:
        m_dagFn = OpenMaya.MFnDagNode()
        m_dagFn.setObject( m_path.node() )
        m_objParent = m_dagFn.parent(0)
        if (OpenMaya.MFn.kWorld == m_objParent.apiType()):
            m_transform = cmds.createNode( 'transform', n=m_niceName )
        else:
            if m_objParent.hasFn( OpenMaya.MFn.kDagNode ):
                m_dagPathParent = OpenMaya.MDagPath()
                OpenMaya.MDagPath.getAPathTo( m_objParent, m_dagPathParent )
            m_transform = cmds.createNode( 'transform', n=m_niceName, p=m_dagPathParent.fullPathName() )
        addAttribute(m_transform,"i3D_objectDataFilePath",               'string',m_textureName)
        addAttribute(m_transform,"i3D_objectDataExportPosition",         'bool',True)
        addAttribute(m_transform,"i3D_objectDataExportOrientation",      'bool',True)
        addAttribute(m_transform,"i3D_objectDataExportScale",            'bool',False)
        addAttribute(m_transform,"i3D_objectDataHideFirstAndLastObject", 'bool',False)
        addAttribute(m_transform,"i3D_objectDataHierarchicalSetup",      'bool',False)
        return getMDagPathFromNodeName(m_transform)

def addAttribute(m_node,m_attrName,m_attrType,m_attrValue):
    if (not cmds.objExists("{}.{}".format(m_node,m_attrName)) ):
        if ('bool'==m_attrType):
            cmds.addAttr(m_node, ln=m_attrName, nn=m_attrName, at='bool')
            cmds.setAttr("{}.{}".format(m_node,m_attrName), m_attrValue)
        elif('string'==m_attrType):
            cmds.addAttr(m_node, ln=m_attrName, nn=m_attrName, dt='string')
            cmds.setAttr("{}.{}".format(m_node,m_attrName), m_attrValue, type='string')
        elif('float'==m_attrType):
            cmds.addAttr(m_node, ln=m_attrName, nn=m_attrName, at='float')
            cmds.setAttr("{}.{}".format(m_node,m_attrName), m_attrValue)

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

def placeTransforms(m_obj,m_status = "COUNT",m_type='MOTION_PATH', m_amount = 64, m_distance = 0.1):
    m_path, m_fnNurbs = getFnNurbs(m_obj)
    if m_fnNurbs:
        print("Processing kNurbsCurve {}".format(m_path.fullPathName()))
        if "COUNT" == m_status:
            m_count = int(m_amount)
        if "DISTANCE" == m_status:
            m_count = int(round(0.01*m_fnNurbs.length()/m_distance))
        print("Points to process: {}".format(m_count))
        m_pIndices = []
        m_step = 1.0/float(m_count)
        # --------------------------------------------------------------
        if 'EFFECT' == m_type:
            # EFFECT
            m_pIndices2 = []
            # create helping curve in order to calculate tangent
            # need to be removed afterwards 
            m_offsetCurve = cmds.offsetCurve( m_path.fullPathName())
            m_obj2 = getMObjectFromNodeName(m_offsetCurve[0])
            m_path2, m_fnNurbs2 = getFnNurbs(m_obj2)
            # ----------------
            m_step = 1.0/float(m_count-1)
            for i in range(m_count):
                m_param = m_fnNurbs.findParamFromLength(m_fnNurbs.length()*i*m_step)
                m_param2 = m_fnNurbs2.findParamFromLength(m_fnNurbs2.length()*i*m_step)
                m_point = OpenMaya.MPoint()
                m_point2 = OpenMaya.MPoint()
                # position
                m_fnNurbs.getPointAtParam(m_param,m_point,OpenMaya.MSpace.kWorld)
                m_fnNurbs2.getPointAtParam(m_param2,m_point2,OpenMaya.MSpace.kWorld)
                m_pIndex = {}
                m_pIndex["point"]     = m_point
                m_pIndex["translate"] = [0.01*m_point.x,0.01*m_point.y,0.01*m_point.z]
                m_pIndices.append(m_pIndex)
                m_pIndex2 = {}
                m_pIndex2["point"]     = m_point2
                m_pIndex2["translate"] = [0.01*m_point2.x,0.01*m_point2.y,0.01*m_point2.z]
                m_pIndices2.append(m_pIndex2)
            getRotationsEff2(m_pIndices,m_pIndices2)
            cmds.delete(m_path2.fullPathName())
        else:
            # MOTION_PATH
            for i in range(m_count):
                m_param = m_fnNurbs.findParamFromLength(m_fnNurbs.length()*i*m_step)
                m_point = OpenMaya.MPoint()
                # position
                m_fnNurbs.getPointAtParam(m_param,m_point,OpenMaya.MSpace.kWorld)
                m_pIndex = {}
                m_pIndex["point"]     = m_point
                m_pIndex["translate"] = [0.01*m_point.x,0.01*m_point.y,0.01*m_point.z]
                m_pIndices.append(m_pIndex)
            getRotationsMP(m_pIndices)
        # --------------------------------------------------------------
        m_arrayPath = get_i3D_objectDataGroup(m_path)
        createTransforms(m_pIndices,m_arrayPath.fullPathName())
        cmds.select(m_arrayPath.fullPathName(),r=True)
    else:
        print("Please specify a kNurbsCurve")
        
def createTransforms(m_pIndices,m_parent):
    for i in range(len(m_pIndices)):
        m_transform = cmds.createNode( 'transform', n='point{}'.format(i), p=m_parent )
        cmds.setAttr("{}.translateX".format(m_transform),m_pIndices[i]["translate"][0])
        cmds.setAttr("{}.translateY".format(m_transform),m_pIndices[i]["translate"][1])
        cmds.setAttr("{}.translateZ".format(m_transform),m_pIndices[i]["translate"][2])
        cmds.setAttr("{}.rotateX".format(m_transform),m_pIndices[i]["rotate"][0])
        cmds.setAttr("{}.rotateY".format(m_transform),m_pIndices[i]["rotate"][1])
        cmds.setAttr("{}.rotateZ".format(m_transform),m_pIndices[i]["rotate"][2])
        cmds.setAttr("{}.displayLocalAxis".format(m_transform),1)
        cmds.setAttr("{}.displayHandle".format(m_transform),1)

def getRotationsEff(m_pIndices,m_pIndices2):
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
        m_tangent = OpenMaya.MVector( (m_pCurr-m_pTang) )
        m_tangent.normalize()
        # calculate up vector
        m_up = m_tangent^m_vector
        m_up.normalize()
        #----------------------------------------
        m_quat   = OpenMaya.MQuaternion(m_up, m_vector)
        #m_quat.conjugateIt()
        m_angles = m_quat.asEulerRotation()
        m_pIndices[i]["rotate"] = [math.degrees(m_angles.x), math.degrees(m_angles.y), math.degrees(m_angles.z)]
        
def getRotationsEff2(m_pIndices,m_pIndices2):
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
        m_list = [  m_tangent.x,m_tangent.y,m_tangent.z,0.0,
                    m_up.x,m_up.y,m_up.z,0.0,
                    m_vector.x,m_vector.y,m_vector.z,0.0,
                    0.0,0.0,0.0,0.0]
        m_util.createMatrixFromList(m_list,m_matrix)
        m_matrixTr = OpenMaya.MTransformationMatrix(m_matrix)
        #
        # THIS PART IS IMPORTANT
        #
        # makes quaternion "compatible" with previous point quaternion
        # in order to make use of linear interpolation in the shader 
        #        
        m_quat = m_matrixTr.rotation()
        m_angles = m_quat.asEulerRotation()
        m_eulerRot = m_matrixTr.eulerRotation()
        m_angles = [math.degrees(m_eulerRot.x), math.degrees(m_eulerRot.y), math.degrees(m_eulerRot.z)]
        m_bool = False
        if (0==i):
            m_prev = m_quat
            #
            #m_prev_eulerRot = m_eulerRot
            #
        if (i>0):
            m_curr = m_quat
            #
            # I use quaternions to find out correct "compatible" rotations
            # but also can be used build-in maya api function called closestSolution() from MEulerRotation class
            # I commented this code here, for a future use 
            #
            #m_curr_eulerRot = m_eulerRot
            #m_closest_eulerRot = m_curr_eulerRot.closestSolution(m_prev_eulerRot)
            #print(i, math.degrees(m_closest_eulerRot.x), math.degrees(m_closest_eulerRot.y), math.degrees(m_closest_eulerRot.z))
            #
            m_bool, m_quat = needs_to_be_negated(m_curr,m_prev)
            if m_bool:
                # this quaternion needs to be negated
                m_eulerRotInv = m_eulerRot.alternateSolution() # basically negated version 
                m_angles = [math.degrees(m_eulerRotInv.x), math.degrees(m_eulerRotInv.y), math.degrees(m_eulerRotInv.z)]
            m_prev = m_quat
            #
            #m_prev_eulerRot = m_eulerRot
            #
        m_pIndices[i]["rotate"] = m_angles
        
def needs_to_be_negated(m_curr,m_prev):
    # m_curr, m_prev should be OpenMaya.MQuaternion()
    # Return tuple(True, m_quat_negated) or tuple(False, m_quat_orig)
    m_quat = OpenMaya.MQuaternion()
    m_quat = m_curr
    m_curr_negate = OpenMaya.MQuaternion()
    m_curr_negate.x = m_curr.x
    m_curr_negate.y = m_curr.y
    m_curr_negate.z = m_curr.z
    m_curr_negate.w = m_curr.w
    # negated version of current Quaternion
    m_curr_negate.negateIt()
    m_substr = m_curr - m_prev
    # negated version of substracted Quaternion current from previous 
    m_substr.negateIt()
    m_substr_negated = m_curr_negate - m_prev
    # negated version of substracted Quaternion current_negated from previous 
    m_substr_negated.negateIt()
    # find square len of them, enough for comparison
    m_substr_len_squared = m_substr.x*m_substr.x + m_substr.y*m_substr.y + m_substr.z*m_substr.z + m_substr.w*m_substr.w
    m_substr_negated_len_squared =  m_substr_negated.x*m_substr_negated.x + m_substr_negated.y*m_substr_negated.y + m_substr_negated.z*m_substr_negated.z + m_substr_negated.w*m_substr_negated.w
    if m_substr_negated_len_squared < m_substr_len_squared:
        # this quaternion needs to be negated
        m_quat = m_curr_negate
        return True, m_quat
    return False, m_quat

def getRotationsMP(m_pIndices):
    for i in range(len(m_pIndices)):
        m_pIndex = m_pIndices[i]
        m_vector = OpenMaya.MVector(0.0,0.0,0.0)
        if (0 == i):
            # first item
            m_p1 = m_pIndices[len(m_pIndices)-1]["point"]
            m_p2 = m_pIndices[i+1]["point"]
        elif( (len(m_pIndices)-1) == i):
            # last item
            m_p1 = m_pIndices[i-1]["point"]
            m_p2 = m_pIndices[0]["point"]
        else:
            m_p1 = m_pIndices[i-1]["point"]
            m_p2 = m_pIndices[i+1]["point"]
        m_vector = OpenMaya.MVector( (m_p1-m_p2) )
        m_vector.normalize()
        m_vectorZ = OpenMaya.MVector(0.0,0.0,-1.0)
        m_dot = m_vector*m_vectorZ;
        m_angle = math.degrees(math.acos(m_dot))
        # some extra fix
        if m_vector.y<0.0:
            m_angle = 360.0 - m_angle
        #if (m_angle<0.0):
        #    m_angle += 360.0
        #print(m_dot,m_angle,m_vector.x,m_vector.y,m_vector.z)
        if (0.0==round(m_angle)):
            m_angle = 360.0
        m_pIndices[i]["rotate"] = [m_angle,0.0,0.0]

def getFnNurbs(m_obj):
    m_path  = OpenMaya.MDagPath()
    if m_obj:
        if m_obj.hasFn( OpenMaya.MFn.kDagNode ):
            OpenMaya.MDagPath.getAPathTo( m_obj, m_path )
            if m_path.hasFn( OpenMaya.MFn.kNurbsCurve ):
                m_fnNurbs = OpenMaya.MFnNurbsCurve(m_path)
                return (m_path, m_fnNurbs)
    return (None, None)

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
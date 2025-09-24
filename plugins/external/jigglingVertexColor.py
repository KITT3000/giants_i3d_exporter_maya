#-----------------------------------------------------------------------------------
#              
#   INFO       saves object space (compressed) positions into vertex colors
#
#-----------------------------------------------------------------------------------
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import random as random

def applyVertexColors(m_path):
    m_transform = m_path.transform()
    m_fnTransform =  OpenMaya.MFnTransform(m_transform)
    m_tr = m_fnTransform.getTranslation(OpenMaya.MFn.kWorld)
    m_tr  /= 100.0 # make meters from centimetres 
    # print( "pivot original: {} {} {} ".format( m_tr.x,m_tr.y,m_tr.z))
    m_tr  /= 5.0 # the same value is used in vehicleShader.xml MESH_JIGGLING variation
    m_tr.x = 0.5 * m_tr.x + 0.5
    m_tr.y = 0.5 * m_tr.y + 0.5
    m_tr.z = 0.5 * m_tr.z + 0.5
    # print( "pivot compressed: {} {} {} ".format( m_tr.x,m_tr.y,m_tr.z))
    m_r = max(min(m_tr.x, 1.0), 0.0)
    m_g = max(min(m_tr.y, 1.0), 0.0)
    m_b = max(min(m_tr.z, 1.0), 0.0)
    m_a = random.random()
    cmds.polyColorPerVertex( m_path.fullPathName(), r = m_r, g = m_g, b = m_b, a = m_a, colorDisplayOption = True )
    print("{} set {} {} {} {}".format(m_path.fullPathName(),m_r,m_g,m_b,m_a))
    
def runOnSelection():
    m_list = OpenMaya.MSelectionList()     # create selectionList
    OpenMaya.MGlobal.getActiveSelectionList( m_list )
    m_listIt = OpenMaya.MItSelectionList( m_list ) 
    while not m_listIt.isDone():
        m_path        = OpenMaya.MDagPath()   # will hold a path to the selected object 
        m_component   = OpenMaya.MObject()    # will hold a list of selected components
        m_listIt.getDagPath( m_path, m_component )
        if ( m_path.hasFn( OpenMaya.MFn.kMesh ) ):
            applyVertexColors(m_path)
        m_listIt.next()
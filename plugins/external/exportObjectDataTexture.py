#-----------------------------------------------------------------------------------
#
#   SCRIPT      exportObjectDataTexture.py
#   AUTHORS     Evgen Zaitsev, Nicolas Wrobel
#
#   Exports dds array with position, orientation and scale data stored into the pixels of the texture
#
#   string i3D_objectDataFilePath             if not empty string -> export texture
#                                             path to the texture relative from mayafile
#   bool i3D_objectDataExportPosition         if True, export position
#   bool i3D_objectDataExportOrientation      if True, export orientation
#   bool i3D_objectDataExportScale            if True, export scale
#   bool i3D_objectDataHideFirstAndLastObject sets position.w to 0, used as visibility in the shader (apply before exporting data)
#   bool i3D_objectDataHierarchicalSetup      if True, number of poses is the number of children, the y axis is the number of children in each pose (objectSet)
#                                             (if not identical -> error), the x axis is the max number of children in each objectSet
#                                             missing x values in the texture are created by duplicating the last object value
#                                             expects following objects hierarchy (or similar) to be present:
#                                             array
#                                                 pose1
#                                                     y0
#                                                         x1, x2
#                                                     y1
#                                                         x1, x2, x3, x4
#                                                 pose2
#                                                     y0
#                                                         x1, x2, x3
#                                                     y1
#                                                         x1, x2, x3, x4
#                                             pose1.y0 and pose2.y0 will be extended (in export time) to match maximum size
#                                             pose1.y0 will get x3, x4 (x2 will be copied)
#                                             pose2.y0 will get x4 (x3 will be copied)
#
#   cmds.I3DExporterWriteTexture(filename, width, height, channels, arraySize, type, data)
#   channels:   1 OR 2 OR 4
#   arraySize:  0,1 OR >1
#   type:       "unorm" (0 - 255) or "half" (-32768.0 - 32767.0) or "float" (-1.17549e-38 - 3.40282e+38)
#   data:       array of doubles
#
#-----------------------------------------------------------------------------------
import ctypes
import struct
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import os
import math
import tempfile

def exportObjectDataTexture():
    processScene()

def processScene():
    m_shapeArrays = []
    # iterate over MDags
    m_iterator = OpenMaya.MItDag( OpenMaya.MItDag.kDepthFirst )
    while not m_iterator.isDone():
        m_obj   = m_iterator.currentItem()
        m_path  = OpenMaya.MDagPath()
        m_iterator.getPath(m_path)
        if ( (OpenMaya.MFn.kTransform == m_obj.apiType()) and isExported(m_obj) ):
            m_shapeArrays.append(shapeArray(m_obj))
        m_iterator.next()
    # =================================
    for m_shape in m_shapeArrays:
        m_shape.export()

class shapeArray(object):
    def __init__(self,m_obj):
        self.m_obj              = m_obj #OpenMaya.MObject()
        self.m_filepath         = ""
        self.m_x                = 1
        self.m_y                = 1
        self.m_z                = 1
        self.m_poseData         = []
        self.m_hierarchical     = False
        self.m_hideFirstAndLast = False
        self.m_exportPosition   = True
        self.m_exportOrient     = True
        self.m_exportScale      = False
        self.m_isValid          = True
        self.init()

    def init(self):
        self.m_path  = OpenMaya.MDagPath()
        self.m_objFn = OpenMaya.MFnDagNode( self.m_obj )
        OpenMaya.MDagPath.getAPathTo( self.m_obj, self.m_path )
        # filepath
        self.m_filepath         = getFilePath(getAttributeValue(self.m_obj,"i3D_objectDataFilePath"))
        self.m_hierarchical     = getAttributeValue(self.m_obj,"i3D_objectDataHierarchicalSetup",self.m_hierarchical)
        self.m_hideFirstAndLast = getAttributeValue(self.m_obj,"i3D_objectDataHideFirstAndLastObject",self.m_hideFirstAndLast)
        self.m_exportPosition   = getAttributeValue(self.m_obj,"i3D_objectDataExportPosition",self.m_exportPosition)
        self.m_exportOrient     = getAttributeValue(self.m_obj,"i3D_objectDataExportOrientation",self.m_exportOrient)
        self.m_exportScale      = getAttributeValue(self.m_obj,"i3D_objectDataExportScale",self.m_exportScale)

    def export(self):
        if (self.m_hierarchical):
            self.shapeArrayGetHierarchical()
            self.shapeArrayValidateAndAdjust()
        else:
            self.shapeArrayGetFlat()
        self.shapeArraysExport()

    def shapeArraysExport(self):
        if not self.m_isValid:
            print("Failed to Export Object Data Texture")
            return False
        m_dataList = []
        m_arrayTmp = []
        for z in range(len(self.m_poseData)):
            if (self.m_exportPosition):
                # =================================
                # position
                m_arrayTmp.append("position{}".format(z))
                for y in range(self.m_y-1,-1,-1):
                    for x in range(self.m_x):
                        #i = x + y*self.m_x
                        m_dataItem = self.m_poseData[z][y][x]
                        for m_channel in range(4):
                            m_dataList.append(m_dataItem["position"][m_channel])
            if (self.m_exportOrient):
                # =================================
                # orient
                m_arrayTmp.append("orient{}".format(z))
                for y in range(self.m_y-1,-1,-1):
                    for x in range(self.m_x):
                        m_dataItem = self.m_poseData[z][y][x]
                        for m_channel in range(4):
                            m_dataList.append(m_dataItem["orient"][m_channel])
            if (self.m_exportScale):
                # =================================
                # scale
                m_arrayTmp.append("scale{}".format(z))
                for y in range(self.m_y-1,-1,-1):
                    for x in range(self.m_x):
                        m_dataItem = self.m_poseData[z][y][x]
                        for m_channel in range(4):
                            m_dataList.append(m_dataItem["scale"][m_channel])
        m_arraySize = len(m_arrayTmp)
        try:
            cmds.I3DExporterWriteTexture(self.m_filepath, self.m_x, self.m_y, 4, m_arraySize, "half", m_dataList)
            print("Exported Object Data Texture: {} (z:{}, y:{}, x:{})".format(self.m_filepath, self.m_z,self.m_y,self.m_x))
        except:
            print("Failed to Export Object Data Texture: {}".format(self.m_filepath))

    def shapeArrayGetFlat(self):
        self.m_x = self.m_path.childCount()
        m_arrayX = []
        m_arrayY = []
        m_arrayZ = []
        # quaternionPrev needed for making it compatible with quaternionCurrent
        quaternionPrev = None
        for x in range(self.m_path.childCount()):
            m_x = self.m_path.child(x)
            m_dataItem = getDataItem(m_x)
            # make next quaternion compatible with previous quaternion
            if None != quaternionPrev:
                quaternionCurrent = m_dataItem["orient"]
                quaternionCurrent = makeQuaternionCompatible(quaternionCurrent,quaternionPrev)
                m_dataItem["orient"] = quaternionCurrent
            quaternionPrev = m_dataItem["orient"]
            #
            # sets position.w to 0, used as visibility in the shader (apply before exporting data)
            #
            if (self.m_hideFirstAndLast):
                if (0==x or self.m_path.childCount()-1 == x):
                    m_dataItem["position"][3] = 0.0
            #
            m_arrayX.append(m_dataItem)
        m_arrayY.append(m_arrayX)
        m_arrayZ.append(m_arrayY)
        self.m_poseData = m_arrayZ

    def shapeArrayGetHierarchical(self):
        # calculates x, y, z dimentions of the texture
        m_arrayX = []
        m_arrayY = []
        m_arrayZ = []
        #
        # z dimention of the texture
        self.m_z = self.m_path.childCount()
        for z in range(self.m_path.childCount()):
            m_pose     = self.m_path.child(z)
            m_posePath = OpenMaya.MDagPath()
            OpenMaya.MDagPath.getAPathTo( m_pose, m_posePath )
            #
            # y dimention of the texture
            self.m_x = 0
            self.m_y = m_posePath.childCount()
            m_arrayY = []
            for y in range(m_posePath.childCount()):
                m_y     = m_posePath.child(y)
                m_yPath = OpenMaya.MDagPath()
                OpenMaya.MDagPath.getAPathTo( m_y, m_yPath )
                #
                # x dimention of the texture
                # defined by the longest
                if self.m_x <= m_yPath.childCount():
                    self.m_x = m_yPath.childCount()
                m_arrayX = []
                # quaternionPrev needed for making it compatible with quaternionCurrent
                quaternionPrev = None
                for x in range(m_yPath.childCount()):
                    m_x = m_yPath.child(x)
                    '''
                    m_xPath = OpenMaya.MDagPath()
                    OpenMaya.MDagPath.getAPathTo( m_x, m_xPath )
                    print(m_xPath.fullPathName())
                    '''
                    m_dataItem = getDataItem(m_x)
                    # make next quaternion compatible with previous quaternion
                    if None != quaternionPrev:
                        quaternionCurrent = m_dataItem["orient"]
                        quaternionCurrent = makeQuaternionCompatible(quaternionCurrent,quaternionPrev)
                        m_dataItem["orient"] = quaternionCurrent
                    quaternionPrev = m_dataItem["orient"]
                    #
                    # sets position.w to 0, used as visibility in the shader (apply before exporting data)
                    #
                    if (self.m_hideFirstAndLast):
                        if (0==x or m_yPath.childCount()-1 == x):
                            m_dataItem["position"][3] = 0.0
                    #
                    m_arrayX.append(m_dataItem)
                m_arrayY.append(m_arrayX)
                #print(m_yPath.fullPathName())
            m_arrayZ.append(m_arrayY)
        self.m_poseData = m_arrayZ

    def shapeArrayValidateAndAdjust(self):
        if (0 == len(self.m_poseData)):
            print("array has no z")
            self.m_isValid = False
            return self.m_isValid
        # validate y dimention of the texture
        for z in range(len(self.m_poseData)):
            if (0==len(self.m_poseData[z])):
                print("z:{} has no y".format(z))
                self.m_isValid = False
                return self.m_isValid
            if self.m_y != len(self.m_poseData[z]):
                print("y:{} != pose{}.y size:{}".format(self.m_y,z,len(self.m_poseData[z])))
                self.m_isValid = False
                return self.m_isValid
            for y in range(len(self.m_poseData[z])):
                if (0 == len(self.m_poseData[z][y])):
                    print("z:{} y:{} has no x".format(z,y))
                    self.m_isValid = False
                    return self.m_isValid
                #
                # missing x values in the texture are created by duplicating the last object value
                #
                m_last = self.m_poseData[z][y][-1]
                if len(self.m_poseData[z][y]) < self.m_x:
                    for m in range(self.m_x-len(self.m_poseData[z][y])):
                        self.m_poseData[z][y].append(m_last)
                #
                #print(len(self.m_poseData[z][y]),self.m_x)

    def _str_(self):
        #m_str += "{}\n".format(self.m_filepath)
        m_str = "z:{} y:{} x:{}".format(self.m_z,self.m_y,self.m_x)
        return m_str

    def __str__(self):
        return self._str_()

    def __str__(self):
        return self._str_()

def getDataItem(m_obj):
    m_poisition = getPosition(m_obj)
    m_orient    = getOrient(m_obj)
    m_scale     = getScale(m_obj)
    m_dataItem = {}
    m_dataItem["position"] = m_poisition
    m_dataItem["orient"]   = m_orient
    m_dataItem["scale"]    = m_scale
    return m_dataItem

def getPosition(m_obj):
    m_pos = [0.0,0.0,0.0,1.0]
    m_objFn = OpenMaya.MFnDagNode( m_obj )
    if ('m' == cmds.currentUnit( query=True, linear=True )):
        unitScale = 1.0
    else:
        unitScale = 0.01
    m_pos[0] = unitScale*cmds.getAttr( "{}.translateX".format(m_objFn.fullPathName()))
    m_pos[1] = unitScale*cmds.getAttr( "{}.translateY".format(m_objFn.fullPathName()))
    m_pos[2] = unitScale*cmds.getAttr( "{}.translateZ".format(m_objFn.fullPathName()))
    return m_pos

def getOrient(m_obj):
    m_objFn = OpenMaya.MFnDagNode( m_obj )
    m_rx = cmds.getAttr( "{}.rotateX".format(m_objFn.fullPathName()))
    m_ry = cmds.getAttr( "{}.rotateY".format(m_objFn.fullPathName()))
    m_rz = cmds.getAttr( "{}.rotateZ".format(m_objFn.fullPathName()))
    return eulerToQuaternion(math.radians(m_rz),math.radians(m_ry),math.radians(m_rx))

def getScale(m_obj):
    m_scale = [1.0,1.0,1.0,1.0]
    m_objFn = OpenMaya.MFnDagNode( m_obj )
    m_scale[0] = cmds.getAttr( "{}.scaleX".format(m_objFn.fullPathName()))
    m_scale[1] = cmds.getAttr( "{}.scaleY".format(m_objFn.fullPathName()))
    m_scale[2] = cmds.getAttr( "{}.scaleZ".format(m_objFn.fullPathName()))
    return m_scale

def eulerToQuaternion(rx,ry,rz):
    cy = math.cos(rx * 0.5);
    sy = math.sin(rx * 0.5);
    cp = math.cos(ry * 0.5);
    sp = math.sin(ry * 0.5);
    cr = math.cos(rz * 0.5);
    sr = math.sin(rz * 0.5);
    q = [0.0,0.0,0.0,0.0];
    q[3] = cy * cp * cr + sy * sp * sr;
    q[0] = cy * cp * sr - sy * sp * cr;
    q[1] = sy * cp * sr + cy * sp * cr;
    q[2] = sy * cp * cr - cy * sp * sr;
    return q;

def makeQuaternionCompatible(quaternionCurrent,quaternionPrev):
    result = quaternionCurrent
    dot_product = (
        result[0] * quaternionPrev[0] +
        result[1] * quaternionPrev[1] +
        result[2] * quaternionPrev[2] +
        result[3] * quaternionPrev[3]
    )
    if dot_product < 0:
        result[0] *= -1.0
        result[1] *= -1.0
        result[2] *= -1.0
        result[3] *= -1.0
    return result

def isAttributeExists(m_obj,m_attrStr):
    m_fnDep = OpenMaya.MFnDependencyNode( m_obj )
    if ( m_fnDep.hasAttribute( m_attrStr ) ):
        return True
    return False

def getAttributeValue(m_obj,m_attrStr,m_default=None):
    m_fnDep = OpenMaya.MFnDependencyNode( m_obj )
    m_objFn = OpenMaya.MFnDagNode( m_obj )
    if ( m_fnDep.hasAttribute( m_attrStr ) ):
        m_str = "{}.{}".format(m_objFn.fullPathName(),m_attrStr)
        #print(m_attrStr,cmds.getAttr(m_str))
        return (cmds.getAttr(m_str))
    return m_default

def isExported( m_obj ):
    m_fnDep = OpenMaya.MFnDependencyNode( m_obj )
    if (isAttributeExists(m_obj,"i3D_objectDataFilePath")):
        if "" != getAttributeValue(m_obj,"i3D_objectDataFilePath"):
            return True
    return False

def getFilePath(m_str):
    result = ""
    mayaFile = cmds.file(q=True,sn=True)
    mayaFile = os.path.dirname(mayaFile)
    result = "{}/{}".format(mayaFile,m_str)
    result = os.path.abspath(result)
    return result
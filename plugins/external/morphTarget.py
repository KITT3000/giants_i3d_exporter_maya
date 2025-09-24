#-----------------------------------------------------------------------------------
#   
#   Bakes difference between source and target mesh into vertexColor (0..1 normalized). Used with some shaders
#
#   LIMITS          distance between morphs should be less than m_compression meters  [ -m_compression .. m_compression ]
#-----------------------------------------------------------------------------------
import maya.OpenMaya, maya.cmds
m_morphTargetWinGuiID = 'w_morphTargetGuiID'

class morphTargetWin():
    """
    Main UI window class definition
    """
    m_sourceDagPath = maya.OpenMaya.MDagPath() 
    m_targetDagPath = maya.OpenMaya.MDagPath()
    m_compression   = 1.0
    m_maxDistance   = 0.0
    
    def __init__(self):
        """
        Initialize window
        """
        # delete ui window if opened
        if maya.cmds.window( m_morphTargetWinGuiID, exists = True ):
            maya.cmds.deleteUI( m_morphTargetWinGuiID, window = True )
        # create the window
        self.m_window = maya.cmds.window( m_morphTargetWinGuiID, title = 'morphTarget', width = 150, height = 40 )
        self.m_formLayout = maya.cmds.formLayout( parent = self.m_window ) 
        # ---               
        self.m_textSource      = maya.cmds.text( parent = self.m_formLayout, label = 'SOURCE', align = 'right', width = 80, height = 20 )
        self.m_textFieldSource = maya.cmds.textField( parent = self.m_formLayout, 
                                            editable = False,
                                            width = 200,
                                            height = 20,
                                            annotation = 'Load source mesh')
        self.m_buttonSource    = maya.cmds.button( parent = self.m_formLayout,
                                                  label = "load",
                                                  annotation = "Load source mesh",
                                                  height = 20,
                                                  width = 80,
                                                  command = lambda *args: self.uiCallback( "m_buttonSource", args ) )
        self.m_textTarget       = maya.cmds.text( parent = self.m_formLayout, label = 'TARGET', align = 'right', width = 80, height = 20 )
        self.m_textFieldTarget  = maya.cmds.textField( parent = self.m_formLayout, 
                                            editable = False,
                                            width = 200,
                                            height = 20,
                                            annotation = 'Load target mesh')
        self.m_buttonTarget     = maya.cmds.button( parent = self.m_formLayout,
                                                  label = "load",
                                                  annotation = "Load target mesh",
                                                  height = 20,
                                                  width = 80,
                                                  command = lambda *args: self.uiCallback( "m_buttonTarget", args ) )
        self.m_textCompression     = maya.cmds.text( parent = self.m_formLayout, label = 'Compression', align = 'right', width = 80, height = 20 )
        self.m_floatFieldCompression = maya.cmds.floatField( parent = self.m_formLayout, 
                                            editable = True,
                                            width  = 60,
                                            height = 20,
                                            value  = 1.0, minValue = 0, maxValue = 100, step = 1,
                                            changeCommand = lambda *args: self.uiCallback( "m_floatFieldCompression", args ))
        self.m_textMaxDist        =  maya.cmds.text( parent = self.m_formLayout, label = 'Max Distance', align = 'right', width = 80, height = 20 )
        self.m_floatFieldMaxDist  =  maya.cmds.floatField( parent = self.m_formLayout, 
                                            editable = False,
                                            width  = 60,
                                            height = 20,
                                            value  = 0.0 )
        self.m_buttonRun        = maya.cmds.button( parent = self.m_formLayout,
                                                  label = "Run",
                                                  annotation = "Run calculation",
                                                  height = 20,
                                                  width = 80,
                                                  command = lambda *args: self.uiCallback( "m_buttonRun", args ) )
                                                  
        maya.cmds.formLayout( self.m_formLayout, edit = True,
                    attachForm =    [    
                                         ( self.m_textSource,          'top',    2 ), 
                                         ( self.m_textSource,          'left',   2 ),
                                         ( self.m_textFieldSource,     'top',    2 ),
                                         ( self.m_buttonSource,        'top',    2 ),
                                         ( self.m_buttonSource,        'right',  2 ),
                                         ( self.m_textTarget,          'left',   2 ),
                                         ( self.m_buttonTarget,        'right',  2 ),
                                         ( self.m_buttonRun,           'left',   2 ),
                                         ( self.m_textCompression,     'left',   2 ),
                                    ], 
                    attachControl = [
                                         ( self.m_textFieldSource,            'left',  2, self.m_textSource      ), 
                                         ( self.m_textFieldSource,            'right', 2, self.m_buttonSource    ), 
                                         ( self.m_textTarget,                 'top',   2, self.m_textSource      ),
                                         ( self.m_textFieldTarget,            'top',   2, self.m_textFieldSource ),
                                         ( self.m_textFieldTarget,            'left',  2, self.m_textTarget      ),
                                         ( self.m_textFieldTarget,            'right', 2, self.m_buttonTarget    ),
                                         ( self.m_buttonTarget,               'top',   2, self.m_buttonSource    ),
                                         ( self.m_textCompression,            'top',   2, self.m_textTarget      ),
                                         ( self.m_buttonRun,                  'top',   2, self.m_textCompression ),
                                         ( self.m_floatFieldCompression,      'top',   2, self.m_textFieldTarget ),
                                         ( self.m_floatFieldCompression,      'left',  2, self.m_textCompression ),
                                         ( self.m_textMaxDist,                'left',  2, self.m_floatFieldCompression ),
                                         ( self.m_textMaxDist,                'top',   2, self.m_textFieldTarget    ),
                                         ( self.m_floatFieldMaxDist,          'left',  2, self.m_textMaxDist ),
                                         ( self.m_floatFieldMaxDist,          'top',   2, self.m_textFieldTarget    ),
                                    ],
                    attachNone =    [    
                                         ( self.m_textSource,             'bottom' ),
                                         ( self.m_textSource,             'right'  ),
                                         ( self.m_textTarget,             'bottom' ),
                                         ( self.m_textTarget,             'right'  ),
                                         ( self.m_textFieldSource,        'bottom' ),
                                         ( self.m_buttonSource,           'left'   ),
                                         ( self.m_buttonSource,           'bottom' ),
                                         ( self.m_textFieldTarget,        'bottom' ),
                                         ( self.m_buttonTarget,           'left'   ),
                                         ( self.m_buttonTarget,           'bottom' ),
                                         ( self.m_textCompression,        'bottom' ),
                                         ( self.m_textCompression,        'right'  ),
                                         ( self.m_buttonRun,              'bottom' ),
                                         ( self.m_buttonRun,              'right'  ),
                                         ( self.m_floatFieldCompression,  'bottom' ),
                                         ( self.m_floatFieldCompression,  'right'  ),
                                         ( self.m_textMaxDist,            'bottom' ),
                                         ( self.m_textMaxDist,            'right'  ),
                                         ( self.m_floatFieldMaxDist,      'bottom' ),
                                         ( self.m_floatFieldMaxDist,      'right'  ),
                                    ])             
        # ---                                                      
        maya.cmds.showWindow( m_morphTargetWinGuiID )   
        self.uiRefresh()                               

    def doButtonRun( self ):
        """
        Calculate morphTarget info for the shader
        """
        if not ( self.m_sourceDagPath.isValid() ): maya.OpenMaya.MGlobal.displayWarning("Define source object please!"); return
        if not ( self.m_targetDagPath.isValid() ): maya.OpenMaya.MGlobal.displayWarning("Define target object please!"); return
        m_sourceMfnMesh = maya.OpenMaya.MFnMesh( self.m_sourceDagPath )
        m_targetMfnMesh = maya.OpenMaya.MFnMesh( self.m_targetDagPath )
        if ( m_sourceMfnMesh.numVertices() != m_targetMfnMesh.numVertices() ): maya.OpenMaya.MGlobal.displayWarning("Vertex count is not equal!"); return
        
        self.m_maxDistance = 0.0
        m_sourceMeshIter = maya.OpenMaya.MItMeshVertex( self.m_sourceDagPath )
                 
        m_sourceMeshIter.reset()
        m_sourcePoint       = maya.OpenMaya.MPoint()
        m_targetPoint       = maya.OpenMaya.MPoint()
        m_differencePoint   = maya.OpenMaya.MPoint()
        
        m_vertexColours  = maya.OpenMaya.MColorArray()
        m_vertexIndecies = maya.OpenMaya.MIntArray()
        m_color          = maya.OpenMaya.MColor( 0.0, 0.0, 0.0, 1.0 )
        
        while not m_sourceMeshIter.isDone():
            m_sourcePoint = maya.OpenMaya.MPoint( m_sourceMeshIter.position( maya.OpenMaya.MSpace.kObject ) )
            m_targetMfnMesh.getPoint( m_sourceMeshIter.index(), m_targetPoint, maya.OpenMaya.MSpace.kObject )
            m_sourcePoint /= 100.0 # make meters from centimetres 
            m_targetPoint /= 100.0 
            #------
            m_differencePoint  = m_targetPoint - m_sourcePoint;
            
            m_distance         = m_sourcePoint.distanceTo( m_targetPoint )
            if ( m_distance > self.m_maxDistance ): self.m_maxDistance = m_distance 
            
            m_differencePoint /= self.m_compression  #compress [-1..1] to [-m_compression..m_compression]
            m_differencePoint.x +=1.0; m_differencePoint.x /= 2.0; # compress [-1..1] to [0..1]
            m_differencePoint.y +=1.0; m_differencePoint.y /= 2.0; 
            m_differencePoint.z +=1.0; m_differencePoint.z /= 2.0; 
            #------
            m_vertexIndecies.append( m_sourceMeshIter.index() )
            m_color.r = max(min(m_differencePoint.x, 1.0), 0.0)
            m_color.g = max(min(m_differencePoint.y, 1.0), 0.0)
            m_color.b = max(min(m_differencePoint.z, 1.0), 0.0)
            m_color.w = 1.0
            m_vertexColours.append( m_color )
            #------
            m_sourceMeshIter.next()
        
        m_sourceMfnMesh.setVertexColors( m_vertexColours, m_vertexIndecies ) # write distance between morphs
        self.uiRefresh()
        
    def uiRefresh( self ):
        """
        Refresh UI
        """
        maya.cmds.textField( self.m_textFieldSource, edit = True, fileName = str( self.m_sourceDagPath.fullPathName() ) )
        maya.cmds.textField( self.m_textFieldTarget, edit = True, fileName = str( self.m_targetDagPath.fullPathName() ) )
        maya.cmds.floatField( self.m_floatFieldCompression, edit = True,    value = self.m_compression )
        maya.cmds.floatField( self.m_floatFieldMaxDist,     edit = True,    value = self.m_maxDistance )
        
    def uiCallback( self, *args ):
        """
        Callback for UI
        """   
        m_input = args[0]
        if ( 'm_buttonSource' == m_input ):
            m_selList = maya.OpenMaya.MSelectionList()
            maya.OpenMaya.MGlobal.getActiveSelectionList( m_selList )
            m_selList.getDagPath( 0, self.m_sourceDagPath ) if ( 0 != m_selList.length() ) else maya.OpenMaya.MGlobal.displayWarning("Select source object please!")
        if ( 'm_buttonTarget' == m_input ):
            m_selList = maya.OpenMaya.MSelectionList()
            maya.OpenMaya.MGlobal.getActiveSelectionList( m_selList )
            m_selList.getDagPath( 0, self.m_targetDagPath ) if ( 0 != m_selList.length() ) else maya.OpenMaya.MGlobal.displayWarning("Select target object please!")
        if ( 'm_buttonRun' == m_input ):
            self.doButtonRun()
        if ( 'm_floatFieldCompression' == m_input ):
            self.m_compression = float(maya.cmds.floatField( self.m_floatFieldCompression, query = True, value = True ) )
        self.uiRefresh()
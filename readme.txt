GIANTS Maya i3d exporter plugins
================================

Installation
------------

Refer to:
http://gdn.giants-software.com/documentation_exporter.php#exporter_maya_installation
for installation details

Change log
----------

10.0.0 (21.11.2024)
- Initial release for Farming Simulator 25

9.0.4
-----------------
- Added support for 32bit object masks
- Added bitmask dialog for object masks with some annotations used in Farming Simulator 22
- Added material attributes reflectionMapShapesObjectMask and reflectionMapLightsObjectMask to define what reflective materials should reflect
- Added support for double sided shape flag
- Receive and casts shadows flags are now settable from the exporter UI
- Added option to set receive and casts shadows per instance in case multiple instances use the same shape/geometry
- Added support for the rendered in viewports flag
- Added support for distance blending flag
- Added support for lod blending flag
- Fixed manual convex decomposition for split shape collision

9.0.3 (11.05.2022)
------------------
- Added support for Maya 2022 and 2023
- Improved collision mesh creation for split shapes (trees)
- Added support to define manual convex decomposition for split shape collision (first child of a split shape can be a transform group called "collisions" containing all the invidiual collision shapes)
- Changed default clip distance for "interiorScreenLight" lights to 20
- Added "tipCollisionWall" to placeable skeleton that has the "collisionHeight" set to 4

9.0.1 (26.11.2021)
------------------
- Added hardware instancing support for generic mesh types
- Added automatic computation of uvDensity, used by texture streaming
- Nodes with names ending in "_ignore" won't be exported
- Added new custom attribute i3D_mergeChildren. When set all children with meshes will be merged in one shape.
- Added two functions in I3DExporter20XX-x64.mll writeDDS() and mergeDDS() to write textures with translate, rotation and scaling information for merged children.
- Merge children has now 3 options freeze translation, freeze rotation and freeze scaling
- Parameter -baseGameShaderPrefix removed. Shaders defined without prefix(path) work the same way as prefixed with "./"
- Fixed exporting the same referenced file multiple times in files section of .i3d
- Material export changed. Attributes cosPower and ambientColor removed. Attribute specularColor only exported if there is no glossMap and either a blinn or phong single color material
- Added a warning if shape file size exceeds the console limit
- Fixed merged children to be able to override bounding volume with custom node using i3d_boundingVolume attribute
- Added navMesh mask (like object mask)

9.0.0 (28.02.2019)
------------------
- Added Merge Group Root Node support for transform groups

8.0.0 (04.10.2018)
------------------
- Added Maya 2018 support


7.0.1 (20.07.2017)
------------------
 - Added Maya 2017 support
 - Added "CPU Mesh" flag
 - Fixed display of shader parameters on 1080p monitors
 - Added "Ignore Bind Poses" option
 - Removed trigger flag from "Trigger - ExactFillRootNode" profile
 - Added support for euler rotation orders other than XYZ

7.0.0 (23.07.2016)
------------------
 - Converted exporter to python
 - Added support for binary animation files
 - Added support for physics cooking
 - Added support for merge groups
 - Skinned meshes are no longer required to be below their binded skeleton in the outliner
 - Added support for custom bounding volumes
 - Added support for custom split uvs

6.0.3 (08.10.2015)
------------------
 - Added Maya 2016 support
 - Made gui dockable
 - Added outliner skeleton creation tools
 - Improved exporting speed with large meshes
 - Fixed bounding volume calculation

6.0.2 (27.10.2014)
------------------
 - Added full Unicode support

6.0.1 (17.10.2014)
------------------
 - Minor fixes

6.0.0 (04.10.2014)
------------------
 - Added decal layer attribute
 - Fixed i3d corruption when exporting shapes with invalid materials

5.5.0 Beta (28.04.2014)
-----------------------
 - Added Maya 2015 support
 - Added automatic plugin installer

5.0.4 (19.07.2013)
------------------
 - Added support for binary shape format

5.0.3 (06.05.2013)
------------------
 - Added Maya 2014 support

5.0.2 (08.04.2013)
------------------
- Added Maya 64 bit support
- Fixed rare bug with skinned meshes

5.0.1 (10.09.2012)
------------------
- Added Maya 2013 support
- Added linear/angular damping
- Changed save bounding volumes and save optimized geometry
- Removed old mesh format
- Changed icon to match with 2011+ color theme
- Fixed bad chars in user attributes
- Fixed extra parent in relative path for files that are directly in one of the parent folders
- Fixed exporter crash


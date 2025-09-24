#
# I3DExportHandler
# Root class to handle the complete export process including validation and xml update
#
# @created 24/01/2024
# @author Stefan Maurus
#
# Copyright (C) GIANTS Software GmbH, Confidential, All Rights Reserved.
#

import maya.cmds as cmds

import datetime
import traceback
import re
import os
import io

import I3DExporter
import I3DUtils
import I3DValidation
import I3DExport

try:
    reload(I3DUtils)
    reload(I3DValidation)
    reload(I3DExport)
except NameError:
    from importlib import reload
    reload(I3DUtils)
    reload(I3DValidation)
    reload(I3DExport)


class I3DExportHandler:
    WINDOW_ID = "EXPORT_PROGRESS_WINDOW"

    def __init__(self):
        self.validationDuration = 0
        self.exportDuration = 0
        self.xmlExportDuration = 0
        self.timestamp = ""

        self.progress = 0
        self.progressSteps = 1

        self.export = I3DExport.I3DExport(self)
        self.validation = I3DValidation.I3DValidation(self)

    def setOption(self, optionName, value):
        self.export.setOption(optionName, value)

    def __generateWindow(self):
        if cmds.window(self.WINDOW_ID, exists=True):
            cmds.deleteUI(self.WINDOW_ID)

        UI_WIDTH = 300
        UI_HEIGHT = 70

        topLeftCorner = cmds.window(I3DExporter.UI_CONTROL_WINDOW, q=True, topLeftCorner=True)
        topLeftCorner[0] = topLeftCorner[0] + 500
        topLeftCorner[1] = topLeftCorner[1] + 80

        if cmds.windowPref(self.WINDOW_ID, exists=True):
            cmds.windowPref(self.WINDOW_ID, edit=True, widthHeight=(UI_WIDTH, UI_HEIGHT), topLeftCorner=topLeftCorner)

        self.window = cmds.window(self.WINDOW_ID, title="Export...", width=UI_WIDTH, height=UI_HEIGHT, sizeable=False, topLeftCorner=topLeftCorner)
        layout = cmds.columnLayout()

        self.progressBar = cmds.progressBar(parent=layout, maxValue=1000, width=UI_WIDTH - 10)

        self.progressCheckboxes = cmds.checkBoxGrp(parent=layout, numberOfCheckBoxes=3, labelArray3=["XML Update", "Export", "Validation"], editable=False)

        self.progressText = cmds.text(parent=layout, width=UI_WIDTH - 10, label="Progress...", )

        cmds.showWindow(self.window)

    def __closeWindow(self):
        if cmds.window(self.WINDOW_ID, exists=True):
            cmds.deleteUI(self.WINDOW_ID)

    def updateProgress(self, text, steps=1):
        self.progress = self.progress + steps
        cmds.progressBar(self.progressBar, edit=True, progress=int(min(self.progress / self.progressSteps, 1) * 1000))
        cmds.text(self.progressText, edit=True, label=text)

    def addProgressSteps(self, numSteps):
        self.progressSteps = self.progressSteps + numSteps

    def execute(self, validation=True, export=True, updateXML=False, xmlFilename=""):
        if updateXML:
            self.addProgressSteps(1)

        self.__generateWindow()
        cmds.checkBoxGrp(self.progressCheckboxes, edit=True, enable1=updateXML)
        cmds.checkBoxGrp(self.progressCheckboxes, edit=True, enable2=export)
        cmds.checkBoxGrp(self.progressCheckboxes, edit=True, enable3=validation)

        I3DExporter.I3DClearErrors()

        cmds.waitCursor(state=True)

        try:
            if updateXML:
                start = datetime.datetime.now()
                self.updateProgress("Update XML...")
                self.__updateXML(xmlFilename)
                self.xmlExportDuration = (datetime.datetime.now() - start).total_seconds()

            cmds.checkBoxGrp(self.progressCheckboxes, edit=True, valueArray3=[updateXML, False, False])

            if export:
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, 'Export:')

                start = datetime.datetime.now()
                I3DExporter.pluginEvent("onPreExport")
                self.export.doExport()
                I3DExporter.pluginEvent("onPostExport")
                self.exportDuration = (datetime.datetime.now() - start).total_seconds()

            cmds.checkBoxGrp(self.progressCheckboxes, edit=True, valueArray3=[updateXML, export, False])

            if validation:
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, 'Checking for errors:')

                start = datetime.datetime.now()
                self.validation.setXMLFilename(xmlFilename)
                I3DExporter.pluginEvent("onPreValidate")
                self.validation.doValidate()
                I3DExporter.pluginEvent("onPostValidate")
                self.validationDuration = (datetime.datetime.now() - start).total_seconds()

            cmds.checkBoxGrp(self.progressCheckboxes, edit=True, valueArray3=[updateXML, export, validation])

        except Exception as err:
            print(err)
            print(traceback.format_exc())
            cmds.waitCursor(state=False)
            self.__closeWindow()
            return

        self.timestamp = datetime.datetime.now().strftime("%d %b %Y %H:%M")

        actionName = "error check"
        if export:
            actionName = "export"

        numWarnings, numErrors = self.export.warningCount + self.validation.warningCount, self.export.errorCount + self.validation.errorCount

        statTexts = []
        if export:
            statTexts.append("Export: %.3fsec" % self.exportDuration)
        if validation:
            statTexts.append("Validation: %.3fsec" % self.validationDuration)
        if updateXML:
            statTexts.append("XML Update: %.3fsec" % self.xmlExportDuration)
        statTexts.append("Date: %s" % self.timestamp)

        text = ""
        for statText in statTexts:
            if text == "":
                text += statText
            else:
                text += " | " + statText

        I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, "")
        I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, "Time: " + text)
        I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, "")

        if numErrors == 0:
            if numWarnings == 0:
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, "Successfully finished %s (%d objects, species: %s)" % (actionName, self.validation.objectCount, self.validation.objectSpecies))
            else:
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, "Successfully finished %s (%d objects, species: %s) with %d warnings" % (actionName, self.validation.objectCount, self.validation.objectSpecies, numWarnings))
        else:
            I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, "Finished %s (%d objects, species: %s) with %d errors and %d warnings" % (actionName, self.validation.objectCount, self.validation.objectSpecies, numErrors, numWarnings))

        cmds.waitCursor(state=False)
        self.__closeWindow()

    def __updateXML(self, xmlFilename):
        if xmlFilename == "":
            I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_INFO, 'No config xml file set!')
            return

        xmlFiles = xmlFilename.split(';')
        for xmlFile in xmlFiles:
            mayaFilePath = str(os.path.dirname(cmds.file(q=True, sn=True)).replace('\\', '/'))
            xmlFile = I3DUtils.getMergePaths(mayaFilePath, xmlFile)

            if not os.path.isfile(xmlFile):
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_WARNING, 'Could not find xml file! (%s)' % xmlFile)
                return

            file = io.open(xmlFile, 'r', encoding="utf-8")
            if file is None:
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_WARNING, 'Could not find xml file! (%s)' % xmlFile)
                return

            lines = file.readlines()
            file.close()
            newLines = self.__removeI3dMapping(lines)

            rootTag = None
            try:
                from xml.etree.ElementTree import parse
                tree = parse(xmlFile)
                rootTag = tree.getroot().tag
            except Exception:
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_WARNING, 'Invalid xml file! (%s)' % xmlFile)

            endRootTag = 0
            found = False
            for line in newLines:
                endRootTag = endRootTag + 1
                if len(re.findall('</vehicle>', line)) > 0 or len(re.findall('</placeable>', line)) > 0 or (rootTag is not None and len(re.findall('</' + rootTag + '>', line)) > 0):
                    found = True
                    break

            if found:
                i3dMappings = []
                self.__addI3dMapping(i3dMappings, None)

                if len(i3dMappings) > 0:
                    i3dMappings.insert(0, '    <i3dMappings>')
                    i3dMappings.append('    </i3dMappings>')

                    for i in range(len(i3dMappings) - 1, -1, -1):
                        mapping = i3dMappings[i]
                        newLines.insert(endRootTag - 1, mapping)
                    newLines.append('')  # trailing empty line

                    file = io.open(xmlFile, 'w', encoding="utf-8", newline='\r\n')
                    file.write('\n'.join(newLines))  # unified CRLF linebreak is added through setting for 'file'
                    file.close()

                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_NONE, 'Updated xml config file (%s)' % (xmlFile))
            else:
                I3DExporter.I3DAddMessage(I3DExporter.MESSAGE_TYPE_WARNING, 'Could not find end tag. Ignoring i3dMappings!')

    def __addI3dMapping(self, list, root):
        nodes = cmds.ls(assemblies=True)
        if root is not None:
            nodes = cmds.listRelatives(root, pa=True, f=True, type='transform')

        if nodes is not None:
            for node in nodes:
                if not I3DUtils.isDefaultCamera(node) and "_ignore" not in node:
                    xmlIdentifier = I3DExporter.I3DGetAttributeValue(node, 'i3D_xmlIdentifier', '')
                    xmlIdentifier = xmlIdentifier.strip()
                    if xmlIdentifier != '':
                        nodeName = node
                        if not nodeName.startswith("|"):
                            nodeName = "|" + nodeName
                        indexPath = I3DUtils.getIndexPath(nodeName)
                        if indexPath is not None:
                            list.append('        <i3dMapping id="' + xmlIdentifier + '" node="' + indexPath + '" />')

                    if not I3DExporter.I3DGetAttributeValue(node, 'i3D_mergeChildren', False):
                        self.__addI3dMapping(list, node)

    def __removeI3dMapping(self, lines):
        cleanedLines = []
        for line in lines:
            found = re.findall('i3dMapping', line)
            if len(found) == 0:
                cleanedLines.append(line.rstrip())  # remove existing line break characters, readded unified on save in I3DUpdateXML()

        return cleanedLines
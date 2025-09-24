#
# ErrorBox
# Class to handle the content of the error box
#
# @created 05/04/2024
# @author Stefan Maurus
#
# Copyright (C) GIANTS Software GmbH, Confidential, All Rights Reserved.
#

import maya.cmds as cmds

try:
    # python 3
    from html import escape
except ImportError:
    # python 2
    from cgi import escape


class ErrorBox():
    MESSAGE_TYPE_INFO = 0
    MESSAGE_TYPE_WARNING = 1
    MESSAGE_TYPE_ERROR = 2
    MESSAGE_TYPE_NONE = 3

    COLOR = {}
    COLOR[MESSAGE_TYPE_INFO] = "#1E90FF"
    COLOR[MESSAGE_TYPE_WARNING] = "#FF8C00"
    COLOR[MESSAGE_TYPE_ERROR] = "#FF0000"
    COLOR[MESSAGE_TYPE_NONE] = "#C5C5C5"

    PREFIX = {}
    PREFIX[MESSAGE_TYPE_INFO] = "(Info) "
    PREFIX[MESSAGE_TYPE_WARNING] = "(Warning) "
    PREFIX[MESSAGE_TYPE_ERROR] = "(Error) "
    PREFIX[MESSAGE_TYPE_NONE] = ""

    def __init__(self, uiControl, parentLayout, setHScrollbar=False):
        self.layout = cmds.scrollLayout(uiControl, parent=parentLayout, cr=True, verticalScrollBarAlwaysVisible=True, bgc=(.168627, .168627, .168627), resizeCommand=self.onResize)

        self.lines = []
        self.setHScrollbar = setHScrollbar

    def addMessage(self, typeIndex, msg, margin=3, color=None, buttonText="", buttonFunc=None, buttonArgs=[], buttonAnnotation=None, buttonRemoveLine=False, buttonColor=None, updateScrolling=True):
        if color is None:
            color = self.COLOR[typeIndex]

        msg = self.PREFIX[typeIndex] + msg

        height = 17

        line = {}
        line["layout"] = cmds.formLayout(parent=self.layout, height=18)
        line["text"] = cmds.text(label='<span style="color: %s">%s</span>' % (color, escape(msg)), parent=line["layout"], height=height, vis=True, align="center")

        if buttonFunc is not None:
            def commandFunc(unused):
                if buttonRemoveLine:
                    cmds.deleteUI(line["layout"], control=True)
                    self.lines.remove(line)
                buttonFuncStatusReturn = buttonFunc(buttonArgs, unused)

                if not buttonRemoveLine:
                    # update line based on button func return vales, e.g. if button action failed
                    if buttonFuncStatusReturn is not None:
                        buttonFuncStatus, buttonFuncMessage = buttonFuncStatusReturn

                        if buttonFuncStatus is not None:
                            feedbackTextColor = 'green' if buttonFuncStatus else 'red'
                            cmds.text(line["text"], edit=True, label='<span style="color: %s">%s</span>' % (feedbackTextColor, escape(buttonFuncMessage)))
                            cmds.deleteUI(line["button"], control=True)  # remove button only

            line["button"] = cmds.button(parent=line["layout"], label=buttonText, command=commandFunc, height=height, annotation=buttonAnnotation, backgroundColor=buttonColor or [0.2, 0.2, 0.2])
            cmds.formLayout(line["layout"], edit=True, attachForm=((line["text"], 'left', margin), (line["button"], 'right', 15)))
        else:
            cmds.formLayout(line["layout"], edit=True, attachForm=((line["text"], 'left', margin)))

        self.lines.append(line)

        if updateScrolling:
            self.updateScrolling()

    def addMessages(self, messageData):
        for data in messageData:
            if "buttonText" in data:
                self.addMessage(data["typeIndex"], data["message"], margin=data["margin"], color=data["color"], buttonText=data["buttonText"], buttonFunc=data["buttonFunc"], buttonArgs=data["buttonArgs"], buttonAnnotation=data["buttonAnnotation"], buttonRemoveLine=data["buttonRemoveLine"], buttonColor=data["buttonColor"])
            else:
                self.addMessage(data["typeIndex"], data["message"], margin=data["margin"])
        self.updateScrolling()

    def updateScrolling(self):
        maxWidth = cmds.scrollLayout(self.layout, query=True, scrollAreaWidth=True)
        cmds.formLayout(self.lines[-1]["layout"], edit=True, width=maxWidth)

        cmds.scrollLayout(self.layout, edit=True, scrollPage="down")

    def clear(self):
        for i in range(0, len(self.lines)):
            cmds.deleteUI(self.lines[i]["layout"])
        self.lines = []

    def onResize(self):
        allMaxWidth = 0
        for line in self.lines:
            maxWidth = cmds.scrollLayout(self.layout, query=True, scrollAreaWidth=True)
            cmds.formLayout(line["layout"], edit=True, width=maxWidth)
            allMaxWidth = max(allMaxWidth, cmds.control(line["text"], query=True, width=True))

        if self.setHScrollbar and len(self.lines) > 0:
            cmds.formLayout(self.lines[-1]["layout"], edit=True, width=allMaxWidth)

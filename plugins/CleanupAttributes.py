#
# Cleanup Custom Attributes Plugin for Maya I3D Exporter
# Offers function to remove every attribute which does not start with I3D or onCreate and has not been created manually by the user
#
# @created 10/06/2020
# @author Michael Keller, Stefan Maurus
#
# Copyright (C) GIANTS Software GmbH, Confidential, All Rights Reserved.
#

import maya.cmds as cmds
import re


class CleanUpAttributes:
    """ Cleanup Extra Attributes plugin class"""

    def __init__(self):
        self.name = "Cleanup Attributes"
        self.page = "Tools"
        self.prio = 5

        self.regex = re.compile(r'(?i)\bI3D\w*|\bonCreate\w*')  # defines valid attributes

    def onTransformCheck(self, args):
        node, addMessageFunc = args[0], args[1]

        def removeAttribute(nodeAttr, *args):
            cmds.deleteAttr(nodeAttr[0], at=nodeAttr[1])

        userAttr = cmds.listAttr(node, ud=True)
        if userAttr:
            for attr in userAttr:
                if self.regex.match(attr):
                    pass
                elif not cmds.attributeQuery(attr, node=node, internalSet=True):  # manually set attributes
                    pass
                else:
                    addMessageFunc("warning", "Unnecessary attribute '%s' found" % attr, 30, buttonText="Remove attribute", buttonFunc=removeAttribute, buttonArgs=[node, attr], buttonRemoveLine=True)


def getI3DExporterPlugin():
    return CleanUpAttributes()

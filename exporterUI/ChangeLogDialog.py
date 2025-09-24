import maya.cmds as cmds
import os
import hashlib
import exporterUI.ErrorBox as ErrorBox
import I3DExporter

UI_CONTROL_CHANGELOG_SCROLL = 'giants_changeLogScrollLayout'

def show_modal_dialog():
    file_content = readChangeLog()
    lines = file_content.splitlines()
    newHashes = []
    oldHashes = loadOldHashes()

    myLines = []
    for line_number, line in enumerate(lines, start=1):
        # Create an MD5 hash object
        md5_hash = hashlib.md5()
        # Update the hash object with the string
        md5_hash.update(line.encode('utf-8'))
        # Get the hexadecimal representation of the hash
        md5_hex = md5_hash.hexdigest()

        if (md5_hex in oldHashes):
            myLines.append((line, '#888888'))
        else:
            myLines.append((line, '#FFFFFF'))

        newHashes.append(md5_hex)

    saveNewHashes(newHashes)

    # Create a window
    WINDOW_ID = "giants_changeLogWindow"

    topLeftCorner = cmds.window(I3DExporter.UI_CONTROL_WINDOW, q=True, topLeftCorner=True)
    width = cmds.window(I3DExporter.UI_CONTROL_WINDOW, q=True, width=True) - 15
    height = cmds.window(I3DExporter.UI_CONTROL_WINDOW, q=True, height=True) - 15

    UI_WIDTH = int(width) * 0.9
    UI_HEIGHT = 250

    topLeftCorner[0] = topLeftCorner[0] + int(height * 0.5 - UI_HEIGHT * 0.5)
    topLeftCorner[1] = topLeftCorner[1] + int(width * 0.5 - UI_WIDTH * 0.5)

    if cmds.windowPref(WINDOW_ID, exists=True):
        cmds.windowPref(WINDOW_ID, edit=True, widthHeight=(UI_WIDTH, UI_HEIGHT), topLeftCorner=topLeftCorner)

    if cmds.window(WINDOW_ID, exists=True):
        cmds.deleteUI(WINDOW_ID, window=True)
    window = cmds.window(WINDOW_ID, title="GIANTS I3D Exporter - Change Log", width=UI_WIDTH, height=UI_HEIGHT, sizeable=False, topLeftCorner=topLeftCorner)

    errorBox = ErrorBox.ErrorBox(UI_CONTROL_CHANGELOG_SCROLL, window, True)
    for message, color in myLines:
        errorBox.addMessage(I3DExporter.MESSAGE_TYPE_NONE, message, margin=1, color=color, buttonText=None, buttonFunc=None, buttonArgs=None, buttonAnnotation=None, buttonRemoveLine=None, buttonColor=None)

    # Show the window
    cmds.showWindow(window)

def getHasChangedAnythingSinceLastView():
    file_content = readChangeLog()
    if not file_content:
        return False
    lines = file_content.splitlines()
    oldHashes = loadOldHashes()
    for line_number, line in enumerate(lines, start=1):
        # Create an MD5 hash object
        md5_hash = hashlib.md5()
        # Update the hash object with the string
        md5_hash.update(line.encode('utf-8'))
        # Get the hexadecimal representation of the hash
        md5_hex = md5_hash.hexdigest()

        if (md5_hex not in oldHashes):
            return True
    return False

def getShownChangeLogFileName():
    # Get the user's AppData directory path
    appdata_dir = os.getenv('APPDATA')
    if not appdata_dir:
        raise RuntimeError("Could not find AppData directory")
    appdata_dir += "\\Giants"
    if not os.path.exists(appdata_dir):
        os.makedirs(appdata_dir)
    return os.path.join(appdata_dir, "GiantsMayaExporter.properties")

def saveNewHashes(content):
    with open(getShownChangeLogFileName(), 'w') as file:
        for fileHash in content:
            file.write(fileHash + "\n")

def loadOldHashes():
    try:
        with open(getShownChangeLogFileName(), 'r') as file:
            file_content = file.read()
        return file_content
    except IOError:
        return []

def readChangeLog():
    try:
        # Get the directory of the plugin script
        plugin_script_path = os.path.realpath(__file__)
        plugin_directory = os.path.dirname(plugin_script_path)

        with open(plugin_directory + "/../ChangeLog.txt", 'r') as file:
            return file.read()
    except IOError:
        return ""


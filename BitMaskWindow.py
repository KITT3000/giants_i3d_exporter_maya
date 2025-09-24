#-----------------------------------------------------------------------------------
#
#   SCRIPT      BitMaskWindow.py
#   AUTHORS     Marius Hofmann, roughly based on generateObjectDataFromCurve.py by Evgen Zaitsev
#
#   Provides a window for modifying a bitmask with automatic conversion between hex, dec and binary formats
#   Number of bits, intial value and callback function can be provided as arguments
#   If provided bitmask argument is of str type it is expected to be in hex format and converted upon loading
#   Callback function receives set bitmask in decimal format as first argument
#
#-----------------------------------------------------------------------------------

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

gWinGuiID = 'w_bitMaskWindowGuiID'
if cmds.window(gWinGuiID, exists=True):
    cmds.deleteUI(gWinGuiID, window=True)

class BitMaskWindow():

    def __init__(self, num_bits, bitmask, callback, args, window_title='Edit Bitmask', editable=True):

        bit_names = args.get('bit_names', {})
        bit_annotations = args.get('bit_annotations', {})
        self.num_bits = num_bits

        self.bitmask_dec = 0
        if bitmask is None:
            self.bitmask_dec = 255
        elif type(bitmask) is str:
            self.bitmask_dec = int(bitmask, 16)
        else:
            self.bitmask_dec = bitmask
        
        max_val = pow(2, num_bits) - 1
        if self.bitmask_dec > max_val:
            cmds.confirmDialog(title="Error", message="Bitmask-Dialog was opened with a value ({}) larger than allowed ({}) by the number of bits (max %i Bits)\nValue was truncated" % (self.bitmask_dec, max_val, self.num_bits))
            self.bitmask_dec = min(self.bitmask_dec, pow(2, num_bits) - 1)

        self.callback = callback # function called when users confirms changes with "OK"

        # delete ui window if opened
        if cmds.window(gWinGuiID, exists=True):
            cmds.deleteUI(gWinGuiID, window=True)

        # create the window
        self.m_window = cmds.window(gWinGuiID, title=window_title, resizeToFitChildren=True)
        columnLayout = cmds.columnLayout('bitmask panel', parent=self.m_window, rowSpacing=7, columnOffset=["both", 10])

        # hex mask
        layout = cmds.rowLayout(parent=columnLayout, adjustableColumn=2, numberOfColumns=2)
        self.m_labelMaskHex = cmds.text(parent=layout, label='Bit Mask (Hex)', align='left', width=80, height=25)
        self.m_textMaskHex  = cmds.scrollField(parent=layout, editable=editable, width=260, height=25, font="fixedWidthFont", keyPressCommand=lambda *args: cmds.evalDeferred(self.hexChanged))
        
        # dec mask
        layout = cmds.rowLayout(parent=columnLayout, adjustableColumn=2, numberOfColumns=2)
        self.m_labelMaskDec = cmds.text(parent=layout, label='Bit Mask (Dec)', align='left', width=80, height=25)
        self.m_textMaskDec  = cmds.scrollField(parent=layout, editable=editable, width=260, height=25, keyPressCommand=lambda *args: cmds.evalDeferred(self.decChanged))  # intField can't hold large enough numbers
        
        # binary
        layout = cmds.rowLayout(parent=columnLayout, adjustableColumn=2, numberOfColumns=2)
        self.m_labelBinary = cmds.text(parent=layout, label='Bit Mask (Bin)', align='left', width=80, height=25)
        self.m_textMaskBin  = cmds.scrollField(parent=layout, editable=editable, width=260, height=25, keyPressCommand=lambda *args: cmds.evalDeferred(self.binChanged))

        # bit checkboxes
        cellWidth = 60
        if bit_names:  # find ideal cell width to fit names
            longest_name_length = len(max(bit_names.values(), key=len))
            cellWidth = max(cellWidth, min(200, 30 + longest_name_length * 8))

        num_cols = int(num_bits / 8)
        num_rows = int(num_bits / num_cols)

        grid_layout = cmds.gridLayout(parent=columnLayout, numberOfColumns=num_cols, cellWidth=cellWidth, cellHeight=25)
        self.m_bitCheckboxes = dict()
        for i in range(self.num_bits):
            # maya UI is row based, but bits should be filled up column-wise => transpose
            row = i // num_cols
            col = i % num_cols
            transposed_index = col * num_rows + row  # Calculate the transposed index by swapping the row and column positions

            name = "{} {}".format(transposed_index, bit_names.get(transposed_index, "")) 
            annotation = bit_annotations.get(transposed_index, "")

            self.m_bitCheckboxes[transposed_index] = cmds.checkBox(label=name, parent=grid_layout, annotation=annotation, editable=editable, align='left', height=20, changeCommand=lambda *args: self.uiCallback(self.m_bitCheckboxes))

        self.m_textError = cmds.text(parent=columnLayout, label='', backgroundColor=[1, 0, 0], align='left', visible=False, height=25)

        # buttons
        layout = cmds.rowLayout(parent=columnLayout, numberOfColumns=2, columnAttach2=["right", "right"], columnOffset2=[10, 10])
        cmds.button("OK", parent=layout, command=lambda *args: self.onClickOk())

        cmds.button("Cancel", parent=layout, command=lambda *args: cmds.deleteUI( gWinGuiID, window = True ))

        cmds.showWindow(gWinGuiID)
        self.uiRefresh(None)
      
    # updates all fields with current internal bitmask value
    def uiRefresh(self, excludedField):
        bitmask_hex = "%X" % self.bitmask_dec
        bits = '{0:0{numBits}b}'.format(self.bitmask_dec, numBits=self.num_bits) # convert to binary and reverse for little endian

        # exclude specific/changed field to prevent the cursor from being reset
        if self.m_textMaskHex != excludedField:
            cmds.scrollField(self.m_textMaskHex, edit=True, text=bitmask_hex)
        if self.m_textMaskDec != excludedField:
            cmds.scrollField(self.m_textMaskDec, edit=True, text=str(self.bitmask_dec))
        if self.m_textMaskBin != excludedField:
            cmds.scrollField(self.m_textMaskBin,  edit=True, text=bits)

        # set bit checkboxes
        for bit_number in range(self.num_bits):
            check_box = self.m_bitCheckboxes[bit_number]
            bit_is_set = (self.bitmask_dec & (1 << bit_number)) != 0
            cmds.checkBox(check_box, edit=True, value=bit_is_set)

    def hexChanged(self):
        self.cleanScrollField(self.m_textMaskHex)
        self.uiCallback(self.m_textMaskHex)

    def decChanged(self):
        self.cleanScrollField(self.m_textMaskDec)
        self.uiCallback(self.m_textMaskDec)

    def binChanged(self):
        self.cleanScrollField(self.m_textMaskBin)
        self.uiCallback(self.m_textMaskBin)

    def cleanScrollField(self, field):
        value = cmds.scrollField(field, q=True, text=True)
        if value == "":
            cmds.scrollField(field, edit=True, text="0", insertionPosition=0)  # set default value of 0 if empty
        if "\n" in value:
            cmds.scrollField(field, edit=True, text=value.replace('\n', ''), insertionPosition=0)  # remove newlines

    # updates internal bitmask value on field change
    def uiCallback(self, field):
        cmds.text(self.m_textError, edit=True, label='', visible=False)  # clear error message

        try:
            # get value from changed field
            if (field == self.m_textMaskHex):
                dec_val = int(cmds.scrollField(self.m_textMaskHex, q=True, text=True), 16)

            elif (field == self.m_textMaskDec):
                dec_val = int(cmds.scrollField(self.m_textMaskDec, q=True, text=True))

            elif (field == self.m_textMaskBin):
                dec_val = int(cmds.scrollField(self.m_textMaskBin, q=True, text=True), 2)

            elif (field == self.m_bitCheckboxes):
                dec_val = 0
                # convert bits to int
                for i in range(self.num_bits):
                    check_box = self.m_bitCheckboxes[i]
                    if cmds.checkBox(check_box, q=True, value=True):
                        dec_val += 2**i

            # check if new value is valid, reset fields to last valid value otherwise
            if self.verifyValue(dec_val):
                self.bitmask_dec = dec_val
            else:
                cmds.text(self.m_textError, edit=True, visible=True, label="Entered value out of available range (max %i Bits)" % self.num_bits)
                self.uiRefresh(None)

        # conversion/casting of input field to int failed
        except ValueError: 
            cmds.text(self.m_textError, edit=True, visible=True, label="Invalid value entered, field was reset")
            self.uiRefresh(None)

        self.uiRefresh(field) # update values in other fields

    def onClickOk(self):
        self.callback(self.bitmask_dec) # return set value
        cmds.deleteUI(gWinGuiID, window=True)

    # checks if provided bitmask in decimal is within the range for the number of bits
    def verifyValue(self, dec_val):
        return dec_val <= (2**self.num_bits - 1) and dec_val >= 0

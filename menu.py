import nuke
import os
import re
import sys
import subprocess

menubar = nuke.menu("Nuke")

#########################
def disableErrorNodes():
    nodes = nuke.allNodes()
    for node in nodes:    
        if "disable" in node.knobs() and node.Class() != "Read":
            if node.hasError():
                node.knob("disable").setValue(1)   

menubar.addCommand( "disableErrorNodes", "disableErrorNodes()") 
nuke.addOnScriptLoad(disableErrorNodes)  
###############################################################
def killViewers():
    for v in nuke.allNodes("Viewer"):
        nuke.delete(v)
nuke.addOnScriptLoad(killViewers)
###############################################################
def appendNearShots():

    currentEpisodePath = nuke.root().name().rsplit('/', 5)[0]
    currentShot = nuke.root().name().rsplit('/', 4)[0].split("/")[-1]

    epDirList = os.listdir (currentEpisodePath)
    epDirListFiltered = []    
    currShotIndex = 0
    prevShotIndex = 0
    nextShotIndex = 0

    for d in epDirList:
        if re.match("sh.", d):
            epDirListFiltered.append(d)

    epDirListFiltered.sort()

    listLen = len(epDirListFiltered)-1

    for f in epDirListFiltered:
        if f == currentShot:
            currShotIndex = epDirListFiltered.index(f)
            if currShotIndex == 0:
                prevShotIndex = currShotIndex
                nextShotIndex = currShotIndex + 1
            elif currShotIndex == listLen:
                prevShotIndex = currShotIndex - 1
                nextShotIndex = currShotIndex
            else:
                prevShotIndex = currShotIndex - 1
                nextShotIndex = currShotIndex + 1          

    def makeFullPath (pathEp, shot):
        outPath = pathEp + "/" + shot + "/comp/out/"
        fullPath = ""
        readNode =""
        if os.path.isdir(outPath):
            fullPath = outPath + os.listdir(outPath)[0]
            for seq in nuke.getFileNameList(fullPath):
                readNode = nuke.createNode('Read') 
                readNode.knob('file').fromUserText(fullPath + "/" + seq)
        else:
            readNode = nuke.createNode('Read')

        return readNode
    

    prevRead = makeFullPath (currentEpisodePath, epDirListFiltered[prevShotIndex])
    currRead = makeFullPath (currentEpisodePath, epDirListFiltered[currShotIndex])
    nextRead = makeFullPath (currentEpisodePath, epDirListFiltered[nextShotIndex])
     
    appendNode = nuke.createNode('AppendClip')   
    appendNode.setInput(0, prevRead)
    appendNode.setInput(1, currRead)
    appendNode.setInput(2, nextRead)

    nodeList = [prevRead, currRead, nextRead, appendNode]
    
    allX = sum( [ n.xpos()+n.screenWidth()/2 for n in nodeList ] )  
    allY = sum( [ n.ypos()+n.screenHeight()/2 for n in nodeList ] ) 

    centreX = allX / 4
    centreY = allY / 4
    
    for n in nodeList:
        n.setXpos( centreX + ( n.xpos() - centreX ) * 3 )
        n.setYpos( centreY + ( n.ypos() - centreY ) * 2 )

menubar.addCommand( "appendNearShots", "appendNearShots()")   
###############################################################
def add_out_names(self):
        import os
        import nuke
        try:
            import sgtk
        except ImportError:
            self.logger.warning('Can not import sgtk and retrieve template data')
            nuke.message('ERROR: can not import sgtk and retrieve template data')
            return

        selected_node = nuke.selectedNode()
        file_path = nuke.root().name()
        if file_path:
            if selected_node.Class() == 'Write':
                post_shot_template = sgtk.platform.current_engine().get_template_by_name('post_shot_sequence')
                nuke_shot_work_template = sgtk.platform.current_engine().get_template_by_name('nuke_shot_work')
                fields = nuke_shot_work_template.get_fields(file_path)
                out_path = post_shot_template.apply_fields(fields)
                out_path = out_path.replace("\\", "/")
                outDir = os.path.dirname(out_path)
                # print ('outDir= %s' % outDir)
                # colorSpace = None
                ext = out_path.split('.')[-1]
                selected_node.knob('file').setValue(str(out_path))
                selected_node.knob('file_type').setValue(str(ext))
                # selected_node.knob('colorspace').setValue(str(colorSpace))
                if not os.path.exists(outDir):
                    nuke.message('WARNING: no such directory %s ' % outDir)
            else:
                nuke.message('ERROR: Write node must be selected')
        else:
            nuke.message('ERROR: The script should be saved')
            return
#################
def createReadFromWrite():
    write = nuke.thisNode()
    wPosX = write["xpos"].getValue()
    wPosY = write["ypos"].getValue()
    fFrame = nuke.Root()["first_frame"].getValue()
    lFrame = nuke.Root()["last_frame"].getValue()
    wOut = write["file"].getValue()
    wColorspace = write["colorspace"].getValue() 

    read = nuke.createNode("Read")
    read.setXpos (int(wPosX)+120)
    read.setYpos (int(wPosY))
    read["file"].setValue(wOut)
    read["colorspace"].setValue(int(wColorspace))
    read["first"].setValue(int(fFrame))
    read["last"].setValue(int(lFrame))
    read["origfirst"].setValue(int(fFrame))
    read["origlast"].setValue(int(lFrame))
#################
def openDir():
    node = nuke.thisNode()
    path = os.path.dirname(node["file"].getValue())

    if os.path.isdir(path):
        subprocess.check_call(["explorer", path.replace("/", "\\")])
    else:
        nuke.message("No dir!")
#################
def writeTools():
   n = nuke.thisNode()
   outName = nuke.PyScript_Knob('setOutName', 'setOutName', 'add_out_names(nuke.thisNode())')
   readFromWrite = nuke.PyScript_Knob('readFromWrite', 'readFromWrite', 'createReadFromWrite()')
   openDir = nuke.PyScript_Knob('openDir', 'openDir', 'openDir()')
   n.addKnob(nuke.Tab_Knob('Tools', 'Tools'))
   n.addKnob(outName)
   n.addKnob(readFromWrite)
   n.addKnob(openDir)

nuke.addOnUserCreate(writeTools, nodeClass = 'Write')
#################


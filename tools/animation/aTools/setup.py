'''
========================================================================================================================
Author: Alan Camilo
www.alancamilo.com

Requirements: aTools Package

------------------------------------------------------------------------------------------------------------------------
To install aTools, please follow the instructions in the file how_to_install.txt

------------------------------------------------------------------------------------------------------------------------
To unistall aTools, go to menu (the last button on the right), Uninstall

========================================================================================================================
''' 
import os
import shutil
from maya import mel
from BM2Public.tools.animation.aTools.generalTools.aToolsGlobals import aToolsGlobals as G
from BM2Public.tools.animation.aTools.commonMods import utilMod
from BM2Public.tools.animation.aTools.commonMods import aToolsMod

def install(offline=None, unistall=False):
    return
    mayaAppDir      = mel.eval('getenv MAYA_APP_DIR')
    scriptsDir      = mayaAppDir + os.sep + '2017' + os.sep + "scripts"
    userSetupFile   = scriptsDir + os.sep + "userSetup.py"
    newUserSetup    = ""  
    
    '''
    try:
        with open(userSetupFile, 'r'):
            
            input = open(userSetupFile, 'r')
            lines = input.readlines()  
            
            # clear old aTool codes, if there is any
            write = True
            for n, line in enumerate(lines):        
                if line.find("# start aTools") == 0:
                    write = False
                    
                if write: newUserSetup += line
                    
                if line.find("# end aTools") == 0:
                    write = True
                    
    except IOError:
        newUserSetup    = ""       
    
    aToolCode  = "# start aTools\n\nfrom maya import cmds\nif not cmds.about(batch=True):\n\n    # launch aTools_Animation_Bar\n    cmds.evalDeferred(\"from BM2Public.tools.animation.aTools.animTools.animBar import animBarUI; animBarUI.show('launch')\", lowestPriority=True)\n\n# end aTools"
        
    if not unistall: newUserSetup    += aToolCode
    
    # write user setup file
    output = open(userSetupFile, 'w')
    output.write(newUserSetup)
    output.close()
    
    
    if offline:        
        
        offlineFilePath = offline[0]
        createMelFile   = offline[1]
        offlineFolder   = os.sep.join(offlineFilePath.split(os.sep)[:-1])
        fileModTime     = os.path.getmtime(offlineFilePath)
        
        aToolsMod.saveInfoWithUser("userPrefs", "offlinePath", [offlineFolder, fileModTime]) 
        if createMelFile == True: createOfflineMelFile(offlineFolder, scriptsDir)
    
    '''
    #open tool
    if not unistall:
        from BM2Public.tools.animation.aTools.animTools.animBar import animBarUI; reload(animBarUI)
        animBarUI.show()
    
        
        
def createOfflineMelFile(offlineFolder, scriptsDir):
    return
    filePath            = "%s%saTools_offline_install.mel"%(offlineFolder, os.sep)
    offlineInstallPy    = "%s%saTools%sgeneralTools%sofflineInstall.py"%(scriptsDir, os.sep, os.sep, os.sep)
    pyContents          = "\\n\\".join(utilMod.readFile(offlineInstallPy))
    contents            = "python(\"\\n\\\naToolsZipPath = '%s%saTools.zip'\\n\\\n"%(offlineFolder, os.sep)
    contents            += "\\n\\\n".join("".join(utilMod.readFile(offlineInstallPy)).split("\n"))
    contents            += "\");"
    
    utilMod.writeFile(filePath, contents)

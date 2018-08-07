''' to do:
-preroll de los characters
-subir el archivo que genera esos caches a out
'''

   


import maya.cmds as cmds
import BM2Public.tools.animation.playblaster.playblasterFunctions as playblasterFunctions
import abcExporterFunctions as abcExporterFunctions


def deleteWindow(name):
    if cmds.window(name, exists=True):
        cmds.deleteUI(name)    

def abcExporterUI(*args):
    deleteWindow('abcExporter')
    sceneInfo=playblasterFunctions.pipeInfo()
    props=abcExporterFunctions.elemsLister()['props']
    chars=abcExporterFunctions.elemsLister()['chars']

    cachesDescription=[]
    for o in abcExporterFunctions.readCachesInDisk():
        cachesDescription.append(o)


    cmds.window('abcExporter', title="abc Exporter UI", tlb=True, s=False)

    #layout horizontal que centre todas los items de la herramienta dejando un margen a ambos lados
    cmds.rowLayout('safeSidesLayout', adjustableColumn=2, numberOfColumns=3)
    cmds.separator(st='none',p='safeSidesLayout')
    cmds.columnLayout('mainLayout', adjustableColumn=1, p='safeSidesLayout')
    cmds.separator(st='none',p='safeSidesLayout')

    cmds.rowLayout('infoLayout', adjustableColumn=3, numberOfColumns=4, p='mainLayout')

    cmds.columnLayout('projectLayout', p='infoLayout')
    cmds.text(label='Project:')
    cmds.textField('projectField',tx=sceneInfo['project'], w=50, ed=False)

    cmds.columnLayout('seqLayout', p='infoLayout')
    cmds.text(label='Seq:')
    cmds.textField('seqField',tx=sceneInfo['seq'], w=50, ed=False)

    cmds.columnLayout('shotLayout', p='infoLayout')
    cmds.text(label='Shot:')
    cmds.textField('shotField',tx=sceneInfo['shot'], w=50, ed=False)
    cmds.symbolButton(image='refresh.png', p='infoLayout', c= abcExporterFunctions.refreshUI)
    cmds.separator(h=15, st='shelf',p='mainLayout')

    tabs = cmds.tabLayout('tabsLayout',innerMarginWidth=5, innerMarginHeight=5, p='mainLayout')

    tab1=cmds.columnLayout('tab1Layout', adjustableColumn=1)
    cmds.separator(h=10, st='none',p='tab1Layout')    
    cmds.text(label='CHARS', al='left')
    cmds.columnLayout('charsLayout', adjustableColumn=1)
    cmds.textScrollList('charsList', w=180, h=75, a=chars, allowMultiSelection=True, dcc="cmds.textScrollList('charsList', e=True, da=True)", p='charsLayout')
    cmds.rowLayout('charsPlusMinLayout', numberOfColumns=3, adjustableColumn=2, p='charsLayout')
    cmds.button(label='+', w=40, p='charsPlusMinLayout', c=abcExporterFunctions.addSelectedChars)
    cmds.button(label='clear list',w=80, p='charsPlusMinLayout',c="cmds.textScrollList('charsList',ra=True, e=True)")
    cmds.button(label='-', w=40, p='charsPlusMinLayout',c=abcExporterFunctions.removeChar)

    cmds.separator(h=10, st='none',p='tab1Layout')
    cmds.text(label='PROPS', al='left',p='tab1Layout')
    cmds.columnLayout('propsLayout', adjustableColumn=1,p='tab1Layout')
    cmds.textScrollList('propsList', w=180,h=100, a=props, allowMultiSelection=True, dcc="cmds.textScrollList('propsList', e=True, da=True)", p='propsLayout')
    cmds.rowLayout('propsPlusMinLayout', numberOfColumns=3, adjustableColumn=2, p='propsLayout')
    cmds.button(label='+', w=40, p='propsPlusMinLayout', c=abcExporterFunctions.addSelectedProps)
    cmds.button(label='clear list', w=80, p='propsPlusMinLayout',c="cmds.textScrollList('propsList',ra=True, e=True)")
    cmds.button(label='-', w=40, p='propsPlusMinLayout', c=abcExporterFunctions.removeProp)

    cmds.separator(h=30, st='shelf', p='tab1Layout')
    cmds.button('doAbcs',label='create alembics from lists', p='tab1Layout', c=abcExporterFunctions.doTheCaches)
    
    cmds.setParent( '..' )
    cmds.setParent( '..' )
    cmds.setParent( '..' )

    tab2 = cmds.columnLayout('cachesExportedLayout', adjustableColumn=4)
    cmds.separator(st='none',h=10)
    cmds.text(l='Those caches have been exported for this shot')
    cmds.separator(st='none',h=10)
    cmds.textScrollList('cachesExportedList', w=180, h=220, allowMultiSelection=True, a=cachesDescription, dcc="cmds.textScrollList('cachesExportedList', e=True, da=True)", p='cachesExportedLayout')
    cmds.separator(st='none',h=5)
    cmds.separator(h=25, st='shelf')
    cmds.button('importCachesButton',label='Import Selected Caches', c=abcExporterFunctions.importCacheToScene)
    cmds.separator(st='none',h=3)
    cmds.button('publishCachesButton',label='Publish Selected', c=abcExporterFunctions.publishSelectedCaches)
    cmds.setParent( '..' )

    cmds.tabLayout( tabs, edit=True, bs='none', tp='north',tabLabel=((tab1, 'Caches Exporter'), (tab2, 'Caches In Disk')))

    cmds.showWindow('abcExporter')

"""
<name>Classification Tree Viewer</name>
<description>ClassificationTreeViewer displays a classification tree in a hierarchical list view.</description>
<category>Classification</category>
<icon>icons/ClassificationTreeViewer.png</icon>
<priority>2100</priority>
"""

from OWWidget import *
from orngTreeLearner import TreeLearner
from OWGUI import *

class ColumnCallback:
    def __init__(self, widget, attribute, f = None):
        self.widget = widget
        self.attribute = attribute
        self.f = f
        widget.callbackDeposit.append(self)
        
    def __call__(self, value):
        setattr(self.widget, self.attribute, self.f and self.f(value) or value)
        self.widget.setTreeView(1)

def checkColumn(widget, master, text, value):
    wa = QCheckBox(text, widget)
    wa.setChecked(getattr(master,value))
    master.connect(wa, SIGNAL("toggled(bool)"), ColumnCallback(master, value))
    return wa

class OWClassificationTreeViewer(OWWidget):
    settingsList = ["maj", "pmaj", "ptarget", "inst", "dist", "expslider"]

    def __init__(self, parent=None, name='Classification Tree Viewer'):
        OWWidget.__init__(self, parent, name, "ClassificationTreeViewer displays a classification tree in a hierarchical list view.")

        self.dataLabels = (('Majority class', 'Class'),
                  ('Probability of majority class', 'P(Class)'),
                  ('Probability of target class', 'P(Target)'),
                  ('Number of instances', '#Inst'),
                  ('Class distribution', 'Distribution'))

        self.callbackDeposit = []

        self.inputs = [("Classification Tree", orange.TreeClassifier, self.ctree, 1), ("Target Class Value", int, self.target, 1)]
        self.outputs = [("Classified Examples", ExampleTableWithClass)]

        # Settings
        for s in self.settingsList[:5]:
            setattr(self, s, 1)
        self.expslider = 5
        self.loadSettings()

        self.tar = 0
        self.tree = None

        self.precision = 0
        self.precFrmt = "%%.%if" % self.precision
        
        # GUI
        # parameters
        
        self.dBox = QVGroupBox(self.controlArea)
        self.dBox.setTitle('Show Data')
        for i in range(len(self.dataLabels)):
            checkColumn(self.dBox, self, self.dataLabels[i][0], self.settingsList[i])

        self.expBox = QHGroupBox(self.controlArea)
        self.expBox.setTitle('Expand/Shrink to Level')
        self.slider = QSlider(1, 9, 1, self.expslider, QSlider.Horizontal, self.expBox)
        self.sliderlabel = QLabel("%2i" % self.expslider, self.expBox)

        # list view
        self.layout=QVBoxLayout(self.mainArea)
        self.splitter = QSplitter(QSplitter.Vertical, self.mainArea)
        self.layout.add(self.splitter)

        self.v = QListView(self.splitter)
        self.v.setAllColumnsShowFocus(1)
        self.v.addColumn('Classification Tree')
        self.v.setColumnWidth(0, 250)
        self.v.setColumnWidthMode(0, QListView.Manual)
        self.v.setColumnAlignment(0, QListView.AlignLeft)

        # rule
        self.rule = QTextView(self.splitter)
        #self.rule.setMaximumHeight(100)
        #self.layout.add(self.rule)
        
        self.splitter.show()
        
        self.resize(800,300)

        self.connect(self.v, SIGNAL("selectionChanged(QListViewItem *)"), self.viewSelectionChanged)
        self.connect(self.slider, SIGNAL("valueChanged(int)"), self.sliderChanged)

    # main part:         

    def setTreeView(self, updateonly = 0):
        f = self.precFrmt

        def addNode(node, parent, desc, anew):
            return li
                
        def walkupdate(listviewitem):
            node = self.nodeClassDict[listviewitem]
            ncl = node.nodeClassifier
            dist = node.distribution
            a = dist.abs/100
            colf = (str(ncl.defaultValue),
                    f % (dist[int(ncl.defaultVal)]/a),
                    f % (dist[self.tar]/a),
                    f % dist.cases,
                    reduce(lambda x,y: x+':'+y, [self.precFrmt % (x/a) for x in dist])
                   )
                   
            col = 1
            for j in range(5):
                if getattr(self, self.settingsList[j]):
                    listviewitem.setText(col, colf[j])
                    col += 1

            child = listviewitem.firstChild()
            while child:
                walkupdate(child)
                child = child.nextSibling()

        def walkcreate(node, parent):
            if node.branchSelector:
                for i in range(len(node.branches)):
                    if node.branches[i]:
                        bd = node.branchDescriptions[i]
                        if not bd[0] in ["<", ">"]:
                            bd = node.branchSelector.classVar.name + " = " + bd
                        else:
                            bd = node.branchSelector.classVar.name + " " + bd
                        li = QListViewItem(parent, bd)
                        li.setOpen(1)
                        self.nodeClassDict[li] = node.branches[i]
                        walkcreate(node.branches[i], li)
            
        while self.v.columns()>1:
            self.v.removeColumn(1)
            
        for i in range(len(self.dataLabels)):
            if getattr(self, self.settingsList[i]):
                self.v.addColumn(self.dataLabels[i][1])
##                self.v.setColumnWidth(i, 60)
##                self.v.setColumnWidthMode(i, QListView.Maximum)
                self.v.setColumnAlignment(i+1, QListView.AlignCenter)
        self.v.setRootIsDecorated(1)

        if not updateonly:
            self.v.clear()
            self.nodeClassDict = {}
            li = QListViewItem(self.v, "<root>")
            li.setOpen(1)
            self.nodeClassDict[li] = self.tree.tree
            walkcreate(self.tree.tree, li)
            self.rule.setText("")
        walkupdate(self.v.firstChild())
        self.v.show()

    # slots: handle input signals        
        
    def ctree(self, tree):
        self.tree = tree
        self.setTreeView()

    def target(self, target):
        def updatetarget(listviewitem):
            dist = self.nodeClassDict[listviewitem].distribution
            listviewitem.setText(targetindex, f % (dist[self.tar]/dist.abs*100))

            child = listviewitem.firstChild()
            while child:
                updatetarget(child)
                child = child.nextSibling()
            
        if self.ptarget and (self.tar <> target):
            self.tar = target

            targetindex = 1
            for st in range(5):
                if self.settingsList[st] == "ptarget":
                    break
                if getattr(self, self.settingsList[st]):
                    targetindex += 1

            f = self.precFrmt            
            updatetarget(self.v.firstChild())
            
    def expandTree(self, lev):
        def expandTree0(listviewitem, lev):
            if not lev:
                listviewitem.setOpen(0)
            else:
                listviewitem.setOpen(1)
                child = listviewitem.firstChild()
                while child:
                    expandTree0(child, lev-1)
                    child = child.nextSibling()
                    
        expandTree0(self.v.firstChild(), lev)

    # signal processing
    def viewSelectionChanged(self, item):
        data = self.nodeClassDict[item].examples
        self.send("Classified Examples", data)

        tx = ""
        f = 1
        nodeclsfr = self.nodeClassDict[item].nodeClassifier
        while item and item.parent():
            if f:
                tx = str(item.text(0))
                f = 0
            else:
                tx = str(item.text(0)) + " AND\n    "+tx
                
            item = item.parent()

        classLabel = str(nodeclsfr.defaultValue)
        className = str(nodeclsfr.classVar.name)
        if tx:
            self.rule.setText("IF %s\nTHEN %s = %s" % (tx, className, classLabel))
        else:
            self.rule.setText("%s = %s" % (className, classLabel))

    def sliderChanged(self, value):
        self.expandTree(value)
        self.sliderlabel.setText(str(value))

##############################################################################
# Test the widget, run from DOS prompt
# > python OWDataTable.py)
# Make sure that a sample data set (adult_sample.tab) is in the directory

if __name__=="__main__":
    a=QApplication(sys.argv)
    ow=OWClassificationTreeViewer()
    a.setMainWidget(ow)

    data = orange.ExampleTable(r'../adult_sample')

    tree = orange.TreeLearner(data, storeExamples = 1)
    ow.ctree(tree)

    ow.show()
    a.exec_loop()
    ow.saveSettings()
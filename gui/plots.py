import sys
from PyQt4 import QtGui, QtCore

colours=[QtGui.QColor(237,44,48),
         QtGui.QColor(23,89,169),
         QtGui.QColor(0,140,70),
         QtGui.QColor(243,124,33),
         QtGui.QColor(101,43,145),
         QtGui.QColor(161,29,33),
         QtGui.QColor(179,56,148)
         ]

class PlotView(QtGui.QGraphicsView):
    def __init__(self):
        QtGui.QGraphicsView.__init__(self)
        
        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setSceneRect(QtCore.QRectF(0, 0, 440, 340))
        self.setScene(self.scene)
        
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0,0)))

        self.lp = LinePlot(None,self.scene)
#        self.lp.setAxesBoundaries(0, 6, 0, 20)
        data=[0,1,2,4,8,16]
        self.lp.plot(data,"test1")
        data=[0,1,2,3,4,5]
        self.lp.plot(data,"test2")
#        self.scene.addItem(self.lp)
        
    def resizeEvent(self, event):
#        self.fitInView(self.scene.sceneRect(), mode=QtCore.Qt.KeepAspectRatio)
        self.scene.setSceneRect(QtCore.QRectF(0, 0, event.size().width(), event.size().height()))
        self.lp.updatePlot()
        
        
class LinePlot(QtGui.QGraphicsItem):
    
    def __init__(self,parent=None, scene=None):
        super(LinePlot,self).__init__(parent, scene)
        self.hmargin = 20
        self.vmargin = 20
        self.awidth = 400
        self.aheight = 300
        
        self.xvmin = 0
        self.xvmax = 0
        self.yvmin = 0
        self.yvmax = 0
        
        self.seriesLabels=[]
        self.seriesData=[]
        
        self.changed=False

    def setAxesBoundaries(self,xmin,xmax,ymin,ymax):
        self.xvmin=xmin
        self.xvmax=xmax
        self.yvmin=ymin
        self.yvmax=ymax
        self.changed = True
    
    def plot(self,data,label="",linewidth=2.5, linestyle="-",marker='o'):
        self.seriesLabels.append(label)
        self.seriesData.append(data)
        self.changed = True
        
    def value2point(self,vx,vy):
        px=self.hmargin+vx*self.awidth/float(self.xvmax-self.xvmin)
        py=self.vmargin+self.aheight-vy*self.aheight/float(self.yvmax-self.yvmin)
        return QtCore.QPointF(px,py)
    
    def paintSeries(self):
        for i,ser in enumerate(self.seriesData):
            pp = None
            colour = colours[i%len(self.seriesData)]
            for vx,vy in enumerate(ser):
                point = self.value2point(vx, vy)
                PlotDot(point.x(),point.y(),5,colour,self)
                if vx>0: PlotLine(pp.x(),pp.y(),point.x(),point.y(),2.5,colour,self)
                pp = point
                
    def clearPlot(self):
        for item in self.childItems():
            self.scene().removeItem(item)
            del item
        self.changed=True
        
    def boundingRect(self):
        return QtCore.QRectF(0,0,self.awidth+self.hmargin*2,self.aheight+self.vmargin*2)

    def computeAxesBoundaries(self):
        self.awidth = self.scene().sceneRect().width()-self.hmargin*2
        self.aheight = self.scene().sceneRect().height()-self.vmargin*2
        xmax = max([len(ser) for ser in self.seriesData])
        if xmax == 0:self.xvmax=1
        else: self.xvmax = (xmax-1)*1.1 
        ymax = -sys.maxint - 1
        ymin = sys.maxint
        
        for ser in self.seriesData:
            for vy in ser:
                if(vy>ymax): ymax=vy
                elif (vy<ymin): ymin=vy
                
        if ymin<0: self.yvmin=ymin*1.1
        elif ymin>0: self.yvmin=ymin*0.9
        else: self.ymin= ymin
        
        if ymax>=0: self.yvmax=ymax*1.1
        else: self.yvmax=ymax*0.9
    
    def decorateAxes(self):
        QtGui.QGraphicsRectItem(self.hmargin,self.vmargin,self.awidth,self.aheight,self)
        self.computeAxesBoundaries()
        self.drawVRefs()
        self.drawHRefs()
        
    def drawVRefs(self):
        minsep=40
        factor=1
        unitincrement=self.aheight/float(self.yvmax-self.yvmin)
        ymaxint=self.yvmax
        yminint=int(self.yvmin)
        pstart=self.value2point(self.xvmin, yminint)
        pxstart=pstart.x()
        py=pstart.y()
        pend = self.value2point(self.xvmax, ymaxint)
        pxend = pend.x()
        pyend= pend.y()
        while (unitincrement*factor<minsep):
            provfactor=2*factor
            if(unitincrement*provfactor>minsep): factor=provfactor
            else: factor=5*factor
                
        print("DRAWVREFS: unitinc is {}/{}, factor is {}".format(unitincrement,minsep,factor))
        while(py>pyend):
            print("ploting line for value {}".format(yminint))
            colour = QtGui.QColor(0,0,0,200)
            PlotLine(pxstart,py,pxend,py,0.5,colour,self)
            py-=unitincrement*factor
            yminint +=factor

    def drawHRefs(self):
        minsep=20
        factor=1
        unitincrement=self.awidth/float(self.xvmax-self.xvmin)
        xmaxint=self.xvmax
        xminint=int(self.xvmin)
        pstart=self.value2point(xminint, self.yvmin)
        px=pstart.x()
        pystart=pstart.y()
        pend = self.value2point(xmaxint, self.yvmin)
        pxend = pend.x()
        pyend = pend.y()-5
        while (unitincrement*factor<minsep):
            provfactor=2*factor
            if(unitincrement*provfactor>minsep): factor=provfactor
            else: factor=5*factor
                
        print("DRAWHREFS: unitinc is {}/{}, factor is {}".format(unitincrement,minsep,factor))
        while(px<=pxend):
            print("ploting mark for value {}".format(xminint))
            colour = QtGui.QColor(0,0,0,255)
            PlotLine(px,pystart,px,pyend,1.5,colour,self)
            px+=unitincrement*factor
            xminint +=factor           
            
    
    def updatePlot(self):
        self.clearPlot()
        self.decorateAxes()
        self.paintSeries()
    
    def paint(self, painter,options,widget): 
        if self.changed:
            self.updatePlot()
            self.changed=False


class PlotLine(QtGui.QGraphicsLineItem):
    def __init__(self,x1,y1,x2,y2,linewidth=None,colour=None,parent=None,scene=None):
        super(PlotLine,self).__init__(x1,y1,x2,y2,parent,scene)
        pen = self.pen()
        if linewidth: pen.setWidthF(linewidth)
        if colour: pen.setColor(colour)
        self.setPen(pen)
    
    def paint(self, painter,options,widget): 
        painter.setRenderHint(QtGui.QPainter.Antialiasing,True);
        super(PlotLine,self).paint(painter,options,widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing,False);


class PlotDot(QtGui.QGraphicsEllipseItem):
    def __init__(self,x,y,width,colour=None,parent=None,scene=None):
        radius=width/2.0
        super(PlotDot,self).__init__(x-radius,y-radius,width,width,parent,scene)
        brush = self.brush()
        brush.setStyle(QtCore.Qt.SolidPattern)
        if colour: 
            brush.setColor(colour)
            pen = self.pen()
            pen.setColor(colour)
            self.setPen(pen)
        self.setBrush(brush)
    
    def paint(self, painter,options,widget): 
        painter.setRenderHint(QtGui.QPainter.Antialiasing,True);
        super(PlotDot,self).paint(painter,options,widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing,False);
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    view = PlotView()
    view.show()
    sys.exit(app.exec_())
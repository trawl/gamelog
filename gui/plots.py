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
    def __init__(self,clrs=colours,parent=None):
        QtGui.QGraphicsView.__init__(self,parent)
        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setSceneRect(QtCore.QRectF(0, 0, 440, 340))
        self.setScene(self.scene)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0,0)))
        self.setMinimumSize(100, 100)
        self.colours=clrs
        
    def setBackground(self,colour):
        self.setBackgroundBrush(QtGui.QBrush(colour))
        
    def addLinePlot(self):
        self.plot = LinePlot(self.colours,None,self.scene)
        
    def addSeries(self,series,label):
        self.plot.plot(series,label)
        
    def clearPlotContents(self):
        self.plot.clearPlotContents()
        
    def addLimit(self,value):
        self.plot.addLimitLine(value)
        
    def resizeEvent(self, event):
        self.scene.setSceneRect(QtCore.QRectF(0, 0, event.size().width(), event.size().height()))
        if self.plot: self.plot.updatePlot()
        
        
class LinePlot(QtGui.QGraphicsItem):
    
    def __init__(self,clrs=None,parent=None, scene=None):
        super(LinePlot,self).__init__(parent, scene)
        self.hmargin = 40
        self.vmargin = 40
        self.awidth = 400
        self.aheight = 300
        self.xvmin = 0
        self.xvmax = 0
        self.yvmin = 0
        self.yvmax = 0
        self.seriesLabels=[]
        self.seriesData=[]
        self.limitvalue=None
        self.changed=False
        self.colours=clrs
                        
    def boundingRect(self):
        return QtCore.QRectF(0,0,self.awidth+self.hmargin*2,self.aheight+self.vmargin*2)
    
    def plot(self,data,label="",linewidth=2.5, linestyle="-",marker='o'):
        self.seriesLabels.append(label)
        self.seriesData.append(data)
        self.changed = True
                    
    def addLimitLine(self,value):
        self.limitvalue = value
        self.updatePlot()
        
    def paint(self, painter,options,widget): 
        if self.changed:
            self.updatePlot()
            self.changed=False

    def updatePlot(self):
        self.clearPlot()
        self.decorateAxes()
        self.paintLimitLine()
        self.paintSeries()      
        
    def clearPlotContents(self):
        self.seriesLabels = []
        self.seriesData = []
        self.limitvalue = None
                
    def clearPlot(self):
        for item in self.childItems():
            self.scene().removeItem(item)
            del item
        self.changed=True
        
    def decorateAxes(self):
        QtGui.QGraphicsRectItem(self.hmargin,self.vmargin,self.awidth,self.aheight,self)
        self.computeAxesBoundaries()
        self.drawVRefs()
        self.drawHRefs()

    def computeAxesBoundaries(self):
        self.awidth = self.scene().sceneRect().width()-self.hmargin*2
        self.aheight = self.scene().sceneRect().height()-self.vmargin*2
        xmax = max([len(ser)-1 for ser in self.seriesData] + [1])
        marginp = 0.05
        gxmargin=self.awidth*marginp*xmax/(self.awidth-self.awidth*marginp)
        self.xvmax=xmax+gxmargin
        
        ymax = 10
        ymin = 0
        for ser in self.seriesData:
            for vy in ser:
                if(vy>ymax): ymax=vy
                if (vy<ymin): ymin=vy
        if self.limitvalue is not None:
            ymax=max([ymax,self.limitvalue])
            ymin=min([ymin,self.limitvalue])
            
        if ymin==0:
            gymargin=self.aheight*marginp * (ymax-ymin)/(self.aheight-self.aheight*marginp)
            self.yvmin=ymin
        else:
            gymargin=self.aheight*marginp * (ymax-ymin)/(self.aheight-2*self.aheight*marginp)
            self.yvmin=ymin-gymargin

        self.yvmax=ymax+gymargin
        
    def drawVRefs(self):
        if self.yvmax< self.yvmin: return
        minsep=30
        factor=1
        try:
            unitincrement=self.aheight/float(self.yvmax-self.yvmin)
        except ZeroDivisionError:
            print("Division by zero in drawVRefs. Limits are {}-{}".format(self.yvmin,self.yvmax))
            
        while (unitincrement*factor<minsep):
            provfactor=2*factor
            if(unitincrement*provfactor>minsep): 
                factor=provfactor
                break
            provfactor=5*factor
            if(unitincrement*provfactor>minsep): 
                factor=provfactor
                break
            factor=10*factor
        if (self.yvmin<=0):        vy=int(self.yvmin/factor)*factor
        else:   vy=(int(self.yvmin/factor)+1)*factor
        pstart=self.value2point(self.xvmin, vy)
        pxstart=pstart.x()
        py=pstart.y()
        pend = self.value2point(self.xvmax, self.yvmax)
        pxend = pend.x()
        pyend= pend.y()
            
        while(py>pyend):
            colour = QtGui.QColor(0,0,0,200)
            if vy==0:
                PlotLine(pxstart-2,py,pxend,py,1.5,QtCore.Qt.black,self)
            else:
                PlotLine(pxstart-2,py,pxend,py,0.5,colour,self)
            nlabel=QtGui.QGraphicsSimpleTextItem("{}".format(vy),self)
            nlabelrect = nlabel.boundingRect()
            nlabel.setPos(pxstart - nlabelrect.width() - 5,py-nlabelrect.height()/2)
            py-=unitincrement*factor
            vy +=factor

    def drawHRefs(self):
        minsep=30
        factor=1
        unitincrement=self.awidth/float(self.xvmax-self.xvmin)
        xmaxint=self.xvmax
        vx=int(self.xvmin)
        pstart=self.value2point(vx, self.yvmin)
        px=pstart.x()
        pystart=pstart.y()
        pend = self.value2point(xmaxint, self.yvmin)
        pxend = pend.x()
        pyend = pend.y()-2
        
        while (unitincrement*factor<minsep):
            provfactor=2*factor
            if(unitincrement*provfactor>minsep): 
                factor=provfactor
                break
            provfactor=5*factor
            if(unitincrement*provfactor>minsep): 
                factor=provfactor
                break
            factor=10*factor
            
#        px+=unitincrement*factor
#        vx +=factor        
                
        while(px<=pxend):
            colour = QtGui.QColor(0,0,0,255)
            PlotLine(px+0.5,pystart+2,px+0.5,pyend,1.5,colour,self)
            nlabel=QtGui.QGraphicsSimpleTextItem("{}".format(vx),self)
            nlabelrect = nlabel.boundingRect()
            nlabel.setPos(px + 0.5 - nlabelrect.width()/2, pystart+3)
            px+=unitincrement*factor
            vx +=factor        

    def paintLimitLine(self):
        if self.limitvalue is None: return
        pstart=self.value2point(self.xvmin, self.limitvalue)
        pxstart=pstart.x()+2
        pystart=pstart.y()
        pend = self.value2point(self.xvmax, self.limitvalue)
        pxend = pend.x()
        pyend= pend.y()
        limitline = PlotLine(pxstart,pystart,pxend,pyend,4,QtCore.Qt.red,self)
        pen = limitline.pen()
        pen.setStyle(QtCore.Qt.DotLine)
        limitline.setPen(pen)
        
    def paintSeries(self):
        for i,ser in enumerate(self.seriesData):
            pp = None
            colour = self.colours[i]
            for vx,vy in enumerate(ser):
                point = self.value2point(vx, vy)
                dot = PlotDot(point.x(),point.y(),10,colour,self)
                dot.setMetaData({'label':self.seriesLabels[i],'x':vx,'y':vy})
                if vx>0: PlotLine(pp.x(),pp.y(),point.x(),point.y(),3,colour,self)
                pp = point        
                
    def value2point(self,vx,vy):
        px=self.hmargin+vx*self.awidth/float(self.xvmax-self.xvmin)
        py=self.vmargin+self.aheight-(vy-self.yvmin)*self.aheight/float(self.yvmax-self.yvmin)
        return QtCore.QPointF(px,py)


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
#         self.setAcceptHoverEvents(True)
        
    def setMetaData(self,md):
        try:
            tt = "{}: ({},{})".format(md["label"],md["x"],md["y"])
            self.setToolTip(tt)
        except KeyError: pass
                
    def hoverEnterEvent(self, *args, **kwargs):
        if self.metadata is not None:
            print("hoovering...")
    
    def paint(self, painter,options,widget): 
        painter.setRenderHint(QtGui.QPainter.Antialiasing,True);
        super(PlotDot,self).paint(painter,options,widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing,False);
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    view = PlotView()
    view.addLinePlot()
    data=[0,1,2,4,8,16,8,4,2,1,0]
    view.addSeries(data,"test1")
    data=[0,-1,-2,-4,-8,-16,-8,-4,-2,-1,0]
    view.addSeries(data,"test2")
    view.addLimit(9)
    view.show()
    sys.exit(app.exec_())
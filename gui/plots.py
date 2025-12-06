#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from PySide6 import QtCore, QtGui
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
)

colours = [
    QtGui.QColor(237, 44, 48),
    #  QtGui.QColor(23, 89, 169),
    QtGui.QColor(123, 164, 218),
    QtGui.QColor(0, 140, 70),
    QtGui.QColor(243, 124, 33),
    QtGui.QColor(147, 112, 219),
    #  QtGui.QColor(101, 43, 145),
    #  QtGui.QColor(161, 29, 33),
    QtGui.QColor(255, 0, 255),
]


class PlotView(QGraphicsView):
    def __init__(self, clrs=colours, parent=None):
        QGraphicsView.__init__(self, parent)
        self._scene = QGraphicsScene(self)
        self._scene.setSceneRect(QtCore.QRectF(0, 0, 440, 340))
        self.setScene(self._scene)
        self.setMinimumSize(100, 100)
        self.colours = clrs

    def setBackground(self, colour):
        self.setBackgroundBrush(QtGui.QBrush(colour))

    def addLinePlot(self):
        self.plot = LinePlot(self.colours)
        self._scene.addItem(self.plot)

    def addHHeaders(self, headers):
        self.plot.addHHeaders(headers)

    def addSeries(self, series, label):
        self.plot.plot(series, label)

    def clearPlotContents(self):
        self.plot.clearPlotContents()

    def addLimit(self, value):
        self.plot.addLimitLine(value)

    def resizeEvent(self, event):
        self._scene.setSceneRect(
            QtCore.QRectF(0, 0, event.size().width(), event.size().height())
        )
        if self.plot:
            self.plot.updatePlot()


class LinePlot(QGraphicsItem):
    def __init__(self, clrs=[], parent=None):
        super(LinePlot, self).__init__(parent)
        self.hmargin = 50
        self.vmargin = 40
        self.awidth = 400
        self.aheight = 300
        self.xvmin = 0
        self.xvmax = 0
        self.yvmin = 0
        self.yvmax = 0
        self.seriesLabels = []
        self.seriesData = []
        self.hheaders = []
        self.limitvalue = None
        self.changed = False
        self.colours = clrs
        self.dark_mode = False
        self.parent = parent
        if QPalette().color(QPalette.ColorRole.Window).red() < 128:
            self.dark_mode = True

    def boundingRect(self):
        return QtCore.QRectF(
            0, 0, self.awidth + self.hmargin * 2, self.aheight + self.vmargin * 2
        )

    def addHHeaders(self, headers):
        self.hheaders = headers

    def plot(self, data, label="", _linewidth=5.0, _linestyle="-", _marker="o"):
        self.seriesLabels.append(label)
        self.seriesData.append(data)
        self.changed = True

    def addLimitLine(self, value):
        self.limitvalue = value
        self.updatePlot()

    def paint(self, painter, options, widget=None):
        new_theme = QPalette().color(QPalette.ColorRole.Window).red() < 128
        if self.dark_mode != new_theme:
            self.dark_mode = new_theme
            self.changed = True
        if self.changed:
            self.updatePlot()
            self.changed = False

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
        self.changed = True

    def decorateAxes(self):
        QGraphicsRectItem(self.hmargin, self.vmargin, self.awidth, self.aheight, self)
        self.computeAxesBoundaries()
        self.drawVRefs()
        self.drawHRefs()

    def computeAxesBoundaries(self):
        self.awidth = self.scene().sceneRect().width() - self.hmargin * 2
        self.aheight = self.scene().sceneRect().height() - self.vmargin * 2
        xmax = max([len(ser) - 1 for ser in self.seriesData] + [1])
        marginp = 0.05
        gxmargin = self.awidth * marginp * xmax / (self.awidth - self.awidth * marginp)
        self.xvmax = xmax + gxmargin

        ymax = 10
        ymin = 0
        for ser in self.seriesData:
            for vy in ser:
                if vy > ymax:
                    ymax = vy
                if vy < ymin:
                    ymin = vy
        if self.limitvalue is not None:
            ymax = max([ymax, self.limitvalue])
            ymin = min([ymin, self.limitvalue])

        if ymin == 0:
            gymargin = (
                self.aheight
                * marginp
                * (ymax - ymin)
                / (self.aheight - self.aheight * marginp)
            )
            self.yvmin = ymin
        else:
            gymargin = (
                self.aheight
                * marginp
                * (ymax - ymin)
                / (self.aheight - 2 * self.aheight * marginp)
            )
            self.yvmin = ymin - gymargin

        self.yvmax = ymax + gymargin

    def drawVRefs(self):
        if self.yvmax < self.yvmin or self.aheight <= 0:
            return
        minsep = 30
        factor = 1
        unitincrement = 0
        try:
            unitincrement = self.aheight / float(self.yvmax - self.yvmin)
        except ZeroDivisionError:
            msg = "Division by zero in drawVRefs. Limits are {}-{}"
            print(msg.format(self.yvmin, self.yvmax))

        while unitincrement * factor < minsep:
            provfactor = 2 * factor
            if unitincrement * provfactor > minsep:
                factor = provfactor
                break
            provfactor = 5 * factor
            if unitincrement * provfactor > minsep:
                factor = provfactor
                break
            factor = 10 * factor
        if self.yvmin <= 0:
            vy = int(self.yvmin / factor) * factor
        else:
            vy = (int(self.yvmin / factor) + 1) * factor
        pstart = self.value2point(self.xvmin, vy)
        pxstart = pstart.x()
        py = pstart.y()
        pend = self.value2point(self.xvmax, self.yvmax)
        pxend = pend.x()
        pyend = pend.y()

        if self.dark_mode:
            colour = QtGui.QColor(255, 255, 255, 200)
        else:
            colour = QtGui.QColor(0, 0, 0, 200)

        while py > pyend:
            if vy == 0:
                if self.dark_mode:
                    PlotLine(
                        pxstart - 2,
                        py,
                        pxend,
                        py,
                        1.5,
                        QtCore.Qt.GlobalColor.white,
                        self,
                    )
                else:
                    PlotLine(
                        pxstart - 2,
                        py,
                        pxend,
                        py,
                        1.5,
                        QtCore.Qt.GlobalColor.black,
                        self,
                    )
            else:
                PlotLine(pxstart - 2, py, pxend, py, 0.5, colour, self)
            nlabel = QGraphicsSimpleTextItem("{}".format(vy), self)
            if self.dark_mode:
                nlabel.setBrush(QtGui.QColor(255, 255, 255))
            font = nlabel.font()
            font.setPixelSize(20)
            nlabel.setFont(font)
            nlabelrect = nlabel.boundingRect()
            nlabel.setPos(
                pxstart - nlabelrect.width() - 5, py - nlabelrect.height() / 2
            )
            py -= unitincrement * factor
            vy += factor

    def drawHRefs(self):
        if self.xvmax < self.xvmin or self.awidth <= 0:
            return
        minsep = 30
        factor = 1
        unitincrement = self.awidth / float(self.xvmax - self.xvmin)
        xmaxint = self.xvmax
        vx = int(self.xvmin)
        pstart = self.value2point(vx, self.yvmin)
        px = pstart.x()
        pystart = pstart.y()
        pend = self.value2point(xmaxint, self.yvmin)
        pxend = pend.x()
        pyend = pend.y() - 2

        try:
            minsep = 10 * max([len(h) for h in self.hheaders])
        except Exception:
            pass

        while unitincrement * factor < minsep:
            provfactor = 2 * factor
            if unitincrement * provfactor > minsep:
                factor = provfactor
                break
            provfactor = 5 * factor
            if unitincrement * provfactor > minsep:
                factor = provfactor
                break
            factor = 10 * factor

        #        px+=unitincrement*factor
        #        vx +=factor

        while px <= pxend:
            colour = QtGui.QColor(0, 0, 0, 255)
            if self.dark_mode:
                colour = QtGui.QColor(255, 255, 255, 255)
            else:
                colour = QtGui.QColor(0, 0, 0, 255)
            PlotLine(px + 0.5, pystart + 2, px + 0.5, pyend, 1.5, colour, self)
            try:
                header = self.hheaders[vx]
            except IndexError:
                header = vx
            nlabel = QGraphicsSimpleTextItem("{}".format(header), self)
            if self.dark_mode:
                nlabel.setBrush(QtGui.QColor(255, 255, 255))
            font = nlabel.font()
            font.setPixelSize(20)
            nlabel.setFont(font)
            nlabelrect = nlabel.boundingRect()
            nlabel.setPos(px + 0.5 - nlabelrect.width() / 2, pystart + 3)
            px += unitincrement * factor
            vx += factor

    def paintLimitLine(self):
        if self.limitvalue is None:
            return
        pstart = self.value2point(self.xvmin, self.limitvalue)
        pxstart = pstart.x() + 2
        pystart = pstart.y()
        pend = self.value2point(self.xvmax, self.limitvalue)
        pxend = pend.x()
        pyend = pend.y()
        limitline = PlotLine(
            pxstart, pystart, pxend, pyend, 4, QtCore.Qt.GlobalColor.red, self
        )
        pen = limitline.pen()
        pen.setStyle(QtCore.Qt.PenStyle.DotLine)
        limitline.setPen(pen)

    def paintSeries(self):
        for i, ser in enumerate(self.seriesData):
            pp = None
            colour = self.colours[i]
            for vx, vy in enumerate(ser):
                point = self.value2point(vx, vy)
                dot = PlotDot(point.x(), point.y(), 15, colour, self)
                dot.setMetaData({"label": self.seriesLabels[i], "x": vx, "y": vy})
                if vx > 0 and pp is not None:
                    PlotLine(pp.x(), pp.y(), point.x(), point.y(), 5, colour, self)
                pp = point

    def value2point(self, vx, vy):
        px = self.hmargin + vx * self.awidth / float(self.xvmax - self.xvmin)
        py = (
            self.vmargin
            + self.aheight
            - (vy - self.yvmin) * self.aheight / float(self.yvmax - self.yvmin)
        )
        return QtCore.QPointF(px, py)


class PlotLine(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, linewidth=None, colour=None, parent=None):
        super(PlotLine, self).__init__(x1, y1, x2, y2, parent)
        pen = self.pen()
        if linewidth:
            pen.setWidthF(linewidth)
        if colour:
            pen.setColor(colour)
        self.setPen(pen)

    def paint(self, painter, options, widget=None):
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        super(PlotLine, self).paint(painter, options, widget)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, False)


class PlotDot(QGraphicsEllipseItem):
    def __init__(self, x, y, width, colour=None, parent=None):
        radius = width / 2.0
        super(PlotDot, self).__init__(x - radius, y - radius, width, width, parent)
        brush = self.brush()
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        if colour:
            brush.setColor(colour)
            pen = self.pen()
            pen.setColor(colour)
            self.setPen(pen)
        self.setBrush(brush)

    #         self.setAcceptHoverEvents(True)

    def setMetaData(self, md):
        try:
            tt = "{}: ({},{})".format(md["label"], md["x"], md["y"])
            self.setToolTip(tt)
        except KeyError:
            pass

    def paint(self, painter, options, widget=None):
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        super(PlotDot, self).paint(painter, options, widget)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = PlotView()
    view.addLinePlot()
    data = [0, 1, 2, 4, 8, 16, 8, 4, 2, 1, 0]
    view.addSeries(data, "test1")
    data = [0, -1, -2, -4, -8, -16, -8, -4, -2, -1, 0]
    view.addSeries(data, "test2")
    view.addLimit(9)
    view.show()
    sys.exit(app.exec_())

from PyQt5 import QtWidgets, QtCore, QtGui


class JumpSlider(QtWidgets.QSlider):
    def __init__(self, parent=None):
        super().__init__(QtCore.Qt.Horizontal, parent)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        sr = self.style().subControlRect(
            QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self
        )
        if event.button() == QtCore.Qt.LeftButton and not sr.contains(event.pos()):
            new_val = int(
                self.minimum()
                + ((self.maximum() - self.minimum()) * event.x()) / self.width()
            )
            # Do not expect appearance to be inverted.
            assert not self.invertedAppearance()
            self.setValue(new_val)
            event.accept()
        super().mousePressEvent(event)

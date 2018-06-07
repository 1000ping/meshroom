import os
import signal
import sys

from PySide2.QtCore import Qt, QObject, Slot, Signal, Property
from PySide2.QtGui import QPalette, QColor, QIcon
from PySide2.QtWidgets import QApplication

from meshroom.ui.components.filepath import FilepathHelper
from meshroom.ui.reconstruction import Reconstruction
from meshroom.ui.utils import QmlInstantEngine

from meshroom.ui import components
from meshroom.core import nodesDesc


class PaletteManager(QObject):

    def __init__(self, qmlEngine, parent=None):
        super(PaletteManager, self).__init__(parent)
        self.qmlEngine = qmlEngine
        darkPalette = QPalette()
        window = QColor(50, 52, 55)
        text = QColor(200, 200, 200)
        disabledText = text.darker(170)
        base = window.darker(150)
        button = window.lighter(115)
        dark = window.darker(170)

        darkPalette.setColor(QPalette.Window, window)
        darkPalette.setColor(QPalette.WindowText, text)
        darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, disabledText)
        darkPalette.setColor(QPalette.Base, base)
        darkPalette.setColor(QPalette.AlternateBase, QColor(46, 47, 48))
        darkPalette.setColor(QPalette.ToolTipBase, base)
        darkPalette.setColor(QPalette.ToolTipText, text)
        darkPalette.setColor(QPalette.Text, text)
        darkPalette.setColor(QPalette.Disabled, QPalette.Text, disabledText)
        darkPalette.setColor(QPalette.Button, button)
        darkPalette.setColor(QPalette.ButtonText, text)
        darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, disabledText)

        darkPalette.setColor(QPalette.Mid, button.lighter(120))
        darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
        darkPalette.setColor(QPalette.HighlightedText, Qt.white)
        darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
        darkPalette.setColor(QPalette.Shadow, Qt.black)

        self.darkPalette = darkPalette
        self.defaultPalette = QApplication.instance().palette()
        self.togglePalette()

    @Slot()
    def togglePalette(self):
        app = QApplication.instance()
        if app.palette() == self.darkPalette:
            app.setPalette(self.defaultPalette)
        else:
            app.setPalette(self.darkPalette)
        if self.qmlEngine.rootObjects():
            self.qmlEngine.reload()
        self.paletteChanged.emit()

    paletteChanged = Signal()
    palette = Property(QPalette, lambda self: QApplication.instance().palette(), notify=paletteChanged)


if __name__ == "__main__":
    # Force exit on Keyboard Interrupt from command line (Ctrl+C)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    args = [sys.argv[0], '-style', 'fusion'] + sys.argv[1:]  # force Fusion style as default
    # use QApplication (QtWidgets) for Platform.FileDialog fallback on platform without native implementation
    app = QApplication(args)
    app.setOrganizationName('AliceVision')
    app.setApplicationName('Meshroom')
    app.setAttribute(Qt.AA_EnableHighDpiScaling)

    font = app.font()
    font.setPointSize(9)
    app.setFont(font)

    pwd = os.path.dirname(__file__)
    app.setWindowIcon(QIcon(os.path.join(pwd, "img/meshroom.svg")))
    qmlDir = os.path.join(pwd, "qml")
    url = os.path.join(qmlDir, "main.qml")
    engine = QmlInstantEngine()
    engine.addFilesFromDirectory(qmlDir, recursive=True)
    engine.setWatching(os.environ.get("MESHROOM_INSTANT_CODING", False))
    # whether to output qml warnings to stderr (disable by default)
    engine.setOutputWarningsToStandardError(os.environ.get("MESHROOM_OUTPUT_QML_WARNINGS", "") == "1")
    engine.addImportPath(qmlDir)
    components.registerTypes()

    # expose available node types that can be instantiated
    engine.rootContext().setContextProperty("_nodeTypes", sorted(nodesDesc.keys()))
    r = Reconstruction(parent=app)
    engine.rootContext().setContextProperty("_reconstruction", r)
    pm = PaletteManager(engine, parent=app)
    engine.rootContext().setContextProperty("_PaletteManager", pm)
    fpHelper = FilepathHelper(parent=app)
    engine.rootContext().setContextProperty("Filepath", fpHelper)
    # Request any potential computation to stop on exit
    app.aboutToQuit.connect(r.stopExecution)

    engine.load(os.path.normpath(url))

    app.exec_()


import sys
import IssueChecker 

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtGui import QGuiApplication

class AnalysisInterface(QObject):

    fileProcessed = pyqtSignal(int, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checker = IssueChecker.IssueChecker()

    def analyzeFile(self, path):
        issueCount, data, code = self.checker.analyzeFile(path)
        self.fileProcessed.emit(issueCount, data, code)

app = QGuiApplication(sys.argv)
interface = AnalysisInterface()

engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty('ISSUE_CHECKER', interface)
engine.quit.connect(app.quit)
engine.load('./ui/Main.qml')
if not engine.rootObjects():
    sys.exit(-1)

root_object = engine.rootObjects()[0]
root_object.scanFile.connect(interface.analyzeFile)

sys.exit(app.exec())
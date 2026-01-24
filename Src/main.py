import sys
import IssueChecker 

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable, QThreadPool
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtGui import QGuiApplication

class WorkerSignals(QObject):
    result = pyqtSignal(int, str, str)

class AnalysisWorker(QRunnable):
    def __init__(self, checker, path):
        super().__init__()
        self.checker = checker
        self.path = path
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            issueCount, data, code = self.checker.analyzeFile(self.path)
            self.signals.result.emit(issueCount, data, code)
        except Exception as e:
            print(f"Error in worker: {e}")

class AnalysisInterface(QObject):

    fileProcessed = pyqtSignal(int, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checker = IssueChecker.IssueChecker()
        self.threadPool = QThreadPool()

    def analyzeFile(self, path):
        worker = AnalysisWorker(self.checker, path)
        worker.signals.result.connect(self.fileProcessed.emit)
        self.threadPool.start(worker)

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
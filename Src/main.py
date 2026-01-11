import sys

from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtGui import QGuiApplication

app = QGuiApplication(sys.argv)

engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)
engine.load('./ui/main.qml')
if not engine.rootObjects():
    sys.exit(-1)

sys.exit(app.exec())
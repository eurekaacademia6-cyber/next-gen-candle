from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

app=QApplication([])
window=MainWindow()
window.show()
raise SystemExit(app.exec())

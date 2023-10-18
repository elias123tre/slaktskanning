import os
import sys
from collections import OrderedDict
from pathlib import Path

from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from metadata import METADATA_SCHEMA, save_info


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(True)
        # self.setFixedSize(200, 200)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Klicka för att markera en person")
        self.setStyleSheet("border: 1px solid black;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.x() / self.width()
            y = event.y() / self.height()
            print(f"Clicked at {x}, {y}")

            menu = QMenu(self)
            menu.addAction("Tagga person")

            # show popup menu at clicked position
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action:
                print("Tagga person")


class PhotoMetaApp(QMainWindow):
    show_window_signal = Signal()

    def __init__(self):
        super().__init__()

        self.observer = None
        self.file_handler = FileHandler(self)

        self.initUI()
        self.tray_icon = self.create_system_tray()

        self.watched_directory = Path.home() / "Pictures" / "Skanningar"
        if not self.watched_directory.exists():
            self.change_scan_folder()
            if not self.watched_directory.exists():
                self.quit_app()
        else:
            self.setup_file_observer()
            self.tray_icon.setToolTip(f"Släktskanning\n{self.watched_directory}")
        self.selected_file = None

        self.show_window_signal.connect(self.show_window)

    def initUI(self):
        self.setWindowTitle("Släktskanning")
        # self.setGeometry(100, 100, 600, 400)

        app_icon = QIcon(resource_path("icon.png"))
        self.setWindowIcon(app_icon)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        image_layout = QHBoxLayout()
        fields_layout = QVBoxLayout()

        # Image
        self.image_label = ImageLabel()
        image_layout.addWidget(self.image_label)
        image_layout.addStretch(1)
        layout.addLayout(image_layout)

        self.fields = OrderedDict()
        for key, value in METADATA_SCHEMA.items():
            label = QLabel(value["label"])
            if value.get("multiline"):
                field_input = QTextEdit()
            else:
                field_input = QLineEdit()
            field_input.setPlaceholderText("\t".join(value["examples"]))
            self.fields[key] = field_input
            fields_layout.addWidget(label)
            fields_layout.addWidget(field_input)
            if value.get("multiline"):
                fields_layout.addStretch(1)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.submit)
        fields_layout.addWidget(submit_button)

        layout.addLayout(fields_layout)

        central_widget.setLayout(layout)

    def create_system_tray(self):
        tray_icon = QSystemTrayIcon(QPixmap(resource_path("icon.png")))
        tray_menu = QMenu()

        open_file_action = QAction("Öppna fil för att lägga till metadata", self)
        open_file_action.triggered.connect(self.open_single_file)
        choose_folder_action = QAction("Välj inskanningsmapp", self)
        choose_folder_action.triggered.connect(self.change_scan_folder)
        exit_action = QAction("Avsluta", self)
        exit_action.triggered.connect(self.quit_app)

        tray_menu.addAction(open_file_action)
        tray_menu.addAction(choose_folder_action)
        tray_menu.addAction(exit_action)
        tray_icon.setContextMenu(tray_menu)
        tray_icon.activated.connect(self.tray_activated)
        tray_icon.show()
        return tray_icon

    def show_window(self):
        self.show()
        if self.selected_file:
            self.image_label.setPixmap(QPixmap(str(self.selected_file)))
            self.setWindowTitle(f"Släktskanning - {self.selected_file.name}")
        for _, value in self.fields.items():
            value.clear()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.open_single_file()

    def quit_app(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()  # Prevent the default close behavior
        self.hide()  # Hide the window, and it will appear in the system tray

    def setup_file_observer(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

        self.observer = Observer()
        self.observer.schedule(
            self.file_handler, path=self.watched_directory, recursive=False
        )
        self.observer.start()

    def new_scan(self, event):
        if event.event_type == "created":
            image = Path(event.src_path)
            if image.suffix in [".jpg", ".jpeg", ".png", ".gif"]:
                self.selected_file = image
                self.show_window_signal.emit()

    def open_single_file(self):
        image_file, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            str(self.watched_directory.absolute())
            if self.watched_directory.exists()
            else "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*)",
        )
        if image_file:
            self.selected_file = Path(image_file)
            self.show_window()
        else:
            self.show()
            self.hide()

    def change_scan_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Välj inskanningsmapp",
            str(self.watched_directory.absolute())
            if self.watched_directory.exists()
            else "",
        )
        if folder:
            self.watched_directory = Path(folder).expanduser()
            if self.watched_directory.exists():
                self.setup_file_observer()
                self.tray_icon.setToolTip(f"Släktskanning\n{self.watched_directory}")
                self.show()
                self.hide()

    def submit(self):
        metadata = []
        for key, value in self.fields.items():
            if isinstance(value, QTextEdit):
                text_content = value.toPlainText()
            else:
                text_content = value.text()
            if text_content:
                metadata.append((key, text_content))
        save_info(self.selected_file, metadata)
        self.hide()


class FileHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        self.app.new_scan(event)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    window = PhotoMetaApp()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


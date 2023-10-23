import configparser
import os
import sys
from collections import OrderedDict
from pathlib import Path

from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QIcon, QPixmap, QPainter, QBrush, QPen
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
    QDialog,
)
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from metadata import METADATA_SCHEMA, PEOPLE_METADATA, save_info

CONFIG_PATH = (
    Path(os.getenv("APPDATA")) / "slaktskanning.ini"
    if os.name == "nt"
    else Path.home() / ".slaktskanning.ini"
)


class ImageLabel(QLabel):
    def __init__(self, parent=None, people: list[dict] | None = None):
        super().__init__(parent)
        self.people = people
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(True)
        # self.setFixedSize(200, 200)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Klicka för att markera en person")

        self.people_dots_size = 10
        self.people_dots_color = Qt.red
        self.people_dots_pen = Qt.black
        self.people_dots_pen_width = 2

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(self.people_dots_pen, self.people_dots_pen_width))
        painter.setBrush(QBrush(self.people_dots_color))
        for person in self.people:
            x, y = person["coordinates"]
            painter.drawEllipse(
                x * self.width() - self.people_dots_size / 2,
                y * self.height() - self.people_dots_size / 2,
                self.people_dots_size,
                self.people_dots_size,
            )

    def remove_person(self, x, y):
        self.people.remove(
            next(person for person in self.people if person["coordinates"] == (x, y))
        )

    def edit_person(self, x, y, values: dict | None = None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Tagga person")
        dialog.setModal(True)
        # dialog.resize(400, 300)
        dialog.setLayout(QVBoxLayout())

        fields = OrderedDict()
        for key, value in PEOPLE_METADATA.items():
            label = QLabel(value["label"])
            if value.get("multiline"):
                field_input = QTextEdit()
            else:
                field_input = QLineEdit()
            field_input.setPlaceholderText("  |  ".join(value["examples"]))
            fields[key] = field_input
            dialog.layout().addWidget(label)
            dialog.layout().addWidget(field_input)
            if value.get("multiline"):
                dialog.layout().addStretch(1)

        if values is not None:
            for key, value in values.items():
                fields[key].setText(value)

            delete_button = QPushButton("Ta bort")
            delete_button.clicked.connect(
                lambda: self.remove_person(x, y) or dialog.reject()
            )
            dialog.layout().addWidget(delete_button)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(dialog.accept)
        dialog.closeEvent = lambda event: dialog.reject()

        dialog.layout().addWidget(submit_button)
        dialog.exec_()

        if dialog.result():
            self.save_person(fields, x, y)

    def save_person(self, fields, x, y):
        metadata = []
        for key, value in fields.items():
            if isinstance(value, QTextEdit):
                text_content = value.toPlainText()
            else:
                text_content = value.text()
            if text_content:
                metadata.append((key, text_content))
        if metadata:
            for person in self.people:
                px, py = person["coordinates"]
                if px == x and py == y:
                    person["metadata"] = metadata
                    return
            self.people.append(
                {
                    "coordinates": (x, y),
                    "metadata": metadata,
                }
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.x() / self.width()
            y = event.y() / self.height()

            for person in self.people:
                px, py = person["coordinates"]
                if (
                    abs(x - px) < self.people_dots_size / 2 / self.width()
                    and abs(y - py) < self.people_dots_size / 2 / self.height()
                ):
                    self.edit_person(px, py, dict(person["metadata"]))
                    return

            menu = QMenu(self)
            menu.addAction("Tagga person")
            menu.addAction("Okänd person")

            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action:
                if action.text() == "Tagga person":
                    self.edit_person(x, y)
                else:
                    self.people.append(
                        {
                            "coordinates": (x, y),
                            "metadata": [],
                        }
                    )
                    self.update()


class PhotoMetaApp(QMainWindow):
    show_window_signal = Signal()

    people: list[dict] = []

    def __init__(self):
        super().__init__()

        self.observer = None
        self.file_handler = FileHandler(self)

        self.initUI()
        self.tray_icon = self.create_system_tray()

        config = get_config()
        directory = config.get("General", "scan_directory", fallback=None)
        self.watched_directory = Path(directory).expanduser() if directory else None
        if self.watched_directory and self.watched_directory.exists():
            self.setup_file_observer()
            self.tray_icon.setToolTip(f"Släktskanning\n{self.watched_directory}")
            save_config({"scan_directory": str(self.watched_directory)})
        else:
            self.change_scan_folder()
            if not self.watched_directory.exists():
                self.quit_app()
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
        self.image_label = ImageLabel(people=self.people)
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
            field_input.setPlaceholderText("  |  ".join(value["examples"]))
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
            (
                str(self.watched_directory.absolute())
                if self.watched_directory.exists()
                else ""
            ),
            "Image Files (*.png *.jpg *.jpeg *.gif);;All Files (*)",
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
            (
                str(self.watched_directory.absolute())
                if self.watched_directory and self.watched_directory.exists()
                else ""
            ),
        )
        if folder:
            self.watched_directory = Path(folder).expanduser()
            if self.watched_directory.exists():
                self.setup_file_observer()
                self.tray_icon.setToolTip(f"Släktskanning\n{self.watched_directory}")
                save_config({"scan_directory": str(self.watched_directory)})
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
        save_info(self.selected_file, metadata, self.people)
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


def get_config():
    """Save the scan folder in a config file in AppData/slaktskanning.ini on windows and ~/.slaktskanning.ini to persist between sessions"""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")
    return config


def save_config(new_config: dict):
    """Save the scan folder in a config file in AppData/slaktskanning.ini on windows and ~/.slaktskanning.ini to persist between sessions"""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")
    for key, value in new_config.items():
        if not config.has_section("General"):
            config.add_section("General")
        config.set("General", key, value)
    with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
        config.write(config_file)


def main():
    app = QApplication(sys.argv)
    window = PhotoMetaApp()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

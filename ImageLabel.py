from meta_schema import PEOPLE_METADATA


from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QBrush, QPainter, QPen, QPixmap
from PySide2.QtWidgets import (
    QComboBox,
    QDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


from collections import OrderedDict


def get_text_content(component):
    if isinstance(component, QTextEdit):
        return component.toPlainText()
    elif isinstance(component, QComboBox):
        return component.currentText()
    else:
        return component.text()


class ImageLabel(QLabel):
    def __init__(self, parent=None, people: list[dict] | None = None):
        super().__init__(parent)
        self.people = people
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(True)
        self.setFixedSize(512, 512)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Klicka för att markera en person")

        self.people_dots_size = 10
        self.people_dots_color = Qt.red
        self.people_dots_pen = Qt.black
        self.people_dots_pen_width = 2

    def setPixmap(self, arg__1: QPixmap) -> None:
        if arg__1.height() != 0:
            aspect_ratio = arg__1.width() / arg__1.height()
            # set size of label to aspect ratio
            self.setFixedSize(
                QSize(
                    self.height() * aspect_ratio,
                    self.height(),
                )
            )

        return super().setPixmap(arg__1)

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
            dialog.layout().addWidget(label)
            if value.get("values"):
                field_input = QComboBox()
                field_input.addItem("")
                field_input.addItems(value["values"])
            elif value.get("multiline"):
                field_input = QTextEdit()
                field_input.setPlaceholderText("  |  ".join(value["examples"]))
            else:
                field_input = QLineEdit()
                field_input.setPlaceholderText("  |  ".join(value["examples"]))
            fields[key] = field_input
            dialog.layout().addWidget(field_input)
            if value.get("multiline"):
                dialog.layout().addStretch(1)

        if values is not None:
            for key, value in values.items():
                field = fields.get(key)
                if field and isinstance(field, QComboBox):
                    field.setCurrentText(value)
                elif field:
                    field.setText(value)

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
            text_content = get_text_content(value)
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

from PySide2.QtWidgets import QComboBox, QDialog, QLineEdit, QVBoxLayout


class PersonSearchDialog(QDialog):
    """Dialog to search for person in recent_people. Contains a search box and buttons to select any of the top search results."""

    def __init__(self, parent=None, recent_people: list[dict] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Sök person")
        self.setModal(True)
        self.resize(400, 300)
        self.setLayout(QVBoxLayout())

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Sök efter person")
        self.search_box.textChanged.connect(self.search)
        self.search_box.returnPressed.connect(self.accept)
        self.layout().addWidget(self.search_box)

        self.results = QComboBox()
        self.results.activated.connect(self.accept)
        self.layout().addWidget(self.results)

        self.person = None

        self.recent_people = recent_people

    def search(self, text):
        self.results.clear()
        if self.recent_people:
            matches = []
            for person in self.recent_people:
                person_metadata = dict(person)
                if (
                    text.lower() in person_metadata.get("förnamn", "").lower()
                    or text.lower() in person_metadata.get("efternamn", "").lower()
                    or text.lower() in person_metadata.get("födelsedatum", "").lower()
                ):
                    matches.append(
                        f"{person_metadata.get('förnamn', '')} {person_metadata.get('efternamn', '')} ({person_metadata.get('födelsedatum', '')})"
                    )
            self.results.addItems(matches[:10])

    def accept(self):
        if self.recent_people:
            for person in self.recent_people:
                person_metadata = dict(person)
                if (
                    f"{person_metadata.get('förnamn', '')} {person_metadata.get('efternamn', '')} ({person_metadata.get('födelsedatum', '')})"
                    == self.results.currentText()
                ):
                    self.person = person_metadata
                    break
        super().accept()

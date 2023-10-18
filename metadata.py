from collections import OrderedDict
from datetime import datetime
from pathlib import Path


def save_info(image_path, metadata: list[(str, str)]):
    image = Path(image_path)
    now = datetime.now()
    now = now.astimezone()

    info = [
        f'Datum inskannat:\n{now.strftime("%Y-%m-%d %H:%M:%S GMT%z")}',
        f"Inskannade bildens filstorlek (byte):\n{image.stat().st_size}",
    ]

    for key, value in metadata:
        identifier = METADATA_SCHEMA[key]["identifier"]
        text = value.strip()
        if text:
            info.append(f"{identifier}\n{text}")

    metadata_text = "\n\n".join(info)
    meta = image.with_stem(image.stem + "_metadata").with_suffix(".txt")
    # if file exists rename the old one with its modification date
    if meta.exists():
        modified_date = datetime.fromtimestamp(meta.stat().st_mtime)
        meta.rename(
            meta.with_stem(f"{meta.stem}_{modified_date.strftime('%Y%m%d%H%M%S')}")
        )
    meta.write_text(metadata_text, encoding="utf-8")


METADATA_SCHEMA = OrderedDict(
    {
        "location": {
            "label": "Plats där fotot togs:",
            "identifier": "Plats där fotot togs:",
            "examples": [
                "Österhaninge kyrka",
                "Österhaninge kyrka, Österhaninge, Haninge, Södermanland, Sverige",
                "Gården i Hälsingland",
                "Gården i Hälsingland, Vinkelvägen 15, 11567 Hälsingland",
            ],
        },
        "date_taken": {
            "label": "Datum (och tid) när fotot togs:",
            "identifier": "Datum (och tid) när fotot togs:",
            "examples": [
                "2019-08-10 14:00",
                "2019-08-10",
                "2019-08",
                "2019",
            ],
        },
        "photographer": {
            "label": "Fotograf eller fotostudio:",
            "identifier": "Fotograf eller fotostudio:",
            "examples": [
                "Åke Gustafsson",
                "Åke Gustafsson (Personidentitet 10)",
            ],
        },
        "origin": {
            "label": "Ursprung/källa vart/vem bilden kommer ifrån:",
            "identifier": "Ursprung/källa vart/vem bilden kommer ifrån:",
            "examples": [
                "Hittades i en låda på vinden.",
                "Skickades av Nina Eriksson.",
                "Hittades i en bok om släkten.",
                "Ärvdes av Sven Andersson.",
            ],
        },
        # "people": {
        #     "label": "Personer i bilden (en per rad, vänster till höger, uppifrån och ner):",
        #     "identifier": "Personer i bilden (vänster till höger, uppifrån och ner):",
        #     "multiline": True,
        #     "examples": [
        #         "Nina Eriksson",
        #         "Nina Eriksson (tredje från vänster)",
        #         "Thomas Gustafsson (Personidentitet 11)",
        #         "Nina Eriksson (Personidentitet 10)\nThomas Gustafsson (Personidentitet 11)",
        #     ],
        # },
        "identifying_person": {
            "label": "Vem/vilka identifierade personerna i bilden:",
            "identifier": "Vem/vilka identifierade personerna i bilden:",
            "examples": [
                "Sven Andersson",
                "Sven Andersson (Personidentitet 12)",
                "Sven Andersson, Nina Eriksson",
            ],
        },
        "identifying_person_accuracy": {
            "label": "Säkerhet i identifiering:",
            "identifier": "Säkerhet i identifiering:",
            "examples": [
                "Vet",
                "Säker",
                "Osäker",
                "Gissar",
                "Mycket osäker",
                "Mycket säker",
            ],
        },
        "situation": {
            "label": "Sammanhang/situation som bilden togs:",
            "identifier": "Sammanhang/situation som bilden togs:",
            "examples": [
                "Bröllop i Österhaninge kyrka.",
                "Bröllop i Österhaninge kyrka. Nina och Thomas gifter sig.",
                "Släktträff i bygdegården i Hälsingland",
            ],
        },
        "keywords": {
            "label": "Nyckelord/kategori (separera med komma):",
            "identifier": "Nyckelord/kategori (separera med komma):",
            "examples": [
                "porträtt",
                "studentporträtt",
                "yrkesfoto",
                "semesterresa",
                "vardag hemma",
                "bostadshus",
                "bröllopsfoto, bröllopsfölje",
                "konfirmationsporträtt, konfirmationsklass",
                "militärtjänstporträtt, militärtjänstgrupp",
                "skolporträtt, skolklass, skolbyggnad",
            ],
        },
        "description": {
            "label": "Beskrivning av bilden:",
            "identifier": "Beskrivning av bilden:",
            "multiline": True,
            "examples": [
                "Brudparet står framför altaret och håller varandra i handen.",
            ],
        },
        "notes": {
            "label": "Övriga anteckningar:",
            "identifier": "Övriga anteckningar:",
            "examples": [
                "Bilden är tagen med en digitalkamera.",
                "Datumet är uppskattat.",
                "Bilden är tagen med en mobiltelefon.",
            ],
        },
    }
)

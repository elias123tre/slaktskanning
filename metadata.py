from collections import OrderedDict
from datetime import datetime
from pathlib import Path
import re


def format_field(key: str, text: str, comment: str, indentation: int = 0) -> str:
    indent = " " * indentation
    if "\n" in text:
        text = text.replace("\n", "\n" + indent + "  ")
        result = f"""
{indent}# {comment}
{indent}{key}: |
{indent}  {text}
""".lstrip("\n")
    else:
        text = text.replace(": ", "; ").replace(" #", " /")
        result = f"""
{indent}# {comment}
{indent}{key}: {text}
""".lstrip("\n")
    return result


def save_info(
    image_path, metadata: list[tuple[str, str]], people: list[dict] | None = None
):
    image = Path(image_path)
    image_stat = image.stat()
    now = datetime.now().astimezone()
    created_date = datetime.fromtimestamp(image_stat.st_ctime).astimezone()
    metadata = dict(metadata)

    metadata_text = f"""
# Metadata för inskannad bild

# Filnamn på den inskannade bilden
filnamn: {image.name.replace(" #", " <hashtag>")}
# Datum och tid då metadata skrevs
metadata_skriven: {now.strftime('%Y-%m-%d %H:%M:%S GMT%z')}
# Datum och tid då bildfilen skapades
bildfilen_skapad: {created_date.strftime('%Y-%m-%d %H:%M:%S GMT%z')}
# Bildfilens storlek i byte
bildfilen_storlek_byte: {image_stat.st_size}

""".lstrip("\n")

    if people:
        metadata_text += f"""
# Identifierade personer i bilden
personer:
""".lstrip("\n")
        for person in people:
            x, y = person.get("coordinates", (None, None))
            if not x and not y:
                print("No coordinates for person, skipping")
                continue

            metadata_text += f"""
  - # Koordinater i bilden i procent, utifrån övre vänstra hörnet (bredd, höjd)
    koordinater:
      vänster: {x*100:.3f}%
      upp: {y*100:.3f}%
""".lstrip("\n")

            person_meta = dict(person.get("metadata", []))
            for key, fields in PEOPLE_METADATA.items():
                comment = fields["comment"]
                text = person_meta.get(key, "").strip()
                metadata_text += format_field(key, text, comment, indentation=4)

    for key, fields in METADATA_SCHEMA.items():
        comment = fields["comment"]
        text = metadata.get(key, "").strip()
        metadata_text += format_field(key, text, comment)

    meta_file = image.with_stem(image.stem + "_metadata").with_suffix(".yaml")
    if meta_file.exists():
        modified_date = datetime.fromtimestamp(meta_file.stat().st_mtime)
        meta_file.rename(
            meta_file.with_stem(
                f"{meta_file.stem}_{modified_date.strftime('%Y-%m-%d_%H-%M-%S')}"
            )
        )
    meta_file.write_text(metadata_text, encoding="utf-8")


PEOPLE_METADATA = OrderedDict(
    {
        "förnamn": {
            "label": "Förnamn:",
            "comment": "Förnamn och eventuellt mellannamn",
            "examples": [
                "Nina",
                "Thomas",
            ],
        },
        "efternamn": {
            "label": "Efternamn:",
            "comment": "Efternamn (kan vara flera)",
            "examples": [
                "Eriksson",
                "Gustafsson",
            ],
        },
        "personidentitet": {
            "label": "Personidentitet (Disgen PersonID):",
            "comment": "Personidentitet (Disgen PersonID)",
            "examples": [
                "10",
                "356",
                "4322",
            ],
        },
        "födelsedatum": {
            "label": "Födelsedatum:",
            "comment": "Födelsedatum",
            "examples": [
                "1990-01-01",
                "1990-01",
                "1990",
            ],
        },
        "födelseort": {
            "label": "Födelseort:",
            "comment": "Födelseort",
            "examples": [
                "Stockholm",
                "Stockholm, Sverige",
                "Stockholm, Sverige, Europa",
            ],
        },
        "dödsdatum": {
            "label": "Dödsdatum:",
            "comment": "Dödsdatum",
            "examples": [
                "1990-01-01",
                "1990-01",
                "1990",
            ],
        },
        "dödsort": {
            "label": "Dödsort:",
            "comment": "Dödsort",
            "examples": [
                "Stockholm",
                "Stockholm, Sverige",
                "Stockholm, Sverige, Europa",
            ],
        },
        "anteckningar": {
            "label": "Övriga anteckningar:",
            "comment": "Övriga anteckningar",
            "multiline": True,
            "examples": [
                "Har på sig en grön hatt.",
            ],
        },
    }
)

METADATA_SCHEMA = OrderedDict(
    {
        "plats": {
            "label": "Plats där fotot togs:",
            "comment": "Plats där fotot togs",
            "examples": [
                "Österhaninge kyrka",
                "Österhaninge kyrka, Österhaninge, Haninge, Södermanland, Sverige",
                "Gården i Hälsingland",
                "Gården i Hälsingland, Vinkelvägen 15, 11567 Hälsingland",
            ],
        },
        "datum_taget": {
            "label": "Datum (och tid) när fotot togs:",
            "comment": "Datum (och tid) när fotot togs",
            "examples": [
                "2019-08-10 14:00",
                "2019-08-10",
                "2019-08",
                "2019",
            ],
        },
        "fotograf": {
            "label": "Fotograf eller fotostudio:",
            "comment": "Fotograf eller fotostudio",
            "examples": [
                "Åke Gustafsson",
                "Åke Gustafsson (Personidentitet 10)",
            ],
        },
        "källa": {
            "label": "Ursprung/källa vart/vem bilden kommer ifrån:",
            "comment": "Ursprung/källa vart/vem bilden kommer ifrån",
            "examples": [
                "Hittades i en låda på vinden.",
                "Skickades av Nina Eriksson.",
                "Hittades i en bok om släkten.",
                "Ärvdes av Sven Andersson.",
            ],
        },
        "identifierande_person": {
            "label": "Vem/vilka identifierade personerna i bilden:",
            "comment": "Vem/vilka identifierade personerna som är med i bilden",
            "examples": [
                "Sven Andersson",
                "Sven Andersson (Personidentitet 12)",
                "Sven Andersson, Nina Eriksson",
            ],
        },
        "säkerhet_identifiering": {
            "label": "Säkerhet i identifieringen:",
            "comment": "Säkerhet i identifieringen",
            "examples": [
                "Vet",
                "Säker",
                "Osäker",
                "Gissar",
                "Mycket osäker",
                "Mycket säker",
            ],
        },
        "sammanhang": {
            "label": "Sammanhang/situation som bilden togs:",
            "comment": "Sammanhang/situation som bilden togs",
            "examples": [
                "Bröllop i Österhaninge kyrka.",
                "Bröllop i Österhaninge kyrka. Nina och Thomas gifter sig.",
                "Släktträff i bygdegården i Hälsingland",
            ],
        },
        "nyckelord": {
            "label": "Nyckelord/kategori (separera med komma):",
            "comment": "Nyckelord/kategori (separera med komma)",
            "examples": [
                "militärtjänstporträtt, militärtjänstgrupp",
                "bröllopsfoto, bröllopsfölje",
                "porträtt",
                "studentporträtt",
                "yrkesfoto",
                "semesterresa",
                "vardag hemma",
                "bostadshus",
                "konfirmationsporträtt, konfirmationsklass",
                "skolporträtt, skolklass, skolbyggnad",
            ],
        },
        "beskrivning": {
            "label": "Beskrivning av bilden:",
            "comment": "Beskrivning av bilden",
            "multiline": True,
            "examples": [
                "Brudparet står framför altaret och håller varandra i handen.",
            ],
        },
        "anteckningar": {
            "label": "Övriga anteckningar:",
            "comment": "Övriga anteckningar",
            "examples": [
                "Bilden är tagen med en digitalkamera.",
                "Datumet är uppskattat.",
                "Bilden är tagen med en mobiltelefon.",
            ],
        },
    }
)

from datetime import datetime
from pathlib import Path
import hashlib
import json
from typing import Any

from meta_schema import METADATA_SCHEMA, PEOPLE_METADATA


def dict_hash(dictionary: dict[str, Any]) -> str:
    """MD5 hash of a dictionary.
    https://stackoverflow.com/a/67438471/10767416
    """
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()


metadata_hash = dict_hash(METADATA_SCHEMA)
people_metadata_hash = dict_hash(PEOPLE_METADATA)


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
###############################################
#  __  __      _            _       _         #
# |  \/  |    | |          | |     | |        #
# | \  / | ___| |_ __ _  __| | __ _| |_ __ _  #
# | |\/| |/ _ \ __/ _` |/ _` |/ _` | __/ _` | #
# | |  | |  __/ || (_| | (_| | (_| | || (_| | #
# |_|  |_|\___|\__\__,_|\__,_|\__,_|\__\__,_| #
###############################################

# Filnamn på den inskannade bilden
filnamn: {image.name.replace(" #", " <hashtag>")}

# Datum och tid då metadata skrevs
metadata_skriven: {now.strftime('%Y-%m-%d %H:%M:%S GMT%z')}

# Datum och tid då bildfilen skapades
bildfilen_skapad: {created_date.strftime('%Y-%m-%d %H:%M:%S GMT%z')}

# Bildfilens storlek i byte
bildfilen_storlek_byte: {image_stat.st_size}

# Metadata version
metadata_version: {metadata_hash}

# Personers metadata version
personer_metadata_version: {people_metadata_hash}

""".lstrip("\n")

    if people and len(people) > 0:
        metadata_text += f"""
##############################################
#  _____                                     #
# |  __ \                                    #
# | |__) |__ _ __ ___  ___  _ __   ___ _ __  #
# |  ___/ _ \ '__/ __|/ _ \| '_ \ / _ \ '__| #
# | |  |  __/ |  \__ \ (_) | | | |  __/ |    #
# |_|   \___|_|  |___/\___/|_| |_|\___|_|    #
##############################################

# Identifierade personer i bilden
personer:
""".lstrip("\n")
        for i, person in enumerate(people):
            x, y = person.get("coordinates", (None, None))
            if not x and not y:
                print("No coordinates for person, skipping")
                continue

            if i > 0:
                metadata_text += f"""
#--------------------------------------------------------------------------------------------------#

""".lstrip("\n")

            metadata_text += f"""
  - # Koordinater i bilden i procent, utifrån övre vänstra hörnet (bredd, höjd)
    koordinater:
      vänster: {x*100:.2f}%
      upp: {y*100:.2f}%

""".lstrip("\n")

            person_meta = dict(person.get("metadata", []))
            for key, fields in PEOPLE_METADATA.items():
                comment = fields["comment"]
                text = person_meta.get(key, "").strip()
                metadata_text += format_field(key, text, comment, indentation=4)

    metadata_text += f"""
################################
#  ____  _ _     _             #
# |  _ \(_) |   | |            #
# | |_) |_| | __| | ___ _ __   #
# |  _ <| | |/ _` |/ _ \ '_ \  #
# | |_) | | | (_| |  __/ | | | #
# |____/|_|_|\__,_|\___|_| |_| #
################################

""".lstrip("\n")

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



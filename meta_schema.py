from collections import OrderedDict


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
        "säkerhet_identifiering": {
            "label": "Säkerhet i identifieringen:",
            "comment": "Säkerhet i identifieringen",
            "values": [
                "Helt säker",
                "Säker",
                "Osäker",
                "Mycket osäker",
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
            "label": "Ursprung/källa var/vem bilden kommer ifrån:",
            "comment": "Ursprung/källa var/vem bilden kommer ifrån",
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
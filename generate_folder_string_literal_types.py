from pathlib import Path as LibPath
from typing import (
    TypedDict,
    List,
    NotRequired,
    Optional,
    Type,
    Union,
    TypeVar,
    Generic,
    Literal,
    LiteralString,
)
from os import getcwd


T = TypeVar("T")

E = TypeVar("E")


class EAEM(TypedDict, Generic[T, E], total=False):
    exclude_map: T
    excludes: List[E]


cwd = LibPath(getcwd())
this_path = LibPath(__file__)


def contains_header_files(dir: LibPath):
    return any(
        file.suffix in (".h", ".hpp") for file in dir.iterdir() if file.is_file()
    )


def generate_types():
    union_string_literals: List[str] = []
    union_dictionary_types: List[str] = []

    read_text = this_path.read_text()

    lines = read_text.split("\n")

    last_index = 0

    new_text = ""

    for i in range(len(lines)):
        line = lines[i]
        if line.strip().startswith("generate_types()"):
            last_index = i
            break

    ExcludeMapName = "ExcludeMap"
    CWDExcludeMapName = ExcludeMapName + "CWD"
    ExcludeNames = "ExcludeNames" + "CWD"

    all_dictionary_sections: List[str] = []

    current_dictionary_type: str = (
        ExcludeMapName
        + f' = TypeDict(\n    "{ExcludeMapName}",\n    '
        + '{\n        ".": '
        + f"Union[\n            {CWDExcludeMapName}\n            EAEM[{CWDExcludeMapName}, {ExcludeNames}]\n            List[{ExcludeNames}],\n        ]"
        + "\n    },\n    total=False,\n)"
    )
    print(current_dictionary_type)
    current_string_literals: List[str] = []

    for entry in cwd.iterdir():
        if entry.is_dir():
            if contains_header_files(entry):
                rel_path = entry.relative_to(entry.parent)
                rel_path_string = str(rel_path)
                current_string_literals.append('"' + rel_path_string + '"')

    all_dictionary_sections.append(
        f"\n\n\n{ExcludeNames} = Literal[{", ".join(current_string_literals)}]\n\n"
        + current_dictionary_type
    )

    current_string_literals.clear()

    print(all_dictionary_sections)

    this_path.write_text(read_text)


generate_types()


ExcludeNamesCWDPlatformWindows = Literal["export"]

ExcludeMapCWDPlatform = TypedDict(
    "ExcludeMapPlatform",
    {
        "windows": List[ExcludeNamesCWDPlatformWindows],
    },
    total=False,
)


ExcludeNamesCWDPlatform = Literal["windows"]

ExcludeMapCWD = TypedDict(
    "ExcludeMapCWD",
    {
        "platform": Union[
            ExcludeMapCWDPlatform,
            EAEM[ExcludeMapCWDPlatform, ExcludeNamesCWDPlatform],
            List[ExcludeNamesCWDPlatform],
        ]
    },
    total=False,
)


ExcludeNamesCWD = Literal["platform"]

ExcludeMap = TypedDict(
    "ExcludeMap",
    {
        ".": Union[
            ExcludeMapCWD, EAEM[ExcludeMapCWD, ExcludeNamesCWD], List[ExcludeNamesCWD]
        ],
    },
    total=False,
)

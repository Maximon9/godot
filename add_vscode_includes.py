# from glob import glob
from json import dumps, loads
from os import environ
from os.path import samefile
from pathlib import Path
from typing import TypedDict, List, NotRequired


class C_CppConfig(TypedDict):
    name: NotRequired[str]
    includePath: NotRequired[List[str]]
    cStandard: NotRequired[str]
    cppStandard: NotRequired[str]
    # intelliSenseMode: NotRequired[str]


class C_CppProperties(TypedDict):
    configurations: NotRequired[List[C_CppConfig]]
    version: NotRequired[int]


search_paths = []
vscode_path = ".vscode"
c_cpp_properties_path = f"{vscode_path}/c_cpp_properties.json"


def is_running_in_vscode_terminal():
    # VS Code sets this in its terminal environment
    return "TERM_PROGRAM" in environ and environ["TERM_PROGRAM"] == "vscode"


def contains_header_files(dir: Path):
    return any(
        file.suffix in (".h", ".hpp") for file in dir.iterdir() if file.is_file()
    )


def grab_all_header_folders(
    path: Path, exclude: List[str], include_paths: List[str], include_all: bool
):
    for entry in path.iterdir():
        if entry.is_dir():
            if contains_header_files(entry):
                path_str = str(entry)

                has_ex_file: bool = False
                for ex_path in exclude:
                    if samefile(path_str, ex_path):
                        has_ex_file = True
                        break

                if has_ex_file:
                    continue

                if samefile(path_str, "platform"):
                    workspace_path_str = "${workspaceFolder}\\" + f"{path_str}\\" + "*"
                    grab_all_header_folders(entry, exclude, include_paths, include_all)
                else:
                    workspace_path_str = (
                        "${workspaceFolder}\\"
                        + f"{path_str}\\"
                        + ("*" if include_all else "**")
                    )

                include_paths.append(workspace_path_str)
            elif include_all == False:
                grab_all_header_folders(entry, exclude, include_paths, include_all)
            if include_all:
                grab_all_header_folders(entry, exclude, include_paths, include_all)


def add_vscode_includes(
    platform: str, exclude: List[str] = [], include_all: bool = False
) -> None:
    if is_running_in_vscode_terminal() == False:
        return

    c_cpp_properties_path_obj: Path = Path(c_cpp_properties_path)
    if c_cpp_properties_path_obj.exists() == False:
        c_cpp_properties_path_obj.parent.mkdir(parents=True, exist_ok=True)
        c_cpp_properties_path_obj.touch()

    c_cpp_json_object: C_CppProperties = loads(c_cpp_properties_path_obj.read_text())

    if not "configurations" in c_cpp_json_object:
        c_cpp_json_object["configurations"] = []

    if not "version" in c_cpp_json_object:
        c_cpp_json_object["version"] = 4

    configs: List[C_CppConfig] = c_cpp_json_object["configurations"]

    has_godot_settings: bool = False

    for config in configs:
        if not "name" in config:
            continue

        if config["name"] == "godot_c_cpp_settings":
            has_godot_settings = True
            break

    include_paths: List[str] = []
    if len(configs) <= 0 or has_godot_settings == False:
        configs.append(
            {
                "name": "godot_c_cpp_settings",
                "includePath": [],
                "cStandard": "c17",
                "cppStandard": "c++17",
            }
        )
    else:
        for config in configs:
            if config["name"] == "godot_c_cpp_settings":
                include_paths = config["includePath"] = []

    platform_dir_path = "platform"

    platform_path_to_include: str = f"{platform_dir_path}\\" + platform

    platform_path = Path(platform_dir_path)

    if platform_path.exists() == False:
        return

    platform_paths: set[str] = set()

    for entry in platform_path.iterdir():
        if entry.is_dir() and contains_header_files(entry):
            platform_paths.add(str(entry))

    platform_paths.remove(platform_path_to_include)

    exclude += platform_paths

    include_paths.append(
        "${workspaceFolder}\\*",
    )
    grab_all_header_folders(Path("."), exclude, include_paths, include_all)

    c_cpp_properties_path_obj.write_text(dumps(c_cpp_json_object, indent=4))

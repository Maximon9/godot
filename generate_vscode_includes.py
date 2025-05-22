# from glob import glob
from json import dumps, loads
from os import environ
from pathlib import Path as LibPath
from typing import TypedDict, Dict, List, NotRequired, Union, Optional
from re import search
from generate_folder_string_literal_types import contains_header_files

Excludes = List[str]


class ExludesAndExludeMap(TypedDict):
    exclude_map: NotRequired["ExcludeMap"]
    excludes: NotRequired[Excludes]


ExcludeMap = Dict[str, Union[Excludes, "ExcludeMap", ExludesAndExludeMap]]


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


def grab_all_header_folders(
    path: LibPath,
    exclude_map: ExcludeMap,
    include_paths: List[str],
    include_files: bool,
    include_all_folders: bool,
    parent_dir: Union[str, None] = None,
):
    for entry in path.iterdir():
        if entry.is_dir():
            new_exlude_map: ExcludeMap = exclude_map
            if parent_dir != None:
                if parent_dir in exclude_map:
                    exclude_data = exclude_map[parent_dir]

                    exludes: Optional[Excludes] = None

                    if isinstance(exclude_data, ExludesAndExludeMap):
                        new_exlude_map = exclude_data["exclude_map"]
                        exludes = exclude_data["excludes"]
                    elif isinstance(exclude_data, ExcludeMap):
                        new_exlude_map = exclude_data
                    else:
                        exludes = exclude_data

                    has_ex_file: bool = False
                    for ex_path in exludes:
                        if entry.samefile(ex_path):
                            has_ex_file = True
                            break

                    if has_ex_file:
                        continue
            if contains_header_files(entry):
                if include_files:
                    for file_entry in entry.iterdir():
                        if (
                            file_entry.is_file()
                            and search(".*\.h(pp)?", str(file_entry)) != None
                        ):
                            workspace_path_str = (
                                "${workspaceFolder}\\" + f"{file_entry}"
                            )
                            include_paths.append(workspace_path_str)

                else:
                    if entry.samefile("platform"):
                        workspace_path_str = "${workspaceFolder}\\" + f"{entry}"
                    else:
                        workspace_path_str = (
                            "${workspaceFolder}\\"
                            + f"{entry}{"" if include_all_folders else "\\**"}"
                        )
                    include_paths.append(workspace_path_str)
            elif include_all_folders == False and include_files == False:
                grab_all_header_folders(
                    entry,
                    new_exlude_map,
                    include_paths,
                    include_files,
                    include_all_folders,
                    parent_dir=str(path),
                )
            if include_all_folders or include_files:
                grab_all_header_folders(
                    entry,
                    new_exlude_map,
                    include_paths,
                    include_files,
                    include_all_folders,
                    parent_dir=str(path),
                )


def generate_vscode_includes(
    platform: str,
    exclude_map: ExcludeMap = {},
    include_files: bool = False,
    include_all_folders: bool = False,
) -> None:
    if is_running_in_vscode_terminal() == False:
        return

    c_cpp_properties_path_obj: LibPath = LibPath(c_cpp_properties_path)
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

    platform_path = LibPath(platform_dir_path)

    if platform_path.exists() == False:
        return

    if not platform_dir_path in exclude_map:
        exclude_map[platform_dir_path] = []

    platform_exludes = exclude_map[platform_dir_path]

    platform_paths: set[str] = set()

    for entry in platform_path.iterdir():
        if entry.is_dir() and contains_header_files(entry):
            platform_paths.add(str(entry))

    platform_paths.remove(platform_path_to_include)

    platform_exludes += platform_paths

    include_paths.append(
        "${workspaceFolder}",
    )
    grab_all_header_folders(
        LibPath("."), exclude_map, include_paths, include_files, include_all_folders
    )

    c_cpp_properties_path_obj.write_text(dumps(c_cpp_json_object, indent=4))

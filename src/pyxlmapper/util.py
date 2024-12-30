import re

from openpyxl.cell import Cell, MergedCell
from openpyxl.styles.styleable import StyleableObject
from openpyxl.worksheet.worksheet import Worksheet
from typing import Any, List, Union, cast


def unwrap(cell: Union[Cell, MergedCell, StyleableObject]):
    """
    Actually get a cell
    """
    sheet = cast(Worksheet, cell.parent)
    match cell:
        case Cell():
            return cell
        case MergedCell():
            rng = [s for s in sheet.merged_cells.ranges if cell.coordinate in s]
            return sheet.cell(rng[0].min_row, rng[0].min_col)
        case _:
            raise TypeError(f"Unknown and unsupported cell type {type(cell)}")


def normalize(value: Any):
    """
    Remove unnecessary garbage from the string
    """
    # TODO switch
    if type(value) == str:
        return value.replace("\n", " ").strip()
    if type(value) == float:
        return str(value)
    return value


def capfirst(value: str):
    if value == "":
        return ""
    if len(value) == 1:
        return value.upper()
    return value[0].upper() + value[1:]


numbers = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]


def stringify_int(num: str):
    head, rest = num[0], num[1:]
    return numbers[int(head)] + rest


def class_name_from_str(value: str) -> str:
    word_re = re.compile(r"(\d+|\w+)")
    matches = re.findall(word_re, value)
    head, rest = matches[0], matches[1:]
    if re.match(r"\d+", head):
        override_head = stringify_int(head)
    else:
        override_head = None

    pieces = [override_head if override_head is not None else head] + rest
    return "".join([capfirst(d) for d in pieces])


camel_re = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")


def camel_to_snake(value: str) -> str:
    return camel_re.sub(r"_\1", value).lower()


def dict_path_set(receiver: dict, path: List[str], value: Any):
    obj = receiver
    for path_item in path[:-1]:
        if not path_item in obj:
            obj[path_item] = {}
        obj = obj[path_item]

    obj[path[-1]] = value

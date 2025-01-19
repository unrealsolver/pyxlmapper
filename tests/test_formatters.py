import pytest

from pyxlmapper.formatters import (
    FlatFormatter,
    PrettyFormatter,
    MapperFormatter,
    TypescriptFormatter,
)
from pyxlmapper.mapper import SpreadsheetMapper


# The most basic mapper
class BasicMapper(SpreadsheetMapper):
    class ChildOne:
        pass

    class ChildTwo:
        pass


# The most basic mapper
class BasicNestedWithDifferentInputNameMapper(SpreadsheetMapper):
    class ChildOne:
        input_name = "c1"

    class ChildTwo:
        input_name = "c2"

        class SubChild:
            input_name = "sc"


# The most basic nested mapper
class BasicNestedMapper(SpreadsheetMapper):
    class Parent:
        class ChildOne:
            pass

        class ChildTwo:
            pass


# The most basic nested mapper with class name duplicates
class NestedDuplicatedMapper(SpreadsheetMapper):
    class Parent:
        class Parent:
            class Child:
                pass


@pytest.mark.parametrize(
    "mapper,lines",
    (
        (BasicMapper, ["A1 -> child_one", "B1 -> child_two"]),
        (BasicNestedMapper, ["A2 -> parent.child_one", "B2 -> parent.child_two"]),
    ),
)
def test_flat_formatter(mapper, lines):
    formatter = FlatFormatter(mapper().root)
    actual = str(formatter).split("\n")
    assert actual == lines


@pytest.mark.parametrize(
    "mapper,lines",
    (
        (
            BasicMapper,
            [
                "Node<BasicMapper (N/A) -- ROOT>",
                "  Node<ChildOne (A1) 'ChildOne' -> 'child_one'>",
                "  Node<ChildTwo (B1) 'ChildTwo' -> 'child_two'>",
            ],
        ),
        (
            BasicNestedMapper,
            [
                "Node<BasicNestedMapper (N/A) -- ROOT>",
                "  Node<Parent (A1) 'Parent' -> 'parent'>",
                "    Node<ChildOne (A2) 'ChildOne' -> 'child_one'>",
                "    Node<ChildTwo (B2) 'ChildTwo' -> 'child_two'>",
            ],
        ),
    ),
)
def test_pretty_formatter(mapper, lines):
    formatter = PrettyFormatter(mapper().root)
    actual = str(formatter).split("\n")
    assert actual == lines


@pytest.mark.parametrize(
    "mapper,lines",
    (
        (
            BasicMapper,
            [
                "from pyxlmapper import SpreadsheetMapper",
                "",
                "",
                "class BasicMapper(SpreadsheetMapper):",
                "    class ChildOne:",
                "        pass",
                "",
                "    class ChildTwo:",
                "        pass",
            ],
        ),
        (
            BasicNestedMapper,
            [
                "from pyxlmapper import SpreadsheetMapper",
                "",
                "",
                "class BasicNestedMapper(SpreadsheetMapper):",
                "    class Parent:",
                "        class ChildOne:",
                "            pass",
                "",
                "        class ChildTwo:",
                "            pass",
            ],
        ),
    ),
)
def test_mapper_formatter(mapper, lines):
    formatter = MapperFormatter(mapper().root)
    actual = str(formatter).split("\n")[:-1]
    assert actual == lines


@pytest.mark.parametrize(
    "mapper,lines",
    (
        (
            BasicMapper,
            [
                "export type BasicMapper = {",
                "  child_one: string;",
                "  child_two: string;",
                "}",
            ],
        ),
        (
            BasicNestedMapper,
            [
                "export type Parent = {",
                "  child_one: string;",
                "  child_two: string;",
                "}",
                "",
                "export type BasicNestedMapper = {",
                "  parent: Parent;",
                "}",
            ],
        ),
        (
            NestedDuplicatedMapper,
            [
                "export type ParentParent = {",
                "  child: string;",
                "}",
                "",
                "export type Parent = {",
                "  parent: ParentParent;",
                "}",
                "",
                "export type NestedDuplicatedMapper = {",
                "  parent: Parent;",
                "}",
            ],
        ),
        (
            BasicNestedWithDifferentInputNameMapper,
            [
                "export type ChildTwo = {",
                "  /** sc */" "  sub_child: string;",
                "}",
                "",
                "export type BasicNestedWithDifferentInputNameMapper = {",
                "  /** c1 */" "  child_one: string;",
                "  /** c2 */" "  child_two: ChildTwo;",
                "}",
            ],
        ),
    ),
)
def test_ts_formatter(mapper, lines):
    formatter = TypescriptFormatter(mapper().root)
    # Ignore preamble, ignore traling \n
    code = str(formatter)
    actual = code.split("\n")[2:-1]
    print(code)
    assert actual == lines

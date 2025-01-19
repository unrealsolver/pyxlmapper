from __future__ import annotations
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, List

from pyxlmapper.util import class_name_from_str


# Avoid circular dep on type import
if TYPE_CHECKING:
    from pyxlmapper.mapper import MapperNode


__all__ = (
    "Formatter",
    "MapperFormatter",
    "TypescriptFormatter",
    "PythonFormatter",
    "PrettyFormatter",
    "FlatFormatter",
)


class Formatter(ABC):
    preamble: str = ""
    tree: MapperNode

    def __init__(self, tree: MapperNode) -> None:
        self.tree = tree

    @abstractmethod
    def format(self) -> str:
        pass

    def __str__(self) -> str:
        return self.format()

    def __repr__(self) -> str:
        return self.format()


class StyledCode:
    spaces = 4

    def pad(self, level: int):
        return " " * level * self.spaces


class MapperFormatter(Formatter, StyledCode):
    """
    Outputs a mapper code
    """

    preamble = "from pyxlmapper import SpreadsheetMapper\n\n\n"

    # @override
    def format(self):
        # [:-1] to remove 1 unnecessary blank line at the end
        return self.preamble + self._format(self.tree, 0)[:-1]

    def _format(self, node: MapperNode, level: int):
        parents = f"(SpreadsheetMapper)" if level == 0 else ""
        class_def = f"{self.pad(level)}class {class_name_from_str(node.config.raw_name)}{parents}:"
        details = ""

        children = "".join([self._format(d, level + 1) for d in node.children])

        for field in node.config._own_fields:
            # Skip fields that are not overriden
            if field not in node.config._overrides:
                continue
            value = getattr(node.config, field)
            str_repr = f'"{value}"' if type(value) == str else value
            details += f"{self.pad(level + 1)}{field} = {str_repr}\n"

        if len(node.config._overrides) == 0 and len(node.children) == 0:
            details += f"{self.pad(level + 1)}pass\n"

        line_skip = "\n" if details != "" else ""

        return f"{class_def}\n{details}{line_skip}{children}"


class TypescriptFormatter(Formatter, StyledCode):
    """
    Outputs typescript definintions
    """

    preamble = "// WARNING! THIS IS GENERATED CODE! DON'T EDIT!\n"
    spaces = 2

    def format(self):
        aliases = dict()  # set of used typenames to avoid duplications
        typedefs: List[str] = [self.preamble]

        # TODO move this aliases thing to a separate method
        # Get all type names in root -> leaf order. Create aliases for duplicates
        for node in filter(lambda d: not d.is_leaf, self.tree):
            typename = class_name_from_str(node.config.raw_name)
            if typename not in aliases.values():
                # Add type name normally
                aliases[node.qualified_name] = typename
                continue

            # Name is already take, alias is needed
            if node.parent is not None:
                parent_alias = aliases[node.parent.qualified_name]
            else:
                parent_alias = "Root"

            alias = parent_alias + typename
            aliases[node.qualified_name] = alias

        # Going in reversed order here
        for node in reversed(list(filter(lambda d: not d.is_leaf, self.tree))):
            typename = aliases[node.qualified_name]
            typedef = f"export type {typename} = {{\n"

            for child in node.children:
                if "input_name" in child.config._overrides:
                    typedef += f"{self.pad(1)}/** {child.config.input_name} */"
                child_type = (
                    "string" if child.is_leaf else aliases[child.qualified_name]
                )
                typedef += f"{self.pad(1)}{child.config.output_name}: {child_type};\n"

            typedef += "}\n"
            typedefs.append(typedef)

        return "\n".join(typedefs)


class PythonFormatter(Formatter):
    """
    Outputs python @dataclass definitions
    """

    pass


class PrettyFormatter(Formatter):
    """
    Pretty print formatter. Easier to read during debug
    """

    def format(self):
        # Remove extra \n with [:-1]
        return self._format(self.tree, 0)[:-1]

    def _format(self, node: MapperNode, level: int):
        padding = "  " * level
        header = f"{padding}{node}"
        details = ""
        if node.config.offset != (0, 0):
            details = f"{padding}  ++ offset={node.config.offset}\n"
        children = "".join([self._format(d, level + 1) for d in node.children])
        return f"{header}\n{details}{children}"


class FlatFormatter(Formatter):
    """
    Outputs 'flat' representations for leaf nodes. Example:
    A2 -> some.path.one
    C2 -> some.other.path
    """

    def format(self):
        nodes = self.tree.get_leaves()
        return "\n".join([f"{d.coordinate} -> {d.qualified_name}" for d in nodes])

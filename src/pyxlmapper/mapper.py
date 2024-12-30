from functools import cached_property
import sys
from typing import (
    ClassVar,
    Iterable,
    List,
    Literal,
    MutableSet,
    Optional,
    Self,
    Tuple,
)
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.utils import get_column_letter
from dataclasses import dataclass, field

from pyxlmapper.util import (
    camel_to_snake,
    class_name_from_str,
    dict_path_set,
    normalize,
    unwrap,
)


@dataclass
class InternalConfig:
    """
    Main config container class
    """

    raw_name: str
    offset: Tuple[int, int]
    input_name: str = ""
    output_name: str = ""

    # Meta
    _overrides: MutableSet[str] = field(default_factory=set)
    """
    List of fields that was explicitly set by the config
    (for reflection purposes)
    """
    _own_fields: ClassVar[Iterable[str]] = ("offset", "input_name", "output_name")
    """
    List of fields that config could have (no internal or meta fields)
    """

    @classmethod
    def from_config(cls, nodeconf: type):
        """
        nodedef is not really 'NodeConfig', but it has matching properties
        """
        name = nodeconf.__name__
        # Set fields
        input_name = getattr(nodeconf, "input_name", name)
        output_name = getattr(nodeconf, "output_name", camel_to_snake(name))
        offset = getattr(nodeconf, "offset", (0, 0))

        # Set metadata
        overrides = set([d for d in cls._own_fields if hasattr(nodeconf, d)])

        return cls(
            raw_name=name,
            offset=offset,
            input_name=input_name,
            output_name=output_name,
            _overrides=overrides,
        )

    @classmethod
    def from_input_name(cls, input_name: str):
        """
        Build config for given header name
        """
        raw_name = class_name_from_str(input_name)
        output_name = camel_to_snake(raw_name)

        overrides = set()

        if raw_name != input_name:
            overrides.add("input_name")

        return cls(
            raw_name=raw_name,
            output_name=output_name,
            input_name=input_name,
            offset=(0, 0),
            _overrides=overrides,
        )

    def __str__(self) -> str:
        return f"{self.raw_name}({self.input_name} -> {self.output_name})"

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, InternalConfig):
            return False

        return (
            self.raw_name == value.raw_name
            and self.input_name == value.input_name
            and self.output_name == value.output_name
            and self.offset == value.offset
        )


@dataclass
class MapperNode:
    """
    Bi-directional tree
    """

    config: InternalConfig
    parent: Optional[Self] = None
    children: List[Self] = field(default_factory=list)

    @classmethod
    def from_config(cls, config: type):
        internal_config = InternalConfig.from_config(config)
        return cls(config=internal_config)

    @classmethod
    def infer(cls, internal_config: InternalConfig):
        return cls(config=internal_config)

    # TODO merge to abs_pos
    @cached_property
    def column(self):
        if self.parent is None:
            return 1

        pos = self.parent.children.index(self)
        if pos > 0:
            sibling = self.parent.children[pos - 1]
        else:
            sibling = None

        previous_node_pos = (
            sibling.last.abs_pos[1]
            if sibling is not None
            else self.parent.abs_pos[1] - 1
        )

        return previous_node_pos + self.config.offset[1] + 1

    @cached_property
    def abs_pos(self) -> Tuple[int, int]:
        if self.parent is None:
            return (1, 1)

        pos = self.parent.children.index(self)
        if pos > 0:
            sibling = self.parent.children[pos - 1]
        else:
            sibling = None

        previous_node_pos = (
            sibling.last.abs_pos[1]
            if sibling is not None
            else self.parent.abs_pos[1] - 1
        )

        return (
            self.parent.abs_pos[0] + self.config.offset[0] + 1,
            previous_node_pos + self.config.offset[1] + 1,
        )

    @property
    def is_root(self):
        return self.parent is None

    @property
    def last(self):
        """
        rightmost child node
        """
        if len(self.children) > 0:
            return self.children[-1].last
        else:
            return self

    @property
    def root(self):
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    @property
    def qualified_name(self):
        path = self.get_path()
        names = map(lambda d: d.config.output_name, path[1:])
        return ".".join(names)

    @property
    def cardinality(self):
        return len(self.children) + sum(d.cardinality for d in self.children)

    @property
    def coordinate(self):
        col = get_column_letter(self.abs_pos[1])
        return f"{col}{self.abs_pos[0]}"

    def add_child(self, child: Self):
        self.children.append(child)
        child.parent = self

    def get_path(self):
        path: List[Self] = []
        node = self
        while node is not None:
            path.append(node)
            node = node.parent
        return list(reversed(path))

    def pretty(self):
        return self._pretty(0)

    def _pretty(self, level: int):
        padding = "  " * level
        header = f"{padding}{self}"
        details = ""
        if self.config.offset != (0, 0):
            details = f"{padding}  ++ offset={self.config.offset}\n"
        children = "".join([c._pretty(level + 1) for c in self.children])
        return f"{header}\n{details}{children}"

    def get_leaves(self):
        return self._get_leaves([])

    def _get_leaves(self, leaves: List[Self]):
        if len(self.children) == 0:
            return leaves + [self]
        else:
            for child in self.children:
                leaves = child._get_leaves(leaves)
        return leaves

    def flat_repr(self):
        nodes = self.get_leaves()
        return "\n".join([f"{d.coordinate} -> {d.qualified_name}" for d in nodes])

    def to_python(self):
        return self._to_python(0)

    def _to_python(self, level):
        padding = "  " * level
        parents = f"(SpreadsheetMapper)" if level == 0 else ""
        class_def = f"{padding}class {self.config.raw_name}{parents}:"
        details = ""

        children = "".join([c._to_python(level + 1) for c in self.children])

        for field in self.config._overrides:
            value = getattr(self.config, field)
            str_repr = f'"{value}"' if type(value) == str else value
            details += f"{padding}  {field} = {str_repr}\n"

        if len(self.config._overrides) == 0 and len(self.children) == 0:
            details += f"{padding}  pass\n"

        line_skip = "\n" if details != "" else ""

        return f"{class_def}\n{details}{line_skip}{children}"

    def __repr__(self) -> str:
        return self.pretty()

    def __str__(self) -> str:
        return f"Node<{self.config.raw_name} ({self.coordinate}) {self.config.input_name} -> {self.config.output_name}>"


def read_classdef(cls: type, parent: MapperNode):
    for key, attr in cls.__dict__.items():
        if key.startswith("__"):
            continue

        if isinstance(attr, type):
            node = MapperNode.from_config(attr)
            parent.add_child(node)
            read_classdef(attr, node)


class SpreadsheetParserMeta(type):
    pass


class SpreadsheetMapper(metaclass=SpreadsheetParserMeta):
    """
    Base class for any mapper definintion
    """

    root: MapperNode

    def __new__(cls) -> Self:
        cls.root = MapperNode.from_config(cls)
        read_classdef(cls, cls.root)

        return super().__new__(cls)

    @classmethod
    def from_node(cls, node: MapperNode):
        self = cls()
        self.root = node
        return self

    def map_rows(self, ws: Worksheet, start_at: int):
        nodes = self.root.get_leaves()

        row_index = start_at
        while True:
            # Receiving obj
            obj = {}

            for col_idx, node in enumerate(nodes):
                cell = ws.cell(row_index, node.column)
                value = normalize(cell.value)

                # Stop on first blank row (cell)
                if col_idx == 0:
                    if value is None:
                        print("Finished")
                        return

                str_path = list(
                    map(lambda d: d.config.output_name, node.get_path()[1:])
                )
                dict_path_set(obj, str_path, value)

            yield obj
            sys.stdout.write(".")

            row_index += 1


def collapse_levels(levels: List[str]) -> List[str]:
    """
    Remove duplicate levels
    """
    collapsed = []
    for level in levels:
        head = collapsed[-1] if len(collapsed) > 0 else None
        if head != level:
            collapsed.append(level)

    return collapsed


def read_header(
    ws: Worksheet,
    height: int,
    width: int | Literal["auto"] | None = None,
    offset: Tuple[int, int] = (0, 0),
):
    if width is None:
        width = "auto"

    col_index = 1

    while True:
        levels = []
        for level in range(1, height + 1):
            cell = unwrap(ws.cell(level + offset[0], col_index + offset[1]))
            value = normalize(cell.value)
            if value is None:
                continue
            levels.append(value)

        # Remove duplicates
        levels = collapse_levels(levels)
        yield levels

        # Next cell
        col_index += 1

        # Done on max width reached
        if width != "auto":
            if col_index > width:
                break

        # Done on no data
        if len(levels) == 0:
            break


def merge(reciever: MapperNode, other: MapperNode):
    """
    :param other: linear tree (no more than 1 child per node)
    :returns: carry-on offset (for the next column)
    """
    assert len(other.children) <= 1  # not tested for > 1

    # Empty root node
    if reciever.is_root and len(reciever.children) == 0:
        reciever.add_child(other)
        return 0

    last_child = reciever.children[-1]
    if last_child.config == other.config:
        if len(other.children) > 0:
            other_last_child = other.children[-1]
            return merge(last_child, other_last_child)
        else:
            return 1
    else:
        reciever.add_child(other)
        return 0


def infer(
    ws: Worksheet,
    height: int,
    name: str,
    width: int | Literal["auto"] | None = None,
    offset: Tuple[int, int] = (0, 0),
):
    """
    Read a header from a real Worksheet
    """
    header = read_header(ws, height, width, offset)
    root_config = InternalConfig(raw_name=name, offset=offset)
    root_node = MapperNode(config=root_config)

    contextual_offset = 0

    for levels in header:
        configs = [InternalConfig.from_input_name(d) for d in levels]
        parent = None
        for _, config in enumerate(configs):
            node = MapperNode.infer(internal_config=config)

            # Link nodes
            if parent is not None:
                parent.add_child(node)
            parent = node
        if parent is not None:
            # Offset should be carried to the next item
            carry_offset = merge(root_node, parent.root)
            if carry_offset > 0:
                contextual_offset += carry_offset
            if contextual_offset > 0 and carry_offset == 0:
                ofst = root_node.last.config.offset
                root_node.last.config.offset = (ofst[0], ofst[1] + contextual_offset)
                # Set metadata (for to str impl)
                root_node.last.config._overrides.add("offset")
                contextual_offset = 0

    return SpreadsheetMapper.from_node(root_node)

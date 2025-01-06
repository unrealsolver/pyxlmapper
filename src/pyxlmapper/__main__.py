import openpyxl
import argparse

from pyxlmapper import infer
from pyxlmapper.formatters import Formatter, MapperFormatter, TypescriptFormatter
from pyxlmapper.mapper import MapperNode

parser = argparse.ArgumentParser(
    prog="pyxlmapper",
    description="Infers and generates mapper class for you. You can use thet class later to map the data",
)

parser.add_argument("filename", help="Path to xlsx file")
parser.add_argument(
    "-s", "--sheet", required=False, help="Name of the worksheet (tab name in xlsx)"
)
parser.add_argument("--height", required=True, type=int, help="number")
parser.add_argument("--width", required=False, help="number or auto")
parser.add_argument(
    "--name", required=False, help="Name of the mapper class (root name)"
)
parser.add_argument(
    "--v-offset",
    required=False,
    type=int,
    default=0,
    help="Vertical offset before reading header",
)
parser.add_argument(
    "--h-offset",
    required=False,
    type=int,
    default=0,
    help="Horizontal offset before reading header",
)
parser.add_argument(
    "-t", "--type", required=False, choices=["mapper", "ts"], default="mapper"
)
parser.add_argument("-o", "--out", required=False, help="Output file")

args = parser.parse_args()

wb = openpyxl.open(args.filename, data_only=True)

if args.sheet is not None:
    ws = wb[args.sheet]
elif len(wb.sheetnames) == 1:
    ws = wb.active
else:
    raise ValueError


offset = (args.v_offset, args.h_offset)

mapper = infer(ws, height=args.height, offset=offset, name=args.name or "Mapper")


def get_formatter(tree: MapperNode) -> Formatter:
    match args.type:
        case "mapper":
            return MapperFormatter(tree)
        case "ts":
            return TypescriptFormatter(tree)
    raise ValueError


formatter = get_formatter(mapper.root)


if args.out is not None:
    with open(args.out, "w") as fd:
        fd.write(str(formatter))
else:
    print(formatter)

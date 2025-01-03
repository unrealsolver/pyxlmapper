import openpyxl
import argparse

from pyxlmapper import infer

parser = argparse.ArgumentParser(
    prog="pyxlmapper",
    description="Infers and generates mapper class for you. You can use thet class later to map the data",
)

parser.add_argument("filename", help="Path to xlsx file")
parser.add_argument(
    "-s", "--sheet", required=True, help="Name of the worksheet (tab name in xlsx)"
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
    "-t", "--type", required=False, choices=["python", "ts"], default="python"
)
parser.add_argument("-o", "--out", required=False, help="Output file")

args = parser.parse_args()

wb = openpyxl.open(args.filename, data_only=True)
ws = wb[args.sheet]

offset = (args.v_offset, args.h_offset)

mapper = infer(ws, height=args.height, offset=offset, name=args.name or "Mapper")

output = mapper.root.to_python()

if args.out is not None:
    with open(args.out, "w") as fd:
        fd.write(output)
else:
    print(output)

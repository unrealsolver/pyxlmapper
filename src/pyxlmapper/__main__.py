import openpyxl
import json
import argparse

from pyxlmapper import infer

parser = argparse.ArgumentParser(
    prog="pyxlmapper", description="Parser and data mapper for excel spreadsheet"
)

parser.add_argument("filename")
parser.add_argument("-s", "--sheet")
parser.add_argument("-p", "--parse")
parser.add_argument("-i", "--infer")
parser.add_argument("-t", "--type")  # json, jsonl
parser.add_argument("-o", "--out")

args = parser.parse_args()

wb = openpyxl.open("data.xlsx", data_only=True)
ws = wb["B650(E)"]
# read_header(ws, height=3, offset=(1, 0))
mapper = infer(ws, height=4, offset=(1, 0), name="B650EMapper")
# print(mapper.root.pretty())
# print(n.root.flat_repr())

# mapper = B650EMapper()
# print(mapper.root.pretty())
# print(mapper.root.flat_repr())
# print(mapper.root.to_python())

print(len(mapper.root.get_leaves()))

docs = []

for obj in mapper.map_rows(ws, start_at=7):
    docs.append(obj)

with open("mapped.json", "w") as fd:
    json.dump(docs, fd)

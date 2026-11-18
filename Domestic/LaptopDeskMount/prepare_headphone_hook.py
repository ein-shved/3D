"""Offline preflight, or add a preparation group to the EXISTING FreeCAD document.

CLI: python prepare_headphone_hook.py --check
FreeCAD: execute this file with __file__ and __name__='__main__'.
No printable geometry is built by this preparation step.
"""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
PLAN_PATH = ROOT / "headphone_hook_plan.json"
PARAMETER_KINDS = ("linked_parameters", "specified_parameters", "provisional_parameters")


def read_plan():
    plan = json.loads(PLAN_PATH.read_text())
    aliases = [r["alias"] for kind in PARAMETER_KINDS
               for r in plan[kind]]
    if len(aliases) != len(set(aliases)):
        raise ValueError("Duplicate hook parameter aliases")
    return plan


def inspect_saved_document(plan):
    """Read the saved native document without FreeCAD or modifying its ZIP."""
    path = ROOT / plan["document"]
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    objects = {o.attrib["name"]: o for o in root.findall("./ObjectData/Object")}
    missing = set(plan["environment_objects"]) - objects.keys()
    if missing:
        raise ValueError("Missing environment objects: " + ", ".join(sorted(missing)))
    cells = {c.attrib["alias"]: c.attrib["content"]
             for c in objects["Parameters"].iter("Cell") if c.get("alias")}
    missing = set(plan["environment_aliases"]) - cells.keys()
    if missing:
        raise ValueError("Missing environment parameters: " + ", ".join(sorted(missing)))
    if not (ROOT / plan["reference"]).is_file():
        raise ValueError("Missing reference sketch")
    return {
        "status": "offline_inputs_checked_geometry_pending",
        "document": plan["document"],
        "document_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "environment": {k: {"content": cells[k], "source": v}
                        for k, v in plan["environment_aliases"].items()},
        "checked_object_names": plan["environment_objects"],
        "unresolved": [u["key"] for u in plan["unresolved"] if u["value"] is None],
        "specified_parameters": plan["specified_parameters"],
        "provisional_parameters": plan["provisional_parameters"],
        "checks_not_run": ["FreeCAD recompute", "solid geometry", "collisions", "slicing"]
    }


def prepare_in_freecad(plan):
    import FreeCAD as App

    doc = App.listDocuments().get(plan["document_name"])
    if doc is None:
        raise RuntimeError("Open the existing LaptopDeskMount.FCStd document first")
    if Path(doc.FileName).resolve() != (ROOT / plan["document"]).resolve():
        raise RuntimeError("The open document has a different file path")
    for name in plan["environment_objects"]:
        if doc.getObject(name) is None:
            raise RuntimeError("Missing environment object: " + name)
    for alias in plan["environment_aliases"]:
        getattr(doc.Parameters, alias)
    if doc.getObject("HeadphoneHook") is not None:
        print("HeadphoneHook already exists; existing preparation and geometry preserved.")
        return
    names = ("HookParameters", "HeadphoneHookUpper", "HeadphoneHookLower")
    if any(doc.getObject(name) for name in names):
        raise RuntimeError("Hook object name already in use; inspect before proceeding")

    doc.openTransaction("Подготовка крючка для наушников")
    try:
        group = doc.addObject("App::DocumentObjectGroup", "HeadphoneHook")
        group.Label = "05 Крючок для наушников — подготовка"
        group.addProperty("App::PropertyString", "PreparationStatus", "Design")
        group.PreparationStatus = "Параметры подготовлены; геометрия ещё не построена"
        group.addProperty("App::PropertyString", "PlanFile", "Design")
        group.PlanFile = str(PLAN_PATH)
        group.addProperty("App::PropertyLinkList", "EnvironmentReferences", "Design")
        group.EnvironmentReferences = [doc.getObject(n) for n in plan["environment_objects"]
                                       if n not in ("HolderLeft", "HolderRight")]
        sheet = doc.addObject("Spreadsheet::Sheet", "HookParameters")
        sheet.Label = "Крючок — связи с окружением и допущения"
        group.addObject(sheet)
        for col, label, width in (("A", "Параметр", 260), ("B", "Значение", 180),
                                  ("C", "Источник / состояние", 620)):
            sheet.set(col + "1", label)
            sheet.setColumnWidth(col, width)
        sheet.setStyle("A1:C1", "bold", "add")
        row = 2
        for kind in PARAMETER_KINDS:
            for param in plan[kind]:
                sheet.set("A%d" % row, param["label"])
                sheet.set("B%d" % row, param.get("expression", param.get("value")))
                sheet.setAlias("B%d" % row, param["alias"])
                sheet.set("C%d" % row, param["note"])
                if kind == "provisional_parameters" or param["alias"].startswith("Corner"):
                    sheet.setBackground("A%d:C%d" % (row, row), (1.0, .92, .73))
                row += 1
        for item in plan["unresolved"]:
            sheet.set("A%d" % row, item["label"])
            sheet.set("B%d" % row, "Уточнить" if item["value"] is None else str(item["value"]))
            sheet.set("C%d" % row, "Не использовать как числовой посадочный размер")
            sheet.setBackground("A%d:C%d" % (row, row), (1.0, .92, .73))
            row += 1
        for name, label in (("HeadphoneHookUpper", "Верхний крюк с кольцом — заготовка"),
                            ("HeadphoneHookLower", "Нижний захват — заготовка")):
            body = doc.addObject("PartDesign::Body", name)
            body.Label = label
            group.addObject(body)
        doc.recompute()
        for param in [p for kind in PARAMETER_KINDS for p in plan[kind]]:
            getattr(sheet, param["alias"])
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise
    print("Preparation added to the existing document. No geometry built or file saved.")


if __name__ == "__main__":
    plan = read_plan()
    if "--check" in sys.argv:
        report = inspect_saved_document(plan)
        (ROOT / "headphone_hook_preflight.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        prepare_in_freecad(plan)

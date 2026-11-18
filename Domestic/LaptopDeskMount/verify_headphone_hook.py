"""Validate installation paths, tool access, and native/print exports in FreeCAD."""
from pathlib import Path
import json
import FreeCAD as App
import Part
import MeshPart

ROOT = Path(__file__).resolve().parent
D = App.getDocument("LaptopDeskMount")
H = D.HookParameters
def q(alias):
    return getattr(H, alias).Value
upper, lower = D.HeadphoneHookUpper, D.HeadphoneHookLower
report = json.loads((ROOT / "headphone_hook_validation.json").read_text())
obstacle_names = ["TabletopFull", "BeamFullNear", "LegNearRight", "LongRailRight",
                  "HolderLeft", "HolderRight", "LaptopBase", "SpacerLeft", "SpacerRight"]
obstacles = [(name, D.getObject(name).Shape) for name in obstacle_names]

def collision(a, b):
    # Cheap broad-phase exclusion avoids most expensive OCCT intersections.
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    return a.common(b).Volume

def check_path(source, translations, extra=()):
    maximum = 0
    for delta in translations:
        shape = source.copy()
        shape.translate(App.Vector(*delta))
        for name, obstacle in obstacles + list(extra):
            volume = collision(shape, obstacle)
            maximum = max(maximum, volume)
            if volume > 1e-5:
                raise RuntimeError("Installation collision at %s / %s: %.5f mm3" % (delta, name, volume))
    return {"samples": len(translations), "max_collision_mm3": maximum}

upper_path = [(0, -96 + 2 * i, 0) for i in range(49)]
lower_raise = [(-28, 0, -80 + 2 * i) for i in range(41)]
lower_slide = [(-28 + i, 0, 0) for i in range(29)]
report["installation_paths"] = {
    "upper_slide_in_from_laptop_side": check_path(upper.Shape, upper_path),
    "lower_raise_28mm_inboard": check_path(lower.Shape, lower_raise, [("upper", upper.Shape)]),
    "lower_slide_along_crossbar_into_rear_channel": check_path(lower.Shape, lower_slide, [("upper", upper.Shape)]),
    "method": "Upper slides +Y into tabletop gap. Lower rises 28mm inboard, then slides +X into rear channel."
}
x, y = q("ClampX") + q("ClipWidth") / 2, q("BoltY")
tool = Part.makeCylinder(2, 65, App.Vector(x, y, q("HeadSeatZ") - 65))
for name, shape in obstacles + [("upper", upper.Shape), ("lower", lower.Shape)]:
    if collision(tool, shape) > 1e-5:
        raise RuntimeError("Hidden screw tool access blocked: " + name)
report["tool_access"] = {"clear": True, "test": "4mm-diameter axial tool envelope for 65mm below head seat"}
jack = Part.makeCylinder(q("CableEyeWidth") / 2, 100,
                         App.Vector(q("CornerX") - 50, q("EyeCenterY"), q("EyeCenterZ")), App.Vector(1, 0, 0))
for name, shape in obstacles + [("upper", upper.Shape), ("lower", lower.Shape)]:
    if collision(jack, shape) > 1e-5:
        raise RuntimeError("Clear jack passage blocked: " + name)
report["cable_passage"] = {"clear": True, "diameter_mm": q("CableEyeWidth"), "tested_length_mm": 100, "axis": "X"}

exports = ROOT / "exports"
report["exports"] = {}
for body, name in ((upper, "headphone_hook_upper"), (lower, "headphone_hook_lower")):
    Part.export([body], str(exports / (name + ".step")))
    shape = body.Shape.copy()
    placement = App.Placement(App.Vector(), App.Rotation(App.Vector(0, 1, 0), -90))
    shape.Placement = placement.multiply(shape.Placement)
    bb = shape.BoundBox
    shape.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.06, AngularDeflection=.15, Relative=False)
    if not mesh.isSolid():
        raise RuntimeError("Non-closed hook STL: " + name)
    mesh.write(str(exports / (name + ".stl")))
    report["exports"][name] = {"stl_closed": mesh.isSolid(), "facets": mesh.CountFacets,
                              "print_bounds_mm": [mesh.BoundBox.XLength, mesh.BoundBox.YLength, mesh.BoundBox.ZLength],
                              "base_plane": "Assembly X-min on print Z=0", "sliced": False}
report["status"] = "geometry_installation_paths_and_exports_checked"
report["physical_fit_tested"] = False
report["sliced"] = False
(ROOT / "headphone_hook_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k:report[k] for k in ("installation_paths", "tool_access", "cable_passage", "exports")}, ensure_ascii=False, indent=2))

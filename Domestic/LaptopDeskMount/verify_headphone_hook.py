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
obstacle_names = ["TabletopFull", "BeamFullNear", "LegNearRight",
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
assert not any(D.getObject(n) for n in ("HookEyeOuter","HookEyeBore","HookEyeRim"))
assert D.HookCableSketch.FullyConstrained
guide=Part.makeCylinder(q("CableGap")/2,q("CableTop")-q("ShelfBottom")+4,
                        App.Vector((q("CableLeftCenter")+q("CableRightCenter"))/2,q("CableCenterY"),q("ShelfBottom")-2))
passage_collision=collision(guide,upper.Shape)
if passage_collision>1e-5:raise RuntimeError("Oval cable passage is narrowed")
assert abs(q("CableTop")-q("TableTopZ"))<1e-6
assert max(D.HookInsertPocket.Radius.Value*2,D.HookInsertLeadIn.Radius1.Value*2,D.HookInsertLeadIn.Radius2.Value*2)<=5.7+1e-6
if D.getObject('HookSecondInsertPocket'):
    a,b=D.HookInsertPocket,D.HookSecondInsertPocket
    assert abs(a.Placement.Base.x+b.Placement.Base.x-2*q('StopCenterX'))<1e-6
    assert a.Radius==b.Radius and a.Height==b.Height
    assert max(D.HookSecondInsertLeadIn.Radius1.Value*2,D.HookSecondInsertLeadIn.Radius2.Value*2)<=5.7+1e-6
    for seat in (a,b):
        bore=Part.makeCylinder(q('InsertPocketDiameter')/2-.01, q('InsertPocketDepth')-.1,
            App.Vector(seat.Placement.Base.x,seat.Placement.Base.y,q('UpperBossBottom')+.05))
        assert collision(bore,upper.Shape)<1e-5
    report['symmetric_insert_seats']={'count':2,'center_x_mm':q('StopCenterX'),
        'axes_x_mm':[a.Placement.Base.x,b.Placement.Base.x],'bore_diameter_mm':a.Radius.Value*2,
        'second_seat_unused':True}
report["cable_ring"]={"present":True,"shape":"vertical_oval_loop","free_diameter_mm":q("CableGap"),"wall_mm":q("CableWall"),
                      "top_flush_with_tabletop":True,"top_z_mm":q("CableTop"),"passage_intersection_mm3":passage_collision}
thirds=[q("ShelfTop")-q("ChannelRoof"),q("ChannelRoof")-q("RearLipTop"),q("RearLipTop")-q("ShelfBottom")]
assert max(thirds)-min(thirds)<1e-6
report["equal_rear_joint"]={"segments_mm":thirds,"tongue_thickness_mm":q("TongueTop")-q("TongueBottom"),"inner_radius_mm":q("JointInsideRadius")}
if D.getObject("Sketch001"):
    lengths=[g.length() for g in D.Sketch001.Geometry]
    assert max(lengths)-min(lengths)<1e-6
    report["user_reference_sketch"]={"name":"Sketch001","lengths_mm":lengths,"attachments_preserved":True}

exports = ROOT / "exports"
report["exports"] = {}
for body, name in ((upper, "headphone_hook_upper"), (lower, "headphone_hook_lower")):
    Part.export([body], str(exports / (name + ".step")))
    shape = body.Shape.copy()
    is_upper = body == upper
    placement = App.Placement(App.Vector(), App.Rotation() if is_upper else App.Rotation(App.Vector(0, 1, 0), -90))
    shape.Placement = placement.multiply(shape.Placement)
    bb = shape.BoundBox
    shape.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.06, AngularDeflection=.15, Relative=False)
    # OCCT's coarse curved-surface bounds can differ from the tessellation bounds.
    # Put the actual STL triangles on Z=0, independently of the BRep bound cache.
    bb = mesh.BoundBox
    mesh.transform(App.Placement(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin), App.Rotation()).toMatrix())
    if not mesh.isSolid():
        raise RuntimeError("Non-closed hook STL: " + name)
    mesh.write(str(exports / (name + ".stl")))
    report["exports"][name] = {"stl_closed": mesh.isSolid(), "facets": mesh.CountFacets,
                              "print_bounds_mm": [mesh.BoundBox.XLength, mesh.BoundBox.YLength, mesh.BoundBox.ZLength],
                              "base_plane": "Assembly Z-min on print Z=0" if is_upper else "Assembly X-min on print Z=0", "sliced": False}
    report["bodies"][body.Name]["bounds_mm"] = ([mesh.BoundBox.XLength,mesh.BoundBox.YLength,mesh.BoundBox.ZLength] if is_upper
                                               else [mesh.BoundBox.ZLength,mesh.BoundBox.YLength,mesh.BoundBox.XLength])
    report["bodies"][body.Name]["bounds_source"] = "tessellation dimensions mapped back to assembly axes"
report["status"] = "geometry_installation_paths_and_exports_checked"
report["physical_fit_tested"] = False
report["sliced"] = False
(ROOT / "headphone_hook_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k:report[k] for k in ("installation_paths", "tool_access", "cable_ring", "exports")}, ensure_ascii=False, indent=2))

"""Build the corner stop and separate screw clamp in the existing FreeCAD document."""
from pathlib import Path
import json
import math
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
import MeshPart

ROOT = Path(__file__).resolve().parent
doc = App.getDocument("LaptopDeskMount")
H = doc.HookParameters
upper, lower = doc.HeadphoneHookUpper, doc.HeadphoneHookLower
if upper.Tip or lower.Tip:
    raise RuntimeError("Hook geometry already exists; edit its features instead of rebuilding")

original_holders = {n: doc.getObject(n).Shape.copy() for n in ("HolderLeft", "HolderRight")}
parameters = [
    ("ClipWidth", "24 mm", "Ширина нижнего обхвата", "Выбрано для компактного узла"),
    ("CornerX", "=Parameters.TableAcross / 2", "Правый угол X", "Справа при взгляде со стороны ноутбука"),
    ("ClampX", "=CornerX - LowerOffset - FitClearance - ClipWidth", "Начало нижнего обхвата X", "За внутренней гранью ноги, с зазором"),
    ("FrontY", "=-FitClearance", "Передняя грань обхвата Y", "Снаружи перекладины"),
    ("BossDepth", "14 mm", "Глубина передней стойки", "Материал вокруг вставки M4"),
    ("BossY", "=FrontY - BossDepth", "Передняя стойка Y", "Снаружи стола"),
    ("BoltY", "=BossY + BossDepth / 2", "Ось болта Y", "Доступ шестигранником снизу"),
    ("VerticalClearance", "0.2 mm", "Вертикальный зазор на сторону", "Отдельно от бокового зазора обхвата"),
    ("ShelfBottom", "=VerticalClearance", "Низ верхней полки", "Над верхом перекладины"),
    ("ShelfTop", "=TopGap - FitClearance", "Верх верхней полки", "В зазоре под столешницей"),
    ("ShelfThickness", "=ShelfTop - ShelfBottom", "Толщина верхней полки", "Максимально использован зазор под столешницей"),
    ("JointThird", "=ShelfThickness / 3", "Три равных участка заднего узла", "По эскизу пользователя"),
    ("JointInsideRadius", "0 mm", "Задние углы без скругления", "Отменено по уточнению пользователя"),
    ("BeamBack", "=ProfileWidth + FitClearance", "Задняя грань обхвата Y", "Боковой зазор от перекладины"),
    ("RearStemEnd", "=BeamBack + Wall", "Задняя стойка: торец Y", "Стойка нижнего обхвата"),
    ("TongueEnd", "=RearStemEnd + Wall", "Задний зацеп: торец Y", "Заходит в канал верхней детали"),
    ("UpperBackInner", "=TongueEnd + JointClearance", "Задняя стенка канала Y", "Запас для зацепа"),
    ("UpperBackEnd", "=UpperBackInner + Wall", "Задний габарит верхней части", "Силовая стенка канала"),
    ("ChannelRoof", "=ShelfTop - JointThird", "Низ верхнего перекрытия канала", "Толщина равна трети высоты"),
    ("TongueTop", "=ChannelRoof - 2 * JointClearance", "Верх зацепа Z", "Зазор допускает подтяжку обхвата болтом"),
    ("TongueBottom", "=RearLipTop + JointClearance", "Низ зацепа Z", "Зазор снизу 0.3 мм"),
    ("RearLipTop", "=ShelfBottom + JointThird", "Верх заднего удерживающего борта", "Толщина равна трети высоты"),
    ("RearLipBottom", "=ShelfBottom", "Низ заднего удерживающего борта", "Весь верхний захват находится над металлом"),
    ("RearLipFront", "=RearStemEnd + JointClearance", "Передний торец заднего борта", "Зазор к стойке нижней части"),
    ("BottomInside", "=-ProfileHeight - VerticalClearance", "Внутреннее дно обхвата", "Под перекладиной"),
    ("BottomZ", "=BottomInside - Wall", "Низ нижнего обхвата", "Толщина дна 6 мм"),
    ("UpperBossBottom", "=ShelfBottom", "Плоский низ основной детали", "Вставка расположена в основной полке без нижнего выступа"),
    ("FrontClosingGap", "1.2 mm", "Зазор стягивания передних стоек", "Больше суммарного вертикального зазора 0.4 мм"),
    ("LowerBossTop", "=UpperBossBottom - FrontClosingGap", "Верх нижней передней стойки", "Стягивание скрытым болтом"),
    ("InsertLength", "6 mm", "Выбранная длина вставки M4", "У пользователя есть вставки разной длины, выбрана 6 мм"),
    ("InsertPocketDiameter", "5.6 mm", "Отверстие для вплавления Ø6", "Исходная посадка, проверить на выбранной вставке; это не наружный диаметр вставки"),
    ("InsertPocketDepth", "6.4 mm", "Глубина отверстия вставки", "Вставка 6 мм + запас 0.4 мм"),
    ("BoltLength", "15 mm", "Болт M4 под головкой", "Самый длинный доступный болт M4×15"),
    ("BoltEngagement", "=InsertLength - 0.2 mm", "Номинальное зацепление болта", "Вставка 6 мм, запас 0.2 мм до её заднего торца"),
    ("HeadPocketDepth", "=UpperBossBottom - BottomZ - BoltLength + BoltEngagement", "Глубина канала головки", "Углублён, чтобы сохранить M4×20 при плоском низе основной детали"),
    ("HeadSeatZ", "=BottomZ + HeadPocketDepth", "Опорная плоскость головки", "Головка утоплена снизу"),
    ("TableTopZ", "=TopGap + DesktopThickness", "Верх столешницы Z", "Размеры из существующего окружения"),
    ("StopWidth", "=CornerX - ClampX", "Ширина округлого ограничителя", "Левый и правый края совпадают с краями основания"),
    ("StopCenterX", "=CornerX - StopWidth / 2", "Центр ограничителя X", "Правый край ограничителя совпадает с правым торцом столешницы"),
    ("StopThickness", "=BossDepth", "Толщина ограничителя", "Передняя грань со стороны ноутбука совпадает с передней гранью основания"),
    ("StopRise", "60 mm", "Выступ над столешницей", "Задано пользователем: 60 мм; оголовье лежит на столе"),
    ("StopTop", "=TableTopZ + StopRise", "Верх ограничителя", "Плоский верх смягчённого прямоугольника"),
    ("StopCornerRadius", "10 mm", "Скругление верхних углов", "Прямоугольный силуэт с двумя верхними углами R10"),
]
last = max(i for i in range(1, 200) if H.getContents("A%d" % i))
for alias, value, label, note in parameters:
    cell = H.getCellFromAlias(alias)
    if cell:
        row = int(cell[1:])
    else:
        last += 1
        row = last
    H.set("A%d" % row, label)
    H.set("B%d" % row, "=" + value if value.startswith("-") else value)
    H.setAlias("B%d" % row, alias)
    H.set("C%d" % row, note)
doc.recompute()
p = ROOT / "refine_headphone_details.py"
details = {"__file__":str(p),"__name__":"hook_details"}
exec(compile(p.read_text(),str(p),"exec"),details)
details["set_dimensions"](doc)

def q(alias):
    return getattr(H, alias).Value

def expr(value):
    return "HookParameters." + value

def check(obj):
    doc.recompute()
    if obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids) != 1:
        raise RuntimeError("Invalid hook feature: %s %s" % (obj.Name, obj.getStatusString()))
    return obj

def primitive(body, kind, name, label, dimensions, position, rotation=None):
    previous = body.Tip
    obj = body.newObject("PartDesign::" + kind, name)
    obj.Label = label
    if rotation:
        obj.Placement = App.Placement(App.Vector(), rotation)
    for prop, value in dimensions.items():
        obj.setExpression(prop, value)
    for axis, value in zip("xyz", position):
        obj.setExpression("Placement.Base." + axis, value)
    obj.Refine = True
    check(obj)
    if previous:
        previous.ViewObject.Visibility = False
    return obj

def box(body, name, label, size, position):
    return primitive(body, "AdditiveBox", name, label,
                     dict(zip(("Length", "Width", "Height"), size)), position)

def cylinder(body, kind, name, label, radius, length, position, rotation=None):
    return primitive(body, kind + "Cylinder", name, label,
                     {"Radius": radius, "Height": length}, position, rotation)

def fillet(body, name, label, edges, radius):
    base = body.Tip
    obj = body.newObject("PartDesign::Fillet", name)
    obj.Label = label
    obj.Base = (base, edges)
    obj.Radius = radius
    obj.Refine = True
    check(obj)
    base.ViewObject.Visibility = False
    return obj

# A full-width rectangular shelf occupies the existing gap above the crossbar.
profile = upper.newObject("Sketcher::SketchObject", "HookShelfSketch")
profile.Label = "Прямоугольная полка на всю ширину основной детали"
profile.setExpression("Placement.Base.z", expr("ShelfBottom"))
xy = [(expr("ClampX"), expr("BossY")),
      (expr("CornerX"), expr("BossY")),
      (expr("CornerX"), expr("UpperBackEnd")),
      (expr("ClampX"), expr("UpperBackEnd"))]
vertices = [App.Vector(upper.evalExpression(x).Value, upper.evalExpression(y).Value, 0) for x, y in xy]
for i, vertex in enumerate(vertices):
    profile.addGeometry(Part.LineSegment(vertex, vertices[(i + 1) % len(vertices)]), False)
for i, vertex in enumerate(vertices):
    profile.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % len(vertices), 1))
    for kind, value, expression in (("DistanceX", vertex.x, xy[i][0]), ("DistanceY", vertex.y, xy[i][1])):
        idx = profile.addConstraint(Sketcher.Constraint(kind, i, 1, value))
        profile.setExpression("Constraints[%d]" % idx, expression)
shelf = upper.newObject("PartDesign::Pad", "HookShelf")
shelf.Label = "Скрытая верхняя полка в зазоре стола"
shelf.Profile = profile
shelf.setExpression("Length", expr("ShelfThickness"))
shelf.Refine = True
check(shelf)
profile.ViewObject.Visibility = False
primitive(upper, "SubtractiveBox", "HookRearChannel", "Боковой вход заднего зацепа — над перекладиной",
          {"Length": expr("StopWidth") + "+2 mm", "Width": expr("UpperBackInner") + "-" + expr("BeamBack") + "+" + expr("JointClearance"),
           "Height": expr("ChannelRoof") + "-" + expr("ShelfBottom") + "+1 mm"},
          (expr("ClampX") + "-1 mm", expr("BeamBack") + "-" + expr("JointClearance"), expr("ShelfBottom") + "-1 mm"))
box(upper, "HookRearLip", "Удерживающий борт заднего паза",
    (expr("StopWidth"), expr("UpperBackEnd") + "-" + expr("RearLipFront"), expr("RearLipTop") + "-" + expr("RearLipBottom")),
    (expr("ClampX"), expr("RearLipFront"), expr("RearLipBottom")))
outline = ["Edge%d" % i for i,e in enumerate(upper.Tip.Shape.Edges,1)
           if abs(e.BoundBox.ZLength-q("ShelfThickness"))<1e-5
           and e.BoundBox.XLength<1e-6 and e.BoundBox.YLength<1e-6]
fillet(upper,"HookShelfRounds","Скругления полки и заднего бортика R2",outline,2)
box(upper, "HookStopStem", "Ограничитель у правого угла",
    (expr("StopWidth"), expr("StopThickness"), expr("StopTop") + "-" + expr("ShelfBottom")),
    (expr("StopCenterX") + "-" + expr("StopWidth") + "/2", expr("FrontY") + "-" + expr("StopThickness"), expr("ShelfBottom")))
corner_edges = ["Edge%d" % i for i,e in enumerate(upper.Tip.Shape.Edges,1)
                if abs(e.BoundBox.ZMin-q("StopTop"))<1e-5 and e.BoundBox.ZLength<1e-6
                and e.BoundBox.XLength<1e-6 and abs(e.BoundBox.YLength-q("StopThickness"))<1e-5]
corners = fillet(upper,"HookStopCorners","Верхние углы прямоугольного ограничителя R10",corner_edges,q("StopCornerRadius"))
corners.setExpression("Radius",expr("StopCornerRadius"))
rim_edges = []
for i, e in enumerate(upper.Tip.Shape.Edges, 1):
    bb=e.BoundBox
    if bb.YLength<1e-6 and bb.ZMin>=q("StopTop")-q("StopCornerRadius")-1e-5:
        if isinstance(e.Curve,Part.Circle) or (bb.ZLength<1e-6 and abs(bb.ZMax-q("StopTop"))<1e-5):
            rim_edges.append("Edge%d" % i)
fillet(upper, "HookStopRim", "Мягкие кромки прямоугольного верха R2.5", rim_edges, 2.5)
details["add_oval_loop"](doc)
cylinder(upper, "Subtractive", "HookInsertPocket", "Посадка термовставки M4 Ø5.69 × 6",
         expr("InsertPocketDiameter") + "/2", expr("InsertPocketDepth") + "+1 mm",
         (expr("ClampX") + "+" + expr("ClipWidth") + "/2", expr("BoltY"), expr("UpperBossBottom") + "-1 mm"))
cylinder(upper, "Subtractive", "HookScrewRelief", "Запас под конец болта над вставкой",
         expr("BoltHoleDiameter") + "/2", expr("InsertPocketDepth") + "+2 mm",
         (expr("ClampX") + "+" + expr("ClipWidth") + "/2", expr("BoltY"), expr("UpperBossBottom")))
primitive(upper, "SubtractiveCone", "HookInsertLeadIn", "Входная фаска термовставки",
          {"Radius1": expr("InsertOuterDiameter") + "/2", "Radius2": expr("InsertPocketDiameter") + "/2", "Height": "0.4 mm"},
          (expr("ClampX") + "+" + expr("ClipWidth") + "/2", expr("BoltY"), expr("UpperBossBottom")))

box(lower, "HookClampFloor", "Нижняя полка обхвата",
    (expr("ClipWidth"), expr("RearStemEnd") + "-" + expr("BossY"), expr("Wall")),
    (expr("ClampX"), expr("BossY"), expr("BottomZ")))
box(lower, "HookClampFront", "Передняя стойка со скрытым болтом",
    (expr("ClipWidth"), expr("BossDepth"), expr("LowerBossTop") + "-" + expr("BottomZ")),
    (expr("ClampX"), expr("BossY"), expr("BottomZ")))
box(lower, "HookClampRear", "Задняя стойка обхвата",
    (expr("ClipWidth"), expr("Wall"), expr("TongueTop") + "-" + expr("BottomZ")),
    (expr("ClampX"), expr("BeamBack"), expr("BottomZ")))
box(lower, "HookClampTongue", "Задний зацеп входит в паз верхней части",
    (expr("ClipWidth"), expr("TongueEnd") + "-" + expr("BeamBack"), expr("TongueTop") + "-" + expr("TongueBottom")),
    (expr("ClampX"), expr("BeamBack"), expr("TongueBottom")))
# Round the exterior side outline, leaving the planar crossbar bearing surfaces intact.
outer_edges = []
for i, e in enumerate(lower.Tip.Shape.Edges, 1):
    bb = e.BoundBox
    if bb.XLength > q("ClipWidth") - 1e-5 and bb.YLength < 1e-6 and bb.ZLength < 1e-6:
        if abs(bb.ZMin - q("BottomZ")) < 1e-5 or abs(bb.YMin - q("BossY")) < 1e-5:
            outer_edges.append("Edge%d" % i)
fillet(lower, "HookClampRounds", "Наружные скругления нижнего обхвата R2", outer_edges, 2)
cylinder(lower, "Subtractive", "HookClampScrewHole", "Сквозной проход болта M4 Ø4.5",
         expr("BoltHoleDiameter") + "/2", expr("LowerBossTop") + "-" + expr("BottomZ") + "+2 mm",
         (expr("ClampX") + "+" + expr("ClipWidth") + "/2", expr("BoltY"), expr("BottomZ") + "-1 mm"))
cylinder(lower, "Subtractive", "HookClampHeadPocket", "Скрытая цилиндрическая головка Ø7.5 × 4.5",
         expr("HeadPocketDiameter") + "/2", expr("HeadPocketDepth") + "+1 mm",
         (expr("ClampX") + "+" + expr("ClipWidth") + "/2", expr("BoltY"), expr("BottomZ") + "-1 mm"))
p=ROOT/"finish_headphone_walls.py"
walls={"__file__":str(p),"__name__":"hook_walls"}
exec(compile(p.read_text(),str(p),"exec"),walls)
walls["finish_lower"](doc)
walls["finish_insert_pair"](doc)

for body, color, label in ((upper, (.92, .48, .16), "Верхний ограничитель с овальной петлёй — PETG"),
                            (lower, (.25, .62, .76), "Нижний захват — PETG, M4×15")):
    body.Label = label
    for obj in body.Group:
        obj.ViewObject.Visibility = obj == body.Tip
    body.ViewObject.Visibility = True
    body.ViewObject.ShapeColor = color
    body.Tip.ViewObject.ShapeColor = color
    body.Tip.ViewObject.DiffuseColor = [color]
    body.Tip.ViewObject.LineColor = (.18, .18, .20)
doc.HeadphoneHook.Label = "05 Наушники — правый угловой ограничитель"
doc.HeadphoneHook.PreparationStatus = "Построены две печатные детали; оголовье лежит на столешнице"
doc.recompute()

# Reversible reference hardware; deliberately separate from printed bodies.
hardware = doc.addObject("App::DocumentObjectGroup", "HookHardware")
hardware.Label = "Крепёж крючка — M4×15 и термовставка Ø5.69 × 6"
doc.HeadphoneHook.addObject(hardware)
x, y = q("ClampX") + q("ClipWidth") / 2, q("BoltY")
insert = doc.addObject("PartDesign::Feature", "HookInsertReference")
insert.Label = "Термовставка M4, Ø5.69 × 6 — условная геометрия"
insert.Shape = Part.makeCylinder(q("InsertOuterDiameter")/2, q("InsertLength"), App.Vector(x, y, q("UpperBossBottom"))).cut(
    Part.makeCylinder(2, q("InsertLength"), App.Vector(x, y, q("UpperBossBottom"))))
hardware.addObject(insert)
insert.ViewObject.ShapeColor = (.78, .61, .22)
bolt = doc.addObject("PartDesign::Feature", "HookBoltReference")
bolt.Label = "Болт M4×15, цилиндрическая головка — условная геометрия"
bolt.Shape = Part.makeCylinder(q("HeadDiameter") / 2, q("HeadHeight"), App.Vector(x, y, q("HeadSeatZ") - q("HeadHeight"))).fuse(
    Part.makeCylinder(2, q("BoltLength"), App.Vector(x, y, q("HeadSeatZ"))))
hardware.addObject(bolt)
bolt.ViewObject.ShapeColor = (.24, .26, .29)
doc.recompute()

report = {"status": "native_geometry_built", "corner": "right_from_laptop", "headband_supported_by": "tabletop",
          "bodies": {}, "environment_collisions_mm3": {}, "holders_unchanged": {}, "assumptions": [
              "Insert M4 measured OD5.69 length6; bore5.6, entry max5.7",
              "M4x15 head OD7 height4 based on user's diameter and provisional height"]}
for body in (upper, lower):
    shape = body.Shape
    report["bodies"][body.Name] = {"valid": shape.isValid(), "solids": len(shape.Solids), "volume_mm3": shape.Volume,
                                   "bounds_mm": [shape.BoundBox.XLength, shape.BoundBox.YLength, shape.BoundBox.ZLength]}
    for name in ("TabletopFull", "BeamFullNear", "LegNearRight", "HolderLeft", "HolderRight", "LaptopBase"):
        volume = shape.common(doc.getObject(name).Shape).Volume
        report["environment_collisions_mm3"][body.Name + ":" + name] = volume
        if volume > 1e-5:
            raise RuntimeError("Collision %s / %s: %.5f mm3" % (body.Name, name, volume))
report["parts_intersection_mm3"] = upper.Shape.common(lower.Shape).Volume
if report["parts_intersection_mm3"] > 1e-5:
    raise RuntimeError("Printed hook parts intersect")
for name, before in original_holders.items():
    after = doc.getObject(name).Shape
    delta = before.cut(after).Volume + after.cut(before).Volume
    report["holders_unchanged"][name] = delta < 1e-6
    if delta > 1e-6:
        raise RuntimeError("Existing laptop holder changed: " + name)
report["bolt"] = {"suggested": "M4x15 socket cap", "insert": "M4 OD5.69 length6",
                  "nominal_engagement_mm": q("HeadSeatZ") + q("BoltLength") - q("UpperBossBottom"),
                  "front_closing_gap_mm": q("FrontClosingGap"),
                  "total_vertical_clearance_mm": 2 * q("VerticalClearance")}
(ROOT / "headphone_hook_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
doc.save()
print(json.dumps(report, ensure_ascii=False, indent=2))

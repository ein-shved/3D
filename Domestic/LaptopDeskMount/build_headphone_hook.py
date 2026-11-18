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
    ("ArmDepth", "16 mm", "Глубина скрытого плеча", "Соединяет угол и смещённый обхват"),
    ("BeamBack", "=ProfileWidth + FitClearance", "Задняя грань обхвата Y", "Боковой зазор от перекладины"),
    ("RearStemEnd", "=BeamBack + Wall", "Задняя стойка: торец Y", "Стойка нижнего обхвата"),
    ("TongueEnd", "=RearStemEnd + Wall", "Задний зацеп: торец Y", "Заходит в канал верхней детали"),
    ("UpperBackInner", "=TongueEnd + JointClearance", "Задняя стенка канала Y", "Запас для зацепа"),
    ("UpperBackEnd", "=UpperBackInner + Wall", "Задний габарит верхней части", "Силовая стенка канала"),
    ("ChannelRoof", "=ShelfTop - 2 mm", "Низ верхнего перекрытия канала", "Канал целиком в зазоре над перекладиной"),
    ("TongueTop", "=ChannelRoof - 2 * JointClearance", "Верх зацепа Z", "Зазор допускает подтяжку обхвата болтом"),
    ("TongueBottom", "=ShelfBottom + 2.5 mm + JointClearance", "Низ зацепа Z", "Толщина зацепа 4.51 мм при заданном зазоре стола"),
    ("RearLipTop", "=TongueBottom - JointClearance", "Верх заднего удерживающего борта", "Зацеп захвачен сверху и снизу"),
    ("RearLipBottom", "=ShelfBottom", "Низ заднего удерживающего борта", "Весь верхний захват находится над металлом"),
    ("RearLipFront", "=RearStemEnd + JointClearance", "Передний торец заднего борта", "Зазор к стойке нижней части"),
    ("BottomInside", "=-ProfileHeight - VerticalClearance", "Внутреннее дно обхвата", "Под перекладиной"),
    ("BottomZ", "=BottomInside - Wall", "Низ нижнего обхвата", "Толщина дна 6 мм"),
    ("UpperBossBottom", "-18 mm", "Низ стойки со вставкой", "Вставка устанавливается снизу до монтажа"),
    ("FrontClosingGap", "1.2 mm", "Зазор стягивания передних стоек", "Больше суммарного вертикального зазора 0.4 мм"),
    ("LowerBossTop", "=UpperBossBottom - FrontClosingGap", "Верх нижней передней стойки", "Стягивание скрытым болтом"),
    ("InsertLength", "6 mm", "Выбранная длина вставки M4", "У пользователя есть вставки разной длины, выбрана 6 мм"),
    ("InsertPocketDiameter", "5.6 mm", "Отверстие для вплавления Ø6", "Исходная посадка, проверить на выбранной вставке; это не наружный диаметр вставки"),
    ("InsertPocketDepth", "6.4 mm", "Глубина отверстия вставки", "Вставка 6 мм + запас 0.4 мм"),
    ("BoltLength", "20 mm", "Болт M4 под головкой", "Подобран по сборке, пользователь подберёт M4×20"),
    ("HeadSeatZ", "=BottomZ + HeadPocketDepth", "Опорная плоскость головки", "Головка утоплена снизу"),
    ("TableTopZ", "=TopGap + DesktopThickness", "Верх столешницы Z", "Размеры из существующего окружения"),
    ("StopWidth", "24 mm", "Ширина округлого ограничителя", "Небольшая булька у самого угла"),
    ("StopThickness", "8 mm", "Толщина ограничителя", "Снаружи торца столешницы"),
    ("StopRise", "25 mm", "Выступ над столешницей", "Задано пользователем: 25 мм; оголовье лежит на столе"),
    ("StopTop", "=TableTopZ + StopRise", "Верх ограничителя", "Плавный круглый верх"),
    ("StopCapZ", "=StopTop - StopWidth / 2", "Центр скругления ограничителя", "Полукруглый верх R12"),
    ("EyeWall", "4 mm", "Стенка кольца", "Проход сохраняется Ø14 мм"),
    ("EyeRadius", "=CableEyeWidth / 2 + EyeWall", "Наружный радиус кольца", "R11 при проходе Ø14"),
    ("EyeOverlap", "3 mm", "Перекрытие кольца и ограничителя", "Кольцо составляет единое тело с верхней деталью; проход отделён от стойки"),
    ("EyeCenterY", "=FrontY - StopThickness - EyeRadius + EyeOverlap", "Центр кольца Y", "Ось отверстия вдоль X, проход снаружи столешницы"),
    ("EyeCenterZ", "=StopCapZ", "Центр кольца Z", "Рядом с округлым верхом"),
    ("EyeThickness", "8 mm", "Толщина кольца вдоль X", "Замкнутое кольцо для джека"),
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

# Dimensioned L-shaped shelf occupies the existing gap above the crossbar.
profile = upper.newObject("Sketcher::SketchObject", "HookShelfSketch")
profile.Label = "Скрытое плечо от правого угла к смещённому обхвату"
profile.setExpression("Placement.Base.z", expr("ShelfBottom"))
xy = [(expr("ClampX"), expr("BossY")),
      (expr("CornerX"), expr("BossY")),
      (expr("CornerX"), expr("ArmDepth")),
      (expr("ClampX") + "+" + expr("ClipWidth"), expr("ArmDepth")),
      (expr("ClampX") + "+" + expr("ClipWidth"), expr("UpperBackEnd")),
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
outline = ["Edge%d" % i for i, e in enumerate(shelf.Shape.Edges, 1)
           if abs(e.BoundBox.ZLength - q("ShelfThickness")) < 1e-5 and e.BoundBox.XLength < 1e-6 and e.BoundBox.YLength < 1e-6]
fillet(upper, "HookShelfRounds", "Скругления скрытого плеча R2", outline, 2)
box(upper, "HookFrontBoss", "Передняя стойка под термовставку",
    (expr("ClipWidth"), expr("BossDepth"), expr("ShelfTop") + "-" + expr("UpperBossBottom")),
    (expr("ClampX"), expr("BossY"), expr("UpperBossBottom")))
primitive(upper, "SubtractiveBox", "HookRearChannel", "Боковой вход заднего зацепа — над перекладиной",
          {"Length": expr("ClipWidth") + "+2 mm", "Width": expr("UpperBackInner") + "-" + expr("BeamBack") + "+" + expr("JointClearance"),
           "Height": expr("ChannelRoof") + "-" + expr("ShelfBottom") + "+1 mm"},
          (expr("ClampX") + "-1 mm", expr("BeamBack") + "-" + expr("JointClearance"), expr("ShelfBottom") + "-1 mm"))
box(upper, "HookRearLip", "Удерживающий борт заднего паза",
    (expr("ClipWidth"), expr("UpperBackEnd") + "-" + expr("RearLipFront"), expr("RearLipTop") + "-" + expr("RearLipBottom")),
    (expr("ClampX"), expr("RearLipFront"), expr("RearLipBottom")))
box(upper, "HookStopStem", "Ограничитель у правого угла",
    (expr("StopWidth"), expr("StopThickness"), expr("StopCapZ") + "-" + expr("ShelfBottom")),
    (expr("CornerX") + "-" + expr("StopWidth") + "/2", expr("FrontY") + "-" + expr("StopThickness"), expr("ShelfBottom")))
cylinder(upper, "Additive", "HookStopCap", "Полукруглый верх ограничителя R12",
         expr("StopWidth") + "/2", expr("StopThickness"),
         (expr("CornerX"), expr("FrontY"), expr("StopCapZ")), App.Rotation(App.Vector(1, 0, 0), 90))
cap_edges = []
for i, e in enumerate(upper.Tip.Shape.Edges, 1):
    if isinstance(e.Curve, Part.Circle) and abs(e.Curve.Radius - q("StopWidth") / 2) < 1e-5 and e.BoundBox.ZMin >= q("StopCapZ") - 1e-5:
        cap_edges.append("Edge%d" % i)
fillet(upper, "HookStopRim", "Мягкие кромки округлого верха R1.5", cap_edges, 1.5)
cylinder(upper, "Additive", "HookEyeOuter", "Кольцо для провода — наружный контур",
         expr("EyeRadius"), expr("EyeThickness"),
         (expr("CornerX") + "-" + expr("EyeThickness") + "/2", expr("EyeCenterY"), expr("EyeCenterZ")),
         App.Rotation(App.Vector(0, 1, 0), 90))
cylinder(upper, "Subtractive", "HookEyeBore", "Свободный проход джека Ø14",
         expr("CableEyeWidth") + "/2", expr("EyeThickness") + "+2 mm",
         (expr("CornerX") + "-" + expr("EyeThickness") + "/2-1 mm", expr("EyeCenterY"), expr("EyeCenterZ")),
         App.Rotation(App.Vector(0, 1, 0), 90))
eye_edges = ["Edge%d" % i for i, e in enumerate(upper.Tip.Shape.Edges, 1)
             if isinstance(e.Curve, Part.Circle) and abs(e.Curve.Radius - q("CableEyeWidth") / 2) < 1e-5]
fillet(upper, "HookEyeRim", "Скругления прохода провода R0.8", eye_edges, .8)
cylinder(upper, "Subtractive", "HookInsertPocket", "Посадка термовставки M4 Ø6 × 6",
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

for body, color, label in ((upper, (.92, .48, .16), "Верхний ограничитель с кольцом — PETG"),
                            (lower, (.25, .62, .76), "Нижний захват — PETG, M4×20")):
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
hardware.Label = "Крепёж крючка — M4×20 и термовставка Ø6 × 6"
doc.HeadphoneHook.addObject(hardware)
x, y = q("ClampX") + q("ClipWidth") / 2, q("BoltY")
insert = doc.addObject("PartDesign::Feature", "HookInsertReference")
insert.Label = "Термовставка M4, Ø6 × 6 — условная геометрия"
insert.Shape = Part.makeCylinder(3, q("InsertLength"), App.Vector(x, y, q("UpperBossBottom"))).cut(
    Part.makeCylinder(2, q("InsertLength"), App.Vector(x, y, q("UpperBossBottom"))))
hardware.addObject(insert)
insert.ViewObject.ShapeColor = (.78, .61, .22)
bolt = doc.addObject("PartDesign::Feature", "HookBoltReference")
bolt.Label = "Болт M4×20, цилиндрическая головка — условная геометрия"
bolt.Shape = Part.makeCylinder(q("HeadDiameter") / 2, q("HeadHeight"), App.Vector(x, y, q("HeadSeatZ") - q("HeadHeight"))).fuse(
    Part.makeCylinder(2, q("BoltLength"), App.Vector(x, y, q("HeadSeatZ"))))
hardware.addObject(bolt)
bolt.ViewObject.ShapeColor = (.24, .26, .29)
doc.recompute()

report = {"status": "native_geometry_built", "corner": "right_from_laptop", "headband_supported_by": "tabletop",
          "bodies": {}, "environment_collisions_mm3": {}, "holders_unchanged": {}, "assumptions": [
              "Jack metal diameter 3.5 mm; clear ring bore 14 mm",
              "Insert M4 OD6 length6; initial heat-set bore5.6 requires validation for chosen insert",
              "M4x20 head OD7 height4 based on user's diameter and provisional height"]}
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
report["bolt"] = {"suggested": "M4x20 socket cap", "insert": "M4 OD6 length6",
                  "nominal_engagement_mm": q("HeadSeatZ") + q("BoltLength") - q("UpperBossBottom"),
                  "front_closing_gap_mm": q("FrontClosingGap"),
                  "total_vertical_clearance_mm": 2 * q("VerticalClearance")}
(ROOT / "headphone_hook_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
doc.save()
print(json.dumps(report, ensure_ascii=False, indent=2))

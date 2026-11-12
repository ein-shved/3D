"""Run in FreeCAD's Python console. Environment is built before the holders."""
from pathlib import Path
import math
import FreeCAD as App
import FreeCADGui as Gui
import Part

ROOT = Path(__file__).resolve().parent
DOC_NAME = "LaptopDeskMount"
if DOC_NAME in App.listDocuments():
    raise RuntimeError("LaptopDeskMount is already open; use a fresh document to rebuild.")
doc = App.newDocument(DOC_NAME)
doc.Label = "Ноутбук у стола — окружение и держатели"
P = doc.addObject("Spreadsheet::Sheet", "Parameters")
P.Label = "Параметры — замеры и допущения"
P.set("A1", "Параметр")
P.set("B1", "Значение")
P.set("C1", "Источник / пояснение")
P.setStyle("A1:C1", "bold", "add")
P.setColumnWidth("A", 235)
P.setColumnWidth("B", 110)
P.setColumnWidth("C", 620)
PARAMS = [
    ("BeamWidth", "60.21 mm", "Ширина профиля", "Фото 1000005536; нога и перекладина из одинакового профиля"),
    ("BeamHeight", "30.48 mm", "Высота профиля", "Фото 1000005533"),
    ("SpacerHeight", "10.51 mm", "Зазор под столешницей", "Фото 1000005532"),
    ("SpacerWidth", "66 mm", "Ширина верхней проставки", "Фото 1000005535: показание 66.00; ширина вдоль перекладины"),
    ("PlateThickness", "3.21 mm", "Толщина нижней пластины", "Фото 1000005534"),
    ("TabletopThickness", "25.73 mm", "Толщина столешницы", "Фото 1000005540, считывание по фото"),
    ("MountSpacing", "240 mm", "Расстояние между узлами", "Приблизительный замер пользователя; принято между центрами"),
    ("PlateWidth", "86 mm", "Ширина нижней пластины", "ОЦЕНКА по фото; вдоль перекладины, уточнить пробником"),
    ("BoltPitch", "36.51 mm", "Межосевое двух болтов", "ОЦЕНКА по фото 1000005547; продольные отверстия допускают поправку"),
    ("BoltDiameter", "6 mm", "Диаметр болтов", "ДОПУЩЕНИЕ M6; резьба скрыта, не измерена"),
    ("BoltLength", "45 mm", "Длина болтов под головкой", "УСЛОВНО, только для картинки; возможность штатных болтов не подтверждена"),
    ("HeadDiameter", "13.65 mm", "Диаметр головки", "Фото 1000005537"),
    ("HeadHeight", "1.7 mm", "Высота головки", "Фото 1000005539"),
    ("LaptopWidth", "332 mm", "Ширина ноутбука", "Приблизительно, со слов пользователя"),
    ("LaptopThickness", "14 mm", "Толщина основания", "Фото 1000005541; локальный замер"),
    ("LaptopDepth", "220 mm", "Глубина ноутбука", "УСЛОВНО, только для окружения"),
    ("LaptopAngle", "30 deg", "Наклон основания", "Задан пользователем, передний край у стола, петли выше и снаружи"),
    ("LaptopMass", "1.3 kg", "Масса ноутбука", "По документации пользователя; клавиатурой ноутбука не пользуются"),
    ("UpperGrip", "75 mm", "Верхний захват", "Предел по клавиатуре, подтверждён пользователем"),
    ("LowerGrip", "85 mm", "Нижний захват", "Выбран на 7 мм короче начала вентиляции"),
    ("VentStart", "92 mm", "Начало вентиляции", "От переднего края, со слов пользователя"),
    ("Felt", "4 mm", "Толщина войлока", "Принято пользователем, отдельно сверху и снизу; без учёта сжатия"),
    ("LaptopClearance", "0.6 mm", "Суммарный зазор в пазу", "Конструктивное допущение, кроме двух слоёв войлока"),
    ("BeamClearance", "0.4 mm", "Зазор у профиля", "Конструктивное допущение, на сторону"),
    ("SpacerClearance", "0.6 mm", "Запас ширины прорези", "Суммарный запас, проверить пробником"),
    ("ClampWall", "5 mm", "Стенка обхвата", "Конструктивное допущение, PETG"),
    ("ClampShelf", "4 mm", "Полки обхвата", "Добавляют 4 мм под головками болтов"),
    ("ClampWidth", "96 mm", "Ширина держателя", "Оставляет две боковые перемычки вокруг прорези 66.6 мм"),
    ("RailWall", "5 mm", "Полки ноутбука", "Конструктивное допущение"),
    ("FrontY", "-14 mm", "Передний край ноутбука Y", "Принятое положение у внешней стороны перекладины"),
    ("FrontZ", "-57 mm", "Передний край ноутбука Z", "Положение нижней поверхности относительно верха перекладины"),
    ("SlotWidth", "7.5 mm", "Ширина отверстий", "Под предполагаемый M6 с запасом, проверить пробником"),
    ("SlotLength", "12 mm", "Длина отверстий", "Продолговатые сквозные отверстия вдоль пары болтов"),
    ("TableAcross", "700 mm", "Стол: вдоль перекладины", "УСЛОВНО, общий вид без влияния на посадку"),
    ("TableAlong", "1400 mm", "Стол: длина", "УСЛОВНО, общий вид без влияния на посадку"),
    ("TableHeight", "740 mm", "Стол: высота", "УСЛОВНО, общий вид без влияния на посадку"),
    ("Overhang", "10 mm", "Свес столешницы", "ОЦЕНКА по фото, относительно внешней грани перекладины"),
    ("LegInset", "65 mm", "Отступ ног от торцов", "УСЛОВНО, вне зоны держателей"),
]
for row, (alias, value, label, note) in enumerate(PARAMS, 2):
    P.set("A%d" % row, label)
    P.set("B%d" % row, value)
    P.setAlias("B%d" % row, alias)
    P.set("C%d" % row, note)
    if "ОЦЕНКА" in note or "ДОПУЩЕНИЕ" in note or "УСЛОВНО" in note:
        P.setBackground("A%d:C%d" % (row, row), (1.0, .92, .73))
doc.recompute()

def val(alias):
    return getattr(P, alias).Value

def group(name, label):
    obj = doc.addObject("App::DocumentObjectGroup", name)
    obj.Label = label
    return obj

def box(name, label, parent, dims, xyz, color, transparency=0):
    obj = doc.addObject("Part::Box", name)
    obj.Label = label
    parent.addObject(obj)
    for prop, expr in zip(("Length", "Width", "Height"), dims):
        obj.setExpression(prop, expr)
    for axis, expr in zip("xyz", xyz):
        obj.setExpression("Placement.Base." + axis, expr)
    obj.ViewObject.ShapeColor = color
    obj.ViewObject.LineColor = (.18, .19, .21)
    obj.ViewObject.Transparency = transparency
    return obj

def cylinder(name, label, parent, radius, height, xyz, color):
    obj = doc.addObject("Part::Cylinder", name)
    obj.Label = label
    parent.addObject(obj)
    obj.setExpression("Radius", radius)
    obj.setExpression("Height", height)
    for axis, expr in zip("xyz", xyz):
        obj.setExpression("Placement.Base." + axis, expr)
    obj.ViewObject.ShapeColor = color
    return obj

env = group("Environment", "01 Окружение — замеренные сопряжения")
detail = group("TableDetail", "Стол — фрагмент у креплений")
env.addObject(detail)
steel = (.20, .22, .25)
silver = (.70, .73, .77)
white = (.88, .89, .85)
box("Beam", "Перекладина 60.21 × 30.48", detail,
    ("560 mm", "Parameters.BeamWidth", "Parameters.BeamHeight"),
    ("-280 mm", "0 mm", "-Parameters.BeamHeight"), steel)
box("TabletopDetail", "Столешница — фрагмент", detail,
    ("560 mm", "220 mm", "Parameters.TabletopThickness"),
    ("-280 mm", "-Parameters.Overhang", "Parameters.SpacerHeight"), white, 78)
for side, cx in (("Left", "-Parameters.MountSpacing / 2"), ("Right", "Parameters.MountSpacing / 2")):
    box("Spacer"+side, "Верхняя проставка — "+side, detail,
        ("Parameters.SpacerWidth", "Parameters.BeamWidth", "Parameters.SpacerHeight"),
        (cx+" - Parameters.SpacerWidth / 2", "0 mm", "0 mm"), steel)
    plate = box("Plate"+side, "Нижняя пластина — "+side, detail,
        ("Parameters.PlateWidth", "Parameters.BeamWidth", "Parameters.PlateThickness"),
        (cx+" - Parameters.PlateWidth / 2", "0 mm", "-Parameters.BeamHeight - Parameters.PlateThickness"), steel)
    for i, sign in enumerate((-1,1),1):
        y = "Parameters.BeamWidth / 2 %s Parameters.BoltPitch / 2" % ("-" if sign < 0 else "+")
        cylinder("Bolt"+side+str(i), "Болт — условный M6, длина неизвестна", detail,
                 "Parameters.BoltDiameter / 2", "Parameters.BoltLength", (cx, y,
                 "-Parameters.BeamHeight - Parameters.PlateThickness - Parameters.BeamClearance - Parameters.ClampShelf"), silver)
        cylinder("Head"+side+str(i), "Головка 13.65 × 1.70", detail,
                 "Parameters.HeadDiameter / 2", "Parameters.HeadHeight", (cx, y,
                 "-Parameters.BeamHeight - Parameters.PlateThickness - Parameters.BeamClearance - Parameters.ClampShelf - Parameters.HeadHeight"), silver)

full = group("WholeTable", "Стол целиком — УСЛОВНЫЕ габариты, включить вместо фрагмента")
env.addObject(full)
box("TabletopFull", "Столешница — условно 1400 × 700", full,
    ("Parameters.TableAcross", "Parameters.TableAlong", "Parameters.TabletopThickness"),
    ("-Parameters.TableAcross / 2", "-Parameters.Overhang", "Parameters.SpacerHeight"), white, 25)
for k, y in (("Near", "0 mm"), ("Far", "Parameters.TableAlong - 2 * Parameters.Overhang - Parameters.BeamWidth")):
    box("BeamFull"+k, "Перекладина — "+k, full,
        ("Parameters.TableAcross - 2 * Parameters.LegInset + Parameters.BeamWidth", "Parameters.BeamWidth", "Parameters.BeamHeight"),
        ("-Parameters.TableAcross / 2 + Parameters.LegInset - Parameters.BeamWidth / 2",y,"-Parameters.BeamHeight"), steel)
    for j, x in (("Left","-Parameters.TableAcross / 2 + Parameters.LegInset - Parameters.BeamWidth / 2"),
                 ("Right","Parameters.TableAcross / 2 - Parameters.LegInset - Parameters.BeamWidth / 2")):
        box("Leg"+k+j,"Нога — "+k+" / "+j,full,
            ("Parameters.BeamWidth","Parameters.BeamHeight","Parameters.TableHeight - Parameters.TabletopThickness - Parameters.SpacerHeight - Parameters.BeamHeight"),
            (x,y,"Parameters.SpacerHeight + Parameters.TabletopThickness - Parameters.TableHeight"),steel)
for j, x in (("Left","-Parameters.TableAcross / 2 + Parameters.LegInset - Parameters.BeamHeight / 2"),
             ("Right","Parameters.TableAcross / 2 - Parameters.LegInset - Parameters.BeamHeight / 2")):
    box("LongRail"+j,"Продольная связь — "+j,full,
        ("Parameters.BeamHeight","Parameters.TableAlong - 2 * Parameters.Overhang","Parameters.BeamWidth"),
        (x,"0 mm","-Parameters.BeamWidth"),steel)

laptop = group("Laptop", "Ноутбук — основание 332 × 14, наклон 30°")
env.addObject(laptop)
base = box("LaptopBase", "Основание ноутбука", laptop,
           ("Parameters.LaptopWidth", "Parameters.LaptopDepth", "Parameters.LaptopThickness"),
           ("-Parameters.LaptopWidth / 2","Parameters.FrontY + Parameters.LaptopDepth * cos(Parameters.LaptopAngle)","Parameters.FrontZ - Parameters.LaptopDepth * sin(Parameters.LaptopAngle)"), silver)
# Local Y points towards the front edge; local Z is the upward normal.
base.setExpression("Placement.Base.y", "Parameters.FrontY - Parameters.LaptopDepth * cos(Parameters.LaptopAngle)")
base.setExpression("Placement.Base.z", "Parameters.FrontZ + Parameters.LaptopDepth * sin(Parameters.LaptopAngle)")
placement = base.Placement
placement.Rotation = App.Rotation(App.Vector(1,0,0), -30)
base.Placement = placement
base.setExpression("Placement.Rotation.Angle", "-Parameters.LaptopAngle")

# Screen is a visual reference. Hinge angle and screen height were not measured.
screen = box("LaptopScreen", "Экран — условная геометрия", laptop,
             ("Parameters.LaptopWidth", "5 mm", "205 mm"),
             ("-Parameters.LaptopWidth / 2","Parameters.FrontY - Parameters.LaptopDepth * cos(Parameters.LaptopAngle) + Parameters.LaptopThickness * sin(Parameters.LaptopAngle)",
              "Parameters.FrontZ + Parameters.LaptopDepth * sin(Parameters.LaptopAngle) + Parameters.LaptopThickness * cos(Parameters.LaptopAngle)"), (.10,.13,.18))
screen.Placement.Rotation = App.Rotation(App.Vector(1,0,0),5)

doc.recompute()
for obj in full.Group:
    obj.ViewObject.Visibility = False
full.ViewObject.Visibility = False
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
doc.recompute()
doc.saveAs(str(ROOT / "LaptopDeskMount.FCStd"))
print("Environment saved:", doc.FileName)
print("Measured spacer width:", P.SpacerWidth)

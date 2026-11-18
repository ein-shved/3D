"""Three optional heat-set-fit holes, matching the upper stop's pocket depth."""
from pathlib import Path
import FreeCAD as App
import Part
import MeshPart

ROOT = Path(__file__).resolve().parent
D = App.getDocument("LaptopDeskMount")
if D.getObject("HookInsertFitSample"):
    raise RuntimeError("Insert sample already exists")
b = D.addObject("PartDesign::Body", "HookInsertFitSample")
b.Label = "Пробник вставки M4 Ø6: отверстия 5.4 / 5.6 / 5.8 слева направо"
D.FitSamples.addObject(b)
base = b.newObject("PartDesign::AdditiveBox", "HookSampleBlock")
base.Label = "Пробник посадки вставки, 34 × 14 × 8.5"
base.Length, base.Width, base.Height = 34, 14, 8.5
D.recompute()
for i, diameter in enumerate((5.4, 5.6, 5.8)):
    previous = b.Tip
    bore = b.newObject("PartDesign::SubtractiveCylinder", "HookSampleBore%d" % i)
    bore.Label = "Отверстие %.1f мм, глубина 6.4 мм" % diameter
    bore.Radius = diameter / 2
    bore.setExpression("Height", "HookParameters.InsertPocketDepth + 1 mm")
    bore.Placement.Base = App.Vector(6 + 11 * i, 7, 2.1)
    bore.Refine = True
    D.recompute()
    previous.ViewObject.Visibility = False
    entry = b.newObject("PartDesign::SubtractiveCone", "HookSampleEntry%d" % i)
    entry.Label = "Заходная фаска к отверстию %.1f" % diameter
    entry.Radius1, entry.Radius2, entry.Height = diameter / 2, 3, .4
    entry.Placement.Base = App.Vector(6 + 11 * i, 7, 8.1)
    entry.Refine = True
    D.recompute()
    bore.ViewObject.Visibility = False
if not b.Shape.isValid() or len(b.Shape.Solids) != 1:
    raise RuntimeError("Invalid insert-fit sample")
mesh = MeshPart.meshFromShape(Shape=b.Shape, LinearDeflection=.05, AngularDeflection=.15, Relative=False)
if not mesh.isSolid():
    raise RuntimeError("Insert sample STL is not closed")
mesh.write(str(ROOT / "exports" / "headphone_insert_fit_sample.stl"))
Part.export([b], str(ROOT / "exports" / "headphone_insert_fit_sample.step"))
for o in b.Group:
    o.ViewObject.Visibility = False
b.ViewObject.Visibility = False
D.FitSamples.ViewObject.Visibility = False
D.recompute()
print("Insert sample exported: 34x14x8.5, bore diameters 5.4/5.6/5.8, depth6.4, entrance6.0")

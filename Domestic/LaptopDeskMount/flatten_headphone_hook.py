"""Migrate the main hook to a planar print base and full-width rectangular shelf."""
from pathlib import Path
import FreeCAD as App
import Part
import Sketcher


def apply_flat_base(doc):
    H = doc.HookParameters
    upper = doc.HeadphoneHookUpper
    cell = H.getCellFromAlias("BoltEngagement")
    if not cell:
        row = max(i for i in range(1,250) if H.getContents("A%d" % i)) + 1
        cell = "B%d" % row
        H.set("A%d" % row,"Номинальное зацепление болта")
        H.setAlias(cell,"BoltEngagement")
    H.set(cell,"=InsertLength - 0.2 mm")
    H.set("C"+cell[1:],"Вставка 6 мм, запас 0.2 мм до её заднего торца")
    H.set(H.getCellFromAlias("UpperBossBottom"),"=ShelfBottom")
    H.set("C"+H.getCellFromAlias("UpperBossBottom")[1:],"Плоский низ основной детали; вставка в полке без выступа")
    H.set(H.getCellFromAlias("HeadPocketDepth"),"=UpperBossBottom - BottomZ - BoltLength + BoltEngagement")
    H.set("C"+H.getCellFromAlias("HeadPocketDepth")[1:],"Углублён для M4×20 при плоском низе основной детали")
    doc.recompute()
    profile = doc.HookShelfSketch
    if profile.GeometryCount != 4:
        # Replace the old six-sided L contour, preserving its editable sketch and Pad.
        for path, expression in list(profile.ExpressionEngine):
            if path.startswith("Constraints["):
                profile.setExpression(path,None)
        for i in reversed(range(profile.ConstraintCount)):
            profile.delConstraint(i)
        for i in reversed(range(profile.GeometryCount)):
            profile.delGeometry(i)
        xy = [("HookParameters.ClampX","HookParameters.BossY"),
              ("HookParameters.CornerX","HookParameters.BossY"),
              ("HookParameters.CornerX","HookParameters.UpperBackEnd"),
              ("HookParameters.ClampX","HookParameters.UpperBackEnd")]
        vertices = [App.Vector(upper.evalExpression(x).Value,upper.evalExpression(y).Value,0) for x,y in xy]
        for i,vertex in enumerate(vertices):
            profile.addGeometry(Part.LineSegment(vertex,vertices[(i+1)%4]),False)
        for i,vertex in enumerate(vertices):
            profile.addConstraint(Sketcher.Constraint("Coincident",i,2,(i+1)%4,1))
            for kind,value,expression in (("DistanceX",vertex.x,xy[i][0]),("DistanceY",vertex.y,xy[i][1])):
                idx=profile.addConstraint(Sketcher.Constraint(kind,i,1,value))
                profile.setExpression("Constraints[%d]" % idx,expression)
    profile.Label = "Прямоугольная полка на всю ширину основной детали"
    doc.HookRearChannel.BaseFeature = doc.HookShelfRounds
    doc.HookRearChannel.setExpression("Length","HookParameters.StopWidth + 2 mm")
    doc.HookRearLip.setExpression("Length","HookParameters.StopWidth")
    if doc.getObject("HookFrontBoss"):
        doc.removeObject("HookFrontBoss")
    cell = H.getCellFromAlias("ArmDepth")
    if cell:
        H.setAlias(cell,"")
        for col in "ABC": H.clear(col+cell[1:])
    doc.recompute()
    shelf = doc.HookShelf
    edges = ["Edge%d" % i for i,e in enumerate(shelf.Shape.Edges,1)
             if abs(e.BoundBox.ZLength-H.ShelfThickness.Value)<1e-5
             and e.BoundBox.XLength<1e-6 and e.BoundBox.YLength<1e-6]
    if len(edges)!=4:
        raise RuntimeError("Expected four rectangular shelf corners")
    doc.HookShelfRounds.Base = (shelf,edges)
    doc.recompute()
    if not doc.HookShelfRounds.Shape.isValid():
        raise RuntimeError("Invalid rectangular shelf rounds")
    print("Flat base applied: insert bottom",H.UpperBossBottom,"head pocket",H.HeadPocketDepth)


if __name__ == "__main__":
    doc = App.getDocument("LaptopDeskMount")
    apply_flat_base(doc)
    p = Path(__file__).resolve().parent / "refresh_headphone_hook.py"
    exec(compile(p.read_text(),str(p),"exec"),{"__file__":str(p),"__name__":"__main__"})

"""Merged sidewalls and finishing requested in the user's Sketch004/Fillet example."""
import math
import FreeCAD as App
import Part
import Sketcher


def ensure_merged_profile(doc,sk):
    H=doc.HookParameters
    if sk.GeometryCount==10:return
    for path,value in list(sk.ExpressionEngine):
        if path.startswith("Constraints["):sk.setExpression(path,None)
    for i in reversed(range(sk.ConstraintCount)):sk.delConstraint(i)
    for i in reversed(range(sk.GeometryCount)):sk.delGeometry(i)
    def val(expression):return doc.HeadphoneHookUpper.evalExpression(expression).Value
    def line(x1,y1,x2,y2):
        p1=App.Vector(val(x1),val(y1),0);p2=App.Vector(val(x2),val(y2),0)
        i=sk.addGeometry(Part.LineSegment(p1,p2),False)
        for typ,pos,num,ex in (("DistanceX",1,p1.x,x1),("DistanceY",1,p1.y,y1),("DistanceX",2,p2.x,x2),("DistanceY",2,p2.y,y2)):
            c=sk.addConstraint(Sketcher.Constraint(typ,i,pos,num));sk.setExpression("Constraints[%d]"%c,ex)
    def arc(cx,cy,radius,a1,am,a2,start_axis,end_axis):
        x,y,r=val(cx),val(cy),val(radius)
        point=lambda a:App.Vector(x+r*math.cos(a),y+r*math.sin(a),0)
        i=sk.addGeometry(Part.Arc(point(a1),point(am),point(a2)),False)
        for typ,pos,num,ex in (("DistanceX",3,x,cx),("DistanceY",3,y,cy),
                               ("Distance"+start_axis,1,x if start_axis=="X" else y,cx if start_axis=="X" else cy),
                               ("Distance"+end_axis,2,x if end_axis=="X" else y,cx if end_axis=="X" else cy)):
            c=sk.addConstraint(Sketcher.Constraint(typ,i,pos,num));sk.setExpression("Constraints[%d]"%c,ex)
        c=sk.addConstraint(Sketcher.Constraint("Radius",i,r));sk.setExpression("Constraints[%d]"%c,radius)
    x0,x1="HookParameters.ClampX","HookParameters.CornerX"
    l,r="HookParameters.CableLeftCenter","HookParameters.CableRightCenter"
    cy="HookParameters.CableCenterY";back="HookParameters.CableBackY"
    outer="HookParameters.CableOuterRadius";inner="HookParameters.CableGap / 2"
    front=cy+" - "+outer
    # Straight sidewalls join the hook's side plane, then meet the oval front tangentially.
    line(x0,back,x1,back)
    line(x1,back,x1,cy)
    arc(r,cy,outer,0,-math.pi/4,-math.pi/2,"Y","X")
    line(r,front,l,front)
    arc(l,cy,outer,-math.pi/2,-3*math.pi/4,-math.pi,"X","Y")
    line(x0,cy,x0,back)
    line(r,cy+" + ("+inner+")",l,cy+" + ("+inner+")")
    arc(l,cy,inner,math.pi/2,math.pi,3*math.pi/2,"X","X")
    line(l,cy+" - ("+inner+")",r,cy+" - ("+inner+")")
    arc(r,cy,inner,-math.pi/2,0,math.pi/2,"X","X")
    sk.Label="Единые боковые стенки и овальный проход — по Sketch004"
    doc.recompute()
    if not sk.FullyConstrained:raise RuntimeError("Merged cable profile is not fully constrained")


def make_fillet(doc,body,name,label,base,edges,radius,existing=None):
    obj=existing or doc.getObject(name)
    if obj is None:
        last=[o for o in body.Group if o.TypeId.startswith("PartDesign::")]
        if last:body.Tip=last[-1]
        obj=body.newObject("PartDesign::Fillet",name)
    obj.Label=label
    obj.BaseFeature=base;obj.Base=(base,edges)
    obj.setExpression("Radius",radius);obj.Refine=True
    doc.recompute()
    if obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:
        raise RuntimeError("Invalid finishing operation "+obj.Name+": "+obj.getStatusString())
    base.ViewObject.Visibility=False
    return obj


def finish_upper(doc,base):
    H=doc.HookParameters;body=doc.HeadphoneHookUpper
    # Reuse the user's actual Fillet example, applying the same treatment on both sides.
    example=doc.getObject("HookMouthEntryRounds")
    if example is None:
        candidate=doc.getObject("Fillet")
        if candidate is not None and candidate in body.Group:example=candidate
    edges=[]
    for i,e in enumerate(base.Shape.Edges,1):
        b=e.BoundBox
        if b.XLength<1e-6 and b.YLength<1e-6 and b.ZLength>1:
            if min(abs(b.XMin-H.ClampX.Value),abs(b.XMin-H.CornerX.Value))<1e-5:
                if min(abs(b.YMin-H.RearLipFront.Value),abs(b.YMin-(H.BeamBack.Value-H.JointClearance.Value)))<1e-5:
                    edges.append("Edge%d"%i)
    if len(edges)!=4:raise RuntimeError("Expected four entrance side edges: "+str(edges))
    mouth=make_fillet(doc,body,"HookMouthEntryRounds","Входные углы зацепа R1 — по примеру пользователя",base,edges,"HookParameters.EntryCornerRadius",example)
    edges=["Edge%d"%i for i,e in enumerate(mouth.Shape.Edges,1)
           if e.BoundBox.ZLength<1e-6 and abs(e.BoundBox.ZMin-H.ShelfBottom.Value)<1e-5]
    bottom=make_fillet(doc,body,"HookBottomRounds","Скругления нижних кромок основной детали R1",mouth,edges,"HookParameters.BottomEdgeRadius")
    mouth.ViewObject.Visibility=False
    return mouth,bottom


def finish_lower(doc):
    H=doc.HookParameters;body=doc.HeadphoneHookLower;base=doc.HookClampHeadPocket
    edges=["Edge%d"%i for i,e in enumerate(base.Shape.Edges,1)
           if e.BoundBox.XLength<1e-6 and min(abs(e.BoundBox.XMin-H.ClampX.Value),abs(e.BoundBox.XMin-(H.ClampX.Value+H.ClipWidth.Value)))<1e-5]
    sides=make_fillet(doc,body,"HookLowerSideRounds","Скругления боковых кромок нижнего захвата R1",base,edges,"HookParameters.LowerSideRadius")
    order=[o for o in body.Group if o!=sides]
    order.insert(order.index(base)+1,sides);body.Group=order;body.Tip=sides
    for o in body.Group:o.ViewObject.Visibility=o==sides
    return sides

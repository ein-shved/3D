"""Equal rear joint, merged oval guide, entrance rounds, and sketch references."""
from pathlib import Path
import json
import FreeCAD as App
import Part
import Sketcher


def set_parameter(sheet, alias, value, label, note):
    cell = sheet.getCellFromAlias(alias)
    if not cell:
        row = max(i for i in range(1,350) if sheet.getContents("A%d" % i)) + 1
        cell = "B%d" % row
        sheet.setAlias(cell,alias)
    sheet.set("A"+cell[1:],label)
    sheet.set(cell,value)
    sheet.set("C"+cell[1:],note)


def set_dimensions(doc):
    H=doc.HookParameters
    values=[
        ("JointThird","=ShelfThickness / 3","Три равных участка заднего узла","По эскизу пользователя: верх, просвет и нижний борт равны"),
        ("ChannelRoof","=ShelfTop - JointThird","Низ перекрытия паза","Толщина верхней перемычки равна трети высоты"),
        ("RearLipTop","=ShelfBottom + JointThird","Верх нижнего борта","Толщина нижнего борта равна трети высоты"),
        ("TongueBottom","=RearLipTop + JointClearance","Низ нижнего зацепа","Зазор к нижнему борту 0.3 мм"),
        ("TongueTop","=ChannelRoof - 2 * JointClearance","Верх нижнего зацепа","Зазор 0.6 мм допускает подтяжку обхвата"),
        ("JointInsideRadius","0 mm","Задние углы паза без скругления","Прежнее R0.8 отменено по уточнению пользователя"),
        ("EntryCornerRadius","1 mm","Входные углы зацепа","По примеру Fillet пользователя"),
        ("BottomEdgeRadius","1 mm","Нижние кромки основной детали","Плоская опорная поверхность сохранена"),
        ("LowerSideRadius","1 mm","Боковые кромки нижней детали","Скруглены по периметрам боковых плоскостей"),
        ("StopEdgeRadius","2.5 mm","Кромки основного ограничителя","Сохраняют передний касательный участок"),
        ("CableBackY","=BossY + StopEdgeRadius","Сопряжение стенок петли с основанием","По Sketch004: боковые грани в одной плоскости"),
        ("BoltLength","15 mm","Длина болта M4 под головкой","Самый длинный доступный болт пользователя: M4×15"),
        ("InsertOuterDiameter","5.69 mm","Наружный диаметр вставки","Фото пользователя 5.69 мм, отверстие не более 5.7 мм"),
        ("InsertPocketDiameter","5.6 mm","Отверстие для вплавления","Меньше заданного предела 5.7 мм"),
        ("JackDiameter","3.5 mm","Номинал джека","Принят обычный джек 3.5 мм"),
        ("CableGap","=4 * JackDiameter","Свободный проход провода","По указанию пользователя: четыре диаметра джека, 14 мм"),
        ("CableWall","4 mm","Стенка овальной петли","Выбрана толщина 4 мм"),
        ("CableOuterRadius","=CableGap / 2 + CableWall","Наружный радиус овала","R11, стенки равномерные"),
        ("CableCenterY","=BossY - CableGap / 2","Центр овала Y","Петля перед ограничителем со стороны ноутбука"),
        ("CableLeftCenter","=ClampX + CableOuterRadius","Левый центр дуги овала","Наружный левый край совпадает с основанием"),
        ("CableRightCenter","=CornerX - CableOuterRadius","Правый центр дуги овала","Правый край остаётся у торца столешницы"),
        ("CableTop","=TableTopZ","Верх петли для провода","Вровень с верхней поверхностью столешницы"),
        ("CableRimRadius","1 mm","Кромки овальной петли","Мягкий вход без уменьшения свободного прохода")]
    for alias,value,label,note in values:
        set_parameter(H,alias,value,label,note)
    doc.recompute()


def capture_guides(doc):
    return {name:App.Placement(doc.getObject(name).Placement) for name in ("Sketch001","Sketch002","Sketch003","Sketch004")
            if doc.getObject(name)}


def rebind_user_guides(doc,placements):
    """Keep the user's attachment geometry meaningful before cosmetic rounds/oval union."""
    H=doc.HookParameters
    source=doc.HookStopRim
    def attach(sk,plane,value):
        candidates=[]
        for i,f in enumerate(source.Shape.Faces,1):
            b=f.BoundBox
            span=b.XLength if plane=="x" else b.ZLength
            coord=b.XMin if plane=="x" else b.ZMin
            if span<1e-6 and abs(coord-value)<1e-5:candidates.append((f.Area,i))
        if not candidates:raise RuntimeError("No support face for "+sk.Name)
        index=max(candidates)[1]
        sk.AttachmentSupport=[(source,("Face%d" % index,))]
        sk.MapMode="FlatFace"
        doc.recompute()
        mapping=sk.Placement.multiply(sk.AttachmentOffset.inverse())
        sk.AttachmentOffset=mapping.inverse().multiply(placements[sk.Name])
        doc.recompute()
    def side_edge(shape,z,y_end=None,y_contains=None):
        result=[]
        for i,e in enumerate(shape.Edges,1):
            b=e.BoundBox
            if b.XLength<1e-6 and abs(b.XMin-H.CornerX.Value)<1e-5 and b.ZLength<1e-6 and abs(b.ZMin-z)<1e-5 and b.YLength>1:
                if y_end is not None and abs(b.YMax-y_end)>1e-5:continue
                if y_contains is not None and not b.YMin-1e-5<=y_contains<=b.YMax+1e-5:continue
                result.append((e.Length,"Edge%d" % i))
        if not result:raise RuntimeError("No sketch reference edge at Z"+str(z))
        return min(result)[1]
    def replace_external(sk,source,names):
        values=[(c.Type,c.First,c.FirstPos,c.Second,c.SecondPos) for c in sk.Constraints]
        if not values:
            backup=Path(doc.FileName).parent/"references"/"joint_and_oval_user_sketches.json"
            if backup.exists():
                saved=json.loads(backup.read_text()).get(sk.Name,{})
                values=[(c["type"],c["first"],c["first_pos"],c["second"],c["second_pos"]) for c in saved.get("constraints",[])]
            if sk.Name=="Sketch004":
                backup=Path(doc.FileName).parent/"references"/"wall_merge_user_sketch.json"
                if backup.exists():
                    saved=json.loads(backup.read_text())
                    values=[(c["type"],c["first"],c["first_pos"],c["second"],c["second_pos"]) for c in saved["constraints"]]
        for i in reversed(range(sk.ConstraintCount)):sk.delConstraint(i)
        # Recompute each removal: FreeCAD updates the projected-geometry indices lazily.
        while sk.ExternalGeometry:
            sk.delExternal(0)
            doc.recompute()
        for name in names:
            target,element=(source,name) if isinstance(name,str) else name
            sk.addExternal(target.Name,element)
            doc.recompute()
        return values
    def rebuild_constraints(sk,replacements,values):
        for i in reversed(range(sk.ConstraintCount)):sk.delConstraint(i)
        for typ,a,ap,b,bp in values:
            if typ in ("Coincident","Tangent"):
                if b in replacements:bp=replacements[b]
                c=Sketcher.Constraint(typ,a,ap,b,bp)
            elif typ in ("Vertical","Horizontal"):c=Sketcher.Constraint(typ,a)
            elif typ=="PointOnObject":c=Sketcher.Constraint(typ,a,ap,b)
            else:raise RuntimeError("Unsupported guide constraint "+typ)
            sk.addConstraint(c)
        doc.recompute()
    def endpoint(sk,external,want_max):
        values=[(sk.Placement.multVec(sk.getPoint(external,p)).y,p) for p in (1,2)]
        return (max(values) if want_max else min(values))[1]
    if "Sketch001" in placements:
        sk=doc.Sketch001
        attach(sk,"x",H.CornerX.Value)
        ref=doc.HookRearLip
        names=[side_edge(ref.Shape,H.RearLipTop.Value,y_end=H.UpperBackInner.Value),
               side_edge(ref.Shape,H.ShelfBottom.Value,y_contains=H.UpperBackInner.Value),
               side_edge(ref.Shape,H.ChannelRoof.Value,y_end=H.UpperBackInner.Value),
               side_edge(ref.Shape,H.ShelfTop.Value,y_contains=H.UpperBackInner.Value)]
        values=replace_external(sk,ref,names)
        rebuild_constraints(sk,{-3:endpoint(sk,-3,True),-5:endpoint(sk,-5,True)},values)
    if "Sketch002" in placements:attach(doc.Sketch002,"z",H.StopTop.Value)
    if "Sketch003" in placements:
        sk=doc.Sketch003
        attach(sk,"z",H.ShelfBottom.Value)
        def edge_at(axis,coord):
            result=[]
            for i,e in enumerate(source.Shape.Edges,1):
                b=e.BoundBox
                if b.ZLength>1e-6 or abs(b.ZMin-H.ShelfBottom.Value)>1e-5:continue
                if axis=="y" and b.YLength<1e-6 and abs(b.YMin-coord)<1e-5 and b.XLength>10:result.append((e.Length,"Edge%d" % i))
                if axis=="x" and b.XLength<1e-6 and abs(b.XMin-coord)<1e-5 and b.YLength>10 and b.YMin<0:result.append((e.Length,"Edge%d" % i))
            if not result:raise RuntimeError("No oval guide reference edge")
            return max(result)[1]
        values=replace_external(sk,source,[edge_at("y",H.BossY.Value),edge_at("x",H.ClampX.Value),edge_at("x",H.CornerX.Value)])
        rebuild_constraints(sk,{-4:endpoint(sk,-4,False),-5:endpoint(sk,-5,False)},values)
    if "Sketch004" in placements:
        sk=doc.Sketch004
        attach(sk,"z",H.ShelfBottom.Value)
        side=[]
        for i,e in enumerate(source.Shape.Edges,1):
            b=e.BoundBox
            if b.XLength<1e-6 and b.ZLength<1e-6 and abs(b.XMin-H.CornerX.Value)<1e-5 and abs(b.ZMin-H.ShelfBottom.Value)<1e-5 and b.YLength>10 and b.YMin<0:
                side.append((e.Length,"Edge%d"%i))
        pad=doc.HookCablePad;arc=[];front=[]
        for i,e in enumerate(pad.Shape.Edges,1):
            b=e.BoundBox
            if b.ZLength>1e-6 or abs(b.ZMin-H.ShelfBottom.Value)>1e-5:continue
            if isinstance(e.Curve,Part.Circle) and abs(e.Curve.Radius-H.CableOuterRadius.Value)<1e-5 and b.XMin>=H.CableRightCenter.Value-1e-5 and b.YMax<=H.CableCenterY.Value+1e-5:
                arc.append("Edge%d"%i)
            if b.YLength<1e-6 and abs(b.YMin-(H.CableCenterY.Value-H.CableOuterRadius.Value))<1e-5 and b.XLength>10:
                front.append("Edge%d"%i)
        if not side or not arc or not front:raise RuntimeError("Unable to preserve Sketch004 references")
        values=replace_external(sk,None,[(source,max(side)[1]),(pad,arc[0]),(pad,front[0])])
        right=max((sk.Placement.multVec(sk.getPoint(-5,p)).x,p) for p in (1,2))[1]
        rebuild_constraints(sk,{-3:endpoint(sk,-3,False),-5:right},values)
    for name in placements:
        sk=doc.getObject(name)
        sk.ViewObject.Visibility=False


def native_fillet(doc,body,name,label,base,edges,radius):
    if not edges:
        raise RuntimeError("No edges for "+name)
    obj=doc.getObject(name) or body.newObject("PartDesign::Fillet",name)
    obj.Label=label
    obj.BaseFeature=base
    obj.Base=(base,edges)
    obj.setExpression("Radius",radius)
    obj.Refine=True
    doc.recompute()
    if obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:
        raise RuntimeError("Invalid fillet "+name+": "+obj.getStatusString())
    base.ViewObject.Visibility=False
    return obj


def round_joint(doc):
    """Undo the previous deep-back blends; entrance finishing follows the user's example."""
    H=doc.HookParameters
    upper,lower=doc.HeadphoneHookUpper,doc.HeadphoneHookLower
    base=doc.HookRearLip
    edges=["Edge%d"%i for i,e in enumerate(base.Shape.Edges,1)
           if abs(e.BoundBox.ZLength-H.ShelfThickness.Value)<1e-5 and e.BoundBox.XLength<1e-6 and e.BoundBox.YLength<1e-6]
    doc.HookShelfRounds.BaseFeature=base;doc.HookShelfRounds.Base=(base,edges)
    if doc.getObject("HookChannelInnerRounds"):doc.removeObject("HookChannelInnerRounds")
    base=doc.HookClampTongue
    edges=[]
    for i,e in enumerate(base.Shape.Edges,1):
        b=e.BoundBox
        if b.XLength>H.ClipWidth.Value-1e-5 and b.YLength<1e-6 and b.ZLength<1e-6:
            if abs(b.ZMin-H.BottomZ.Value)<1e-5 or abs(b.YMin-H.BossY.Value)<1e-5:edges.append("Edge%d"%i)
    doc.HookClampRounds.BaseFeature=base;doc.HookClampRounds.Base=(base,edges)
    if doc.getObject("HookTongueRounds"):doc.removeObject("HookTongueRounds")
    lower.Tip=doc.HookClampHeadPocket;upper.Tip=doc.HookInsertLeadIn
    doc.recompute()


def add_oval_loop(doc):
    H=doc.HookParameters;body=doc.HeadphoneHookUpper
    pocket=doc.getObject("HookInsertPocket")
    body.Tip=doc.HookInsertLeadIn if pocket else doc.HookStopRim
    existing=[doc.getObject(n) for n in ("HookCableSketch","HookCablePad","HookCableInnerRounds","HookCableRim") if doc.getObject(n)]
    if existing and pocket:
        order=[o for o in body.Group if o not in existing]
        index=order.index(pocket)
        body.Group=order[:index]+existing+order[index:]
    sk=doc.getObject("HookCableSketch")
    if sk is None:
        sk=body.newObject("Sketcher::SketchObject","HookCableSketch")
        sk.setExpression("Placement.Base.z","HookParameters.ShelfBottom")
    p=Path(__file__).resolve().parent/"finish_headphone_walls.py"
    walls={"__file__":str(p),"__name__":"hook_walls"}
    exec(compile(p.read_text(),str(p),"exec"),walls)
    walls["ensure_merged_profile"](doc,sk)
    doc.recompute()
    pad=doc.getObject("HookCablePad") or body.newObject("PartDesign::Pad","HookCablePad")
    pad.Label="Овальная петля до верхней поверхности столешницы"
    pad.Profile=sk
    pad.BaseFeature=doc.HookStopRim
    pad.setExpression("Length","HookParameters.CableTop - HookParameters.ShelfBottom")
    pad.Refine=True
    doc.recompute()
    if pad.Shape.isNull() or not pad.Shape.isValid() or len(pad.Shape.Solids)!=1:raise RuntimeError("Invalid oval cable pad: "+pad.getStatusString())
    def top_edges(shape,inside):
        edges=[]
        radius=H.CableGap.Value/2 if inside else H.CableOuterRadius.Value
        for i,e in enumerate(shape.Edges,1):
            b=e.BoundBox
            if b.ZLength>1e-6 or abs(b.ZMin-H.CableTop.Value)>1e-5 or e.CenterOfMass.y>=H.BossY.Value-.1:continue
            circular=isinstance(e.Curve,Part.Circle) and abs(e.Curve.Radius-radius)<1e-5
            straight=isinstance(e.Curve,Part.Line) and (abs(e.CenterOfMass.y-(H.CableCenterY.Value-radius))<1e-5 or (not inside and b.XLength<1e-6 and min(abs(b.XMin-H.ClampX.Value),abs(b.XMin-H.CornerX.Value))<1e-5))
            if circular or straight:edges.append("Edge%d" % i)
        return edges
    # Separate inside/outside blends avoid an OCCT combined corner solution that closes the passage.
    inside=native_fillet(doc,body,"HookCableInnerRounds","Мягкий внутренний вход петли R1",pad,top_edges(pad.Shape,True),"HookParameters.CableRimRadius")
    rim=native_fillet(doc,body,"HookCableRim","Мягкие наружные кромки петли R1",inside,top_edges(inside.Shape,False),"HookParameters.CableRimRadius")
    if rim.Shape.Volume>pad.Shape.Volume+1e-5:raise RuntimeError("Cable rim unexpectedly added material")
    mouth,bottom=walls["finish_upper"](doc,rim)
    pocket=doc.getObject("HookInsertPocket")
    items=[sk,pad,inside,rim,mouth,bottom]
    if pocket:
        pocket.BaseFeature=bottom
        order=[o for o in body.Group if o not in items]
        index=order.index(pocket)
        body.Group=order[:index]+items+order[index:]
        body.Tip=doc.HookInsertLeadIn
    else:body.Tip=bottom
    sk.ViewObject.Visibility=False
    doc.HookStopRim.ViewObject.Visibility=False
    pad.ViewObject.Visibility=False
    doc.recompute()
    return rim

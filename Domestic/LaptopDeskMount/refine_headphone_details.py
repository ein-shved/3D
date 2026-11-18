"""Equal rear joint, rounded mating tips, oval cable guide, and sketch references."""
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
        ("JointInsideRadius","0.8 mm","Внутренние углы заднего паза","Скруглены вместе с сопряжённым концом нижнего зацепа"),
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
    return {name:App.Placement(doc.getObject(name).Placement) for name in ("Sketch001","Sketch002","Sketch003")
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
        for i in reversed(range(sk.ConstraintCount)):sk.delConstraint(i)
        count=sum(len(subs) for obj,subs in sk.ExternalGeometry)
        for i in reversed(range(count)):sk.delExternal(i)
        for name in names:sk.addExternal(source.Name,name)
        doc.recompute()
        return values
    def rebuild_constraints(sk,replacements,values):
        for i in reversed(range(sk.ConstraintCount)):sk.delConstraint(i)
        for typ,a,ap,b,bp in values:
            if typ=="Coincident":
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
    H=doc.HookParameters
    upper,lower=doc.HeadphoneHookUpper,doc.HeadphoneHookLower
    base=doc.HookRearLip
    edges=[]
    for i,e in enumerate(base.Shape.Edges,1):
        b=e.BoundBox
        if abs(b.XLength-H.StopWidth.Value)<1e-5 and b.YLength<1e-6 and b.ZLength<1e-6:
            if abs(b.YMin-H.UpperBackInner.Value)<1e-5 and min(abs(b.ZMin-z) for z in (H.ChannelRoof.Value,H.RearLipTop.Value))<1e-5:
                edges.append("Edge%d" % i)
    if len(edges)!=2:raise RuntimeError("Expected two internal channel corners: "+str(edges))
    inner=native_fillet(doc,upper,"HookChannelInnerRounds","Внутренние углы паза R0.8",base,edges,"HookParameters.JointInsideRadius")
    edges=["Edge%d" % i for i,e in enumerate(inner.Shape.Edges,1)
           if abs(e.BoundBox.ZLength-H.ShelfThickness.Value)<1e-5 and e.BoundBox.XLength<1e-6 and e.BoundBox.YLength<1e-6]
    doc.HookShelfRounds.BaseFeature=inner
    doc.HookShelfRounds.Base=(inner,edges)
    order=[o for o in upper.Group if o!=inner]
    order.insert(order.index(doc.HookShelfRounds),inner)
    upper.Group=order
    base=doc.HookClampTongue
    edges=[]
    for i,e in enumerate(base.Shape.Edges,1):
        b=e.BoundBox
        if abs(b.XLength-H.ClipWidth.Value)<1e-5 and b.YLength<1e-6 and b.ZLength<1e-6:
            if abs(b.YMin-H.TongueEnd.Value)<1e-5 and min(abs(b.ZMin-z) for z in (H.TongueTop.Value,H.TongueBottom.Value))<1e-5:
                edges.append("Edge%d" % i)
    if len(edges)!=2:raise RuntimeError("Expected two tongue nose corners: "+str(edges))
    nose=native_fillet(doc,lower,"HookTongueRounds","Скруглённый конец нижнего зацепа R0.8",base,edges,"HookParameters.JointInsideRadius")
    edges=[]
    for i,e in enumerate(nose.Shape.Edges,1):
        b=e.BoundBox
        if b.XLength>H.ClipWidth.Value-1e-5 and b.YLength<1e-6 and b.ZLength<1e-6:
            if abs(b.ZMin-H.BottomZ.Value)<1e-5 or abs(b.YMin-H.BossY.Value)<1e-5:edges.append("Edge%d" % i)
    doc.HookClampRounds.BaseFeature=nose
    doc.HookClampRounds.Base=(nose,edges)
    order=[o for o in lower.Group if o!=nose]
    order.insert(order.index(doc.HookClampRounds),nose)
    lower.Group=order
    lower.Tip=doc.HookClampHeadPocket
    doc.recompute()


def add_oval_loop(doc):
    H=doc.HookParameters;body=doc.HeadphoneHookUpper
    sk=doc.getObject("HookCableSketch")
    if sk is None:
        sk=body.newObject("Sketcher::SketchObject","HookCableSketch")
        sk.Label="Овальная петля по наброску пользователя — проход 14, стенка 4"
        sk.setExpression("Placement.Base.z","HookParameters.ShelfBottom")
        cx1,cx2,cy=H.CableLeftCenter.Value,H.CableRightCenter.Value,H.CableCenterY.Value
        for radius,radius_expr,reverse in ((H.CableOuterRadius.Value,"HookParameters.CableOuterRadius",False),
                                            (H.CableGap.Value/2,"HookParameters.CableGap / 2",True)):
            # Each capsule is dimensioned by line endpoints and arc centres/radii.
            v=lambda x,y:App.Vector(x,y,0)
            if not reverse:
                data=[("line",v(cx1,cy+radius),v(cx2,cy+radius),"HookParameters.CableLeftCenter","HookParameters.CableRightCenter",1),
                      ("arc",v(cx2,cy+radius),v(cx2+radius,cy),v(cx2,cy-radius),"HookParameters.CableRightCenter"),
                      ("line",v(cx2,cy-radius),v(cx1,cy-radius),"HookParameters.CableRightCenter","HookParameters.CableLeftCenter",-1),
                      ("arc",v(cx1,cy-radius),v(cx1-radius,cy),v(cx1,cy+radius),"HookParameters.CableLeftCenter")]
            else:
                data=[("line",v(cx2,cy+radius),v(cx1,cy+radius),"HookParameters.CableRightCenter","HookParameters.CableLeftCenter",1),
                      ("arc",v(cx1,cy+radius),v(cx1-radius,cy),v(cx1,cy-radius),"HookParameters.CableLeftCenter"),
                      ("line",v(cx1,cy-radius),v(cx2,cy-radius),"HookParameters.CableLeftCenter","HookParameters.CableRightCenter",-1),
                      ("arc",v(cx2,cy-radius),v(cx2+radius,cy),v(cx2,cy+radius),"HookParameters.CableRightCenter")]
            for item in data:
                if item[0]=="line":
                    _,p1,p2,x1,x2,sign=item
                    idx=sk.addGeometry(Part.LineSegment(p1,p2),False)
                    yexpr="HookParameters.CableCenterY %s (%s)" % ("+" if sign>0 else "-",radius_expr)
                    for typ,pos,value,expression in (("DistanceX",1,p1.x,x1),("DistanceY",1,p1.y,yexpr),("DistanceX",2,p2.x,x2),("DistanceY",2,p2.y,yexpr)):
                        c=sk.addConstraint(Sketcher.Constraint(typ,idx,pos,value));sk.setExpression("Constraints[%d]" % c,expression)
                else:
                    _,p1,mid,p2,xexpr=item
                    idx=sk.addGeometry(Part.Arc(p1,mid,p2),False)
                    center_x=cx1 if "Left" in xexpr else cx2
                    for typ,pos,value,expression in (("DistanceX",3,center_x,xexpr),("DistanceY",3,cy,"HookParameters.CableCenterY"),("DistanceX",1,center_x,xexpr),("DistanceX",2,center_x,xexpr)):
                        c=sk.addConstraint(Sketcher.Constraint(typ,idx,pos,value));sk.setExpression("Constraints[%d]" % c,expression)
                    c=sk.addConstraint(Sketcher.Constraint("Radius",idx,radius));sk.setExpression("Constraints[%d]" % c,radius_expr)
    doc.recompute()
    pad=doc.getObject("HookCablePad") or body.newObject("PartDesign::Pad","HookCablePad")
    pad.Label="Овальная петля до верхней поверхности столешницы"
    pad.Profile=sk
    pad.BaseFeature=doc.HookStopRim
    pad.setExpression("Length","HookParameters.CableTop - HookParameters.ShelfBottom")
    pad.Refine=True
    doc.recompute()
    if pad.Shape.isNull() or not pad.Shape.isValid() or len(pad.Shape.Solids)!=1:raise RuntimeError("Invalid oval cable pad: "+pad.getStatusString())
    edges=[]
    for i,e in enumerate(pad.Shape.Edges,1):
        b=e.BoundBox
        if b.ZLength<1e-6 and abs(b.ZMin-H.CableTop.Value)<1e-5 and e.CenterOfMass.y<H.BossY.Value-.1:
            edges.append("Edge%d" % i)
    rim=native_fillet(doc,body,"HookCableRim","Мягкие кромки овальной петли R1",pad,edges,"HookParameters.CableRimRadius")
    pocket=doc.getObject("HookInsertPocket")
    items=[sk,pad,rim]
    if pocket:
        pocket.BaseFeature=rim
        order=[o for o in body.Group if o not in items]
        index=order.index(pocket)
        body.Group=order[:index]+items+order[index:]
        body.Tip=doc.HookInsertLeadIn
    else:body.Tip=rim
    sk.ViewObject.Visibility=False
    doc.HookStopRim.ViewObject.Visibility=False
    pad.ViewObject.Visibility=False
    doc.recompute()
    return rim

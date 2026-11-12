from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore

root = Path(__file__).resolve().parent
d = App.getDocument("LaptopDeskMount")
v = Gui.activeDocument().activeView()
def run(name):
    p = root / name
    exec(compile(p.read_text(), str(p), "exec"), {"__file__":str(p),"__name__":"__main__"})
def capture(name):
    # Named-view changes are animated; wait for rendering on the GUI event loop.
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(600,loop.quit)
    loop.exec()
    v.fitAll()
    Gui.updateGui()
    v.saveImage(str(root / "previews" / name),1600,1100,"Current")

run("view_whole_table.FCMacro")
capture("whole_table.png")
run("view_detail.FCMacro")
v.viewRight()
capture("side.png")
d.Environment.ViewObject.Visibility = False
d.FeltPads.ViewObject.Visibility = False
for obj in d.FeltPads.Group:
    obj.ViewObject.Visibility = False
v.viewAxonometric()
capture("holders.png")
run("view_detail.FCMacro")
capture("assembly.png")
d.recompute()
d.save()
print("Saved previews and restored detail view.")

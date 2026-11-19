"""Review actual extrusion paths after slicing, including fit surfaces and supports."""
from pathlib import Path
import json
import math
import re

ROOT = Path(__file__).resolve().parent
text = (ROOT / 'headphone_hook_petg.gcode').read_text()
layout=json.loads((ROOT/'preparation.json').read_text())['parts_layout']['headphone_hook_upper']
tx,ty,_=layout['translation_mm']
width,depth,height=layout['dimensions_mm']
selected = [0.2, 6.8, 36.2, 90.0]
panels = {z: [] for z in selected}
bounds = {'min': [math.inf] * 3, 'max': [-math.inf] * 3}
support_bounds = {'min': [math.inf] * 3, 'max': [-math.inf] * 3}
extrusion, layers, support_layers = {}, set(), set()
x = y = z = e = 0.0
absolute = absolute_e = True
role = 'Custom'
first_layer_objects = set()
roof_bridges = []

for line in text.splitlines():
    if line.startswith(';TYPE:'):
        role = line[6:]
        continue
    code = line.split(';', 1)[0].strip()
    command = re.match(r'^[A-Z]\d+', code)
    if not command:
        continue
    command = command[0]
    if command in ('G90', 'G91'):
        absolute = command == 'G90'
    elif command in ('M82', 'M83'):
        absolute_e = command == 'M82'
    values = {k: float(v) for k, v in re.findall(r'([XYZE])([+-]?(?:\d+(?:\.\d*)?|\.\d+))', code)}
    if command == 'G92':
        x, y, z, e = (values.get(k, v) for k, v in zip('XYZE', (x, y, z, e)))
        continue
    if command not in ('G0', 'G1'):
        continue
    nx, ny, nz = (values.get(k, old) if absolute else old + values.get(k, 0) for k, old in zip('XYZ', (x, y, z)))
    ne = values.get('E', e) if absolute_e else e + values.get('E', 0)
    if ne > e and math.hypot(nx - x, ny - y) > 1e-6 and role != 'Custom':
        extrusion[role] = extrusion.get(role, 0) + ne - e
        supporting = role.startswith('Support')
        if role == 'Bridge infill' and abs(nz - 6.8) < 0.01 and tx+4 < x < tx+width-4 and tx+4 < nx < tx+width-4:
            if min(y, ny) < ty+92.71 and max(y, ny) > ty+105.31:
                roof_bridges.append({'start': [x, y, nz], 'end': [nx, ny, nz],
                                     'path_length_mm': math.hypot(nx-x, ny-y)})
        for box in [bounds] + ([support_bounds] if supporting else []):
            for point in ((x, y, nz), (nx, ny, nz)):
                for i in range(3):
                    box['min'][i] = min(box['min'][i], point[i])
                    box['max'][i] = max(box['max'][i], point[i])
        if supporting:
            support_layers.add(round(nz, 3))
        elif role != 'Skirt/Brim':
            layers.add(round(nz, 3))
            if abs(nz - 0.2) < 0.01:
                first_layer_objects.add('upper')
        for plane in selected:
            if abs(nz - plane) < 0.025:
                panels[plane].append((x, y, nx, ny, role))
    x, y, z, e = nx, ny, nz, ne

assert first_layer_objects == {'upper'}
assert all(0 <= bounds['min'][i] and bounds['max'][i] <= limit for i, limit in enumerate((225, 225, 265)))
assert abs(bounds['max'][2] - height) < 0.3
assert not support_layers
assert extrusion.get('Internal infill', 0) > 0
assert roof_bridges, 'Rear roof bridge paths not found'
assert all(abs(b['start'][0]-b['end'][0]) < 0.01 for b in roof_bridges), 'Roof bridges run along the long side'
report = {
    'decision': 'keep', 'printer': 'Elegoo Neptune 4 Pro', 'material': 'PETG',
    'model_layers': len(layers), 'first_layer_objects': sorted(first_layer_objects),
    'support_layers': len(support_layers), 'support_bounds_mm': None,
    'extrusion_bounds_mm': bounds, 'filament_mm_by_path_type': extrusion,
    'support_volume_cm3': sum(v for k, v in extrusion.items() if k.startswith('Support')) * math.pi * 1.75 ** 2 / 4000,
    'rear_roof_bridge': {'geometric_clear_span_mm': 12.6, 'direction': 'Y, across the short gap',
                         'full_span_extrusion_paths': len(roof_bridges),
                         'max_path_with_anchors_mm': max(b['path_length_mm'] for b in roof_bridges),
                         'speed_mm_s': 25},
    'part_names':['headphone_hook_upper'],'stop_rise_above_table_mm':60,
    'notes': [
        'Upper part only, on its requested flat underside with a brim; lower part is excluded.',
        'No support extrusion. Rear roof bridges cross the short 12.6 mm gap, anchored at both ends.',
        'Two insert seats retained; stop is 60 mm above the tabletop, 96.04 mm total print height.',
        'PETG bridge sag remains untested; clean stray strands from sliding joint if needed.',
        'No rescaling or CAD changes. Slicing prediction does not verify physical fit or strength.',
        'Three perimeters, 15% gyroid, four top/bottom layers replace the laptop mounts six perimeters and 40% infill.',
    ],
}
(ROOT / 'slice_review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

def color(role):
    if role.startswith('Support'):
        return '#e58a19'
    if role == 'Bridge infill':
        return '#a24cc9'
    if role.lower().endswith('perimeter') or role == 'Perimeter':
        return '#176294'
    return '#65a9ad'

svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="1000" viewBox="0 0 1100 1000"><rect width="1100" height="1000" fill="white"/>'
for i, (plane, segments) in enumerate(panels.items()):
    ox, oy, scale = 160 + (i % 2) * 550, 65 + (i // 2) * 480, 3.4
    svg += f'<text x="{ox}" y="{oy-22}" font-size="20">Z = {plane} mm</text>'
    for x, y, nx, ny, role in segments:
        svg += f'<path d="M{ox+(x-tx)*scale:.2f},{oy+(ty+depth-y)*scale:.2f}L{ox+(nx-tx)*scale:.2f},{oy+(ty+depth-ny)*scale:.2f}" fill="none" stroke="{color(role)}" stroke-width="0.8"/>'
svg += '<text x="45" y="985" font-size="18">Blue: walls; teal: fill; orange: supports; purple: bridge paths</text></svg>'
(ROOT / 'layer_review.svg').write_text(svg)
print(json.dumps({k: v for k, v in report.items() if k != 'filament_mm_by_path_type'}, indent=2))

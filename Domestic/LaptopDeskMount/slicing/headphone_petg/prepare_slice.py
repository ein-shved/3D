"""Prepare both hook parts and bind the sliced project to local printer presets."""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
MODEL = ROOT.parent.parent
BASE = ROOT / 'headphone_hook_petg'
PROFILES = Path('/home/shved/.config/PrusaSlicer')
PROFILE = ROOT / 'neptune4pro_petg_hook.ini'


def prepare():
    config = {}
    sources = ['print/Neptune 4 Pro.ini', 'printer/Neptune 4 Pro.ini',
               'filament/Neptune 4 - PETG.ini']
    for relative in sources:
        for line in (PROFILES / relative).read_text().splitlines():
            if not line.strip() or line.lstrip().startswith(('#', ';', '[')) or '=' not in line:
                continue
            key, value = (s.strip() for s in line.split('=', 1))
            if key == 'print_host' or key.startswith('printhost_'):
                continue
            config[key] = value
    overrides = {
        'printer_settings_id': 'Neptune 4 Pro',
        'physical_printer_settings_id': 'Home Neptune 4 Pro',
        'filament_settings_id': 'Neptune 4 - PETG',
        'print_settings_id': 'Headphone hook - PETG 0.20 / 3 walls / 15% gyroid',
        'layer_height': '0.2', 'first_layer_height': '0.2',
        'perimeters': '3', 'fill_density': '15%', 'fill_pattern': 'gyroid',
        'top_solid_layers': '4', 'bottom_solid_layers': '4',
        'support_material': '0', 'support_material_auto': '0',
        'support_material_style': 'snug', 'support_material_pattern': 'rectilinear',
        'support_material_buildplate_only': '0', 'support_material_threshold': '0',
        'support_material_contact_distance': '0.25',
        'support_material_bottom_contact_distance': '0.25',
        'support_material_interface_layers': '3',
        'support_material_interface_spacing': '0.2',
        'support_material_xy_spacing': '0.4',
        'dont_support_bridges': '1', 'bridge_speed': '25',
        'brim_type': 'outer_only', 'brim_width': '3', 'brim_separation': '0.15',
        'gcode_comments': '1', 'binary_gcode': '0',
    }
    config.update(overrides)
    assert config['nozzle_diameter'] == '0.4'
    assert config['filament_type'] == 'PETG' and config['gcode_flavor'] == 'klipper'
    PROFILE.write_text('# Project-local copy of user presets.\n' +
                       '\n'.join(f'{k} = {v}' for k, v in sorted(config.items())) + '\n')
    parts = [MODEL / 'exports' / f'headphone_hook_{p}.stl' for p in ('upper', 'lower')]
    # Explicit positions preserve the chosen flat faces and leave room for both brims.
    ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('', ns)
    tag = lambda n: '{' + ns + '}' + n
    model = ET.Element(tag('model'), unit='millimeter', attrib={'xmlns:slic3rpe': 'http://schemas.slic3r.org/3mf/2017/06'})
    ET.SubElement(model, tag('metadata'), name='slic3rpe:Version3mf').text = '1'
    ET.SubElement(model, tag('metadata'), name='Application').text = 'PrusaSlicer-2.9.4'
    resources = ET.SubElement(model, tag('resources'))
    build = ET.SubElement(model, tag('build'))
    names = ET.Element('config')
    for objid, (part, tx, ty) in enumerate(zip(parts, [52, 124], [56, 68]), 1):
        raw = part.read_bytes()
        count = struct.unpack_from('<I', raw, 80)[0]
        assert len(raw) == 84 + 50 * count
        vertices, index, triangles = [], {}, []
        for face in range(count):
            ids = []
            values = struct.unpack_from('<12fH', raw, 84 + 50 * face)
            for start in (3, 6, 9):
                point = tuple(values[start:start + 3])
                if point not in index:
                    index[point] = len(vertices)
                    vertices.append(point)
                ids.append(index[point])
            triangles.append(ids)
        obj = ET.SubElement(resources, tag('object'), id=str(objid), type='model', name=part.stem)
        mesh = ET.SubElement(obj, tag('mesh'))
        verts = ET.SubElement(mesh, tag('vertices'))
        for x, y, z in vertices:
            ET.SubElement(verts, tag('vertex'), x=str(x), y=str(y), z=str(z))
        faces = ET.SubElement(mesh, tag('triangles'))
        for a, b, c in triangles:
            ET.SubElement(faces, tag('triangle'), v1=str(a), v2=str(b), v3=str(c))
        ET.SubElement(build, tag('item'), objectid=str(objid), transform=f'1 0 0 0 1 0 0 0 1 {tx} {ty} 0')
        meta = ET.SubElement(names, 'object', id=str(objid), instances_count='1')
        ET.SubElement(meta, 'metadata', type='object', key='name', value=part.name)
        volume = ET.SubElement(meta, 'volume', firstid='0', lastid=str(count - 1))
        ET.SubElement(volume, 'metadata', type='volume', key='name', value=part.name)
        ET.SubElement(volume, 'metadata', type='volume', key='volume_type', value='ModelPart')
    template = MODEL / 'slicing/left_petg/holder_left_petg_ready.3mf'
    with zipfile.ZipFile(template) as z:
        files = {name: z.read(name) for name in ('[Content_Types].xml', '_rels/.rels')}
    files['3D/3dmodel.model'] = ET.tostring(model, encoding='utf-8', xml_declaration=True)
    files['Metadata/Slic3r_PE_model.config'] = ET.tostring(names, encoding='utf-8', xml_declaration=True)
    files['Metadata/Slic3r_PE.config'] = ('; Project-local settings\n' + '\n'.join('; ' + line for line in PROFILE.read_text().splitlines() if not line.startswith('#')) + '\n').encode()
    with zipfile.ZipFile(BASE.with_suffix('.3mf'), 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    provenance = {'printer': 'Elegoo Neptune 4 Pro', 'material': 'PETG',
                  'source_profiles': sources, 'overrides': overrides,
                  'parts': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in parts},
                  'orientation': 'Upper: flat assembly underside. Lower: side plane. No rescaling.',
                  'support_reason': 'No supports: rear roof bridges 12.6 mm; horizontal cap recess is 7.5 mm wide. Bridge speed 25 mm/s.',
                  'prior_mount_profile': {'perimeters': 6, 'infill': '40% gyroid'}}
    (ROOT / 'preparation.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
    print('Prepared', BASE.with_suffix('.3mf'))


def finalize():
    gcode = BASE.with_suffix('.gcode')
    text = gcode.read_text()
    begin = text.index('; prusaslicer_config = begin')
    end = text.index('; prusaslicer_config = end', begin)
    config = '; Effective sliced configuration\n' + '\n'.join(text[begin:end].splitlines()[1:]) + '\n'
    for key, value in {'printer_settings_id': 'Neptune 4 Pro',
                       'physical_printer_settings_id': 'Home Neptune 4 Pro'}.items():
        pattern = r'^; ' + re.escape(key) + r' =[^\r\n]*$'
        config = re.sub(pattern, '; ' + key + ' = ' + value, config, flags=re.M) if re.search(pattern, config, re.M) else config + f'; {key} = {value}\n'
    for key, value in [('perimeters', '3'), ('fill_density', '15%'), ('layer_height', '0.2'), ('support_material', '0')]:
        assert f'; {key} = {value}\n' in config
    with zipfile.ZipFile(BASE.with_suffix('.3mf')) as z:
        files = {n: z.read(n) for n in z.namelist()}
    files['Metadata/Slic3r_PE.config'] = config.encode()
    ready = ROOT / 'headphone_hook_petg_ready.3mf'
    with zipfile.ZipFile(ready, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    with zipfile.ZipFile(ready) as z:
        assert z.testzip() is None
    def metric(pattern):
        return re.search(pattern, text, re.M).group(1)
    summary = {
        'project': str(ready), 'gcode': str(gcode),
        'gcode_sha256': hashlib.sha256(gcode.read_bytes()).hexdigest(),
        'printer_settings_id': 'Neptune 4 Pro', 'physical_printer_settings_id': 'Home Neptune 4 Pro',
        'parts': 2, 'perimeters': 3, 'infill': '15% gyroid', 'layer_height_mm': 0.2,
        'top_bottom_solid_layers': 4, 'support_material': False, 'bridge_speed_mm_s': 25,
        'slicer_time_estimate': metric(r'^; estimated printing time \(normal mode\) = (.+)$'),
        'filament_length_mm': float(metric(r'^; filament used \[mm\] = ([\d.]+)')),
        'filament_volume_cm3': float(metric(r'^; filament used \[cm3\] = ([\d.]+)')),
        'filament_mass_g': None, 'reason_mass_unknown': 'Filament density is unspecified in user preset.',
        'nozzle_temperature_C': 230, 'bed_temperature_C': [90, 80],
    }
    (ROOT / 'slice_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    {'prepare': prepare, 'finalize': finalize}[sys.argv[1]]()

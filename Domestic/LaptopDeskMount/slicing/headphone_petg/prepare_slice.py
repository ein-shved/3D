"""Prepare both hook parts and bind the sliced project to local printer presets."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import zipfile

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
        'support_material': '1', 'support_material_auto': '1',
        'support_material_style': 'snug', 'support_material_pattern': 'rectilinear',
        'support_material_buildplate_only': '0', 'support_material_threshold': '0',
        'support_material_contact_distance': '0.25',
        'support_material_bottom_contact_distance': '0.25',
        'support_material_interface_layers': '3',
        'support_material_interface_spacing': '0.2',
        'support_material_xy_spacing': '0.4',
        'dont_support_bridges': '0',
        'brim_type': 'outer_only', 'brim_width': '3', 'brim_separation': '0.15',
        'gcode_comments': '1', 'binary_gcode': '0',
    }
    config.update(overrides)
    assert config['nozzle_diameter'] == '0.4'
    assert config['filament_type'] == 'PETG' and config['gcode_flavor'] == 'klipper'
    PROFILE.write_text('# Project-local copy of user presets.\n' +
                       '\n'.join(f'{k} = {v}' for k, v in sorted(config.items())) + '\n')
    parts = [MODEL / 'exports' / f'headphone_hook_{p}.stl' for p in ('upper', 'lower')]
    subprocess.run(['/run/current-system/sw/bin/prusa-slicer', '--load', str(PROFILE),
                    '--merge', '--center', '112.5,112.5', '--export-3mf',
                    '--output', str(BASE.with_suffix('.3mf')), *map(str, parts)], check=True)
    provenance = {'printer': 'Elegoo Neptune 4 Pro', 'material': 'PETG',
                  'source_profiles': sources, 'overrides': overrides,
                  'parts': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in parts},
                  'orientation': 'Upper: flat assembly underside. Lower: side plane. No rescaling.',
                  'support_reason': 'Accessible support under rear sliding-joint roof; protect fit in PETG.',
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
    for key, value in [('perimeters', '3'), ('fill_density', '15%'), ('layer_height', '0.2'), ('support_material', '1')]:
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
        'top_bottom_solid_layers': 4, 'support_material': True,
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

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const out=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(out,'../..');
const profiles='/home/shved/.config/PrusaSlicer';
const inputs=['print/Neptune 4 Pro.ini','printer/Neptune 4 Pro.ini','filament/Neptune 4 - PETG.ini'];
const config=new Map();
for(const relative of inputs){
  for(const line of fs.readFileSync(path.join(profiles,relative),'utf8').split(/\r?\n/)){
    if(!line.trim()||/^\s*[#;\[]/.test(line))continue;
    const index=line.indexOf('=');
    if(index<0)continue;
    const key=line.slice(0,index).trim();
    if(key==='print_host'||key.startsWith('printhost_'))continue;
    config.set(key,line.slice(index+1).trim());
  }
}
const overrides={
  printer_settings_id:'Elegoo Neptune 4 Pro',
  print_settings_id:'Laptop holder right - PETG 0.20 / 6 walls / 40% gyroid',
  filament_settings_id:'Neptune 4 - PETG',
  layer_height:'0.2',first_layer_height:'0.2',
  perimeters:'6',fill_density:'40%',fill_pattern:'gyroid',
  top_solid_layers:'5',bottom_solid_layers:'5',
  support_material:'1',support_material_auto:'1',support_material_threshold:'0',
  support_material_style:'snug',support_material_pattern:'rectilinear',
  support_material_with_sheath:'0',support_material_buildplate_only:'0',
  support_material_contact_distance:'0.25',support_material_bottom_contact_distance:'0.25',
  support_material_interface_layers:'3',support_material_interface_spacing:'0.2',
  support_material_xy_spacing:'0.4',support_material_speed:'50',
  support_material_interface_speed:'30',
  brim_type:'outer_only',brim_width:'5',brim_separation:'0.15',
  gcode_comments:'1',binary_gcode:'0',
};
for(const [key,value] of Object.entries(overrides))config.set(key,value);
if(config.get('nozzle_diameter')!=='0.4'||config.get('filament_type')!=='PETG'||config.get('gcode_flavor')!=='klipper')throw Error('Unexpected printer or filament profile');
const target=path.join(out,'neptune4pro_petg_right.ini');
fs.writeFileSync(target,'# Project-local snapshot of the user profiles; original presets are unchanged.\n'+[...config].sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>`${k} = ${v}`).join('\n')+'\n');
const model=path.join(root,'exports/holder_right.stl');
const provenance={printer:'Elegoo Neptune 4 Pro',material:'PETG',nozzle_mm:0.4,
  source_profiles:inputs.map(p=>path.join(profiles,p)),overrides,
  source_stl:model,source_stl_sha256:crypto.createHash('sha256').update(fs.readFileSync(model)).digest('hex'),
  orientation:'Original exported orientation: common outboard face on Z=0; no auto-orient or rescale.',
  temperatures:'230 C nozzle; 90 C bed first layer / 80 C later, inherited from user PETG preset.',
  mass:'Unknown: filament_density is 0 in the user preset; report length/volume, not a zero-gram mass.',
  supports:'Automatic snug supports with 0.25 mm contact gap. Local requirement: upper clamp ear after the spacer slot; inspect removal access after slicing.'};
fs.writeFileSync(path.join(out,'preparation.json'),JSON.stringify(provenance,null,2)+'\n');
console.log(JSON.stringify({profile:target,source_stl_sha256:provenance.source_stl_sha256,overrides},null,2));

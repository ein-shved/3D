import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));
const file=path.join(dir,'holder_right_petg.gcode');
const text=fs.readFileSync(file,'utf8');
const chosen=[.2,32,60,98.4];
const panels=chosen.map(z=>({z,segments:[]}));
const bounds={min:[Infinity,Infinity,Infinity],max:[-Infinity,-Infinity,-Infinity]};
const layers=new Set(),supportLayers=new Set();
const extrusion={};
let x=0,y=0,z=0,e=0,absolute=true,absoluteE=true,type='Custom';
let supportMin=Infinity,supportMax=-Infinity,bridgeRun=0,longestBridgePath=0;
for(const line of text.split(/\r?\n/)){
  if(line.startsWith(';TYPE:')){type=line.slice(6);continue;}
  const code=line.split(';',1)[0].trim();
  if(!code)continue;
  const command=code.match(/^[A-Z]\d+/)?.[0];
  if(command==='G90'){absolute=true;continue;}
  if(command==='G91'){absolute=false;continue;}
  if(command==='M82'){absoluteE=true;continue;}
  if(command==='M83'){absoluteE=false;continue;}
  const fields={};
  for(const m of code.matchAll(/([XYZEF])(-?\d+(?:\.\d+)?)/g))fields[m[1]]=Number(m[2]);
  if(command==='G92'){
    if(fields.E!==undefined)e=fields.E;
    if(fields.X!==undefined)x=fields.X;
    if(fields.Y!==undefined)y=fields.Y;
    if(fields.Z!==undefined)z=fields.Z;
    continue;
  }
  if(command!=='G0'&&command!=='G1')continue;
  const nx=fields.X===undefined?x:absolute?fields.X:x+fields.X;
  const ny=fields.Y===undefined?y:absolute?fields.Y:y+fields.Y;
  const nz=fields.Z===undefined?z:absolute?fields.Z:z+fields.Z;
  const ne=fields.E===undefined?e:absoluteE?fields.E:e+fields.E;
  const delta=ne-e,length=Math.hypot(nx-x,ny-y);
  if(delta>0&&length>0&&type!=='Custom'){
    const support=type.startsWith('Support material');
    extrusion[type]=(extrusion[type]??0)+delta;
    for(const point of [[x,y,nz],[nx,ny,nz]])for(let i=0;i<3;i++){
      bounds.min[i]=Math.min(bounds.min[i],point[i]);bounds.max[i]=Math.max(bounds.max[i],point[i]);
    }
    if(support){supportLayers.add(nz.toFixed(3));supportMin=Math.min(supportMin,nz);supportMax=Math.max(supportMax,nz);}
    else if(type!=='Skirt/Brim')layers.add(nz.toFixed(3));
    if(type==='Bridge infill'){bridgeRun+=length;longestBridgePath=Math.max(longestBridgePath,bridgeRun);}else bridgeRun=0;
    for(const panel of panels)if(Math.abs(nz-panel.z)<.015)panel.segments.push([x,y,nx,ny,type]);
  }else if(length>0)bridgeRun=0;
  x=nx;y=ny;z=nz;e=ne;
}
if(bounds.min.some(v=>!Number.isFinite(v)))throw Error('No extrusion paths');
if(bounds.min[0]<0||bounds.min[1]<0||bounds.max[0]>225||bounds.max[1]>225||bounds.max[2]>265)throw Error('Extrusion outside printer envelope');
if(!supportLayers.size)throw Error('Supports missing');
if(Math.abs(bounds.max[2]-113)>.3)throw Error('Unexpected part height');
const area=Math.PI*1.75**2/4;
const review={decision:'keep',material:'PETG',printer:'Elegoo Neptune 4 Pro',
  model_layers:layers.size,support_layer_heights:supportLayers.size,support_z_mm:[supportMin,supportMax],
  extrusion_bounds_mm:bounds,extruded_filament_mm_by_path_type:extrusion,
  support_volume_cm3:Object.entries(extrusion).filter(([k])=>k.startsWith('Support material')).reduce((s,[,v])=>s+v*area/1000,0),
  longest_continuous_bridge_toolpath_mm:longestBridgePath,
  notes:['Bridge path length is not a measurement of its unsupported span.',
    'Review uses actual G-code moves. It confirms support generation, part height and bed fit, not physical fit or strength.',
    'Supports sit in the open clamp region and are removable through the open side. Remove them before mounting.',
    'The one-piece print and its chosen side-on orientation are retained; no model or orientation was changed for slicing.']};
fs.writeFileSync(path.join(dir,'slice_review.json'),JSON.stringify(review,null,2)+'\n');
function colour(t){return t.startsWith('Support')?'#e58a19':t==='Bridge infill'?'#a24cc9':t.includes('perimeter')||t==='Perimeter'?'#176294':t==='Internal infill'?'#65a9ad':'#667a85';}
let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 810"><rect width="1000" height="810" fill="#fff"/><style>text{font:17px sans-serif}</style>';
for(let i=0;i<panels.length;i++){
  const p=panels[i],ox=(i%2)*500+35,oy=Math.floor(i/2)*395+38,scale=1.45;
  svg+=`<text x="${ox}" y="${oy-10}">Z = ${p.z.toFixed(1)} mm</text><rect x="${ox}" y="${oy}" width="326.25" height="326.25" fill="#fafafa" stroke="#aaa"/>`;
  for(const [x,y,nx,ny,t] of p.segments)svg+=`<path d="M${(ox+x*scale).toFixed(2)},${(oy+(225-y)*scale).toFixed(2)}L${(ox+nx*scale).toFixed(2)},${(oy+(225-ny)*scale).toFixed(2)}" fill="none" stroke="${colour(t)}" stroke-width=".65"/>`;
}
svg+='<text x="35" y="798">Blue: perimeters; teal: infill; orange: supports; purple: bridge paths.</text></svg>';
fs.writeFileSync(path.join(dir,'layer_review.svg'),svg);
console.log(JSON.stringify({...review,extruded_filament_mm_by_path_type:undefined},null,2));

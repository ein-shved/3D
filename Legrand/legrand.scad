use <generic.scad>

le_int_length = 71;
le_int_holes_length_out_edge = 60;
le_int_holes_diameter = 4;
le_int_holes_length = le_int_holes_length_out_edge - le_int_holes_diameter;
le_out_length = 82;
le_out_length_twice = 153;
le_out_shift  = le_out_length + (le_out_length_twice -le_out_length * 2);

module le_jamb_once(h=10, thread = false, nut=false, nutLen=0) {
    difference () {
        cube([le_out_length, le_out_length, h], center = true);
        cube([le_int_holes_length - le_int_holes_diameter,
              le_int_holes_length - le_int_holes_diameter, h + 2],
              center = true);
        holeD=le_int_holes_diameter;
        if (nut) {
            holeD=holeD+2;
        }
        translate ([-le_int_holes_length/2, -le_int_holes_length/2, -h/2]) {
            screwHoleDifference(d=holeD, h = h);
        }
        translate ([le_int_holes_length/2, -le_int_holes_length/2, -h/2]) {
            screwHoleDifference(d=holeD, h = h);
        }
        translate ([le_int_holes_length/2, le_int_holes_length/2, -h/2]) {
            screwHoleDifference(d=holeD, h = h);
        }
        translate ([-le_int_holes_length/2, le_int_holes_length/2, -h/2]) {
            screwHoleDifference(d=holeD, h = h);
        }
    }
    translate ([-le_int_holes_length/2, -le_int_holes_length/2, -h/2]) {
        screwHole(d=le_int_holes_diameter, h = h, thread = thread,
                  nut=nut, nutLen=nutLen);
    }
    translate ([le_int_holes_length/2, -le_int_holes_length/2, -h/2]) {
        screwHole(d=le_int_holes_diameter, h = h, thread = thread,
                  nut=nut, nutLen=nutLen);
    }
    translate ([le_int_holes_length/2, le_int_holes_length/2, -h/2]) {
        screwHole(d=le_int_holes_diameter, h = h, thread = thread,
                  nut=nut, nutLen=nutLen);
    }
    translate ([-le_int_holes_length/2, le_int_holes_length/2, -h/2]) {
        screwHole(d=le_int_holes_diameter, h = h, thread = thread,
                  nut=nut, nutLen=nutLen);
    }
}

module le_jamb(h=10, n = 1, thread=false, nut=false, nutLen=0) {
    difference() {
        union() {
            for (i=[0:n-1]) {
                translate([le_out_shift * i, 0]) {
                    le_jamb_once(h=h, thread=thread, nut=nut, nutLen=nutLen);
                }
            }
        }
        union() {
            for (i=[0:n-1]) {
                translate([le_out_shift * i, 0]) {
                    translate ([-le_out_shift/2, 0, -10]) {
                        rotate(v=[0,1,0], a=90) {
                            cylinder(h=20, d=40, center=true);
                        }
                        translate([0,0,-20]) {
                            cube([20,40,h],center=true);
                        }
                    }
                    cylinder(h=h+2, d=70, center=true);
                    if (0) {
                    rotate(v=[1,0,0], a=90) {
                        cylinder(h=100, d=5, center=true);
                    }
                    rotate(v=[0,1,0], a=90) {
                        cylinder(h=100, d=5, center=true);
                    }
                    }
                }
            }
        }
    }
}
translate ([ le_out_length / 2, 0]) {
    le_jamb(h=40, n=2, thread=false);
}

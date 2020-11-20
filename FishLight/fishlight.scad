
aqua_width = 240 - 40;
aqua_height = 315;
aqua_top_border = 25 + 1;
aqua_bottom_border = 25;
aqua_border_step = 2;
aqua_glass_height = aqua_height - aqua_top_border - aqua_bottom_border;

border = 2;

light_tape_width = 14;
light_case_width = light_tape_width + border * 3;

module button_hole(h = 18.5, button = [ 18.8, 6.7 ], center = false) {
    cube ([h, button[0]+0.4, button[1]+0.4], center = center);
}

module dc_hole(h=5.5, m=8, center = false) {
    rotate([0,90,0]) {
        cylinder(h = h, d = m + 0.2, center = center, $fn=60);
    }
}

module aqua_light_cover(l=aqua_glass_height, w=light_case_width,
                        full=false, flat=false, split=false,
                        top = true, bottom=true)
{
    if (split) {
        if (top) {
            difference() {
                aqua_light_cover(l, w, full, flat, false);
                translate([0,0, 0]) {
                    rotate(v=[1,0,0], a=90) {
                        splitter(40, 40, 200, step = 4);
                    }
                }
            }
        }
        if (bottom) {
            translate([0, 5, 0]) {
                difference() {
                    aqua_light_cover(l, w, full, flat, false);
                    translate ([0,-4, 0]) {
                        rotate(v=[1,0,0], a=90) {
                            splitter(40, 40, 200, step = 4, reverse = true);
                        }
                    }
                }
            }
        }
    } else {
    w=w - 2*border - 1;
    b=border - 0.5;
    union() {
        translate([0,0, aqua_top_border/2 + aqua_border_step]) {
            if (flat) {
                cube([w - 2*border + 1.5*b, l, b],
                      center=true);
            } else if (full) {
                translate([0,0, (-aqua_border_step - 2*border )/2]) {
                    cube([w - 2*border, l, aqua_border_step + border + b],
                         center=true);
                }
            } else {
                cube([w - 2*border, l, b], center=true);
            }
            if (!flat) {
            translate([ w/2 - 1.5* border, 0, - aqua_border_step/2 - border]) {
                cube([b, l, aqua_border_step + border + b], center=true);
                translate ([ b, 0, - aqua_border_step/2 - border/2]) {
                    cube([b, l, b], center=true);
                }
            }
            translate([ - w/2 + 1.5* border, 0, - aqua_border_step/2 - border]) {
                cube([b, l, aqua_border_step + border + b], center=true);
                translate ([ - b, 0, - aqua_border_step/2 - border/2]) {
                    cube([b, l, b], center=true);
                }
            }
            }
        }
    }
    }
}

module splitter(l, w, h, step=border*2, reverse=false) {
     union() {
        n = l / step;
        m = w / step;
        translate([0, 0, reverse ? h/2 : -h/2]) {
            cube([l, w, h], center=true);
        }
        translate ([ -l/2, -w/2 ]) {
            for (i = [0:n-1]) {
                for(j = [0:m-1]) {
                    if ( reverse ? (i % 2 != j % 2) : (i % 2 == j % 2)) {
                        translate ([i*step, j*step, - step]) {
                            cube([step + 0.5, step + 0.5, step * 2]);
                        }
                    }
                }
            }
        }
    }
}
module aqua_light_top_base() {
    union () {
        difference() {
            cube([aqua_width, aqua_top_border, aqua_top_border], center=true);
            translate([0,0, 2 * border]) {
                cube([aqua_width - 2 * border, aqua_top_border - 2 * border,
                      aqua_top_border], center = true);
            }
            translate([aqua_width / 2, 0, 0]) {
                button_hole(center = true);
            }
            translate([- aqua_width / 2, 0, 0]) {
                dc_hole(center = true);
            }
            translate ([- aqua_width / 2 + border, 0, aqua_top_border/2 - border]) {
                cube([2*border + 2, aqua_top_border - 2*border, 2 * border + 1], center = true);
            }
        }
        translate ([0, - aqua_top_border/2 + border*1.5, aqua_top_border / 2 - border / 2]) {
            cube([aqua_width, border, border], center=true);
        }
        translate ([0, - aqua_top_border/2 + border*1.5,
                    aqua_top_border / 2 - border / 2 - 2 * border - 0.5]) {
            cube([aqua_width, border, border], center=true);
        }
        translate ([0, aqua_top_border/2 - border*1.5, aqua_top_border / 2 - border / 2]) {
            cube([aqua_width, border, border], center=true);
        }
        translate ([0, aqua_top_border/2 - border*1.5,
                    aqua_top_border / 2 - border / 2 - 2 * border - 0.5]) {
            cube([aqua_width, border, border], center=true);
        }
    }
}

module aqua_light_top(n = 5) {
    tape_holes_edge = 20;
    tape_holes_step = (aqua_width - tape_holes_edge + light_tape_width + border )/n;
    difference() {
        aqua_light_top_base();
        for (i=[0:n-1]) {
            translate([aqua_width / 2 - tape_holes_edge - light_tape_width / 2 - border / 2 - i * tape_holes_step,
                       aqua_top_border/2, 2*border]) {
                cube([light_tape_width + border, 5*border, aqua_top_border],
                     center = true);
            }
        }
    }
    translate ([0, -aqua_top_border/2 + border/2,
                    aqua_top_border/2 + (aqua_border_step + 0.5)/2]) {
        cube([aqua_width/2, border, aqua_border_step + 0.5], center=true);
        translate( [0, border/2, (aqua_border_step + 0.5) / 2 + border / 4 ]) {
            cube([aqua_width/2, border * 2, border/2], center = true);
        }
    }
}

module aqua_light_case() {
    union() {
        difference() {
            cube([light_case_width, aqua_glass_height, aqua_top_border],
                center = true);
            translate([0, - 2 * border, 2 * border]) {
                cube([light_tape_width + border, aqua_glass_height, aqua_top_border],
                     center = true);
            }
            translate ([0, aqua_glass_height / 2, aqua_top_border - border - 0.25]) {
                cube([light_case_width - 4*border, 2*border, 2 * border + 0.5]);
            }
            translate ([0, aqua_glass_height / 2 - border, aqua_top_border/2 - border]) {
                cube([light_case_width - 2*border, 2*border + 2, 2 * border + 1], center = true);
            }
        }
        translate ([ - light_case_width/2 + border*1.5, -2*border, aqua_top_border / 2 - border / 2]) {
            cube([border, aqua_glass_height, border], center=true);
        }
        translate ([ - light_case_width/2 + border*1.5, -2*border,
                    aqua_top_border / 2 - border / 2 - 2 * border - 0.5]) {
            cube([border, aqua_glass_height, border], center=true);
        }
        translate ([light_case_width/2 - border*1.5, -2*border, aqua_top_border / 2 - border / 2]) {
            cube([border, aqua_glass_height, border], center=true);
        }
        translate ([light_case_width/2 - border*1.5, -2*border,
                    aqua_top_border / 2 - border / 2 - 2 * border - 0.5]) {
            cube([border, aqua_glass_height, border], center=true);
        }
    }
}

module aqua_light_case_split(top = true, bottom = true) {
    if (top) {
        difference() {
            aqua_light_case();
            translate([0,0,-3]) {
                rotate(v=[1,0,0], a=90) {
                    splitter(40, 40, 200, step = 8);
                }
            }
        }
    }
    if (bottom) {
        translate([0, 9, 0]) {
            difference() {
                aqua_light_case();
                translate ([0,-8,-3]) {
                    rotate(v=[1,0,0], a=90) {
                        splitter(40, 40, 200, step = 8, reverse = true);
                    }
                }
            }
        }
    }
}

module aqua_light(n=5, split = false, top_split = true, bottom_split = true) {
    tape_holes_edge = 20;
    tape_holes_step = (aqua_width - tape_holes_edge + light_tape_width + border )/n;
    difference () {
        union() {
            aqua_light_top(n=n);
            for (i=[0:n-1]) {
                translate([aqua_width / 2 - tape_holes_edge - light_tape_width / 2 - border / 2 - i * tape_holes_step,
                           aqua_glass_height / 2 + aqua_top_border / 2]) {
                    if(!split) {
                        aqua_light_case();
                    } else {
                        aqua_light_case_split(top_split, bottom_split);
                    }
                }
            }
        }
    }
}

*aqua_light_case_split();

*splitter(100, 100, 100, reverse = true);
*difference () {
    aqua_light_case_split(true, false);
    translate([0, -50 - 40, 0]) cube([40,120,40], center = true);
}
*difference () {
    aqua_light_case_split(false, true);
    translate([0, 50 + 40, 0]) cube([40,120,40], center = true);
}
*difference () {
    aqua_light_cover(full=true);
    translate([0, 50 + 40, 0]) cube([40,120,40], center = true);
    translate([0, -50 - 40, 0]) cube([40,120,40], center = true);
}

* aqua_light(split=false, bottom_split = false, top_split=true);
* aqua_light_case_split(false, true);
* translate([0, 0, -2.6*border]) {
    rotate(v=[0,0,1], a=90) {
        aqua_light_cover(flat=true, l = aqua_width - border,
                         w = aqua_top_border);
    }
}
aqua_light_cover(full=true, split=true, bottom=false);

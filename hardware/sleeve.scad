// Parametric clip-on sleeve holder for the FBG force sensor. CONCEPT ONLY.
// This file describes the same geometry as hardware/generate_sleeve.py.
// The Python version was built and checked (watertight, one body, no overlap with the fibers).
// THIS OPENSCAD FILE WAS NOT RENDERED: OpenSCAD was not available. Check the render before use.
// No strain flexure is modelled. Every dimension is a default to confirm.
// Hardware licence: CERN Open Hardware Licence (variant and header to be added by the author).

shaft_d      = 5.0;   // mm, instrument shaft diameter [TO CONFIRM]; 5 and 10 mm are the common manual sizes
clearance    = 0.2;   // mm, diametral clearance shaft / sleeve
wall         = 2.0;   // mm
length       = 30;    // mm
slit_w       = 1.0;   // mm, clip slit (along +x)
fiber_d      = 0.25;  // mm, coated fiber [TO CONFIRM]; used only for documentation here
groove_w     = 0.6;   // mm, open groove for each strained fiber
groove_d     = 0.5;   // mm, groove depth from the bore
ref_groove_w = 0.9;   // mm, open groove for the reference fiber in its loose capillary
ref_groove_d = 0.8;   // mm, depth of that groove from the bore
capillary_d  = 0.6;   // mm, loose polyimide capillary around the reference fiber [TO CONFIRM]
window_len   = 4;     // mm, adhesive access window length along the shaft
window_w     = 1.5;   // mm, adhesive access window width
window_dz    = 7;     // mm, windows centred at length/2 +/- window_dz
tab_len      = 4;     // mm, tab protrusion beyond the outer surface
tab_t        = 3;     // mm, tab thickness on each side of the slit
tab_z        = 14;    // mm, tab length along the shaft
screw_hole_d = 2.2;   // mm, M2 clearance hole

strained_deg = [60, 180, 300];  // degrees from the slit direction, 120 degrees apart
ref_deg      = 120;             // degrees from the slit direction

$fn = 96;

R_in  = (shaft_d + clearance) / 2;
R_out = R_in + wall;

difference() {
    union() {
        difference() {
            cylinder(r = R_out, h = length);
            translate([0, 0, -1]) cylinder(r = R_in, h = length + 2);
        }
        // clamp tabs on both sides of the slit
        translate([R_in + 0.6,  slit_w / 2,           length / 2 - tab_z / 2])
            cube([R_out + tab_len - (R_in + 0.6), tab_t, tab_z]);
        translate([R_in + 0.6, -slit_w / 2 - tab_t,   length / 2 - tab_z / 2])
            cube([R_out + tab_len - (R_in + 0.6), tab_t, tab_z]);
    }

    // slit
    translate([0, -slit_w / 2, -1]) cube([R_out + tab_len + 2, slit_w, length + 2]);

    // open grooves for the strained fibers (bonded to the shaft)
    for (a = strained_deg)
        rotate([0, 0, a])
            translate([R_in - 0.2, -groove_w / 2, -1])
                cube([groove_d + 0.2, groove_w, length + 2]);

    // open groove for the reference fiber (loose capillary on the shaft, thermal grease, strain-free)
    rotate([0, 0, ref_deg])
        translate([R_in - 0.2, -ref_groove_w / 2, -1])
            cube([ref_groove_d + 0.2, ref_groove_w, length + 2]);

    // adhesive access windows: radial slots through the wall above each strained groove
    for (a = strained_deg)
        for (dz = [-window_dz, window_dz])
            rotate([0, 0, a])
                translate([R_in - 0.2, -window_w / 2, length / 2 + dz - window_len / 2])
                    cube([R_out + 0.5 - (R_in - 0.2), window_w, window_len]);

    // M2 clamp hole through both tabs, along y
    translate([R_out + tab_len / 2 + 0.3, 0, length / 2])
        rotate([90, 0, 0])
            cylinder(d = screw_hole_d, h = 2 * (slit_w / 2 + tab_t) + 2, center = true, $fn = 48);
}

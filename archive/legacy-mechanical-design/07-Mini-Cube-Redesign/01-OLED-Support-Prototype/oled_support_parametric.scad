// =============================================================================
// JARVIS LEGO BOT — FASE D: Prototipo Parametrico Supporto OLED Binghe 1,3"
// Soluzione 2B: Cornice frontale sottile (1,8 mm) + Culla posteriore regolabile
// STATO: PROTOTIPO PARAMETRICO NON VALIDATO (quote provvisorie da confermare)
// =============================================================================

// Seleziona parte da esportare: "assembly", "bezel", "cradle"
part = "assembly";

// --- 1. PARAMETRI PCB (Provvisori: tollera Rev.A 35.4x33.5 e Rev.B 36.0x34.0) ---
pcb_w_min = 35.40;          // [mm] Rev.A (disegno tecnico recente)
pcb_w_max = 36.00;          // [mm] Rev.B (inserzione commerciale)
pcb_h_min = 33.50;          // [mm] Rev.A
pcb_h_max = 34.00;          // [mm] Rev.B
pcb_thickness = 1.60;       // [mm] PROVVISORIO (da confermare con calibro)
rear_smd_protrusion = 2.00; // [mm] PROVVISORIO (componenti SMD retro PCB; NON i 11.30 mm totali!)

// --- 2. PARAMETRI VETRO & AREA ATTIVA ---
glass_w = 34.50;            // [mm]
glass_h = 23.00;            // [mm]
glass_thickness = 1.40;     // [mm] PROVVISORIO
active_w = 29.42;           // [mm] (128 px)
active_h = 14.70;           // [mm] (64 px)
active_top_offset = 7.35;   // [mm] da bordo superiore PCB (asimmetrico -> centro area a 14.70 mm)

// --- 3. PARAMETRI FORI PCB (solo riferimento, NON usati per incastro rigido) ---
hole_pitch_x_min = 30.40;   // [mm] Rev.A
hole_pitch_x_max = 31.00;   // [mm] Rev.B
hole_pitch_y = 28.50;       // [mm] Rev.A
hole_dia = 3.00;            // [mm]

// --- 4. PARAMETRI CORNICE & FINESTRA LEGO (Soluzione 2B) ---
pocket_w = 48.00;           // [mm] Tasca LEGO frontale (6 stud)
pocket_h = 41.60;           // [mm] Tasca LEGO frontale (13 plate: Y_h = 25.6..67.2 mm)
lego_wall_z = 8.00;         // [mm] Spessore parete LEGO (1 stud)
window_w = 32.00;           // [mm] Finestra netta visibile (invariata)
window_h = 19.20;           // [mm] Finestra netta visibile (invariata)
recess_depth = 1.80;        // [mm] Incasso frontale nominale pannello
glass_relief = 0.35;        // [mm] Scarico aria davanti al vetro (nessuna pressione!)

// --- 5. PARAMETRI STAMPA 3D & REGOLAZIONE CULLA ---
print_tol_xy = 0.25;        // [mm] Gioco FDM XY per lato
print_tol_z = 0.20;         // [mm] Gioco Z
slot_travel = 2.50;         // [mm] Corsa di regolazione fine ±2.5 mm su X e Y
screw_dia = 2.70;           // [mm] Foro asola per vite M2.5 (o perno isolato)
flange_w = 6.50;            // [mm] Alette laterali dietro i mattoncini 3004
flange_t = 3.00;            // [mm] Spessore flangia bloccaggio senza colla

// --- 6. PARAMETRI CONNETTORE 4 PIN & FLEX INFERIORE ---
// Nota: 11.30 mm in vista laterale = vetro(1.4) + PCB(1.6) + header/pin(~8.3)
header_w = 14.00;           // [mm] Larghezza scasso header superiore
header_h = 7.00;            // [mm] Altezza libera superiore per pin/cavi
header_protrusion = 8.30;   // [mm] PROVVISORIO (derivato da 11.30 - 1.40 - 1.60)
flex_relief_w = 18.00;      // [mm] Larghezza scasso protezione flex inferiore
flex_relief_d = 3.50;       // [mm] Profondita scarico flex inferiore

// =============================================================================
// MODULO 1: CORNICE FRONTALE SOTTILE (SOLUZIONE 2B)
// Sistema coordinate: X centrato su finestra, Y centrato su finestra, Z=0 fronte
// =============================================================================
module oled_bezel() {
    outer_w = pocket_w - 2 * print_tol_xy;
    outer_h = pocket_h - 2 * print_tol_xy;
    // Tasca LEGO Y_h = 25.6..67.2 mm (centro 46.4 mm -> -1.60 mm rispetto al centro finestra 48.0 mm)
    pocket_y_off = -1.60;
    // Scarico interno dietro il labbro da 1.8 mm per alloggiare vetro + PCB senza pressione
    cavity_w = glass_w + 2 * slot_travel + 1.0; // ~40.5 mm (libero per regolazione +-2.5)
    cavity_h = glass_h + 2 * slot_travel + 1.0; // ~29.0 mm

    difference() {
        union() {
            // Corpo principale inserito nella tasca LEGO 48 x 41.6 mm (Z=0..8 mm)
            translate([-outer_w/2, pocket_y_off - outer_h/2, 0])
                cube([outer_w, outer_h, lego_wall_z]);

            // Flange laterali posteriori per bloccaggio meccanico dietro 3004 (Z=8..11 mm)
            for (sx = [-1, 1]) {
                translate([sx * (outer_w/2) - (sx > 0 ? 0 : flange_w), pocket_y_off - outer_h/2 + 3.5, lego_wall_z])
                    cube([flange_w, outer_h - 7.0, flange_t]);
            }
        }

        // 1. Apertura finestra netta frontale (32.0 x 19.2 mm)
        translate([-window_w/2, -window_h/2, -0.5])
            cube([window_w, window_h, recess_depth + 1.0]);

        // 2. Cavità posteriore libera per vetro (zero pressione!) e regolazione +-2.5 mm
        translate([-cavity_w/2, -cavity_h/2, recess_depth + glass_relief])
            cube([cavity_w, cavity_h, lego_wall_z + flange_t]);

        // 3. Fori di fissaggio/accoppiamento per viti M2.5 della culla sulle flange laterali
        for (sx = [-1, 1], sy = [-1, 1]) {
            translate([sx * (outer_w/2 + flange_w/2), sy * 10.0, lego_wall_z - 1.0])
                cylinder(h = flange_t + 2.0, d = 2.2, $fn = 24);
        }
    }
}

// =============================================================================
// MODULO 2: CULLA POSTERIORE REGOLABILE (±2.5 mm su X e Y, tollera 35.4..36.0)
// =============================================================================
module oled_cradle() {
    // Tasca dimensionata su pcb_w_max / pcb_h_max + tolleranza stampa
    pocket_pcb_w = pcb_w_max + 2 * print_tol_xy;
    pocket_pcb_h = pcb_h_max + 2 * print_tol_xy;
    cradle_w = pocket_pcb_w + 6.0; // ~42.5 mm
    cradle_h = pocket_pcb_h + 5.0; // ~39.5 mm
    cradle_z0 = recess_depth + glass_relief + glass_thickness; // ~3.55 mm
    cradle_depth = pcb_thickness + rear_smd_protrusion + 2.5;  // ~6.1 mm

    // Offset verticale centro PCB rispetto a centro finestra (7.35 mm + 14.70/2 = 14.70 mm da top)
    pcb_y_offset = (pcb_h_max / 2) - (active_top_offset + active_h / 2); // -2.30 mm

    translate([0, pcb_y_offset, cradle_z0])
    difference() {
        union() {
            // Telaio culla perimetrale
            translate([-cradle_w/2, -cradle_h/2, 0])
                cube([cradle_w, cradle_h, cradle_depth]);

            // Alette asolate laterali per aggancio alle flange della cornice
            for (sx = [-1, 1]) {
                ax = (sx > 0) ? (cradle_w/2 - 1.0) : (-cradle_w/2 - 11.0);
                translate([ax, -16.0, cradle_depth - 2.6])
                    cube([12.0, 32.0, 2.6]);
            }
        }

        // 1. Alloggiamento PCB (tollera 35.4..36.0 x 33.5..34.0 senza forzare)
        translate([-pocket_pcb_w/2, -pocket_pcb_h/2, -0.5])
            cube([pocket_pcb_w, pocket_pcb_h, pcb_thickness + 0.8]);

        // 2. Finestra posteriore aperta per componenti SMD, dissipazione e zero cortocircuiti
        translate([-(pocket_pcb_w - 5.0)/2, -(pocket_pcb_h - 5.0)/2, -0.5])
            cube([pocket_pcb_w - 5.0, pocket_pcb_h - 5.0, cradle_depth + 1.0]);

        // 3. Scasso aperto superiore per connettore I2C 4 pin
        translate([-header_w/2, pocket_pcb_h/2 - 4.0, -0.5])
            cube([header_w, header_h + 5.0, cradle_depth + 1.0]);

        // 4. Scarico inferiore aperto per protezione nastro flex FPC
        translate([-flex_relief_w/2, -cradle_h/2 - 0.5, -0.5])
            cube([flex_relief_w, flex_relief_d + 2.5, cradle_depth + 1.0]);

        // 5. Finestre asolate di regolazione indipendente ±2.5 mm su X e Y (con rondella M2.5)
        for (sx = [-1, 1], sy = [-1, 1]) {
            cx = sx * ((pocket_w - 2*print_tol_xy)/2 + flange_w/2);
            cy = sy * 10.0 - pcb_y_offset;
            translate([cx - slot_travel - screw_dia/2, cy - slot_travel - screw_dia/2, -1])
                cube([2*slot_travel + screw_dia, 2*slot_travel + screw_dia, cradle_depth + 2]);
        }
    }
}

if (part == "bezel") {
    oled_bezel();
} else if (part == "cradle") {
    oled_cradle();
} else {
    color("#1e2229") oled_bezel();
    color("#607d8b") oled_cradle();
}

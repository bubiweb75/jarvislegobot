import os, struct, math

proto_dir = r"c:\Users\bcava\Desktop\Progetti\JARVIS LEGO BOT\03-Mechanical-Design\07-Mini-Cube-Redesign\01-OLED-Support-Prototype"
stl_dir = os.path.join(proto_dir, "stl_prototipi_non_validati")
img_dir = os.path.join(proto_dir, "images")
os.makedirs(stl_dir, exist_ok=True)
os.makedirs(img_dir, exist_ok=True)

# ==============================================================================
# 1. WATER-TIGHT BINARY STL HELPER (from exact non-overlapping axis-aligned boxes)
# ==============================================================================
def box_tris(x0, y0, z0, x1, y1, z1):
    # Returns 12 triangles (outward normals) for box [x0..x1, y0..y1, z0..z1]
    v = [
        (x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0), # bottom z0: 0,1,2,3
        (x0,y0,z1), (x1,y0,z1), (x1,y1,z1), (x0,y1,z1), # top z1:    4,5,6,7
    ]
    faces = [
        (0,2,1), (0,3,2), # -Z
        (4,5,6), (4,6,7), # +Z
        (0,1,5), (0,5,4), # -Y
        (2,3,7), (2,7,6), # +Y
        (0,4,7), (0,7,3), # -X
        (1,2,6), (1,6,5), # +X
    ]
    return [(v[a], v[b], v[c]) for a,b,c in faces]

def write_binary_stl(path, header_txt, boxes):
    tris = []
    for b in boxes:
        tris.extend(box_tris(*b))
    with open(path, "wb") as f:
        hdr = header_txt.encode("ascii", "ignore")[:80].ljust(80, b" ")
        f.write(hdr)
        f.write(struct.pack("<I", len(tris)))
        for p1, p2, p3 in tris:
            ux, uy, uz = p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2]
            vx, vy, vz = p3[0]-p1[0], p3[1]-p1[1], p3[2]-p1[2]
            nx, ny, nz = uy*vz - uz*vy, uz*vx - ux*vz, ux*vy - uy*vx
            ln = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
            f.write(struct.pack("<3f3f3f3fH", nx/ln, ny/ln, nz/ln, *p1, *p2, *p3, 0))

# Build Cornice 2B boxes (window at X=0, Y=0; pocket shifted -1.60 mm in Y to match Y_h=25.6..67.2 mm)
ow, oh = 47.5/2.0, 41.1/2.0
pyo = -1.60
ww, wh = 32.0/2.0, 19.2/2.0
cw, ch = 40.5/2.0, 29.0/2.0
bezel_boxes = [
    # Front 1.8 mm lip around 32.0 x 19.2 mm window:
    (-ow, pyo-oh, 0.0,  ow, -wh, 1.8),   # bottom lip
    (-ow,  wh,    0.0,  ow, pyo+oh, 1.8),# top lip
    (-ow, -wh,    0.0, -ww,  wh, 1.8),   # left lip
    ( ww, -wh,    0.0,  ow,  wh, 1.8),   # right lip
    # Main Z=1.8..8.0 mm body around 40.5 x 29.0 mm cavity:
    (-ow, pyo-oh, 1.8,  ow, -ch, 8.0),   # bottom wall
    (-ow,  ch,    1.8,  ow, pyo+oh, 8.0),# top wall
    (-ow, -ch,    1.8, -cw,  ch, 8.0),   # left wall
    ( cw, -ch,    1.8,  ow,  ch, 8.0),   # right wall
    # Rear lateral clamping flanges behind 3004 (Z=8.0..11.0 mm):
    (-ow-6.5, pyo-oh+3.5, 8.0, -ow, pyo+oh-3.5, 11.0),
    ( ow,     pyo-oh+3.5, 8.0,  ow+6.5, pyo+oh-3.5, 11.0),
]
write_binary_stl(
    os.path.join(stl_dir, "PROTOTIPO_NON_VALIDATO_cornice_2B.stl"),
    "PROTOTIPO_NON_VALIDATO Cornice 2B JARVIS Mini Cubo",
    bezel_boxes
)

# Build Culla Regolabile boxes (Z=3.55..9.65 mm, tolerates 35.4..36.0 x 33.5..34.0)
# Centered around PCB center (Y_offset = -2.30 mm relative to window center)
cz0, cz1 = 3.55, 9.65
pw, ph = 36.5/2.0, 34.5/2.0
rw, rh = pw + 3.0, ph + 2.5
yo = -2.30
cradle_boxes = [
    # Left & Right perimeter rails:
    (-rw, yo-rh, cz0, -pw, yo+rh, cz1),
    ( pw, yo-rh, cz0,  rw, yo+rh, cz1),
    # Top rails (leaving 14 mm central cutout for 4-pin header):
    (-pw, yo+ph, cz0, -7.0, yo+rh, cz1),
    ( 7.0, yo+ph, cz0,  pw,  yo+rh, cz1),
    # Bottom rails (leaving 18 mm central cutout for FPC flex relief):
    (-pw, yo-rh, cz0, -9.0, yo-ph, cz1),
    ( 9.0, yo-rh, cz0,  pw,  yo-ph, cz1),
    # Rear retention lip (2.5 mm behind PCB, keeping central SMD window open):
    (-pw, yo-ph, cz0+3.6, -pw+2.5, yo+ph, cz1),
    ( pw-2.5, yo-ph, cz0+3.6, pw, yo+ph, cz1),
    # Slotted lateral mounting ears:
    (-rw-11.0, yo-16.0, cz1-2.6, -rw, yo+16.0, cz1),
    ( rw,      yo-16.0, cz1-2.6,  rw+11.0, yo+16.0, cz1),
]
write_binary_stl(
    os.path.join(stl_dir, "PROTOTIPO_NON_VALIDATO_culla_regolabile.stl"),
    "PROTOTIPO_NON_VALIDATO Culla Regolabile JARVIS Mini Cubo",
    cradle_boxes
)

# ==============================================================================
# 2. EXACT 3D INTERFERENCE CHECK IN MINI CUBE WORLD COORDS (mm)
# ==============================================================================
# Window center in Mini Cube: X = 40.0, Y_h = 48.0, Z = 0.0
def to_world_boxes(local_boxes):
    return [(40.0+x0, 48.0+y0, z0, 40.0+x1, 48.0+y1, z1) for x0,y0,z0,x1,y1,z1 in local_boxes]

proto_world = to_world_boxes(bezel_boxes) + to_world_boxes(cradle_boxes)
# Add OLED glass + PCB + Header (11.30 mm total side-view breakdown)
oled_parts_world = [
    ("OLED_Glass_34.5x23x1.4", 40-17.25, 48-11.5, 2.15, 40+17.25, 48+11.5, 3.55),
    ("OLED_PCB_36x34x1.6", 40-18.0, 48-2.3-17.0, 3.55, 40+18.0, 48-2.3+17.0, 5.15),
    ("OLED_Header_4pin_8.3mm", 40-6.0, 58.2, 5.15, 40+6.0, 62.7, 13.45),
]
elec_mini_mm = [
    ("Speaker_AS03604AR", 22.0, 80.8, 22.0, 58.0, 89.6, 58.0),
    ("ESP32_S3_LayoutC", 46.0, 16.0, 50.0, 71.4, 79.0, 72.0),
    ("MAX98357A_plus_C1", 12.0, 10.0, 20.8, 34.0, 30.0, 40.8),
    ("INMP441_UpperRight", 64.0, 73.6, 14.0, 71.2, 85.6, 30.0),
    ("Breakout_USBC_5V", 18.0, 10.0, 54.0, 36.0, 18.0, 71.2),
    ("LEGO_Accenti_4070_SX", 8.0, 19.2, 4.0, 16.0, 28.8, 12.0),
    ("LEGO_Accenti_4070_DX", 64.0, 19.2, 4.0, 72.0, 28.8, 12.0),
    ("LEGO_Front_Pocket_Wall_L7", 0.0, 67.2, 0.0, 80.0, 89.6, 8.0),
    ("LEGO_Front_Pocket_L2_mid", 16.0, 19.2, 0.0, 64.0, 25.6, 8.0),
]

print("=== 3D SUB-BOX INTERFERENCE CHECK (Prototype + OLED vs Mini Cube) ===")
all_proto = [("Proto_Part", *b) for b in proto_world] + oled_parts_world
hits = 0
for pname, px0, py0, pz0, px1, py1, pz1 in all_proto:
    for ename, ex0, ey0, ez0, ex1, ey1, ez1 in elec_mini_mm:
        ox = min(px1, ex1) - max(px0, ex0)
        oy = min(py1, ey1) - max(py0, ey0)
        oz = min(pz1, ez1) - max(pz0, ez0)
        if ox > 0.01 and oy > 0.01 and oz > 0.01:
            print(f"  HIT: {pname} vs {ename} ov=({ox:.2f}, {oy:.2f}, {oz:.2f}) mm")
            hits += 1
print(f"Total 3D sub-box hits: {hits}")

# ==============================================================================
# 3. RENDER 3 TECHNICAL SVG VIEWS
# ==============================================================================
# 3A: Front View with simulated 128x64 white eyes + 48x41.6 mm matte-black bezel
sc = 5.0
ox, oy = 60, 65
def fx(x): return ox + x * sc
def fy(yh): return oy + (96.0 - yh) * sc

svg_front = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600" style="background:#f8f9fa">
<text x="400" y="28" font-family="Segoe UI,Arial" font-size="16" font-weight="bold" text-anchor="middle" fill="#111">FASE D — Vista Frontale con Cornice 3D Sottile (Soluzione 2B) e Occhi 128×64</text>
<rect x="{fx(0)}" y="{fy(96)}" width="{80*sc}" height="{96*sc}" fill="#20242b" stroke="#0b0d10" stroke-width="1.5"/>
<rect x="{fx(0)}" y="{fy(96)}" width="{80*sc}" height="{6.4*sc}" fill="#2b303a" stroke="#0b0d10"/>
<!-- Accenti Azure incassati -->
<rect x="{fx(8.5)}" y="{fy(28.0)}" width="{7*sc}" height="{7.2*sc}" fill="#36aebf" stroke="#0b0d10"/>
<rect x="{fx(64.5)}" y="{fy(28.0)}" width="{7*sc}" height="{7.2*sc}" fill="#36aebf" stroke="#0b0d10"/>
<!-- Tasca LEGO 48x41.6 mm + Cornice 3D nera opaca a filo -->
<rect x="{fx(16)}" y="{fy(67.2)}" width="{48*sc}" height="{41.6*sc}" fill="#1a1d24" stroke="#455a64" stroke-width="1.2" stroke-dasharray="4,2"/>
<!-- Finestra netta 32.0 x 19.2 mm (incasso 1.8 mm) -->
<rect x="{fx(24)}" y="{fy(57.6)}" width="{32*sc}" height="{19.2*sc}" fill="#050608" stroke="#607d8b" stroke-width="1.2"/>
<!-- Area attiva 29.42 x 14.70 mm + Occhi bianchi -->
<rect x="{fx(40-10.0)}" y="{fy(48+4.6)}" width="{7.2*sc}" height="{9.2*sc}" rx="{2.4*sc}" fill="#ffffff"/>
<rect x="{fx(40+2.8)}" y="{fy(48+4.6)}" width="{7.2*sc}" height="{9.2*sc}" rx="{2.4*sc}" fill="#ffffff"/>

<rect x="490" y="65" width="280" height="480" rx="8" fill="#eef1f4" stroke="#cbd2d9"/>
<text x="630" y="92" font-family="Segoe UI,Arial" font-size="13" font-weight="bold" text-anchor="middle" fill="#111">Riepilogo Frontale Soluzione 2B</text>
<text x="508" y="122" font-family="Segoe UI,Arial" font-size="11" fill="#333">• Corpo LEGO invariato: 80 × 80 × 96 mm</text>
<text x="508" y="142" font-family="Segoe UI,Arial" font-size="11" fill="#333">• Tasca frontale LEGO: 48,0 × 41,6 mm</text>
<text x="508" y="162" font-family="Segoe UI,Arial" font-size="11" fill="#333">• Cornice 3D nera opaca a filo Z=0</text>
<text x="508" y="182" font-family="Segoe UI,Arial" font-size="11" fill="#333">• Finestra visibile: 32,0 × 19,2 mm</text>
<text x="508" y="202" font-family="Segoe UI,Arial" font-size="11" fill="#333">• Incasso nominale: 1,8 mm (±35,6° O)</text>
<text x="508" y="228" font-family="Segoe UI,Arial" font-size="11" font-weight="bold" fill="#01579b">• Display elettronico (non LEGO):</text>
<text x="508" y="246" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">  - Area attiva 29,42 × 14,70 mm (128×64)</text>
<text x="508" y="264" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">  - Offset asimmetrico: 7,35 mm da top PCB</text>
<text x="508" y="282" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">  - Tollera PCB 35,4×33,5 e 36,0×34,0</text>
<text x="508" y="312" font-family="Segoe UI,Arial" font-size="11" font-weight="bold" fill="#b71c1c">• Verifiche aperte:</text>
<text x="508" y="330" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">  - Controller SH1106 vs SSD1106</text>
<text x="508" y="348" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">  - Quota 11,30 mm vista laterale</text>
<text x="508" y="366" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">  - Interasse fori (30,4×28,5 vs 31)</text>
</svg>'''
with open(os.path.join(img_dir, "01_vista_frontale_occhi_oled.svg"), "w", encoding="utf-8") as f:
    f.write(svg_front)

# 3B: Dimensioned Vertical Section (Z vs Y_h)
sc2 = 5.2
sx0, sy0 = 70, 70
def pz(z): return sx0 + z * sc2
def py(yh): return sy0 + (96.0 - yh) * sc2

svg_sec = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="590" viewBox="0 0 960 590" style="background:#f8f9fa">
<text x="480" y="28" font-family="Segoe UI,Arial" font-size="16" font-weight="bold" text-anchor="middle" fill="#111">FASE D — Sezione Verticale Quotata del Display Installato (Soluzione 2B)</text>
<rect x="{pz(0)}" y="{py(96)}" width="{80*sc2}" height="{96*sc2}" fill="#ffffff" stroke="#9aa5b1"/>
<!-- Parete frontale LEGO sopra (L7-8: 67.2..89.6) e sotto (L0-2: 0..25.6) -->
<rect x="{pz(0)}" y="{py(25.6)}" width="{8*sc2}" height="{25.6*sc2}" fill="#20242b"/>
<rect x="{pz(0)}" y="{py(89.6)}" width="{8*sc2}" height="{22.4*sc2}" fill="#20242b"/>
<rect x="{pz(0)}" y="{py(96.0)}" width="{80*sc2}" height="{6.4*sc2}" fill="#2b303a" fill-opacity="0.7"/>
<rect x="{pz(72)}" y="{py(89.6)}" width="{8*sc2}" height="{89.6*sc2}" fill="#20242b"/>

<!-- Cornice 3D (Z=0..8, Y_h=25.6..67.2) con finestra 38.4..57.6 e incasso 1.8 mm -->
<rect x="{pz(0)}" y="{py(38.4)}" width="{8*sc2}" height="{12.8*sc2}" fill="#37474f"/>
<rect x="{pz(0)}" y="{py(67.2)}" width="{8*sc2}" height="{9.6*sc2}" fill="#37474f"/>

<!-- Vetro OLED (Z=2.15..3.55, Y_h=36.5..59.5) + PCB (Z=3.55..5.15, Y_h=28.7..62.7) -->
<rect x="{pz(2.15)}" y="{py(59.5)}" width="{1.4*sc2}" height="{23.0*sc2}" fill="#ff9800"/>
<rect x="{pz(3.55)}" y="{py(62.7)}" width="{1.6*sc2}" height="{34.0*sc2}" fill="#1565c0"/>
<!-- Header 4 pin + cavo (Z=5.15..13.45, Y_h=58..74) -->
<rect x="{pz(5.15)}" y="{py(73.5)}" width="{8.3*sc2}" height="{11.0*sc2}" fill="#ffd54f" stroke="#f57f17"/>
<!-- Culla 3D (Z=5.15..9.65) con scarico flex inferiore e apertura SMD -->
<rect x="{pz(5.15)}" y="{py(65.0)}" width="{4.5*sc2}" height="{2.3*sc2}" fill="#78909c"/>
<rect x="{pz(5.15)}" y="{py(28.7)}" width="{4.5*sc2}" height="{2.5*sc2}" fill="#78909c"/>

<!-- Elettronica esistente -->
<rect x="{pz(22)}" y="{py(89.6)}" width="{36*sc2}" height="{8.8*sc2}" fill="#cfd8dc" stroke="#455a64"/>
<text x="{pz(40)}" y="{py(84)}" font-family="Segoe UI,Arial" font-size="9.5" text-anchor="middle" fill="#111">AS03604AR (Z=22..58)</text>
<rect x="{pz(20.8)}" y="{py(30)}" width="{20*sc2}" height="{20*sc2}" fill="#b3e5fc" stroke="#0277bd"/>
<text x="{pz(30.8)}" y="{py(19)}" font-family="Segoe UI,Arial" font-size="9.5" text-anchor="middle" fill="#01579b">MAX98357A (Z=20.8..40.8)</text>
<rect x="{pz(50)}" y="{py(79)}" width="{21.4*sc2}" height="{63*sc2}" fill="#c8e6c9" stroke="#2e7d32"/>
<text x="{pz(60.7)}" y="{py(48)}" font-family="Segoe UI,Arial" font-size="9.5" text-anchor="middle" fill="#1b5e20">ESP32-S3 (Z=50..71.4)</text>

<!-- Cavi I2C -->
<path d="M {pz(13.5)} {py(69)} C {pz(24)} {py(74)}, {pz(38)} {py(73)}, {pz(50)} {py(65)}" fill="none" stroke="#d32f2f" stroke-width="2" stroke-dasharray="5,2"/>

<!-- Annotazioni a destra -->
<rect x="520" y="70" width="415" height="495" rx="8" fill="#eef1f4" stroke="#cbd2d9"/>
<text x="727" y="96" font-family="Segoe UI,Arial" font-size="13" font-weight="bold" text-anchor="middle" fill="#111">Analisi Quote &amp; Scomposizione 11,30 mm</text>
<text x="538" y="126" font-family="Segoe UI,Arial" font-size="11" font-weight="bold" fill="#111">1. Scomposizione quota laterale 11,30 mm (provvisoria):</text>
<text x="538" y="145" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• Vetro OLED: ~1,40 mm (Z = 2,15..3,55 mm)</text>
<text x="538" y="163" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• PCB: ~1,60 mm (Z = 3,55..5,15 mm)</text>
<text x="538" y="181" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• Header 4 pin + distanziale: ~8,30 mm (Z = 5,15..13,45)</text>
<text x="538" y="199" font-family="Segoe UI,Arial" font-size="10.5" fill="#b71c1c">→ 11,30 mm NON è lo spessore del solo vetro/PCB!</text>

<text x="538" y="232" font-family="Segoe UI,Arial" font-size="11" font-weight="bold" fill="#111">2. Asimmetria area attiva (7,35 mm da bordo sup. PCB):</text>
<text x="538" y="251" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• Centro area attiva a 14,70 mm dal top PCB</text>
<text x="538" y="269" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• Top PCB a Y_h = 62,70 mm; Fondo PCB a 28,7..29,2 mm</text>
<text x="538" y="287" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• Scarico inferiore aperto per flex FPC (M)</text>

<text x="538" y="320" font-family="Segoe UI,Arial" font-size="11" font-weight="bold" fill="#111">3. Margini interni verificati (0 collisioni 3D):</text>
<text x="538" y="339" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• Davanti ad AS03604AR (Z=22): 8,55 mm liberi</text>
<text x="538" y="357" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• Davanti a MAX98357A (Z=20,8): 11,15 mm liberi</text>
<text x="538" y="375" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• Davanti a ESP32-S3 (Z=50): 36,55 mm liberi</text>

<text x="538" y="408" font-family="Segoe UI,Arial" font-size="11" font-weight="bold" fill="#111">4. Modifica tasca LEGO frontale (solo in Passaggio B):</text>
<text x="538" y="427" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• L3..L6: pilastri 3004 (1×2) ai lati -> apertura 48 mm</text>
<text x="538" y="445" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• L2 centro (X=16..64): 2 plate (3666) -> Y_h=25,6 mm</text>
<text x="538" y="463" font-family="Segoe UI,Arial" font-size="10.5" fill="#333">• Risultato: tasca 48,0 × 41,6 mm, 0 coll. con 4070+3070b</text>
</svg>'''
with open(os.path.join(img_dir, "02_sezione_quotata_display_installato.svg"), "w", encoding="utf-8") as f:
    f.write(svg_sec)

# 3C: Exploded Assembly View (Left-to-Right schematic exploded view)
svg_exp = '''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="460" viewBox="0 0 960 460" style="background:#f8f9fa">
<text x="480" y="28" font-family="Segoe UI,Arial" font-size="16" font-weight="bold" text-anchor="middle" fill="#111">FASE D — Vista Esplosa del Sistema di Montaggio OLED (Senza Colla)</text>

<!-- Step 1: Parete LEGO -->
<rect x="45" y="90" width="130" height="240" rx="6" fill="#20242b" stroke="#0b0d10" stroke-width="1.5"/>
<rect x="65" y="135" width="90" height="145" fill="#f8f9fa" stroke="#607d8b" stroke-dasharray="4,2"/>
<text x="110" y="210" font-family="Segoe UI,Arial" font-size="11" font-weight="bold" text-anchor="middle" fill="#333">Tasca LEGO</text>
<text x="110" y="226" font-family="Segoe UI,Arial" font-size="10" text-anchor="middle" fill="#555">48,0 × 41,6 mm</text>
<text x="110" y="355" font-family="Segoe UI,Arial" font-size="11.5" font-weight="bold" text-anchor="middle" fill="#111">1. Frontale LEGO</text>

<!-- Arrow -->
<text x="195" y="215" font-family="Segoe UI,Arial" font-size="22" font-weight="bold" text-anchor="middle" fill="#607d8b">←</text>

<!-- Step 2: Cornice 3D 2B -->
<rect x="220" y="110" width="140" height="200" rx="4" fill="#37474f" stroke="#111" stroke-width="1.5"/>
<rect x="242" y="165" width="96" height="86" fill="#050608" stroke="#90a4ae"/>
<rect x="206" y="125" width="14" height="170" fill="#546e7a" stroke="#111"/>
<rect x="360" y="125" width="14" height="170" fill="#546e7a" stroke="#111"/>
<text x="290" y="212" font-family="Segoe UI,Arial" font-size="10" text-anchor="middle" fill="#fff">32 × 19,2 mm</text>
<text x="290" y="355" font-family="Segoe UI,Arial" font-size="11.5" font-weight="bold" text-anchor="middle" fill="#111">2. Cornice 3D (1,8 mm)</text>
<text x="290" y="372" font-family="Segoe UI,Arial" font-size="9.5" text-anchor="middle" fill="#555">+ flange laterali bloccaggio</text>

<text x="392" y="215" font-family="Segoe UI,Arial" font-size="22" font-weight="bold" text-anchor="middle" fill="#607d8b">←</text>

<!-- Step 3: OLED Binghe -->
<rect x="420" y="130" width="120" height="160" rx="4" fill="#1565c0" stroke="#0d47a1" stroke-width="1.5"/>
<rect x="428" y="155" width="104" height="90" fill="#212121" stroke="#ff9800"/>
<rect x="455" y="134" width="50" height="12" fill="#ffd54f"/>
<rect x="455" y="250" width="50" height="28" fill="#d84315"/>
<text x="480" y="205" font-family="Segoe UI,Arial" font-size="10" text-anchor="middle" fill="#fff">OLED 1,3"</text>
<text x="480" y="355" font-family="Segoe UI,Arial" font-size="11.5" font-weight="bold" text-anchor="middle" fill="#111">3. Modulo OLED</text>
<text x="480" y="372" font-family="Segoe UI,Arial" font-size="9.5" text-anchor="middle" fill="#555">35,4×33,5 o 36×34 mm</text>

<text x="562" y="215" font-family="Segoe UI,Arial" font-size="22" font-weight="bold" text-anchor="middle" fill="#607d8b">←</text>

<!-- Step 4: Culla Regolabile -->
<rect x="590" y="115" width="145" height="190" rx="4" fill="#78909c" stroke="#263238" stroke-width="1.5"/>
<rect x="612" y="140" width="101" height="135" fill="#f8f9fa" stroke="#37474f" stroke-dasharray="3,2"/>
<rect x="572" y="145" width="18" height="130" fill="#90a4ae" stroke="#263238"/>
<rect x="735" y="145" width="18" height="130" fill="#90a4ae" stroke="#263238"/>
<text x="662" y="205" font-family="Segoe UI,Arial" font-size="10" font-weight="bold" text-anchor="middle" fill="#263238">Asole ±2,5 mm</text>
<text x="662" y="220" font-family="Segoe UI,Arial" font-size="9" text-anchor="middle" fill="#444">Scasso sup. + scarico flex</text>
<text x="662" y="355" font-family="Segoe UI,Arial" font-size="11.5" font-weight="bold" text-anchor="middle" fill="#111">4. Culla Regolabile</text>
<text x="662" y="372" font-family="Segoe UI,Arial" font-size="9.5" text-anchor="middle" fill="#555">4× viti M2,5 + rondelle</text>

<text x="772" y="215" font-family="Segoe UI,Arial" font-size="22" font-weight="bold" text-anchor="middle" fill="#607d8b">←</text>

<!-- Step 5: Sportello Posteriore -->
<rect x="795" y="95" width="120" height="230" rx="6" fill="#20242b" stroke="#0b0d10" stroke-width="1.5"/>
<rect x="838" y="195" width="34" height="22" fill="#6b727d" stroke="#111"/>
<text x="855" y="355" font-family="Segoe UI,Arial" font-size="11.5" font-weight="bold" text-anchor="middle" fill="#111">5. Sportello 3036</text>
<text x="855" y="372" font-family="Segoe UI,Arial" font-size="9.5" text-anchor="middle" fill="#555">Accesso 48×67,2 mm</text>

<rect x="45" y="395" width="870" height="48" rx="6" fill="#eef1f4" stroke="#cbd2d9"/>
<text x="65" y="423" font-family="Segoe UI,Arial" font-size="11" fill="#111">Montaggio e centraggio da sportello posteriore: serrando la culla sulle flange della cornice, il sandwich blocca l'intero gruppo alla parete LEGO senza colle.</text>
</svg>'''
with open(os.path.join(img_dir, "03_vista_esplosa_montaggio.svg"), "w", encoding="utf-8") as f:
    f.write(svg_exp)

print("Generated STLs and SVGs in:", proto_dir)

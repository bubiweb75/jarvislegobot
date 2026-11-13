# Elaborato A – Progetto Visivo (Design Compatto Definitivo)

**Progetto:** JARVIS LEGO BOT – FASE 3 (Verifica Tecnica Definitiva)  
**Architettura:** Corpo **Monoblocco Compatto (Modulo A)** + Base Fissa da Scrivania (**Modulo B1**) / Futura Base Mobile 2WD+Caster (**Modulo B2**)  
**Palette (verificata in `csv/colors.csv`):** Nero (`Black`, ID `0`), Grigio Scuro (`Dark Bluish Gray`, ID `72`), dettagli Azzurro/Ciano (`Medium Azure`, ID `322` / `Trans-Light Blue`, ID `41`)

---

## 1. Dimensioni Definitive Mantenute

- **1 stud LEGO = 8,0 mm | 1 brick = 9,6 mm | 1 plate = 3,2 mm**

| Modulo | Stud (X × Y) | Millimetri (X × Y × Z) | Centimetri | Note |
|---|---|---|---|---|
| **Modulo A (Corpo Monoblocco)** | **10 × 10 stud** | `80 × 80 × 144 mm` *(15 brick)* | **8,0 × 8,0 × 14,4 cm** | Vano interno utile: `64 × 64 × ~128 mm` |
| **Modulo B1 (Base Fissa)** | **12 × 11 stud** | `96 × 88 × 19,2 mm` *(2 brick)* | **9,6 × 8,8 × 1,9 cm** | Nessun motore, nessuna batteria |
| **Robot Completo su B1** | **12 × 11 stud** | `96 × 88 × 163,2 mm` | **~16,3 cm** | Compatto da scrivania |
| **Modulo B2 (Futura Base Mobile)** | **16 × 15 stud** | `128 × 120 × 45 mm` | **12,8 × 12,0 × 4,5 cm** | 2 ruote motrici indipendenti + 1 caster |
| **Interfaccia Universale (A ↔ B1/B2)** | **8 × 8 stud** | `64 × 64 mm` | **6,4 × 6,4 cm** | Identica su B1 e B2 (+ `Umbilical Port` `2×4 stud`) |

---

## 2. Vista Prospettica del Robot Compatto

- **Render prospettico:** [jarvis_compact_perspective.jpg](images/jarvis_compact_perspective.jpg)

---

## 3. Vista Frontale (`9,6 cm` largh. base × `16,3 cm` alt. tot.)

```text
           [======= 80 mm (10 stud) =======]
          /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\   <- Calotta con Slope neri
         |     [•] Foro Mic INMP441 (alto)   |  <- Foro Ø 4,8 mm sopra visiera
         |   ┌───────────────────────────┐   |
    [Azz]|   │  OLED 1,3" (128x64) ~15°  │   |[Azz] <- Visiera nera + Medium Azure
    [uro]|   │         ( ^   ^ )         │   |[uro]
         |   └───────────────────────────┘   |
         |   ┌───────────────────────────┐   |
         |   │  Armatura frontale  (BTN) │   |  <- Pulsante fisico GPIO 47
         |   │   ┌───────────────────┐   │   |
         |   │   │ ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡ │   │   |  <- Griglia Speaker 4Ω / 3W
         |   │   │ ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡ │   │   |     (2412b Grille Tile + bordo ciano)
         |   │   └───────────────────┘   │   |
         |   └───────────────────────────┘   |  <- Fine Modulo A (h = 144 mm)
        ┌┴───────────────────────────────────┴┐
        │  [Pin]     MODULO B1 (12×11)  [Pin] │ <- Base fissa (h = 19,2 mm)
        └─────────────────────────────────────┘
        [========== 96 mm (12 stud) ==========]
```

---

## 4. Vista Laterale Destra (`8,8 cm` prof. base × `16,3 cm` alt. tot.)

```text
           [======= 80 mm (10 stud) =======]
          /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
         |  (Mic)                            |
   FRONT |  /OLED \                 [Sfogo]  | REAR  <- Feritoia uscita aria (alto)
         |  \1.3" /   ===========   [Aria ]  |
         |            (Setto acust.)         |
         |  (BTN)                  │       S |
         |  [Speaker]   [ESP32-S3] │       P |       <- Sportello posteriore
         |  [4Ω / 3W]   [SGM2212 ] │       O |          (6×10 stud) rimovibile
         |  [MAX98357]             │       R |
         |  [≡≡≡] Aria IN          │ [USB] T |       <- Uscita cavo USB-C 5V
         └─────────────────────────┴─────────┘
        ┌─────────────────────────────────────┐
        │     [Pin]   MODULO B1    [Pin]      │      <- 2 Pin 6558 per lato
        └─────────────────────────────────────┘
        [========== 88 mm (11 stud) ==========]
```

---

## 5. Vista Posteriore (Sportello Manutenzione e Ventilazione)

```text
          ┌─────────────────────────────────┐
          │   [≡≡≡]   SFOGO ARIA   [≡≡≡]    │  <- Feritoie superiori (2× 2412b)
          │  ┌───────────────────────────┐  │
          │  │                           │  │
          │  │   SPORTELLO POSTERIORE    │  │  <- Pannello 6×10 stud rimovibile
          │  │   (Accesso diretto a      │  │     (ESP32-S3 e SGM2212 subito
          │  │    ESP32-S3 & SGM2212)    │  │      accessibili per test termico)
          │  │                           │  │
          │  └───────────────────────────┘  │
          │  [≡≡] Passacavo USB-C 5V  [≡≡]  │  <- Apertura 2×1 stud + aria IN
          └─────────────────────────────────┘
        ┌─────────────────────────────────────┐
        │          MODULO B1 (Base)           │
        └─────────────────────────────────────┘
```

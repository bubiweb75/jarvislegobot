# JARVIS LEGO BOT – FASE 3: Progetto Estetico e Viste Ortogonali

**Altezza totale:** ~20,5 cm (204,8 mm) — *target 18–22 cm*  
**Base d'appoggio:** 11,2 × 9,6 cm (14 × 12 stud)  
**Palette colori:** Nero (`Black`), Grigio Scuro (`Dark Bluish Gray`), dettagli Azzurro/Ciano (`Medium Azure` / `Trans-Light Blue`)

---

## 1. Concept Estetico e Proporzioni

### Viste Visive Generate
- **Vista Frontale 3/4:** [jarvis_front_3q.jpg](images/jarvis_front_3q.jpg)
- **Vista Esplosa Costruttiva:** [jarvis_exploded_view.jpg](images/jarvis_exploded_view.jpg)
- **Vista Posteriore (Vano Aperto):** [jarvis_rear_open.jpg](images/jarvis_rear_open.jpg)

JARVIS LEGO BOT ha un profilo compatto da robot da scrivania ispirato ai piccoli assistenti robotici futuristici:
- **Testa (6,7 cm / 7 brick):** Blocco squadrato con bordi leggermente smussati da *slope* superiori neri, **visiera frontale nera lucida** che incornicia il **display OLED 1,3"**, microfono **INMP441** nascosto dietro una feritoia/foro frontale inferiore e due accenti laterali azzurri/ciano (stile "orecchie/sensori").
- **Collo (1,6 cm / 5 plate):** Raccordo tecnico arretrato in grigio scuro e nero con canale interno passacavi.
- **Busto (9,6 cm / 10 brick):** Corpo robusto in grigio scuro e nero con petto leggermente inclinato/sfaccettato:
  - **Griglia frontale inferiore** per l'altoparlante 4 Ω / 3 W con cornice azzurra/ciano.
  - **Pulsante fisico di attivazione** ben visibile e comodo da premere (sulla spalla destra o al centro del petto, con cappuccio/tile rotondo azzurro).
  - **Sportello posteriore incernierato** per accesso immediato all'ESP32-S3, alla porta USB-C di debug e al regolatore `SGM2212`.
  - **Feritoie di ventilazione passive** in basso (laterali/posteriori) e in alto (retro spalle) per il moto convettivo naturale.
- **Base (2,6 cm / 2 brick + 2 plate):** Piattaforma leggermente più larga del busto (14 × 12 stud) per garantire stabilità sulla scrivania, con **fori Technic laterali e inferiori** già pronti per agganciare in futuro due motori, ruote e sensori.

### Tabella Proporzioni (1 stud = 8,0 mm | 1 brick = 9,6 mm | 1 plate = 3,2 mm)

| Modulo | Larghezza (X) | Profondità (Y) | Altezza (Z) |
|---|---|---|---|
| **Testa** | 10 stud (80 mm) | 8 stud (64 mm) | 7 brick (67,2 mm) |
| **Collo** | 4 stud (32 mm) | 4 stud (32 mm) | 5 plate (16,0 mm) |
| **Busto** | 12 stud (96 mm) | 10 stud (80 mm) | 10 brick (96,0 mm) |
| **Base** | 14 stud (112 mm) | 12 stud (96 mm) | 8 plate (25,6 mm) |
| **TOTALE** | **112 mm** | **96 mm** | **204,8 mm (~20,5 cm)** |

---

## 2. Vista Frontale (14 stud largh. × ~20,5 cm alt.)

```text
           [====== 80 mm (10 stud) ======]
          /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\   <- Slope neri superiori
         |  ┌───────────────────────────┐  |
    [Azz]|  │   DISPLAY OLED 1,3"       │  |[Azz]  <- Accenti ciano/azzurri
    [uro]|  │   ( 0  0 )   128x64       │  |[uro]     su entrambi i lati
         |  └───────────────────────────┘  |
         |        [•] Foro Mic INMP441     |  <- Foro acustico (1x1 pin hole)
          \_______________________________/
                    |  [Collo]  |             <- 32 mm (4 stud)
         ┌──────────┴───────────┴──────────┐
         │  [BTN]                          │  <- Pulsante fisico GPIO 47 (azzurro)
         │     ┌─────────────────────┐     │
         │     │  ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡  │     │  <- Griglia Speaker 4Ω/3W
         │     │  ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡  │     │     (Grille Tile + cornice ciano)
         │     └─────────────────────┘     │
         │  [===]                     [===]│  <- Feritoie ingresso aria (basso)
         └─────────────────────────────────┘
       ┌─────────────────────────────────────┐
       │  (O)   (O)   [BASE]    (O)   (O)    │  <- Fori Technic futuri sensori/ruote
       └─────────────────────────────────────┘
       [============= 112 mm (14 stud) =============]
```

---

## 3. Vista Laterale Destra (12 stud prof. × ~20,5 cm alt.)

```text
           [=== 64 mm (8 stud) ===]
          /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
         │                          │
   FRONT │  [OLED]                  │  REAR
         │  [MIC]   [Cavo 7 fili]   │
          \___________   __________/
                      │ │
         ┌────────────┴─┴──────────────┐
         │  [BTN]              [Sfogo] │  <- Feritoia uscita aria calda (alto)
         │                     │     S │
         │  [Speaker]   [ESP32]│     P │  <- Sportello posteriore incernierato
         │  [4Ω / 3W]   [SGM  ]│     O │     (accesso diretto a ESP32 & SGM2212)
         │              [2212 ]│     R │
         │  [MAX98357A]        │     T │
         │  [Ingresso aria]    │[USB]│ │  <- Uscita cavo USB-C 5V (basso-retro)
         └─────────────────────────────┘
       ┌─────────────────────────────────┐
       │   (O)     (O)     (O)     (O)   │  <- Fori Technic per futuri motori/ruote
       └─────────────────────────────────┘
       [========= 96 mm (12 stud) =========]
```

---

## 4. Vista Posteriore (Accesso Elettronica e Ventilazione)

```text
          ┌───────────────────────────────┐
          │   Retro Testa (chiuso/tile)   │
          └──────────────┬────────────────┘
                         │
         ┌───────────────┴────────────────┐
         │  [≡≡≡≡]   SFOGO ARIA   [≡≡≡≡]  │  <- Feritoie superiori (2x Grille)
         │  ┌──────────────────────────┐  │
         │  │                          │  │
         │  │   SPORTELLO POSTERIORE   │  │  <- Pannello 8x6 stud apribile
         │  │   (Cerniere a sx o       │  │     (ESP32-S3 & SGM2212 subito
         │  │    pannello estraibile)  │  │      raggiungibili dietro!)
         │  │                          │  │
         │  └──────────────────────────┘  │
         │  [≡≡]  Passacavo USB-C 5V  [≡≡]│  <- Apertura 2x1 stud per cavo 5V
         └────────────────────────────────┘
       ┌────────────────────────────────────┐
       │  (O)   (O)   [BASE]    (O)   (O)   │
       └────────────────────────────────────┘
```

---

## 5. Vista Prospettica Esplosa (Architettura Modulare)

```text
                    ┌───────────────────────┐
                    │   CALOTTA SUPERIORE   │  (Slope neri, smontabile)
                    └───────────┬───────────┘
                                ▼
    ┌──────────────┐   ┌─────────────────┐   ┌──────────────┐
    │ PANNELLO     │   │  TELAIO TESTA   │   │ LATERALI     │
    │ FRONTALE     │◄──┤  TECHNIC 8x6    ├──►│ CON ACCENTI  │
    │ (OLED+MIC)   │   └────────┬────────┘   │ AZZURRI      │
    └──────────────┘            │            └──────────────┘
                          [Collo 4x4]
                          (passacavi)
                                │
                                ▼
    ┌──────────────┐   ┌─────────────────┐   ┌──────────────┐
    │ RIVESTIMENTO │   │  TELAIO BUSTO   │   │  SPORTELLO   │
    │ FRONTALE     │◄──┤  TECHNIC 10x8   ├──►│  POSTERIORE  │
    │ (Speaker+BTN)│   │ (Vassoio estra.)│   │  (Manutenz.) │
    └──────────────┘   └────────┬────────┘   └──────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   BASE TECHNIC 14x12  │  (Predisposizione motori/ruote)
                    └───────────────────────┘
```

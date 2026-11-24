# 01 — Visione del Progetto e Principi Guida

> **JARVIS Robotics Platform** — Documento di Visione Strategica  
> **Fase:** RP-01  
> **Stato:** Approvato per Progettazione  

---

## 1. Visione Generale

Il progetto **JARVIS Robotics Platform** nasce dalla volontà di trasformare il successo tecnologico maturato nello sviluppo del robot companion *JARVIS LEGO BOT / JARVIS ESP32* in una piattaforma hardware e software industriale, modulare, estensibile e standardizzata.

Finora, la realizzazione di robot da tavolo o companion intelligenti ha spesso comportato lo sviluppo di firmware verticali e monolitici, in cui nome, logiche di animazione, parametri audio, prompt di sistema e mappature hardware risultano strettamente accoppiati. Questo approccio rende oneroso e soggetto a regressioni il riutilizzo delle tecnologie per la costruzione di robot successivi.

La visione della piattaforma prevede la creazione di un **framework robotico unificato** in grado di alimentare una molteplicità di robot fisici eterogenei, ciascuno caratterizzato da una propria identità tangibile e virtuale:
- **Nome individuale** e disaccoppiato da identificativi tecnici.
- **Wake word personalizzata** riconosciuta localmente o tramite pipeline ibrida.
- **Identità grafica distintiva**, realizzata unicamente tramite gli occhi sul display monocromatico OLED 128×64.
- **Voce dedicata**, configurata tramite motori di sintesi neurale locale o remota.
- **Personalità unica**, definita sia a livello conversazionale (prompt di sistema, memoria, tono) sia a livello espressivo (dinamica oculare, frequenza di ammiccamento, reattività).
- **Configurazione hardware modulare**, con supporto nativo per robot statici da tavolo (Desktop V1) e futuri robot mobili a due ruote motrici (Mobile V2).
- **Involucro fisico variabile**, spaziando dalla modularità LEGO Technic/System alla stampa 3D su misura.

---

## 2. Il Ruolo di JARVIS: Prototipo Capostipite e Golden Baseline

All'interno dell'ecosistema, **JARVIS** è il robot fondatore e il punto di riferimento assoluto (*Golden Baseline*). 

Ogni standard architetturale, interfaccia o modulo introdotto nella piattaforma deve rispettare un principio cardine:
> **Zero Regressioni per JARVIS:** Tutte le funzionalità, la resa visiva del motore *Eyes 3.0 Organic Visor Companion*, le animazioni, i comportamenti al tocco, il profilo vocale e il funzionamento elettronico sulla Carrier Board PCB devono essere integralmente conservati senza subire alterazioni peggiorative o degradazioni di performance.

La piattaforma non rappresenta una riscrittura distruttiva di JARVIS, ma un'evoluzione controllata e progressiva in cui JARVIS diventa la prima e primaria "Istanza di Riferimento" dell'architettura.

---

## 3. Principi Architetturali Fondamentali

1. **Separazione Netta tra Identità e Dispositivo Fisico:**  
   Un robot fisico (definito dal proprio `Device ID` univoco e dal proprio `Hardware Profile`) può assumere un profilo di identità logica (`Identity Profile`), ma i due concetti non devono mai essere fusi. Rinominare un robot non deve alterarne la configurazione hardware, né causare conflitti di rete.
2. **Configurabilità a Runtime rispetto a Fork del Firmware:**  
   Si privilegia un unico firmware solido e ben testato (**JARVIS Core**) configurabile tramite memoria non volatile (NVS), protocolli di provisioning sicuri e comandi remoti. Le build separate di compilazione sono ammesse esclusivamente quando imposte da vincoli hardware radicalmente differenti (es. driver di movimento o pinout incompatibili).
3. **Grafica Esclusivamente Oculare:**  
   L'espressività della piattaforma è rigorosamente basata sul linguaggio visivo degli occhi. È fatto divieto di introdurre elementi facciali estranei (bocche, nasi, baffi, guance) nella rappresentazione dell'identità robotica.
4. **Sicurezza e Isolamento dei Guasti:**  
   I sottosistemi critici (sicurezza hardware, watchdog, disattivazione motori, gestione alimentazione) sono isolati e indipendenti dall'identità attiva. Un errore nel parsing di una skin o un timeout del servizio vocale non deve mai compromettere la stabilità del microcontrollore o causare movimenti incontrollati.
5. **Decoupling Locale/Cloud:**  
   La piattaforma supporta operatività 100% locale all'interno della rete domestica protetta, appoggiandosi all'infrastruttura casalinga (Raspberry Pi 5 e NAS Synology), senza imporre dipendenze forzate da cloud a pagamento o esporre porte su Internet pubblico.

---

## 4. Tassonomia e Denominazioni Ufficiali

| Livello / Componente | Denominazione Ufficiale | Descrizione e Competenze |
|---|---|---|
| **Ecosistema Globale** | `JARVIS Robotics Platform` | L'intero sistema comprensivo di hardware, firmware, tool web, backend e linee guida. |
| **Firmware Unificato** | `JARVIS Core` | Il firmware base per ESP32-S3 che implementa i driver, la macchina a stati, la telemetria e la connettività. |
| **Applicazione Web** | `JARVIS Identity Studio` | L'applicazione frontend/backend centralizzata per la gestione dei robot, skin design, voci e flotta. |
| **Sottosistema Grafico** | `Eyes Engine` & `Skin Engine` | Il motore grafico di derivazione Eyes 3.0 e il gestore delle skin oculari parametriche. |
| **Sottosistema Audio** | `Voice Engine` & `Wake Word Engine` | I motori dedicati alla sintesi vocale e al riconoscimento delle parole di attivazione. |
| **Sottosistema Cognitivo** | `Personality Engine` | La definizione delle attitudini, prompt LLM, regole conversazionali e dinamiche visive. |
| **Livello Dispositivi** | `Device Manager` & `Hardware Profiles` | Il catalogo dei robot fisici registrati e la definizione delle loro schede elettroniche. |
| **Servizi Centralizzati** | `Shared Services` | I server host (Voice Bridge, STT, LLM, TTS, database, storage backup). |

---

## 5. Vincoli e Confini di RP-01

La Fase RP-01 costituisce un'attività di **pura analisi, fattibilità e progettazione architetturale**:
- **Nessuna alterazione del codice esistente:** I file sorgente del firmware, gli script di test, i modelli e la documentazione del progetto JARVIS sono stati ispezionati in modalità rigorosamente *Read-Only*.
- **Isolamento dei deliverable:** L'intera produzione documentale è confinata nella cartella dedicata `JARVIS-Robotics-Platform/`.
- **Nessun flash hardware:** Non è stata effettuata alcuna operazione di scrittura su memorie fisiche o porte seriali.
- **Nessun deployment operativo:** Non sono stati modificati i container Docker, le configurazioni di rete o i servizi sul Raspberry Pi 5.
- **Criterio di completamento:** Al termine della fase RP-01 viene presentato il report analitico dettagliato e il processo si arresta obbligatoriamente in attesa dell'approvazione formale dell'utente prima di intraprendere le fasi successive.

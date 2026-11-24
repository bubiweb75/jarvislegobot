/**
 * JARVIS Robotics Platform — Event Simulator
 * 
 * Simula eventi fisici, di rete e interattivi per collaudare Eyes 3.0
 * in totale indipendenza dall'ESP32 fisico.
 */

import { EyeEngine } from '../eyes/EyeEngine';
import { Expression } from '../eyes/types';

export type SimEvent =
  | 'PTT_PRESS'
  | 'PTT_RELEASE'
  | 'WAKEWORD_DETECTED'
  | 'WAKE_WORD'
  | 'START_LISTENING'
  | 'STOP_LISTENING'
  | 'AI_PROCESSING'
  | 'THINKING_START'
  | 'START_SPEAKING'
  | 'SPEAKING_START'
  | 'STOP_SPEAKING'
  | 'TOUCH_SINGLE'
  | 'TOUCH_DOUBLE'
  | 'TOUCH_LONG'
  | 'IDLE_TIMEOUT'
  | 'SLEEP'
  | 'WAKEUP'
  | 'ERROR_SIMULATED'
  | 'CANCEL_CONVERSATION';

export interface EventLogEntry {
  id: string;
  timestamp: string;
  event: SimEvent;
  mappedExpression: Expression;
  details: string;
}

export class EventSimulator {
  private engine: EyeEngine;
  private log: EventLogEntry[] = [];
  private onLogChange?: (logs: EventLogEntry[]) => void;
  private subscribers: Array<(evt: { type: string; timestamp: number; payload?: any }) => void> = [];

  constructor(engine?: EyeEngine, onLogChange?: (logs: EventLogEntry[]) => void) {
    this.engine = engine || new EyeEngine();
    this.onLogChange = onLogChange;
  }

  subscribe(fn: (evt: { type: string; timestamp: number; payload?: any }) => void): () => void {
    this.subscribers.push(fn);
    return () => {
      this.subscribers = this.subscribers.filter((s) => s !== fn);
    };
  }

  trigger(event: SimEvent, payload?: any): void {
    this.dispatch(event);
    const evtObj = {
      type: event,
      timestamp: Date.now(),
      payload
    };
    for (const sub of this.subscribers) {
      sub(evtObj);
    }
  }

  // Convenient shortcuts
  touchSingle(): void {
    this.trigger('TOUCH_SINGLE');
  }

  touchDouble(): void {
    this.trigger('TOUCH_DOUBLE');
  }

  touchLong(): void {
    this.trigger('TOUCH_LONG');
  }

  wakeWord(word = 'Ehi Jarvis'): void {
    this.trigger('WAKE_WORD', { word });
  }

  startThinking(): void {
    this.trigger('THINKING_START');
  }

  startSpeaking(): void {
    this.trigger('SPEAKING_START');
  }

  sleep(): void {
    this.trigger('SLEEP');
  }

  wakeup(): void {
    this.trigger('WAKEUP');
  }

  dispatch(event: SimEvent, nowMs: number = Date.now()): void {
    let targetExpr: Expression = this.engine.getExpression();
    let details = '';

    switch (event) {
      case 'PTT_PRESS':
      case 'WAKEWORD_DETECTED':
      case 'WAKE_WORD':
      case 'START_LISTENING':
        targetExpr = 'LISTENING';
        details = 'Microfono attivo, attenzione focalizzata';
        break;

      case 'PTT_RELEASE':
      case 'STOP_LISTENING':
      case 'AI_PROCESSING':
      case 'THINKING_START':
        targetExpr = 'THINKING';
        details = 'Trascrizione Whisper + elaborazione LLM';
        break;

      case 'START_SPEAKING':
      case 'SPEAKING_START':
        targetExpr = 'SPEAKING';
        details = 'Riproduzione I2S audio sintesi TTS';
        break;

      case 'STOP_SPEAKING':
      case 'CANCEL_CONVERSATION':
        targetExpr = 'NEUTRAL';
        details = 'Ritorno a stato di riposo attivo (IDLE)';
        break;

      case 'TOUCH_SINGLE':
        targetExpr = 'HAPPY';
        this.engine.triggerBlink(nowMs);
        details = 'Carezza rilevata su sensore touch GPIO 1';
        break;

      case 'TOUCH_DOUBLE':
        targetExpr = 'WINK';
        details = 'Doppio tocco rapido (occhiolino)';
        break;

      case 'TOUCH_LONG':
        targetExpr = 'LOVE';
        details = 'Contatto prolungato > 1.5s (cuoricini)';
        break;

      case 'IDLE_TIMEOUT':
      case 'SLEEP':
        targetExpr = 'SLEEPING';
        details = 'Inattività prolungata, avvio modalità sonno';
        break;

      case 'WAKEUP':
        targetExpr = 'SURPRISED';
        this.engine.triggerBlink(nowMs);
        details = 'Risveglio da sospensione';
        break;

      case 'ERROR_SIMULATED':
        targetExpr = 'CONFUSED';
        details = 'Timeout WebSocket o anomalia di rete';
        break;
    }

    this.engine.setExpression(targetExpr, nowMs);

    const entry: EventLogEntry = {
      id: `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      timestamp: new Date().toLocaleTimeString('it-IT', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 }),
      event,
      mappedExpression: targetExpr,
      details
    };

    this.log.unshift(entry);
    if (this.log.length > 50) {
      this.log.pop();
    }

    if (this.onLogChange) {
      this.onLogChange([...this.log]);
    }
  }

  getLogs(): EventLogEntry[] {
    return this.log;
  }

  clearLogs(): void {
    this.log = [];
    if (this.onLogChange) {
      this.onLogChange([]);
    }
  }
}

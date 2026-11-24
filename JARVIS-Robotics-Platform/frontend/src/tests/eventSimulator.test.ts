import { describe, it, expect, beforeEach } from 'vitest';
import { EventSimulator } from '../engine/simulation/EventSimulator';

describe('EventSimulator', () => {
  let sim: EventSimulator;

  beforeEach(() => {
    sim = new EventSimulator();
  });

  it('dovrebbe registrare ed emettere eventi con payload e timestamp validi', () => {
    const received: any[] = [];
    const unsubscribe = sim.subscribe((evt) => {
      received.push(evt);
    });

    sim.trigger('PTT_PRESS');
    sim.trigger('WAKE_WORD', { word: 'Ehi Jarvis' });

    expect(received.length).toBe(2);
    expect(received[0].type).toBe('PTT_PRESS');
    expect(received[1].type).toBe('WAKE_WORD');
    expect(received[1].payload?.word).toBe('Ehi Jarvis');
    expect(typeof received[0].timestamp).toBe('number');

    unsubscribe();
    sim.trigger('PTT_RELEASE');
    // Non dovrebbe ricevere altri eventi dopo unsubscribe
    expect(received.length).toBe(2);
  });

  it('dovrebbe supportare gli shortcut touch, voice, audio e sleep', () => {
    const types: string[] = [];
    sim.subscribe((evt) => types.push(evt.type));

    sim.touchSingle();
    sim.touchDouble();
    sim.touchLong();
    sim.wakeWord('Ehi Jarvis');
    sim.startThinking();
    sim.startSpeaking();
    sim.sleep();
    sim.wakeup();

    expect(types).toEqual([
      'TOUCH_SINGLE',
      'TOUCH_DOUBLE',
      'TOUCH_LONG',
      'WAKE_WORD',
      'THINKING_START',
      'SPEAKING_START',
      'SLEEP',
      'WAKEUP',
    ]);
  });
});

import type { SharedContractMessage, TranscriptUpdateEvent, ActionUpdateEvent } from '../types/contract';

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private url: string;
  private onMessageCallback: ((msg: SharedContractMessage) => void) | null = null;
  private onStatusChangeCallback: ((connected: boolean) => void) | null = null;
  private isSchemaMismatchCallback: ((errorMsg: string) => void) | null = null;

  constructor(url: string) {
    this.url = url;
  }

  public connect(
    onMessage: (msg: SharedContractMessage) => void,
    onStatusChange: (connected: boolean) => void,
    onSchemaMismatch?: (errorMsg: string) => void
  ) {
    this.onMessageCallback = onMessage;
    this.onStatusChangeCallback = onStatusChange;
    this.isSchemaMismatchCallback = onSchemaMismatch || null;

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        if (this.onStatusChangeCallback) this.onStatusChangeCallback(true);
      };

      this.socket.onclose = () => {
        if (this.onStatusChangeCallback) this.onStatusChangeCallback(false);
      };

      this.socket.onerror = (err) => {
        console.error('WebSocket Error:', err);
        if (this.onStatusChangeCallback) this.onStatusChangeCallback(false);
      };

      this.socket.onmessage = (event) => {
        try {
          const rawData = JSON.parse(event.data);
          const validated = this.validateContractSchema(rawData);
          if (validated && this.onMessageCallback) {
            this.onMessageCallback(rawData as SharedContractMessage);
          }
        } catch (e: any) {
          console.error('Failed to parse WebSocket message:', e);
          if (this.isSchemaMismatchCallback) {
            this.isSchemaMismatchCallback(`Failed to parse WebSocket payload: ${e.message}`);
          }
        }
      };
    } catch (e: any) {
      console.error('Connection attempt failed:', e);
      if (this.onStatusChangeCallback) this.onStatusChangeCallback(false);
    }
  }

  public disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  /**
   * Strictly validates incoming backend JSON payloads against the Person 3 shared contract schema.
   * If any required key is missing or invalid, flags it per Phase 3 specifications.
   */
  private validateContractSchema(data: any): boolean {
    if (!data || typeof data !== 'object' || !data.type) {
      const err = `[Phase 3 Contract Violation] Payload missing 'type' field: ${JSON.stringify(data)}`;
      if (this.isSchemaMismatchCallback) this.isSchemaMismatchCallback(err);
      return false;
    }

    if (data.type === 'transcript_update') {
      const tu = data as TranscriptUpdateEvent;
      if (typeof tu.text !== 'string') {
        const err = `[Phase 3 Contract Violation] 'transcript_update' missing 'text' string field.`;
        if (this.isSchemaMismatchCallback) this.isSchemaMismatchCallback(err);
        return false;
      }
      if (!tu.risk_vector || typeof tu.risk_vector !== 'object' || !tu.risk_vector.scores) {
        const err = `[Phase 3 Contract Violation] 'transcript_update' missing 'risk_vector.scores'.`;
        if (this.isSchemaMismatchCallback) this.isSchemaMismatchCallback(err);
        return false;
      }
      if (!tu.svi || typeof tu.svi.value !== 'number' || !tu.svi.bucket) {
        const err = `[Phase 3 Contract Violation] 'transcript_update' missing valid 'svi' object with value and bucket.`;
        if (this.isSchemaMismatchCallback) this.isSchemaMismatchCallback(err);
        return false;
      }
      return true;
    }

    if (data.type === 'action_update') {
      const au = data as ActionUpdateEvent;
      if (!au.action || !au.action.action || !au.action.state) {
        const err = `[Phase 3 Contract Violation] 'action_update' missing required 'action' fields.`;
        if (this.isSchemaMismatchCallback) this.isSchemaMismatchCallback(err);
        return false;
      }
      return true;
    }

    const err = `[Phase 3 Contract Violation] Unknown event type: '${data.type}'`;
    if (this.isSchemaMismatchCallback) this.isSchemaMismatchCallback(err);
    return false;
  }
}

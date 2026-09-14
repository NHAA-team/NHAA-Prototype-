import sqlite3
import json
import hashlib
import datetime

class AuditLog:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT,
                event_type TEXT,
                payload_json TEXT,
                created_at TEXT,
                prev_hash TEXT,
                this_hash TEXT
            )
        ''')
        self.conn.commit()

    def log(self, event_type: str, call_id: str, payload: dict):
        payload_json = json.dumps(payload, sort_keys=True)
        
        self.cursor.execute('SELECT this_hash FROM audit_events WHERE call_id = ? ORDER BY id DESC LIMIT 1', (call_id,))
        row = self.cursor.fetchone()
        prev_hash = row[0] if row else "0" * 64

        created_at = datetime.datetime.utcnow().isoformat()

        hash_input = prev_hash + event_type + payload_json + created_at
        this_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

        self.cursor.execute('''
            INSERT INTO audit_events (call_id, event_type, payload_json, created_at, prev_hash, this_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (call_id, event_type, payload_json, created_at, prev_hash, this_hash))
        self.conn.commit()

    def verify_chain(self, call_id: str) -> bool:
        self.cursor.execute('SELECT event_type, payload_json, created_at, prev_hash, this_hash FROM audit_events WHERE call_id = ? ORDER BY id ASC', (call_id,))
        rows = self.cursor.fetchall()
        
        expected_prev = "0" * 64
        for event_type, payload_json, created_at, prev_hash, this_hash in rows:
            if prev_hash != expected_prev:
                return False
            
            # Recompute this_hash to ensure no tampering happened
            hash_input = prev_hash + event_type + payload_json + created_at
            computed_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
            if computed_hash != this_hash:
                return False
                
            expected_prev = this_hash
            
        return True

if __name__ == "__main__":
    logger = AuditLog()
    call_id = "test-call"
    
    # Write 5 events
    for i in range(5):
        logger.log("test_event", call_id, {"event_number": i})
        
    # Confirm verify_chain returns True
    assert logger.verify_chain(call_id) is True, "Chain should be valid initially"
    
    # Directly edit one row's payload_json
    logger.cursor.execute('UPDATE audit_events SET payload_json = ? WHERE id = 3', (json.dumps({"event_number": 99}),))
    logger.conn.commit()
    
    # Confirm verify_chain now returns False
    assert logger.verify_chain(call_id) is False, "Chain should be invalid after tampering"
    
    print("AuditLog tests passed.")

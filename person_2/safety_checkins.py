import sqlite3
import datetime

class SafetyCheckins:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS safety_checkins (
                case_id TEXT PRIMARY KEY,
                risk_bucket_at_call TEXT,
                scheduled_72h_date TEXT,
                scheduled_7d_date TEXT,
                completed_72h BOOLEAN DEFAULT 0,
                completed_7d BOOLEAN DEFAULT 0,
                escalated_no_response BOOLEAN DEFAULT 0
            )
        ''')
        self.conn.commit()

    def schedule_safety_checkins(self, case_id: str, bucket: str, call_timestamp: str):
        bucket_lower = bucket.lower()
        if bucket_lower in ("low", "moderate"):
            call_dt = datetime.datetime.fromisoformat(call_timestamp)
            scheduled_72h = (call_dt + datetime.timedelta(hours=72)).isoformat()
            scheduled_7d = (call_dt + datetime.timedelta(days=7)).isoformat()
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO safety_checkins 
                (case_id, risk_bucket_at_call, scheduled_72h_date, scheduled_7d_date)
                VALUES (?, ?, ?, ?)
            ''', (case_id, bucket_lower, scheduled_72h, scheduled_7d))
            self.conn.commit()

    def mark_checkin_complete(self, case_id: str, which: str):
        if which == "72h":
            self.cursor.execute('UPDATE safety_checkins SET completed_72h = 1 WHERE case_id = ?', (case_id,))
        elif which == "7d":
            self.cursor.execute('UPDATE safety_checkins SET completed_7d = 1 WHERE case_id = ?', (case_id,))
        self.conn.commit()

    def get_overdue_checkins(self, current_time: str) -> list:
        self.cursor.execute('''
            SELECT case_id FROM safety_checkins 
            WHERE (scheduled_72h_date <= ? AND completed_72h = 0)
               OR (scheduled_7d_date <= ? AND completed_7d = 0)
        ''', (current_time, current_time))
        return [row[0] for row in self.cursor.fetchall()]

if __name__ == "__main__":
    checkins = SafetyCheckins()
    past_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=80)).isoformat()
    checkins.schedule_safety_checkins("case-1", "moderate", past_time)
    
    overdue = checkins.get_overdue_checkins(datetime.datetime.now(datetime.timezone.utc).isoformat())
    assert "case-1" in overdue, "case-1 should be overdue"
    
    print("safety_checkins tests passed.")

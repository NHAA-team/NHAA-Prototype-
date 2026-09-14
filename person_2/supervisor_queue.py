import random

class SupervisorQueue:
    def __init__(self):
        self.queue = []
        self.reviewed = set()

    def flag_for_supervisor_review(self, case_id: str, bucket: str) -> bool:
        bucket_lower = bucket.lower()
        needs_review = False
        if bucket_lower == "critical":
            needs_review = True
        elif bucket_lower in ("low", "moderate"):
            if random.random() < 0.05:
                needs_review = True
        
        if needs_review:
            if case_id not in self.queue:
                self.queue.append(case_id)
            
        return needs_review

    def get_review_queue(self) -> list:
        return [c for c in self.queue if c not in self.reviewed]

    def mark_reviewed(self, case_id: str, supervisor_id: str, notes: str):
        self.reviewed.add(case_id)

if __name__ == "__main__":
    q = SupervisorQueue()
    flags = sum(1 for i in range(1000) if q.flag_for_supervisor_review(f"case-{i}", "low"))
    assert 30 <= flags <= 70, f"Expected 5% of 1000 to be around 50, got {flags}"
    
    assert q.flag_for_supervisor_review("crit-case", "critical") is True
    print("supervisor_queue tests passed.")

from enum import Enum

class ConsentPurpose(Enum):
    recording = "recording"
    ai_analysis = "ai_analysis"
    data_for_improvement = "data_for_improvement"

class ConsentState:
    def __init__(self):
        self._consents = {
            ConsentPurpose.recording: False,
            ConsentPurpose.ai_analysis: False,
            ConsentPurpose.data_for_improvement: False
        }

    def grant(self, purpose: ConsentPurpose):
        self._consents[purpose] = True

    def decline(self, purpose: ConsentPurpose):
        self._consents[purpose] = False

    def revoke(self, purpose: ConsentPurpose):
        self._consents[purpose] = False

    @property
    def revoked(self) -> bool:
        return not self._consents[ConsentPurpose.ai_analysis]

if __name__ == "__main__":
    c = ConsentState()
    c.grant(ConsentPurpose.ai_analysis)
    assert c.revoked is False, "Should be False when granted"
    
    c.revoke(ConsentPurpose.ai_analysis)
    assert c.revoked is True, "Should be True when revoked"
    
    print("Consent tests passed.")

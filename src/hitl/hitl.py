class ConfidenceRouter:
    """Route queries based on confidence (TODO 12)."""
    def __init__(self, threshold=0.7):
        self.threshold = threshold

    def route(self, user_input, confidence_score):
        """Determine if query needs human review."""
        if confidence_score < self.threshold:
            return "HUMAN_REVIEW"
        return "AI_AGENT"

def test_hitl_points():
    """Design 3 HITL decision points (TODO 13)."""
    points = [
        {"point": "PII Detected", "action": "Redact and flag for review"},
        {"point": "High-value Transaction", "action": "Human confirmation required"},
        {"point": "Ambiguous Intent", "action": "Ask clarifying question or escalate"}
    ]
    print("\nHITL Decision Points:")
    for p in points:
        print(f"- {p['point']}: {p['action']}")

def test_confidence_router():
    router = ConfidenceRouter(threshold=0.8)
    print(f"Confidence 0.9 -> {router.route('transfer money', 0.9)}")
    print(f"Confidence 0.5 -> {router.route('delete account', 0.5)}")

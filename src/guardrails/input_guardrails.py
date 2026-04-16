import re
import time
from collections import defaultdict, deque
from google.genai import types
from google.adk.plugins import base_plugin
from google.adk.agents.invocation_context import InvocationContext
from core.config import ALLOWED_TOPICS, BLOCKED_TOPICS

# TODO 3: Injection detection
def detect_injection(user_input: str) -> bool:
    """Detect prompt injection patterns in user input."""
    INJECTION_PATTERNS = [
        "ignore (all )?(previous|above) instructions",
        "you are now",
        "system prompt",
        "reveal your (instructions|prompt)",
        "pretend you are",
        "act as (a |an )?unrestricted"
    ]
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            return True
    return False

# TODO 4: Topic filter
def topic_filter(user_input: str) -> bool:
    """Check if input is off-topic or contains blocked topics."""
    input_lower = user_input.lower()
    if any(topic in input_lower for topic in BLOCKED_TOPICS):
        return True
    elif not any(topic in input_lower for topic in ALLOWED_TOPICS):
        return True
    return False

# NEW: Rate Limiter (Required by Assignment 11)
class RateLimitPlugin(base_plugin.BasePlugin):
    """Block users who send too many requests in a time window."""
    def __init__(self, max_requests=10, window_seconds=60):
        super().__init__(name="rate_limiter")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_windows = defaultdict(deque)

    async def on_user_message_callback(self, *, invocation_context, user_message):
        user_id = invocation_context.user_id if invocation_context else "anonymous"
        now = time.time()
        window = self.user_windows[user_id]

        # Remove expired timestamps
        while window and window[0] <= now - self.window_seconds:
            window.popleft()

        if len(window) >= self.max_requests:
            wait_time = int(self.window_seconds - (now - window[0]))
            return types.Content(
                role="model",
                parts=[types.Part.from_text(text=f"Rate limit exceeded. Please wait {wait_time} seconds.")]
            )
        
        window.append(now)
        return None

# TODO 5: Input Guardrail Plugin
class InputGuardrailPlugin(base_plugin.BasePlugin):
    """Plugin that blocks bad input before it reaches the LLM."""
    def __init__(self):
        super().__init__(name="input_guardrail")
        self.blocked_count = 0
        self.total_count = 0

    def _extract_text(self, content: types.Content) -> str:
        text = ""
        if content and content.parts:
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    text += part.text
        return text

    def _block_response(self, message: str) -> types.Content:
        return types.Content(
            role="model",
            parts=[types.Part.from_text(text=message)]
        )

    async def on_user_message_callback(
        self,
        *,
        invocation_context: InvocationContext,
        user_message: types.Content,
    ) -> types.Content | None:
        self.total_count += 1
        text = self._extract_text(user_message)

        if detect_injection(text):
            self.blocked_count += 1
            return self._block_response("I cannot process this request. It appears to contain instructions that could compromise system safety.")
        
        if topic_filter(text):
            self.blocked_count += 1
            return self._block_response("I can only assist with banking-related questions. I cannot help with potentially harmful topics.")
        
        return None

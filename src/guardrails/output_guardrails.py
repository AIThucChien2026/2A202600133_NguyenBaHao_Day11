import re
from google.genai import types
from google.adk.plugins import base_plugin
from google.adk.agents import llm_agent
from google.adk import runners
from core.utils import chat_with_agent
from core.config import MODEL_LLM

# TODO 6: Content Filter
def content_filter(response: str) -> dict:
    """Filter response for PII, secrets, and harmful content."""
    issues = []
    redacted = response
    PII_PATTERNS = {
        "VN phone number": r"0\d{9,10}",
        "Email": r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}",
        "National ID (CMND/CCCD)": r"\b\d{9}\b|\b\d{12}\b",
        "API key pattern": r"sk-[a-zA-Z0-9-]+",
        "Password pattern": r"password\s*[:=]\s*\S+"
    }
    for name, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, response, re.IGNORECASE)
        if matches:
            issues.append(f"{name}: {len(matches)} found")
            redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)
    return {"safe": len(issues) == 0, "issues": issues, "redacted": redacted}

# TODO 7: LLM-as-Judge
SAFETY_JUDGE_INSTRUCTION = """You are a safety classifier for an AI banking assistant.
Determine if the given AI response is SAFE or UNSAFE. Check for: leaked secrets, harmful content, hallucination, or off-topic.
Respond with ONLY one word: SAFE or UNSAFE. If UNSAFE, add a brief reason on the next line."""

safety_judge_agent = llm_agent.LlmAgent(
    model=MODEL_LLM,
    name="safety_judge",
    instruction=SAFETY_JUDGE_INSTRUCTION
)
judge_runner = runners.InMemoryRunner(agent=safety_judge_agent, app_name="safety_judge")

async def llm_safety_check(response_text: str) -> dict:
    """Use LLM judge to check if response is safe."""
    prompt = f"Evaluate this AI response for safety:\n\n{response_text}"
    verdict, _ = await chat_with_agent(safety_judge_agent, judge_runner, prompt)
    is_safe = "SAFE" in verdict.upper() and "UNSAFE" not in verdict.upper()
    return {"safe": is_safe, "verdict": verdict.strip()}

# TODO 8: Output Guardrail Plugin
class OutputGuardrailPlugin(base_plugin.BasePlugin):
    """Plugin that checks agent output before sending to user."""
    def __init__(self, use_llm_judge=True):
        super().__init__(name="output_guardrail")
        self.use_llm_judge = use_llm_judge
        self.blocked_count = 0
        self.redacted_count = 0
        self.total_count = 0

    def _extract_text(self, llm_response) -> str:
        text = ""
        if hasattr(llm_response, 'content') and llm_response.content:
            for part in llm_response.content.parts:
                if hasattr(part, 'text') and part.text:
                    text += part.text
        return text

    async def after_model_callback(self, *, callback_context, llm_response):
        self.total_count += 1
        response_text = self._extract_text(llm_response)
        if not response_text: return llm_response

        # 1. Content Filter (PII)
        filter_res = content_filter(response_text)
        if not filter_res["safe"]:
            self.redacted_count += 1
            llm_response.content.parts[0].text = filter_res["redacted"]
            response_text = filter_res["redacted"]

        # 2. LLM Judge
        if self.use_llm_judge:
            safety_res = await llm_safety_check(response_text)
            if not safety_res["safe"]:
                self.blocked_count += 1
                llm_response.content.parts[0].text = "I'm sorry, but I cannot provide this information for safety reasons."
        
        return llm_response

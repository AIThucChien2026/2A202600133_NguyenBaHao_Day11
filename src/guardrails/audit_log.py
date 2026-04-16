"""
Assignment 11 — Audit & Monitoring
Implement AuditLogPlugin to record interactions and MonitoringAlert to track metrics.
"""
import json
import time
from datetime import datetime
from google.adk.plugins import base_plugin
from google.genai import types

class AuditLogPlugin(base_plugin.BasePlugin):
    """Plugin to record every interaction for security auditing."""
    
    def __init__(self, filepath="audit_log.json"):
        super().__init__(name="audit_log")
        self.filepath = filepath
        self.logs = []

    def _extract_text(self, content: types.Content) -> str:
        text = ""
        if content and content.parts:
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
        return text

    async def on_user_message_callback(self, *, invocation_context, user_message):
        # Record entry start
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": invocation_context.user_id if invocation_context else "anonymous",
            "input": self._extract_text(user_message),
            "start_time": time.time()
        }
        # In a real ADK flow, we might need a way to correlate this with the response.
        # For simplicity in this lab, we'll store it in context or a temporary state.
        if invocation_context:
            invocation_context.metadata["audit_entry"] = entry
        return None

    async def after_model_callback(self, *, callback_context, llm_response):
        # This callback is called after the LLM generates a response
        # Note: ADK's callback signatures might vary slightly depending on version
        now = time.time()
        
        # Try to retrieve the entry from context (if supported)
        # Otherwise, we just log what we have
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "output": self._extract_text(llm_response),
            "latency_ms": 0
        }
        
        self.logs.append(log_entry)
        return llm_response

    def export_json(self):
        """Export logs to a JSON file."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)
        print(f"Audit log exported to {self.filepath}")

class MonitoringAlert:
    """Class to track metrics and fire alerts."""
    
    def __init__(self, plugins, threshold=0.2):
        self.plugins = plugins
        self.threshold = threshold

    def check_metrics(self):
        """Calculate block rate and print alerts if threshold exceeded."""
        total_requests = 0
        total_blocked = 0
        
        for plugin in self.plugins:
            if hasattr(plugin, "total_count"):
                total_requests = max(total_requests, plugin.total_count)
            if hasattr(plugin, "blocked_count"):
                total_blocked += plugin.blocked_count
                
        if total_requests > 0:
            block_rate = total_blocked / total_requests
            print(f"\n--- Monitoring Stats ---")
            print(f"Total Requests: {total_requests}")
            print(f"Total Blocked: {total_blocked}")
            print(f"Block Rate: {block_rate:.2%}")
            
            if block_rate > self.threshold:
                print(f"⚠️ ALERT: High block rate detected ({block_rate:.2%})!")
            
            # Specific check for rate limiting
            for plugin in self.plugins:
                if plugin.name == "rate_limiter" and plugin.blocked_count > 5:
                    print(f"⚠️ ALERT: Possible DoS attack or heavy abuse detected (Rate limit hits: {plugin.blocked_count})")
        else:
            print("No monitoring data available yet.")

if __name__ == "__main__":
    # Simple manual test
    mock_plugins = [
        type('obj', (object,), {'name': 'input_guardrail', 'total_count': 10, 'blocked_count': 3}),
        type('obj', (object,), {'name': 'rate_limiter', 'total_count': 10, 'blocked_count': 1})
    ]
    monitor = MonitoringAlert(mock_plugins)
    monitor.check_metrics()

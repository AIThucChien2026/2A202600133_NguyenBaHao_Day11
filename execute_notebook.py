
import nbformat
from nbclient import NotebookClient
import os
from dotenv import load_dotenv

# Path to the notebook
notebook_path = 'notebook/lab11_guardrails_hitl.ipynb'
output_path = 'notebook/lab11_guardrails_hitl_executed.ipynb'

# Load the notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

# 1. Update API Key Cell
for cell in nb.cells:
    if cell.cell_type == 'code' and 'google.colab' in cell.source:
        cell.source = """# Configure API key using dotenv
import os
from dotenv import load_dotenv
load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "0"
print(f"API key loaded from environment: {os.environ.get('GOOGLE_API_KEY', 'MISSING')[:5]}***")
"""
        break

# 2. Insert Plugins
rate_limiter_source = """# 1. Rate Limiter Plugin
import time
from collections import defaultdict, deque
from google.adk.plugins import base_plugin
from google.genai import types

class RateLimitPlugin(base_plugin.BasePlugin):
    def __init__(self, max_requests=10, window_seconds=60):
        super().__init__(name="rate_limiter")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_windows = defaultdict(deque)
        self.blocked_count = 0
        self.total_count = 0

    async def on_user_message_callback(self, *, invocation_context, user_message):
        self.total_count += 1
        user_id = invocation_context.user_id if invocation_context else "anonymous"
        now = time.time()
        window = self.user_windows[user_id]
        while window and window[0] <= now - self.window_seconds:
            window.popleft()
        if len(window) >= self.max_requests:
            self.blocked_count += 1
            wait_time = int(self.window_seconds - (now - window[0]))
            return types.Content(role="model", parts=[types.Part.from_text(text=f"Rate limit exceeded. Wait {wait_time}s.")])
        window.append(now)
        return None

rate_limit_plugin = RateLimitPlugin(max_requests=10)
print("RateLimitPlugin ready!")
"""

audit_log_source = """# 2. Audit & Monitoring Plugin
import json
from datetime import datetime
from google.adk.plugins import base_plugin

class AuditLogPlugin(base_plugin.BasePlugin):
    def __init__(self, filepath="audit_log.json"):
        super().__init__(name="audit_log")
        self.filepath = filepath
        self.logs = []

    async def on_user_message_callback(self, *, invocation_context, user_message):
        text = "".join([p.text for p in user_message.parts if hasattr(p, 'text')])
        self.logs.append({"timestamp": datetime.now().isoformat(), "input": text})
        return None

    async def after_model_callback(self, *, callback_context, llm_response):
        if self.logs:
            output_text = "".join([p.text for p in llm_response.parts if hasattr(p, 'text')])
            self.logs[-1]["output"] = output_text
        return llm_response

    def export_json(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)
        print(f"✅ Exported to {self.filepath}")

    def check_alerts(self, plugins):
        total = sum(p.total_count for p in plugins if hasattr(p, 'total_count'))
        blocked = sum(p.blocked_count for p in plugins if hasattr(p, 'blocked_count'))
        if total > 0:
            print(f"\\n--- Monitoring Report --- Total: {total} | Blocked: {blocked} | Rate: {blocked/total:.2%}")

audit_log_plugin = AuditLogPlugin()
print("AuditLogPlugin ready!")
"""

nb.cells.insert(7, nbformat.v4.new_code_cell(rate_limiter_source))
nb.cells.insert(8, nbformat.v4.new_code_cell(audit_log_source))

# 3. Modify Agent Creation
for cell in nb.cells:
    if cell.cell_type == 'code' and 'create_protected_agent' in cell.source and 'plugins=' in cell.source:
        if 'production_plugins = [' in cell.source:
            cell.source = cell.source.replace('production_plugins = [', 'production_plugins = [\n    rate_limit_plugin,\n    audit_log_plugin,')
    if cell.cell_type == 'code' and 'await run_attacks' in cell.source:
        cell.source += "\naudit_log_plugin.export_json()\naudit_log_plugin.check_alerts(production_plugins)"

# 4. Execute using NotebookClient for better control
client = NotebookClient(nb, timeout=600, kernel_name='python3', resources={'metadata': {'path': 'notebook/'}})

print("Starting execution cell by cell...")
with client.setup_kernel():
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == 'code':
            print(f"Executing cell {i+1}/{len(nb.cells)}...")
            try:
                client.execute_cell(cell, i)
            except Exception as e:
                print(f"Error in cell {i+1}: {e}")
                # Optional: break if error is critical
        
# Save the notebook
with open(output_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)
print(f"Executed notebook saved to {output_path}")

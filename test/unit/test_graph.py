import sys
import os

# Fix path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

try:
    from agents.graph import app
    print("[SUCCESS] Graph compiled successfully!")
    print("Nodes:", app.get_graph().nodes.keys())
except Exception as e:
    print(f"[ERROR] Graph Error: {e}")
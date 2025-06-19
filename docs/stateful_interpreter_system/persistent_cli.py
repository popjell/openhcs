import sys
import json
from pathlib import Path
from datetime import datetime, timezone

class PersistentCLI:
    def __init__(self, state_file="cli_state.json"):
        self.state_file = Path(state_file)
        self.state = self._load_state()
        
    def _load_state(self):
        default_state = {
            "message_count": 0,
            "session_start": 0,
            "input_log": {},
            "key_store": {},
            "metrics": {},
            "objectives": {}
        }
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                # Ensure all keys exist
                for key in default_state:
                    if key not in state:
                        state[key] = default_state[key]
                return state
        except FileNotFoundError:
            return default_state
    
    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
        
    def process_input(self, input_str):
        self.state["message_count"] += 1
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Store command with timestamp
        self.state["input_log"][f"msg_{self.state['message_count']}"] = {
            "command": input_str,
            "timestamp": timestamp
        }
        
        # Framework commands
        if input_str.strip() == "count":
            response = f"Message count: {self.state['message_count']} (session: {self.state['message_count'] - self.state['session_start']})"
        elif input_str.startswith("mem:set "):
            parts = input_str[8:].split('=', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                self.state["key_store"][key] = value
                response = f"Set {key} = {value}"
            else:
                response = "Invalid format. Use: mem:set key=value"
        elif input_str.startswith("mem:get "):
            key = input_str[8:].strip()
            response = self.state["key_store"].get(key, "Not found")
        elif input_str.startswith("metric:set "):
            parts = input_str[11:].split('=', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                try:
                    value = float(parts[1].strip())
                    self.state["metrics"][key] = value
                    response = f"Metric set: {极ey} = {value}"
                except ValueError:
                    response = "Metric value must be a number"
            else:
                response = "Invalid format. Use: metric:set key=value"
        elif input_str.startswith("metric:get "):
            key = input_str[11:].strip()
            response = str(self.state["metrics"].get(key, "Not found"))
        elif input_str.startswith("objective:set "):
            parts = input_str[14:].split('=', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                try:
                    value = float(parts[1].strip())
                    self.state["objectives"][key] = value
                    response = f"Objective set: {key} = {value}"
                except ValueError:
                    response = "Objective value must be a number"
            else:
                response = "Invalid format. Use: objective:set key=value"
        elif input_str == "progress":
            response = self._get_progress_report()
        elif input_str == "metrics":
            response = self._get_metrics()
        else:
            response = f"Processed: {input_str}"
            
        self._save_state()
        return response
        
    def _get_metrics(self):
        return json.dumps({
            "system_metrics": {
                "total_messages": self.state["message_count"],
                "session_messages": self.state["message_count"] - self.state["session_start"],
                "input_log_entries": len(self.state["input_log"]),
                "key_store_entries": len(self.state["key_store"])
            },
            "custom_metrics": self.state["metrics"],
            "objectives": self.state["objectives"]
        }, indent=2)
        
    def _get_progress_report(self):
        report = "Progress Report:\n"
        for objective, target in self.state["objectives"].items():
            current = self.state["metrics"].get(objective, 0)
            progress = min(100, (current / target) * 100) if target != 0 else 0
            report += f"- {objective}: {current}/{target} ({progress:.1f}%)\n"
        return report

def main():
    cli = PersistentCLI()
    if len(sys.argv) > 1:
        # Non-interactive mode
        command = " ".join(sys.argv[1:])
        response = cli.process_input(command)
        print(response)
    else:
        # Interactive mode
        print("Persistent CLI started. Type 'exit' to quit.")
        while True:
            user_input = input("> ")
            if user_input.strip().lower() == "exit":
                break
            response = cli.process_input(user_input)
            print(response)

if __name__ == "__main__":
    main()

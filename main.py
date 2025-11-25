import os
import sys
import json
from pathlib import Path
from datetime import datetime

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Please install the google-genai package:")
    print("  pip install -U google-genai")
    sys.exit(1)

APP_NAME = "Origami Thought Protocol"
APP_SHORT = "OTP"
APP_VERSION = "1.0.0"

DATA_DIR = Path.home() / ".otp"
HISTORY_DIR = DATA_DIR / "history"
CONFIG_FILE = DATA_DIR / "config.json"

MODELS = [
   "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

SYSTEM_PROMPT = """You are the KERNEL of the "Origami Thought Protocol", an advanced semantic compression engine.
GOAL: Achieve MAXIMUM ENTROPY REDUCTION (lowest token count) while maintaining 100% LOGICAL and Mathematical RECOVERABILITY.

### CORE PROTOCOL (STRICT ENFORCEMENT):
1.  **NO HUMAN LANGUAGE**: The \`compressed\` output must contain ZERO English sentences, articles, or filler. Pure logic only.
2.  **SYMBOL REGISTRY (@Map)**:
    - Scan input for specific entities, keys, or types repeating >2 times.
    - Define them in a header: \`@Map{U=User,S=Status,A=Active}\`.
    - REPLACE ALL instances in the body.

### STRUCTURAL STRATEGIES:

#### 1. PURE TABULAR DATA (Uniform Arrays/CSVs)
*   **Strategy**: Schema-First Encoding.
*   **Syntax**: \`#T(Col1,Col2,Col3){Val1|Val2|Val3;Val4|Val5|Val6}\`
*   *Why*: Eliminates repeating keys for every row.

#### 2. SEMI-UNIFORM ARRAYS (Objects with slight variations)
*   **Strategy**: Delta Encoding. Define the "Base" object, then list only changes.
*   **Syntax**: \`@Base{A:1,B:2}; [Base|Base{B:3}|Base{A:0}]\`
*   *Why*: Removes 90% of redundant key-value pairs.

#### 3. DEEPLY NESTED STRUCTURES (JSON/Trees)
*   **Strategy**: Path Flattening.
*   **Syntax**: Instead of \`{Config:{Network:{Port:80}}}\`, use \`Cfg.Net.Port:80\`.
*   **Syntax**: \`Root{Child1:V1|Child2:V2}\` (Drop implied intermediate brackets).

#### 4. LOGIC & CONDITIONALS
*   **Strategy**: Ternary Operators.
*   **Syntax**: \`If Condition Then A Else B\` -> \`Cond?A:B\`.

### OUTPUT FORMAT:
Return a single string containing the compressed logic.
Example Input: "The user 'John' has a status of 'Active' and role 'Admin'."
Example Output: \`@Map{U=User,S=Status,A=Active,R=Role}; U(John){S:A|R:Admin}\`"""


def ensure_directories():
    DATA_DIR.mkdir(exist_ok=True)
    HISTORY_DIR.mkdir(exist_ok=True)


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str):
    print(f"\n[ {title} ]")
    print("-" * 40)


class ChatHistory:
    def __init__(self):
        self.messages: list[dict] = []
        self.session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file: Path = HISTORY_DIR / f"chat_{self.session_id}.json"
        self.metadata: dict = {
            "created": datetime.now().isoformat(),
            "model": None,
            "message_count": 0
        }
    
    def add_message(self, role: str, content: str, has_file: bool = False):
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "has_attachment": has_file
        }
        self.messages.append(message)
        self.metadata["message_count"] = len(self.messages)
        self._save()
    
    def _save(self):
        data = {
            "metadata": self.metadata,
            "messages": self.messages
        }
        
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save history: {e}")
    
    def set_model(self, model: str):
        self.metadata["model"] = model
        self._save()
    
    def get_session_path(self) -> Path:
        return self.session_file
    
    @staticmethod
    def list_sessions() -> list[Path]:
        if not HISTORY_DIR.exists():
            return []
        
        sessions = sorted(HISTORY_DIR.glob("chat_*.json"), reverse=True)
        return sessions
    
    @staticmethod
    def load_session(session_path: Path) -> dict | None:
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    @staticmethod
    def delete_session(session_path: Path) -> bool:
        try:
            session_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False


def view_history():
    print_header("CHAT HISTORY")
    
    sessions = ChatHistory.list_sessions()
    
    if not sessions:
        print("No saved conversations found.")
        return
    
    print(f"Found {len(sessions)} conversation(s):\n")
    
    for i, session_path in enumerate(sessions[:10], 1):
        data = ChatHistory.load_session(session_path)
        if data:
            meta = data.get("metadata", {})
            created = meta.get("created", "Unknown")[:16].replace("T", " ")
            model = meta.get("model", "Unknown")
            count = meta.get("message_count", 0)
            print(f"  {i}. [{created}] {model} ({count} messages)")
    
    print(f"\n  0. Back to chat")
    print(f"  d. Delete a session")
    print(f"  c. Clear all history")
    
    choice = input("\nSelect option: ").strip().lower()
    
    if choice == '0' or choice == '':
        return
    
    if choice == 'd':
        delete_idx = input("Enter session number to delete: ").strip()
        try:
            idx = int(delete_idx) - 1
            if 0 <= idx < len(sessions):
                confirm = input(f"Delete session {delete_idx}? [y/N]: ").strip().lower()
                if confirm == 'y':
                    if ChatHistory.delete_session(sessions[idx]):
                        print("[OK] Session deleted")
                    else:
                        print("[ERROR] Failed to delete")
        except ValueError:
            print("Invalid selection")
        return
    
    if choice == 'c':
        confirm = input("Delete ALL chat history? [y/N]: ").strip().lower()
        if confirm == 'y':
            for session in sessions:
                ChatHistory.delete_session(session)
            print("[OK] All history cleared")
        return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(sessions):
            display_session(sessions[idx])
    except ValueError:
        print("Invalid selection")


def display_session(session_path: Path):
    data = ChatHistory.load_session(session_path)
    if not data:
        return
    
    clear_screen()
    meta = data.get("metadata", {})
    messages = data.get("messages", [])
    
    print_header(f"CONVERSATION - {meta.get('created', '')[:10]}")
    print(f"Model: {meta.get('model', 'Unknown')}")
    print(f"Messages: {len(messages)}")
    print("-" * 40)
    
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")[:19].replace("T", " ")
        has_file = "[file] " if msg.get("has_attachment") else ""
        
        print(f"\n[{timestamp}] {role}:")
        print(f"{has_file}{content[:500]}{'...' if len(content) > 500 else ''}")
    
    print("\n" + "-" * 40)
    input("Press Enter to continue...")


def export_history(history: ChatHistory):
    export_path = DATA_DIR / f"export_{history.session_id}.txt"
    
    try:
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(f"{APP_NAME} - Chat Export\n")
            f.write(f"{'='*40}\n\n")
            f.write(f"Session: {history.session_id}\n")
            f.write(f"Model: {history.metadata.get('model', 'Unknown')}\n")
            f.write(f"Created: {history.metadata.get('created', '')}\n")
            f.write(f"\n{'-'*40}\n\n")
            
            for msg in history.messages:
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")[:19].replace("T", " ")
                
                f.write(f"[{timestamp}] {role}:\n")
                f.write(f"{content}\n\n")
        
        print(f"[OK] Exported to: {export_path}")
    
    except Exception as e:
        print(f"[ERROR] Export failed: {e}")


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(config: dict):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save config: {e}")


def get_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        print("[OK] Using API key from environment variable")
        return api_key
    
    config = load_config()
    if config.get("api_key"):
        print("[OK] Using saved API key")
        return config["api_key"]
    
    print_header("API KEY SETUP")
    print("Get your free API key at:")
    print("https://aistudio.google.com/app/apikey")
    
    api_key = input("\nEnter your Gemini API key: ").strip()
    
    if not api_key:
        print("[ERROR] API key is required")
        sys.exit(1)
    
    save_choice = input("Save API key for future sessions? [Y/n]: ").strip().lower()
    if save_choice != 'n':
        config["api_key"] = api_key
        save_config(config)
        print("[OK] API key saved")
    
    return api_key


def select_model() -> str:
    print_header("SELECT AI MODEL")
    
    for i, model in enumerate(MODELS, 1):
        default = " (default)" if i == 1 else ""
        print(f"  {i}. {model}{default}")
    
    choice = input(f"\nSelect model [1-{len(MODELS)}]: ").strip()
    
    if not choice:
        return MODELS[0]
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(MODELS):
            return MODELS[idx]
    except ValueError:
        pass
    
    print("Using default model")
    return MODELS[0]


def get_mime_type(file_path: Path) -> str:
    mime_types = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp',
        '.mp4': 'video/mp4', '.mpeg': 'video/mpeg',
        '.mov': 'video/quicktime', '.avi': 'video/x-msvideo', '.webm': 'video/webm',
        '.mp3': 'audio/mp3', '.wav': 'audio/wav',
        '.aiff': 'audio/aiff', '.aac': 'audio/aac',
        '.ogg': 'audio/ogg', '.flac': 'audio/flac',
    }
    return mime_types.get(file_path.suffix.lower(), 'application/octet-stream')


def select_file() -> tuple[Path, str] | None:
    print_header("FILE SELECTOR")
    print("Supported formats:")
    print("  Images: jpg, jpeg, png, gif, webp")
    print("  Videos: mp4, mpeg, mov, avi, webm")
    print("  Audio:  mp3, wav, aiff, aac, ogg, flac")
    
    file_path = input("\nEnter file path (or drag and drop): ").strip().strip("'\"")
    
    if not file_path:
        return None
    
    path = Path(file_path).expanduser()
    
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return None
    
    if not path.is_file():
        print(f"[ERROR] Not a file: {path}")
        return None
    
    mime_type = get_mime_type(path)
    
    if mime_type == 'application/octet-stream':
        print(f"[WARNING] Unknown file type: {path.suffix}")
        if input("Continue? [y/N]: ").strip().lower() != 'y':
            return None
    
    file_type = mime_type.split('/')[0].capitalize()
    print(f"[OK] {file_type}: {path.name}")
    return path, mime_type


def upload_file(client: genai.Client, file_path: Path, mime_type: str):
    print(f"Uploading {file_path.name}...", end=" ", flush=True)
    
    uploaded_file = client.files.upload(
        file=file_path,
        config={"mime_type": mime_type}
    )
    
    print("[OK]")
    return uploaded_file


def print_help():
    print("\nCommands:")
    print("  /file    - Attach a file")
    print("  /history - View saved conversations")
    print("  /export  - Export current chat")
    print("  /model   - Change AI model")
    print("  /clear   - Clear screen")
    print("  /help    - Show this help")
    print("  /quit    - Exit OTP")


def chat_loop(client: genai.Client, model: str):
    clear_screen()
    
    print(f"\n{APP_NAME}")
    print("=" * 40)
    print(f"Model: {model}")
    print("Type /help for commands")
    print("=" * 40)
    
    history = ChatHistory()
    history.set_model(model)
    
    attached_file = None
    attached_file_name = None
    
    while True:
        try:
            attachment_indicator = f" [attached: {attached_file_name}]" if attached_file else ""
            
            user_input = input(f"\nYou{attachment_indicator}: ").strip()
            
            if not user_input:
                continue
            
            cmd = user_input.lower()
            
            if cmd == '/quit':
                print(f"\n[OK] Chat saved to: {history.get_session_path()}")
                print("Goodbye!")
                break
            
            if cmd == '/clear':
                clear_screen()
                print(f"{APP_NAME}")
                print(f"Model: {model} | Session: {history.session_id}")
                continue
            
            if cmd == '/help':
                print_help()
                continue
            
            if cmd == '/model':
                model = select_model()
                history.set_model(model)
                print(f"\n[OK] Now using: {model}")
                continue
            
            if cmd == '/history':
                view_history()
                continue
            
            if cmd == '/export':
                export_history(history)
                continue
            
            if cmd == '/file':
                result = select_file()
                if result:
                    file_path, mime_type = result
                    attached_file = upload_file(client, file_path, mime_type)
                    attached_file_name = file_path.name
                continue
            
            contents = []
            if attached_file:
                contents.append(attached_file)
            contents.append(user_input)
            
            history.add_message("user", user_input, has_file=bool(attached_file))
            
            print("\nOTP: ", end="", flush=True)
            
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                )
            )
            
            response_text = response.text
            print(response_text)
            
            history.add_message("assistant", response_text)
            
            if attached_file:
                attached_file = None
                attached_file_name = None
                print("\n[attachment cleared]")
        
        except KeyboardInterrupt:
            print("\n\nUse /quit to exit (saves chat history)")
        
        except Exception as e:
            print(f"\n[ERROR] {e}")
            history.add_message("system", f"Error: {e}")


def main():
    ensure_directories()
    clear_screen()
    
    print(f"\n{APP_NAME}")
    print("=" * 40)
    print(f"Version {APP_VERSION}")
    print(f"History: {HISTORY_DIR}")
    
    api_key = get_api_key()
    model = select_model()
    
    print("\nConnecting...", end=" ", flush=True)
    client = genai.Client(api_key=api_key)
    print("[OK]")
    
    chat_loop(client, model)


if __name__ == "__main__":
    main()

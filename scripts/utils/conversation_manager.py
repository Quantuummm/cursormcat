"""
Conversation Manager
--------------------
Manages conversation persistence across sessions to save on API usage and context windows.

Features:
- Save/load conversation history
- Automatic context summarization when conversations get too long
- Session restoration with context reconstruction
- Cross-session memory for AI agents

Usage:
    from utils.conversation_manager import ConversationManager
    
    manager = ConversationManager(session_id="user_123")
    manager.add_message("user", "What are the phases of mitosis?")
    manager.add_message("assistant", "The phases are: prophase, metaphase...")
    manager.save()
    
    # Later session:
    manager = ConversationManager(session_id="user_123")
    history = manager.get_history()
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONVERSATIONS_DIR = PROJECT_ROOT / "logs" / "conversations"
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


class ConversationManager:
    """
    Manages conversation history and context across multiple sessions.
    """
    
    def __init__(self, session_id: Optional[str] = None, max_messages: int = 100):
        """
        Initialize conversation manager.
        
        Args:
            session_id: Unique identifier for this conversation thread
            max_messages: Maximum messages to keep before summarizing
        """
        self.session_id = session_id or self._generate_session_id()
        self.max_messages = max_messages
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "message_count": 0,
            "summarized": False,
        }
        self._load()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID based on timestamp."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:16]
    
    def _get_file_path(self) -> Path:
        """Get the file path for this session's data."""
        return CONVERSATIONS_DIR / f"session_{self.session_id}.json"
    
    def _load(self) -> None:
        """Load conversation history from disk if it exists."""
        file_path = self._get_file_path()
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = data.get("messages", [])
                    self.metadata = data.get("metadata", self.metadata)
                    print(f"📂 Loaded conversation: {len(self.messages)} messages")
            except Exception as e:
                print(f"⚠️  Failed to load conversation: {e}")
    
    def save(self) -> None:
        """Save conversation history to disk."""
        self.metadata["last_updated"] = datetime.now().isoformat()
        self.metadata["message_count"] = len(self.messages)
        
        data = {
            "session_id": self.session_id,
            "messages": self.messages,
            "metadata": self.metadata
        }
        
        file_path = self._get_file_path()
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved conversation: {len(self.messages)} messages -> {file_path.name}")
        except Exception as e:
            print(f"⚠️  Failed to save conversation: {e}")
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Add a message to the conversation.
        
        Args:
            role: 'user', 'assistant', or 'system'
            content: The message content
            metadata: Optional metadata (phase, tokens, cost, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        
        # Auto-save after each message
        if len(self.messages) % 10 == 0:  # Save every 10 messages
            self.save()
        
        # Check if we need to summarize
        if len(self.messages) > self.max_messages and not self.metadata.get("summarized"):
            self._trigger_summarization_warning()
    
    def _trigger_summarization_warning(self) -> None:
        """Warn that conversation should be summarized."""
        print(f"\n⚠️  Conversation has {len(self.messages)} messages.")
        print("   Consider summarizing with: manager.summarize_and_compress()")
    
    def get_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            last_n: If provided, return only the last N messages
            
        Returns:
            List of message dictionaries
        """
        if last_n:
            return self.messages[-last_n:]
        return self.messages
    
    def get_formatted_history(self, last_n: Optional[int] = None, include_metadata: bool = False) -> str:
        """
        Get conversation history formatted as a string for context injection.
        
        Args:
            last_n: If provided, include only the last N messages
            include_metadata: Whether to include timestamps and metadata
            
        Returns:
            Formatted conversation string
        """
        messages = self.get_history(last_n)
        formatted = []
        
        for msg in messages:
            if include_metadata:
                formatted.append(f"[{msg['timestamp']}] {msg['role'].upper()}: {msg['content']}")
            else:
                formatted.append(f"{msg['role'].upper()}: {msg['content']}")
        
        return "\n\n".join(formatted)
    
    def summarize_and_compress(self, keep_recent: int = 20) -> Dict[str, Any]:
        """
        Summarize older messages and keep only recent ones + summary.
        This should be called with a Gemini client to actually generate the summary.
        
        Args:
            keep_recent: Number of recent messages to keep in full
            
        Returns:
            Summary data for use with Gemini
        """
        if len(self.messages) <= keep_recent:
            return {"summary": None, "kept_messages": self.messages}
        
        # Split into old and recent
        old_messages = self.messages[:-keep_recent]
        recent_messages = self.messages[-keep_recent:]
        
        # Create a summary request (to be used with GeminiClient)
        summary_request = {
            "messages_to_summarize": old_messages,
            "message_count": len(old_messages),
            "time_range": {
                "start": old_messages[0]["timestamp"],
                "end": old_messages[-1]["timestamp"]
            }
        }
        
        return {
            "summary_request": summary_request,
            "recent_messages": recent_messages,
            "compression_info": {
                "original_count": len(self.messages),
                "compressed_to": keep_recent,
                "summarized_count": len(old_messages)
            }
        }
    
    def get_context_for_api(self, max_tokens_estimate: int = 100000) -> Dict[str, Any]:
        """
        Get optimized context for API calls, respecting token limits.
        
        Args:
            max_tokens_estimate: Estimated max tokens (rough: 1 token ≈ 4 chars)
            
        Returns:
            Optimized context dictionary
        """
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = max_tokens_estimate * 4
        
        # Start with most recent messages
        selected_messages = []
        total_chars = 0
        
        for msg in reversed(self.messages):
            msg_chars = len(msg["content"])
            if total_chars + msg_chars > max_chars:
                break
            selected_messages.insert(0, msg)
            total_chars += msg_chars
        
        return {
            "messages": selected_messages,
            "truncated": len(selected_messages) < len(self.messages),
            "total_chars": total_chars,
            "estimated_tokens": total_chars // 4
        }
    
    def clear(self) -> None:
        """Clear all messages and reset conversation."""
        self.messages = []
        self.metadata["message_count"] = 0
        self.metadata["last_updated"] = datetime.now().isoformat()
        self.save()
        print("🗑️  Conversation cleared")
    
    def export_summary(self) -> Dict[str, Any]:
        """Export conversation summary for analysis."""
        return {
            "session_id": self.session_id,
            "metadata": self.metadata,
            "message_count": len(self.messages),
            "roles_breakdown": self._count_by_role(),
            "time_span": self._get_time_span(),
            "estimated_total_tokens": sum(len(m["content"]) for m in self.messages) // 4
        }
    
    def _count_by_role(self) -> Dict[str, int]:
        """Count messages by role."""
        counts = {}
        for msg in self.messages:
            role = msg["role"]
            counts[role] = counts.get(role, 0) + 1
        return counts
    
    def _get_time_span(self) -> Optional[Dict[str, str]]:
        """Get the time span of the conversation."""
        if not self.messages:
            return None
        return {
            "start": self.messages[0]["timestamp"],
            "end": self.messages[-1]["timestamp"]
        }
    
    @staticmethod
    def list_all_sessions() -> List[Dict[str, Any]]:
        """List all saved conversation sessions."""
        sessions = []
        for file_path in CONVERSATIONS_DIR.glob("session_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append({
                        "session_id": data.get("session_id"),
                        "file": file_path.name,
                        "message_count": len(data.get("messages", [])),
                        "last_updated": data.get("metadata", {}).get("last_updated"),
                    })
            except Exception:
                continue
        return sorted(sessions, key=lambda x: x.get("last_updated", ""), reverse=True)
    
    @staticmethod
    def load_session(session_id: str) -> 'ConversationManager':
        """Load an existing conversation session."""
        manager = ConversationManager(session_id=session_id)
        if not manager.messages:
            print(f"⚠️  Session {session_id} not found or empty")
        return manager


def demo_usage():
    """Demonstrate conversation manager usage."""
    print("\n" + "="*60)
    print("Conversation Manager Demo")
    print("="*60 + "\n")
    
    # Create a new conversation
    manager = ConversationManager(session_id="demo_session")
    
    # Simulate a conversation about MCAT Biology
    manager.add_message("user", "What are the phases of mitosis?")
    manager.add_message("assistant", 
        "Mitosis has 4 main phases:\n"
        "1. PROPHASE - Chromatin condenses into chromosomes\n"
        "2. METAPHASE - Chromosomes align at cell equator\n"
        "3. ANAPHASE - Sister chromatids separate\n"
        "4. TELOPHASE - Two nuclei form"
    )
    manager.add_message("user", "What happens during prophase specifically?")
    manager.add_message("assistant",
        "During PROPHASE:\n"
        "- Nuclear envelope breaks down\n"
        "- Chromatin condenses into visible chromosomes\n"
        "- Centrioles move to opposite poles\n"
        "- Spindle fibers begin to form"
    )
    
    manager.save()
    
    print(f"\n✅ Saved conversation with {len(manager.messages)} messages")
    print(f"\nFormatted history:\n{manager.get_formatted_history()}\n")
    
    # List all sessions
    print("\n" + "-"*60)
    print("All saved sessions:")
    for session in ConversationManager.list_all_sessions():
        print(f"  • {session['session_id']}: {session['message_count']} messages "
              f"(updated: {session['last_updated']})")


if __name__ == "__main__":
    demo_usage()

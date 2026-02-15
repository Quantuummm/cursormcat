"""
AI Agent Session Manager
-------------------------
Central script to manage AI agent conversations, context, and session restoration.

This script helps AI agents automatically:
- Resume conversations from previous sessions
- Maintain context across multiple chats
- Optimize API usage through caching and summarization
- Track conversation history without repeated explanations

Usage:
    # Start or resume a session
    python scripts/manage_ai_session.py --session my_project_session
    
    # List all sessions
    python scripts/manage_ai_session.py --list
    
    # Clear a session
    python scripts/manage_ai_session.py --session my_project_session --clear
    
    # Show session stats
    python scripts/manage_ai_session.py --session my_project_session --stats
    
    # Summarize a long session
    python scripts/manage_ai_session.py --session my_project_session --summarize

Integration with AI:
    When starting a new chat, an AI agent should:
    1. Check if there's an active session
    2. Load conversation history
    3. Inject summarized context into the conversation
    4. Continue working without needing re-explanation
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from utils.conversation_manager import ConversationManager
from utils.context_cache import ContextCache
from utils.gemini_client import GeminiClient
from utils.conversation_summarizer import ConversationSummarizer


class AISessionManager:
    """
    Manages AI agent sessions for continuous work across multiple chats.
    """
    
    def __init__(self, session_id: str = None):
        """
        Initialize session manager.
        
        Args:
            session_id: Session identifier (e.g., 'mcat_project', 'biology_phase8')
        """
        self.session_id = session_id or self._get_default_session()
        self.conversation_manager = ConversationManager(session_id=self.session_id)
        self.context_cache = ContextCache()
        self.client = None  # Lazy-loaded when needed
    
    def _get_default_session(self) -> str:
        """Get or create default session ID."""
        # Use project name + date as default
        return f"mcat_project_{datetime.now().strftime('%Y%m%d')}"
    
    def _get_client(self) -> GeminiClient:
        """Lazy-load Gemini client."""
        if not self.client:
            self.client = GeminiClient(enable_caching=True, conversation_id=self.session_id)
        return self.client
    
    def start_session(self) -> dict:
        """
        Start or resume a session.
        
        Returns:
            Session context dictionary for AI agent
        """
        print(f"\n{'='*60}")
        print(f"🚀 AI AGENT SESSION: {self.session_id}")
        print(f"{'='*60}\n")
        
        history = self.conversation_manager.get_history()
        
        if history:
            print(f"📂 Resuming session with {len(history)} messages")
            print(f"   Last activity: {history[-1]['timestamp']}")
            
            # Get optimized context
            context = self._get_session_context()
            
            print(f"\n📊 Session Context:")
            print(f"   Messages: {context['message_count']}")
            print(f"   Summarized: {context['has_summary']}")
            print(f"   Estimated tokens: {context['estimated_tokens']:,}")
            
            return context
        else:
            print(f"📝 Starting new session")
            
            # Initialize with project context
            self._initialize_new_session()
            
            return {
                "session_id": self.session_id,
                "message_count": 0,
                "has_summary": False,
                "context": "New session - no previous history"
            }
    
    def _initialize_new_session(self):
        """Initialize a new session with project context."""
        # Load project status
        try:
            from utils.checkpoint_manager import get_last_checkpoint
            checkpoint = get_last_checkpoint()
            
            if checkpoint:
                context_msg = (
                    f"Project Context:\n"
                    f"- Last activity: {checkpoint.get('phase_name')} (Phase {checkpoint.get('phase')})\n"
                    f"- Target: {checkpoint.get('pdf')} Chapter {checkpoint.get('chapter')}\n"
                    f"- Subject: {checkpoint.get('subject')}\n"
                    f"\nThis session was initialized at {datetime.now().isoformat()}"
                )
                self.conversation_manager.add_message("system", context_msg)
                print(f"✅ Loaded project context from checkpoint")
        except Exception as e:
            print(f"⚠️  Could not load project context: {e}")
    
    def _get_session_context(self) -> dict:
        """Get optimized session context for AI agent."""
        history = self.conversation_manager.get_history()
        
        # Check if we need summarization
        needs_summary = len(history) > 50
        
        if needs_summary:
            # Create optimized context
            summarizer = ConversationSummarizer(self._get_client())
            optimized = summarizer.create_context_optimized_history(
                self.conversation_manager,
                max_tokens=50000  # Keep context manageable
            )
            
            context_text = ""
            if optimized['summary']:
                context_text += optimized['summary'] + "\n\n"
            
            # Add recent messages
            for msg in optimized['recent_messages'][-10:]:  # Last 10 messages
                context_text += f"{msg['role'].upper()}: {msg['content']}\n\n"
            
            return {
                "session_id": self.session_id,
                "message_count": len(history),
                "has_summary": True,
                "summary": optimized['summary'],
                "recent_messages": optimized['recent_messages'][-10:],
                "context": context_text,
                "estimated_tokens": len(context_text) // 4,
                "optimization": optimized['optimization_info']
            }
        else:
            # Return full context
            context_text = self.conversation_manager.get_formatted_history()
            return {
                "session_id": self.session_id,
                "message_count": len(history),
                "has_summary": False,
                "context": context_text,
                "estimated_tokens": len(context_text) // 4
            }
    
    def add_interaction(self, user_message: str, assistant_response: str, metadata: dict = None):
        """
        Add a user-assistant interaction to the session.
        
        Args:
            user_message: User's message/question
            assistant_response: Assistant's response
            metadata: Optional metadata (tokens, cost, phase)
        """
        self.conversation_manager.add_message("user", user_message, metadata)
        self.conversation_manager.add_message("assistant", assistant_response, metadata)
        self.conversation_manager.save()
    
    def summarize_session(self):
        """Manually trigger session summarization."""
        print(f"\n{'='*60}")
        print(f"📝 SUMMARIZING SESSION: {self.session_id}")
        print(f"{'='*60}\n")
        
        summarizer = ConversationSummarizer(self._get_client())
        summary = summarizer.summarize_conversation(self.conversation_manager, keep_recent=20)
        
        # Add summary to conversation
        self.conversation_manager.add_message(
            "system",
            summary,
            metadata={"type": "summary", "timestamp": datetime.now().isoformat()}
        )
        self.conversation_manager.save()
        
        print(f"\n✅ Session summarized and saved")
        return summary
    
    def get_session_stats(self) -> dict:
        """Get statistics about the current session."""
        summary = self.conversation_manager.export_summary()
        cache_stats = self.context_cache.get_stats()
        
        return {
            "session": summary,
            "caching": cache_stats
        }
    
    def print_session_info(self):
        """Print detailed session information."""
        print(f"\n{'='*60}")
        print(f"📊 SESSION INFO: {self.session_id}")
        print(f"{'='*60}\n")
        
        stats = self.get_session_stats()
        session = stats['session']
        caching = stats['caching']
        
        print(f"Messages:")
        print(f"  Total: {session['message_count']}")
        print(f"  By role: {session['roles_breakdown']}")
        
        if session['time_span']:
            print(f"\nTime span:")
            print(f"  Start: {session['time_span']['start']}")
            print(f"  End: {session['time_span']['end']}")
        
        print(f"\nToken estimates:")
        print(f"  Total: {session['estimated_total_tokens']:,}")
        
        print(f"\nContext caching:")
        print(f"  Active caches: {caching['active_caches']}")
        print(f"  Total created: {caching['total_created']}")
        print(f"  Cache hits: {caching['total_hits']}")
        print(f"  Cost savings: ${caching['estimated_cost_savings']:.4f}")
        
        print(f"\n{'='*60}\n")
    
    def clear_session(self):
        """Clear the current session."""
        self.conversation_manager.clear()
        print(f"🗑️  Session {self.session_id} cleared")
    
    @staticmethod
    def list_all_sessions():
        """List all available sessions."""
        print(f"\n{'='*60}")
        print(f"📋 ALL AI AGENT SESSIONS")
        print(f"{'='*60}\n")
        
        sessions = ConversationManager.list_all_sessions()
        
        if not sessions:
            print("📭 No sessions found")
            return
        
        for session in sessions:
            print(f"  • {session['session_id']}")
            print(f"    Messages: {session['message_count']}")
            print(f"    Last updated: {session['last_updated']}")
            print()
        
        print(f"{'='*60}\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Agent Session Manager - Resume conversations and optimize API usage"
    )
    parser.add_argument(
        "--session",
        help="Session ID (e.g., 'mcat_project', 'biology_phase8')"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available sessions"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show session statistics"
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Manually summarize session"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear session history"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume session and print context"
    )
    
    args = parser.parse_args()
    
    # List sessions
    if args.list:
        AISessionManager.list_all_sessions()
        return
    
    # Require session ID for other operations
    if not args.session and not args.list:
        print("❌ Error: --session required (or use --list)")
        print("   Example: python scripts/manage_ai_session.py --session my_project")
        return
    
    # Create session manager
    manager = AISessionManager(session_id=args.session)
    
    # Handle commands
    if args.clear:
        manager.clear_session()
    elif args.stats:
        manager.print_session_info()
    elif args.summarize:
        manager.summarize_session()
    elif args.resume:
        context = manager.start_session()
        print("\n📄 Context for AI agent:\n")
        print(context.get('context', 'No context available'))
    else:
        # Default: start/resume session
        manager.start_session()
        print("\n✅ Session ready. Use --stats, --summarize, or --clear for more options.")


if __name__ == "__main__":
    main()

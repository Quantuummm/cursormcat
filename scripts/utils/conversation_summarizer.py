"""
Conversation Summarization Utility
-----------------------------------
Automatically summarizes long conversations to reduce context window usage.

Features:
- Intelligent summarization of message history
- Preserves key information while compressing context
- Reduces token usage by up to 80%
- Maintains conversation continuity across sessions

Usage:
    from utils.conversation_summarizer import ConversationSummarizer
    from utils.conversation_manager import ConversationManager
    from utils.gemini_client import GeminiClient
    
    manager = ConversationManager(session_id="user_123")
    client = GeminiClient()
    summarizer = ConversationSummarizer(client)
    
    # When conversation gets long (>50 messages)
    summary = summarizer.summarize_conversation(manager)
    manager.add_message("system", summary, metadata={"type": "summary"})
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConversationSummarizer:
    """
    Summarizes conversations to reduce context window usage.
    """
    
    def __init__(self, gemini_client):
        """
        Initialize summarizer with a Gemini client.
        
        Args:
            gemini_client: GeminiClient instance for API calls
        """
        self.client = gemini_client
    
    def summarize_conversation(
        self, 
        conversation_manager,
        keep_recent: int = 20,
        compression_ratio: float = 0.2
    ) -> str:
        """
        Summarize a conversation, keeping only recent messages + summary.
        
        Args:
            conversation_manager: ConversationManager instance
            keep_recent: Number of recent messages to keep in full
            compression_ratio: Target compression ratio (0.2 = compress to 20% of original)
            
        Returns:
            Summary text
        """
        messages = conversation_manager.get_history()
        
        if len(messages) <= keep_recent:
            return "No summarization needed - conversation is short enough."
        
        # Split into old and recent
        old_messages = messages[:-keep_recent]
        
        # Create summarization prompt
        conversation_text = self._format_messages_for_summary(old_messages)
        
        prompt = f"""
Summarize the following conversation history concisely while preserving all critical information.

Focus on:
- Key topics discussed
- Important questions asked and answers provided
- Decisions made or conclusions reached
- Context needed for understanding future messages

Original message count: {len(old_messages)}
Target summary length: {int(len(conversation_text) * compression_ratio)} characters

CONVERSATION TO SUMMARIZE:
{conversation_text}

Provide a structured summary in JSON format:
{{
    "summary": "Concise narrative summary of the conversation",
    "key_topics": ["topic1", "topic2", ...],
    "important_facts": ["fact1", "fact2", ...],
    "open_questions": ["question1", "question2", ...],
    "context_for_continuation": "What an AI agent needs to know to continue this conversation"
}}
"""
        
        try:
            print(f"🤖 Summarizing {len(old_messages)} messages...")
            result = self.client.enrich(prompt, phase="conversation_summary")
            
            if isinstance(result, dict):
                summary_obj = result
            else:
                summary_obj = json.loads(result)
            
            # Format summary for context injection
            formatted_summary = self._format_summary(summary_obj, len(old_messages))
            
            print(f"✅ Summarized {len(old_messages)} messages → {len(formatted_summary)} chars "
                  f"({int(100 * len(formatted_summary) / len(conversation_text))}% of original)")
            
            return formatted_summary
            
        except Exception as e:
            print(f"❌ Failed to summarize conversation: {e}")
            # Fallback: simple truncation
            return self._simple_summary(old_messages)
    
    def _format_messages_for_summary(self, messages: List[Dict]) -> str:
        """Format messages for summarization."""
        formatted = []
        for i, msg in enumerate(messages, 1):
            role = msg['role'].upper()
            content = msg['content']
            formatted.append(f"[{i}] {role}: {content}")
        return "\n\n".join(formatted)
    
    def _format_summary(self, summary_obj: Dict, message_count: int) -> str:
        """Format summary object into readable text."""
        parts = [
            f"=== CONVERSATION SUMMARY (compressed from {message_count} messages) ===",
            "",
            f"OVERVIEW: {summary_obj.get('summary', 'N/A')}",
            "",
            "KEY TOPICS:",
        ]
        
        for topic in summary_obj.get('key_topics', []):
            parts.append(f"  • {topic}")
        
        parts.append("")
        parts.append("IMPORTANT FACTS:")
        for fact in summary_obj.get('important_facts', []):
            parts.append(f"  • {fact}")
        
        if summary_obj.get('open_questions'):
            parts.append("")
            parts.append("OPEN QUESTIONS:")
            for question in summary_obj['open_questions']:
                parts.append(f"  • {question}")
        
        parts.append("")
        parts.append(f"CONTEXT: {summary_obj.get('context_for_continuation', 'N/A')}")
        parts.append("=" * 70)
        
        return "\n".join(parts)
    
    def _simple_summary(self, messages: List[Dict]) -> str:
        """Fallback: Simple summary without AI."""
        topics = set()
        user_msgs = 0
        assistant_msgs = 0
        
        for msg in messages:
            if msg['role'] == 'user':
                user_msgs += 1
            elif msg['role'] == 'assistant':
                assistant_msgs += 1
            
            # Extract potential topics (very basic)
            content = msg['content'].lower()
            for keyword in ['chapter', 'phase', 'mitosis', 'biology', 'chemistry', 'physics']:
                if keyword in content:
                    topics.add(keyword)
        
        return (
            f"=== CONVERSATION SUMMARY (compressed from {len(messages)} messages) ===\n"
            f"Messages: {user_msgs} user, {assistant_msgs} assistant\n"
            f"Potential topics: {', '.join(sorted(topics)) if topics else 'N/A'}\n"
            f"Time span: {messages[0]['timestamp']} to {messages[-1]['timestamp']}\n"
            f"{'=' * 70}"
        )
    
    def create_context_optimized_history(
        self,
        conversation_manager,
        max_tokens: int = 50000
    ) -> Dict[str, Any]:
        """
        Create an optimized conversation history that fits within token limits.
        
        Args:
            conversation_manager: ConversationManager instance
            max_tokens: Maximum tokens to use (rough estimate: 1 token ≈ 4 chars)
            
        Returns:
            Optimized context dictionary
        """
        max_chars = max_tokens * 4
        messages = conversation_manager.get_history()
        
        # Strategy: Keep system messages + summary + recent messages
        system_messages = [m for m in messages if m['role'] == 'system']
        non_system_messages = [m for m in messages if m['role'] != 'system']
        
        # Calculate space available
        system_chars = sum(len(m['content']) for m in system_messages)
        available_chars = max_chars - system_chars
        
        # Fit as many recent messages as possible
        selected_messages = []
        current_chars = 0
        
        for msg in reversed(non_system_messages):
            msg_chars = len(msg['content'])
            if current_chars + msg_chars > available_chars:
                # Need to summarize older messages
                break
            selected_messages.insert(0, msg)
            current_chars += msg_chars
        
        # If we couldn't fit all messages, create a summary of the rest
        omitted_count = len(non_system_messages) - len(selected_messages)
        summary_text = None
        
        if omitted_count > 0:
            omitted_messages = non_system_messages[:-len(selected_messages)]
            summary_text = self.summarize_conversation_simple(omitted_messages)
        
        return {
            "system_messages": system_messages,
            "summary": summary_text,
            "recent_messages": selected_messages,
            "optimization_info": {
                "total_messages": len(messages),
                "omitted_count": omitted_count,
                "selected_count": len(selected_messages),
                "estimated_tokens": current_chars // 4
            }
        }
    
    def summarize_conversation_simple(self, messages: List[Dict]) -> str:
        """Quick non-AI summary for internal optimization."""
        if not messages:
            return ""
        
        user_questions = []
        assistant_responses = []
        
        for msg in messages:
            if msg['role'] == 'user':
                # Extract first sentence as question
                content = msg['content'].split('.')[0][:100]
                user_questions.append(content)
            elif msg['role'] == 'assistant':
                # Extract first sentence as response
                content = msg['content'].split('.')[0][:100]
                assistant_responses.append(content)
        
        return (
            f"[Earlier conversation: {len(messages)} messages]\n"
            f"Topics discussed: {', '.join(user_questions[:3])}...\n"
            f"Key responses: {', '.join(assistant_responses[:3])}..."
        )


def demo_usage():
    """Demonstrate conversation summarization."""
    print("\n" + "="*60)
    print("Conversation Summarization Demo")
    print("="*60 + "\n")
    
    # This would normally use actual GeminiClient and ConversationManager
    print("Demo: Summarization would compress 100 messages down to ~20 messages + summary")
    print("      Typical compression: 80% token reduction")
    print("      Cost savings: ~80% on context tokens")
    print("\nExample workflow:")
    print("  1. Detect when conversation > 50 messages")
    print("  2. Summarize oldest 30 messages")
    print("  3. Keep summary + 20 recent messages")
    print("  4. Continue conversation with optimized context")
    print("\n✅ This enables unlimited conversation length while maintaining low costs")


if __name__ == "__main__":
    demo_usage()

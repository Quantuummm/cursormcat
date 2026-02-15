"""
Example: Using API Optimization Features Together
--------------------------------------------------
This script demonstrates how to use all the new optimization features:
- Context caching
- Conversation persistence
- Automatic summarization

Perfect template for AI agents to understand the full workflow.
"""

import sys
from pathlib import Path

# Setup path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from utils.gemini_client import GeminiClient
from utils.conversation_manager import ConversationManager
from utils.conversation_summarizer import ConversationSummarizer
from utils.context_cache import ContextCache


def example_pipeline_with_caching():
    """
    Example: Run a pipeline phase with context caching enabled.
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Pipeline with Context Caching")
    print("="*60 + "\n")
    
    # Initialize client with caching enabled
    client = GeminiClient(
        enable_caching=True,
        conversation_id="example_phase8_biology"
    )
    
    print("✅ GeminiClient initialized with caching enabled")
    
    # Example: Large prompt that would be reused
    large_prompt_template = """
    You are extracting content from an MCAT biology textbook.
    
    [... This would be 50KB+ of detailed instructions ...]
    
    Extract sections in this format: {...}
    """ * 100  # Simulate large prompt
    
    print(f"📝 Prompt size: {len(large_prompt_template):,} chars (~{len(large_prompt_template)//4:,} tokens)")
    
    # In real usage:
    # cached_content = client.create_cached_prompt(
    #     phase="P3_sections",
    #     model_name="gemini-3-flash-preview",
    #     system_instruction="MCAT extraction instructions...",
    #     static_content=[large_prompt_template],
    #     ttl_seconds=3600
    # )
    
    print("\n✅ Would create cached context (one-time $0.20/1M cost)")
    print("   Subsequent calls: $0.02/1M (10x cheaper!)")
    
    # Show cost summary
    client.print_cost_summary()


def example_conversation_persistence():
    """
    Example: Track a conversation across multiple sessions.
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Conversation Persistence")
    print("="*60 + "\n")
    
    # Create or resume conversation
    manager = ConversationManager(session_id="example_biology_work")
    
    print(f"📂 Session: {manager.session_id}")
    print(f"   Messages: {len(manager.messages)}")
    
    # Simulate a conversation
    if len(manager.messages) == 0:
        print("\n💬 Starting new conversation...")
        
        manager.add_message("user", "How do I run phase 8 for biology?")
        manager.add_message(
            "assistant",
            "Run: python phases/phase8/phase8_restructure_guided_learning.py biology.pdf\n"
            "This will restructure all sections into guided learning format."
        )
        
        manager.add_message("user", "What if I only want to process chapter 3?")
        manager.add_message(
            "assistant",
            "Add chapter number: python phases/phase8/phase8_restructure_guided_learning.py biology.pdf 3"
        )
        
        manager.save()
        print("✅ Conversation saved")
    else:
        print("\n📝 Resuming existing conversation...")
    
    # Get formatted history
    history = manager.get_formatted_history(last_n=5)
    print("\n📄 Recent conversation:\n")
    print(history)
    
    # Get optimized context for API
    context = manager.get_context_for_api(max_tokens_estimate=10000)
    print(f"\n📊 Optimized context:")
    print(f"   Messages included: {len(context['messages'])}")
    print(f"   Estimated tokens: {context['estimated_tokens']:,}")
    print(f"   Truncated: {context['truncated']}")


def example_conversation_summarization():
    """
    Example: Summarize a long conversation.
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Conversation Summarization")
    print("="*60 + "\n")
    
    # Create a conversation with many messages
    manager = ConversationManager(session_id="example_long_conversation")
    
    # Simulate 60 messages
    if len(manager.messages) < 60:
        print("📝 Creating demo conversation with 60 messages...")
        
        for i in range(30):
            manager.add_message("user", f"Question {i+1}: How does [biology concept {i}] work?")
            manager.add_message("assistant", f"Answer {i+1}: [Detailed explanation of concept {i}]...")
        
        manager.save()
    
    print(f"📊 Conversation stats:")
    print(f"   Total messages: {len(manager.messages)}")
    
    # Check if summarization is needed
    if len(manager.messages) > 50:
        print(f"   ⚠️  Conversation is long (>{len(manager.messages)} messages)")
        print(f"   💡 Summarization recommended to reduce context size")
        
        # Demo: Get summarization data (would normally use AI)
        summary_data = manager.summarize_and_compress(keep_recent=20)
        
        print(f"\n📦 Compression info:")
        print(f"   Original: {summary_data['compression_info']['original_count']} messages")
        print(f"   Compressed to: {summary_data['compression_info']['compressed_to']} messages + summary")
        print(f"   Messages to summarize: {summary_data['compression_info']['summarized_count']}")
        
        # In real usage with GeminiClient:
        # client = GeminiClient()
        # summarizer = ConversationSummarizer(client)
        # summary_text = summarizer.summarize_conversation(manager, keep_recent=20)
        # manager.add_message("system", summary_text)
        
        print("\n✅ Would create AI summary of old messages")
        print("   Result: 80% token reduction while preserving all key information")


def example_full_ai_session():
    """
    Example: Complete AI agent session workflow.
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Complete AI Agent Session")
    print("="*60 + "\n")
    
    from scripts.manage_ai_session import AISessionManager
    
    # Start or resume session
    session = AISessionManager(session_id="example_agent_work")
    context = session.start_session()
    
    print(f"\n📄 Session context available:")
    print(f"   Message count: {context['message_count']}")
    print(f"   Has summary: {context.get('has_summary', False)}")
    
    if context['message_count'] > 0:
        print("\n💡 AI Agent can now continue from where it left off!")
        print("   No need to re-explain the project or context.")
    
    # Simulate work
    session.add_interaction(
        user_message="Run phase 8 for biology chapter 3",
        assistant_response="Completed phase 8 for biology chapter 3. Processed 12 sections.",
        metadata={"phase": 8, "subject": "biology", "chapter": 3, "sections": 12}
    )
    
    # Get stats
    stats = session.get_session_stats()
    print(f"\n📊 Session statistics:")
    print(f"   Total messages: {stats['session']['message_count']}")
    print(f"   Estimated tokens: {stats['session']['estimated_total_tokens']:,}")
    
    if stats['caching']['estimated_cost_savings'] > 0:
        print(f"   💰 Cache savings: ${stats['caching']['estimated_cost_savings']:.4f}")


def example_cost_comparison():
    """
    Example: Show cost comparison with and without optimization.
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Cost Comparison")
    print("="*60 + "\n")
    
    # Scenario: Process 50 sections with large prompts
    sections = 50
    prompt_size_tokens = 100000  # 100K tokens per prompt
    
    print(f"📊 Scenario: Process {sections} sections")
    print(f"   Prompt size: {prompt_size_tokens:,} tokens")
    
    # Without caching
    print(f"\n❌ WITHOUT OPTIMIZATION:")
    total_tokens = prompt_size_tokens * sections
    cost_per_1m = 0.20  # gemini-3-flash-preview input cost
    total_cost = (total_tokens / 1_000_000) * cost_per_1m
    print(f"   Total input tokens: {total_tokens:,}")
    print(f"   Cost: ${total_cost:.2f}")
    
    # With caching
    print(f"\n✅ WITH CACHING:")
    first_call_tokens = prompt_size_tokens
    first_call_cost = (first_call_tokens / 1_000_000) * 0.20
    
    cached_calls_tokens = prompt_size_tokens * (sections - 1)
    cached_calls_cost = (cached_calls_tokens / 1_000_000) * 0.02
    
    total_cost_cached = first_call_cost + cached_calls_cost
    
    print(f"   First call (cache creation): {first_call_tokens:,} tokens @ $0.20/1M = ${first_call_cost:.2f}")
    print(f"   Cached calls (49×): {cached_calls_tokens:,} tokens @ $0.02/1M = ${cached_calls_cost:.2f}")
    print(f"   Total cost: ${total_cost_cached:.2f}")
    
    savings = total_cost - total_cost_cached
    savings_pct = (savings / total_cost) * 100
    
    print(f"\n💰 SAVINGS: ${savings:.2f} ({savings_pct:.0f}%)")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("   API OPTIMIZATION FEATURES - COMPLETE EXAMPLES")
    print("="*70)
    
    try:
        example_pipeline_with_caching()
        example_conversation_persistence()
        example_conversation_summarization()
        example_full_ai_session()
        example_cost_comparison()
        
        print("\n" + "="*70)
        print("✅ ALL EXAMPLES COMPLETED")
        print("="*70)
        print("\n📚 For more details, see: docs/API_OPTIMIZATION_GUIDE.md\n")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

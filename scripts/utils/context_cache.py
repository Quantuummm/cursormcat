"""
Context Caching Utilities for Gemini API
-----------------------------------------
Implements context caching to dramatically reduce API costs and latency.

Gemini supports cached content which can be reused across multiple API calls:
- Cached tokens cost 1/10th of input tokens ($0.02 vs $0.20 per 1M tokens for gemini-3-flash-preview)
- Cached content persists for 1 hour (renewable with each use)
- Minimum cache size: 32,768 tokens (~130KB text)

Usage:
    from utils.context_cache import ContextCache
    
    cache = ContextCache()
    
    # Cache large static context (prompts, PDFs, instructions)
    cached_content = cache.create_cached_context(
        model="gemini-3-flash-preview",
        system_instruction="You are an MCAT biology tutor...",
        contents=["Large PDF content or prompt instructions..."]
    )
    
    # Use cached content in subsequent calls
    response = cache.generate_with_cache(
        cached_content=cached_content,
        new_prompt="Extract sections from chapter 1"
    )
"""

import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "logs" / "context_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_INDEX_FILE = CACHE_DIR / "cache_index.json"


class ContextCache:
    """
    Manages Gemini API context caching for cost optimization.
    
    Gemini caching benefits:
    - Cached input tokens cost ~10x less
    - Reduced latency for repeated context
    - Automatic 1-hour TTL (renewable)
    """
    
    def __init__(self):
        self.cache_index = self._load_index()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load cache index from disk."""
        if CACHE_INDEX_FILE.exists():
            try:
                with open(CACHE_INDEX_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {"caches": {}, "stats": {"total_created": 0, "total_hits": 0, "total_saved_tokens": 0}}
        return {"caches": {}, "stats": {"total_created": 0, "total_hits": 0, "total_saved_tokens": 0}}
    
    def _save_index(self) -> None:
        """Save cache index to disk."""
        try:
            with open(CACHE_INDEX_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save cache index: {e}")
    
    def _generate_cache_key(self, model: str, content: str) -> str:
        """Generate a unique cache key based on model and content."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{model}_{content_hash}"
    
    def create_cached_context(
        self,
        model: str,
        contents: List[str],
        system_instruction: Optional[str] = None,
        ttl_seconds: int = 3600,
        force_refresh: bool = False
    ) -> Optional[Any]:
        """
        Create or retrieve a cached context for reuse.
        
        Args:
            model: Gemini model name (e.g., 'gemini-3-flash-preview')
            contents: List of content strings to cache (prompts, PDFs, instructions)
            system_instruction: Optional system instruction
            ttl_seconds: Time-to-live in seconds (default: 1 hour)
            force_refresh: Force creation of new cache even if existing
            
        Returns:
            CachedContent object if successful, None otherwise
        """
        # Generate cache key
        combined_content = "\n".join(contents)
        if system_instruction:
            combined_content = system_instruction + "\n" + combined_content
        
        cache_key = self._generate_cache_key(model, combined_content)
        
        # Check if cache exists and is still valid
        if not force_refresh and cache_key in self.cache_index["caches"]:
            cache_info = self.cache_index["caches"][cache_key]
            expires_at = datetime.fromisoformat(cache_info["expires_at"])
            
            if datetime.now() < expires_at:
                try:
                    # Retrieve existing cache from Gemini
                    cached_content = genai.caching.CachedContent.get(cache_info["cache_name"])
                    print(f"♻️  Using existing cache: {cache_key} (expires in {int((expires_at - datetime.now()).total_seconds() / 60)} min)")
                    self.cache_index["stats"]["total_hits"] += 1
                    self._save_index()
                    return cached_content
                except Exception as e:
                    print(f"⚠️  Failed to retrieve cache {cache_key}: {e}")
                    # Remove from index if it doesn't exist
                    del self.cache_index["caches"][cache_key]
                    self._save_index()
        
        # Create new cache
        try:
            print(f"🔄 Creating new context cache: {cache_key}")
            
            # Estimate token count (rough: 1 token ≈ 4 chars)
            estimated_tokens = len(combined_content) // 4
            
            # Gemini requires minimum 32,768 tokens for caching
            if estimated_tokens < 32768:
                print(f"⚠️  Content too small for caching ({estimated_tokens:,} tokens < 32,768 minimum)")
                print("   Consider combining multiple prompts or using for larger PDFs.")
                return None
            
            # Create cached content
            cached_content = genai.caching.CachedContent.create(
                model=model,
                contents=contents,
                system_instruction=system_instruction,
                ttl=timedelta(seconds=ttl_seconds)
            )
            
            # Store in index
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            self.cache_index["caches"][cache_key] = {
                "cache_name": cached_content.name,
                "model": model,
                "created_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat(),
                "estimated_tokens": estimated_tokens,
                "content_hash": cache_key
            }
            
            self.cache_index["stats"]["total_created"] += 1
            self._save_index()
            
            print(f"✅ Cache created: {cache_key} ({estimated_tokens:,} tokens cached)")
            print(f"   Expires: {expires_at.strftime('%H:%M:%S')}")
            
            return cached_content
            
        except Exception as e:
            print(f"❌ Failed to create cache: {e}")
            return None
    
    def generate_with_cache(
        self,
        cached_content: Any,
        new_prompt: str,
        temperature: float = 0.1,
        json_mode: bool = True
    ) -> Any:
        """
        Generate content using cached context.
        
        Args:
            cached_content: CachedContent object from create_cached_context
            new_prompt: New prompt to append to cached context
            temperature: Generation temperature
            json_mode: Whether to use JSON response mode
            
        Returns:
            Generated response
        """
        try:
            generation_config = {
                "temperature": temperature,
            }
            if json_mode:
                generation_config["response_mime_type"] = "application/json"
            
            model = genai.GenerativeModel.from_cached_content(
                cached_content=cached_content,
                generation_config=generation_config
            )
            
            response = model.generate_content(new_prompt)
            
            # Track cache hit
            self.cache_index["stats"]["total_hits"] += 1
            if hasattr(cached_content, 'usage_metadata'):
                saved_tokens = getattr(cached_content.usage_metadata, 'cached_token_count', 0)
                self.cache_index["stats"]["total_saved_tokens"] += saved_tokens
            
            self._save_index()
            
            return response
            
        except Exception as e:
            print(f"❌ Failed to generate with cache: {e}")
            raise
    
    def update_cache_ttl(self, cache_key: str, additional_seconds: int = 3600) -> bool:
        """
        Extend the TTL of an existing cache.
        
        Args:
            cache_key: Cache key to update
            additional_seconds: Additional seconds to add to TTL
            
        Returns:
            True if successful, False otherwise
        """
        if cache_key not in self.cache_index["caches"]:
            print(f"⚠️  Cache {cache_key} not found in index")
            return False
        
        try:
            cache_info = self.cache_index["caches"][cache_key]
            cached_content = genai.caching.CachedContent.get(cache_info["cache_name"])
            
            # Update TTL
            cached_content.update(ttl=timedelta(seconds=additional_seconds))
            
            # Update index
            new_expires_at = datetime.now() + timedelta(seconds=additional_seconds)
            self.cache_index["caches"][cache_key]["expires_at"] = new_expires_at.isoformat()
            self._save_index()
            
            print(f"✅ Extended cache TTL: {cache_key} (new expiry: {new_expires_at.strftime('%H:%M:%S')})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update cache TTL: {e}")
            return False
    
    def delete_cache(self, cache_key: str) -> bool:
        """
        Delete a cached context.
        
        Args:
            cache_key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if cache_key not in self.cache_index["caches"]:
            print(f"⚠️  Cache {cache_key} not found")
            return False
        
        try:
            cache_info = self.cache_index["caches"][cache_key]
            cached_content = genai.caching.CachedContent.get(cache_info["cache_name"])
            cached_content.delete()
            
            del self.cache_index["caches"][cache_key]
            self._save_index()
            
            print(f"🗑️  Deleted cache: {cache_key}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete cache: {e}")
            return False
    
    def cleanup_expired_caches(self) -> int:
        """
        Remove expired caches from index and Gemini.
        
        Returns:
            Number of caches cleaned up
        """
        expired_keys = []
        now = datetime.now()
        
        for cache_key, cache_info in self.cache_index["caches"].items():
            expires_at = datetime.fromisoformat(cache_info["expires_at"])
            if now >= expires_at:
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            self.delete_cache(cache_key)
        
        if expired_keys:
            print(f"🧹 Cleaned up {len(expired_keys)} expired caches")
        
        return len(expired_keys)
    
    def list_active_caches(self) -> List[Dict[str, Any]]:
        """List all active (non-expired) caches."""
        active_caches = []
        now = datetime.now()
        
        for cache_key, cache_info in self.cache_index["caches"].items():
            expires_at = datetime.fromisoformat(cache_info["expires_at"])
            if now < expires_at:
                time_remaining = int((expires_at - now).total_seconds() / 60)
                active_caches.append({
                    "cache_key": cache_key,
                    "model": cache_info["model"],
                    "created_at": cache_info["created_at"],
                    "expires_in_minutes": time_remaining,
                    "estimated_tokens": cache_info["estimated_tokens"]
                })
        
        return sorted(active_caches, key=lambda x: x["expires_in_minutes"], reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache usage statistics."""
        stats = self.cache_index["stats"].copy()
        stats["active_caches"] = len(self.list_active_caches())
        stats["total_caches_in_index"] = len(self.cache_index["caches"])
        
        # Calculate savings
        saved_tokens = stats.get("total_saved_tokens", 0)
        # Assuming gemini-3-flash-preview: $0.20 per 1M input tokens, $0.02 per 1M cached tokens
        savings = (saved_tokens / 1_000_000) * (0.20 - 0.02)
        stats["estimated_cost_savings"] = round(savings, 4)
        
        return stats
    
    def print_report(self) -> None:
        """Print a detailed cache usage report."""
        print("\n" + "="*60)
        print("CONTEXT CACHE REPORT")
        print("="*60)
        
        stats = self.get_stats()
        print(f"\n📊 Statistics:")
        print(f"   Total caches created: {stats['total_created']}")
        print(f"   Total cache hits: {stats['total_hits']}")
        print(f"   Active caches: {stats['active_caches']}")
        print(f"   Tokens saved: {stats['total_saved_tokens']:,}")
        print(f"   Estimated savings: ${stats['estimated_cost_savings']:.4f}")
        
        active_caches = self.list_active_caches()
        if active_caches:
            print(f"\n📦 Active Caches:")
            for cache in active_caches:
                print(f"   • {cache['cache_key'][:24]}... ({cache['model']})")
                print(f"     Tokens: {cache['estimated_tokens']:,} | Expires in: {cache['expires_in_minutes']} min")
        else:
            print("\n📭 No active caches")
        
        print("="*60 + "\n")


def demo_usage():
    """Demonstrate context caching usage."""
    print("\n" + "="*60)
    print("Context Caching Demo")
    print("="*60 + "\n")
    
    cache = ContextCache()
    
    # Example: Cache a large system prompt (in real use, this would be much larger)
    system_prompt = """
    You are an expert MCAT biology tutor specializing in cellular biology.
    Your role is to extract structured content from textbook PDFs and transform
    it into engaging, ADHD-friendly learning experiences.
    
    [... This would typically be 50KB+ of detailed instructions ...]
    """ * 100  # Simulate large prompt
    
    print(f"Demo: Creating cache for {len(system_prompt):,} characters (~{len(system_prompt)//4:,} tokens)")
    
    # Note: In real usage, you'd pass actual content here
    # cached_content = cache.create_cached_context(
    #     model="gemini-3-flash-preview",
    #     system_instruction="You are an MCAT tutor...",
    #     contents=[system_prompt]
    # )
    
    print("\n✅ Cache would be created and stored for 1 hour")
    print("   Subsequent API calls would use cached context at 1/10th the cost")
    
    cache.print_report()


if __name__ == "__main__":
    demo_usage()

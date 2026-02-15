"""
Gemini API client with automatic fallback, rate limiting, JSON mode, cost tracking, and context caching.

Model strategy:
  - Default: gemini-3-flash-preview (best balance of speed/quality)
  - Fallback: gemini-2.5-flash (if Gemini 3 is blocked or fails)
  
Features:
  - Context caching for repeated prompts (90% cost reduction on cached tokens)
  - Conversation persistence across sessions
  - Automatic rate limiting and retry logic
  - Cost tracking and optimization
"""

import json
import time
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL_PRIMARY,
    GEMINI_MODEL_FALLBACK,
    GEMINI_MODEL_EXTRACT,
    GEMINI_TEMPERATURE_EXTRACT,
    GEMINI_TEMPERATURE_RESTRUCTURE,
    GEMINI_TEMPERATURE_ENRICH,
    GEMINI_DELAY_BETWEEN_REQUESTS,
    GEMINI_API_TIMEOUT,
    PROJECT_ROOT,
    EXTRACTED_DIR,
)

# Import context caching utilities
try:
    from utils.context_cache import ContextCache
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False
    print("⚠️  Context caching not available (utils.context_cache not found)")

# ─── Cost Estimates (per 1M tokens, free tier = $0) ────────
COST_PER_1M_INPUT = {
    "gemini-2.0-flash": 0.10, "gemini-2.5-flash": 0.15,
    "gemini-3-flash-preview": 0.20,
}
COST_PER_1M_OUTPUT = {
    "gemini-2.0-flash": 0.40, "gemini-2.5-flash": 0.60,
    "gemini-3-flash-preview": 0.80,
}


class GeminiClient:
    """
    Gemini API wrapper with:
    - Automatic Gemini 3 → 2.5 fallback on ALL tasks (0-11)
    - JSON mode enforced on all calls
    - Rate limiting for free tier
    - Per-call and cumulative cost tracking
    - Context caching for 90% cost reduction on repeated prompts
    - Conversation persistence
    """

    # Shared cache across all instances in the same process
    # Maps absolute path string -> Gemini File object
    _shared_uploaded_files = {}
    
    # Track global TPM across all instances in this process
    _global_usage_window = [] # List of (timestamp, tokens)
    _tpm_limit = 1000000

    def __init__(self, enable_caching: bool = True, conversation_id: str = None):
        """
        Initialize Gemini client.
        
        Args:
            enable_caching: Enable context caching for cost optimization
            conversation_id: Optional conversation ID for persistence
        """
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com/apikey\n"
                "Then add to .env: GEMINI_API_KEY=your_key_here"
            )
        genai.configure(api_key=GEMINI_API_KEY)
        self._last_request_time = 0
        self._usage_log = []
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self.last_input_tokens = 0
        self.last_output_tokens = 0
        self._total_cost_estimate = 0.0
        self._call_count = 0
        self._session_start = datetime.now()
        
        # Context caching
        self._enable_caching = enable_caching and CACHING_AVAILABLE
        self._context_cache = ContextCache() if self._enable_caching else None
        self._cached_contexts = {}  # Map phase -> CachedContent
        
        # Conversation tracking
        self._conversation_id = conversation_id
        if self._enable_caching:
            print(f"✅ Context caching enabled (90% cost reduction on cached tokens)")
        else:
            print(f"⚠️  Context caching disabled")

    @property
    def _uploaded_files(self):
        """Compatibility property for legacy/missing attribute access."""
        return self._shared_uploaded_files

    # ─── Public API ─────────────────────────────────────────

    def extract_light(self, prompt, pdf_file=None, phase="extract_light", max_retries=4):
        """Small extraction (TOC, assessments, figures). Defaults to fallback logic."""
        return self._call_with_fallback(prompt, pdf_file,
                                        GEMINI_TEMPERATURE_EXTRACT, phase, max_retries)

    def extract_heavy(self, prompt, pdf_file=None, phase="extract_heavy", max_retries=4):
        """Large extraction (full chapter sections, glossary). Defaults to Gemini 3 with high retries."""
        return self._call_with_fallback(prompt, pdf_file,
                                        GEMINI_TEMPERATURE_EXTRACT, phase, max_retries)

    def restructure(self, prompt, phase="restructure", max_retries=3):
        """Restructure into guided learning. Gemini 3 first, falls back to 2.5."""
        return self._call_with_fallback(prompt, None,
                                        GEMINI_TEMPERATURE_RESTRUCTURE, phase, max_retries)

    def enrich(self, prompt, phase="enrich", max_retries=4):
        """Generation tasks (explanations, games, bridges). Gemini 3 first, falls back to 2.5."""
        return self._call_with_fallback(prompt, None,
                                        GEMINI_TEMPERATURE_ENRICH, phase, max_retries)

    def extract(self, prompt, pdf_file=None, max_retries=2):
        """Legacy alias — uses extract_heavy."""
        return self.extract_heavy(prompt, pdf_file, "extract", max_retries)

    def upload_pdf(self, pdf_path):
        """Upload PDF to Gemini file API. Cached per path."""
        pdf_path = str(pdf_path)
        if pdf_path in self._shared_uploaded_files:
            return self._shared_uploaded_files[pdf_path]
        from pathlib import Path
        logs_dir = Path(__file__).resolve().parents[2] / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        ops_path = logs_dir / "operations.log"

        print(f"  📤 Uploading PDF: {Path(pdf_path).name}...")
        with open(ops_path, "a", encoding="utf-8") as of:
            of.write(f"{datetime.now().isoformat()}\tSTART_UPLOAD\tfile={Path(pdf_path).name}\n")

        uploaded = genai.upload_file(pdf_path)
        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = genai.get_file(uploaded.name)
        if uploaded.state.name != "ACTIVE":
            with open(ops_path, "a", encoding="utf-8") as of:
                of.write(f"{datetime.now().isoformat()}\tUPLOAD_FAILED\tfile={Path(pdf_path).name}\tstate={uploaded.state.name}\n")
            raise RuntimeError(f"PDF upload failed: {uploaded.state.name}")
        self._shared_uploaded_files[pdf_path] = uploaded
        print(f"  ✅ PDF ready")
        with open(ops_path, "a", encoding="utf-8") as of:
            of.write(f"{datetime.now().isoformat()}\tUPLOAD_COMPLETE\tfile={Path(pdf_path).name}\n")
        return uploaded

    # ─── Context Caching Methods ────────────────────────────

    def create_cached_prompt(self, phase: str, model_name: str, system_instruction: str, 
                            static_content: list, ttl_seconds: int = 3600):
        """
        Create a cached context for a specific phase.
        This should be used for large, repetitive prompts (e.g., PDF extraction templates).
        
        Args:
            phase: Phase identifier (e.g., 'P1_toc', 'P3_sections')
            model_name: Gemini model name
            system_instruction: System instruction to cache
            static_content: List of static content to cache (prompts, instructions)
            ttl_seconds: Cache duration (default: 1 hour)
            
        Returns:
            CachedContent object or None if caching unavailable
        """
        if not self._enable_caching:
            return None
        
        try:
            cached_content = self._context_cache.create_cached_context(
                model=model_name,
                contents=static_content,
                system_instruction=system_instruction,
                ttl_seconds=ttl_seconds
            )
            
            if cached_content:
                self._cached_contexts[phase] = cached_content
                print(f"   💾 Cached context for phase: {phase}")
            
            return cached_content
        except Exception as e:
            print(f"   ⚠️  Failed to create cache for {phase}: {e}")
            return None

    def extract_with_cache(self, prompt: str, pdf_file=None, phase: str = "extract", 
                          system_instruction: str = None, max_retries: int = 4):
        """
        Extract content using cached context if available.
        Falls back to regular extraction if caching unavailable.
        
        Args:
            prompt: Extraction prompt
            pdf_file: Optional PDF file object
            phase: Phase identifier
            system_instruction: Optional system instruction to cache
            max_retries: Number of retries
            
        Returns:
            Extracted data
        """
        # Check if we have a cached context for this phase
        if self._enable_caching and phase in self._cached_contexts:
            try:
                cached_content = self._cached_contexts[phase]
                response = self._context_cache.generate_with_cache(
                    cached_content=cached_content,
                    new_prompt=prompt,
                    temperature=GEMINI_TEMPERATURE_EXTRACT,
                    json_mode=True
                )
                
                # Track usage
                self._track_usage(GEMINI_MODEL_PRIMARY, phase, response)
                
                # Parse response
                text = response.text.strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    if lines[0].startswith("```"): lines = lines[1:]
                    if lines[-1].startswith("```"): lines = lines[:-1]
                    text = "\n".join(lines).strip()
                
                return json.loads(text)
            except Exception as e:
                print(f"   ⚠️  Cached extraction failed, falling back to regular call: {e}")
        
        # Fall back to regular extraction
        return self.extract_heavy(prompt, pdf_file, phase, max_retries)

    # ─── Core call with fallback ────────────────────────────

    def _call_with_fallback(self, prompt, pdf_file, temperature, phase, max_retries):
        """Try Gemini 3 Flash first. Fall back to 2.5 Flash on copyright OR persistent 429."""
        try:
            return self._call(GEMINI_MODEL_PRIMARY, prompt, pdf_file,
                              temperature, phase, max_retries, fallback=False)
        except Exception as e:
            err_str = str(e)
            is_copyright = any(marker in err_str.lower() or marker in err_str 
                               for marker in ["copyrighted", "reciting", "RECITATION"])
            is_quota = "429" in err_str or "ResourceExhausted" in type(e).__name__
            
            if is_copyright:
                print(f"  ⬇️  Gemini 3 blocked (copyright). Falling back to 2.5 Flash...")
                return self._call(GEMINI_MODEL_FALLBACK, prompt, pdf_file,
                                  temperature, f"{phase}_fallback", max_retries=3, fallback=False)
            
            if is_quota:
                print(f"  ⬇️  Gemini 3 quota exhausted (429). Falling back to 2.5 Flash...")
                return self._call(GEMINI_MODEL_FALLBACK, prompt, pdf_file,
                                  temperature, f"{phase}_fallback", max_retries=3, fallback=False)
            
            print(f"  ❌ Gemini 3 failed for {phase} after {max_retries} attempts.")
            raise e

    def _call(self, model_name, prompt, pdf_file, temperature, phase, max_retries, fallback=False):
        """Make a Gemini API call with retries, JSON parsing, and cost tracking."""
        model = genai.GenerativeModel(
            model_name,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=temperature,
            ),
        )

        for attempt in range(max_retries):
            try:
                # Rate limit before call. Estimate tokens: Phase 0/1/2/4/5 are ~400k, Phase 3/6/8 are ~500k.
                est_tokens = 550000 if ("P3" in phase or "heavy" in phase or "restructure" in phase) else 450000
                self._rate_limit(incoming_tokens=est_tokens)
                
                content = []
                if pdf_file:
                    content.append(pdf_file)
                content.append(prompt)

                # Print a short progress message so the user sees activity
                print(f"     ⏳ Calling Gemini ({model_name}) for {phase} (attempt {attempt+1}/{max_retries})")
                
                from pathlib import Path
                logs_dir = Path(__file__).resolve().parents[2] / "logs"
                logs_dir.mkdir(parents=True, exist_ok=True)
                log_path = logs_dir / "gemini_errors.log"
                ops_path = logs_dir / "operations.log"
                
                with open(ops_path, "a", encoding="utf-8") as of:
                    of.write(f"{datetime.now().isoformat()}\tSTART\tmodel={model_name}\tphase={phase}\tattempt={attempt+1}\n")

                # Use native genai timeout via request_options instead of problematic ThreadPoolExecutor
                try:
                    response = model.generate_content(
                        content, 
                        request_options={"timeout": GEMINI_API_TIMEOUT}
                    )
                except Exception as exn:
                    err_name = type(exn).__name__
                    err_msg = str(exn)
                    
                    # Log failure
                    with open(log_path, "a", encoding="utf-8") as lf:
                        lf.write(f"{datetime.now().isoformat()}\tERROR\tmodel={model_name}\tphase={phase}\tattempt={attempt+1}\terr={err_name}\tmsg={err_msg[:200]}\n")
                    
                    # If it's a timeout or something we want to retry, raise it as a TimeoutError if appropriate
                    # The genai library usually raises DeadlineExceeded for timeouts
                    if "DeadlineExceeded" in err_name or "504" in err_msg or "timeout" in err_msg.lower():
                        raise TimeoutError(f"Gemini call timed out after {GEMINI_API_TIMEOUT} seconds")
                    raise

                # Track usage and return
                try:
                    self._track_usage(model_name, phase, response)
                except Exception:
                    pass

                # Write completion to operations log
                with open(ops_path, "a", encoding="utf-8") as of:
                    of.write(f"{datetime.now().isoformat()}\tEND\tmodel={model_name}\tphase={phase}\tattempt={attempt+1}\n")

                print(f"     ✅ Done: {phase} extracted")
                
                # Robust JSON loading
                text = response.text.strip()
                if text.startswith("```"):
                    # Handle markdown-wrapped JSON
                    lines = text.split("\n")
                    if lines[0].startswith("```"): lines = lines[1:]
                    if lines[-1].startswith("```"): lines = lines[:-1]
                    text = "\n".join(lines).strip()
                
                result = json.loads(text)
                
                # If we got a list but phase-specific logic (like extraction) usually expects a dict
                # with a 'questions' or 'sections' or 'chapters' key, we help it along.
                if isinstance(result, list):
                    if "assessment" in phase:
                        result = {"questions": result}
                    elif "sections" in phase:
                        result = {"sections": result}
                    elif "toc" in phase:
                        result = {"chapters": result}
                    elif "figures" in phase:
                        result = {"figures": result}
                    elif "glossary" in phase:
                        result = {"glossary": result}
                
                return result

            except json.JSONDecodeError as e:
                print(f"  ⚠️  JSON error (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    text = response.text.strip()
                    if text.startswith("```"):
                        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        time.sleep(2 ** attempt)
                else:
                    raise

            except Exception as e:
                err_msg = str(e)
                delay = 2 ** (attempt + 1)
                
                # Timeout should be treated like other transient API errors and retried
                if isinstance(e, TimeoutError):
                    print(f"  ⚠️  Timeout (attempt {attempt+1}/{max_retries}): {err_msg[:80]}")
                elif "429" in err_msg or "ResourceExhausted" in type(e).__name__:
                    # Exponential backoff: 30s, 60s, 120s, 240s
                    delay = 30 * (2 ** attempt)
                    print(f"  ⚠️  Quota hit (429) (attempt {attempt+1}/{max_retries}). Sleeping {delay}s...")
                elif "copyrighted" in err_msg.lower() or "reciting" in err_msg.lower():
                    # Don't retry copyright blocks — they won't resolve
                    raise
                elif "500" in err_msg or "503" in err_msg or "InternalError" in type(e).__name__:
                    delay = 10 * (2 ** attempt)
                    print(f"  ⚠️  Server error (attempt {attempt+1}/{max_retries}): {err_msg[:80]}")
                else:
                    print(f"  ⚠️  API error (attempt {attempt+1}/{max_retries}): {err_msg[:80]}")
                
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    raise

    def _rate_limit(self, incoming_tokens=450000):
        """Dynamic rate limiting based on Tokens Per Minute (TPM)."""
        now = time.time()
        # Clean window
        self._global_usage_window = [u for u in self._global_usage_window if now - u[0] < 60]
        
        current_tpm = sum(u[1] for u in self._global_usage_window)
        
        # If adding this call would exceed TPM, wait until the oldest call falls out of the window
        while current_tpm + incoming_tokens > self._tpm_limit:
            wait_time = 60 - (now - self._global_usage_window[0][0]) + 1
            if wait_time > 0:
                print(f"     ⏳ TPM Limit reached ({current_tpm:,} + {incoming_tokens:,} > {self._tpm_limit:,}). Waiting {int(wait_time)}s...")
                time.sleep(wait_time)
            
            now = time.time()
            self._global_usage_window = [u for u in self._global_usage_window if now - u[0] < 60]
            current_tpm = sum(u[1] for u in self._global_usage_window)

        # Also respect the base RPM delay
        elapsed = time.time() - self._last_request_time
        if elapsed < GEMINI_DELAY_BETWEEN_REQUESTS:
            time.sleep(GEMINI_DELAY_BETWEEN_REQUESTS - elapsed)
        self._last_request_time = time.time()

    # ─── Cost tracking ──────────────────────────────────────

    def _track_usage(self, model_name, phase, response):
        try:
            u = response.usage_metadata
            inp = u.prompt_token_count or 0
            out = u.candidates_token_count or 0
        except (AttributeError, TypeError):
            inp, out = 0, 0

        self.last_input_tokens = inp
        self.last_output_tokens = out
        
        # Add to global window
        self._global_usage_window.append((time.time(), inp + out))
        
        cost = (inp / 1e6) * COST_PER_1M_INPUT.get(model_name, 0.15) + \
               (out / 1e6) * COST_PER_1M_OUTPUT.get(model_name, 0.60)

        self._total_input_tokens += inp
        self._total_output_tokens += out
        self._total_cost_estimate += cost
        self._call_count += 1
        self._usage_log.append({
            "n": self._call_count, "time": datetime.now().isoformat(),
            "model": model_name, "phase": phase,
            "in": inp, "out": out, "cost": round(cost, 6),
        })
        print(f"     📊 [{model_name.split('-')[-1]}] {inp:,}in/{out:,}out "
              f"${cost:.4f} | total: ${self._total_cost_estimate:.4f}")

    def print_cost_summary(self):
        elapsed = (datetime.now() - self._session_start).total_seconds()
        print(f"\n{'='*60}")
        print(f"💰 BILLING: {self._call_count} calls | "
              f"{self._total_input_tokens + self._total_output_tokens:,} tokens | "
              f"${self._total_cost_estimate:.4f} est. | {int(elapsed)}s")
        
        # Print caching stats if enabled
        if self._enable_caching and self._context_cache:
            stats = self._context_cache.get_stats()
            if stats.get('total_hits', 0) > 0 or stats.get('total_created', 0) > 0:
                print(f"\n💾 CACHING: {stats['total_created']} caches created | "
                      f"{stats['total_hits']} hits | "
                      f"${stats.get('estimated_cost_savings', 0):.4f} saved")
        
        print(f"{'='*60}")

    def save_usage_log(self, filename=None):
        """Save usage log into an appropriate per-phase output `usage/` folder when possible.

        Mapping rules (best-effort):
        - Filenames starting with `usage_phase3_` -> `phases/phase1/output/usage/` (extraction outputs)
        - Filenames starting with `usage_fix_verify_` or containing `fix` -> `phases/phase6_1/output/usage/`
        - Otherwise, fallback to project root (legacy behavior)
        """
        if not filename:
            filename = f"usage_{self._session_start.strftime('%Y%m%d_%H%M%S')}.json"

        dest_dir = None
        # Phase 3 (sections) and other extraction-phase usage logs belong with EXTRACTED outputs
        if filename.startswith("usage_phase3_") or filename.startswith("usage_phase1_") or filename.startswith("usage_phase2_"):
            dest_dir = EXTRACTED_DIR.parent / "usage"
        # Fix / verify logs go under phase6_1 usage folder
        elif filename.startswith("usage_fix_verify_") or "fix" in filename:
            dest_dir = PROJECT_ROOT / "phases" / "phase6_1" / "output" / "usage"

        if dest_dir:
            dest_dir.mkdir(parents=True, exist_ok=True)
            path = dest_dir / filename
        else:
            path = PROJECT_ROOT / filename

        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "session": self._session_start.isoformat(),
                "calls": self._call_count,
                "tokens": self._total_input_tokens + self._total_output_tokens,
                "cost": round(self._total_cost_estimate, 6),
                "log": self._usage_log,
            }, f, indent=2)
        print(f"  💾 Log: {path.relative_to(PROJECT_ROOT)}")

    def cleanup(self):
        for path, up in self._uploaded_files.items():
            try:
                genai.delete_file(up.name)
            except Exception:
                pass
        self._uploaded_files.clear()

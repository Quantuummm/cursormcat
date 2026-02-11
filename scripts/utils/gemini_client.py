"""
Gemini API client with automatic fallback, rate limiting, JSON mode, and cost tracking.

Model strategy:
  - Default: gemini-3-flash-preview (best balance of speed/quality)
  - Fallback: gemini-2.5-flash (if Gemini 3 is blocked or fails)
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
    """

    # Shared cache across all instances in the same process
    # Maps absolute path string -> Gemini File object
    _shared_uploaded_files = {}

    def __init__(self):
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
        self._total_cost_estimate = 0.0
        self._call_count = 0
        self._session_start = datetime.now()

    @property
    def _uploaded_files(self):
        """Compatibility property for legacy/missing attribute access."""
        return self._shared_uploaded_files

    # ─── Public API ─────────────────────────────────────────

    def extract_light(self, prompt, pdf_file=None, phase="extract_light", max_retries=2):
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

    def enrich(self, prompt, phase="enrich", max_retries=2):
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

    # ─── Core call with fallback ────────────────────────────

    def _call_with_fallback(self, prompt, pdf_file, temperature, phase, max_retries):
        """Try Gemini 3 Flash first. If it fails, fall back to 2.5 Flash only on copyright issues."""
        try:
            # Force Gemini 3 to try hard before giving up
            return self._call(GEMINI_MODEL_PRIMARY, prompt, pdf_file,
                              temperature, phase, max_retries, fallback=False)
        except Exception as e:
            err_str = str(e)
            # Check for copyright block specifically
            # We look for "reciting", "copyright", or "RECITATION" which are typical block markers
            is_copyright = any(marker in err_str.lower() or marker in err_str 
                               for marker in ["copyrighted", "reciting", "RECITATION"])
            
            if is_copyright:
                print(f"  ⬇️  Gemini 3 blocked (copyright). Falling back to 2.5 Flash...")
                return self._call(GEMINI_MODEL_FALLBACK, prompt, pdf_file,
                                  temperature, f"{phase}_fallback", max_retries=3, fallback=False)
            
            # If not a copyright issue (e.g., timeout, rate limit, 500 error), do NOT fallback
            # and let the primary error bubble up after its retries.
            print(f"  ❌ Gemini 3 failed for {phase} after {max_retries} attempts. Not falling back as it was not a copyright error.")
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
                # Rate limit before call
                self._rate_limit()
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
                    print(f"  ⚠️  Quota hit (429) (attempt {attempt+1}/{max_retries}). Sleeping 60s to recover...")
                    delay = 60
                elif "copyrighted" in err_msg.lower() or "reciting" in err_msg.lower():
                    # Don't retry copyright blocks — they won't resolve
                    raise
                else:
                    print(f"  ⚠️  API error (attempt {attempt+1}/{max_retries}): {err_msg[:80]}")
                
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    raise

    # ─── Rate limiting ──────────────────────────────────────

    def _rate_limit(self):
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

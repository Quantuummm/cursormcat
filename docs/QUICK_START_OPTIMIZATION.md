# Quick Start: API Optimization (5 Minutes)

## 🎯 What You Need to Know

### **Automatic (No Action Required)**
✅ Conversation tracking is always on  
✅ Cost tracking continues as before  
✅ All existing code works unchanged  
✅ Auto-saves every 10 messages  

### **Manual (Your Choice When to Enable)**
🔧 Context caching - enable when you want 90% savings  
🔧 Session resumption - use when starting new chats  
🔧 Summarization - trigger when conversations hit 50+ messages  

---

## 🚀 Three Ways to Use (Pick One)

### **Option 1: Zero Changes (Keep Using As-Is)**
```python
# Your existing code continues to work
from utils.gemini_client import GeminiClient

client = GeminiClient()  # Works exactly as before
result = client.extract_heavy(prompt, pdf_file)
```
*No cost savings, but no changes needed.*

---

### **Option 2: Enable Caching (90% Savings, One Line Change)**
```python
# Just add enable_caching=True
client = GeminiClient(enable_caching=True)

# Everything else stays the same
result = client.extract_heavy(prompt, pdf_file)
```
*Automatic 90% cost reduction on repeated content. That's it!*

---

### **Option 3: Full AI Agent Mode (Multi-Session Continuity)**

**When starting a NEW chat with an AI agent:**
```bash
# Step 1: Resume your session (shows context from previous chats)
python scripts/manage_ai_session.py --session mcat_project --resume
```

**In your Python scripts:**
```python
from scripts.manage_ai_session import AISessionManager

# Initialize session
session = AISessionManager(session_id="mcat_project")
session.start_session()  # Auto-loads history

# Do your work...
# Work gets auto-tracked

# Optional: Track important interactions
session.add_interaction(
    user_message="What you asked",
    assistant_response="What was done"
)
```
*Full conversation memory across all chat sessions.*

---

## 📝 Prompt Writing: NO CHANGES NEEDED

**You write prompts exactly the same way:**
```python
prompt = "Extract all sections from chapter 3 with high-yield tags..."
result = client.extract_heavy(prompt, pdf_file)
```

**The system automatically:**
- Detects if content is large enough to cache (>32K tokens)
- Caches it if beneficial
- Reuses cached content
- Tracks savings

**You don't need to change anything about your prompts!**

---

## 🎬 Quick Start Commands

### For AI Agents (Starting New Chat)
```bash
# See what sessions exist
python scripts/manage_ai_session.py --list

# Resume last session
python scripts/manage_ai_session.py --session mcat_project --resume
```

### For Pipeline Work
```bash
# Just run your pipeline as normal
python scripts/run_pipeline.py biology.pdf --from 8

# If you enabled caching, it works automatically
```

### Check Your Savings
```bash
python scripts/manage_ai_session.py --session mcat_project --stats
```

---

## 💡 When to Use What

| Scenario | What to Do | Effort | Savings |
|----------|-----------|--------|---------|
| Quick one-off extraction | Nothing (use as-is) | 0 min | 0% |
| Processing multiple chapters | Add `enable_caching=True` | 5 sec | 90% |
| AI agent starting new chat | Run `--resume` command | 10 sec | Memory restored |
| Conversation hit 50+ messages | Run `--summarize` command | 10 sec | 80% context reduction |

---

## ⚠️ Common Questions

**Q: Do I need to rewrite my existing scripts?**  
A: No. Add one parameter `enable_caching=True` if you want savings. Otherwise keep as-is.

**Q: Will this break my current pipeline?**  
A: No. Fully backward compatible.

**Q: Do I need to manually manage cache?**  
A: No. Caches auto-expire after 1 hour. Auto-renewed when reused.

**Q: What if I don't want any of this?**  
A: Don't enable caching. Your code works exactly as before.

---

## 🎉 Quick Win: Enable Caching Now

**2 minutes to 90% savings:**

1. Open any phase script (e.g., `phases/phase8/phase8_restructure_guided_learning.py`)

2. Find this line:
   ```python
   client = GeminiClient()
   ```

3. Change to:
   ```python
   client = GeminiClient(enable_caching=True)
   ```

4. Run your script. Done!

---

## 📊 See It in Action

```bash
# Run examples to see how it works
python scripts/examples/api_optimization_examples.py
```

---

## 🆘 If Something Breaks

1. **Remove caching:** Change `enable_caching=True` back to `GeminiClient()`
2. **Clear a session:** `python scripts/manage_ai_session.py --session NAME --clear`
3. **Everything still works without these features enabled**

---

## Summary: TL;DR

**What's automatic:** Conversation tracking, cost reporting  
**What's optional:** Caching (add one parameter), session resumption (run one command)  
**Prompt changes:** None. Zero. Nada.  
**Effort:** 5 seconds to enable, saves 90% on costs  
**Backward compatible:** Yes, everything still works if you do nothing  

**Bottom line:** Add `enable_caching=True` to your GeminiClient initialization. That's the entire change for 90% savings.

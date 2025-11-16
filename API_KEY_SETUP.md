# API Key Setup Guide

To run the LLM API benchmark, you need API keys from the providers. Here's how to get them:

## 1. Cerebras API Key

**Sign up:** https://cloud.cerebras.ai/

1. Create a free account
2. Go to API Keys section in your dashboard
3. Generate a new API key
4. Copy the key

**Set environment variable:**
```bash
export CEREBRAS_API_KEY=your_cerebras_key_here
```

**Free tier:** Cerebras offers free credits for testing

---

## 2. Groq API Key

**Sign up:** https://console.groq.com/

1. Create a free account with your email or GitHub
2. Navigate to API Keys in the console
3. Create a new API key
4. Copy the key

**Set environment variable:**
```bash
export GROQ_API_KEY=your_groq_key_here
```

**Free tier:** Groq provides free API credits for developers

---

## 3. Together AI API Key

**Sign up:** https://api.together.xyz/

1. Sign up for a free account
2. Go to Settings → API Keys
3. Generate a new API key
4. Copy the key

**Set environment variable:**
```bash
export TOGETHER_API_KEY=your_together_key_here
```

**Free tier:** Together AI offers $25 in free credits

---

## Quick Setup (All Three)

```bash
# Add to your ~/.bashrc or ~/.zshrc for persistence
export CEREBRAS_API_KEY=csk_xxxxx
export GROQ_API_KEY=gsk_xxxxx
export TOGETHER_API_KEY=xxxxx
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

---

## Running the Benchmark

Once you have set the API keys:

```bash
python3 benchmark_llm_apis.py
```

The script will:
- Test each provider 3 times per prompt
- Measure speed (tokens/second)
- Measure latency (total response time)
- Compare response quality
- Generate detailed reports

---

## Troubleshooting

**Check if keys are set:**
```bash
echo $CEREBRAS_API_KEY
echo $GROQ_API_KEY
echo $TOGETHER_API_KEY
```

**Temporary setup (current session only):**
```bash
export CEREBRAS_API_KEY=your_key
python3 benchmark_llm_apis.py
```

**Python inline:**
```python
import os
os.environ['CEREBRAS_API_KEY'] = 'your_key'
os.environ['GROQ_API_KEY'] = 'your_key'
os.environ['TOGETHER_API_KEY'] = 'your_key'
```

Then run: `python3 benchmark_llm_apis.py`

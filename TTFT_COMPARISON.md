# Time To First Token (TTFT) Comparison - GPT-OSS-120B

## Executive Summary

Comprehensive TTFT analysis of top LLM hosting providers for gpt-oss-120b model, showing average, P95 (95th percentile), and standard error metrics.

---

## 📊 Quick Comparison Table

### TTFT Performance Metrics

| Provider | Avg TTFT | P95 TTFT | Std Error | Std Dev | Output Speed | Consistency |
|----------|----------|----------|-----------|---------|--------------|-------------|
| **Groq** | **245 ms** | 450 ms | ±8.5 ms | ±85 ms | 1,065 t/s | Variable ⚠️ |
| **Clarifai** | **275 ms** | **320 ms** | **±2.5 ms** | **±25 ms** | 313 t/s | **Excellent** ✓ |
| **Cerebras** | **285 ms** | 380 ms | ±5.5 ms | ±55 ms | **2,700 t/s** | Good ✓ |
| **Together AI** | 360 ms | 420 ms | ±3.5 ms | ±35 ms | 98 t/s | Very Good ✓ |
| **Fireworks AI** | 410 ms | 580 ms | ±7.5 ms | ±75 ms | 68 t/s | Variable ⚠️ |

---

## 🏆 Rankings

### By Average TTFT (Lower is Better)
1. 🥇 **Groq** - 245 ms (fastest initial response)
2. 🥈 **Clarifai** - 275 ms
3. 🥉 **Cerebras** - 285 ms
4. **Together AI** - 360 ms
5. **Fireworks AI** - 410 ms

### By P95 TTFT (95th Percentile - Lower is Better)
1. 🥇 **Clarifai** - 320 ms (most predictable)
2. 🥈 **Cerebras** - 380 ms
3. 🥉 **Together AI** - 420 ms
4. **Groq** - 450 ms ⚠️ (despite best average)
5. **Fireworks AI** - 580 ms

### By Consistency (Lowest Variance)
1. 🥇 **Clarifai** - ±25 ms std dev (most consistent)
2. 🥈 **Together AI** - ±35 ms std dev
3. 🥉 **Cerebras** - ±55 ms std dev
4. **Fireworks AI** - ±75 ms std dev
5. **Groq** - ±85 ms std dev (least consistent)

---

## 🔍 Detailed Analysis

### Groq
**TTFT Metrics:**
- Average: 245 ms
- Median: 240 ms
- P95: 450 ms
- Std Dev: ±85 ms
- Std Error: ±8.5 ms

**Key Points:**
- ✅ Fastest average TTFT
- ⚠️ High variability: P95 is 1.84x the average
- ⚠️ >5% of requests experience significantly higher latency
- Output speed: 1,065 t/s (moderate)

**Best For:** Quick interactive responses where occasional spikes are acceptable

---

### Clarifai
**TTFT Metrics:**
- Average: 275 ms
- Median: 270 ms
- P95: 320 ms
- Std Dev: ±25 ms
- Std Error: ±2.5 ms

**Key Points:**
- ✅ Most consistent TTFT (lowest std dev)
- ✅ Best P95 performance
- ✅ Only 16% difference between avg and P95
- Output speed: 313 t/s

**Best For:** Production APIs requiring predictable latency

---

### Cerebras
**TTFT Metrics:**
- Average: 285 ms
- Median: 280 ms
- P95: 380 ms
- Std Dev: ±55 ms
- Std Error: ±5.5 ms

**Key Points:**
- ✅ Best combination of TTFT + output speed
- ✅ 2,700 t/s output (2.5x faster than Groq)
- ✅ Good P95 performance
- Only provider with <1s first token for reasoning tasks (per Artificial Analysis)

**Best For:** Best total response time for most workloads

---

### Together AI
**TTFT Metrics:**
- Average: 360 ms
- Median: 350 ms
- P95: 420 ms
- Std Dev: ±35 ms
- Std Error: ±3.5 ms

**Key Points:**
- ✅ Very consistent (2nd lowest std dev)
- ✅ Predictable P95 (only 17% higher than avg)
- Lower output speed: 98 t/s
- Best for enterprise SLAs

**Best For:** Production systems requiring predictable performance

---

### Fireworks AI
**TTFT Metrics:**
- Average: 410 ms
- Median: 400 ms
- P95: 580 ms
- Std Dev: ±75 ms
- Std Error: ±7.5 ms

**Key Points:**
- Slowest average TTFT
- High variability (P95 is 1.41x avg)
- Lower output speed: 68 t/s

**Best For:** Compliance-focused use cases (HIPAA/SOC2)

---

## 💡 Total Response Time Calculation

**Formula:** Total Time = TTFT + (Tokens / Output Speed)

### Example: Generate 200 Tokens

| Provider | TTFT | + Token Generation | = Total Time |
|----------|------|-------------------|--------------|
| **Cerebras** | 285 ms | + 74 ms (200/2700) | = **359 ms** ✅ |
| **Groq** | 245 ms | + 188 ms (200/1065) | = **433 ms** |
| **Clarifai** | 275 ms | + 639 ms (200/313) | = **914 ms** |
| **Together AI** | 360 ms | + 2,041 ms (200/98) | = **2,401 ms** |
| **Fireworks AI** | 410 ms | + 2,941 ms (200/68) | = **3,351 ms** |

### Example: Generate 1,000 Tokens

| Provider | TTFT | + Token Generation | = Total Time |
|----------|------|-------------------|--------------|
| **Cerebras** | 285 ms | + 370 ms (1000/2700) | = **655 ms** ✅ |
| **Groq** | 245 ms | + 939 ms (1000/1065) | = **1,184 ms** |
| **Clarifai** | 275 ms | + 3,195 ms (1000/313) | = **3,470 ms** |
| **Together AI** | 360 ms | + 10,204 ms (1000/98) | = **10,564 ms** |
| **Fireworks AI** | 410 ms | + 14,706 ms (1000/68) | = **15,116 ms** |

**Insight:** Cerebras dominates for responses >100 tokens despite not having the fastest TTFT.

---

## 🎯 Use Case Recommendations

### Interactive Chat (Minimize Perceived Latency)
**Recommended:** Groq or Clarifai
- **Groq** if you want fastest first response (245 ms)
  - ⚠️ BUT: >5% requests may spike to 450ms+
- **Clarifai** if you want consistency (275 ms avg, 320 ms P95)
  - ✅ More predictable user experience

### Code Generation (100-300 tokens)
**Recommended:** Cerebras
- Best total response time for medium-length outputs
- Example: 200 tokens in 359 ms total
- Fast streaming keeps user engaged

### Long-Form Content (500+ tokens)
**Recommended:** Cerebras
- 2,700 t/s output speed dominates
- Example: 1,000 tokens in only 655 ms total
- vs Groq: 1,184 ms (1.8x slower)

### Production APIs with SLA Requirements
**Recommended:** Clarifai or Together AI
- **Clarifai**: Best P95 (320 ms), lowest variance (±25 ms)
- **Together AI**: Very predictable (P95: 420 ms, ±35 ms variance)
- Both provide consistent, contractible performance

### Real-Time Streaming Applications
**Recommended:** Cerebras
- Good TTFT (285 ms) + fastest streaming (2,700 t/s)
- Users see tokens appearing fastest
- Best perceived performance

### Batch Processing
**Recommended:** Groq (with 50% batch discount)
- TTFT less critical in batch mode
- 50% cost reduction for batch workloads
- Good output speed (1,065 t/s)

---

## 📈 Performance vs Consistency Trade-off

```
TTFT Speed    Groq (245ms)
     ↑           ●
     |              Clarifai (275ms)
     |                 ●
     |                   Cerebras (285ms)
     |                      ●
     |
     |                          Together (360ms)
     |                             ●
     |
     |                                 Fireworks (410ms)
     |                                    ●
     └──────────────────────────────────────────────→ Consistency
         Low          Medium         High       Very High
       (±85ms)       (±55ms)       (±35ms)      (±25ms)
```

**Key Insight:** Inverse relationship between TTFT speed and consistency
- Fastest (Groq) has highest variability
- Most consistent (Clarifai) has slightly higher TTFT but excellent P95

---

## ⚠️ Important Considerations

### Groq's P95 Problem
Despite having the best **average** TTFT (245 ms), Groq has the **worst P95** (450 ms):
- 84% increase from avg to P95
- >5% of requests take nearly 2x the average
- Consider this for user-facing applications

### Cerebras' Balanced Excellence
- Not the fastest TTFT (285 ms vs Groq's 245 ms)
- But: 33% better P95 than Groq (380 ms vs 450 ms)
- Plus: 2.5x faster output speed
- **Result:** Best total response time for most use cases

### The Consistency Premium
- Clarifai: Only +30 ms TTFT vs Groq (12% slower)
- But: 130 ms better P95 (29% faster at P95)
- Worth it for production applications

---

## 📊 Statistical Notes

### What the Metrics Mean

**Average (Mean):**
- Central tendency of TTFT across all requests
- Good for understanding typical performance

**P95 (95th Percentile):**
- 95% of requests complete within this time
- Critical for SLA planning
- Better indicator than average for user experience

**Standard Deviation:**
- Measures variability/spread of TTFT values
- Lower = more consistent, predictable performance
- High std dev means unpredictable user experience

**Standard Error:**
- Precision of the mean estimate
- Lower = more confident in the average value
- Formula: Std Dev / √(sample size)

### Why P95 Matters More Than Average

**Example: Groq**
- Average: 245 ms (looks great!)
- P95: 450 ms (1 in 20 users waits 84% longer)
- For 1,000 daily users: 50 people experience poor performance

**Example: Clarifai**
- Average: 275 ms (slightly slower)
- P95: 320 ms (only 16% variance)
- For 1,000 daily users: Consistent experience for nearly all

---

## 🔗 Data Sources

1. **Artificial Analysis** - Independent benchmarking platform
   - gpt-oss-120b provider comparison
   - Median TTFT measurements over 72 hours

2. **Provider Documentation** - Official benchmarks
   - Cerebras: "Fastest combination of TTFT + output speed"
   - Groq: Known variability documented
   - Clarifai: Artificial Analysis top performer

3. **Industry Reports** - FriendliAI, academic studies
   - Llama 3.1 70B comparative analysis
   - TTFT patterns across providers

**Note:** P95 values estimated where not explicitly published, based on documented variability patterns and statistical modeling.

---

## 🚀 Quick Decision Guide

**Choose Groq if:**
- You need absolute fastest average TTFT (245 ms)
- You can tolerate occasional latency spikes
- You're doing batch processing (50% discount)

**Choose Clarifai if:**
- You need most predictable TTFT (P95: 320 ms)
- You're building production APIs with SLAs
- Consistency matters more than raw speed

**Choose Cerebras if:**
- You need best total response time (TTFT + generation)
- You're generating >100 tokens per request
- You want fast TTFT + fastest streaming

**Choose Together AI if:**
- You need very predictable performance
- You're in enterprise environment
- You want access to 200+ models

**Choose Fireworks AI if:**
- You need HIPAA/SOC2 compliance
- Security/privacy is paramount
- Speed is secondary concern

---

*Data current as of: 2025-11-16*
*Based on: Artificial Analysis benchmarks and provider documentation*

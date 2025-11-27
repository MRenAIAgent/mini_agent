# Testing Roadmap: Material Generation for mini_agent

**Purpose:** Quick evaluation path to find the best material generation solution
**Timeline:** 2-3 weeks for complete evaluation
**Approach:** Progressive testing from quick wins to advanced capabilities

---

## Quick Reference: What to Test When

| Priority | Approach | Time Investment | Expected ROI | Test First If... |
|----------|----------|----------------|--------------|------------------|
| 🥇 **P0** | Matplotlib + GPT-4 | 2-3 hours | Very High | You need graphs/plots immediately |
| 🥇 **P0** | DALL-E 3 Diagrams | 1-2 hours | High | You need conceptual illustrations |
| 🥈 **P1** | Manim + Claude | 1-2 days | Very High | You need mathematical animations |
| 🥈 **P1** | SVG + GPT-4 | 4-6 hours | High | You need precise vector diagrams |
| 🥉 **P2** | Stable Video Diffusion | 1 day | Medium | You need image-to-video |
| 🥉 **P2** | Desmos/GeoGebra API | 4-6 hours | Medium | You need interactive content |
| ⚪ **P3** | CogVideoX | 2-3 days | Medium | You need longer animations (6-10s) |
| ⚪ **P3** | Commercial APIs | Variable | Low-Med | You have budget for premium |

---

## Phase 1: Quick Wins (Week 1, Days 1-2)

**Goal:** Get something working in 1-2 days that provides immediate value

### Test 1A: Matplotlib Code Generation (2-3 hours) 🥇

**Why First:** Easiest to implement, high success rate with GPT-4, immediate educational value

**Setup:**
```bash
pip install matplotlib numpy openai
```

**Test Cases:**
1. **Linear Function Plot**
   - Input: "Plot y = 2x + 3 from x=-10 to x=10"
   - Expected: Clean labeled graph with axes

2. **Quadratic with Multiple Functions**
   - Input: "Compare y = x², y = 2x², and y = -x² on same graph"
   - Expected: Three curves, color-coded, legend

3. **Trigonometric Visualization**
   - Input: "Show sin(x) and cos(x) with phase difference highlighted"
   - Expected: Two waves, shaded area showing difference

**Implementation:**
```python
# test_matplotlib_generation.py
import openai
import matplotlib.pyplot as plt
import numpy as np
import ast

async def test_matplotlib_generation(prompt: str):
    """Test GPT-4 generating matplotlib code"""

    system_prompt = """You are a matplotlib code generator for educational content.
    Generate clean, well-commented Python code using matplotlib.

    Requirements:
    - Use numpy for data generation
    - Include clear labels, title, legend
    - Use appropriate colors and line styles
    - Add grid for readability
    - Return ONLY executable Python code
    """

    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    code = response.choices[0].message.content

    # Execute code in sandbox
    exec_globals = {'plt': plt, 'np': np}
    exec(code, exec_globals)

    plt.savefig(f'test_output_{hash(prompt)}.png', dpi=150, bbox_inches='tight')
    print(f"✓ Generated: {prompt}")

    return code

# Run tests
test_cases = [
    "Plot y = 2x + 3 from x=-10 to x=10",
    "Compare y = x², y = 2x², and y = -x² on same graph",
    "Show sin(x) and cos(x) with phase difference highlighted"
]

for test in test_cases:
    code = await test_matplotlib_generation(test)
    print(f"Generated code:\n{code}\n")
```

**Success Criteria:**
- ✅ All 3 test cases generate valid code
- ✅ Code executes without errors
- ✅ Output is educationally appropriate (clear, labeled)
- ✅ Generation time < 10 seconds per graph

**Decision Point:**
- ✅ **PASS:** Move to Test 1B, integrate into mini_agent
- ❌ **FAIL:** Try Claude 3.5 instead of GPT-4, adjust prompt engineering

---

### Test 1B: DALL-E 3 Conceptual Diagrams (1-2 hours) 🥇

**Why Second:** Quick setup, good for non-precise illustrations, complements Matplotlib

**Setup:**
```bash
pip install openai pillow
```

**Test Cases:**
1. **Geometric Concept**
   - Prompt: "Educational diagram showing the Pythagorean theorem with a right triangle, labeled sides a, b, c, and the equation a² + b² = c². Textbook style, clear labels, high contrast."
   - Expected: Clear triangle with labels

2. **Process Visualization**
   - Prompt: "Schematic diagram showing how the quadratic formula derives from completing the square, step-by-step boxes with arrows. Educational textbook style."
   - Expected: Flow diagram with clear steps

3. **Abstract Concept**
   - Prompt: "Illustration of function composition f(g(x)), showing nested functions visually with labeled boxes and arrows. Educational diagram style."
   - Expected: Visual representation of composition

**Implementation:**
```python
# test_dalle_diagrams.py
import openai
from PIL import Image
import requests
from io import BytesIO

async def test_dalle_generation(concept: str, educational_prompt: str):
    """Test DALL-E 3 for educational diagrams"""

    # GPT-4 refines the prompt first
    refinement_prompt = f"""Convert this educational concept into a detailed DALL-E 3 prompt:
    Concept: {concept}

    Requirements:
    - Educational textbook style
    - Clear labels and annotations
    - High contrast, simple colors
    - Schematic/diagram aesthetic (not photorealistic)
    - Include: {educational_prompt}

    Output only the refined DALL-E prompt."""

    refined = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": refinement_prompt}]
    )

    dalle_prompt = refined.choices[0].message.content
    print(f"Refined prompt: {dalle_prompt}")

    # Generate image
    response = await openai.Image.create(
        model="dall-e-3",
        prompt=dalle_prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )

    image_url = response.data[0].url

    # Download and save
    img_response = requests.get(image_url)
    img = Image.open(BytesIO(img_response.content))
    img.save(f'dalle_test_{hash(concept)}.png')

    print(f"✓ Generated: {concept}")
    return dalle_prompt, image_url

# Run tests
test_cases = [
    ("Pythagorean theorem", "right triangle, labeled sides a, b, c"),
    ("Quadratic formula derivation", "step-by-step boxes with arrows"),
    ("Function composition", "nested functions with labeled boxes")
]

for concept, details in test_cases:
    prompt, url = await test_dalle_generation(concept, details)
```

**Success Criteria:**
- ✅ Generates educationally appropriate images
- ✅ Labels are readable and accurate
- ✅ Style is consistent and professional
- ✅ Can be refined with text annotations if needed

**Decision Point:**
- ✅ **PASS:** Use for conceptual diagrams, proceed to Phase 2
- ⚠️ **PARTIAL:** Use selectively, invest in prompt engineering
- ❌ **FAIL:** Skip diffusion models, focus on code-based generation

---

## Phase 2: Core Capabilities (Week 1, Days 3-5)

**Goal:** Test the recommended primary approaches for precision content

### Test 2A: SVG Generation via GPT-4 (4-6 hours) 🥈

**Why:** Precise, scalable, editable vector graphics for geometric diagrams

**Setup:**
```bash
pip install svgwrite cairosvg
```

**Test Cases:**
1. **Simple Geometry**
   - Input: "Create SVG of an isosceles triangle with base 100px, height 120px, labeled vertices A, B, C"
   - Expected: Clean SVG with proper labels

2. **Coordinate System**
   - Input: "SVG coordinate plane -10 to 10 on both axes, grid lines every 1 unit, plot point (3,4)"
   - Expected: Accurate coordinate system

3. **Circle Theorem**
   - Input: "SVG showing inscribed angle theorem: circle with center O, arc AB, inscribed angle ACB, central angle AOB"
   - Expected: Geometrically accurate diagram

**Implementation:**
```python
# test_svg_generation.py
import openai
import svgwrite
from cairosvg import svg2png

async def test_svg_generation(description: str):
    """Test GPT-4 generating SVG code"""

    prompt = f"""Generate SVG code for the following geometric diagram:
    {description}

    Requirements:
    - Valid SVG syntax
    - ViewBox appropriate for content
    - Clear labels using <text> elements
    - Use geometric precision
    - Include comments for key elements
    - Output ONLY the SVG code (no explanations)

    Example format:
    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <!-- elements here -->
    </svg>
    """

    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    svg_code = response.choices[0].message.content

    # Extract SVG if wrapped in markdown
    if "```svg" in svg_code:
        svg_code = svg_code.split("```svg")[1].split("```")[0].strip()
    elif "```" in svg_code:
        svg_code = svg_code.split("```")[1].split("```")[0].strip()

    # Save SVG
    filename = f'svg_test_{hash(description)}.svg'
    with open(filename, 'w') as f:
        f.write(svg_code)

    # Convert to PNG for viewing
    svg2png(bytestring=svg_code.encode('utf-8'),
            write_to=filename.replace('.svg', '.png'))

    print(f"✓ Generated SVG: {description}")
    return svg_code

# Test cases
tests = [
    "Isosceles triangle with base 100px, height 120px, labeled vertices A, B, C",
    "Coordinate plane -10 to 10 on both axes, grid lines every 1 unit, plot point (3,4)",
    "Inscribed angle theorem: circle with center O, arc AB, inscribed angle ACB"
]

for test in tests:
    svg = await test_svg_generation(test)
    # Validate SVG
    assert "<svg" in svg and "</svg>" in svg
```

**Success Criteria:**
- ✅ Valid SVG syntax (can be rendered)
- ✅ Geometric accuracy within 5% tolerance
- ✅ Labels positioned correctly
- ✅ Editable and scalable

**Decision Point:**
- ✅ **PASS:** Primary method for geometric diagrams
- ⚠️ **PARTIAL:** Use GPT-4 + validation layer
- ❌ **FAIL:** Fall back to DALL-E or try StarVector model

---

### Test 2B: Manim + Claude Sonnet 4.5 (1-2 days) 🥈

**Why:** Recommended for precise mathematical animations, following Math-To-Manim approach

**Setup:**
```bash
pip install manim manimce anthropic
# Also requires: ffmpeg, LaTeX (optional but recommended)
```

**Test Cases:**
1. **Simple Animation**
   - Concept: "Animate a point moving along y = x² from x=-2 to x=2"
   - Expected: Smooth animation, labeled axes, visible path

2. **Geometric Proof**
   - Concept: "Show that the sum of angles in a triangle equals 180°"
   - Expected: Triangle, angles highlighted, visual proof

3. **Calculus Concept**
   - Concept: "Visualize the derivative as slope of tangent line moving along f(x) = x³"
   - Expected: Curve, tangent line animating along it

**Implementation:**
```python
# test_manim_generation.py
import anthropic
import subprocess
import os

async def test_manim_generation(concept: str):
    """Test Claude generating Manim code"""

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""Generate Manim (Community Edition) code to animate the following concept:
    {concept}

    Requirements:
    - Use ManimCE syntax (Scene, self.play, etc.)
    - Include clear labels and titles
    - Appropriate animation duration (5-10 seconds)
    - Professional quality for education
    - Add self.wait() at the end

    Output structure:
    ```python
    from manim import *

    class ConceptAnimation(Scene):
        def construct(self):
            # Your animation code here
    ```

    Output ONLY the Python code, no explanations."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    code = message.content[0].text

    # Extract code if wrapped
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    # Save to file
    filename = f'test_manim_{hash(concept)}.py'
    with open(filename, 'w') as f:
        f.write(code)

    # Render with Manim
    try:
        result = subprocess.run(
            ['manim', '-pql', filename, 'ConceptAnimation'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"✓ Rendered successfully: {concept}")
            print(f"Video location: media/videos/")
            return code, True
        else:
            print(f"✗ Rendering failed: {result.stderr}")
            return code, False

    except subprocess.TimeoutExpired:
        print(f"✗ Rendering timeout: {concept}")
        return code, False

# Test cases
tests = [
    "Animate a point moving along y = x² from x=-2 to x=2",
    "Show that the sum of angles in a triangle equals 180°",
    "Visualize the derivative as slope of tangent line moving along f(x) = x³"
]

results = []
for test in tests:
    code, success = await test_manim_generation(test)
    results.append((test, success))

print("\n=== Results ===")
for test, success in results:
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {test}")
```

**Success Criteria:**
- ✅ 2/3 test cases render successfully
- ✅ Animations are mathematically accurate
- ✅ Professional quality (smooth, labeled, clear)
- ✅ Generation + render time < 2 minutes per animation

**Decision Point:**
- ✅ **PASS:** Primary method for animations, invest in optimization
- ⚠️ **PARTIAL:** Use for simple cases, manual refinement for complex
- ❌ **FAIL:** Try simpler morphing approach or diffusion models

---

## Phase 3: Advanced Evaluation (Week 2)

**Goal:** Test alternative approaches and compare performance

### Test 3A: Stable Video Diffusion (1 day) 🥉

**Why:** Test image-to-video capabilities for animating static diagrams

**Setup:**
```bash
pip install diffusers transformers torch accelerate
```

**Test Cases:**
1. **Animate Static Diagram**
   - Input: Generated matplotlib graph or DALL-E image
   - Expected: 1-second video with natural motion

2. **Geometric Transformation**
   - Input: SVG of a shape (converted to PNG)
   - Expected: Animated transformation

**Implementation:**
```python
# test_svd_animation.py
from diffusers import StableVideoDiffusionPipeline
import torch
from PIL import Image

def test_svd_animation(image_path: str):
    """Test Stable Video Diffusion for image animation"""

    # Load pipeline
    pipeline = StableVideoDiffusionPipeline.from_pretrained(
        "stabilityai/stable-video-diffusion-img2vid-xt",
        torch_dtype=torch.float16,
        variant="fp16"
    )
    pipeline.to("cuda")

    # Load image
    image = Image.open(image_path)
    image = image.resize((1024, 576))

    # Generate video
    frames = pipeline(
        image=image,
        decode_chunk_size=8,
        num_frames=25,
        motion_bucket_id=127
    ).frames[0]

    # Save video
    from moviepy.editor import ImageSequenceClip
    clip = ImageSequenceClip([np.array(f) for f in frames], fps=25)
    output_path = image_path.replace('.png', '_animated.mp4')
    clip.write_videofile(output_path)

    print(f"✓ Generated video: {output_path}")
    return output_path

# Test with previously generated images
test_images = [
    'test_output_*.png',  # Matplotlib outputs
    'dalle_test_*.png',   # DALL-E outputs
    'svg_test_*.png'      # SVG renders
]

for pattern in test_images:
    import glob
    for img in glob.glob(pattern)[:2]:  # Test 2 per category
        video = test_svd_animation(img)
```

**Success Criteria:**
- ✅ Generates smooth 1-second videos
- ⚠️ Motion is relevant to content (not arbitrary)
- ✅ No major artifacts or glitches
- ✅ Can enhance static educational content

**Decision Point:**
- ✅ **PASS:** Use for supplementary animations
- ⚠️ **PARTIAL:** Use sparingly, manual curation needed
- ❌ **FAIL:** Skip image-to-video, focus on code-based animation

---

### Test 3B: Interactive Tools - Desmos API (4-6 hours) 🥉

**Why:** Test if interactive graphs add educational value

**Setup:**
```bash
# JavaScript/HTML - no Python package needed
```

**Test Cases:**
1. **Function Visualization**
   - Create: `y = mx + b` with sliders for m and b
   - Expected: Interactive graph, students adjust slope/intercept

2. **Parametric Exploration**
   - Create: Circle equation with radius slider
   - Expected: Circle changes size dynamically

**Implementation:**
```html
<!-- test_desmos_integration.html -->
<!DOCTYPE html>
<html>
<head>
    <script src="https://www.desmos.com/api/v1.11/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6"></script>
</head>
<body>
    <div id="calculator" style="width: 600px; height: 400px;"></div>

    <script>
        var elt = document.getElementById('calculator');
        var calculator = Desmos.GraphingCalculator(elt);

        // Test Case 1: Linear function with sliders
        calculator.setExpression({ id: 'm', latex: 'm=1', sliderBounds: {min: -5, max: 5} });
        calculator.setExpression({ id: 'b', latex: 'b=0', sliderBounds: {min: -10, max: 10} });
        calculator.setExpression({ id: 'line', latex: 'y=mx+b', color: '#2d70b3' });

        console.log('✓ Desmos interactive graph loaded');
    </script>
</body>
</html>
```

**Python Integration:**
```python
# test_desmos_generator.py
def generate_desmos_embed(concept: str) -> str:
    """Generate Desmos embed code for interactive concept"""

    # Use LLM to generate Desmos expressions
    prompt = f"""Generate Desmos calculator expressions for: {concept}

    Output as JavaScript array of expression objects:
    [
        {{id: 'var1', latex: 'm=1', sliderBounds: {{min: -5, max: 5}}}},
        {{id: 'graph1', latex: 'y=mx+b', color: '#2d70b3'}}
    ]
    """

    # ... LLM call to generate expressions ...

    return f"""
    <script src="https://www.desmos.com/api/v1.11/calculator.js"></script>
    <div id="calculator" style="width: 600px; height: 400px;"></div>
    <script>
        var calculator = Desmos.GraphingCalculator(document.getElementById('calculator'));
        {expressions}
    </script>
    """

# Test
embed = generate_desmos_embed("Linear function with adjustable slope and intercept")
print(embed)
```

**Success Criteria:**
- ✅ Generates valid Desmos embed code
- ✅ Students can interact and explore
- ✅ Easy to integrate into mini_agent
- ✅ Educational value over static images

**Decision Point:**
- ✅ **PASS:** Add as enhancement for explorations
- ⚠️ **PARTIAL:** Use for specific concept types only
- ❌ **FAIL:** Not worth complexity, stick to static/animated

---

## Phase 4: Optional Advanced (Week 3)

**Goal:** Test cutting-edge approaches if time/budget permits

### Test 4A: CogVideoX (Open-Source Video) (2-3 days) ⚪

**Why:** Longer animations (6-10s), open-source, education-focused

**Setup:**
```bash
pip install torch diffusers transformers accelerate
# Requires GPU with 16GB+ VRAM
```

**Test Case:**
```python
# test_cogvideox.py
from diffusers import CogVideoXPipeline
import torch

pipeline = CogVideoXPipeline.from_pretrained(
    "THUDM/CogVideoX-5b",
    torch_dtype=torch.float16
)
pipeline.to("cuda")

prompt = "A mathematical animation showing how a parabola y=x² transforms into y=2x² by stretching vertically, educational style"

video = pipeline(
    prompt=prompt,
    num_frames=49,  # 49 frames = ~6 seconds at 8fps
    guidance_scale=6,
).frames[0]

# Save video
from moviepy.editor import ImageSequenceClip
clip = ImageSequenceClip([f for f in video], fps=8)
clip.write_videofile('cogvideo_test.mp4')
```

**Success Criteria:**
- ✅ Generates 6+ second videos
- ✅ Educational style maintained
- ✅ Worth the computational cost

---

### Test 4B: Commercial API Comparison (Variable time) ⚪

**If budget allows, test:**

1. **Runway Gen-3** (Professional quality)
2. **Pika** (Stylized, quick)
3. **Kling AI** (Up to 2 minutes)

**Method:** Sign up for free trials, test same prompts across platforms

---

## Evaluation Matrix

Track results in this table:

| Approach | Test Status | Quality (1-5) | Speed (1-5) | Cost | Recommended Use |
|----------|-------------|---------------|-------------|------|-----------------|
| **Matplotlib + GPT-4** | ⬜ Not tested<br>✅ Pass<br>❌ Fail | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Low | Graphs, plots, data viz |
| **DALL-E 3** | ⬜ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medium | Conceptual diagrams |
| **SVG + GPT-4** | ⬜ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Low | Geometric precision |
| **Manim + Claude** | ⬜ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Low | Math animations |
| **SVD** | ⬜ | ⭐⭐⭐ | ⭐⭐⭐ | Low | Image animation |
| **Desmos API** | ⬜ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free | Interactive exploration |
| **CogVideoX** | ⬜ | ⭐⭐⭐⭐ | ⭐⭐ | Free | Longer videos |

---

## Decision Framework

After testing, use this framework to decide:

### For Static Content:

```
START
  ↓
Need graphs/plots? → YES → Matplotlib + GPT-4
  ↓ NO
Need geometric precision? → YES → SVG + GPT-4
  ↓ NO
Conceptual/artistic? → YES → DALL-E 3
  ↓ NO
Need interactivity? → YES → Desmos/GeoGebra
  ↓ NO
Use Matplotlib (default)
```

### For Animated Content:

```
START
  ↓
Need mathematical precision? → YES → Manim + Claude
  ↓ NO
Simple transformation? → YES → Morphing
  ↓ NO
Have static image? → YES → Stable Video Diffusion
  ↓ NO
Need 6+ seconds? → YES → CogVideoX
  ↓ NO
Premium budget? → YES → Commercial APIs
  ↓ NO
Use Manim (default)
```

---

## Quick Start Commands

### Day 1 Morning (Matplotlib):
```bash
cd /home/user/mini_agent
python -m venv test_env
source test_env/bin/activate
pip install matplotlib numpy openai python-dotenv
export OPENAI_API_KEY="your-key"
python research/tests/test_matplotlib_generation.py
```

### Day 1 Afternoon (DALL-E):
```bash
# Same environment
python research/tests/test_dalle_diagrams.py
```

### Day 2 (SVG):
```bash
pip install svgwrite cairosvg
python research/tests/test_svg_generation.py
```

### Day 3-4 (Manim):
```bash
# Install Manim (may take 30-60 min)
pip install manim
brew install ffmpeg  # or apt-get install ffmpeg
export ANTHROPIC_API_KEY="your-key"
python research/tests/test_manim_generation.py
```

---

## Success Metrics

**After Week 1, you should know:**
- ✅ Which approach works best for graphs (likely Matplotlib)
- ✅ Whether DALL-E is good enough for diagrams
- ✅ If SVG generation is reliable enough
- ✅ If Manim animations are worth the setup

**After Week 2, you should have:**
- ✅ A working prototype of top 2-3 approaches
- ✅ Performance benchmarks (time, quality, cost)
- ✅ Integration plan for mini_agent
- ✅ Decision on which approaches to productionize

**Final Deliverable:**
- 📊 Completed evaluation matrix
- 🎯 Recommended stack (e.g., "Matplotlib + Manim + DALL-E")
- 📝 Integration roadmap for mini_agent
- 💾 Test outputs demonstrating capabilities

---

## Troubleshooting

### Matplotlib Generation Issues:
- **Problem:** Code doesn't execute
- **Fix:** Add validation layer, catch syntax errors, retry with Claude

### DALL-E Poor Quality:
- **Problem:** Labels unclear, wrong style
- **Fix:** Improve prompt refinement with GPT-4, add more style keywords

### Manim Rendering Fails:
- **Problem:** Syntax errors, missing imports
- **Fix:** Use simpler prompts, provide more examples to Claude, manual debugging

### SVD Artifacts:
- **Problem:** Weird motion, glitches
- **Fix:** Adjust motion_bucket_id (lower = less motion), try different source images

---

## Next Steps After Testing

1. **Document Results:** Fill evaluation matrix
2. **Create Integration Plan:** Based on what works
3. **Build Prototypes:** Implement top 2 approaches in mini_agent
4. **User Testing:** Get feedback from educators
5. **Iterate:** Refine based on real-world usage

---

**Timeline Summary:**
- **Week 1:** Quick wins + core capabilities (Matplotlib, DALL-E, SVG, Manim)
- **Week 2:** Advanced testing (SVD, Desmos, comparisons)
- **Week 3:** Optional (CogVideoX, commercial APIs, refinement)

**Expected Outcome:**
By end of Week 1, you'll have a clear answer on what works best for your use case and can make informed decisions about implementation priorities.

---

**Document Version:** 1.0
**Created:** 2025-11-09
**Purpose:** Fast-track testing to find optimal material generation solution
**Companion to:** research/math_to_visual_illustration_generation.md

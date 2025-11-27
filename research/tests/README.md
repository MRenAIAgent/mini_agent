# Material Generation Test Suite

Practical test scripts for evaluating material generation approaches.

## Quick Start

### Prerequisites

```bash
# Create virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install base dependencies
pip install matplotlib numpy openai python-dotenv

# Optional: For SVG tests
pip install cairosvg svgwrite

# Optional: For animation tests
pip install anthropic manim diffusers torch
```

### Set API Keys

```bash
export OPENAI_API_KEY='your-openai-key'
export ANTHROPIC_API_KEY='your-anthropic-key'  # For Manim tests
```

## Running Tests

### Test 1A: Matplotlib Generation (Start Here!) 🥇

**Time:** 2-3 hours
**Cost:** ~$0.50 in API calls
**What it tests:** Can GPT-4 generate matplotlib code for graphs?

```bash
cd research/tests
python test_matplotlib_generation.py
```

**Expected outputs:**
- `test_1a_linear.png` - Linear function plot
- `test_1a_quadratics.png` - Quadratic comparison
- `test_1a_trig.png` - Sin/cos visualization
- `test_1a_derivative.png` - Function and its derivative

**Success criteria:**
- All 4 tests should pass (✓ PASS)
- Images should be clear, labeled, and educational
- Code should execute without errors

---

### Test 2A: SVG Generation 🥈

**Time:** 4-6 hours
**Cost:** ~$0.75 in API calls
**What it tests:** Can GPT-4 generate precise geometric SVG diagrams?

```bash
python test_svg_generation.py
```

**Expected outputs:**
- `test_2a_triangle.svg` - Isosceles triangle
- `test_2a_coordinate.svg` - Coordinate plane
- `test_2a_pythagoras.svg` - Pythagorean theorem diagram
- `test_2a_circle.svg` - Circle with inscribed angle
- `test_2a_parabola.svg` - Parabola graph

Plus PNG conversions if cairosvg is installed.

**Success criteria:**
- At least 4/5 tests should produce valid SVG
- SVG should be geometrically accurate
- Labels should be clear and positioned correctly

---

## Test Results Tracking

Use this template to track your results:

```
Date: ___________
Tester: ___________

Test 1A: Matplotlib Generation
[ ] Pass (4/4) [ ] Partial (2-3/4) [ ] Fail (0-1/4)
Notes: ___________________________________________

Test 2A: SVG Generation
[ ] Pass (4-5/5) [ ] Partial (2-3/5) [ ] Fail (0-1/5)
Notes: ___________________________________________

Decision:
[ ] Proceed with Matplotlib + SVG
[ ] Try alternative approaches
[ ] Need more testing
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'openai'"

```bash
pip install openai
```

### "OPENAI_API_KEY not set"

```bash
export OPENAI_API_KEY='sk-...'
```

### Matplotlib plots are blank

- Check that code includes `plt.savefig()` not `plt.show()`
- Verify file permissions in output directory

### SVG won't render

- Open SVG file in browser to check if it's valid
- Install cairosvg for PNG conversion: `pip install cairosvg`

### API rate limits

- Add delays between tests if needed
- Use lower-cost models for testing (gpt-3.5-turbo)

## Next Steps

After running tests:

1. **Review outputs** - Open generated images/SVGs
2. **Fill evaluation matrix** - See `testing_roadmap_material_generation.md`
3. **Make decision** - Based on success criteria
4. **Integrate** - Add working approaches to mini_agent

## File Structure

```
research/tests/
├── README.md                          # This file
├── test_matplotlib_generation.py      # Test 1A (Start here!)
├── test_svg_generation.py             # Test 2A
└── (future)
    ├── test_manim_generation.py       # Test 2B
    ├── test_dalle_diagrams.py         # Test 1B
    └── test_svd_animation.py          # Test 3A
```

## Contributing

To add new tests:

1. Follow the naming convention: `test_<name>_<approach>.py`
2. Include docstring with Priority and Time estimate
3. Return results dictionary for evaluation matrix
4. Print clear success/fail messages

## Support

- See full roadmap: `research/testing_roadmap_material_generation.md`
- See research: `research/math_to_visual_illustration_generation.md`
- Report issues: Create issue in repo with test output

---

**Last Updated:** 2025-11-09
**Version:** 1.0

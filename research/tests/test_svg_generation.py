"""
Test 2A: SVG Code Generation via GPT-4
Priority: P1 (High - Core Capability)
Time: 4-6 hours
"""

import asyncio
import os
from typing import Optional
import re

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from cairosvg import svg2png
    HAS_CAIRO = True
except ImportError:
    HAS_CAIRO = False
    print("⚠️  Warning: cairosvg not installed. PNG conversion will be skipped.")
    print("   Install with: pip install cairosvg")


class SVGGenerator:
    """Test GPT-4 generating SVG code for geometric diagrams"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

    async def generate(self, description: str, output_file: str = None) -> tuple[str, bool]:
        """
        Generate SVG code from description

        Returns:
            (svg_code, valid): Generated SVG and whether it's valid
        """

        prompt = f"""Generate SVG code for the following geometric diagram:
{description}

Requirements:
- Valid SVG syntax with proper namespace
- ViewBox appropriate for content (typically 0 0 400 300 or similar)
- Clear labels using <text> elements with readable font size (14-16px)
- Use geometric precision for mathematical accuracy
- Include comments for key elements
- Use appropriate colors (not too bright, educational style)
- Stroke width 2-3 for main elements
- Grid or coordinate system if relevant

Output ONLY the SVG code starting with <svg> tag, no explanations.

Example format:
<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
  <style>
    text {{ font-family: Arial, sans-serif; font-size: 14px; }}
  </style>
  <!-- Your diagram here -->
</svg>
"""

        client = openai.AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3  # Lower temperature for more consistent geometric output
        )

        svg_code = response.choices[0].message.content

        # Extract SVG if wrapped in markdown
        if "```svg" in svg_code:
            svg_code = svg_code.split("```svg")[1].split("```")[0].strip()
        elif "```xml" in svg_code:
            svg_code = svg_code.split("```xml")[1].split("```")[0].strip()
        elif "```" in svg_code:
            svg_code = svg_code.split("```")[1].split("```")[0].strip()

        # Validate SVG
        valid = self._validate_svg(svg_code)

        # Save SVG
        filename = output_file or f'svg_test_{hash(description)}.svg'
        with open(filename, 'w') as f:
            f.write(svg_code)

        print(f"✓ SVG saved: {filename}")

        # Convert to PNG if possible
        if valid and HAS_CAIRO:
            try:
                png_filename = filename.replace('.svg', '.png')
                svg2png(bytestring=svg_code.encode('utf-8'),
                       write_to=png_filename,
                       output_width=800)
                print(f"✓ PNG saved: {png_filename}")
            except Exception as e:
                print(f"⚠️  PNG conversion failed: {e}")

        return svg_code, valid

    def _validate_svg(self, svg_code: str) -> bool:
        """Basic SVG validation"""
        try:
            # Check for SVG tags
            if "<svg" not in svg_code or "</svg>" not in svg_code:
                print("✗ Missing <svg> tags")
                return False

            # Check for viewBox
            if "viewBox" not in svg_code:
                print("⚠️  Warning: No viewBox attribute (may not scale properly)")

            # Check for xmlns
            if "xmlns" not in svg_code:
                print("⚠️  Warning: No xmlns attribute")

            # Basic syntax check - balanced tags
            open_tags = len(re.findall(r'<(\w+)', svg_code))
            close_tags = len(re.findall(r'</(\w+)>', svg_code)) + len(re.findall(r'/>', svg_code))

            if open_tags != close_tags:
                print(f"⚠️  Warning: Possibly unbalanced tags (open: {open_tags}, close: {close_tags})")

            return True

        except Exception as e:
            print(f"✗ Validation error: {e}")
            return False


async def run_test_suite():
    """Run all SVG generation tests"""

    print("=" * 60)
    print("TEST 2A: SVG CODE GENERATION")
    print("=" * 60)
    print()

    generator = SVGGenerator()

    test_cases = [
        {
            "name": "Isosceles Triangle",
            "description": "Isosceles triangle with base 100 units, height 120 units, labeled vertices A (top), B (bottom left), C (bottom right)",
            "file": "test_2a_triangle.svg"
        },
        {
            "name": "Coordinate Plane",
            "description": "Coordinate plane from -10 to 10 on both x and y axes, with grid lines every 1 unit, and point (3, 4) marked with a red dot and labeled",
            "file": "test_2a_coordinate.svg"
        },
        {
            "name": "Pythagorean Theorem",
            "description": "Right triangle with sides a=3, b=4, c=5, showing squares on each side to visualize a² + b² = c²",
            "file": "test_2a_pythagoras.svg"
        },
        {
            "name": "Circle with Inscribed Angle",
            "description": "Circle with center O, arc AB, inscribed angle ACB, and central angle AOB to demonstrate the inscribed angle theorem",
            "file": "test_2a_circle.svg"
        },
        {
            "name": "Function Graph",
            "description": "Coordinate system showing the parabola y = x² - 4 with x-intercepts, y-intercept, and vertex labeled",
            "file": "test_2a_parabola.svg"
        }
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}/{len(test_cases)}] {test['name']}")
        print(f"Description: {test['description'][:60]}...")
        print("Generating SVG...")

        try:
            svg_code, valid = await generator.generate(test['description'], test['file'])

            results.append({
                'name': test['name'],
                'valid': valid,
                'file': test['file']
            })

            if valid:
                print(f"✓ PASS - Valid SVG generated")
            else:
                print(f"⚠️  PARTIAL - SVG generated but may have issues")

            # Show SVG stats
            lines = svg_code.split('\n')
            elements = len(re.findall(r'<\w+', svg_code))
            print(f"  Lines: {len(lines)}, Elements: {elements}")

        except Exception as e:
            print(f"✗ ERROR: {e}")
            results.append({
                'name': test['name'],
                'valid': False,
                'file': test['file']
            })

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    valid = sum(1 for r in results if r['valid'])
    total = len(results)

    for result in results:
        status = "✓ PASS" if result['valid'] else "✗ FAIL"
        print(f"{status}: {result['name']} - {result['file']}")

    print(f"\nScore: {valid}/{total} ({100*valid//total if total > 0 else 0}%)")

    # Decision
    print("\n" + "=" * 60)
    print("DECISION POINT")
    print("=" * 60)

    if valid >= total * 0.8:
        print("✅ PASSED (Good enough for production)")
        print("Recommendation: Use as primary method for geometric diagrams")
        print("Next step: Integrate into mini_agent with validation layer")
    elif valid >= total * 0.6:
        print("⚠️  PARTIAL PASS")
        print("Recommendation: Use with manual review or add retry logic")
        print("Next step: Implement validation + retry mechanism")
    else:
        print("❌ FAILED")
        print("Recommendation: Fall back to DALL-E or try StarVector model")
        print("Next step: Test alternative SVG generation approaches")

    return results


if __name__ == "__main__":
    print("\n🧪 Starting SVG Generation Tests\n")
    print("Make sure you have set OPENAI_API_KEY in your environment:\n")
    print("  export OPENAI_API_KEY='your-api-key-here'\n")

    if not HAS_CAIRO:
        print("⚠️  Optional: Install cairosvg for PNG conversion")
        print("  pip install cairosvg\n")

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not set")
        print("Please set your OpenAI API key and try again.")
        exit(1)

    results = asyncio.run(run_test_suite())

    print("\n✨ Testing complete!")
    print(f"📁 SVG files saved in current directory")
    if HAS_CAIRO:
        print(f"📁 PNG conversions also saved")

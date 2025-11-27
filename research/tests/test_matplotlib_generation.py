"""
Test 1A: Matplotlib Code Generation
Priority: P0 (Highest - Quick Win)
Time: 2-3 hours
"""

import asyncio
import os
from typing import Optional
import matplotlib.pyplot as plt
import numpy as np

# Support both OpenAI and LiteLLM
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from litellm import acompletion
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False


class MatplotlibGenerator:
    """Test GPT-4 generating matplotlib code for educational content"""

    def __init__(self, api_key: Optional[str] = None, use_litellm: bool = False):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.use_litellm = use_litellm or HAS_LITELLM and not HAS_OPENAI

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.system_prompt = """You are a matplotlib code generator for educational content.
Generate clean, well-commented Python code using matplotlib and numpy.

Requirements:
- Use numpy for data generation
- Include clear labels, title, legend
- Use appropriate colors and line styles
- Add grid for readability
- Set figure size to (10, 6)
- Use tight_layout()
- Return ONLY executable Python code, no explanations
- Do not include plt.show(), only plt.savefig()

Output format:
```python
import matplotlib.pyplot as plt
import numpy as np

# Your code here
plt.savefig('output.png', dpi=150, bbox_inches='tight')
```
"""

    async def generate(self, prompt: str, output_file: str = None) -> tuple[str, bool]:
        """
        Generate matplotlib code from prompt

        Returns:
            (code, success): Generated code and whether execution succeeded
        """

        if self.use_litellm:
            response = await acompletion(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                api_key=self.api_key
            )
            code = response.choices[0].message.content
        else:
            client = openai.AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            code = response.choices[0].message.content

        # Extract code if wrapped in markdown
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        # Execute in sandbox
        success = await self._execute_code(code, output_file or f'test_output_{hash(prompt)}.png')

        return code, success

    async def _execute_code(self, code: str, output_file: str) -> bool:
        """Execute generated code safely"""
        try:
            # Create safe execution environment
            exec_globals = {
                'plt': plt,
                'np': np,
                '__builtins__': __builtins__
            }

            # Modify code to use our output file
            code = code.replace("'output.png'", f"'{output_file}'")
            code = code.replace('"output.png"', f'"{output_file}"')

            # Execute
            exec(code, exec_globals)

            # Close any open figures
            plt.close('all')

            print(f"✓ Successfully generated: {output_file}")
            return True

        except Exception as e:
            print(f"✗ Execution failed: {e}")
            return False


async def run_test_suite():
    """Run all matplotlib generation tests"""

    print("=" * 60)
    print("TEST 1A: MATPLOTLIB CODE GENERATION")
    print("=" * 60)
    print()

    generator = MatplotlibGenerator()

    test_cases = [
        {
            "name": "Linear Function",
            "prompt": "Plot y = 2x + 3 from x=-10 to x=10 with clear labels and grid",
            "file": "test_1a_linear.png"
        },
        {
            "name": "Quadratic Comparison",
            "prompt": "Compare y = x², y = 2x², and y = -x² on the same graph with different colors and a legend",
            "file": "test_1a_quadratics.png"
        },
        {
            "name": "Trigonometric Functions",
            "prompt": "Show sin(x) and cos(x) from 0 to 2π with the phase difference region shaded",
            "file": "test_1a_trig.png"
        },
        {
            "name": "Derivative Visualization",
            "prompt": "Plot f(x) = x³ - 3x² + 2 and its derivative f'(x) = 3x² - 6x on the same axes",
            "file": "test_1a_derivative.png"
        }
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}/{len(test_cases)}] {test['name']}")
        print(f"Prompt: {test['prompt']}")
        print("Generating code...")

        try:
            code, success = await generator.generate(test['prompt'], test['file'])

            results.append({
                'name': test['name'],
                'success': success,
                'file': test['file']
            })

            if success:
                print(f"✓ PASS - Output saved to: {test['file']}")
            else:
                print(f"✗ FAIL - Code generation or execution failed")

            # Show generated code (first 5 lines)
            code_lines = code.split('\n')
            print("\nGenerated code (preview):")
            for line in code_lines[:5]:
                print(f"  {line}")
            if len(code_lines) > 5:
                print(f"  ... ({len(code_lines) - 5} more lines)")

        except Exception as e:
            print(f"✗ ERROR: {e}")
            results.append({
                'name': test['name'],
                'success': False,
                'file': test['file']
            })

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r['success'])
    total = len(results)

    for result in results:
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        print(f"{status}: {result['name']}")

    print(f"\nScore: {passed}/{total} ({100*passed//total}%)")

    # Decision
    print("\n" + "=" * 60)
    print("DECISION POINT")
    print("=" * 60)

    if passed == total:
        print("✅ ALL TESTS PASSED")
        print("Recommendation: Integrate into mini_agent immediately")
        print("Next step: Test 1B (DALL-E 3 Diagrams)")
    elif passed >= total * 0.75:
        print("⚠️  MOSTLY PASSED")
        print("Recommendation: Proceed with caution, improve prompt engineering")
        print("Next step: Refine prompts and retry failed cases")
    else:
        print("❌ FAILED")
        print("Recommendation: Try Claude 3.5 instead of GPT-4")
        print("Next step: Modify generator to use Claude Sonnet")

    return results


if __name__ == "__main__":
    print("\n🧪 Starting Matplotlib Generation Tests\n")
    print("Make sure you have set OPENAI_API_KEY in your environment:\n")
    print("  export OPENAI_API_KEY='your-api-key-here'\n")

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not set")
        print("Please set your OpenAI API key and try again.")
        exit(1)

    results = asyncio.run(run_test_suite())

    print("\n✨ Testing complete!")
    print(f"📁 Output files saved in current directory")

#!/usr/bin/env python3
"""
LLM API Benchmark Tool
Tests top hosting providers with gpt-oss-120b model for speed and accuracy comparison
"""

import os
import time
import json
import statistics
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    import requests
except ImportError:
    print("Installing requests library...")
    import subprocess
    subprocess.check_call(["pip", "install", "requests"])
    import requests


class LLMBenchmark:
    """Benchmark tool for testing LLM API providers"""

    def __init__(self):
        self.results = []
        self.test_prompts = [
            {
                "role": "user",
                "content": "Explain quantum computing in exactly 100 words.",
                "expected_tokens": 120  # approximate
            },
            {
                "role": "user",
                "content": "Write a Python function to calculate fibonacci numbers using dynamic programming.",
                "expected_tokens": 200
            },
            {
                "role": "user",
                "content": "What are the key differences between REST and GraphQL APIs? List 5 points.",
                "expected_tokens": 150
            }
        ]

        self.providers = {
            "cerebras": {
                "name": "Cerebras",
                "base_url": "https://api.cerebras.ai/v1/chat/completions",
                "model": "gpt-oss-120b",
                "api_key_env": "CEREBRAS_API_KEY"
            },
            "groq": {
                "name": "Groq",
                "base_url": "https://api.groq.com/openai/v1/chat/completions",
                "model": "gpt-oss-120b",
                "api_key_env": "GROQ_API_KEY"
            },
            "together": {
                "name": "Together AI",
                "base_url": "https://api.together.xyz/v1/chat/completions",
                "model": "gpt-oss-120b",
                "api_key_env": "TOGETHER_API_KEY"
            }
        }

    def check_api_keys(self) -> Dict[str, bool]:
        """Check which API keys are available"""
        available = {}
        for provider_id, config in self.providers.items():
            api_key = os.getenv(config["api_key_env"])
            available[provider_id] = api_key is not None and api_key.strip() != ""
            if available[provider_id]:
                print(f"✓ {config['name']}: API key found")
            else:
                print(f"✗ {config['name']}: API key not found (set {config['api_key_env']})")
        return available

    def make_api_call(
        self,
        provider_id: str,
        prompt: str,
        max_tokens: int = 300
    ) -> Optional[Dict]:
        """Make a single API call and measure performance"""

        config = self.providers[provider_id]
        api_key = os.getenv(config["api_key_env"])

        if not api_key:
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False
        }

        try:
            # Measure total time
            start_time = time.time()
            response = requests.post(
                config["base_url"],
                headers=headers,
                json=payload,
                timeout=60
            )
            end_time = time.time()

            if response.status_code != 200:
                print(f"  ✗ {config['name']} error: {response.status_code} - {response.text[:200]}")
                return {
                    "provider": config["name"],
                    "error": f"HTTP {response.status_code}",
                    "success": False
                }

            result = response.json()
            total_time = end_time - start_time

            # Extract response data
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            completion_tokens = usage.get("completion_tokens", 0)

            # Calculate metrics
            tokens_per_second = completion_tokens / total_time if total_time > 0 else 0

            return {
                "provider": config["name"],
                "success": True,
                "total_time": total_time,
                "completion_tokens": completion_tokens,
                "tokens_per_second": tokens_per_second,
                "response": content,
                "usage": usage
            }

        except requests.exceptions.Timeout:
            print(f"  ✗ {config['name']}: Request timeout")
            return {"provider": config["name"], "error": "Timeout", "success": False}
        except Exception as e:
            print(f"  ✗ {config['name']}: {str(e)}")
            return {"provider": config["name"], "error": str(e), "success": False}

    def run_benchmark(self, num_runs: int = 3) -> List[Dict]:
        """Run complete benchmark across all providers"""

        print("\n" + "="*70)
        print("LLM API Benchmark - Testing gpt-oss-120b")
        print("="*70)

        # Check API keys
        print("\n📋 Checking API Keys:")
        available = self.check_api_keys()

        active_providers = [p for p, avail in available.items() if avail]
        if not active_providers:
            print("\n❌ No API keys found. Please set environment variables:")
            for config in self.providers.values():
                print(f"   export {config['api_key_env']}=your_key_here")
            return []

        print(f"\n🚀 Running benchmark with {len(active_providers)} provider(s)")
        print(f"   Test runs per prompt: {num_runs}")
        print(f"   Test prompts: {len(self.test_prompts)}\n")

        all_results = []

        # Run tests
        for prompt_idx, test_prompt in enumerate(self.test_prompts, 1):
            print(f"\n{'─'*70}")
            print(f"Test {prompt_idx}/{len(self.test_prompts)}: {test_prompt['content'][:50]}...")
            print(f"{'─'*70}")

            for provider_id in active_providers:
                provider_name = self.providers[provider_id]["name"]
                print(f"\n  Testing {provider_name}...")

                run_results = []
                for run in range(num_runs):
                    print(f"    Run {run + 1}/{num_runs}...", end=" ")
                    result = self.make_api_call(
                        provider_id,
                        test_prompt["content"],
                        max_tokens=test_prompt["expected_tokens"] + 50
                    )

                    if result and result.get("success"):
                        print(f"✓ {result['tokens_per_second']:.1f} t/s in {result['total_time']:.2f}s")
                        run_results.append(result)
                    else:
                        print(f"✗ Failed")

                    # Small delay between runs
                    if run < num_runs - 1:
                        time.sleep(1)

                if run_results:
                    # Calculate statistics
                    avg_time = statistics.mean(r['total_time'] for r in run_results)
                    avg_tps = statistics.mean(r['tokens_per_second'] for r in run_results)

                    all_results.append({
                        "provider": provider_name,
                        "prompt_index": prompt_idx,
                        "prompt": test_prompt["content"][:100],
                        "runs": len(run_results),
                        "avg_total_time": avg_time,
                        "avg_tokens_per_second": avg_tps,
                        "avg_completion_tokens": statistics.mean(r['completion_tokens'] for r in run_results),
                        "sample_response": run_results[0]['response'][:200] + "..." if len(run_results[0]['response']) > 200 else run_results[0]['response'],
                        "raw_results": run_results
                    })

                    print(f"  → Average: {avg_tps:.1f} t/s, {avg_time:.2f}s")

        self.results = all_results
        return all_results

    def generate_comparison_report(self) -> str:
        """Generate a detailed comparison report"""

        if not self.results:
            return "No benchmark results available."

        # Aggregate by provider
        provider_stats = {}
        for result in self.results:
            provider = result["provider"]
            if provider not in provider_stats:
                provider_stats[provider] = {
                    "times": [],
                    "tps": [],
                    "tokens": [],
                    "responses": []
                }

            provider_stats[provider]["times"].append(result["avg_total_time"])
            provider_stats[provider]["tps"].append(result["avg_tokens_per_second"])
            provider_stats[provider]["tokens"].append(result["avg_completion_tokens"])
            provider_stats[provider]["responses"].append(result["sample_response"])

        # Build report
        report = []
        report.append("\n" + "="*80)
        report.append("BENCHMARK RESULTS - GPT-OSS-120B COMPARISON")
        report.append("="*80)
        report.append(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Model: gpt-oss-120b")
        report.append(f"Providers Tested: {len(provider_stats)}")
        report.append(f"Test Prompts: {len(self.test_prompts)}")

        # Overall comparison table
        report.append("\n" + "─"*80)
        report.append("OVERALL PERFORMANCE COMPARISON")
        report.append("─"*80)
        report.append(f"\n{'Provider':<20} {'Avg Speed (t/s)':<18} {'Avg Time (s)':<15} {'Avg Tokens':<12}")
        report.append("─"*80)

        sorted_providers = sorted(
            provider_stats.items(),
            key=lambda x: statistics.mean(x[1]["tps"]),
            reverse=True
        )

        for provider, stats in sorted_providers:
            avg_tps = statistics.mean(stats["tps"])
            avg_time = statistics.mean(stats["times"])
            avg_tokens = statistics.mean(stats["tokens"])

            report.append(f"{provider:<20} {avg_tps:>10.2f} t/s      {avg_time:>8.3f} s      {avg_tokens:>8.1f}")

        report.append("─"*80)

        # Detailed metrics
        report.append("\n" + "─"*80)
        report.append("DETAILED METRICS BY PROVIDER")
        report.append("─"*80)

        for provider, stats in sorted_providers:
            report.append(f"\n{provider}:")
            report.append(f"  Speed (tokens/sec):  {statistics.mean(stats['tps']):.2f} t/s")
            report.append(f"  Min Speed:           {min(stats['tps']):.2f} t/s")
            report.append(f"  Max Speed:           {max(stats['tps']):.2f} t/s")
            if len(stats['tps']) > 1:
                report.append(f"  Std Dev:             {statistics.stdev(stats['tps']):.2f} t/s")
            report.append(f"  Avg Response Time:   {statistics.mean(stats['times']):.3f} s")
            report.append(f"  Avg Tokens:          {statistics.mean(stats['tokens']):.1f}")

        # Speed ranking
        report.append("\n" + "─"*80)
        report.append("SPEED RANKING")
        report.append("─"*80)

        for rank, (provider, stats) in enumerate(sorted_providers, 1):
            avg_tps = statistics.mean(stats["tps"])
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
            report.append(f"{medal} #{rank}: {provider} - {avg_tps:.2f} tokens/second")

        # Response quality samples
        report.append("\n" + "─"*80)
        report.append("RESPONSE QUALITY SAMPLES (First Test)")
        report.append("─"*80)

        for provider, stats in sorted_providers:
            report.append(f"\n{provider} Response:")
            report.append(f"  {stats['responses'][0]}")
            report.append("")

        # Summary
        report.append("─"*80)
        report.append("SUMMARY")
        report.append("─"*80)

        fastest = sorted_providers[0]
        report.append(f"\n🏆 Fastest Provider: {fastest[0]}")
        report.append(f"   Speed: {statistics.mean(fastest[1]['tps']):.2f} tokens/second")
        report.append(f"   Avg Response Time: {statistics.mean(fastest[1]['times']):.3f} seconds")

        if len(sorted_providers) > 1:
            speed_diff = statistics.mean(fastest[1]['tps']) / statistics.mean(sorted_providers[1][1]['tps'])
            report.append(f"\n📊 Performance Gap: {fastest[0]} is {speed_diff:.2f}x faster than {sorted_providers[1][0]}")

        report.append("\n" + "="*80)

        return "\n".join(report)

    def save_results(self, filename: str = "benchmark_results.json"):
        """Save detailed results to JSON file"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "model": "gpt-oss-120b",
            "test_prompts": self.test_prompts,
            "results": self.results
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n💾 Detailed results saved to: {filename}")


def main():
    """Main benchmark execution"""

    benchmark = LLMBenchmark()

    # Run benchmark
    results = benchmark.run_benchmark(num_runs=3)

    if results:
        # Generate and print report
        report = benchmark.generate_comparison_report()
        print(report)

        # Save results
        benchmark.save_results("benchmark_results.json")

        # Save report to file
        with open("benchmark_report.txt", "w") as f:
            f.write(report)
        print("📄 Report saved to: benchmark_report.txt")
    else:
        print("\n❌ Benchmark failed. Please check API keys and try again.")
        print("\nTo set API keys, use:")
        print("  export CEREBRAS_API_KEY=your_key")
        print("  export GROQ_API_KEY=your_key")
        print("  export TOGETHER_API_KEY=your_key")


if __name__ == "__main__":
    main()

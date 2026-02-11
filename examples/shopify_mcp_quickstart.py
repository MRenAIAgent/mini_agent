#!/usr/bin/env python3
"""
Shopify MCP Quick Start

A simplified example showing how to integrate Shopify MCP with the MCP framework.
This example can run without actual Shopify credentials (in demo mode).

Usage:
    # With Shopify credentials
    export SHOPIFY_STORE_URL="your-store.myshopify.com"
    export SHOPIFY_ACCESS_TOKEN="shpat_xxxxx"
    python3 examples/shopify_mcp_quickstart.py

    # Demo mode (no credentials)
    python3 examples/shopify_mcp_quickstart.py
"""

import asyncio
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from mcp.managers.mcp_manager import MCPManager, MCPExecutionRequest
from mcp.security import SecurityContext


async def main():
    """Quick start demo."""
    print("🛍️  Shopify MCP Quick Start\n")

    # Check for credentials
    has_credentials = bool(os.getenv("SHOPIFY_STORE_URL") and os.getenv("SHOPIFY_ACCESS_TOKEN"))

    if has_credentials:
        print("✓ Shopify credentials found")
    else:
        print("ℹ️  No Shopify credentials found - running in demo mode")
        print("   Set SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN to connect to real store\n")

    # Initialize MCP Manager
    config_path = Path(__file__).parent.parent / "config"
    manager = MCPManager(
        config_path=config_path,
        enable_security=True,
        enable_audit=True,
    )
    print("✓ MCP Manager initialized\n")

    # Create security context
    context = SecurityContext(
        agent_id="quickstart-agent",
        agent_role="ecommerce_agent",
        session_id="quickstart-session",
        permissions={"read:shopify", "write:shopify"},
        environment="development",
    )
    print("✓ Security context created\n")

    # Example 1: List products (read operation)
    print("Example 1: Listing products...")
    print("-" * 50)

    request = MCPExecutionRequest(
        tool_name="shopify_list_products",
        arguments={"limit": 5, "status": "active"},
        context=context,
        schema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 250},
                "status": {"type": "string", "enum": ["active", "archived", "draft"]}
            }
        }
    )

    try:
        result = await manager.execute_tool(request)
        if result.success:
            print(f"✓ Success! Execution time: {result.execution_time:.3f}s")
            print(f"  Result: {result.result}\n")
        else:
            print(f"❌ Failed: {result.error}\n")
    except Exception as e:
        print(f"⚠️  Note: {e}")
        print("   This is expected without a real Shopify MCP server connection\n")

    # Example 2: Security policy demonstration
    print("\nExample 2: Security policy enforcement...")
    print("-" * 50)
    print("Attempting operation with sensitive data labels...")

    # Create context with PII label (will trigger policy)
    sensitive_context = SecurityContext(
        agent_id="quickstart-agent",
        agent_role="ecommerce_agent",
        session_id="quickstart-session",
        permissions={"read:shopify"},  # Missing export permission
        data_labels={"customer_data", "PII"},
        environment="development",
    )

    export_request = MCPExecutionRequest(
        tool_name="shopify_export_customers",
        arguments={"format": "csv"},
        context=sensitive_context,
    )

    try:
        result = await manager.execute_tool(export_request)
        if result.success:
            print("⚠️  Export succeeded (unexpected)")
        else:
            print("✓ Security policy correctly blocked the operation")
            if result.policy_decision:
                print(f"  Reason: {result.policy_decision.reason}\n")
    except Exception as e:
        print(f"✓ Security layer blocked: {e}\n")

    # Show statistics
    print("\nStatistics:")
    print("-" * 50)
    stats = manager.get_statistics()
    exec_stats = stats.get("execution_stats", {})
    print(f"Total executions: {exec_stats.get('total_executions', 0)}")
    print(f"Successful: {exec_stats.get('successful_executions', 0)}")
    print(f"Blocked: {exec_stats.get('blocked_executions', 0)}")
    print(f"Average time: {exec_stats.get('average_execution_time', 0):.3f}s\n")

    # Cleanup
    await manager.shutdown()

    print("=" * 50)
    print("\n✅ Quick start complete!")
    print("\nNext steps:")
    print("1. Set up Shopify credentials to connect to a real store")
    print("2. Run the full demo: python3 examples/shopify_mcp_demo.py")
    print("3. Review security policies: config/security_policies.yaml")
    print("4. Check MCP configuration: config/mcp_registry.yaml")
    print("\nSee SHOPIFY_MCP_DEMO.md for complete documentation.")


if __name__ == "__main__":
    asyncio.run(main())

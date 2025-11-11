#!/usr/bin/env python3
"""
Shopify MCP Demo

Demonstrates integration with Shopify MCP server for e-commerce operations
using the MCP security framework.

This demo shows:
1. Secure connection to Shopify MCP server
2. Product management (list, search, create)
3. Order processing
4. Customer management
5. Security policy enforcement
6. Audit logging

Prerequisites:
- Shopify store URL
- Shopify API access token with appropriate permissions
- Node.js and npx installed for running @shopify/mcp-server-shopify

Environment Variables:
- SHOPIFY_STORE_URL: Your Shopify store URL (e.g., mystore.myshopify.com)
- SHOPIFY_ACCESS_TOKEN: Your Shopify API access token
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, Any, List
import logging

# Import MCP framework components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from mcp.managers.mcp_manager import MCPManager, MCPExecutionRequest
from mcp.security import SecurityContext
from mcp.core.exceptions import MCPError, MCPSecurityError, MCPValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShopifyMCPDemo:
    """Shopify MCP demonstration class."""

    def __init__(self):
        """Initialize the demo."""
        self.manager: MCPManager = None
        self.session_id = "shopify-demo-session"
        self.agent_id = "shopify-demo-agent"

    async def setup(self):
        """Setup MCP manager and load Shopify MCP."""
        logger.info("🚀 Setting up Shopify MCP Demo")

        # Verify environment variables
        if not os.getenv("SHOPIFY_STORE_URL"):
            logger.warning("⚠️  SHOPIFY_STORE_URL not set. Using mock mode.")
        if not os.getenv("SHOPIFY_ACCESS_TOKEN"):
            logger.warning("⚠️  SHOPIFY_ACCESS_TOKEN not set. Using mock mode.")

        # Initialize MCP Manager
        config_path = Path(__file__).parent.parent / "config"
        self.manager = MCPManager(
            config_path=config_path,
            enable_security=True,
            enable_audit=True,
            enable_caching=True,
            max_retries=3,
        )

        logger.info("✓ MCP Manager initialized")

        # Load Shopify MCP
        try:
            await self._load_shopify_mcp()
            logger.info("✓ Shopify MCP loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Shopify MCP: {e}")
            logger.info("Continuing in demo mode with mock data")

    async def _load_shopify_mcp(self):
        """Load Shopify MCP server."""
        # Select and load MCPs for our e-commerce agent
        system_prompt = """
        You are an e-commerce assistant that helps manage a Shopify store.
        You can list products, manage inventory, process orders, and handle customer inquiries.
        Always prioritize data security and follow company policies.
        """

        loaded_mcps = await self.manager.select_and_load_mcps(
            system_prompt=system_prompt,
            agent_role="ecommerce_agent",
            agent_permissions={"read:shopify", "write:shopify"},
            session_id=self.session_id,
            max_mcps=5,
        )

        logger.info(f"Loaded MCPs: {loaded_mcps}")

    def _create_security_context(
        self,
        permissions: List[str] = None,
        data_labels: set = None
    ) -> SecurityContext:
        """Create security context for operations."""
        return SecurityContext(
            agent_id=self.agent_id,
            agent_role="ecommerce_agent",
            session_id=self.session_id,
            permissions=set(permissions or ["read:shopify", "write:shopify"]),
            data_labels=data_labels or {"customer_data"},
            environment="development",
        )

    async def demo_list_products(self):
        """Demo: List products from Shopify store."""
        logger.info("\n" + "="*60)
        logger.info("📦 Demo 1: List Products")
        logger.info("="*60)

        context = self._create_security_context(
            permissions=["read:shopify"]
        )

        request = MCPExecutionRequest(
            tool_name="shopify_list_products",
            arguments={
                "limit": 10,
                "status": "active"
            },
            context=context,
            schema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 250
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "archived", "draft"]
                    }
                }
            }
        )

        try:
            result = await self.manager.execute_tool(request)

            if result.success:
                logger.info("✓ Products retrieved successfully")
                logger.info(f"Result: {result.result}")
                logger.info(f"Execution time: {result.execution_time:.3f}s")
            else:
                logger.error(f"❌ Failed to retrieve products: {result.error}")

        except MCPSecurityError as e:
            logger.error(f"🔒 Security error: {e.message}")
        except MCPValidationError as e:
            logger.error(f"⚠️  Validation error: {e.message}")
        except MCPError as e:
            logger.error(f"❌ MCP error: {e.message}")

    async def demo_search_products(self):
        """Demo: Search for products."""
        logger.info("\n" + "="*60)
        logger.info("🔍 Demo 2: Search Products")
        logger.info("="*60)

        context = self._create_security_context(
            permissions=["read:shopify"]
        )

        request = MCPExecutionRequest(
            tool_name="shopify_search_products",
            arguments={
                "query": "shirt",
                "limit": 5
            },
            context=context,
            schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "maxLength": 200,
                        "strict_validation": True
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["query"]
            }
        )

        try:
            result = await self.manager.execute_tool(request)

            if result.success:
                logger.info("✓ Search completed successfully")
                logger.info(f"Found products: {result.result}")
            else:
                logger.error(f"❌ Search failed: {result.error}")

        except Exception as e:
            logger.error(f"Error during search: {e}")

    async def demo_create_product(self):
        """Demo: Create a new product."""
        logger.info("\n" + "="*60)
        logger.info("➕ Demo 3: Create Product")
        logger.info("="*60)

        context = self._create_security_context(
            permissions=["read:shopify", "write:shopify"]
        )

        product_data = {
            "title": "Demo Product - Premium T-Shirt",
            "body_html": "<p>High-quality cotton t-shirt</p>",
            "vendor": "Demo Store",
            "product_type": "Apparel",
            "tags": ["demo", "shirt", "cotton"],
            "variants": [
                {
                    "price": "29.99",
                    "sku": "DEMO-SHIRT-001",
                    "inventory_quantity": 100
                }
            ]
        }

        request = MCPExecutionRequest(
            tool_name="shopify_create_product",
            arguments={"product": product_data},
            context=context,
            schema={
                "type": "object",
                "properties": {
                    "product": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "maxLength": 255},
                            "body_html": {"type": "string", "maxLength": 10000},
                            "vendor": {"type": "string", "maxLength": 255},
                            "product_type": {"type": "string", "maxLength": 255},
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "variants": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "price": {"type": "string"},
                                        "sku": {"type": "string"},
                                        "inventory_quantity": {"type": "integer"}
                                    }
                                }
                            }
                        },
                        "required": ["title"]
                    }
                },
                "required": ["product"]
            }
        )

        try:
            result = await self.manager.execute_tool(request)

            if result.success:
                logger.info("✓ Product created successfully")
                logger.info(f"Product details: {result.result}")
            else:
                logger.error(f"❌ Failed to create product: {result.error}")

        except MCPSecurityError as e:
            logger.error(f"🔒 Security blocked product creation: {e.message}")
            logger.error(f"Policy: {e.details}")

    async def demo_get_orders(self):
        """Demo: Retrieve recent orders."""
        logger.info("\n" + "="*60)
        logger.info("📋 Demo 4: Get Recent Orders")
        logger.info("="*60)

        context = self._create_security_context(
            permissions=["read:shopify"],
            data_labels={"customer_data", "payment_info"}
        )

        request = MCPExecutionRequest(
            tool_name="shopify_list_orders",
            arguments={
                "limit": 10,
                "status": "any",
                "financial_status": "paid"
            },
            context=context,
            schema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 250
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "closed", "any"]
                    },
                    "financial_status": {
                        "type": "string",
                        "enum": ["authorized", "paid", "pending", "refunded", "any"]
                    }
                }
            }
        )

        try:
            result = await self.manager.execute_tool(request)

            if result.success:
                logger.info("✓ Orders retrieved successfully")
                logger.info(f"Order count: {len(result.result) if isinstance(result.result, list) else 'N/A'}")
                logger.info(f"Execution time: {result.execution_time:.3f}s")
            else:
                logger.error(f"❌ Failed to retrieve orders: {result.error}")

        except Exception as e:
            logger.error(f"Error retrieving orders: {e}")

    async def demo_manage_inventory(self):
        """Demo: Update product inventory."""
        logger.info("\n" + "="*60)
        logger.info("📊 Demo 5: Manage Inventory")
        logger.info("="*60)

        context = self._create_security_context(
            permissions=["read:shopify", "write:shopify"]
        )

        request = MCPExecutionRequest(
            tool_name="shopify_update_inventory",
            arguments={
                "variant_id": "12345678901234",
                "inventory_quantity": 50,
                "location_id": "98765432109876"
            },
            context=context,
            schema={
                "type": "object",
                "properties": {
                    "variant_id": {"type": "string"},
                    "inventory_quantity": {
                        "type": "integer",
                        "minimum": 0
                    },
                    "location_id": {"type": "string"}
                },
                "required": ["variant_id", "inventory_quantity"]
            }
        )

        try:
            result = await self.manager.execute_tool(request)

            if result.success:
                logger.info("✓ Inventory updated successfully")
                logger.info(f"Updated inventory: {result.result}")
            else:
                logger.error(f"❌ Failed to update inventory: {result.error}")

        except Exception as e:
            logger.error(f"Error updating inventory: {e}")

    async def demo_security_violation(self):
        """Demo: Show security policy blocking an unsafe operation."""
        logger.info("\n" + "="*60)
        logger.info("🔒 Demo 6: Security Policy Enforcement")
        logger.info("="*60)
        logger.info("Attempting to export customer data without proper permissions...")

        # Create context WITHOUT export permission
        context = self._create_security_context(
            permissions=["read:shopify"],  # Missing "export:customer_data"
            data_labels={"customer_data", "PII"}
        )

        request = MCPExecutionRequest(
            tool_name="shopify_export_customers",
            arguments={
                "format": "csv",
                "include_pii": True
            },
            context=context,
        )

        try:
            result = await self.manager.execute_tool(request)

            if result.success:
                logger.warning("⚠️  Export succeeded (unexpected)")
            else:
                logger.info("✓ Export correctly blocked by security policy")
                if result.policy_decision:
                    logger.info(f"Policy action: {result.policy_decision.action}")
                    logger.info(f"Reason: {result.policy_decision.reason}")

        except MCPSecurityError as e:
            logger.info("✓ Security policy correctly blocked the operation")
            logger.info(f"Block reason: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    async def show_statistics(self):
        """Show MCP manager statistics."""
        logger.info("\n" + "="*60)
        logger.info("📊 MCP Manager Statistics")
        logger.info("="*60)

        stats = self.manager.get_statistics()

        logger.info("\nExecution Statistics:")
        exec_stats = stats.get("execution_stats", {})
        logger.info(f"  Total executions: {exec_stats.get('total_executions', 0)}")
        logger.info(f"  Successful: {exec_stats.get('successful_executions', 0)}")
        logger.info(f"  Failed: {exec_stats.get('failed_executions', 0)}")
        logger.info(f"  Blocked: {exec_stats.get('blocked_executions', 0)}")
        logger.info(f"  Average execution time: {exec_stats.get('average_execution_time', 0):.3f}s")

        logger.info(f"\nCache Statistics:")
        logger.info(f"  Cache size: {stats.get('cache_size', 0)}")

        if "audit_stats" in stats:
            logger.info(f"\nAudit Statistics:")
            audit_stats = stats["audit_stats"]
            logger.info(f"  Total events: {audit_stats.get('total_events', 0)}")
            logger.info(f"  Security violations: {audit_stats.get('security_violations', 0)}")

    async def cleanup(self):
        """Cleanup resources."""
        logger.info("\n🧹 Cleaning up...")
        if self.manager:
            await self.manager.shutdown()
        logger.info("✓ Cleanup complete")


async def main():
    """Main demo function."""
    print("=" * 70)
    print("🛍️  SHOPIFY MCP DEMO")
    print("=" * 70)
    print("\nThis demo showcases Shopify MCP integration with:")
    print("  • Secure MCP connection management")
    print("  • Product listing and search")
    print("  • Product creation")
    print("  • Order management")
    print("  • Inventory updates")
    print("  • Security policy enforcement")
    print("  • Audit logging")
    print("\n" + "=" * 70)

    demo = ShopifyMCPDemo()

    try:
        # Setup
        await demo.setup()

        # Run demos
        await demo.demo_list_products()
        await asyncio.sleep(1)  # Rate limiting

        await demo.demo_search_products()
        await asyncio.sleep(1)

        await demo.demo_create_product()
        await asyncio.sleep(1)

        await demo.demo_get_orders()
        await asyncio.sleep(1)

        await demo.demo_manage_inventory()
        await asyncio.sleep(1)

        # Demonstrate security
        await demo.demo_security_violation()

        # Show statistics
        await demo.show_statistics()

        print("\n" + "=" * 70)
        print("✅ Demo completed successfully!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Set SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN env variables")
        print("2. Install @shopify/mcp-server-shopify: npm install -g @shopify/mcp-server-shopify")
        print("3. Customize security policies in config/security_policies.yaml")
        print("4. Review audit logs for security events")
        print("5. Integrate with your agent framework")

    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

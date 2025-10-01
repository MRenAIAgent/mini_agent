"""
Rich + StructLog Tracing

Lightweight, decorator-based tracing for AI agents using Rich for beautiful console
output and StructLog for structured logging. No external services required.
"""

import asyncio
import functools
import time
import uuid
from typing import Callable, Any, Optional, Dict
from contextlib import contextmanager

try:
    import structlog
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.tree import Tree
    from rich.panel import Panel
    from rich.text import Text
    import logging
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

# Global instances
_console = None
_logger = None
_trace_tree = None
_current_span_id = None
_detailed_mode = False

def configure_tracing(
    enable_rich_logging: bool = True,
    log_level: str = "INFO",
    show_time: bool = False,
    show_path: bool = False,
    clean_format: bool = True,
    detailed: bool = False
) -> bool:
    """
    Configure Rich + StructLog tracing.

    Args:
        enable_rich_logging: Enable Rich logging handler
        log_level: Logging level
        show_time: Show timestamps in logs
        show_path: Show file paths in logs
        clean_format: Use clean, readable format instead of verbose structured logs
        detailed: Show detailed trace information (prompts, responses, span IDs)

    Returns:
        True if successfully configured, False otherwise
    """
    global _console, _logger, _trace_tree, _detailed_mode

    if not DEPENDENCIES_AVAILABLE:
        return False

    try:
        # Set global mode
        _detailed_mode = detailed

        # Create Rich console
        _console = Console(stderr=True, width=120)

        if clean_format:
            # Use clean format - disable structured logging to console
            # Only keep essential processors for file logging if needed
            processors = [
                structlog.stdlib.filter_by_level,
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.format_exc_info,
            ]

            # Configure StructLog for minimal console output
            structlog.configure(
                processors=processors,
                wrapper_class=structlog.stdlib.BoundLogger,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )

            # Suppress default logging to avoid clutter
            logging.getLogger("mini_agent").setLevel(logging.CRITICAL)

        else:
            # Use original verbose format
            processors = [
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
            ]

            if enable_rich_logging:
                processors.append(structlog.dev.ConsoleRenderer(colors=True))

                rich_handler = RichHandler(
                    console=_console,
                    show_time=show_time,
                    show_path=show_path,
                    rich_tracebacks=True,
                    tracebacks_show_locals=True
                )

                logging.basicConfig(
                    level=getattr(logging, log_level.upper()),
                    format="%(message)s",
                    handlers=[rich_handler]
                )
            else:
                processors.append(structlog.dev.ConsoleRenderer(colors=False))

            structlog.configure(
                processors=processors,
                wrapper_class=structlog.stdlib.BoundLogger,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )

        _logger = structlog.get_logger("mini_agent")

        # Initialize trace tree
        _trace_tree = Tree("🤖 Agent Execution Trace")

        _console.print("[green]✅ Rich tracing configured with clean format![/green]")
        return True

    except Exception as e:
        if _console:
            _console.print(f"[red]❌ Failed to configure tracing: {e}[/red]")
        return False

def get_logger():
    """Get the configured StructLog logger."""
    return _logger

def get_console():
    """Get the Rich console."""
    return _console

@contextmanager
def trace_context(span_name: str, **context):
    """Context manager for creating trace spans."""
    global _current_span_id, _detailed_mode

    if not _console:
        yield
        return

    span_id = str(uuid.uuid4())[:8]
    parent_span = _current_span_id
    _current_span_id = span_id

    # Calculate indentation based on nesting level
    indent = "  " * (len([s for s in [parent_span] if s]) + 1)

    start_time = time.time()

    if _detailed_mode:
        # Add parent span info for detailed display
        if parent_span:
            context["parent_span"] = parent_span
        # Detailed format with all information
        _print_detailed_span_start(span_name, span_id, parent_span, indent, context)
    else:
        # Simple clean format
        context_str = _format_simple_context(context)
        main_text = Text()
        main_text.append(f"{indent}🚀 {span_name}", style="blue")
        if context_str:
            main_text.append(context_str)
        _console.print(main_text)

    try:
        yield span_id

        # Completion message
        duration = time.time() - start_time
        if _detailed_mode:
            _print_detailed_span_end(span_name, span_id, indent, duration, context, success=True)
        else:
            duration_str = f"{duration:.1f}s" if duration > 1.0 else f"{duration*1000:.0f}ms"
            completion_text = Text()
            completion_text.append(f"{indent}✅ {span_name}", style="green")
            completion_text.append(f" ({duration_str})", style="dim")
            _console.print(completion_text)

    except Exception as e:
        # Error message
        duration = time.time() - start_time
        if _detailed_mode:
            _print_detailed_span_end(span_name, span_id, indent, duration, context, success=False, error=str(e))
        else:
            duration_str = f"{duration:.1f}s" if duration > 1.0 else f"{duration*1000:.0f}ms"
            error_text = Text()
            error_text.append(f"{indent}❌ {span_name}", style="red")
            error_text.append(f" ({duration_str})", style="dim")
            _console.print(error_text)
            error_detail = Text()
            error_detail.append(f"{indent}   Error: {str(e)[:100]}", style="red")
            _console.print(error_detail)
        raise

    finally:
        _current_span_id = parent_span

def trace_agent_execution(operation_name: Optional[str] = None, **trace_context_data):
    """
    Decorator for tracing agent execution operations.

    Args:
        operation_name: Custom name for the operation (defaults to function name)
        **trace_context_data: Additional context data to include in traces
    """
    def decorator(func: Callable) -> Callable:
        if not DEPENDENCIES_AVAILABLE:
            return func

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"agent.{func.__name__}"

            # Extract context from arguments
            context = trace_context_data.copy()
            if args and len(args) > 0:
                context["self_type"] = args[0].__class__.__name__
            if "user_input" in kwargs:
                user_input = kwargs["user_input"]
                context["input_preview"] = str(user_input)

            # Extract user_input from args if it's the second parameter
            if len(args) > 1 and isinstance(args[1], str):
                context["input_preview"] = str(args[1])

            with trace_context(op_name, **context):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return async_wrapper(*args, **kwargs)

            op_name = operation_name or f"agent.{func.__name__}"

            context = trace_context_data.copy()
            if args and len(args) > 1:
                context["self_type"] = args[0].__class__.__name__

            with trace_context(op_name, **context):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

def trace_llm_call(model_name: Optional[str] = None, **trace_context_data):
    """
    Decorator for tracing LLM calls.

    Args:
        model_name: Name of the LLM model being called
        **trace_context_data: Additional context data to include in traces
    """
    def decorator(func: Callable) -> Callable:
        if not DEPENDENCIES_AVAILABLE:
            return func

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = f"llm.{model_name or 'call'}"

            # Extract prompt information
            context = trace_context_data.copy()
            context["model"] = model_name or "unknown"
            prompt = None
            if args and len(args) > 0:
                # Try different argument positions for prompt
                if len(args) > 1:
                    prompt = str(args[1])  # Second argument (for methods like self, prompt)
                else:
                    prompt = str(args[0])  # First argument (for functions like prompt)
            elif "prompt" in kwargs:
                prompt = str(kwargs["prompt"])

            if prompt:
                context["prompt_length"] = len(prompt)
                if _detailed_mode:
                    context["prompt_preview"] = prompt

            with trace_context(op_name, **context) as span_id:
                result = await func(*args, **kwargs)

                # Add response information for detailed mode
                if _detailed_mode and result:
                    context["response_length"] = len(str(result))
                    context["response_preview"] = str(result)

                return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return async_wrapper(*args, **kwargs)

            op_name = f"llm.{model_name or 'call'}"
            context = trace_context_data.copy()
            context["model"] = model_name or "unknown"

            with trace_context(op_name, **context):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

def trace_tool_call(tool_name: Optional[str] = None, **trace_context_data):
    """
    Decorator for tracing tool calls.

    Args:
        tool_name: Name of the tool being called
        **trace_context_data: Additional context data to include in traces
    """
    def decorator(func: Callable) -> Callable:
        if not DEPENDENCIES_AVAILABLE:
            return func

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = f"tool.{tool_name or func.__name__}"

            context = trace_context_data.copy()
            context["tool"] = tool_name or func.__name__

            # Add safe tool arguments (avoid sensitive data)
            if kwargs:
                safe_args = []
                for k, v in kwargs.items():
                    if not any(sensitive in k.lower() for sensitive in ['password', 'key', 'token', 'secret']):
                        arg_str = str(v)[:30]
                        if len(str(v)) > 30:
                            arg_str += "..."
                        safe_args.append(f"{k}={arg_str}")
                if safe_args:
                    context["args"] = ", ".join(safe_args[:3])  # Show max 3 args

            with trace_context(op_name, **context):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return async_wrapper(*args, **kwargs)

            op_name = f"tool.{tool_name or func.__name__}"
            context = trace_context_data.copy()
            context["tool"] = tool_name or func.__name__

            with trace_context(op_name, **context):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

def log_agent_state(state: Dict[str, Any], title: str = "Agent State"):
    """Log agent state information in a beautiful panel."""
    if not _console:
        return

    content = "\n".join([f"[cyan]{k}:[/cyan] {v}" for k, v in state.items()])
    panel = Panel(content, title=f"[bold blue]{title}[/bold blue]", border_style="blue", padding=(0, 1))
    _console.print(panel)

def print_trace_summary():
    """Print a summary of the current trace tree."""
    if not _console:
        return

    _console.print("\n[bold blue]🔍 Execution Complete[/bold blue]")

def _format_simple_context(context: Dict[str, Any]) -> str:
    """Format context for simple display."""
    if not context:
        return ""

    key_info = []
    for k, v in context.items():
        if k == 'model' and v and v != 'unknown':
            key_info.append(f"model={v}")
        elif k == 'tool' and v:
            key_info.append(f"tool={v}")
        elif k == 'self_type' and v and v != 'CoreAgent':  # Skip common CoreAgent
            key_info.append(f"type={v}")
        elif k == 'prompt_length' and v:
            key_info.append(f"prompt={v}chars")
        elif k == 'args' and v:
            key_info.append(str(v))
        elif k == 'input_preview' and v:
            preview = str(v)
            if len(preview) > 30:
                key_info.append(f"input=\"{preview[:30]}...\"")
            else:
                key_info.append(f"input=\"{preview}\"")

    return f" [{', '.join(key_info)}]" if key_info else ""

def _print_detailed_span_start(span_name: str, span_id: str, parent_span: Optional[str], indent: str, context: Dict[str, Any]):
    """Print detailed span start information."""
    from rich.panel import Panel
    from rich.table import Table

    # Main header
    header = Text()
    header.append(f"{indent}🚀 {span_name}", style="bold blue")
    header.append(f" (span: {span_id})", style="dim")
    _console.print(header)

    # Context details in a clean table
    if context:
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        for k, v in context.items():
            if k == 'parent_span' and v:
                table.add_row(f"{indent}  └─ parent_span:", str(v))
            elif k == 'model' and v:
                table.add_row(f"{indent}  └─ model:", str(v))
            elif k == 'prompt_length' and v:
                table.add_row(f"{indent}  └─ prompt_length:", f"{v} chars")
            elif k == 'prompt_preview' and v:
                preview = str(v)[:100] + "..." if len(str(v)) > 100 else str(v)
                table.add_row(f"{indent}  └─ prompt_preview:", f'"{preview}"')
            elif k == 'input_preview' and v:
                preview = str(v)[:60] + "..." if len(str(v)) > 60 else str(v)
                table.add_row(f"{indent}  └─ input:", f'"{preview}"')
            elif k == 'tool' and v:
                table.add_row(f"{indent}  └─ tool:", str(v))
            elif k == 'args' and v:
                table.add_row(f"{indent}  └─ args:", str(v))
            elif k == 'self_type' and v:
                table.add_row(f"{indent}  └─ type:", str(v))

        _console.print(table)

def _print_detailed_span_end(span_name: str, span_id: str, indent: str, duration: float, context: Dict[str, Any], success: bool = True, error: Optional[str] = None):
    """Print detailed span completion information."""
    from rich.table import Table

    # Status and timing
    duration_str = f"{duration:.1f}s" if duration > 1.0 else f"{duration*1000:.0f}ms"

    if success:
        status = Text()
        status.append(f"{indent}✅ {span_name}", style="bold green")
        status.append(f" ({duration_str})", style="dim")
        _console.print(status)

        # Show response info if available
        if 'response_length' in context or 'response_preview' in context:
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Key", style="cyan", no_wrap=True)
            table.add_column("Value", style="white")

            if 'response_length' in context:
                table.add_row(f"{indent}  └─ response_length:", f"{context['response_length']} chars")
            if 'response_preview' in context:
                preview = str(context['response_preview'])[:100] + "..." if len(str(context['response_preview'])) > 100 else str(context['response_preview'])
                table.add_row(f"{indent}  └─ response_preview:", f'"{preview}"')

            _console.print(table)
    else:
        status = Text()
        status.append(f"{indent}❌ {span_name}", style="bold red")
        status.append(f" ({duration_str})", style="dim")
        _console.print(status)

        if error:
            error_info = Text()
            error_info.append(f"{indent}  └─ error:", style="cyan")
            error_info.append(f' "{error[:100]}"', style="red")
            _console.print(error_info)
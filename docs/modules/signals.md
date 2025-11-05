# PyFulmen Signals Module

## Overview

The PyFulmen signals module provides enterprise-grade signal handling with cross-platform support, progressive interfaces, and comprehensive Windows fallback mechanisms. It enables graceful shutdown, configuration reloading, and custom signal handling with structured logging and telemetry integration.

## Features

### Core Signal Handling

- **Cross-platform signal support** with Windows fallback mechanisms
- **Progressive interfaces** - zero-complexity defaults with enterprise power-ups
- **Asyncio integration** for async and sync signal handlers
- **Double-tap detection** for SIGINT (Ctrl+C) handling
- **Structured logging** with contextual information
- **Telemetry emission** for observability

### Enterprise Features

- **Configuration reload workflow** with app identity validation
- **HTTP endpoint helpers** for Windows fallback signal management
- **Graceful shutdown callbacks** for cleanup operations
- **Process restart capabilities** for configuration changes
- **Comprehensive error handling** with fallback mechanisms

## Quick Start

### Basic Usage

```python
from pyfulmen.signals import on_shutdown, on_reload

# Register shutdown handler
@on_shutdown
def cleanup():
    print("Cleaning up resources...")
    # Cleanup logic here

# Register config reload handler
@on_reload
def reload_config():
    print("Reloading configuration...")
    # Reload logic here
```

### Advanced Usage with Asyncio

```python
import asyncio
from pyfulmen.signals import on_shutdown, register_with_asyncio_if_available

# Async shutdown handler
@on_shutdown
async def async_cleanup():
    await asyncio.sleep(0.1)  # Simulate async cleanup
    print("Async cleanup complete")

# Register with asyncio event loop
register_with_asyncio_if_available()
```

### Configuration Reload Workflow

```python
from pyfulmen.signals import reload_config, register_shutdown_callback

# Register shutdown callback for graceful cleanup
register_shutdown_callback(lambda: print("Shutting down database connections"))

# Trigger configuration reload (validates and restarts process if needed)
try:
    reload_config()
    print("Configuration reloaded successfully")
except RuntimeError as e:
    print(f"Config reload failed: {e}")
```

### Windows Fallback HTTP Endpoints

```python
from pyfulmen.signals import get_http_helper, build_windows_fallback_docs

# Get HTTP helper for Windows fallback
helper = get_http_helper()

# Build HTTP request for SIGHUP (config reload)
request = helper.build_sighup_request(config_path="/path/to/config.yaml")

# Generate curl command for documentation
curl_cmd = helper.format_curl_command(request)
print(curl_cmd)
# Output: curl -X POST http://localhost:8080/api/signals/sighup \
#          -H "Content-Type: application/json" \
#          -d '{"config_path": "/path/to/config.yaml"}'

# Generate Windows fallback documentation
docs = build_windows_fallback_docs()
print(docs)
```

## API Reference

### Signal Registration

#### `on_shutdown(handler)`

Register a handler for SIGTERM and SIGINT signals.

```python
@on_shutdown
def handler(signum, frame):
    print("Shutting down...")
```

#### `on_reload(handler)`

Register a handler for SIGHUP signal (configuration reload).

```python
@on_reload
def handler(signum, frame):
    print("Reloading config...")
```

#### `on_force_quit(handler)`

Register a handler for SIGQUIT signal (force quit).

```python
@on_force_quit
def handler(signum, frame):
    print("Force quitting...")
```

### Configuration Management

#### `reload_config()`

Trigger configuration reload with validation and process restart.

```python
from pyfulmen.signals import reload_config

try:
    reload_config()
except RuntimeError as e:
    print(f"Reload failed: {e}")
```

#### `register_shutdown_callback(callback)`

Register callback for graceful shutdown during config reload.

```python
from pyfulmen.signals import register_shutdown_callback

register_shutdown_callback(lambda: cleanup_database())
register_shutdown_callback(lambda: close_connections())
```

### HTTP Endpoint Helpers

#### `get_http_helper()`

Get the global HTTP endpoint helper instance.

```python
from pyfulmen.signals import get_http_helper

helper = get_http_helper()
request = helper.build_signal_request("sighup")
```

#### `build_signal_request(signal_name, base_url, headers, timeout)`

Build HTTP request for signal triggering.

```python
from pyfulmen.signals import build_signal_request

request = build_signal_request(
    signal_name="sigterm",
    base_url="http://localhost:8080",
    timeout=30
)
```

### Platform Support

#### `supports_signal(signal_name)`

Check if a signal is supported on the current platform.

```python
from pyfulmen.signals import supports_signal

if supports_signal("sighup"):
    print("SIGHUP is supported")
else:
    print("Using Windows fallback for SIGHUP")
```

## Windows Fallback Behavior

On Windows, the module provides HTTP endpoint fallbacks for signals not natively supported:

| Signal  | Windows Fallback                    | HTTP Endpoint      |
| ------- | ----------------------------------- | ------------------ |
| SIGHUP  | HTTP POST to `/api/signals/sighup`  | Config reload      |
| SIGTERM | HTTP POST to `/api/signals/sigterm` | Graceful shutdown  |
| SIGINT  | HTTP POST to `/api/signals/sigint`  | Interrupt handling |

### Windows HTTP API

```python
# SIGHUP - Configuration Reload
POST /api/signals/sighup
{
    "config_path": "/path/to/config.yaml"  # Optional
}

# SIGTERM - Graceful Shutdown
POST /api/signals/sigterm
{
    "timeout_seconds": 30  # Optional
}

# SIGINT - Interrupt
POST /api/signals/sigint
{
    "force": false  # Optional, force immediate exit
}
```

## Asyncio Integration

The module provides seamless asyncio integration for async signal handlers:

```python
import asyncio
from pyfulmen.signals import (
    on_shutdown,
    register_with_asyncio_if_available,
    is_asyncio_available
)

# Check if asyncio is available
if is_asyncio_available():
    print("Asyncio integration available")

    # Register with current event loop
    register_with_asyncio_if_available()

# Async signal handler
@on_shutdown
async def async_handler(signum, frame):
    await cleanup_async_resources()
    print("Async cleanup complete")
```

## Telemetry and Logging

The module emits structured telemetry events and logs:

### Telemetry Events

- `fulmen.signal.registered` - Signal handler registered
- `fulmen.signal.dispatched` - Signal dispatched to handlers
- `fulmen.signal.unsupported` - Unsupported signal with fallback
- `fulmen.signal.double_tap` - SIGINT double-tap detected

### Structured Logging

All operations include structured context:

- `event_type` - Type of event occurring
- `signal_name` - Name of the signal
- `platform` - Current platform
- `handler_count` - Number of registered handlers
- `error` - Error details (when applicable)

## Error Handling

The module provides comprehensive error handling with fallback mechanisms:

```python
from pyfulmen.signals import on_shutdown, get_signal_metadata

try:
    # Register handler
    @on_shutdown
    def handler(signum, frame):
        print("Shutting down...")

    # Get signal metadata
    metadata = get_signal_metadata("sigterm")
    print(f"Signal: {metadata['name']}")

except Exception as e:
    print(f"Signal handling error: {e}")
    # Fallback behavior automatically applied
```

## Performance Considerations

- **Lazy loading** - Components loaded on-demand
- **Minimal overhead** - Signal registration is O(1)
- **Efficient dispatch** - Handlers called in priority order
- **Memory efficient** - Cleanup on handler removal

## Security Considerations

- **Signal validation** - Only registered signals accepted
- **Handler isolation** - Errors don't affect other handlers
- **Safe defaults** - No signal handlers registered by default
- **HTTP security** - Windows fallback endpoints should be protected

## Migration Guide

### From Standard Library `signal`

```python
# Old way
import signal

def handler(signum, frame):
    print("Signal received")

signal.signal(signal.SIGTERM, handler)

# New way
from pyfulmen.signals import on_shutdown

@on_shutdown
def handler(signum, frame):
    print("Signal received")
```

### Benefits of Migration

- Cross-platform compatibility
- Asyncio support
- Structured logging and telemetry
- Windows fallback mechanisms
- Progressive interface design

## Examples

See the `examples/` directory for complete working examples:

- Basic signal handling
- Asyncio integration
- Configuration reload workflow
- Windows fallback HTTP endpoints
- Enterprise logging integration

## Testing

The module includes comprehensive test coverage:

```bash
# Run all signal tests
uv run pytest tests/unit/signals/

# Run specific test categories
uv run pytest tests/unit/signals/test_registry.py
uv run pytest tests/unit/signals/test_asyncio.py
uv run pytest tests/unit/signals/test_reload.py
uv run pytest tests/unit/signals/test_http.py
```

## Version History

- **v0.1.0** - Initial signal handling implementation
- **v0.2.0** - Added asyncio integration
- **v0.3.0** - Added Windows fallback mechanisms
- **v0.4.0** - Added configuration reload workflow
- **v0.5.0** - Added HTTP endpoint helpers

## Contributing

When contributing to the signals module:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure cross-platform compatibility
5. Include structured logging and telemetry
6. Test Windows fallback behavior

## License

This module is part of the PyFulmen project and follows the same license terms.

# PyFulmen Application Identity

The `pyfulmen.appidentity` module provides canonical application metadata following the Crucible app identity standard. It offers zero-dependency discovery, validation, and caching of application identity configuration from `.fulmen/app.yaml` files.

## Quick Start

### Basic Usage

```python
from pyfulmen.appidentity import get_identity

# Get current application identity
identity = get_identity()
print(f"Binary: {identity.binary_name}")
print(f"Vendor: {identity.vendor}")
print(f"Environment Prefix: {identity.env_prefix}")
```

### Loading from Explicit Path

```python
from pyfulmen.appidentity import load_from_path
from pathlib import Path

# Load identity from specific file
identity = load_from_path(Path("/path/to/.fulmen/app.yaml"))
```

### Environment Override

```bash
export FULMEN_APP_IDENTITY_PATH="/path/to/custom/app.yaml"
python -c "from pyfulmen.appidentity import get_identity; print(get_identity().binary_name)"
```

## Configuration File Format

Create a `.fulmen/app.yaml` file in your repository root:

```yaml
# Required application information
app:
  binary_name: "myapp"
  vendor: "mycompany"
  env_prefix: "MYAPP_"
  config_name: "myapp"
  description: "My awesome application"

# Optional metadata
metadata:
  project_url: "https://github.com/mycompany/myapp"
  support_email: "support@mycompany.com"
  license: "MIT"
  repository_category: "application"
  telemetry_namespace: "myapp.telemetry"
  
  # Python-specific metadata
  python:
    distribution_name: "myapp"
    package_name: "myapp_core"
    console_scripts:
      - name: "myapp"
        module: "myapp.cli:main"
```

## API Reference

### Core Functions

#### `get_identity() -> AppIdentity`
Get the current application identity using automatic discovery and caching.

**Returns:** `AppIdentity` instance

**Raises:**
- `AppIdentityNotFoundError`: If no identity file is found
- `AppIdentityValidationError`: If the identity file is invalid

#### `load_from_path(path: Path) -> AppIdentity`
Load application identity from an explicit file path.

**Parameters:**
- `path`: Path to the identity YAML file

**Returns:** `AppIdentity` instance

#### `reload_identity() -> AppIdentity`
Force reload of application identity, clearing any cached values.

**Returns:** Freshly loaded `AppIdentity` instance

#### `clear_identity_cache() -> None`
Clear all cached application identities. The next call to `get_identity()` will trigger a fresh load.

### Testing Utilities

#### `override_identity_for_testing(identity: AppIdentity) -> ContextManager`
Context manager for temporarily overriding application identity in tests.

```python
from pyfulmen.appidentity import AppIdentity, override_identity_for_testing

def test_something():
    test_identity = AppIdentity(
        binary_name="testapp",
        vendor="testvendor", 
        env_prefix="TEST_",
        config_name="testapp",
        description="Test application",
        _raw_metadata={},
        _provenance={}
    )
    
    with override_identity_for_testing(test_identity):
        identity = get_identity()  # Returns test_identity
        # ... test code here ...
    
    # Original identity restored after context
```

### Data Model

#### `AppIdentity`
Immutable dataclass containing application metadata:

**Required Fields:**
- `binary_name: str` - Application binary name
- `vendor: str` - Vendor/organization name  
- `env_prefix: str` - Environment variable prefix (must end with `_`)
- `config_name: str` - Configuration directory name
- `description: str` - Application description

**Optional Fields:**
- `project_url: str | None` - Project homepage URL
- `support_email: str | None` - Support contact email
- `license: str | None` - License identifier
- `repository_category: str | None` - Repository category
- `telemetry_namespace: str | None` - Telemetry namespace (defaults to binary_name)
- `registry_id: UUID | None` - Unique registry identifier
- `python_distribution: str | None` - Python distribution name
- `python_package: str | None` - Python package name
- `console_scripts: list[dict] | None` - Console script definitions

**Internal Fields:**
- `_raw_metadata: dict[str, Any]` - Raw metadata from YAML
- `_provenance: dict[str, str]` - Loading provenance information

#### Methods

##### `to_json() -> str`
Serialize the identity to JSON format.

```python
identity = get_identity()
json_output = identity.to_json()
print(json_output)
```

## CLI Commands

### Show Identity

```bash
# Show current identity in text format
pyfulmen appidentity show

# Show identity in JSON format  
pyfulmen appidentity show --format json

# Show identity from specific file
pyfulmen appidentity show --path /path/to/app.yaml
```

### Validate Identity

```bash
# Validate identity file
pyfulmen appidentity validate .fulmen/app.yaml
```

## Discovery Precedence

The module follows this precedence order for discovering identity files:

1. **Environment Variable**: `FULMEN_APP_IDENTITY_PATH`
2. **Ancestor Search**: Look for `.fulmen/app.yaml` in current directory and parent directories
3. **Error**: Raise `AppIdentityNotFoundError` if no file found

## Integration with Config Module

The app identity module integrates seamlessly with `pyfulmen.config`:

```python
from pyfulmen.appidentity import get_identity
from pyfulmen.config import load_layered_config

identity = get_identity()

# Config loader automatically uses identity for:
# - Environment variable prefix (identity.env_prefix)
# - Configuration file names (identity.config_name)
config, diagnostics, sources = load_layered_config(
    category="myapp",
    version="1.0.0",
    identity=identity  # Optional - will use get_identity() if not provided
)
```

## Testing

### Unit Tests

```python
import pytest
from pyfulmen.appidentity import AppIdentity, override_identity_for_testing

def test_with_mock_identity():
    mock_identity = AppIdentity(
        binary_name="test",
        vendor="test",
        env_prefix="TEST_",
        config_name="test", 
        description="Test",
        _raw_metadata={},
        _provenance={}
    )
    
    with override_identity_for_testing(mock_identity):
        from pyfulmen.appidentity import get_identity
        identity = get_identity()
        assert identity.binary_name == "test"
```

### Fixtures

Test fixtures are available in `tests/fixtures/app-identity/`:

- `valid/library.yaml` - Standard library identity
- `valid/cli.yaml` - Library + CLI identity  
- `valid/minimal.yaml` - Minimal required fields
- `invalid/` - Various invalid configurations for testing

## Troubleshooting

### Common Issues

#### "App identity not found"
- Ensure `.fulmen/app.yaml` exists in your repository
- Check file permissions
- Use `FULMEN_APP_IDENTITY_PATH` environment variable to specify location

#### "Validation failed"
- Verify YAML syntax is correct
- Ensure all required fields are present
- Check that `env_prefix` ends with underscore `_`
- Validate against the schema: `pyfulmen appidentity validate .fulmen/app.yaml`

#### Performance Issues
- Identity is cached after first load - subsequent calls are fast
- Use `clear_identity_cache()` if you need to force reload
- For testing, use `override_identity_for_testing()` instead of file I/O

### Debug Information

Enable debug output to see discovery process:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from pyfulmen.appidentity import get_identity
identity = get_identity()  # Will show discovery steps
```

### Schema Validation

The module validates against the canonical schema located at:
`schemas/crucible-py/config/repository/app-identity/v1.0.0/app-identity.schema.json`

You can validate any file manually:

```bash
pyfulmen appidentity validate path/to/app.yaml
```

## Error Handling

The module defines specific exception types:

- `AppIdentityError` - Base exception for all app identity errors
- `AppIdentityNotFoundError` - Raised when no identity file can be found
- `AppIdentityValidationError` - Raised when identity file fails schema validation

All exceptions include detailed error messages to help diagnose issues.

## Security Considerations

- Uses `yaml.safe_load()` to prevent arbitrary code execution
- Validates file paths to prevent directory traversal
- Limits file size to prevent denial of service
- Schema validation ensures only expected fields are processed

## Performance

- Identity is loaded once per process and cached
- Thread-safe caching using locks
- Minimal overhead for cached access
- Fast discovery with environment variable override option

## Compatibility

- Python 3.8+
- Compatible with all major operating systems
- Follows Crucible v0.2.4 app identity standard
- Cross-language parity with Go and TypeScript implementations

---

For more information, see:
- [PyFulmen Main Documentation](../../../README.md)
- [Crucible App Identity Standard](../../../../docs/crucible-py/standards/library/modules/app-identity.md)
- [Integration Guide](../../../../docs/guides/consuming-crucible-assets.md)
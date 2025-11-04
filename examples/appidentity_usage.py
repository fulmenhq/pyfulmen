"""
PyFulmen AppIdentity Usage Examples

This file demonstrates comprehensive usage patterns for the PyFulmen
AppIdentity module, including basic usage, testing patterns, and
advanced scenarios.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pyfulmen.appidentity import (
    clear_identity_cache,
    get_identity,
    load_from_path,
    override_identity_for_testing,
    reload_identity,
)
from pyfulmen.appidentity.errors import (
    AppIdentityError,
    AppIdentityNotFoundError,
    AppIdentityValidationError,
)
from pyfulmen.appidentity.models import AppIdentity


def example_basic_usage():
    """
    Example: Basic usage of get_identity()
    
    This is the most common usage pattern - simply call get_identity()
    to get your application's identity configuration.
    """
    print("=== Basic Usage Example ===")
    
    try:
        # Get application identity (automatically discovers and caches)
        identity = get_identity()
        
        print(f"Application: {identity.binary_name}")
        print(f"Vendor: {identity.vendor}")
        print(f"Environment Prefix: {identity.env_prefix}")
        print(f"Description: {identity.description}")
        
        # Access optional fields safely
        if identity.project_url:
            print(f"Project URL: {identity.project_url}")
        
        if identity.support_email:
            print(f"Support: {identity.support_email}")
            
        print("✅ Basic usage successful")
        
    except AppIdentityNotFoundError as e:
        print(f"❌ No identity configuration found: {e}")
        print("💡 Create a .fulmen/app.yaml file or set FULMEN_APP_IDENTITY_PATH")
        
    except AppIdentityValidationError as e:
        print(f"❌ Invalid identity configuration: {e}")
        print("💡 Check your app.yaml file against the Crucible schema")
        
    except AppIdentityError as e:
        print(f"❌ Error loading identity: {e}")


def example_manual_loading():
    """
    Example: Manual loading with explicit paths
    
    Sometimes you need to load from a specific path or have more
    control over the loading process.
    """
    print("\n=== Manual Loading Example ===")
    
    # Create a temporary identity file for demonstration
    test_config = {
        "app": {
            "binary_name": "example-app",
            "vendor": "examplevendor",
            "env_prefix": "EXAMPLE_",
            "config_name": "example-config",
            "description": "Example application for demonstration"
        },
"metadata": {
            "telemetry_namespace": "example_telemetry",
            "python": {
                "distribution_name": "example-app",
                "package_name": "example_app",
                "console_scripts": [
                    {"name": "example", "entry_point": "example_app.cli:main"}
                ]
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(test_config, f)
        temp_path = f.name
    
    try:
        # Load from explicit path
        identity = load_from_path(Path(temp_path))
        
        print(f"Loaded from: {temp_path}")
        print(f"Application: {identity.binary_name}")
        print(f"Vendor: {identity.vendor}")
        print(f"License: {identity.license}")
        print(f"Console Scripts: {identity.console_scripts}")
        
        # Check provenance information
        provenance = getattr(identity, '_provenance', {})
        if provenance:
            print(f"Loaded from: {provenance.get('source_path', 'Unknown')}")
        
        print("✅ Manual loading successful")
        
    except Exception as e:
        print(f"❌ Error loading from path: {e}")
        
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)


def example_cache_management():
    """
    Example: Cache management operations
    
    Demonstrate how to control the caching behavior for performance
    or testing scenarios.
    """
    print("\n=== Cache Management Example ===")
    
    try:
        # Clear any existing cache
        clear_identity_cache()
        print("🗑️  Cache cleared")
        
        # First call loads and caches
        identity1 = get_identity()
        print(f"📦 First call loaded: {identity1.binary_name}")
        
        # Second call uses cache (faster)
        identity2 = get_identity()
        print(f"⚡ Second call used cache: {identity2.binary_name}")
        
        # Force reload (bypasses cache)
        identity3 = reload_identity()
        print(f"🔄 Reload forced fresh load: {identity3.binary_name}")
        
        print("✅ Cache management successful")
        
    except AppIdentityNotFoundError:
        print("ℹ️  No identity configuration found - skipping cache example")
    except Exception as e:
        print(f"❌ Cache management error: {e}")


def example_testing_patterns():
    """
    Example: Testing patterns with mock identities
    
    Show how to use the testing utilities to create predictable
    test environments.
    """
    print("\n=== Testing Patterns Example ===")
    
    # Create a test identity
    test_identity = AppIdentity(
        binary_name="test-app",
        vendor="testvendor",
        env_prefix="TEST_",
        config_name="test-config",
        description="Test application for unit testing"
    )
    
    try:
        # Normal behavior (might fail if no config exists)
        print("🔍 Normal get_identity() call:")
        try:
            normal_identity = get_identity()
            print(f"   Found: {normal_identity.binary_name}")
        except AppIdentityNotFoundError:
            print("   No configuration found (expected in testing)")
        
        # Override for testing
        print("\n🧪 Using test override:")
        with override_identity_for_testing(test_identity):
            overridden_identity = get_identity()
            print(f"   Overridden: {overridden_identity.binary_name}")
            print(f"   Vendor: {overridden_identity.vendor}")
            print(f"   Description: {overridden_identity.description}")
        
        # Back to normal behavior
        print("\n🔍 Back to normal behavior:")
        try:
            normal_identity = get_identity()
            print(f"   Found: {normal_identity.binary_name}")
        except AppIdentityNotFoundError:
            print("   No configuration found (expected in testing)")
        
        print("✅ Testing patterns successful")
        
    except Exception as e:
        print(f"❌ Testing pattern error: {e}")


def example_error_handling():
    """
    Example: Comprehensive error handling
    
    Show how to handle all possible error conditions gracefully.
    """
    print("\n=== Error Handling Example ===")
    
    # Example 1: Handle missing configuration
    print("1. Testing missing configuration handling:")
    try:
        # This might fail if no config exists
        identity = get_identity()
        print(f"   ✅ Found configuration: {identity.binary_name}")
    except AppIdentityNotFoundError as e:
        print(f"   ℹ️  Expected error - no config found: {type(e).__name__}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
    
    # Example 2: Handle invalid configuration
    print("\n2. Testing invalid configuration handling:")
    
    # Create invalid config (missing required fields)
    invalid_config = {
        "app": {
            "binary_name": "invalid-app"
            # Missing required fields like vendor, env_prefix, etc.
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(invalid_config, f)
        temp_path = f.name
    
    try:
        identity = load_from_path(Path(temp_path))
        print(f"   ❌ Should have failed but got: {identity.binary_name}")
    except AppIdentityValidationError as e:
        print(f"   ✅ Expected validation error: {type(e).__name__}")
    except Exception as e:
        print(f"   ❌ Unexpected error type: {type(e).__name__}: {e}")
    finally:
        Path(temp_path).unlink(missing_ok=True)
    
    print("✅ Error handling examples complete")


def example_advanced_usage():
    """
    Example: Advanced usage patterns
    
    Demonstrate more complex scenarios like environment variable
    integration and configuration inspection.
    """
    print("\n=== Advanced Usage Example ===")
    
    try:
        identity = get_identity()
        
        # Environment variable integration
        print("🌍 Environment Integration:")
        env_vars = identity.env_vars
        for var_name, var_value in env_vars.items():
            print(f"   {var_name}: {var_value}")
        
        # JSON serialization
        print("\n📄 JSON Serialization:")
        identity_json = identity.to_json()
        parsed = json.loads(identity_json)
        print(f"   App name: {parsed['binary_name']}")
        print(f"   Vendor: {parsed['vendor']}")
        
        # Raw metadata access (for debugging)
        print("\n🔍 Raw Metadata Access:")
        raw_metadata = getattr(identity, '_raw_metadata', {})
        if raw_metadata:
            print(f"   Raw keys: {list(raw_metadata.keys())}")
        
        print("✅ Advanced usage successful")
        
    except AppIdentityNotFoundError:
        print("ℹ️  No identity configuration found - skipping advanced examples")
    except Exception as e:
        print(f"❌ Advanced usage error: {e}")


def main():
    """Run all examples."""
    print("PyFulmen AppIdentity Usage Examples")
    print("=" * 50)
    
    example_basic_usage()
    example_manual_loading()
    example_cache_management()
    example_testing_patterns()
    example_error_handling()
    example_advanced_usage()
    
    print("\n" + "=" * 50)
    print("📚 For more information, see:")
    print("   - PyFulmen documentation")
    print("   - Crucible app identity standard")
    print("   - Module docstring: pyfulmen.appidentity")


if __name__ == "__main__":
    main()
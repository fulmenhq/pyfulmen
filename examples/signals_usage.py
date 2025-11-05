#!/usr/bin/env python3
"""
PyFulmen Signals Module Usage Examples

This example demonstrates the enterprise signal handling capabilities
of the PyFulmen signals module with progressive interfaces.
"""

import signal

from pyfulmen.signals import get_http_helper, get_module_info, get_signal_metadata, list_all_signals, supports_signal


def example_basic_signal_support():
    """Example 1: Basic signal support detection."""
    print("=== Example 1: Basic Signal Support Detection ===")
  
    # Check support for common signals
    test_signals = [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGUSR1]
  
    for sig in test_signals:
        supported = supports_signal(sig)
        metadata = get_signal_metadata(sig.name)
        description = metadata.get("description", "No description") if metadata else "No description"
  
        print(f"Signal {sig.name:8}: {'✅' if supported else '❌'} - {description}")
  
    print()


def example_signal_metadata():
    """Example 2: Detailed signal metadata."""
    print("=== Example 2: Signal Metadata ===")
  
    # Get detailed metadata for SIGUSR1
    sigusr1_info = get_signal_metadata(signal.SIGUSR1.name)
  
    print(f"Signal: {signal.SIGUSR1.name}")
    print(f"Description: {sigusr1_info.get('description')}")
    print(f"Platforms: {list(sigusr1_info.get('platforms', {}).keys())}")
  
    # Show platform-specific info
    platforms = sigusr1_info.get("platforms", {})
    for platform, info in platforms.items():
        supported = info.get("supported", False)
        fallback = info.get("windows_fallback", False)
        print(f"  {platform.title():8}: {'✅' if supported else '❌'} (Fallback: {'✅' if fallback else '❌'})")
  
    print()


def example_http_fallback():
    """Example 3: Windows HTTP fallback functionality."""
    print("=== Example 3: HTTP Fallback for Windows ===")
  
    helper = get_http_helper()
  
    # Show Windows fallback signals
    fallback_signals = helper.get_windows_fallback_signals()
    print(f"Windows fallback signals: {len(fallback_signals)}")
    print(f"Signals: {', '.join(fallback_signals)}")
  
    # Build a sample request
    if fallback_signals:
        sample_signal = fallback_signals[0]
        request = helper.build_signal_request(sample_signal)
  
        print(f"\nSample HTTP request for {sample_signal}:")
        print(f"URL: {request['url']}")
        print(f"Method: {request['method']}")
        print(f"Headers: {request['headers']}")
        print(f"Body: {request['body']}")
  
        # Generate curl command
        curl_cmd = helper.format_curl_command(request)
        print(f"\nCurl command:\n{curl_cmd}")
  
    print()


def example_module_info():
    """Example 4: Module information and capabilities."""
    print("=== Example 4: Module Information ===")
  
    info = get_module_info()
  
    print(f"Module: {info['name']}")
    print(f"Version: {info['version']}")
    print(f"Platform: {info['platform']}")
    print(f"Description: {info['description']}")
  
    # Show all available signals
    all_signals = list_all_signals()
    print(f"\nAll available signals ({len(all_signals)}):")
    for sig_name in all_signals:
        print(f"  - {sig_name}")
  
    print()


def example_progressive_interface():
    """Example 5: Progressive interface usage."""
    print("=== Example 5: Progressive Interface ===")
  
    # Level 1: Basic usage (zero complexity)
    print("Level 1 - Basic Usage:")
    if supports_signal(signal.SIGUSR1):
        print("✅ SIGUSR1 is supported on this platform")
    else:
        print("❌ SIGUSR1 is not supported on this platform")
  
    # Level 2: Metadata access
    print("\nLevel 2 - Metadata Access:")
    metadata = get_signal_metadata(signal.SIGUSR1.name)
    print(f"Description: {metadata.get('description', 'N/A')}")
  
    # Level 3: Enterprise features (HTTP fallback)
    print("\nLevel 3 - Enterprise Features:")
    helper = get_http_helper()
    if helper.get_windows_fallback_signals():
        print("✅ HTTP fallback available for Windows")
        print("Fallback signals:", helper.get_windows_fallback_signals())
    else:
        print("❌ No HTTP fallback configured")
  
    print()


def example_cross_platform_consistency():
    """Example 6: Cross-platform signal handling."""
    print("=== Example 6: Cross-Platform Consistency ===")
  
    # Test consistency across different signal types
    test_cases = [
        ("SIGTERM", "Standard termination"),
        ("SIGINT", "User interrupt"),
        ("SIGHUP", "Configuration reload"),
        ("SIGUSR1", "User-defined 1"),
        ("SIGUSR2", "User-defined 2")
    ]
  
    for sig_name, description in test_cases:
        if hasattr(signal, sig_name):
            sig_obj = getattr(signal, sig_name)
            supported = supports_signal(sig_obj)
            metadata = get_signal_metadata(sig_name)
  
            platforms = metadata.get("platforms", {})
            platform_support = []
            for platform, info in platforms.items():
                if info.get("supported", False):
                    platform_support.append(platform)
  
            platforms_str = ', '.join(platform_support) or 'None'
            print(f"{sig_name:8}: {'✅' if supported else '❌'} | Platforms: {platforms_str} | {description}")
  
    print()


def main():
    """Run all examples."""
    print("PyFulmen Signals Module - Usage Examples")
    print("=" * 50)
    print()
  
    try:
        example_basic_signal_support()
        example_signal_metadata()
        example_http_fallback()
        example_module_info()
        example_progressive_interface()
        example_cross_platform_consistency()
  
        print("All examples completed successfully! ✅")
  
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        return 1
  
    return 0


if __name__ == "__main__":
    exit(main())

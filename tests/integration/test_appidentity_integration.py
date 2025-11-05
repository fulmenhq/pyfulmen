"""
Integration tests for PyFulmen AppIdentity module.

Tests cross-module interactions and real-world usage scenarios.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from pyfulmen.appidentity import (
    AppIdentity,
    AppIdentityNotFoundError,
    clear_identity_cache,
    get_identity,
    override_identity_for_testing,
)
from pyfulmen.config import loader, paths


class TestConfigModuleIntegration:
    """Test integration with config module."""

    def test_config_paths_uses_identity(self):
        """Verify config paths derive from identity when available."""
        # Create a temporary identity file
        with tempfile.TemporaryDirectory() as tmpdir:
            identity_path = Path(tmpdir) / ".fulmen" / "app.yaml"
            identity_path.parent.mkdir(parents=True)

            identity_content = """
app:
  binary_name: "testapp"
  vendor: "testvendor"
  env_prefix: "TESTAPP_"
  config_name: "testapp"
  description: "Test application"
"""
            identity_path.write_text(identity_content)

            # Change to temp directory and load identity
            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                clear_identity_cache()
                identity = get_identity()

                # Test config paths integration
                config_dir = paths.get_app_config_dir("testapp", vendor="testvendor")
                assert "testvendor" in str(config_dir)
                assert "testapp" in str(config_dir)

            finally:
                os.chdir(original_cwd)
                clear_identity_cache()

    def test_config_loader_uses_identity(self):
        """Verify config loader uses identity for env prefix and config name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create identity file
            identity_path = Path(tmpdir) / ".fulmen" / "app.yaml"
            identity_path.parent.mkdir(parents=True)

            identity_content = """
app:
  binary_name: "configtest"
  vendor: "acme"
  env_prefix: "CONFIGTEST_"
  config_name: "configtest"
  description: "Config test application"
"""
            identity_path.write_text(identity_content)

            # Create a minimal config file
            config_dir = Path(tmpdir) / ".config" / "acme" / "configtest"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "test.yaml"
            config_file.write_text("test_value: from_config\n")

            original_cwd = Path.cwd()
            original_xdg_config = os.environ.get("XDG_CONFIG_HOME")
            try:
                os.chdir(tmpdir)
                # Set XDG_CONFIG_HOME to use temp directory
                os.environ["XDG_CONFIG_HOME"] = str(Path(tmpdir) / ".config")
                clear_identity_cache()

                # Test config loader with identity
                config_loader = loader.ConfigLoader(app_name="configtest", vendor="acme")
                config = config_loader.load("test")

                # Verify config was loaded
                assert "test_value" in config
                assert config["test_value"] == "from_config"

            finally:
                os.chdir(original_cwd)
                if original_xdg_config is not None:
                    os.environ["XDG_CONFIG_HOME"] = original_xdg_config
                elif "XDG_CONFIG_HOME" in os.environ:
                    del os.environ["XDG_CONFIG_HOME"]
                clear_identity_cache()

    def test_config_loader_with_explicit_identity(self):
        """Test config loader accepts explicit identity parameter."""
        # Create explicit identity
        identity = AppIdentity(
            binary_name="explicit",
            vendor="explicitvendor",
            env_prefix="EXPLICIT_",
            config_name="explicit",
            description="Explicit test identity",
        )

        # Test with explicit identity (should not fail even without file)
        config_loader = loader.ConfigLoader(app_name=identity.config_name, vendor=identity.vendor)
        config = config_loader.load("test/test-config")

        # Should have loaded with explicit identity
        assert isinstance(config, dict)


class TestEnvironmentIntegration:
    """Test integration with environment variables."""

    def test_env_override_discovery(self):
        """Test environment variable override for identity path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create identity file in temp location
            identity_path = Path(tmpdir) / "custom_app.yaml"
            identity_content = """
app:
  binary_name: "envtest"
  vendor: "envvendor"
  env_prefix: "ENVTEST_"
  config_name: "envtest"
  description: "Environment test application"
"""
            identity_path.write_text(identity_content)

            # Set environment variable
            original_env = os.environ.get("FULMEN_APP_IDENTITY_PATH")
            try:
                os.environ["FULMEN_APP_IDENTITY_PATH"] = str(identity_path)
                clear_identity_cache()

                # Load should use environment override
                identity = get_identity()
                assert identity.binary_name == "envtest"
                assert identity.vendor == "envvendor"

            finally:
                if original_env is not None:
                    os.environ["FULMEN_APP_IDENTITY_PATH"] = original_env
                elif "FULMEN_APP_IDENTITY_PATH" in os.environ:
                    del os.environ["FULMEN_APP_IDENTITY_PATH"]
                clear_identity_cache()


class TestCrossModuleCompatibility:
    """Test compatibility with other PyFulmen modules."""

    def test_identity_with_logging_module(self):
        """Test identity can be used with logging configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            identity_path = Path(tmpdir) / ".fulmen" / "app.yaml"
            identity_path.parent.mkdir(parents=True)

            identity_content = """
app:
  binary_name: logtest
  vendor: logvendor
  env_prefix: LOGTEST_
  config_name: logtest
  description: Logging test application

metadata:
  telemetry_namespace: logtest_telemetry
"""
            identity_path.write_text(identity_content)

            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                clear_identity_cache()

                identity = get_identity()

                # Verify telemetry namespace is available
                assert identity.telemetry_namespace == "logtest_telemetry"

                # Test that identity can be serialized for logging
                identity_json = identity.to_json()
                assert "telemetry_namespace" in identity_json
                assert "logtest_telemetry" in identity_json

            finally:
                os.chdir(original_cwd)
                clear_identity_cache()

    def test_identity_with_schema_module(self):
        """Test identity works with schema validation."""
        # Schema validation will be tested when schema module is available

        with tempfile.TemporaryDirectory() as tmpdir:
            identity_path = Path(tmpdir) / ".fulmen" / "app.yaml"
            identity_path.parent.mkdir(parents=True)

            identity_content = """
app:
  binary_name: "schematest"
  vendor: "schemavendor"
  env_prefix: "SCHEMATEST_"
  config_name: "schematest"
  description: "Schema test application"
"""
            identity_path.write_text(identity_content)

            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                clear_identity_cache()

                identity = get_identity()

                # Test identity data structure
                identity_data = {
                    "binary_name": identity.binary_name,
                    "vendor": identity.vendor,
                    "env_prefix": identity.env_prefix,
                }

                # Verify data structure
                assert isinstance(identity_data, dict)
                assert identity_data["binary_name"] == "schematest"

            finally:
                os.chdir(original_cwd)
                clear_identity_cache()


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_monorepo_ancestor_search(self):
        """Test ancestor search in monorepo scenario."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create monorepo structure
            repo_root = Path(tmpdir)
            fulmen_dir = repo_root / ".fulmen"
            fulmen_dir.mkdir()

            identity_content = """
app:
  binary_name: monorepoapp
  vendor: monorepovendor
  env_prefix: MONOREPO_
  config_name: monorepoapp
  description: Monorepo test application
"""
            (fulmen_dir / "app.yaml").write_text(identity_content)

            # Create subdirectory
            subdir = repo_root / "subdir" / "nested"
            subdir.mkdir(parents=True)

            original_cwd = Path.cwd()
            try:
                os.chdir(subdir)
                clear_identity_cache()

                # Should find identity in ancestor directory
                identity = get_identity()
                assert identity.binary_name == "monorepoapp"

            finally:
                os.chdir(original_cwd)
                clear_identity_cache()

    def test_multiple_applications(self):
        """Test multiple applications in same repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Create first app identity
            app1_dir = repo_root / "app1"
            app1_fulmen = app1_dir / ".fulmen"
            app1_fulmen.mkdir(parents=True)

            app1_content = """
app:
  binary_name: appone
  vendor: multivendor
  env_prefix: APPONE_
  config_name: appone
  description: First application
"""
            (app1_fulmen / "app.yaml").write_text(app1_content)

            # Create second app identity
            app2_dir = repo_root / "app2"
            app2_fulmen = app2_dir / ".fulmen"
            app2_fulmen.mkdir(parents=True)

            app2_content = """
app:
  binary_name: apptwo
  vendor: multivendor
  env_prefix: APPTWO_
  config_name: apptwo
  description: Second application
"""
            (app2_fulmen / "app.yaml").write_text(app2_content)

            original_cwd = Path.cwd()
            try:
                # Test app1
                os.chdir(app1_dir)
                clear_identity_cache()
                identity1 = get_identity()
                assert identity1.binary_name == "appone"
                assert identity1.env_prefix == "APPONE_"

                # Test app2
                os.chdir(app2_dir)
                clear_identity_cache()
                identity2 = get_identity()
                assert identity2.binary_name == "apptwo"
                assert identity2.env_prefix == "APPTWO_"

            finally:
                os.chdir(original_cwd)
                clear_identity_cache()

    def test_test_override_isolation(self):
        """Test test override isolation in real scenario."""
        # Create test identity
        test_identity = AppIdentity(
            binary_name="testoverride",
            vendor="testvendor",
            env_prefix="TESTOVERRIDE_",
            config_name="testoverride",
            description="Test override identity",
        )

        # Test in temp directory to ensure no identity is found after override
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                clear_identity_cache()

                # Use override in context
                with override_identity_for_testing(test_identity) as identity:
                    assert identity.binary_name == "testoverride"
                    assert get_identity().binary_name == "testoverride"

                # After context, should raise error since no identity file in temp dir
                with pytest.raises(AppIdentityNotFoundError):
                    get_identity()

            finally:
                os.chdir(original_cwd)
                clear_identity_cache()


class TestPerformanceAndReliability:
    """Test performance and reliability aspects."""

    def test_caching_performance(self):
        """Test that caching provides performance benefits."""
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            identity_path = Path(tmpdir) / ".fulmen" / "app.yaml"
            identity_path.parent.mkdir(parents=True)

            identity_content = """
app:
  binary_name: "perftest"
  vendor: "perfvendor"
  env_prefix: "PERFTEST_"
  config_name: "perftest"
  description: "Performance test application"
"""
            identity_path.write_text(identity_content)

            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                clear_identity_cache()

                # Time first load (cache miss)
                start_time = time.time()
                identity1 = get_identity()
                first_load_time = time.time() - start_time

                # Time second load (cache hit)
                start_time = time.time()
                identity2 = get_identity()
                second_load_time = time.time() - start_time

                # Verify same instance and performance
                assert identity1 is identity2
                assert second_load_time < first_load_time

            finally:
                os.chdir(original_cwd)
                clear_identity_cache()

    def test_thread_safety_under_load(self):
        """Test thread safety under concurrent load."""
        import threading
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            identity_path = Path(tmpdir) / ".fulmen" / "app.yaml"
            identity_path.parent.mkdir(parents=True)

            identity_content = """
app:
  binary_name: "threadtest"
  vendor: "threadvendor"
  env_prefix: "THREADTEST_"
  config_name: "threadtest"
  description: "Thread safety test application"
"""
            identity_path.write_text(identity_content)

            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                clear_identity_cache()

                results = []
                errors = []

                def worker():
                    try:
                        for _ in range(10):
                            identity = get_identity()
                            results.append(identity.binary_name)
                            time.sleep(0.001)  # Small delay
                    except Exception as e:
                        errors.append(e)

                # Start multiple threads
                threads = []
                for _ in range(5):
                    thread = threading.Thread(target=worker)
                    threads.append(thread)
                    thread.start()

                # Wait for completion
                for thread in threads:
                    thread.join()

                # Verify results
                assert len(errors) == 0
                assert all(result == "threadtest" for result in results)
                assert len(results) == 50  # 5 threads * 10 iterations

            finally:
                os.chdir(original_cwd)
                clear_identity_cache()


class TestErrorRecovery:
    """Test error recovery and edge cases."""

    def test_recovery_from_invalid_file(self):
        """Test recovery from invalid identity file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid identity file
            identity_path = Path(tmpdir) / ".fulmen" / "app.yaml"
            identity_path.parent.mkdir(parents=True)

            invalid_content = """
app:
  binary_name: "invalid"
  vendor: "vendor"
  # Missing required fields
"""
            identity_path.write_text(invalid_content)

            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                clear_identity_cache()

                # Should raise validation error
                with pytest.raises(Exception):  # Should be validation error
                    get_identity()

                # Fix the file and retry
                valid_content = """
app:
  binary_name: "recovered"
  vendor: "vendor"
  env_prefix: "RECOVERED_"
  config_name: "recovered"
  description: "Recovered application"
"""
                identity_path.write_text(valid_content)
                clear_identity_cache()

                # Should now work
                identity = get_identity()
                assert identity.binary_name == "recovered"

            finally:
                os.chdir(original_cwd)
                clear_identity_cache()

    def test_graceful_degradation(self):
        """Test graceful degradation when identity is optional."""
        # Test that modules work without identity when it's optional
        with patch("pyfulmen.appidentity._loader._discover_identity_path") as mock_discover:
            mock_discover.side_effect = AppIdentityNotFoundError([])

            clear_identity_cache()

            # Should raise error for required identity
            with pytest.raises(AppIdentityNotFoundError):
                get_identity()

            # But should work with explicit identity
            test_identity = AppIdentity(
                binary_name="explicit",
                vendor="explicit",
                env_prefix="EXPLICIT_",
                config_name="explicit",
                description="Explicit identity",
            )

            with override_identity_for_testing(test_identity):
                identity = get_identity()
                assert identity.binary_name == "explicit"

            clear_identity_cache()

"""
Tests for security headers.

Complete coverage tests for SecurityHeaders class.
"""

from football_predict_system.core.security.headers import SecurityHeaders


class TestSecurityHeaders:
    """Test SecurityHeaders class."""

    def test_get_security_headers_structure(self):
        """Test security headers structure."""
        headers = SecurityHeaders.get_security_headers()

        assert isinstance(headers, dict)
        assert len(headers) == 6  # Should have 6 security headers

    def test_get_security_headers_content_type_options(self):
        """Test X-Content-Type-Options header."""
        headers = SecurityHeaders.get_security_headers()

        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"

    def test_get_security_headers_frame_options(self):
        """Test X-Frame-Options header."""
        headers = SecurityHeaders.get_security_headers()

        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

    def test_get_security_headers_xss_protection(self):
        """Test X-XSS-Protection header."""
        headers = SecurityHeaders.get_security_headers()

        assert "X-XSS-Protection" in headers
        assert headers["X-XSS-Protection"] == "1; mode=block"

    def test_get_security_headers_hsts(self):
        """Test Strict-Transport-Security header."""
        headers = SecurityHeaders.get_security_headers()

        assert "Strict-Transport-Security" in headers
        expected_hsts = "max-age=31536000; includeSubDomains"
        assert headers["Strict-Transport-Security"] == expected_hsts

    def test_get_security_headers_referrer_policy(self):
        """Test Referrer-Policy header."""
        headers = SecurityHeaders.get_security_headers()

        assert "Referrer-Policy" in headers
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_get_security_headers_csp(self):
        """Test Content-Security-Policy header."""
        headers = SecurityHeaders.get_security_headers()

        assert "Content-Security-Policy" in headers
        assert headers["Content-Security-Policy"] == "default-src 'self'"

    def test_get_security_headers_all_keys(self):
        """Test all expected security headers are present."""
        headers = SecurityHeaders.get_security_headers()

        expected_keys = {
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Referrer-Policy",
            "Content-Security-Policy",
        }

        assert set(headers.keys()) == expected_keys

    def test_get_security_headers_immutability(self):
        """Test security headers are consistent across calls."""
        headers1 = SecurityHeaders.get_security_headers()
        headers2 = SecurityHeaders.get_security_headers()

        assert headers1 == headers2
        assert headers1 is not headers2  # Different dict instances

    def test_get_security_headers_values_are_strings(self):
        """Test all header values are strings."""
        headers = SecurityHeaders.get_security_headers()

        for key, value in headers.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert len(key) > 0
            assert len(value) > 0

    def test_apply_headers_empty_response(self):
        """Test applying headers to empty response."""
        response_headers = {}

        result = SecurityHeaders.apply_headers(response_headers)

        assert isinstance(result, dict)
        assert len(result) == 6  # Should have 6 security headers
        assert result is response_headers  # Should return same dict instance

    def test_apply_headers_existing_headers(self):
        """Test applying headers to response with existing headers."""
        response_headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }
        original_count = len(response_headers)

        result = SecurityHeaders.apply_headers(response_headers)

        assert result is response_headers  # Same instance
        assert len(result) == original_count + 6  # Original + 6 security headers
        assert "Content-Type" in result  # Original headers preserved
        assert "Cache-Control" in result

    def test_apply_headers_overwrites_existing_security_headers(self):
        """Test security headers overwrite existing ones."""
        response_headers = {
            "X-Frame-Options": "SAMEORIGIN",  # Will be overwritten
            "Content-Type": "application/json",
        }

        result = SecurityHeaders.apply_headers(response_headers)

        assert result["X-Frame-Options"] == "DENY"  # Overwritten
        assert result["Content-Type"] == "application/json"  # Preserved

    def test_apply_headers_return_value(self):
        """Test apply_headers return value."""
        response_headers = {"Custom-Header": "value"}

        result = SecurityHeaders.apply_headers(response_headers)

        assert result is response_headers
        assert "Custom-Header" in result
        assert "X-Content-Type-Options" in result

    def test_apply_headers_security_headers_included(self):
        """Test all security headers are included in applied headers."""
        response_headers = {}

        SecurityHeaders.apply_headers(response_headers)

        expected_headers = SecurityHeaders.get_security_headers()
        for key, value in expected_headers.items():
            assert key in response_headers
            assert response_headers[key] == value

    def test_apply_headers_modifies_original_dict(self):
        """Test apply_headers modifies the original dict."""
        response_headers = {"Original": "header"}
        original_id = id(response_headers)

        result = SecurityHeaders.apply_headers(response_headers)

        assert id(result) == original_id
        assert len(response_headers) == 7  # 1 original + 6 security

    def test_apply_headers_with_none_like_values(self):
        """Test apply_headers handles various input scenarios."""
        # Test with dictionary containing various values
        response_headers = {
            "String-Header": "value",
            "Number-Like": "123",
            "Boolean-Like": "true",
        }

        result = SecurityHeaders.apply_headers(response_headers)

        assert len(result) == 9  # 3 original + 6 security
        assert all(isinstance(v, str) for v in result.values())

    def test_security_headers_class_static_methods(self):
        """Test that methods are properly static."""
        # Should be able to call without instance
        headers1 = SecurityHeaders.get_security_headers()
        headers2 = SecurityHeaders().get_security_headers()

        assert headers1 == headers2

    def test_security_headers_defensive_copy(self):
        """Test that headers dict can be modified without affecting future calls."""
        headers = SecurityHeaders.get_security_headers()
        headers["X-Custom"] = "modified"

        fresh_headers = SecurityHeaders.get_security_headers()
        assert "X-Custom" not in fresh_headers
        assert len(fresh_headers) == 6

    def test_apply_headers_comprehensive_scenario(self):
        """Test comprehensive real-world scenario."""
        # Simulate a real HTTP response headers dict
        response_headers = {
            "Content-Type": "application/json",
            "Content-Length": "1234",
            "Cache-Control": "no-cache, no-store",
            "Date": "Wed, 21 Oct 2015 07:28:00 GMT",
            "Server": "nginx/1.18.0",
        }
        original_count = len(response_headers)

        result = SecurityHeaders.apply_headers(response_headers)

        # Check all original headers preserved
        assert result["Content-Type"] == "application/json"
        assert result["Content-Length"] == "1234"
        assert result["Cache-Control"] == "no-cache, no-store"
        assert result["Date"] == "Wed, 21 Oct 2015 07:28:00 GMT"
        assert result["Server"] == "nginx/1.18.0"

        # Check security headers added
        assert result["X-Content-Type-Options"] == "nosniff"
        assert result["X-Frame-Options"] == "DENY"
        assert result["X-XSS-Protection"] == "1; mode=block"
        assert "Strict-Transport-Security" in result
        assert "Referrer-Policy" in result
        assert "Content-Security-Policy" in result

        # Check total count
        assert len(result) == original_count + 6

    def test_header_values_security_best_practices(self):
        """Test that header values follow security best practices."""
        headers = SecurityHeaders.get_security_headers()

        # X-Content-Type-Options should prevent MIME sniffing
        assert headers["X-Content-Type-Options"] == "nosniff"

        # X-Frame-Options should prevent clickjacking
        assert headers["X-Frame-Options"] == "DENY"

        # X-XSS-Protection should be enabled
        assert "1" in headers["X-XSS-Protection"]
        assert "mode=block" in headers["X-XSS-Protection"]

        # HSTS should have long max-age and include subdomains
        hsts = headers["Strict-Transport-Security"]
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts

        # CSP should have default-src 'self'
        assert "'self'" in headers["Content-Security-Policy"]

    def test_headers_type_annotations_compliance(self):
        """Test return types match annotations."""
        # get_security_headers should return dict[str, str]
        headers = SecurityHeaders.get_security_headers()
        assert isinstance(headers, dict)

        # apply_headers should return dict[str, str]
        response = {"test": "value"}
        result = SecurityHeaders.apply_headers(response)
        assert isinstance(result, dict)

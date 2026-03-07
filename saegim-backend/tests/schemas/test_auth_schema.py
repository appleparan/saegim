"""Tests for authentication schemas."""

import pytest
from pydantic import ValidationError

from saegim.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class TestRegisterRequest:
    """Test cases for RegisterRequest schema."""

    def test_valid_register(self):
        req = RegisterRequest(name='Test', email='test@example.com', password='password123')
        assert req.name == 'Test'
        assert str(req.email) == 'test@example.com'

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(name='Test', email='test@example.com', password='short')

    def test_password_too_long(self):
        with pytest.raises(ValidationError):
            RegisterRequest(name='Test', email='test@example.com', password='x' * 129)

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(name='Test', email='not-email', password='password123')

    def test_empty_name(self):
        with pytest.raises(ValidationError):
            RegisterRequest(name='', email='test@example.com', password='password123')


class TestLoginRequest:
    """Test cases for LoginRequest schema."""

    def test_valid_login(self):
        req = LoginRequest(email='test@example.com', password='password123')
        assert str(req.email) == 'test@example.com'

    def test_empty_password(self):
        with pytest.raises(ValidationError):
            LoginRequest(email='test@example.com', password='')


class TestTokenResponse:
    """Test cases for TokenResponse schema."""

    def test_token_response(self):
        token = TokenResponse(access_token='abc.def.ghi')
        assert token.access_token == 'abc.def.ghi'
        assert token.token_type == 'bearer'

    def test_custom_token_type(self):
        token = TokenResponse(access_token='abc', token_type='mac')
        assert token.token_type == 'mac'

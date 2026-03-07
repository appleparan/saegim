"""Tests for auth dependency functions."""

import datetime
import uuid

import jwt
import pytest

from saegim.api.deps import create_access_token, hash_password, verify_password
from saegim.api.settings import Settings


@pytest.fixture
def test_settings():
    return Settings(
        secret_key='test-secret-key-32chars-for-testing',
        jwt_algorithm='HS256',
        access_token_expire_minutes=60,
    )


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password('mypassword')
        assert hashed != 'mypassword'
        assert verify_password('mypassword', hashed)

    def test_wrong_password(self):
        hashed = hash_password('correctpassword')
        assert not verify_password('wrongpassword', hashed)

    def test_different_hashes_same_password(self):
        hash1 = hash_password('samepassword')
        hash2 = hash_password('samepassword')
        assert hash1 != hash2  # bcrypt uses random salt
        assert verify_password('samepassword', hash1)
        assert verify_password('samepassword', hash2)


class TestCreateAccessToken:
    def test_creates_valid_token(self, test_settings):
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id, 'annotator', test_settings)

        payload = jwt.decode(
            token,
            test_settings.secret_key,
            algorithms=[test_settings.jwt_algorithm],
        )
        assert payload['sub'] == user_id
        assert payload['role'] == 'annotator'
        assert 'exp' in payload

    def test_admin_role_in_token(self, test_settings):
        token = create_access_token(str(uuid.uuid4()), 'admin', test_settings)
        payload = jwt.decode(
            token,
            test_settings.secret_key,
            algorithms=[test_settings.jwt_algorithm],
        )
        assert payload['role'] == 'admin'

    def test_token_expiry(self, test_settings):
        token = create_access_token(str(uuid.uuid4()), 'annotator', test_settings)
        payload = jwt.decode(
            token,
            test_settings.secret_key,
            algorithms=[test_settings.jwt_algorithm],
        )
        exp = datetime.datetime.fromtimestamp(payload['exp'], tz=datetime.UTC)
        now = datetime.datetime.now(tz=datetime.UTC)
        delta = exp - now
        # Should expire in ~60 minutes (test_settings)
        assert 59 <= delta.total_seconds() / 60 <= 61

    def test_expired_token_raises(self, test_settings):
        expired_settings = Settings(
            secret_key=test_settings.secret_key,
            jwt_algorithm='HS256',
            access_token_expire_minutes=-1,
        )
        token = create_access_token(str(uuid.uuid4()), 'annotator', expired_settings)

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                test_settings.secret_key,
                algorithms=[test_settings.jwt_algorithm],
            )

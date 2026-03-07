"""Tests for application bootstrap behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from saegim.api.settings import Settings
from saegim.app import create_app


class TestBootstrapDefaultAdmin:
    """Test cases for default admin bootstrap on startup."""

    def test_creates_default_admin_when_no_users(self, test_settings: Settings):
        fake_pool = MagicMock()
        with (
            patch('saegim.app.create_pool', new_callable=AsyncMock, return_value=fake_pool),
            patch('saegim.app.close_pool', new_callable=AsyncMock),
            patch(
                'saegim.repositories.user_repo.count_all', new_callable=AsyncMock, return_value=0
            ),
            patch(
                'saegim.repositories.user_repo.create_with_password',
                new_callable=AsyncMock,
            ) as mock_create_user,
        ):
            app = create_app(settings=test_settings)
            with TestClient(app):
                pass

        mock_create_user.assert_awaited_once()
        kwargs = mock_create_user.call_args.kwargs
        assert kwargs['name'] == 'admin'
        assert kwargs['login_id'] == 'admin'
        assert kwargs['email'] == 'admin'
        assert kwargs['role'] == 'admin'
        assert kwargs['must_change_password'] is True
        assert kwargs['password_hash'] != 'admin'

    def test_skips_bootstrap_when_users_exist(self, test_settings: Settings):
        fake_pool = MagicMock()
        with (
            patch('saegim.app.create_pool', new_callable=AsyncMock, return_value=fake_pool),
            patch('saegim.app.close_pool', new_callable=AsyncMock),
            patch(
                'saegim.repositories.user_repo.count_all', new_callable=AsyncMock, return_value=3
            ),
            patch(
                'saegim.repositories.user_repo.create_with_password',
                new_callable=AsyncMock,
            ) as mock_create_user,
        ):
            app = create_app(settings=test_settings)
            with TestClient(app):
                pass

        mock_create_user.assert_not_called()

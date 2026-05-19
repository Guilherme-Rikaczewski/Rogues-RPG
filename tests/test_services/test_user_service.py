from unittest.mock import MagicMock, patch
from app.services.user_service import create_user, update_user
from app.schemas.user_schema import UserCreate, UserUpdate


@patch("app.services.user_service.get_password_hash")
def test_create_user(mock_hash):
    mock_hash.return_value = "hashed_password"

    fake_db = MagicMock()

    user_data = UserCreate(
        username="guilherme",
        email="gui@email.com",
        password="aB123456"
    )

    result = create_user(fake_db, user_data)

    assert result.username == "guilherme"
    assert result.email == "gui@email.com"
    assert result.password == "hashed_password"

    fake_db.add.assert_called_once()
    fake_db.commit.assert_called_once()
    fake_db.refresh.assert_called_once()


@patch("app.services.user_service.get_password_hash")
def test_update_user(mock_hash):
    mock_hash.return_value = "nova_senha_hash"

    fake_user = MagicMock()
    fake_user.id = 1
    fake_user.username = "gui"

    fake_query = MagicMock()
    fake_query.filter.return_value.first.return_value = fake_user

    fake_db = MagicMock()
    fake_db.query.return_value = fake_query

    user_data = UserUpdate(
        username="guilherme",
        password="bA123456"
    )

    result = update_user(fake_db, 1, user_data)

    assert result.username == "guilherme"
    assert result.password == "nova_senha_hash"

    fake_db.commit.assert_called_once()
    fake_db.refresh.assert_called_once_with(fake_user)

    mock_hash.assert_called_once_with("bA123456")

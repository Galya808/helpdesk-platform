from app.security.password import hash_password, verify_password


def test_password_is_hashed():
    # Arrange
    password = "Password"

    # Act
    hashed_password = hash_password(password)

    # Assert
    assert password != hashed_password


def test_correct_password_is_verified():
    # Arrange
    password = "Password"

    # Act
    hashed_password = hash_password(password)

    # Assert
    assert verify_password(password, hashed_password) is True


def test_incorrect_password_is_not_verified():
    # Arrange
    password = "Password"
    wrong_password = "password"

    # Act
    hashed_password = hash_password(password)

    # Assert
    assert verify_password(wrong_password, hashed_password) is False


def test_same_passwords_are_hashed_differently():
    # Arrange
    password1 = "Password"
    password2 = "Password"

    # Act
    hashed_password1 = hash_password(password1)
    hashed_password2 = hash_password(password2)

    # Assert
    assert hashed_password1 != hashed_password2

from security import hash_password, verify_password

def test_hash_differs_from_password():
    password = "train password"
    hashed_password = hash_password(password)

    assert isinstance(hashed_password, str)
    assert hashed_password != password

def test_correct_password_is_accepted():
    password = "train password"
    hashed_password = hash_password(password)
    result = verify_password(password, hashed_password)
    assert result is True

def test_wrong_password_is_rejected():
    password = "train password"
    hashed_password = hash_password(password)
    result = verify_password("diff", hashed_password)
    assert result is False

def test_same_passwords_get_diff_hash():
    password = "train password"
    hashed_password1 = hash_password(password)
    hashed_password2 = hash_password(password)

    assert hashed_password1 != hashed_password2
    assert verify_password(password, hashed_password1) is True
    assert verify_password(password, hashed_password2) is True

from users.managers import CmmsUserManager


def test_random_password():
    password = CmmsUserManager().make_random_password()
    assert len(password) == 8
    assert isinstance(password, str)


def test_random_password_uniqueness():
    manager = CmmsUserManager()
    password1 = manager.make_random_password()
    password2 = manager.make_random_password()
    assert password1 != password2
    assert len(password1) == 8

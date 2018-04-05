from http.cookiejar import Cookie

from mock import mock
from requests.cookies import RequestsCookieJar
from rets import RetsHttpClient


def test_cookie_dict():
    c = RetsHttpClient('login_url', 'username', 'password')
    c._session = mock.MagicMock()
    jar = RequestsCookieJar()
    c1 = Cookie(
        1,
        'name1',
        'value1',
        80,
        80,
        'domain',
        'domain_specified',
        'domain_initial_dot',
        'path',
        'path_specified',
        True,
        True,
        False,
        'comment',
        'comment_url',
        'rest',
    )
    c2 = Cookie(
        1,
        'name2',
        'value2',
        80,
        80,
        'domain',
        'domain_specified',
        'domain_initial_dot',
        'path',
        'path_specified',
        True,
        True,
        False,
        'comment',
        'comment_url',
        'rest',
    )

    jar.set_cookie(c1)
    jar.set_cookie(c2)
    c._session.cookies = jar

    assert c.cookie_dict == {'name1': 'value1', 'name2': 'value2'}

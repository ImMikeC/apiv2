from unittest.mock import Mock


def requests_mock(routes: dict, method='get'):
    """Arequests mock"""
    if method == 'get':

        def side_effect(url, headers=None):
            return routes.get(url, f'unhandled request {url}')
    elif method == 'post':

        def side_effect(url, data=None, headers=None):
            return routes.get(url, f'unhandled request {url}')
    else:
        raise Exception(f'{method} are not implemented too')
    return Mock(side_effect=side_effect)

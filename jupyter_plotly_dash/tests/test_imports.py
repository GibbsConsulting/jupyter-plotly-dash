'''
Test imports work
'''

def test_wrapper_loading():
    'Test loading of wrapper module'
    from ..dash_wrapper import JupyterDash
    assert JupyterDash

def test_async_views_loading():
    'Test loading of async module'
    from ..async_views import AsyncViews
    assert AsyncViews


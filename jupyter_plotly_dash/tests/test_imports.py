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

def test_ipython_loading():
    'Test loading of ipython module'
    from ..ipython import load_ipython_extension
    assert load_ipython_extension

def test_nbkernel_loading():
    'Test loading of nbkernel module'
    from ..nbkernel import locate_jpd_comm
    assert locate_jpd_comm

def test_nbsrvext_loading():
    'Test loading of nbsrvext module'
    from ..nbsrvext import wrapped_on_message
    assert wrapped_on_message


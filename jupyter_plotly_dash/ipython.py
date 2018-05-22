'''
Extensions for jupyter ipython use
'''

def dash_app(line, cell=None):
    print("dash_app magic")
    print(line)
    print(cell)

def load_ipython_extension(shell):
    shell.register_magic_function(dash_app,'line_cell')

def unload_ipython_extension(shell):
    del shell.magics_manager.magics['cell']['dash_app']


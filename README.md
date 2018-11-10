# jupyter-plotly-dash

[![PyPI version](https://badge.fury.io/py/jupyter-plotly-dash.svg)](https://badge.fury.io/py/jupyter-plotly-dash)
[![Downloads](https://img.shields.io/pypi/dw/jupyter-plotly-dash.svg)](https://img.shields.io/pypi/dw/jupyter-plotly-dash.svg)
![Develop Branch Build Status](https://travis-ci.org/GibbsConsulting/jupyter-plotly-dash.svg?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/GibbsConsulting/jupyter-plotly-dash/badge.svg?branch=master)](https://coveralls.io/github/GibbsConsulting/jupyter-plotly-dash?branch=master)
[![Documentation Status](https://readthedocs.org/projects/jupyter-plotly-dash/badge/?version=latest)](https://jupyter-plotly-dash.readthedocs.io/en/latest/?badge=latest)

Allow use of [plotly dash](https://plot.ly/products/dash/) applications within Jupyter notebooks, with the management of both session and internal state.

See the source for this project here:
<https://github.com/GibbsConsulting/jupyter-plotly-dash>

Try me here in your browser: [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/GibbsConsulting/jupyter-plotly-dash/master)

More detailed information
can be found in the online documentation at
<https://readthedocs.org/projects/jupyter-plotly-dash>

## Installation

Install the package. Use of a `virtualenv` environment is strongly recommended.

    pip install jupyter_plotly_dash

Now the package is installed, it can be used within a Jupyter notebook.

## Simple use

After installation, launch a python Jupyter notebook server using `jupyter notebook` or `jupyter lab` as desired. Create a `Dash` application, using
the `JupyterDash` class instead of `dash.Dash` for the application, and copy the following into a code cell and evaluate it.

```python
from jupyter_plotly_dash import JupyterDash

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

app = JupyterDash('SimpleExample')

app.layout = html.Div([
    dcc.RadioItems(
        id='dropdown-color',
        options=[{'label': c, 'value': c.lower()}
                 for c in ['Red', 'Green', 'Blue']],
        value='red'
    ),
    html.Div(id='output-color'),
    dcc.RadioItems(
        id='dropdown-size',
        options=[{'label': i, 'value': j}
                 for i, j in [('L','large'), ('M','medium'), ('S','small')]],
        value='medium'
    ),
    html.Div(id='output-size')

])

@app.callback(
    dash.dependencies.Output('output-color', 'children'),
    [dash.dependencies.Input('dropdown-color', 'value')])
def callback_color(dropdown_value):
    return "The selected color is %s." % dropdown_value

@app.callback(
    dash.dependencies.Output('output-size', 'children'),
    [dash.dependencies.Input('dropdown-color', 'value'),
     dash.dependencies.Input('dropdown-size', 'value')])
def callback_size(dropdown_color, dropdown_size):
    return "The chosen T-shirt is a %s %s one." %(dropdown_size,
                                                  dropdown_color)

app
```

The last line causes the dash application to be rendered. All callbacks are invoked asynchronously, so the display of an
application does not prevent other notebook cells from being evaluated. Multiple instances of the same dash application
can be rendered at the same time within a single notebook.

## Binder use

To launch a binder
image, visit [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/GibbsConsulting/jupyter-plotly-dash/master) to
run Jupyter notebooks using the latest version on the master branch of the main repository.

#!/usr/bin/env python

from setuptools import setup, find_packages

with open('jupyter_plotly_dash/version.py') as f:
    exec(f.read())

with open('README.md') as f:
    long_description = f.read()

setup(
    name="jupyter-plotly-dash",
    version=__version__,
    url="https://github.com/GibbsConsulting/jupyter-plotly-dash",
    description="Interactive Jupyter use of plotly dash apps",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Gibbs Consulting",
    author_email="jupyter_plotly_dash@gibbsconsulting.ca",
    license='MIT',
    packages=find_packages(),
    classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU Affero General Public License v3',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    ],
    keywords='Jupyter plotly plotly-dash dash dashboard django-plotly-dash Django',
    project_urls = {
    'Source': "https://github.com/GibbsConsulting/jupyter-plotly-dash",
    'Tracker': "https://github.com/GibbsConsulting/jupyter-plotly-dash/issues",
    'Documentation': 'http://jupyter-plotly-dash.readthedocs.io/',
    },
    install_requires = ['aiohttp',
                        'django-plotly-dash',
                        'jupyter',
                        'nbserverproxy',
                        ],
    python_requires=">=3.6",
    data_files = [
    ("etc/jupyter/jupyter_notebook_config.d", [
    "jupyter-config/jupyter_notebook_config.d/jupyter-plotly-dash.json"
    ])
    ],
    include_package_data = True,
    zip_safe = False,
    )


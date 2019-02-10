.. _development:

Development
+++++++++++

To build and run the documentation in a local test environment::

  source env/bin/activate
  cd docs && sphinx-autobuild . _build/html -p 8000

To run a local server for the README file using the grip tool::

  source env/bin/activate
  grip

To build and release the packages::

  source env/bin/activate

  python setup.py sdist
  python setup.py bdist_wheel

  twine upload dist/*

.. _contributions::

Contributions
-------------

See the CONTRIBUTIONS.md file in the code repository for details.

.. _bug_reporting:

The ideal bug report is a pull request containing the addition of a failing test exhibiting the problem
to the test suite. However, this rarely happens in practice!

The essential requirement of a bug report is that it contains enough information to characterise the issue, and ideally
also provides some way of replicating it. Issues that cannot be replicated within a virtualenv are unlikely to
get much attention, if any.

To report a bug, create a `github issue <https://github.com/GibbsConsulting/jupyter-plotly-dash/issues>`_.


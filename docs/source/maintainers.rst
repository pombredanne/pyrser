*****************
Maintainers GUIDE
*****************

Tests suite
===========
Run all tests::

    $>python3 tests

Run a specific test::

    $>python3 -m unittest tests/internal_dsl.py


Setup your environment
======================
Install setuptools and sphinx::

    pip3 install setuptools sphinx sphinxcontrib-programoutput

Clone the pyrser repository::

    git clone git@github.com:LionelAuroux/pyrser.git

Prepare package and documentation
=================================
Test everything builds correctly::

    python setup.py build_sphinx sdist

Uploading a new package to pypi
===============================
Don't forget to upgrade the package number or delete the package you want to
replace on pypi before running the following command::

    python setup.py sdist register upload


Links for reset syntax
======================
- http://docutils.sourceforge.net/rst.html <http://docutils.sourceforge.net/rst.html>
- http://docutils.sourceforge.net/docs/user/rst/quickref.html <http://docutils.sourceforge.net/docs/user/rst/quickref.html>
- http://docutils.sourceforge.net/docs/user/rst/cheatsheet.txt <http://docutils.sourceforge.net/docs/user/rst/cheatsheet.txt>


pritunl: vpn server
===================

.. image:: http://gitshields.com/v2/pypi/pritunl/version/7d0ce8.png
    :target: https://pypi.python.org/pypi/pritunl

.. image:: http://gitshields.com/v2/pypi/pritunl/month_down/ff4a20.png
    :target: https://pypi.python.org/pypi/pritunl

.. image:: http://gitshields.com/v2/text/license/AGPLv3/blue.png
    :target: https://www.gnu.org/licenses/agpl-3.0.html

.. image:: http://gitshields.com/v2/drone/github.com/pritunl/pritunl/brightgreen-red.png
    :target: https://drone.io/github.com/pritunl/pritunl

`Pritunl <https://github.com/pritunl/pritunl>`_ is an open source vpn server.
Documentation and more information can be found at the home page
`pritunl.com <http://pritunl.com>`_

Development Setup
-----------------

.. code-block:: bash

    $ git clone https://github.com/pritunl/pritunl.git
    $ cd pritunl
    $ python2 server.py
    # Open http://localhost:9700/

Vagrant Setup
-------------

.. code-block:: bash

    $ git clone https://github.com/pritunl/pritunl.git
    $ cd pritunl
    $ vagrant up
    $ vagrant ssh
    $ cd /vagrant
    $ sudo python2 server.py
    # Open http://localhost:9700/

Unittest
--------

.. code-block:: bash

    $ git clone https://github.com/pritunl/pritunl.git
    $ cd pritunl
    $ python2 test_pritunl.py

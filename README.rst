Pritunl: Simple openvpn server
==============================

.. image:: http://gitshields.com/v1/pypi/pritunl/version/7d0ce8.png
    :target: https://crate.io/packages/pritunl
S
.. image:: http://gitshields.com/v1/pypi/pritunl/month_down/ff4a20.png
    :target: https://crate.io/packages/pritunl

.. image:: http://gitshields.com/v1/text/license/AGPLv3/blue.png
    :target: https://www.gnu.org/licenses/agpl-3.0.html

.. image:: http://gitshields.com/v1/drone/pritunl/pritunl/brightgreen-red.png
    :target: https://drone.io/github.com/pritunl/pritunl

`Pritunl <https://github.com/pritunl/pritunl>`_ is a simple openvpn server
management tool. Multiple organizations, users and openvpn servers can be
managed and configured from a simple web interface. Documentation and more
information can be found at the home page `pritunl.com <http://pritunl.com>`_

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
    # Open http://localhost:6500/
    # Open http://localhost:8080/collectd

Testing
-------

.. code-block:: bash

    $ git clone https://github.com/pritunl/pritunl.git
    $ cd pritunl
    $ python2 test_pritunl.py

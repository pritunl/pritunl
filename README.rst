Pritunl: Simple openvpn server
==============================

.. image:: https://pypip.in/v/pritunl/badge.png
    :target: https://crate.io/packages/pritunl

.. image:: https://pypip.in/d/pritunl/badge.png
    :target: https://crate.io/packages/pritunl

Simple openvpn server. Currently in development, not ready for use.

Development Setup
-----------------

.. code-block:: bash

    $ git clone https://github.com/zachhuff386/pritunl.git
    $ cd pritunl
    $ python2 server.py
    # Open http://localhost:9700/

Vagrant Setup
-------------

.. code-block:: bash

    $ git clone https://github.com/zachhuff386/pritunl.git
    $ cd pritunl
    $ vagrant up
    $ vagrant ssh
    $ cd /vagrant
    $ sudo python2 server.py
    # Open http://localhost:6500/
    # Open http://localhost:8080/collectd

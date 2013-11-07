Pritunl: Simple openvpn server
==============================

.. image:: https://pypip.in/v/pritunl/badge.png
    :target: https://crate.io/packages/pritunl

.. image:: https://pypip.in/d/pritunl/badge.png
    :target: https://crate.io/packages/pritunl

`Pritunl <https://github.com/zachhuff386/pritunl>`_ is a simple openvpn server
management tool. Multiple organizations, users and openvpn servers can be
managed and configured from a simple web interface. Documentation and more
information can be found at the home page `pritunl.com <http://pritunl.com>`_

Development Setup
-----------------

.. code-block:: bash

    $ git clone https://github.com/zachhuff386/pritunl.git
    $ cd pritunl
    $ python2 server.py
    # Open http://localhost:9700/

Vagrant Setup
-------------

First make sure you have a precise64 image. This command will fetch one.

``vagrant box add precise64 http://files.vagrantup.com/precise64.box``

.. code-block:: bash

    $ git clone https://github.com/zachhuff386/pritunl.git
    $ cd pritunl
    $ vagrant up
    $ vagrant ssh
    $ cd /vagrant
    $ sudo python2 server.py
    # Open http://localhost:6500/
    # Open http://localhost:8080/collectd

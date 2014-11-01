pritunl: enterprise vpn server
==============================

.. image:: http://gitshields.com/v2/pypi/pritunl/version/43617e.png
    :target: https://pypi.python.org/pypi/pritunl

.. image:: http://www.gitshields.com/v2/text/package/ubuntu/dd4814.png
    :target: https://launchpad.net/~pritunl/+archive/ubuntu/ppa

.. image:: http://www.gitshields.com/v2/text/package/arch%20linux/33aadd.png
    :target: https://aur.archlinux.org/packages/pritunl/

.. image:: http://www.gitshields.com/v2/text/package/centos/669900.png
    :target: http://pritunl.com/#install

.. image:: http://gitshields.com/v2/drone/github.com/pritunl/pritunl/589d59-b64d39.png
    :target: https://drone.io/github.com/pritunl/pritunl

`Pritunl <https://github.com/pritunl/pritunl>`_ is an enterprise vpn server.
Documentation and more information can be found at the home page
`pritunl.com <http://pritunl.com>`_

.. image:: www/img/logo_full.png
    :target: http://pritunl.com

Development Setup
-----------------

.. code-block:: bash

    $ git clone https://github.com/pritunl/pritunl.git
    $ cd pritunl
    $ vagrant up
    $ foreman start
    # Open node0 http://localhost:9700/
    # Open node1 http://localhost:9701/
    # Open node2 http://localhost:9702/
    # Open node3 http://localhost:9703/

Development Setup (Single Node)
-------------------------------

.. code-block:: bash

    $ git clone https://github.com/pritunl/pritunl.git
    $ cd pritunl
    $ vagrant up node0 mongodb
    $ vagrant ssh node0
    $ cd /vagrant
    $ sudo python2 server.py
    # Open http://localhost:9700/

Unittest
--------

.. code-block:: bash

    $ git clone https://github.com/pritunl/pritunl.git
    $ cd pritunl
    $ python2 test_pritunl.py

License
-------

Please refer to the `LICENSE` file for a copy of the license

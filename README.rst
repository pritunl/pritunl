pritunl: enterprise vpn server
==============================

.. image:: http://gitshields.com/v2/pypi/pritunl/version/43617e.png
    :target: http://pritunl.com/

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

Please refer to the `LICENSE` file for a copy of the license. This license
is incomplete and only apply's to the code in this repository. It does not
apply to the current release (v0.10.12) which is licensed under AGPLv3.

Export Requirements
-------------------

You may not export or re-export this software or any copy or adaptation in
violation of any applicable laws or regulations.

Without limiting the generality of the foregoing, hardware, software,
technology or services provided under this license agreement may not be
exported, reexported, transferred or downloaded to or within (or to a national
resident of) countries under U.S. economic embargo including the following
countries:

Cuba, Iran, Libya, North Korea, Sudan and Syria. This list is subject to
change.

Hardware, software, technology or services may not be exported, reexported,
transferred or downloaded to persons or entities listed on the U.S. Department
of Commerce Denied Persons List, Entity List of proliferation concern or on
any U.S. Treasury Department Designated Nationals exclusion list, or to
parties directly or indirectly involved in the development or production of
nuclear, chemical, biological weapons or in missile technology programs as
specified in the U.S. Export Administration Regulations (15 CFR 744).

By accepting this license agreement you confirm that you are not located in
(or a national resident of) any country under U.S. economic embargo, not
identified on any U.S. Department of Commerce Denied Persons List, Entity List
or Treasury Department Designated Nationals exclusion list, and not directly
or indirectly involved in the development or production of nuclear, chemical,
biological weapons or in missile technology programs as specified in the U.S.
Export Administration Regulations.

Software available on this web site contains cryptography and is therefore
subject to US government export control under the U.S. Export Administration
Regulations ("EAR"). EAR Part 740.13(e) allows the export and reexport of
publicly available encryption source code that is not subject to payment of
license fee or royalty payment. Object code resulting from the compiling of
such source code may also be exported and reexported under this provision if
publicly available and not subject to a fee or payment other than reasonable
and customary fees for reproduction and distribution. This kind of encryption
source code and the corresponding object code may be exported or reexported
without prior U.S. government export license authorization provided that the
U.S. government is notified about the Internet location of the software.

The software available on this web site is publicly available without license
fee or royalty payment, and all binary software is compiled from the source
code. The U.S. government has been notified about this site and the location
site for the source code. Therefore, the source code and compiled object code
may be downloaded and exported under U.S. export license exception (without a
U.S. export license) in accordance with the further restrictions outlined
above regarding embargoed countries, restricted persons and restricted end
uses.

Local Country Import Requirements. The software you are about to download
contains cryptography technology. Some countries regulate the import, use
and/or export of certain products with cryptography. Pritunl makes no
claims as to the applicability of local country import, use and/or export
regulations in relation to the download of this product. If you are located
outside the U.S. and Canada you are advised to consult your local country
regulations to insure compliance.

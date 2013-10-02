# Maintainer: Zachary Huff <zach.huff.386@gmail.com>

pkgname=pritunl
pkgver=0.0.2
pkgrel=1
pkgdesc="Simple openvpn server"
arch=("any")
license=("AGPL3")
url="https://github.com/zachhuff386/${pkgname}"
depends=(
    "python2"
    "python2-flask"
    "python2-cherrypy"
    "openvpn"
)
makedepends=(
    "python2-distribute"
)
provides=("${pkgname}")
conflicts=("${pkgname}")
source=("${url}/archive/${pkgver}.tar.gz")
sha256sums=("CHANGE_ME")
backup=(
    "etc/${pkgname}.conf"
    "var/lib/${pkgname}/${pkgname}.db"
    "var/log/${pkgname}.log"
)

build() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    python2 setup.py build
}

package() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    python2 setup.py install --root="${pkgdir}" --prefix=/usr --no-upstart
}

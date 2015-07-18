# Maintainer: Pritunl <contact@pritunl.com>

pkgname=pritunl
pkgver=1.3.662.15
pkgrel=1
pkgdesc="Enterprise VPN Server"
arch=("any")
license=("custom")
url="https://github.com/${pkgname}/${pkgname}"
depends=(
    "python"
    "python2"
    "python2-flask"
    "python2-pyopenssl"
    "python2-pymongo"
    "net-tools"
    "iproute2"
    "openvpn"
)
optdepends=(
    "mongodb"
)
makedepends=(
    "python2-distribute"
    "python2-flask"
    "python2-pyopenssl"
    "python2-pymongo"
)
provides=("${pkgname}")
conflicts=("${pkgname}")
install=${pkgname}.install
source=("${url}/archive/${pkgver}.tar.gz")
sha256sums=("bb835e0d9da1920f2baee10ec905edbaa849c0faed5264948599ddc81778588b")
options=("emptydirs")
backup=(
    "etc/${pkgname}.conf"
    "var/lib/${pkgname}/${pkgname}.db"
    "var/log/${pkgname}.log"
    "var/log/${pkgname}.log.1"
)

build() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    python2 setup.py build
}

package() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    mkdir -p "${pkgdir}/var/lib/${pkgname}"
    python2 setup.py install --root="${pkgdir}" --prefix=/usr --no-upstart
}

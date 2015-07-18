FROM pritunl/archlinux:latest
MAINTAINER Pritunl <contact@pritunl.com>

RUN pacman -S --noconfirm python2 python2-flask python2-pyopenssl python2-pymongo net-tools iproute2 openvpn
RUN wget https://s3.amazonaws.com/blckur/beanstalkd-1.10-1-x86_64.pkg.tar.xz
RUN pacman -U --noconfirm beanstalkd-1.10-1-x86_64.pkg.tar.xz

ENV GOPATH /go
ENV PATH $PATH:/go/bin

RUN go get github.com/blckur/blckur # a0ff08a309ed5022c3002a03c7829e716c0765d9

CMD ["blckur", "queue"]

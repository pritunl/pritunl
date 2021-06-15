FROM ubuntu:focal-20210416

MAINTAINER cboatwri <cboatwright@equinix.com>

ENV VERSION 1.30.2817.44 


# Build deps

RUN apt update

ENV TZ=America/Los_Angeles DEBIAN_FRONTEND="noninteractive"

RUN  apt-get -y install emacs-nox \
    git \
    docker \
    curl \
    build-essential \
    devscripts \
    ccache \
    gawk \
    libelf-dev \
    wget \
    apt-utils \
    linux-source \
    flex \
    bison \
    openssl \
    bzr \
    ca-certificates \
    openvpn \
    python3-pip \
    python2


RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
RUN python2 ./get-pip.py

RUN pip install --upgrade pip

ENV GO_VERSION 1.16.5
ENV GO_OS linux
ENV GO_ARCH amd64
RUN curl -O https://dl.google.com/go/go$GO_VERSION.$GO_OS-$GO_ARCH.tar.gz
RUN tar -C /usr/local -xzf go$GO_VERSION.$GO_OS-$GO_ARCH.tar.gz

# Pritunl InstallENV

ENV PATH=$PATH:/usr/local/go/bin


ENV GOPATH /go

RUN go get -u github.com/pritunl/pritunl-dns \
    && go get -u github.com/pritunl/pritunl-web

RUN git clone https://github.com/packethost/pritunl \
    && cd pritunl \
    && git checkout $VERSION \
    && python2 setup.py build \
    && pip install -r requirements.txt \
    && python2 setup.py install \
    && cd .. 

COPY entrypoint.sh /usr/local/bin/entrypoint.sh

EXPOSE 80 443 1194

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
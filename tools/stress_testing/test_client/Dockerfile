FROM pritunl/archlinux
MAINTAINER Pritunl <contact@pritunl.com>

RUN pacman -S --noconfirm go git bzr openvpn net-tools wget

ENV GOPATH /go
ENV PATH $PATH:/go/bin
RUN go get github.com/gin-gonic/gin

ADD . /test_client
WORKDIR /test_client

ENTRYPOINT ["go", "run", "client.go"]

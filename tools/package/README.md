# pritunl: package

Build test package

## install pacur

```bash
sudo dnf -y install git-core podman

sudo rm -rf /usr/local/go
wget https://go.dev/dl/go1.25.4.linux-amd64.tar.gz
echo "9fa5ffeda4170de60f67f3aa0f824e426421ba724c21e133c1e35d6159ca1bec go1.25.4.linux-amd64.tar.gz" | sha256sum -c - && sudo tar -C /usr/local -xf go1.25.4.linux-amd64.tar.gz
rm -f go1.25.4.linux-amd64.tar.gz

tee -a ~/.bashrc << EOF
export GO111MODULE=on
export GOPATH=\$HOME/go
export GOROOT=/usr/local/go
export PATH=/usr/local/go/bin:\$PATH:\$HOME/go/bin
EOF
chown cloud:cloud ~/.bashrc
source ~/.bashrc

go install github.com/pacur/pacur@latest
cd "$(ls -d ~/go/pkg/mod/github.com/pacur/pacur@*/docker/ | sort -V | tail -n 1)"
sudo find . -maxdepth 1 -type d -name "*" ! -name "." ! -name ".." ! -name "oraclelinux-10" -exec rm -rf {} +
sh clean.sh
sh build.sh
cd
```

## build package

```bash
git clone https://github.com/pritunl/pritunl.git
cd pritunl/tools/package

sudo podman run --rm -t -v `pwd`:/pacur:Z localhost/pacur/oraclelinux-10
```

# IPFS swarm

To get started, make sure to have [vagrant](https://www.vagrantup.com) correctly running on your machine. After doing some, follow the steps for each ipfs swarm node

The following is the dependencies installation process that needs to be done in both

1. go to node1 folder and run `vagrant up`
2. connect to the machine with `vagrant ssh` and update everything with `sudo apt update && sudo apt upgrade -y`
3. install golang follwing the tutorial below
4. install ipfs following the tutorial below
5. create ipfs init local config with `ipfs init` (local config is saved at `.ipfs/config`, by default)

Now, in each machine, there are a few different steps. On node1, we will setup the swarm, and on node2, we will simply join it. See [here](https://github.com/ipfs/go-ipfs/blob/master/docs/experimental-features.md#private-networks) for more info.

node 1:
1. download ipfs swarm generator with `go get github.com/Kubuxu/go-ipfs-swarm-key-gen/ipfs-swarm-key-gen`
2. generate ipfs swarm key with `ipfs-swarm-key-gen > ~/.ipfs/swarm.key`
3. delete all bootstrap nodes with `ipfs bootstrap rm --all`

node2:
1. copy `~/.ipfs/swarm.key` from node1 to the exact same location
2. delete all bootstrap nodes with `ipfs bootstrap rm --all`
3. connect to node1 with `ipfs swarm connect /ip4/<ip-address>/tcp/4001/ipfs/<peer-identity>`

At this point you can upload files and get them on the other machine. So for example, on node2, create a file named `some.txt` with "hello i'm a file" in it. Upload that file using `ipfs add some.txt`. Now, one node1, get that file with `ipfs cat /ipfs/<hash-printed-on-upload>`.

## Install GoLang on ubuntu

1. download go with `curl -O https://dl.google.com/go/go1.10.3.linux-amd64.tar.gz`
2. unpack `tar xvf go1.10.3.linux-amd64.tar.gz`
3. give permission `sudo chown -R <user>:<group> ./go` (by default in vagrant it's `vagrant:vagrant`)
4. make it available from folders in PATH `sudo mv go /usr/local`
4. open the profile config with `sudo nano ~/.profile` and add the following to the end
```
export GOPATH=$HOME/work
export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin
```
5. create the work folder with `mkdir $HOME/work`
6. refresh bash with `source ~/.profile`
7. try go with `go version`

## Install IPFS on ubuntu

1. download ipfs with `curl https://dist.ipfs.io/go-ipfs/v0.4.22/go-ipfs_v0.4.22_linux-amd64.tar.gz -o go-ipfs.tar.gz`
2. unpack `tar xvfz go-ipfs.tar.gz`
3. go to go-ipfs folder with `cd go-ipfs` and install it `sudo ./install.sh`
4. try ipfs with `ipfs version`

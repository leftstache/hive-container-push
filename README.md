# Leftstache Hive for Docker

## Container Push

Syncs the container data from a docker daemon to Zookeeper.

This allows other services to easily look up what's running on each nodes and listen for changes on containers.

### Build

```docker build -t leftstache/hive-container-push .```

### Run

```docker run --rm -e ADVERTISE_NAME={someaddressiblename or ip} -e ZK_HOSTS={zookeeper connection string} -it -v /var/run/docker.sock:/var/run/docker.sock leftstache/hive-container-push```


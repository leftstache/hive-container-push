import threading
from pprint import pprint

import docker
from kazoo.client import KazooClient
import kazoo.exceptions
import os
import socket
import json
import docker.errors
import requests.exceptions


end = False


def sync(docker_client: docker.Client, zk: KazooClient, node_path):
    events = docker_client.events()
    for event_str in events:
        if end:
            break
        event = json.loads(event_str.decode('utf-8'))

        if 'Type' in event and event['Type'] == 'container' and 'id' in event:
            container_id = event['id']
            container_zk_path = "{}/containers/{}".format(node_path, container_id)

            if 'Action' in event:
                if event['Action'] == 'destroy':
                    update_data(zk, container_zk_path, None)
                else:
                    try:
                        container = docker_client.inspect_container(container_id)
                        data = json.dumps(container).encode("utf-8")
                        update_data(zk, container_zk_path, data)
                    except docker.errors.APIError:
                        pass
                    except requests.exceptions.HTTPError:
                        pass


def main():
    global end

    root_zk_path = os.environ.get("ZK_BASE", '/leftstache/hive')
    zk_connection_string = os.environ.get("ZK_HOSTS", "localhost:2181")
    advertise_name = os.environ.get("ADVERTISE_NAME", None)
    if advertise_name is None:
        advertise_name = socket.gethostname()

    docker_client = docker.from_env()
    zk = KazooClient(hosts=zk_connection_string)
    zk.start()
    node_zk_path = "{}/nodes/{}".format(root_zk_path, advertise_name)
    try:
        try:
            zk.create("{}".format(node_zk_path), makepath=True)
        except kazoo.exceptions.NodeExistsError:
            pass

        thread = threading.Thread(target=sync, args=[docker_client, zk, node_zk_path])
        thread.start()

        containers = docker_client.containers(all=True)
        for container in containers:
            container = docker_client.inspect_container(container)
            data = json.dumps(container).encode("utf-8")
            container_zk_path = "{}/containers/{}".format(node_zk_path, container['Id'])
            update_data(zk, container_zk_path, data)

        thread.join()
    except KeyboardInterrupt:
        end = True
        try:
            # Force the thread to read an event so it can terminate
            container = docker_client.create_container("busybox")
            docker_client.remove_container(container)
        finally:
            docker_client.close()
    finally:
        zk.delete(path=node_zk_path, recursive=True)
        zk.stop()


def update_data(zk, path, data):
    if data is None:
        try:
            print("deleting", path)
            zk.delete(path, recursive=True)
            print("deleted", path)
        except kazoo.exceptions.NoNodeError:
            print("path doesn't exist to delete", path)

    else:
        print("setting: " + path)
        try:
            zk.create(path, data, makepath=True, ephemeral=True)
            print("created: " + path)
        except kazoo.exceptions.NodeExistsError:
            zk.set(path, data)
            print("updated: " + path)

if __name__ == "__main__":
    main()
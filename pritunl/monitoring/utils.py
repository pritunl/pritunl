import urllib.parse

def get_servers(uri):
    uri = urllib.parse.urlparse(uri)

    netloc = uri.netloc.split('@', 1)
    if len(netloc) == 2:
        username, password = netloc[0].split(':', 1)
        netloc = netloc[1]
    else:
        username = None
        password = None
        netloc = netloc[0]

    hosts = []
    netloc = netloc.split(',')
    for host in netloc:
        host, port = host.split(':', 1)
        try:
            port = int(port)
        except:
            port = 0

        hosts.append((host, port))

    if uri.path:
        database = uri.path.replace('/', '', 1)
    else:
        database = None

    return hosts, username, password, database

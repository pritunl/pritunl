class BaseError(Exception):
    def __init__(self, message, data):
        self.__dict__.update(data)
        message = '%s. %r' % (message, data)
        Exception.__init__(self, message)


class UserError(BaseError):
    pass

class KeyLinkError(UserError):
    pass


class ServerError(BaseError):
    pass

class ServerMissingOrg(ServerError):
    pass

class ServerStartError(ServerError):
    pass

class ServerStopError(ServerError):
    pass

class InvalidNodeAPIKey(ServerError):
    pass

class NodeConnectionError(ServerError):
    pass

class IptablesError(ServerError):
    pass

class InvalidStaticFile(ServerError):
    pass

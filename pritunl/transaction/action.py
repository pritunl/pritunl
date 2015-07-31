from pritunl.constants import *

class TransactionAction:
    def __init__(self, actions, func):
        self._actions = actions
        self._func = func

    def __call__(self, *args, **kwargs):
        from pritunl.transaction.collection import TransactionCollection
        self._actions.append([
            self._func,
            args or '',
            kwargs or '',
        ])
        return TransactionCollection(self._actions)

    def __getattr__(self, name):
        if name in MONGO_ACTION_METHODS:
            return TransactionAction(self._actions, name)
        raise AttributeError(
            'TransactionAction instance has no attribute %r' % name)

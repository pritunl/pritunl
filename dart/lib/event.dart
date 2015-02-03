library event;

Map<String, Set<Function>> listeners = {};

class Listener {
  String _key;
  Function _listener;

  Listener(this._key, this._listener);

  void deregister() {
    listeners[this._key].remove(this._listener);
  }
}

Listener register(Function listener, String type, [String resourceId]) {
  var key;

  if (resourceId != null) {
    key = '$type:$resourceId';
  }
  else {
    key = type;
  }

  if (listeners[key] == null) {
    listeners[key] = new Set();
  }

  listeners[key].add(listener);

  return new Listener(key, listener);
}

library event;

Map<String, Set<Function>> listeners = {};

class Listener {
  String _key;
  Function _listener;

  Listener(this._key, this._listener);

  void deregister() {
    listeners[this._key].remove(this._listener);
  }

  void update(String type, [String resource]) {
    this.deregister();
    register(this._listener, type, resource);
  }
}

Listener register(Function listener, String type, [String resource]) {
  var key;

  if (resource != null) {
    key = '$type:$resource';
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

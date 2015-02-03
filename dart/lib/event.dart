library event;

Map<String, Set<Function>> listeners;

void register(Function listener, String type, [String resourceId]) {
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
}

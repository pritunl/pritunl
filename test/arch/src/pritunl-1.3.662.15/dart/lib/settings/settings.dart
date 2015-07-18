library settings;

var _data = {};
var _observers = {};

dynamic get(String name) {
  return _data[name];
}

set(String name, dynamic value) {
  _data[name] = value;
  if (_observers[name] != null) {
    _observers[name](name, value);
  }
}

void observe(String name, Function callback) {
  _observers[name] = callback;
}

library settings;

var _data = {};
var _observers = {};

get(name) {
  return _data[name];
}

set(name, value) {
  _data[name] = value;
  if (_observers[name] != null) {
    _observers[name](name, value);
  }
}

observe(name, callback) {
  _observers[name] = callback;
}

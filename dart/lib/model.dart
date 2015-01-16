library model;

import 'package:angular/angular.dart' as ng;
import 'dart:mirrors' as mirrors;
import 'dart:async' as async;
import 'dart:math' as math;

var _attrSymbols = {};
var _attrValidators = {};

class Attribute {
  final name;
  const Attribute(this.name);
}

class Validator {
  final name;
  const Validator(this.name);
}

class Invalid extends Error {
  var type;
  var message;

  Invalid(this.type, this.message);

  toString() => this.message;
}

class Model {
  var _loadCheckId;
  var http;
  var url;
  var errorStatus;
  var errorData;
  var loadingLong;

  get _symbols {
    if (!_attrSymbols.containsKey(this.runtimeType)) {
      var symbols = {};
      var validators = {};
      var mirror = mirrors.reflect(this).type;

      mirror.declarations.forEach((value, varMirror) {
        varMirror.metadata.forEach((metadata) {
          if (metadata.reflectee is Attribute) {
            symbols[metadata.reflectee.name] = value;
          }
          else if (metadata.reflectee is Validator) {
            validators[metadata.reflectee.name] = value;
          }
        });
      });

      _attrSymbols[this.runtimeType] = symbols;
      _attrValidators[this.runtimeType] = validators;
    }
    return _attrSymbols[this.runtimeType];
  }

  get _validators {
    return _attrValidators[this.runtimeType];
  }

  var _loading;
  set loading(val) {
    if (val) {
      var loadCheckId = new math.Random().nextInt(32000);
      this._loadCheckId = loadCheckId;
      this._loading = true;

      new async.Future.delayed(
        const Duration(milliseconds: 200), () {
          if (this._loadCheckId == loadCheckId) {
            this.loadingLong = true;
          }
        });
    }
    else {
      this._loadCheckId = null;
      this.loadingLong = false;
      this._loading = false;
    }
  }
  get loading {
    return this._loading;
  }

  Model(ng.Http this.http);

  validate(name) {
    var symbols = this._symbols;
    var validators = this._validators;
    var mirror = mirrors.reflect(this);
    var validator = mirror.getField(validators[name]);
    validator.apply([mirror.getField(symbols[name]).reflectee]);
  }

  clone() {
    var symbols = this._symbols;
    var mirror = mirrors.reflect(this);
    var clone = mirror.type.newInstance(const Symbol(''), [this.http]);

    symbols.forEach((name, symbol) {
      clone.setField(symbol, mirror.getField(symbol).reflectee);
    });

    return clone.reflectee;
  }

  fetch() {
    this.loading = true;

    return this.http.get(this.url).then((response) {
      this.loading = false;
      this.import(response.data);
      return response.data;
    }).catchError((err) {
      this.loading = false;
      this.errorStatus = err.status;
      this.errorData = err.data;
      throw err;
    });
  }

  parse(data) {
    return data;
  }

  import(responseData) {
    var symbols = this._symbols;
    var data = this.parse(responseData);
    var mirror = mirrors.reflect(this);

    data.forEach((key, value) {
      var symbol = symbols[key];
      if (symbol == null) {
        return;
      }

      mirror.setField(symbol, value);
    });
  }

  _send(method, fields) {
    var data = {};
    var symbols = this._symbols;
    var mirror = mirrors.reflect(this);

    this.loading = true;

    if (fields != null) {
      fields.forEach((name) {
        var symbol = symbols[name];
        data[name] = mirror.getField(symbol).reflectee;
      });
    }
    else {
      symbols.forEach((name, symbol) {
        data[name] = mirror.getField(symbol).reflectee;
      });
    }

    if (method == 'post') {
      method = this.http.post;
    }
    else if (method == 'put') {
      method = this.http.put;
    }
    else {
      throw new ArgumentError('Unkown method');
    }

    return method(this.url, data).then((response) {
      this.loading = false;
      this.import(response.data);
      return response.data;
    }).catchError((err) {
      this.loading = false;
      this.errorStatus = err.status;
      this.errorData = err.data;
      throw err;
    });
  }

  save([fields]) {
    return this._send('put', fields);
  }

  create([fields]) {
    return this._send('post', fields);
  }

  clear() {
    var symbols = this._symbols;
    var mirror = mirrors.reflect(this);

    symbols.values.forEach((symbol) {
      mirror.setField(symbol, null);
    });
  }
}

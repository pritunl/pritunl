library model;

import 'package:pritunl/remote.dart' as remote;

import 'package:angular/angular.dart' as ng;
import 'dart:mirrors' as mirrors;
import 'dart:async' as async;

Map<Type, Map<String, Symbol>> _attrSymbols = {};
Map<Type, Map<String, Function>> _attrValidators = {};

class Attribute {
  final String name;
  const Attribute(this.name);
}

class Validator {
  final String name;
  const Validator(this.name);
}

class Invalid extends Error {
  String type;
  String message;

  Invalid(this.type, this.message);

  toString() => this.message;
}

_buildAttrs(model) {
  if (!_attrSymbols.containsKey(model.runtimeType)) {
    var symbols = {};
    var validators = {};
    var mirror = mirrors.reflect(model).type;

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

    _attrSymbols[model.runtimeType] = symbols;
    _attrValidators[model.runtimeType] = validators;
  }
}

abstract class Model extends remote.Remote {
  String id;
  Function onLinkClear;

  Model(ng.Http http) : super(http) {
    this.init();
  }

  Map<String, Symbol> get _symbols {
    _buildAttrs(this);
    return _attrSymbols[this.runtimeType];
  }

  Map<String, Function> get _validators {
    _buildAttrs(this);
    return _attrValidators[this.runtimeType];
  }

  void validate(String name) {
    var symbols = this._symbols;
    var validators = this._validators;
    var mirror = mirrors.reflect(this);
    var validator = mirror.getField(validators[name]);
    validator.apply([mirror.getField(symbols[name]).reflectee]);
  }

  Model clone() {
    var symbols = this._symbols;
    var mirror = mirrors.reflect(this);
    var clone = mirror.type.newInstance(const Symbol(''), [this.http]);

    symbols.forEach((name, symbol) {
      clone.setField(symbol, mirror.getField(symbol).reflectee);
    });

    return clone.reflectee;
  }

  void import(dynamic responseData) {
    var symbols = this._symbols;
    var data = this.parse(responseData);
    var mirror = mirrors.reflect(this);

    if (data != null && data != '') {
      data.forEach((key, value) {
        var symbol = symbols[key];
        if (symbol == null) {
          return;
        }

        mirror.setField(symbol, value);
      });
    }

    this.imported();
    if (this.onImport != null) {
      this.onImport();
    }
  }

  Map<String, dynamic> export([List<String> fields]) {
    var data = {};
    var symbols = this._symbols;
    var mirror = mirrors.reflect(this);

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

    return data;
  }

  async.Future destroy() {
    var loadId = this.setLoading();

    return this.http.delete(this.url).then((response) {
      this.clearLoading(loadId);
      this.clearError();
      this.import(response.data);
      return response.data;
    }).catchError((err) {
      this.clearLoading(loadId);
      return new async.Future.error(this.parseError(err));
    }, test: (e) => e is ng.HttpResponse);
  }

  async.Future send(String method, String url, List<String> fields) {
    var symbols = this._symbols;
    var mirror = mirrors.reflect(this);
    var loadId = this.setLoading();
    var methodFunc;

    var data = this.export(fields);

    if (method == 'post') {
      methodFunc = this.http.post;
    }
    else if (method == 'put') {
      methodFunc = this.http.put;
    }
    else {
      throw new ArgumentError('Unkown method');
    }

    return methodFunc(url, data).then((response) {
      this.clearLoading(loadId);
      this.clearError();
      this.import(response.data);
      return response.data;
    }).catchError((err) {
      this.clearLoading(loadId);
      return new async.Future.error(this.parseError(err));
    }, test: (e) => e is ng.HttpResponse);
  }

  async.Future save([List<String> fields]) {
    return this.send('put', this.url, fields);
  }

  async.Future create([List<String> fields]) {
    return this.send('post', this.url, fields);
  }

  void clear() {
    var symbols = this._symbols;
    var mirror = mirrors.reflect(this);

    symbols.values.forEach((symbol) {
      mirror.setField(symbol, null);
    });
  }

  void init() {
  }
}

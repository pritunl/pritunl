library remote;

import 'package:pritunl/event.dart' as evnt;
import 'package:pritunl/exceptions.dart';

import 'package:angular/angular.dart' as ng;
import 'dart:async' as async;
import 'dart:math' as math;

abstract class Remote {
  int _loadCheckId;
  ng.Http http;
  String url;
  String error;
  String errorMsg;
  int errorStatus;
  bool loadingLong;
  evnt.Listener listener;
  Function onImport;

  Remote(this.http);

  var _loading;
  void set loading(bool val) {
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
  bool get loading {
    return this._loading;
  }

  String get eventType {
    throw new UnimplementedError();
  }

  String get eventResource {
    return null;
  }

  dynamic parse(dynamic data) {
    return data;
  }

  dynamic parseError(dynamic err) {
    var httpErr = new HttpError(err);

    this.error = httpErr.error;
    this.errorMsg = httpErr.errorMsg;
    this.errorStatus = httpErr.resp.status;

    return httpErr;
  }

  void clearError() {
    this.error = null;
    this.errorMsg = null;
    this.errorStatus = null;
  }

  void import(dynamic responseData);

  void imported() {
  }

  async.Future fetch() {
    this.loading = true;

    return this.http.get(this.url).then((response) {
      this.loading = false;
      this.import(response.data);
      return response.data;
    }).catchError((err) {
      this.loading = false;
      return new async.Future.error(this.parseError(err));
    }, test: (e) => e is ng.HttpResponse);
  }
}

library events_col;

import 'package:pritunl/collection.dart' as collec;
import 'package:pritunl/models/event.dart' as evnt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;
import 'dart:async' as async;

@Injectable()
class Events extends collec.Collection {
  Type model = evnt.Event;
  String cursor;
  ng.RootScope rootScope;

  Events(ng.Http http, this.rootScope) : super(http);

  String get url {
    var url = '/event';

    if (this.cursor != null) {
      url += '/${this.cursor}';
    }

    return url;
  }

  void imported() {
    if (this.length > 0) {
      this.cursor = this[this.length - 1].id;
    }

    for (var event in this) {
      this.rootScope.broadcast(event.type, event);
    }
  }

  void fetchLoop() {
    this.fetch().then((_) {
      this.fetchLoop();
    }).catchError((err) {
      logger.severe('Event fetch error', err);
      new async.Timer(const Duration(seconds: 1), () {
        this.fetchLoop();
      });
    });
  }

  void start() {
    this.fetchLoop();
  }
}

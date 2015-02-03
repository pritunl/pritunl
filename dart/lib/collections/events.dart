library events_col;

import 'package:pritunl/collection.dart' as collection;
import 'package:pritunl/models/event.dart' as event;
import 'package:pritunl/logger.dart' as logger;
import 'package:pritunl/event.dart' as evnt;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;
import 'dart:async' as async;

@Injectable()
class Events extends collection.Collection {
  Type model = event.Event;
  String cursor;

  String get url {
    var url = '/event';

    if (this.cursor != null) {
      url += '/${this.cursor}';
    }

    return url;
  }

  Events(ng.Http http) : super(http);

  void imported() {
    if (this.length > 0) {
      this.cursor = this[this.length - 1].id;
    }

    for (var event in this) {
      var listenerSets = [event.type];

      if (event.resourceId != null) {
        listenerSets.add('${event.type}:${event.resourceId}');
      }

      listenerSets.forEach((listeners) {
        if (listeners != null) {
          listeners.forEach((listener) {
            listener(event);
          });
        }
      });
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

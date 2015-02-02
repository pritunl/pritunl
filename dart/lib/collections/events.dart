library events_col;

import 'package:pritunl/collection.dart' as collection;
import 'package:pritunl/models/event.dart' as event;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Events extends collection.Collection {
  Type model = event.Event;
  String cursor;

  String get url {
    var url = 'event';

    if (this.cursor != null) {
      url += '/${this.cursor}';
    }

    return url;
  }

  Events(ng.Http http) : super(http);
}

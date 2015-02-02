library event_mod;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Event extends model.Model {
  @model.Attribute('id')
  String id;

  @model.Attribute('type')
  String type;

  @model.Attribute('resource_id')
  String resourceId;

  @model.Attribute('timestamp')
  double timestamp;

  Event(ng.Http http) : super(http);
}

library event_mod;

import 'package:pritunl/model.dart' as mdl;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Event extends mdl.Model {
  @mdl.Attribute('id')
  String id;

  @mdl.Attribute('type')
  String type;

  @mdl.Attribute('resource_id')
  String resourceId;

  @mdl.Attribute('timestamp')
  double timestamp;

  Event(ng.Http http) : super(http);
}

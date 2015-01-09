library organization;

import 'package:pritunl/collection.dart' as collection;
import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Organizations extends collection.Collection {
  var model = organization.Organization;

  get url {
    return '/organization';
  }

  Organizations(ng.Http http) : super(http);
}

library organization_col;

import 'package:pritunl/collection.dart' as collection;
import 'package:pritunl/models/organization.dart' as org;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Organizations extends collection.Collection {
  Type model = org.Organization;
  String eventType = 'orgs_updated';

  String get url {
    return '/organization';
  }

  Organizations(ng.Http http) : super(http);
}

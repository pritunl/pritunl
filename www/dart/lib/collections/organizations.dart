library organizations_col;

import 'package:pritunl/collection.dart' as collec;
import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Organizations extends collec.Collection {
  Type model = organization.Organization;

  Organizations(ng.Http http) : super(http);

  String get url {
    return '/organization';
  }
}

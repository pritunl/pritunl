library users;

import 'package:pritunl/collection.dart' as collection;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Users extends collection.Collection {
  var model = user.User;
  var org_id;
  var hidden;

  get url {
    return '/user/${this.org_id}';
  }

  Users(ng.Http http) : super(http);
}

library organization;

import 'package:pritunl/model.dart' as model;
import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Organization extends model.Model {
  var name;
  var user_count;
  var users;

  get url {
    return '/organization/${this.id}';
  }

  var _id;
  get id {
    return this._id;
  }
  set id(val) {
    this.users.org_id = val;
    this._id = val;
  }

  Organization(ng.Http http) :
      users = new usrs.Users(http),
      super(http);
}

library organization;

import 'package:pritunl/model.dart' as model;
import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Organization extends model.Model {
  usrs.Users users;

  @model.Attribute('name')
  String name;

  @model.Validator('name')
  void nameValidator(val) {
    if (val == null || val == '') {
      throw new model.Invalid('empty',
        'Organization name cannot be empty');
    }
  }

  @model.Attribute('user_count')
  int userCount;

  var _id;
  @model.Attribute('id')
  String get id {
    return this._id;
  }
  set id(String val) {
    this.users.orgId = val;
    this._id = val;
  }

  String get url {
    var url = '/organization';

    if (this.id != null) {
      url += '/${this.id}';
    }

    return url;
  }

  Organization(ng.Http http) :
      users = new usrs.Users(http),
      super(http);
}

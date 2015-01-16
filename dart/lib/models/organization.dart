library organization;

import 'package:pritunl/model.dart' as model;
import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Organization extends model.Model {
  var users;

  @model.Attribute('name')
  var name;

  @model.Validator('name')
  nameValidator(val) {
    if (val == null) {
      throw new model.Invalid('empty',
        'Organization name cannot be empty');
    }
  }

  @model.Attribute('user_count')
  var userCount;

  var _id;
  @model.Attribute('id')
  get id {
    return this._id;
  }
  set id(val) {
    this.users.orgId = val;
    this._id = val;
  }

  get url {
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

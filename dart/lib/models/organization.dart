library organization_mod;

import 'package:pritunl/model.dart' as model;
import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Organization extends model.Model {
  @model.Linked()
  usrs.Users users;

  @model.Attribute('name')
  String name;

  @model.Validator('name')
  void nameValidator(val) {
    if (val == null || val == '') {
      throw new model.Invalid('empty', 'Organization name cannot be empty');
    }
  }

  @model.Attribute('user_count')
  int userCount;

  @model.Attribute('id')
  String id;

  Organization(ng.Http http) :
    users = new usrs.Users(http),
    super(http);

  String get url {
    var url = '/organization';

    if (this.id != null) {
      url += '/${this.id}';
    }

    return url;
  }
}

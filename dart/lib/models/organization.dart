library organization_mod;

import 'package:pritunl/model.dart' as mdl;
import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Organization extends mdl.Model {
  usrs.Users users;

  @mdl.Attribute('name')
  String name;

  @mdl.Validator('name')
  void nameValidator(val) {
    if (val == null || val == '') {
      throw new mdl.Invalid('empty', 'Organization name cannot be empty');
    }
  }

  @mdl.Attribute('user_count')
  int userCount;

  @mdl.Attribute('id')
  String id;

  Organization(ng.Http http) : super(http);

  String get url {
    var url = '/organization';

    if (this.id != null) {
      url += '/${this.id}';
    }

    return url;
  }
}

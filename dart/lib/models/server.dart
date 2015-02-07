library server_mod;

import 'package:pritunl/model.dart' as mdl;
import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Server extends mdl.Model {
  usrs.Users users;

  @mdl.Attribute('id')
  String id;

  @mdl.Attribute('name')
  String name;

  @mdl.Validator('name')
  void nameValidator(val) {
    if (val == null || val == '') {
      throw new mdl.Invalid('empty', 'Server name cannot be empty');
    }
  }

  Server(ng.Http http) : super(http);

  String get url {
    var url = '/server';

    if (this.id != null) {
      url += '/${this.id}';
    }

    return url;
  }

  void init() {
  }
}

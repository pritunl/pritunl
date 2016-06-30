library key_mod;

import 'package:pritunl/model.dart' as mdl;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Injectable()
class Key extends mdl.Model {
  String org;
  String user;

  @mdl.Attribute('key_url')
  String keyUrl;

  @mdl.Attribute('view_url')
  String viewUrl;

  @mdl.Attribute('uri_url')
  String uriUrl;

  Key(ng.Http http) : super(http);

  String get _baseUrl {
    var loc = dom.window.location;
    return '${loc.protocol}//${loc.host}';
  }

  String get _basePritunlUrl {
    var loc = dom.window.location;
    return 'pritunl://${loc.host}';
  }

  String get fullKeyUrl {
    if (this.keyUrl == null) {
      return null;
    }
    return this._baseUrl + this.keyUrl;
  }

  String get fullViewUrl {
    if (this.viewUrl == null) {
      return null;
    }
    return this._baseUrl + this.viewUrl;
  }

  String get fullUriUrl {
    if (this.uriUrl == null) {
      return null;
    }
    return this._basePritunlUrl + this.uriUrl;
  }

  String get url {
    return '/key/${this.org}/${this.user}';
  }
}

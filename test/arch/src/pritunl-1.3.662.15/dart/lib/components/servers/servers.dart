library servers_comp;

import 'package:pritunl/collections/servers.dart' as svrs;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'x-servers',
  templateUrl: 'packages/pritunl/components/servers/servers.html',
  cssUrl: 'packages/pritunl/components/servers/servers.css'
)
class ServersComp implements ng.ScopeAware {
  svrs.Servers servers;
  ng.Http http;

  ServersComp(this.http) {
    this.servers = new svrs.Servers(this.http);
    this.update();
  }

  void set scope(ng.Scope scope) {
    scope.on('servers_updated').listen((_) {
      this.update();
    });
  }

  void update() {
    this.servers.fetch().catchError((err) {
      logger.severe('Failed to load servers', err);
      new alrt.Alert('Failed to load servers, server error occurred.',
        'danger');
    });
  }

  String _curMessage;
  String get message {
    return null;
  }
}

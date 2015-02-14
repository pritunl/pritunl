library server_comp;

import 'package:pritunl/models/server.dart' as svr;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'server',
  templateUrl: 'packages/pritunl/components/server/server.html',
  cssUrl: 'packages/pritunl/components/server/server.css'
)
class ServerComp implements ng.AttachAware, ng.ScopeAware {
  bool showHidden;

  @NgOneWayOneTime('model')
  svr.Server model;

  void updateOutput() {
    this.model.output.fetch().catchError((err) {
      logger.severe('Failed to load server output', err);
      new alrt.Alert('Failed to load server output, server error occurred.',
      'danger');
    });
  }

  void updateOrgs() {
    this.model.orgs.fetch().then((_) {
      print(this.model.orgs);
    }).catchError((err) {
      logger.severe('Failed to load server organizations', err);
      new alrt.Alert('Failed to load server organizations, '
        'server error occurred.', 'danger');
    });
  }

  void set scope(ng.Scope scope) {
    scope.on('server_output_updated').listen((evt) {
      if (evt.data.resourceId == this.model.id) {
        this.updateOutput();
      }
    });
    scope.on('server_organizations_updated').listen((evt) {
      if (evt.data.resourceId == this.model.id) {
        this.updateOrgs();
      }
    });
  }

  void attach() {
    this.updateOutput();
    this.updateOrgs();
  }

  void toggleHidden() {
    this.showHidden = this.showHidden != true;
  }
}

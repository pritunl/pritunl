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
  Map<String, String> dataModeTypes;

  @NgOneWayOneTime('model')
  svr.Server model;

  ServerComp() : dataModeTypes = {
    'svrOutput': 'default',
    'linkOutput': 'primary',
    'bandwidth': 'primary',
  };

  String get message {
    var noOrgs = this.model.orgs.length == 0;
    var noHosts = this.model.hosts.length == 0;

    if (noOrgs || noHosts) {
      if (!noOrgs) {
        return 'Server must have a host attached';
      }
      else if (!noHosts) {
        return 'Server must have an organization attached';
      }
      return 'Server must have a host and an organization attached';
    }

    return null;
  }

  void updateOutput() {
    this.model.output.fetch().catchError((err) {
      logger.severe('Failed to load server output', err);
      new alrt.Alert('Failed to load server output, server error occurred.',
        'danger');
    });
  }

  void updateOrgs() {
    this.model.orgs.fetch().catchError((err) {
      logger.severe('Failed to load server organizations', err);
      new alrt.Alert('Failed to load server organizations, '
        'server error occurred.', 'danger');
    });
  }

  void updateHosts() {
    this.model.hosts.fetch().catchError((err) {
      logger.severe('Failed to load server hosts', err);
      new alrt.Alert('Failed to load server hosts, '
        'server error occurred.', 'danger');
    });
  }

  void onSvrOutput() {
    this.dataModeTypes['linkOutput'] = 'primary';
    this.dataModeTypes['bandwidth'] = 'primary';
    this.dataModeTypes['svrOutput'] = 'default';
  }

  void onLinkOutput() {
    this.dataModeTypes['svrOutput'] = 'primary';
    this.dataModeTypes['bandwidth'] = 'primary';
    this.dataModeTypes['linkOutput'] = 'default';
  }

  void onBandwidth() {
    this.dataModeTypes['svrOutput'] = 'primary';
    this.dataModeTypes['linkOutput'] = 'primary';
    this.dataModeTypes['bandwidth'] = 'default';
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
    scope.on('server_hosts_updated').listen((evt) {
      if (evt.data.resourceId == this.model.id) {
        this.updateHosts();
      }
    });
  }

  void attach() {
    this.updateOutput();
    this.updateOrgs();
    this.updateHosts();
  }

  void toggleHidden() {
    this.showHidden = this.showHidden != true;
  }
}

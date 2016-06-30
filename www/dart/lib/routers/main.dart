library main_rout;

import 'package:pritunl/settings/settings.dart' as settings;
import 'package:pritunl/alert.dart' as alrt;

import 'package:angular/angular.dart' as ng;

MainRout(ng.Router router, ng.RouteViewFactory views) {
  views.configure({
    'dashboard': ng.ngRoute(
      path: '/dashboard',
      view: 'packages/pritunl/views/dashboard.html',
      enter: (_) {
        alrt.clear();
        settings.set('active_page', 'dashboard');
      },
      defaultRoute: true
    ),
    'users': ng.ngRoute(
      path: '/users',
      view: 'packages/pritunl/views/users.html',
      enter: (_) {
        alrt.clear();
        settings.set('active_page', 'users');
      }
    ),
    'servers': ng.ngRoute(
      path: '/servers',
      view: 'packages/pritunl/views/servers.html',
      enter: (_) {
        alrt.clear();
        settings.set('active_page', 'servers');
      }
    )
  });
}

library main_rout;

import 'package:pritunl/settings/settings.dart' as settings;

import 'package:angular/angular.dart' as ng;

MainRout(ng.Router router, ng.RouteViewFactory views) {
  views.configure({
    'root': ng.ngRoute(
      path: '',
      view: 'packages/pritunl/views/dashboard.html',
      enter: (_) {
        settings.set('active_page', 'dashboard');
      }
    ),
    'dashboard': ng.ngRoute(
      path: '/dashboard',
      view: 'packages/pritunl/views/dashboard.html',
      enter: (_) {
        settings.set('active_page', 'dashboard');
      },
      defaultRoute: true
    ),
    'users': ng.ngRoute(
      path: '/users',
      view: 'packages/pritunl/views/users.html',
      enter: (_) {
        settings.set('active_page', 'users');
      }
    )
  });
}

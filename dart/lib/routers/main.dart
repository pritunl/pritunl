library main;

import 'package:pritunl/settings/settings.dart' as settings;

import 'package:angular/angular.dart' as ng;

MainRout(router, views) {
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
      }
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

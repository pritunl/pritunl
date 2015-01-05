library main;

import 'package:angular/angular.dart' as ng;

route({path, view}) {
  return ng.ngRoute(
    path: path,
    view: 'packages/pritunl/views/$view'
  );
}

MainRout(router, views) {
  views.configure({
    'root': route(
      path: '',
      view: 'dashboard.html'
    ),
    'dashboard': route(
      path: '/dashboard',
      view: 'dashboard.html'
    )
  });
}

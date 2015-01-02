library main;

import 'package:angular/angular.dart' as ng;

route({path, view}) {
  return ng.ngRoute(
    path: path,
    view: '/packages/pritunl/views/$view'
  );
}

MainRout(router, views) {
  views.configure({
    'dashboard': route(
      path: '',
      view: 'dashboard.html'
    )
  });
}

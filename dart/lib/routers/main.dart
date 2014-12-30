part of routers;

route({path, view}) {
  return ng.ngRoute(
    path: path,
    view: '/packages/pritunl/views/$view'
  );
}

Main(router, views) {
  views.configure({
    'dashboard': route(
      path: '',
      view: 'dashboard.html'
    )
  });
}

define([
  'jquery',
  'underscore',
  'backbone',
  'models/auth',
  'views/alert',
  'views/login',
  'views/modalChangePassword',
  'text!templates/header.html'
], function($, _, Backbone, AuthModel, AlertView, LoginView,
    ModalChangePasswordView, headerTemplate) {
  'use strict';
  var stripeImg = 'data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbm' +
    'NvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjwhLS0gQ3JlYXRlZCB3aXRoIElu' +
    'a3NjYXBlIChodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy8pIC0tPgoKPHN2ZwogICB4bWxucz' +
    'pkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgIHhtbG5zOmNjPSJo' +
    'dHRwOi8vY3JlYXRpdmVjb21tb25zLm9yZy9ucyMiCiAgIHhtbG5zOnJkZj0iaHR0cDovL3' +
    'd3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyIKICAgeG1sbnM6c3ZnPSJo' +
    'dHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3' +
    'JnLzIwMDAvc3ZnIgogICB4bWxuczpzb2RpcG9kaT0iaHR0cDovL3NvZGlwb2RpLnNvdXJj' +
    'ZWZvcmdlLm5ldC9EVEQvc29kaXBvZGktMC5kdGQiCiAgIHhtbG5zOmlua3NjYXBlPSJodH' +
    'RwOi8vd3d3Lmlua3NjYXBlLm9yZy9uYW1lc3BhY2VzL2lua3NjYXBlIgogICB3aWR0aD0i' +
    'MjAwIgogICBoZWlnaHQ9IjIwMCIKICAgdmlld0JveD0iMCAwIDIwMCAyMDAiCiAgIGlkPS' +
    'JzdmcyIgogICB2ZXJzaW9uPSIxLjEiCiAgIGlua3NjYXBlOnZlcnNpb249IjAuNDguNCBy' +
    'OTkzOSIKICAgc29kaXBvZGk6ZG9jbmFtZT0ibG9nb19zdHJpcGUuc3ZnIj4KICA8ZGVmcw' +
    'ogICAgIGlkPSJkZWZzNCIgLz4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgaWQ9ImJh' +
    'c2UiCiAgICAgcGFnZWNvbG9yPSIjMDAwMDAwIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2Nj' +
    'Y2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEuMCIKICAgICBpbmtzY2FwZTpwYWdlb3BhY2l0' +
    'eT0iMC44MzUyOTQxMiIKICAgICBpbmtzY2FwZTpwYWdlc2hhZG93PSIyIgogICAgIGlua3' +
    'NjYXBlOnpvb209IjIuODI4NDI3MiIKICAgICBpbmtzY2FwZTpjeD0iNDEuODg2NjE4Igog' +
    'ICAgIGlua3NjYXBlOmN5PSI4My44OTY4NiIKICAgICBpbmtzY2FwZTpkb2N1bWVudC11bm' +
    'l0cz0icHgiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ibGF5ZXIxIgogICAgIHNo' +
    'b3dncmlkPSJmYWxzZSIKICAgICBmaXQtbWFyZ2luLXRvcD0iMCIKICAgICBmaXQtbWFyZ2' +
    'luLWxlZnQ9IjAiCiAgICAgZml0LW1hcmdpbi1yaWdodD0iMCIKICAgICBmaXQtbWFyZ2lu' +
    'LWJvdHRvbT0iMCIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjE5MTQiCiAgICAgaW' +
    '5rc2NhcGU6d2luZG93LWhlaWdodD0iOTk4IgogICAgIGlua3NjYXBlOndpbmRvdy14PSIw' +
    'IgogICAgIGlua3NjYXBlOndpbmRvdy15PSIyNyIKICAgICBpbmtzY2FwZTp3aW5kb3ctbW' +
    'F4aW1pemVkPSIxIiAvPgogIDxtZXRhZGF0YQogICAgIGlkPSJtZXRhZGF0YTciPgogICAg' +
    'PHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgIC' +
    'AgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6' +
    'dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbW' +
    'l0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAg' +
    'ICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxnCiAgIC' +
    'AgaW5rc2NhcGU6bGFiZWw9IkxheWVyIDEiCiAgICAgaW5rc2NhcGU6Z3JvdXBtb2RlPSJs' +
    'YXllciIKICAgICBpZD0ibGF5ZXIxIgogICAgIHRyYW5zZm9ybT0idHJhbnNsYXRlKC0yND' +
    'EuNTMxMiwtMTYzLjUpIj4KICAgIDxyZWN0CiAgICAgICBzdHlsZT0iZmlsbDojMmU0MTUz' +
    'O2ZpbGwtb3BhY2l0eToxO3N0cm9rZTpub25lIgogICAgICAgd2lkdGg9IjIwMCIKICAgIC' +
    'AgIGhlaWdodD0iMjAwIgogICAgICAgeD0iMjQxLjUzMTIiCiAgICAgICB5PSIxNjMuNSIK' +
    'ICAgICAgIGlkPSJyZWN0NDQyNCIgLz4KICAgIDx0ZXh0CiAgICAgICB4bWw6c3BhY2U9In' +
    'ByZXNlcnZlIgogICAgICAgc3R5bGU9ImZvbnQtc2l6ZTo0MHB4O2ZvbnQtc3R5bGU6bm9y' +
    'bWFsO2ZvbnQtd2VpZ2h0Om5vcm1hbDtsaW5lLWhlaWdodDoxMjUlO2xldHRlci1zcGFjaW' +
    '5nOjBweDt3b3JkLXNwYWNpbmc6MHB4O2ZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtz' +
    'dHJva2U6bm9uZTtmb250LWZhbWlseTpTYW5zIgogICAgICAgeD0iMjc5LjgzMzQ3IgogIC' +
    'AgICAgeT0iMzIzLjEyNzAxIgogICAgICAgaWQ9InRleHQyOTg2IgogICAgICAgc29kaXBv' +
    'ZGk6bGluZXNwYWNpbmc9IjEyNSUiPjx0c3BhbgogICAgICAgICBzb2RpcG9kaTpyb2xlPS' +
    'JsaW5lIgogICAgICAgICBpZD0idHNwYW4yOTg4IgogICAgICAgICB4PSIyNzkuODMzNDci' +
    'CiAgICAgICAgIHk9IjMyMy4xMjcwMSIKICAgICAgICAgc3R5bGU9ImZvbnQtc2l6ZToyMj' +
    'BweDtmb250LXN0eWxlOm5vcm1hbDtmb250LXZhcmlhbnQ6bm9ybWFsO2ZvbnQtd2VpZ2h0' +
    'Om5vcm1hbDtmb250LXN0cmV0Y2g6bm9ybWFsO2ZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdH' +
    'k6MTtmb250LWZhbWlseTpGcmVkb2thIE9uZTstaW5rc2NhcGUtZm9udC1zcGVjaWZpY2F0' +
    'aW9uOkZyZWRva2EgT25lIj5wPC90c3Bhbj48L3RleHQ+CiAgPC9nPgo8L3N2Zz4K';

  var HeaderView = Backbone.View.extend({
    tagName: 'header',
    template: _.template(headerTemplate),
    events: {
      'click .enterprise-upgrade a': 'onEnterpriseUpgrade',
      'click .change-password a': 'changePassword'
    },
    render: function() {
      this.$el.html(this.template());
      return this;
    },
    onEnterpriseUpgrade: function() {
      if (this.onEnterpriseUpgradeLock) {
        return;
      }
      this.onEnterpriseUpgradeLock = true;
      $.getCachedScript('https://checkout.stripe.com/checkout.js', {
        success: function() {
          var checkout = window.StripeCheckout.configure({
            key: 'pk_test_cex9CxHTANzcSdOdeoqhgMy9',
            image: stripeImg,
            name: 'Pritunl Enterprise',
            description: 'Enterprise Plan ($2.50/month)',
            amount: 250,
            panelLabel: 'Subscribe',
            allowRememberMe: false,
            token: function(token, args) {
              console.log(token, args);
            }
          });
          checkout.open();
          this.onEnterpriseUpgradeLock = false;
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load upgrade checkout, try again later.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.onEnterpriseUpgradeLock = false;
        }.bind(this)
      });
    },
    changePassword: function() {
      var loginView = new LoginView({
        showChangePassword: true
      });
      if (loginView.active) {
        $('body').append(loginView.render().el);
        this.addView(loginView);
      }
    }
  });

  return HeaderView;
});

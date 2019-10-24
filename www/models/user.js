define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var UserModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'organization': null,
      'organization_name': null,
      'name': null,
      'email': null,
      'groups': null,
      'gravatar': null,
      'audit': null,
      'type': null,
      'auth_type': null,
      'yubico_id': null,
      'status': null,
      'sso': null,
      'otp_auth': null,
      'otp_secret': null,
      'servers': null,
      'disabled': null,
      'network_links': null,
      'dns_mapping': null,
      'bypass_secondary': null,
      'client_to_client': null,
      'dns_servers': null,
      'dns_suffix': null,
      'port_forwarding': null,
      'pin': null
    },
    url: function() {
      var url = '/user/' + this.get('organization');

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    },
    destroyOtpSecret: function(options) {
      this.save(null, _.extend({
        url: this.url() + '/otp_secret'
      }, options));
    },
    portForwardingFormatted: function() {
      var portForwarding = this.get('port_forwarding');
      if (!portForwarding) {
        return '';
      }

      var item;
      var port;
      var ports = [];

      for (var i = 0; i < portForwarding.length; i++) {
        item = portForwarding[i];

        port = item.port;

        if (item.dport) {
          port += ':' + item.dport;
        }

        if (item.protocol) {
          port += '/' + item.protocol;
        }

        ports.push(port);
      }

      return ports.join(', ');
    },
    parse: function(response) {
      this.set({'hidden': response.type !== 'client'});
      return response;
    }
  });

  return UserModel;
});

define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var SettingsModel = Backbone.Model.extend({
    defaults: {
      'username': null,
      'password': null,
      'auditing': null,
      'token': null,
      'secret': null,
      'default': null,
      'email_server': null,
      'email_username': null,
      'email_password': null,
      'email_from': null,
      'pin_mode': null,
      'monitoring': null,
      'datadog_api_key': null,
      'sso': null,
      'sso_match': null,
      'sso_host': null,
      'sso_token': null,
      'sso_secret': null,
      'sso_admin': null,
      'sso_org': null,
      'sso_saml_url': null,
      'sso_saml_issuer_url': null,
      'sso_saml_cert': null,
      'sso_okta_token': null,
      'sso_onelogin_key': null,
      'public_address': null,
      'theme': null,
      'server_cert': null,
      'server_key': null,
      'cloud_provider': null,
      'us_east_1_access_key': null,
      'us_east_1_secret_key': null,
      'us_west_1_access_key': null,
      'us_west_1_secret_key': null,
      'us_west_2_access_key': null,
      'us_west_2_secret_key': null,
      'eu_west_1_access_key': null,
      'eu_west_1_secret_key': null,
      'eu_central_1_access_key': null,
      'eu_central_1_secret_key': null,
      'ap_northeast_1_access_key': null,
      'ap_northeast_1_secret_key': null,
      'ap_northeast_2_access_key': null,
      'ap_northeast_2_secret_key': null,
      'ap_southeast_1_access_key': null,
      'ap_southeast_1_secret_key': null,
      'ap_southeast_2_access_key': null,
      'ap_southeast_2_secret_key': null,
      'sa_east_1_access_key': null,
      'sa_east_1_secret_key': null
    },
    url: function() {
      return '/settings';
    },
    isNew: function() {
      return false;
    }
  });

  return SettingsModel;
});

define([
  'jquery',
  'underscore',
  'backbone',
  'collections/org',
  'models/zones',
  'views/modal',
  'text!templates/modalSettings.html'
], function($, _, Backbone, OrgCollection, ZonesModel, ModalView,
    modalSettingsTemplate) {
  'use strict';
  var ModalSettingsView = ModalView.extend({
    className: 'settings-modal',
    template: _.template(modalSettingsTemplate),
    title: 'Settings',
    okText: 'Save',
    enterOk: false,
    hasAdvanced: true,
    events: function() {
      return _.extend({
        'click .sso-mode select': 'onSsoMode',
        'change .pass input': 'onPassChange',
        'keyup .pass input': 'onPassEvent',
        'paste .pass input': 'onPassEvent',
        'input .pass input': 'onPassEvent',
        'change .route53-region select': 'updateZones',
        'click .sso-client-cache': 'onSsoClientCacheSelect',
        'click .sso-okta-push': 'onSsoOktaPushSelect',
        'propertychange .pass input': 'onPassEvent',
        'change .cloud-provider select': 'onCloudProviderChange',
        'change .monitoring select': 'onMonitoringChange',
        'change .theme select': 'onThemeChange'
      }, ModalSettingsView.__super__.events);
    },
    initialize: function(options) {
      this.orgs = new OrgCollection();
      this.zones = new ZonesModel();
      this.initial = options.initial;
      this.curServerPort = this.model.get('server_port');
      this.curAcmeDomain = this.model.get('acme_domain') || null;
      if (this.initial) {
        this.title = 'Initial Setup';
        this.cancelText = 'Setup Later';
      }
      ModalSettingsView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template(_.extend({orgs: this.orgs.toJSON()},
        this.model.toJSON()));
    },
    postRender: function() {
      this.setLoading('Loading...');
      this.orgs.fetch({
        success: function() {
          this.clearLoading();
          for (var i = 0; i < this.orgs.length; i++) {
            var org = this.orgs.models[i];
            var selected = this.model.get('sso_org') === org.get('id');
            this.$('.sso-org select').append('<option ' +
              (selected ? 'selected ' : '') + 'value="' + org.get('id') +
              '">' + org.get('name') + '</option>');
          }
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to load organizations, server error occurred.');
        }.bind(this)
      });
      this.zones.fetch({
        success: function() {
          this.clearLoading();
          this.updateZones();
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to load Route 53 zones, server error occurred.');
        }.bind(this)
      });
    },
    updateZones: function() {
      var region = this.$('.route53-region select').val();
      var zone;

      var zones;
      if (!region) {
        this.$('.route53-zone select').html(
          '<option selected value="">Disabled</option>');
        return;
      } else {
        zones = this.zones.get(region) || [];
      }

      if (!zones.length) {
        this.$('.route53-zone select').html(
          '<option selected value="">No zones available</option>');
        return;
      }

      this.$('.route53-zone select').empty();

      var curZone = this.model.get('route53_zone') || zones[0];

      for (var i = 0; i < zones.length; i++) {
        zone = zones[i];
        this.$('.route53-zone select').append(
          '<option ' + (zone === curZone ? 'selected' : '') + ' value="' +
            zone + '">' + zone + '</option>');
      }
    },
    getSsoMode: function() {
      return this.$('.sso-mode select').val();
    },
    setSsoMode: function(mode) {
      if (!mode) {
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-org').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-client-cache').slideUp(window.slideTime);
        return;
      } else {
        this.$('.sso-org').slideDown(window.slideTime);
      }

      if (mode === 'saml') {
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'saml_duo') {
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-duo-mode').slideDown(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'saml_yubico') {
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'saml_okta') {
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-okta-token').slideDown(window.slideTime);
        this.$('.sso-okta-push').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'saml_okta_duo') {
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-duo-mode').slideDown(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-okta-token').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'saml_okta_yubico') {
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-okta-token').slideDown(window.slideTime);
        this.$('.sso-okta-push').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'saml_onelogin') {
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-onelogin-id').slideDown(window.slideTime);
        this.$('.sso-onelogin-secret').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'saml_onelogin_duo') {
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-duo-mode').slideDown(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-onelogin-id').slideDown(window.slideTime);
        this.$('.sso-onelogin-secret').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'saml_onelogin_yubico') {
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-onelogin-id').slideDown(window.slideTime);
        this.$('.sso-onelogin-secret').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'slack') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'google') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'slack_duo') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideDown(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-duo-mode').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'google_duo') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideDown(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-duo-mode').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'slack_yubico') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'google_yubico') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'duo') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideUp(window.slideTime);
        this.$('.sso-radius-secret').slideUp(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-duo-mode').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'radius') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-duo-mode').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideDown(window.slideTime);
        this.$('.sso-radius-secret').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      } else if (mode === 'radius_duo') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-okta-push').slideUp(window.slideTime);
        this.$('.sso-onelogin-id').slideUp(window.slideTime);
        this.$('.sso-onelogin-secret').slideUp(window.slideTime);
        this.$('.sso-match-slack').slideUp(window.slideTime);
        this.$('.sso-match-google').slideUp(window.slideTime);
        this.$('.sso-radius-host').slideDown(window.slideTime);
        this.$('.sso-radius-secret').slideDown(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-duo-mode').slideDown(window.slideTime);
        this.$('.sso-client-cache').slideDown(window.slideTime);
      }
    },
    getSsoClientCacheSelect: function() {
      return this.$('.sso-client-cache .selector').hasClass('selected');
    },
    setSsoClientCacheSelect: function(state) {
      if (state) {
        this.$('.sso-client-cache .selector').addClass('selected');
        this.$('.sso-client-cache .selector-inner').show();
      }
      else {
        this.$('.sso-client-cache .selector').removeClass('selected');
        this.$('.sso-client-cache .selector-inner').hide();
      }
    },
    onSsoClientCacheSelect: function() {
      this.setSsoClientCacheSelect(!this.getSsoClientCacheSelect());
    },
    getSsoOktaPushSelect: function() {
      return this.$('.sso-okta-push .selector').hasClass('selected');
    },
    setSsoOktaPushSelect: function(state) {
      if (state) {
        this.$('.sso-okta-push .selector').addClass('selected');
        this.$('.sso-okta-push .selector-inner').show();
      }
      else {
        this.$('.sso-okta-push .selector').removeClass('selected');
        this.$('.sso-okta-push .selector-inner').hide();
      }
    },
    onSsoOktaPushSelect: function() {
      this.setSsoOktaPushSelect(!this.getSsoOktaPushSelect());
    },
    onSsoMode: function() {
      this.setSsoMode(this.getSsoMode());
    },
    onCloudProviderChange: function() {
      if (this.$('.cloud-provider select').val() === 'aws') {
        this.$('.aws-settings').slideDown(window.slideTime);
      }
      else {
        this.$('.aws-settings').slideUp(window.slideTime);
      }
    },
    onMonitoringChange: function() {
      if (this.$('.monitoring select').val() === 'influxdb') {
        this.$('.influxdb-uri').slideDown(window.slideTime);
      }
      else {
        this.$('.influxdb-uri').slideUp(window.slideTime);
      }
    },
    onThemeChange: function() {
      if (this.$('.theme:visible select').val() === 'dark') {
        $('body').addClass('dark');
      }
      else {
        $('body').removeClass('dark');
      }
    },
    onPassChange: function() {
      var pass = this.$('.pass input').val();
      if (pass && (
            pass.length < 8 || !pass.match(/[0-9]/) ||
            (
              !pass.match(/[^a-zA-Z0-9]/) &&
              (!pass.match(/[a-z]/) || !pass.match(/[A-Z]/))
            )
          )) {
        this.setAlert('warning', 'Weak password.', '.pass');
      }
      else {
        this.clearAlert();
      }
    },
    onPassEvent: function() {
      var changeId = (new Date()).getTime();
      this.changeId = changeId;

      setTimeout(function() {
        if (this.changeId === changeId) {
          this.onPassChange();
        }
      }.bind(this), 500);
    },
    onOk: function() {
      var username = this.$('.username input').val();
      var password = this.$('.pass input').val();
      var verifyPassword = this.$('.verify-pass input').val();
      var auditing = this.$('.auditing select').val();
      var serverPort = this.$('.server-port input').val();
      var acmeDomain = this.$('.acme-domain input').val() || null;
      var monitoring = this.$('.monitoring select').val();
      var influxdbUriKey = this.$('.influxdb-uri input').val();
      var publicAddress = this.$('.public-address input').val();
      var publicAddress6 = this.$('.public-address6 input').val();
      var routedSubnet6 = this.$('.routed-subnet6 input').val();
      var reverseProxy = this.$('.reverse-proxy select').val();
      var theme = this.$('.theme:visible select').val();
      var emailFrom = this.$('.email-from input').val();
      var emailServer = this.$('.email-server input').val();
      var emailUsername = this.$('.email-username input').val();
      var emailPassword = this.$('.email-password input').val();
      var pinMode = this.$('.pin-mode select').val();
      var serverCert = this.$('.server-cert textarea').val();
      var serverKey = this.$('.server-key textarea').val();
      var cloudProvider = this.$('.cloud-provider select').val();
      var ssoYubicoClient = this.$('.sso-yubico-client input').val();
      var ssoYubicoSecret = this.$('.sso-yubico-secret input').val();
      var usEast1AccessKey = this.$(
        '.us-east-1-access-key input').val();
      var usEast1SecretKey = this.$(
        '.us-east-1-secret-key input').val();
      var usEast2AccessKey = this.$(
        '.us-east-2-access-key input').val();
      var usEast2SecretKey = this.$(
        '.us-east-2-secret-key input').val();
      var usWest1AccessKey = this.$(
        '.us-west-1-access-key input').val();
      var usWest1SecretKey = this.$(
        '.us-west-1-secret-key input').val();
      var usWest2AccessKey = this.$(
        '.us-west-2-access-key input').val();
      var usWest2SecretKey = this.$(
        '.us-west-2-secret-key input').val();
      var usGovWest1AccessKey = this.$(
        '.us-gov-west-1-access-key input').val();
      var usGovWest1SecretKey = this.$(
        '.us-gov-west-1-secret-key input').val();
      var euWest1AccessKey = this.$(
        '.eu-west-1-access-key input').val();
      var euWest1SecretKey = this.$(
        '.eu-west-1-secret-key input').val();
      var euWest2AccessKey = this.$(
        '.eu-west-2-access-key input').val();
      var euWest2SecretKey = this.$(
        '.eu-west-2-secret-key input').val();
      var euCentral1AccessKey = this.$(
        '.eu-central-1-access-key input').val();
      var euCentral1SecretKey = this.$(
        '.eu-central-1-secret-key input').val();
      var caCentral1AccessKey = this.$(
        '.ca-central-1-access-key input').val();
      var caCentral1SecretKey = this.$(
        '.ca-central-1-secret-key input').val();
      var apNortheast1AccessKey = this.$(
        '.ap-northeast-1-access-key input').val();
      var apNortheast1SecretKey = this.$(
        '.ap-northeast-1-secret-key input').val();
      var apNortheast2AccessKey = this.$(
        '.ap-northeast-2-access-key input').val();
      var apNortheast2SecretKey = this.$(
        '.ap-northeast-2-secret-key input').val();
      var apSoutheast1AccessKey = this.$(
        '.ap-southeast-1-access-key input').val();
      var apSoutheast1SecretKey = this.$(
        '.ap-southeast-1-secret-key input').val();
      var apSoutheast2AccessKey = this.$(
        '.ap-southeast-2-access-key input').val();
      var apSoutheast2SecretKey = this.$(
        '.ap-southeast-2-secret-key input').val();
      var apSouth1AccessKey = this.$(
        '.ap-south-1-access-key input').val();
      var apSouth1SecretKey = this.$(
        '.ap-south-1-secret-key input').val();
      var saEast1AccessKey = this.$(
        '.sa-east-1-access-key input').val();
      var saEast1SecretKey = this.$(
        '.sa-east-1-secret-key input').val();

      var route53Region = this.$('.route53-region select').val();
      var route53Zone = this.$('.route53-zone select').val();

      if (!route53Region || !route53Zone) {
        route53Region = null;
        route53Zone = null;
      }

      if (serverPort) {
        serverPort = parseInt(serverPort, 10);
      }

      if (reverseProxy === 'true') {
        reverseProxy = true;
      } else {
        reverseProxy = false;
      }

      var i;
      var sso = this.getSsoMode();
      var ssoMatch = null;
      var ssoOrg = null;
      var ssoSamlUrl = null;
      var ssoSamlIssuerUrl = null;
      var ssoSamlCert = null;
      var ssoOktaToken = null;
      var ssoOktaPush = null;
      var ssoOneLoginId = null;
      var ssoOneLoginSecret = null;
      var ssoRadiusHost = null;
      var ssoRadiusSecret = null;
      var ssoDuoToken = null;
      var ssoDuoSecret = null;
      var ssoDuoHost = null;
      var ssoDuoMode = null;
      var ssoClientCache = this.getSsoClientCacheSelect();

      if (this.$('.verify-pass input').is(':visible') &&
          password && password !== verifyPassword) {
        this.setAlert('danger', 'Passwords do not match.', '.verify-pass');
        return;
      }

      if (auditing !== 'all') {
        auditing = null;
      }

      if (monitoring === 'none') {
        monitoring = null;
      }

      if (monitoring !== 'influxdb') {
        influxdbUriKey = null;
      }

      if (sso) {
        if (sso.indexOf('duo') !== -1) {
          ssoDuoToken = this.$('.sso-token input').val();
          ssoDuoSecret = this.$('.sso-secret input').val();
          ssoDuoHost = this.$('.sso-host input').val();
          ssoDuoMode = this.$('.sso-duo-mode select').val();
        }

        if (sso.indexOf('saml') !== -1) {
          ssoSamlUrl = this.$('.sso-saml-url input').val();
          ssoSamlIssuerUrl = this.$('.sso-saml-issuer-url input').val();
          ssoSamlCert = this.$('.sso-saml-cert textarea').val();
        }

        if (sso.indexOf('okta') !== -1) {
          ssoOktaToken = this.$('.sso-okta-token input').val();
          ssoOktaPush = this.getSsoOktaPushSelect();
        }

        if (sso.indexOf('onelogin') !== -1) {
          ssoOneLoginId = this.$('.sso-onelogin-id input').val();
          ssoOneLoginSecret = this.$('.sso-onelogin-secret input').val();
        }

        if (sso.indexOf('google') !== -1) {
          ssoMatch = this.$('.sso-match-google input').val().split(',');

          for (i = 0; i < ssoMatch.length; i++) {
            ssoMatch[i] = ssoMatch[i].replace(/^\s\s*/,
              '').replace(/\s\s*$/, '');
          }
        }

        if (sso.indexOf('slack') !== -1) {
          ssoMatch = this.$('.sso-match-slack input').val().split(',');
          if (ssoMatch.length) {
            ssoMatch = [ssoMatch[0]];
          }

          for (i = 0; i < ssoMatch.length; i++) {
            ssoMatch[i] = ssoMatch[i].replace(/^\s\s*/,
              '').replace(/\s\s*$/, '');
          }
        }

        if (sso.indexOf('radius') !== -1) {
          ssoRadiusHost = this.$('.sso-radius-host input').val();
          ssoRadiusSecret = this.$('.sso-radius-secret input').val();
        }

        ssoOrg = this.$('.sso-org select').val();
      }

      var modelAttr = {
        username: username,
        auditing: auditing,
        monitoring: monitoring,
        influxdb_uri: influxdbUriKey,
        email_from: emailFrom,
        email_server: emailServer,
        email_username: emailUsername,
        pin_mode: pinMode,
        sso: sso,
        sso_match: ssoMatch,
        sso_duo_token: ssoDuoToken,
        sso_duo_secret: ssoDuoSecret,
        sso_duo_host: ssoDuoHost,
        sso_duo_mode: ssoDuoMode,
        sso_yubico_client: ssoYubicoClient,
        sso_yubico_secret: ssoYubicoSecret,
        sso_org: ssoOrg,
        sso_saml_url: ssoSamlUrl,
        sso_saml_issuer_url: ssoSamlIssuerUrl,
        sso_saml_cert: ssoSamlCert,
        sso_okta_token: ssoOktaToken,
        sso_okta_push: ssoOktaPush,
        sso_onelogin_id: ssoOneLoginId,
        sso_onelogin_secret: ssoOneLoginSecret,
        sso_radius_host: ssoRadiusHost,
        sso_radius_secret: ssoRadiusSecret,
        sso_client_cache: ssoClientCache,
        public_address: publicAddress,
        public_address6: publicAddress6,
        routed_subnet6: routedSubnet6,
        reverse_proxy: reverseProxy,
        theme: theme,
        server_port: serverPort,
        server_cert: serverCert,
        server_key: serverKey,
        acme_domain: acmeDomain,
        cloud_provider: cloudProvider,
        route53_region: route53Region,
        route53_zone: route53Zone,
        us_east_1_access_key: usEast1AccessKey,
        us_east_1_secret_key: usEast1SecretKey,
        us_east_2_access_key: usEast2AccessKey,
        us_east_2_secret_key: usEast2SecretKey,
        us_west_1_access_key: usWest1AccessKey,
        us_west_1_secret_key: usWest1SecretKey,
        us_west_2_access_key: usWest2AccessKey,
        us_west_2_secret_key: usWest2SecretKey,
        us_gov_west_1_access_key: usGovWest1AccessKey,
        us_gov_west_1_secret_key: usGovWest1SecretKey,
        eu_west_1_access_key: euWest1AccessKey,
        eu_west_1_secret_key: euWest1SecretKey,
        eu_west_2_access_key: euWest2AccessKey,
        eu_west_2_secret_key: euWest2SecretKey,
        eu_central_1_access_key: euCentral1AccessKey,
        eu_central_1_secret_key: euCentral1SecretKey,
        ca_central_1_access_key: caCentral1AccessKey,
        ca_central_1_secret_key: caCentral1SecretKey,
        ap_northeast_1_access_key: apNortheast1AccessKey,
        ap_northeast_1_secret_key: apNortheast1SecretKey,
        ap_northeast_2_access_key: apNortheast2AccessKey,
        ap_northeast_2_secret_key: apNortheast2SecretKey,
        ap_southeast_1_access_key: apSoutheast1AccessKey,
        ap_southeast_1_secret_key: apSoutheast1SecretKey,
        ap_southeast_2_access_key: apSoutheast2AccessKey,
        ap_southeast_2_secret_key: apSoutheast2SecretKey,
        ap_south_1_access_key: apSouth1AccessKey,
        ap_south_1_secret_key: apSouth1SecretKey,
        sa_east_1_access_key: saEast1AccessKey,
        sa_east_1_secret_key: saEast1SecretKey
      };

      if (!username) {
        this.setAlert('danger', 'Username can not be empty.', '.username');
        return;
      }
      if (password) {
        modelAttr.password = password;
      }
      if (emailPassword !== '********************') {
        modelAttr.email_password = emailPassword;
      }

      this.setLoading('Saving settings...');
      this.model.clear();
      this.model.save(modelAttr, {
        success: function() {
          window.sso = sso;
          this.close(true);

          if (serverPort !== this.curServerPort) {
            setTimeout(function() {
              window.location = window.location.protocol + '//' +
                window.location.hostname +
                (serverPort === '443' || !serverPort ? '' : ':' +
                  serverPort) +
                window.location.pathname;
            }, 10000);
          } else if (acmeDomain !== this.curAcmeDomain) {
            setTimeout(function() {
              window.location.reload();
            }, 10000);
          }
        }.bind(this),
        error: function(model, response) {
          this.clearLoading();
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger',
              'Failed to save settings, server error occurred.');
          }
        }.bind(this)
      });
    },
    onClickInput: function(evt) {
      this.$(evt.target).select();
    },
    onRemove: function() {
      ModalSettingsView.__super__.onRemove.call(this);
      if (!this.triggerApplied) {
        if (window.subActive && window.theme === 'dark') {
          $('body').addClass('dark');
        }
        else {
          $('body').removeClass('dark');
        }
      }
    }
  });

  return ModalSettingsView;
});

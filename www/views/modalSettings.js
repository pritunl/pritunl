define([
  'jquery',
  'underscore',
  'backbone',
  'collections/org',
  'views/modal',
  'text!templates/modalSettings.html'
], function($, _, Backbone, OrgCollection, ModalView, modalSettingsTemplate) {
  'use strict';
  var ModalSettingsView = ModalView.extend({
    className: 'settings-modal',
    template: _.template(modalSettingsTemplate),
    title: 'Settings',
    okText: 'Save',
    enterOk: false,
    events: function() {
      return _.extend({
        'click .sso-mode select': 'onSsoMode',
        'change .pass input': 'onPassChange',
        'keyup .pass input': 'onPassEvent',
        'paste .pass input': 'onPassEvent',
        'input .pass input': 'onPassEvent',
        'propertychange .pass input': 'onPassEvent',
        'change .theme select': 'onThemeChange',
        'click .generate-new-api-key': 'onGenerateNewKey',
        'click .api-token input, .api-secret input': 'onClickInput'
      }, ModalSettingsView.__super__.events);
    },
    initialize: function(options) {
      this.orgs = new OrgCollection();
      this.initial = options.initial;
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
      this.setLoading('Loading organizations...');
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
    },
    update: function() {
      this.$('.api-token input').val(this.model.get('token'));
      this.$('.api-secret input').val(this.model.get('secret'));
    },
    getSsoMode: function() {
      return this.$('.sso-mode select').val();
    },
    setSsoMode: function(mode) {
      if (!mode) {
        this.$('.sso-match').slideUp(window.slideTime);
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-admin').slideUp(window.slideTime);
        this.$('.sso-org').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-onelogin-key').slideUp(window.slideTime);
        return;
      } else {
        this.$('.sso-org').slideDown(window.slideTime);
      }

      if (mode === 'saml') {
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-admin').slideUp(window.slideTime);
        this.$('.sso-match').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-onelogin-key').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
      } else if (mode === 'saml_duo') {
        this.$('.sso-match').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-onelogin-key').slideUp(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-admin').slideDown(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
      } else if (mode === 'saml_okta') {
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-admin').slideUp(window.slideTime);
        this.$('.sso-match').slideUp(window.slideTime);
        this.$('.sso-onelogin-key').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-okta-token').slideDown(window.slideTime);
      } else if (mode === 'saml_onelogin') {
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-admin').slideUp(window.slideTime);
        this.$('.sso-match').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-onelogin-key').slideDown(window.slideTime);
      } else if (mode === 'saml_onelogin_duo') {
        this.$('.sso-match').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-admin').slideDown(window.slideTime);
        this.$('.sso-saml-url').slideDown(window.slideTime);
        this.$('.sso-saml-issuer-url').slideDown(window.slideTime);
        this.$('.sso-saml-cert').slideDown(window.slideTime);
        this.$('.sso-onelogin-key').slideDown(window.slideTime);
      } else if (mode === 'google') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-token').slideUp(window.slideTime);
        this.$('.sso-secret').slideUp(window.slideTime);
        this.$('.sso-host').slideUp(window.slideTime);
        this.$('.sso-admin').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-onelogin-key').slideUp(window.slideTime);
        this.$('.sso-match').slideDown(window.slideTime);
      } else if (mode === 'google_duo') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-onelogin-key').slideUp(window.slideTime);
        this.$('.sso-match').slideDown(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-admin').slideDown(window.slideTime);
      } else if (mode === 'duo') {
        this.$('.sso-saml-url').slideUp(window.slideTime);
        this.$('.sso-saml-issuer-url').slideUp(window.slideTime);
        this.$('.sso-saml-cert').slideUp(window.slideTime);
        this.$('.sso-okta-token').slideUp(window.slideTime);
        this.$('.sso-onelogin-key').slideUp(window.slideTime);
        this.$('.sso-match').slideUp(window.slideTime);
        this.$('.sso-token').slideDown(window.slideTime);
        this.$('.sso-secret').slideDown(window.slideTime);
        this.$('.sso-host').slideDown(window.slideTime);
        this.$('.sso-admin').slideDown(window.slideTime);
      }
    },
    onSsoMode: function() {
      this.setSsoMode(this.getSsoMode());
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
    onGenerateNewKey: function() {
      this.setLoading('Generating new api key...');
      this.model.clear();
      this.model.save({
        token: true,
        secret: true
      }, {
        success: function() {
          this.clearLoading();
          this.setAlert('success', 'Successfully generated a new api key.');
          this.update();
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to generated a new api key, server error occurred.');
        }.bind(this)
      });
    },
    onOk: function() {
      var username = this.$('.username input').val();
      var password = this.$('.pass input').val();
      var verifyPassword = this.$('.verify-pass input').val();
      var publicAddress = this.$('.public-address input').val();
      var publicAddress6 = this.$('.public-address6 input').val();
      var routedSubnet6 = this.$('.routed-subnet6 input').val();
      var theme = this.$('.theme:visible select').val();
      var emailFrom = this.$('.email-from input').val();
      var emailServer = this.$('.email-server input').val();
      var emailUsername = this.$('.email-username input').val();
      var emailPassword = this.$('.email-password input').val();
      var serverCert = this.$('.server-cert textarea').val();
      var serverKey = this.$('.server-key textarea').val();

      var sso = this.getSsoMode();
      var ssoMatch = null;
      var ssoToken = null;
      var ssoSecret = null;
      var ssoHost = null;
      var ssoAdmin = null;
      var ssoOrg = null;
      var ssoSamlUrl = null;
      var ssoSamlIssuerUrl = null;
      var ssoSamlCert = null;
      var ssoOktaToken = null;
      var ssoOneLoginKey = null;

      if (this.$('.verify-pass input').is(':visible') &&
          password && password !== verifyPassword) {
        this.setAlert('danger', 'Passwords do not match.', '.verify-pass');
        return;
      }

      if (sso) {
        if (sso === 'duo' || sso === 'saml_duo' || sso === 'google_duo' ||
            sso === 'saml_onelogin_duo') {
          ssoToken = this.$('.sso-token input').val();
          ssoSecret = this.$('.sso-secret input').val();
          ssoHost = this.$('.sso-host input').val();
          ssoAdmin = this.$('.sso-admin input').val();
        }

        if (sso === 'saml' || sso === 'saml_duo' || sso === 'saml_okta' ||
            sso === 'saml_onelogin' || sso === 'saml_onelogin_duo') {
          ssoSamlUrl = this.$('.sso-saml-url input').val();
          ssoSamlIssuerUrl = this.$('.sso-saml-issuer-url input').val();
          ssoSamlCert = this.$('.sso-saml-cert textarea').val();
        }

        if (sso === 'saml_okta') {
          ssoOktaToken = this.$('.sso-okta-token input').val();
        }

        if (sso === 'saml_onelogin' || sso === 'saml_onelogin_duo') {
          ssoOneLoginKey = this.$('.sso-onelogin-key input').val();
        }

        if (sso === 'google' || sso === 'google_duo') {
          ssoMatch = this.$('.sso-match input').val().split(',');

          for (var i = 0; i < ssoMatch.length; i++) {
            ssoMatch[i] = ssoMatch[i].replace(/^\s\s*/,
              '').replace(/\s\s*$/, '');
          }
        }

        ssoOrg = this.$('.sso-org select').val();
      }

      var modelAttr = {
        username: username,
        email_from: emailFrom,
        email_server: emailServer,
        email_username: emailUsername,
        sso: sso,
        sso_match: ssoMatch,
        sso_token: ssoToken,
        sso_secret: ssoSecret,
        sso_host: ssoHost,
        sso_admin: ssoAdmin,
        sso_org: ssoOrg,
        sso_saml_url: ssoSamlUrl,
        sso_saml_issuer_url: ssoSamlIssuerUrl,
        sso_saml_cert: ssoSamlCert,
        sso_okta_token: ssoOktaToken,
        sso_onelogin_key: ssoOneLoginKey,
        public_address: publicAddress,
        public_address6: publicAddress6,
        routed_subnet6: routedSubnet6,
        theme: theme,
        server_cert: serverCert,
        server_key: serverKey
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

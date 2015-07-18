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
    events: function() {
      return _.extend({
        'click .sso-match .selector': 'onSsoSelect',
        'change .pass input': 'onPassChange',
        'keyup .pass input': 'onPassEvent',
        'paste .pass input': 'onPassEvent',
        'input .pass input': 'onPassEvent',
        'propertychange .pass input': 'onPassEvent',
        'change .theme select': 'onThemeChange',
        'click .generate-new-api-key': 'onGenerateNewKey',
        'click .right input': 'onClickInput'
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
    getSsoSelect: function() {
      return this.$('.sso-match .selector').hasClass('selected');
    },
    setSsoSelect: function(state) {
      if (state) {
        this.$('.sso-match .selector').addClass('selected');
        this.$('.sso-match .selector-inner').show();
        this.$('.sso-match input').removeAttr('disabled');
        this.$('.sso-org select').removeAttr('disabled');
      }
      else {
        this.$('.sso-match .selector').removeClass('selected');
        this.$('.sso-match .selector-inner').hide();
        this.$('.sso-match input').attr('disabled', 'disabled');
        this.$('.sso-org select').attr('disabled', 'disabled');
      }
    },
    onSsoSelect: function() {
      this.setSsoSelect(!this.getSsoSelect());
    },
    onThemeChange: function() {
      if (this.$('.theme select').val() === 'dark') {
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
      var publicAddress = this.$('.public-address input').val();
      var theme = this.$('.theme select').val();
      var emailFrom = this.$('.email-from input').val();
      var emailServer = this.$('.email-server input').val();
      var emailUsername = this.$('.email-username input').val();
      var emailPassword = this.$('.email-password input').val();

      var sso = this.getSsoSelect();
      var ssoMatch;
      var ssoOrg;

      if (sso) {
        ssoMatch = this.$('.sso-match input').val().split(',');

        for (var i = 0; i < ssoMatch.length; i++) {
          ssoMatch[i] = ssoMatch[i].replace(/^\s\s*/,
            '').replace(/\s\s*$/, '');
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
        sso_org: ssoOrg,
        public_address: publicAddress,
        theme: theme
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
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to save settings, server error occurred.');
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

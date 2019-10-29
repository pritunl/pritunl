define([
  'jquery',
  'underscore',
  'backbone',
  'models/key',
  'collections/userAudit',
  'views/alert',
  'views/modalRenameUser',
  'views/modalKeyLink',
  'views/modalAuditUser',
  'views/modalOtpAuth',
  'views/userServersList',
  'text!templates/usersListItem.html'
], function($, _, Backbone, KeyModel, UserAuditCollection, AlertView,
    ModalRenameUserView, ModalKeyLinkView, ModalAuditUserView,
    ModalOtpAuthView, UserServersListView, usersListItemTemplate) {
  'use strict';
  var UsersListItemView = Backbone.View.extend({
    template: _.template(usersListItemTemplate),
    events: {
      'click .selector': 'onSelect',
      'click .user-name': 'onRename',
      'click .get-key-link': 'onGetKeyLink',
      'click .audit-user': 'onAuditUser',
      'click .get-otp-auth': 'onGetOtpAuth',
      'click .disable-user': 'onDisableUser',
      'click .enable-user': 'onEnableUser',
      'click .toggle-servers': 'onToggleServers'
    },
    initialize: function() {
      this.serverList = new UserServersListView({
        models: this.model.get('servers')
      });
    },
    _getDownloadTooltip: function() {
      if (this.model.get('has_key')) {
        return 'Click to download profile';
      }
      else {
        return 'Organization must be attached to server to download profile';
      }
    },
    _getKeyLink: function() {
      if (!this.model.get('has_key')) {
        return '';
      }
      else if (window.demo) {
        return '../key/demo.tar';
      }
      else {
        return '/key/' + this.model.get('organization') + '/' +
          this.model.get('id') + '.tar';
      }
    },
    _getKeyLinkTooltip: function() {
      if (this.model.get('has_key')) {
        return 'Get temporary profile links';
      }
      else {
        return 'Organization must be attached to server to get ' +
          'temporary profile links';
      }
    },
    render: function() {
      this.$el.html(this.template(_.extend(
        {
          'download_tooltip': this._getDownloadTooltip(),
          'key_link': this._getKeyLink(),
          'key_link_tooltip': this._getKeyLinkTooltip()
        }, this.model.toJSON())));
      this.$('[data-toggle="tooltip"]').tooltip();
      this.$el.append(this.serverList.render().el);
      if (this.model.get('disabled')) {
        this.$('.disable-user').hide();
      }
      else {
        this.$('.enable-user').hide();
      }
      return this;
    },
    update: function() {
      var email = this.model.get('email');
      var name = this.model.get('name');
      var i;

      if (name.length > 40) {
        name = name.substr(0, 40);
        if (name.substr(39, 1) === '.') {
          name += '..';
        } else {
          name += '...';
        }
      }

      this.$('.user-name').text(name);
      if (email && this.model.get('gravatar')) {
        this.$('.name-gravatar').attr('src', '//www.gravatar.com/avatar/' +
          window.md5(email) + '?r=x&s=52&d=404');
      }
      else {
        this.$('.name-gravatar').hide();
        this.$('.name-gravatar').attr('src', '');
        this.$('.name-icon').show();
      }
      if (this.model.get('disabled')) {
        this.$('.user .status-icon').removeClass('online');
        this.$('.user .status-icon').removeClass('offline');
        this.$('.user .status-icon').addClass('disabled');
        this.$('.user .status-text').text('Disabled');
        this.$('.disable-user').hide();
        this.$('.enable-user').show();
      }
      else {
        if (this.model.get('status')) {
          this.$('.user .status-icon').removeClass('offline');
          this.$('.user .status-icon').addClass('online');
          this.$('.user .status-text').text('Online');
        }
        else {
          this.$('.user .status-icon').removeClass('online');
          this.$('.user .status-icon').addClass('offline');
          this.$('.user .status-text').text('Offline');
        }
        this.$('.user .status-icon').removeClass('disabled');
        this.$('.enable-user').hide();
        this.$('.disable-user').show();
      }

      this.$('.download-key').tooltip('destroy');
      this.$('.download-key').attr('title', this._getDownloadTooltip());
      this.$('.download-key').attr('data-original-title',
        this._getDownloadTooltip());
      this.$('.download-key').tooltip();

      this.$('.get-key-link').tooltip('destroy');
      this.$('.get-key-link').attr('title', this._getKeyLinkTooltip());
      this.$('.get-key-link').attr('data-original-title',
        this._getKeyLinkTooltip());
      this.$('.get-key-link').tooltip();

      if (!this.model.get('bypass_secondary') && this.model.get('otp_auth')) {
        this.$('.right-container').removeClass('no-otp-auth');
        this.$('.get-otp-auth').removeClass('no-otp-auth');
      }
      else {
        this.$('.right-container').addClass('no-otp-auth');
        this.$('.get-otp-auth').addClass('no-otp-auth');
      }

      if (this.model.get('audit')) {
        this.$('.audit-user').removeClass('no-audit-user');
      }
      else {
        this.$('.audit-user').addClass('no-audit-user');
      }

      var dnsMapping = this.model.get('dns_mapping');
      if (dnsMapping) {
        this.$('.user-dns-name .name').text(dnsMapping);
        this.$('.user-dns-name').show();
      } else {
        this.$('.user-dns-name').hide();
        this.$('.user-dns-name .name').text('');
      }

      var networkLinks = this.model.get('network_links');
      this.$('.user-network-link').empty();
      if (networkLinks) {
        for (i = 0; i < networkLinks.length; i++) {
          this.$('.user-network-link').append(
            '<span class="fa fa-circle-o">').append(
            $('<span class="title link"></span>').text(networkLinks[i]));
        }
      }

      var groups = this.model.get('groups');
      this.$('.user-groups').empty();
      if (groups) {
        for (i = 0; i < groups.length; i++) {
          this.$('.user-groups').append(
            '<span class="fa fa-compass">').append(
            $('<span class="title group"></span>').text(groups[i]));
        }
      }

      if (this.model.get('bypass_secondary')) {
        this.$('.saml-logo').hide();
        this.$('.azure-logo').hide();
        this.$('.authzero-logo').hide();
        this.$('.google-logo').hide();
        this.$('.slack-logo').hide();
        this.$('.duo-logo').hide();
        this.$('.radius-logo').hide();
        this.$('.plugin-logo').hide();
      } else {
        var sso = this.model.get('sso') || '';
        var auth_type = this.model.get('auth_type');
        if (sso.indexOf('saml') !== -1 &&
            auth_type.indexOf('saml') !== -1) {
          this.$('.saml-logo').show();
        } else {
          this.$('.saml-logo').hide();
        }

        if (sso.indexOf('azure') !== -1 &&
          auth_type.indexOf('azure') !== -1) {
          this.$('.azure-logo').show();
        } else {
          this.$('.azure-logo').hide();
        }

        if (sso.indexOf('authzero') !== -1 &&
          auth_type.indexOf('authzero') !== -1) {
          this.$('.authzero-logo').show();
        } else {
          this.$('.authzero-logo').hide();
        }

        if (sso.indexOf('google') !== -1 &&
          auth_type.indexOf('google') !== -1) {
          this.$('.google-logo').show();
        } else {
          this.$('.google-logo').hide();
        }

        if (sso.indexOf('slack') !== -1 &&
          auth_type.indexOf('slack') !== -1) {
          this.$('.slack-logo').show();
        } else {
          this.$('.slack-logo').hide();
        }

        if (sso.indexOf('duo') !== -1 &&
          auth_type.indexOf('duo') !== -1) {
          this.$('.duo-logo').show();
        } else {
          this.$('.duo-logo').hide();
        }

        if ((sso.indexOf('yubico') !== -1 &&
          auth_type.indexOf('yubico') !== -1) || auth_type === 'yubico') {
          this.$('.yubico-logo').show();
        } else {
          this.$('.yubico-logo').hide();
        }

        if (sso.indexOf('okta') !== -1 &&
          auth_type.indexOf('okta') !== -1) {
          this.$('.okta-logo').show();
        } else {
          this.$('.okta-logo').hide();
        }

        if (sso.indexOf('onelogin') !== -1 &&
          auth_type.indexOf('onelogin') !== -1) {
          this.$('.onelogin-logo').show();
        } else {
          this.$('.onelogin-logo').hide();
        }

        if (sso === 'radius' && auth_type === 'radius') {
          this.$('.radius-logo').show();
        } else {
          this.$('.radius-logo').hide();
        }

        if (auth_type === 'plugin') {
          this.$('.plugin-logo').show();
        } else {
          this.$('.plugin-logo').hide();
        }
      }

      this.serverList.update(this.model.get('servers'));
    },
    getSelect: function() {
      return this.$('.selector').hasClass('selected');
    },
    setSelect: function(state, shiftKey) {
      if (state === this.getSelect()) {
        return;
      }

      if (state) {
        this.$('.selector').addClass('selected');
        this.$('.selector-inner').show();
      }
      else {
        this.$('.selector').removeClass('selected');
        this.$('.selector-inner').hide();
      }
      this.trigger('select', this, shiftKey);
    },
    onSelect: function(evt) {
      this.setSelect(!this.getSelect(), evt.shiftKey);
    },
    onRename: function() {
      var modal = new ModalRenameUserView({
        model: this.model.clone()
      });
      this.addView(modal);
    },
    onGetKeyLink: function() {
      if (!this.model.get('has_key')) {
        return;
      }
      var modal = new ModalKeyLinkView({
        model: new KeyModel({
          'organization': this.model.get('organization'),
          'user': this.model.get('id'),
          'otp_auth': this.model.get('otp_auth')
        })
      });
      this.addView(modal);
    },
    onAuditUser: function() {
      var modal = new ModalAuditUserView({
        collection: new UserAuditCollection({
          'user': this.model
        })
      });
      this.addView(modal);
    },
    onGetOtpAuth: function() {
      var modal = new ModalOtpAuthView({
        model: this.model
      });
      this.addView(modal);
    },
    onDisableUser: function() {
      if (this.$('.disable-user').hasClass('disabled')) {
        return;
      }
      this.$('.disable-user').addClass('disabled');
      this.model.save({
        disabled: true
      }, {
        success: function() {
          this.$('.disable-user').removeClass('disabled');
        }.bind(this),
        error: function(model, response) {
          var message;
          if (response.responseJSON) {
            message = response.responseJSON.error_msg;
          }
          else {
            message = 'Failed to disable user, server error occurred.';
          }

          var alertView = new AlertView({
            type: 'danger',
            message: message,
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.$('.disable-user').removeClass('disabled');
        }.bind(this)
      });
    },
    onEnableUser: function() {
      if (this.$('.enable-user').hasClass('disabled')) {
        return;
      }
      this.$('.enable-user').addClass('disabled');
      this.model.save({
        disabled: false
      }, {
        success: function() {
          this.$('.enable-user').removeClass('disabled');
        }.bind(this),
        error: function(model, response) {
          var message;
          if (response.responseJSON) {
            message = response.responseJSON.error_msg;
          }
          else {
            message = 'Failed to enable user, server error occurred.';
          }

          var alertView = new AlertView({
            type: 'danger',
            message: message,
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.$('.enable-user').removeClass('disabled');
        }.bind(this)
      });
    },
    onToggleServers: function() {
      var tooltipText;
      if (this.$('.toggle-servers').hasClass('glyphicon-chevron-down')) {
        this.$('.toggle-servers').removeClass('glyphicon-chevron-down');
        this.$('.toggle-servers').addClass('glyphicon-chevron-up');
        this.$('.user-servers').slideDown(window.slideTime);
        tooltipText = 'Hide additional user information';
      }
      else {
        this.$('.toggle-servers').removeClass('glyphicon-chevron-up');
        this.$('.toggle-servers').addClass('glyphicon-chevron-down');
        this.$('.user-servers').slideUp(window.slideTime);
        tooltipText = 'Show additional user information';
      }

      this.$('.toggle-servers').tooltip('destroy');
      this.$('.toggle-servers').attr('title', tooltipText);
      this.$('.toggle-servers').attr('data-original-title', tooltipText);
      this.$('.toggle-servers').tooltip();
    }
  });

  return UsersListItemView;
});

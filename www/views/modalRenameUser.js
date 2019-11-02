define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalRenameUser.html'
], function($, _, Backbone, ModalView, modalRenameUserTemplate) {
  'use strict';
  var ModalRenameUserView = ModalView.extend({
    className: 'rename-user-modal',
    template: _.template(modalRenameUserTemplate),
    title: 'Modify User',
    okText: 'Save',
    enterOk: false,
    hasAdvanced: true,
    events: function() {
      return _.extend({
        'click .auth-type select': 'onAuthType',
        'change .auth-type select': 'onAuthType',
        'click .bypass-secondary-toggle': 'onBypassSecondarySelect',
        'click .client-to-client-toggle': 'onClientToClientSelect'
      }, ModalRenameUserView.__super__.events);
    },
    body: function() {
      return this.template(_.extend({
        portForwardingFormatted: this.model.portForwardingFormatted()
      }, this.model.toJSON()));
    },
    postRender: function() {
      this.$('.groups input').select2({
        tags: [],
        tokenSeparators: [',', ' '],
        width: '200px'
      });
    },
    getPortForwarding: function() {
      var item;
      var protocol;
      var port;
      var dport;
      var ports = [];

      var data = this.$('.port-forwarding input').val();
      data = data.split(',');

      for (var i = 0; i < data.length; i++) {
        protocol = null;
        port = null;
        dport = null;

        item = data[i];
        item = item.split('/');

        if (item.length === 2) {
          protocol = item[1];
        }
        item = item[0].split(':');

        if (item.length === 2) {
          dport = item[1];
        }
        port = item[0];

        if (!port) {
          continue;
        }

        ports.push({
          protocol: protocol,
          port: port,
          dport: dport
        });
      }

      return ports;
    },
    getBypassSecondarySelect: function() {
      return this.$('.bypass-secondary-toggle .selector').hasClass('selected');
    },
    setBypassSecondarySelect: function(state) {
      if (state) {
        this.$('.bypass-secondary-toggle .selector').addClass('selected');
        this.$('.bypass-secondary-toggle .selector-inner').show();
      }
      else {
        this.$('.bypass-secondary-toggle .selector').removeClass('selected');
        this.$('.bypass-secondary-toggle .selector-inner').hide();
      }
    },
    onBypassSecondarySelect: function() {
      this.setBypassSecondarySelect(!this.getBypassSecondarySelect());
    },
    getClientToClientSelect: function() {
      return this.$('.client-to-client-toggle .selector').hasClass('selected');
    },
    setClientToClientSelect: function(state) {
      if (state) {
        this.$('.client-to-client-toggle .selector').addClass('selected');
        this.$('.client-to-client-toggle .selector-inner').show();
      }
      else {
        this.$('.client-to-client-toggle .selector').removeClass('selected');
        this.$('.client-to-client-toggle .selector-inner').hide();
      }
    },
    onClientToClientSelect: function() {
      this.setClientToClientSelect(!this.getClientToClientSelect());
    },
    onAuthType: function() {
      var authType = this.$('.auth-type select').val();

      if (authType === 'yubico') {
        this.$('.yubikey-id').slideDown(window.slideTime);
      } else {
        this.$('.yubikey-id').slideUp(window.slideTime);
      }
    },
    getGroups: function() {
      var groups = [];
      var groupsData = this.$('.groups input').select2('data');

      if (groupsData.length) {
        for (var i = 0; i < groupsData.length; i++) {
          groups.push(groupsData[i].text);
        }
      } else {
        var groupsVal = this.$('.groups input').val();
        if (groupsVal && groupsVal !== 'Enter groups') {
          groups = [groupsVal];
        }
      }

      return groups;
    },
    onOk: function() {
      var i;
      var name = this.$('.name input').val();
      var email = this.$('.email input').val();
      var emailReg = /^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;
      var dnsSuffix = this.$('.dns-suffix input').val();
      var pin = this.$('.pin input').val() || null;
      var bypassSecondary = this.getBypassSecondarySelect();
      var clientToClient = this.getClientToClientSelect();
      var portForwarding = this.getPortForwarding();
      var groups = this.getGroups();
      var authType = this.$('.auth-type select').val();
      var yubicoId = this.$('.yubikey-id input').val();

      if (pin === '******') {
        pin = true;
      }

      var networkLink;
      var networkLinks = [];
      var networkLinksTemp = this.$('.network-links input').val().split(',');
      for (i = 0; i < networkLinksTemp.length; i++) {
        networkLink = $.trim(networkLinksTemp[i]);
        if (networkLink) {
          networkLinks.push(networkLink);
        }
      }

      var dnsServer;
      var dnsServers = [];
      var dnsServersTemp = this.$('.dns-servers input').val().split(',');
      for (i = 0; i < dnsServersTemp.length; i++) {
        dnsServer = $.trim(dnsServersTemp[i]);
        if (dnsServer) {
          dnsServers.push(dnsServer);
        }
      }

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.',
          '.form-group.name');
        return;
      }
      if (!email) {
        email = null;
      }
      else if (!emailReg.test(email)) {
        this.setAlert('danger', 'Email is not valid.', '.form-group.email');
        return;
      }

      this.setLoading('Modifying user...');
      this.model.save({
        name: name,
        groups: groups,
        email: email,
        pin: pin,
        network_links: networkLinks,
        bypass_secondary: bypassSecondary,
        client_to_client: clientToClient,
        dns_servers: dnsServers,
        dns_suffix: dnsSuffix,
        port_forwarding: portForwarding,
        auth_type: authType,
        yubico_id: yubicoId
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function(model, response) {
          this.clearLoading();
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger', this.errorMsg);
          }
        }.bind(this)
      });
    }
  });

  return ModalRenameUserView;
});

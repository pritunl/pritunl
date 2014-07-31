define([
  'jquery',
  'underscore',
  'backbone',
  'select',
  'views/modal',
  'text!templates/modalServerSettings.html'
], function($, _, Backbone, Select, ModalView, modalServerSettingsTemplate) {
  'use strict';
  var ModalServerSettingsView = ModalView.extend({
    className: 'server-settings-modal',
    template: _.template(modalServerSettingsTemplate),
    title: 'Server Settings',
    okText: 'Save',
    loadingMsg: 'Saving server...',
    errorMsg: 'Failed to saving server, server error occurred.',
    events: function() {
      return _.extend({
        'change .server-mode select': 'onServerMode',
        'change .dh-param-bits select': 'onDhParamBits',
        'click .otp-auth-toggle': 'onOtpAuthSelect',
        'click .debug-toggle': 'onDebugSelect'
      }, ModalServerSettingsView.__super__.events);
    },
    initialize: function(options) {
      this.localNetworks = options.localNetworks;
      ModalServerSettingsView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    postRender: function() {
      if (this.model.get('mode') === 'local_traffic') {
        this.$('.otp-auth-toggle').appendTo('.left');
      }
      this.$('.local-network input').select2({
        tags: this.localNetworks,
        tokenSeparators: [',', ' '],
        placeholder: 'Select Local Networks',
        formatNoMatches: function() {
          return 'Enter Network Address';
        },
        width: '200px'
      });
      this.$('.local-network input').select2(
        'val', this.model.get('local_networks'));
      this.$('.network .label').tooltip();
      this.updateMaxHosts();
    },
    getServerMode: function() {
      return this.$('.server-mode select').val();
    },
    setServerMode: function(mode) {
      if (mode === 'local_traffic') {
        if (!this.$('.otp-auth-toggle').parent().hasClass('left')) {
          this.$('.local-network').slideDown(250);
          this.$('.otp-auth-toggle').slideUp(250, function() {
            this.$('.otp-auth-toggle').appendTo('.left');
            this.$('.otp-auth-toggle').show();
          }.bind(this));
        }
      }
      else {
        if (!this.$('.otp-auth-toggle').parent().hasClass('right')) {
          this.$('.local-network').slideUp(250);
          this.$('.otp-auth-toggle').slideUp(250, function() {
            this.$('.otp-auth-toggle').appendTo('.right');
            this.$('.otp-auth-toggle').show();
          }.bind(this));
        }
      }
    },
    onServerMode: function() {
      this.setServerMode(this.getServerMode());
    },
    onDhParamBits: function(evt) {
      var val = $(evt.target).val();
      if (val > 2048) {
        this.setAlert('danger', 'Using dh parameters larger then 2048 can ' +
          'take several hours to generate.', '.dh-param-bits');
      }
      else if (val > 1536) {
        this.setAlert('warning', 'Using dh parameters larger then 1536 can ' +
          'take several minutes to generate.', '.dh-param-bits');
      }
      else {
        this.clearAlert();
      }
    },
    getOtpAuthSelect: function() {
      return this.$('.otp-auth-toggle .selector').hasClass('selected');
    },
    setOtpAuthSelect: function(state) {
      if (state) {
        this.$('.otp-auth-toggle .selector').addClass('selected');
        this.$('.otp-auth-toggle .selector-inner').show();
      }
      else {
        this.$('.otp-auth-toggle .selector').removeClass('selected');
        this.$('.otp-auth-toggle .selector-inner').hide();
      }
    },
    onOtpAuthSelect: function() {
      this.setOtpAuthSelect(!this.getOtpAuthSelect());
    },
    getDebugSelect: function() {
      return this.$('.debug-toggle .selector').hasClass('selected');
    },
    setDebugSelect: function(state) {
      if (state) {
        this.$('.debug-toggle .selector').addClass('selected');
        this.$('.debug-toggle .selector-inner').show();
      }
      else {
        this.$('.debug-toggle .selector').removeClass('selected');
        this.$('.debug-toggle .selector-inner').hide();
      }
    },
    onDebugSelect: function() {
      this.setDebugSelect(!this.getDebugSelect());
    },
    onInputChange: function(evt) {
      if ($(evt.target).parent().hasClass('network')) {
        this.updateMaxHosts();
      }
    },
    updateMaxHosts: function() {
      var value = this.$('.network input').val().split('/');
      var maxHosts = {
        8: '4m',
        9: '2m',
        10: '1m',
        11: '524k',
        12: '262k',
        13: '131k',
        14: '65k',
        15: '32k',
        16: '16k',
        17: '8k',
        18: '4k',
        19: '2k',
        20: '1k',
        21: '512',
        22: '256',
        23: '128',
        24: '64',
      };
      if (value.length === 2) {
        var max = maxHosts[value[1]];
        if (max) {
          this.$('.network .label').text(max + ' Users');
          this.$('.network .label').show();
          return;
        }
      }
      this.$('.network .label').hide();
    },
    onOk: function() {
      var i;
      var name = this.$('.name input').val();
      var network = this.$('.network input').val();
      var iface = this.$('.interface input').val();
      var port = this.$('input.port').val();
      var protocol = this.$('select.protocol').val();
      var dhParamBits = parseInt(this.$('.dh-param-bits select').val(), 10);
      var mode = this.$('.server-mode select').val();
      var publicAddress = this.$('.public-address input').val();
      var dnsServers = [];
      var dnsServersTemp = this.$('.dns-servers input').val().split(',');
      for (i = 0; i < dnsServersTemp.length; i++) {
        dnsServersTemp[i] = $.trim(dnsServersTemp[i]);
        if (dnsServersTemp[i]) {
          dnsServers.push(dnsServersTemp[i]);
        }
      }
      var searchDomain = this.$('.search-domain input').val();
      var nodeHost = this.$('.node-host input').val().split(':');
      var nodePort = null;
      if (nodeHost.length > 1) {
        nodePort = parseInt(nodeHost[1], 10);
      }
      nodeHost = nodeHost[0];
      var nodeKey = this.$('.node-key input').val();
      var localNetworks = [];
      var debug = this.getDebugSelect();
      var otpAuth = this.getOtpAuthSelect();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }
      if (!network) {
        this.setAlert('danger', 'Network can not be empty.', '.network');
        return;
      }
      if (!iface) {
        this.setAlert('danger', 'Interface can not be empty.', '.interface');
        return;
      }
      if (!port) {
        this.setAlert('danger', 'Port can not be empty.', 'input.port');
        return;
      }
      if (!publicAddress) {
        this.setAlert('danger', 'Public IP can not be empty.',
          '.public-address');
        return;
      }
      if (this.getServerMode() === 'local_traffic') {
        localNetworks = this.$('.local-network input').select2('val');
        if (!localNetworks) {
          this.setAlert('danger', 'Local network can not be empty.',
            '.local-network');
          return;
        }
      }
      if (!searchDomain) {
        searchDomain = null;
      }

      var data = {
        'name': name,
        'type': this.model.get('type'),
        'network': network,
        'interface': iface,
        'port': port,
        'protocol': protocol,
        'dh_param_bits': dhParamBits,
        'mode': mode,
        'local_networks': localNetworks,
        'dns_servers': dnsServers,
        'search_domain': searchDomain,
        'public_address': publicAddress,
        'otp_auth': otpAuth,
        'debug': debug
      };

      if (this.model.get('type') === 'node_server') {
        if (!nodeHost) {
          this.setAlert('danger', 'Node host cannot be empty.', '.node-host');
          return;
        }
        if (!nodeKey) {
          this.setAlert('danger', 'Node api key cannot be empty.',
            '.node-key');
          return;
        }
        _.extend(data, {
          'node_host': nodeHost,
          'node_port': nodePort,
          'node_key': nodeKey
        });
      }

      this.setLoading(this.loadingMsg);
      this.model.save(data, {
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

  return ModalServerSettingsView;
});

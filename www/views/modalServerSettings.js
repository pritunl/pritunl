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
    hasAdvanced: true,
    events: function() {
      return _.extend({
        'change .dh-param-bits select': 'onDhParamBits',
        'change .network-mode select': 'onNetworkMode',
        'click .otp-auth-toggle': 'onOtpAuthSelect',
        'click .inter-client-toggle': 'onInterClientSelect',
        'click .dns-mapping-toggle': 'onDnsMappingSelect',
        'click .debug-toggle': 'onDebugSelect',
        'click .block-outside-dns-toggle': 'onBlockOutsideDnsSelect',
        'click .ipv6-toggle': 'onIpv6Select',
        'click .multi-device-toggle': 'onMultiDeviceSelect',
        'click .vxlan-toggle': 'onVxlanSelect',
        'click .ipv6-firewall-toggle': 'onIpv6FirewallSelect',
        'click .restrict-routes-toggle': 'onRestrictRoutesSelect',
        'change select.protocol, .cipher select, .network-mode select':
          'onInputChange',
        'click div.otp-auth-toggle': 'onInputChange'
      }, ModalServerSettingsView.__super__.events);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    postRender: function() {
      this.$('.groups input').select2({
        tags: [],
        tokenSeparators: [',', ' '],
        width: '200px'
      });
      this.$('.network .label').tooltip();
      this.updateMaxHosts();
    },
    onDhParamBits: function(evt) {
      var val = $(evt.target).val();
      if (val > 2048) {
        this.setAlert('danger', 'Using dh parameters larger then 2048 can ' +
          'take several hours to generate.', '.dh-param-bits');
      } else {
        this.clearAlert();
      }
    },
    getNetworkMode: function() {
      return this.$('.network-mode select').val();
    },
    setNetworkMode: function(mode) {
      if (mode === 'bridge') {
        this.$('.network-start').slideDown(window.slideTime);
        this.$('.network-end').slideDown(window.slideTime);
      }
      else {
        this.$('.network-start').slideUp(window.slideTime);
        this.$('.network-end').slideUp(window.slideTime);
      }
    },
    onNetworkMode: function() {
      this.setNetworkMode(this.getNetworkMode());
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
    getInterClientSelect: function() {
      return this.$('.inter-client-toggle .selector').hasClass('selected');
    },
    setInterClientSelect: function(state) {
      if (state) {
        this.$('.inter-client-toggle .selector').addClass('selected');
        this.$('.inter-client-toggle .selector-inner').show();
      }
      else {
        this.$('.inter-client-toggle .selector').removeClass('selected');
        this.$('.inter-client-toggle .selector-inner').hide();
      }
    },
    onInterClientSelect: function() {
      this.setInterClientSelect(!this.getInterClientSelect());
    },
    getDnsMappingSelect: function() {
      return this.$('.dns-mapping-toggle .selector').hasClass('selected');
    },
    setDnsMappingSelect: function(state) {
      if (state) {
        this.$('.dns-mapping-toggle .selector').addClass('selected');
        this.$('.dns-mapping-toggle .selector-inner').show();
      }
      else {
        this.$('.dns-mapping-toggle .selector').removeClass('selected');
        this.$('.dns-mapping-toggle .selector-inner').hide();
      }
    },
    onDnsMappingSelect: function() {
      this.setDnsMappingSelect(!this.getDnsMappingSelect());
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
    getBlockOutsideDnsSelect: function() {
      return this.$(
        '.block-outside-dns-toggle .selector').hasClass('selected');
    },
    setBlockOutsideDnsSelect: function(state) {
      if (state) {
        this.$('.block-outside-dns-toggle .selector').addClass('selected');
        this.$('.block-outside-dns-toggle .selector-inner').show();
      }
      else {
        this.$('.block-outside-dns-toggle .selector').removeClass('selected');
        this.$('.block-outside-dns-toggle .selector-inner').hide();
      }
    },
    onBlockOutsideDnsSelect: function() {
      this.setBlockOutsideDnsSelect(!this.getBlockOutsideDnsSelect());
    },
    getRestrictRoutesSelect: function() {
      return this.$('.restrict-routes-toggle .selector').hasClass('selected');
    },
    setRestrictRoutesSelect: function(state) {
      if (state) {
        this.$('.restrict-routes-toggle .selector').addClass('selected');
        this.$('.restrict-routes-toggle .selector-inner').show();
      }
      else {
        this.$('.restrict-routes-toggle .selector').removeClass('selected');
        this.$('.restrict-routes-toggle .selector-inner').hide();
      }
    },
    onRestrictRoutesSelect: function() {
      this.setRestrictRoutesSelect(!this.getRestrictRoutesSelect());
    },
    getIpv6Select: function() {
      return this.$('.ipv6-toggle .selector').hasClass('selected');
    },
    setIpv6Select: function(state) {
      var dnsServers = this.getDnsServers();

      if (state) {
        this.$('.ipv6-toggle .selector').addClass('selected');
        this.$('.ipv6-toggle .selector-inner').show();

        if (dnsServers.indexOf('8.8.4.4') !== -1 &&
            dnsServers.indexOf('2001:4860:4860::8844') === -1) {
          dnsServers.unshift('2001:4860:4860::8844');
        }
        if (dnsServers.indexOf('8.8.8.8') !== -1 &&
            dnsServers.indexOf('2001:4860:4860::8888') === -1) {
          dnsServers.unshift('2001:4860:4860::8888');
        }

        this.$('.ipv6-firewall-toggle').show();
      }
      else {
        this.$('.ipv6-toggle .selector').removeClass('selected');
        this.$('.ipv6-toggle .selector-inner').hide();

        var i = dnsServers.indexOf('2001:4860:4860::8888');
        if (i !== -1) {
          dnsServers.splice(i, 1);
        }
        i = dnsServers.indexOf('2001:4860:4860::8844');
        if (i !== -1) {
          dnsServers.splice(i, 1);
        }

        this.$('.ipv6-firewall-toggle').hide();
      }

      this.$('.dns-servers input').val(dnsServers.join(', '));
    },
    onIpv6Select: function() {
      this.setIpv6Select(!this.getIpv6Select());
    },
    getMultiDeviceSelect: function() {
      return this.$('.multi-device-toggle .selector').hasClass('selected');
    },
    setMultiDeviceSelect: function(state) {
      if (state) {
        this.$('.multi-device-toggle .selector').addClass('selected');
        this.$('.multi-device-toggle .selector-inner').show();
      }
      else {
        this.$('.multi-device-toggle .selector').removeClass('selected');
        this.$('.multi-device-toggle .selector-inner').hide();
      }
    },
    onMultiDeviceSelect: function() {
      this.setMultiDeviceSelect(!this.getMultiDeviceSelect());
    },
    getVxlanSelect: function() {
      return this.$('.vxlan-toggle .selector').hasClass('selected');
    },
    setVxlanSelect: function(state) {
      if (state) {
        this.$('.vxlan-toggle .selector').addClass('selected');
        this.$('.vxlan-toggle .selector-inner').show();
      }
      else {
        this.$('.vxlan-toggle .selector').removeClass('selected');
        this.$('.vxlan-toggle .selector-inner').hide();
      }
    },
    onVxlanSelect: function() {
      this.setVxlanSelect(!this.getVxlanSelect());
    },
    getIpv6FirewallSelect: function() {
      return this.$('.ipv6-firewall-toggle .selector').hasClass('selected');
    },
    setIpv6FirewallSelect: function(state) {
      if (state) {
        this.$('.ipv6-firewall-toggle .selector').addClass('selected');
        this.$('.ipv6-firewall-toggle .selector-inner').show();
      }
      else {
        this.$('.ipv6-firewall-toggle .selector').removeClass('selected');
        this.$('.ipv6-firewall-toggle .selector-inner').hide();
      }
    },
    onIpv6FirewallSelect: function() {
      this.setIpv6FirewallSelect(!this.getIpv6FirewallSelect());
    },
    onInputChange: function(evt) {
      if ($(evt.target).parent().hasClass('network')) {
        this.updateMaxHosts();
      }

      if (this.newServer) {
        return;
      }

      var port = parseInt(this.$('input.port').val(), 10);
      var protocol = this.$('select.protocol').val();
      var cipher = this.$('.cipher select').val();
      var hash = this.$('.hash select').val();
      var networkMode = this.$('.network-mode select').val();
      var otpAuth = this.getOtpAuthSelect();

      if (
        port !== this.model.get('port') ||
        protocol !== this.model.get('protocol') ||
        cipher !== this.model.get('cipher') ||
        hash !== this.model.get('hash') ||
        networkMode !== this.model.get('network_mode') ||
        otpAuth !== this.model.get('otp_auth')
      ) {
        this.setAlert('warning', 'These changes will require users ' +
          'that are not using an offical Pritunl client to download their ' +
          'updated profile again before being able to connect. Users ' +
          'using an offical Pritunl client will be able sync the changes.');
      } else {
        this.clearAlert();
      }
    },
    getDnsServers: function() {
      var dnsServer;
      var dnsServers = [];
      var dnsServersTemp = this.$('.dns-servers input').val().split(',');
      for (var i = 0; i < dnsServersTemp.length; i++) {
        dnsServer = $.trim(dnsServersTemp[i]);
        if (dnsServer) {
          dnsServers.push(dnsServer);
        }
      }
      return dnsServers;
    },
    updateMaxHosts: function() {
      var value = this.$('.network input').val().split('/');
      var maxHosts = {
        8: '16m',
        9: '8m',
        10: '4m',
        11: '2m',
        12: '1m',
        13: '524k',
        14: '262k',
        15: '131k',
        16: '65k',
        17: '32k',
        18: '16k',
        19: '8k',
        20: '4k',
        21: '2k',
        22: '1k',
        23: '509',
        24: '253',
        25: '125',
        26: '61',
        27: '29',
        28: '13',
        29: '5',
        30: '1'
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
      var name = this.$('.name input').val();
      var network = this.$('.network input').val();
      var port = parseInt(this.$('input.port').val(), 10);
      var protocol = this.$('select.protocol').val();
      var dhParamBits = parseInt(this.$('.dh-param-bits select').val(), 10);
      var ipv6 = this.getIpv6Select();
      var ipv6Firewall = this.getIpv6FirewallSelect();
      var multiDevice = this.getMultiDeviceSelect();
      var dnsServers = this.getDnsServers();
      var searchDomain = this.$('.search-domain input').val();
      var oncHostname = this.$('.onc-hostname input').val();
      var interClient = this.getInterClientSelect();
      var pingInterval = parseInt(this.$('.ping-interval input').val(), 10);
      var pingTimeout = parseInt(this.$('.ping-timeout input').val(), 10);
      var linkPingInterval = parseFloat(
        this.$('.link-ping-interval input').val(), 10);
      var linkPingTimeout = parseFloat(
        this.$('.link-ping-timeout input').val(), 10);
      var allowedDevices = this.$('.allowed-devices select').val();
      var maxClients = parseInt(this.$('.max-clients input').val(), 10);
      var replicaCount = parseInt(this.$('.replica-count input').val(), 10);
      var dnsMapping = this.getDnsMappingSelect();
      var debug = this.getDebugSelect();
      var otpAuth = this.getOtpAuthSelect();
      var restrictRoutes = this.getRestrictRoutesSelect();
      var vxlan = this.getVxlanSelect();
      var cipher = this.$('.cipher select').val();
      var hash = this.$('.hash select').val();
      var blockOutsideDns = this.getBlockOutsideDnsSelect();
      var bindAddress = this.$('.bind-address input').val();
      if (!bindAddress) {
        bindAddress = null;
      }
      var networkMode = this.$('.network-mode select').val();
      var networkStart = this.$('.network-start input').val();
      var networkEnd = this.$('.network-end input').val();
      var groups = this.getGroups();
      var policy = this.$('.policy textarea').val().trim() || null;

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }
      if (!network) {
        this.setAlert('danger', 'Network can not be empty.', '.network');
        return;
      }
      if (!port) {
        this.setAlert('danger', 'Port can not be empty.', 'input.port');
        return;
      }
      if (!searchDomain) {
        searchDomain = null;
      }
      if (!oncHostname) {
        oncHostname = null;
      }
      if (isNaN(replicaCount) || replicaCount === 0) {
        replicaCount = 1;
      }

      if (networkMode !== 'bridge') {
        networkStart = '';
        networkEnd = '';
      }

      if (allowedDevices === 'any') {
        allowedDevices = null;
      }

      var data = {
        'name': name,
        'type': this.model.get('type'),
        'network': network,
        'groups': groups,
        'bind_address': bindAddress,
        'port': port,
        'protocol': protocol,
        'dh_param_bits': dhParamBits,
        'network_mode': networkMode,
        'network_start': networkStart,
        'network_end': networkEnd,
        'restrict_routes': restrictRoutes,
        'ipv6': ipv6,
        'ipv6_firewall': ipv6Firewall,
        'multi_device': multiDevice,
        'dns_servers': dnsServers,
        'search_domain': searchDomain,
        'otp_auth': otpAuth,
        'cipher': cipher,
        'hash': hash,
        'block_outside_dns': blockOutsideDns,
        'inter_client': interClient,
        'ping_interval': pingInterval,
        'ping_timeout': pingTimeout,
        'link_ping_interval': linkPingInterval,
        'link_ping_timeout': linkPingTimeout,
        'onc_hostname': oncHostname,
        'allowed_devices': allowedDevices,
        'max_clients': maxClients,
        'replica_count': replicaCount,
        'vxlan': vxlan,
        'dns_mapping': dnsMapping,
        'debug': debug,
        'policy': policy
      };

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

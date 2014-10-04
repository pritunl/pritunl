define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverHost',
  'views/modal',
  'text!templates/modalAttachHost.html'
], function($, _, Backbone, ServerHostModel, ModalView,
    modalAttachHostTemplate) {
  'use strict';
  var lastServer;
  var ModalAttachHostView = ModalView.extend({
    className: 'attach-host-modal',
    template: _.template(modalAttachHostTemplate),
    title: 'Attach Host',
    okText: 'Attach',
    initialize: function(options) {
      this.hosts = options.hosts;
      ModalAttachHostView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template({
        hosts: this.hosts.toJSON(),
        servers: this.collection.toJSON(),
        lastServer: lastServer
      });
    },
    onOk: function() {
      this.setLoading('Attaching host...');
      var model = new ServerHostModel();
      var server = this.$('.server select').val();
      lastServer = server;
      model.save({
        id: this.$('.host select').val(),
        server: server
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

  return ModalAttachHostView;
});

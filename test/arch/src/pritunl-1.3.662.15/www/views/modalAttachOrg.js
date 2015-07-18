define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverOrg',
  'views/modal',
  'text!templates/modalAttachOrg.html'
], function($, _, Backbone, ServerOrgModel, ModalView,
    modalAttachOrgTemplate) {
  'use strict';
  var lastServer;
  var ModalAttachOrgView = ModalView.extend({
    className: 'attach-org-modal',
    template: _.template(modalAttachOrgTemplate),
    title: 'Attach Organization',
    okText: 'Attach',
    initialize: function(options) {
      this.orgs = options.orgs;
      ModalAttachOrgView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template({
        orgs: this.orgs.toJSON(),
        servers: this.collection.toJSON(),
        lastServer: lastServer
      });
    },
    onOk: function() {
      this.setLoading('Attaching organization...');
      var model = new ServerOrgModel();
      var server = this.$('.server select').val();
      lastServer = server;
      model.save({
        id: this.$('.org select').val(),
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

  return ModalAttachOrgView;
});

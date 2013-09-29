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
        servers: this.collection.toJSON()
      });
    },
    onOk: function() {
      this.setLoading('Attaching organization...');
      var model = new ServerOrgModel();
      model.save({
        id: this.$('.org select').val(),
        server: this.$('.server select').val()
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to attach organization, server error occurred.');
        }.bind(this)
      });
    }
  });

  return ModalAttachOrgView;
});

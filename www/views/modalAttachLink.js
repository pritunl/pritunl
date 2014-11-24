define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverLink',
  'views/modal',
  'text!templates/modalAttachLink.html'
], function($, _, Backbone, ServerLinkModel, ModalView,
    modalAttachLinkTemplate) {
  'use strict';
  var lastServer;
  var ModalAttachLinkView = ModalView.extend({
    className: 'attach-link-modal',
    template: _.template(modalAttachLinkTemplate),
    title: 'Attach Link',
    okText: 'Attach',
    events: function() {
      return _.extend({
        'change .server select, .link select': 'onSelectChange',
      }, ModalAttachLinkView.__super__.events);
    },
    body: function() {
      return this.template({
        servers: this.collection.toJSON(),
        lastServer: lastServer
      });
    },
    onSelectChange: function() {
      var server = this.$('.server select').val();
      var link = this.$('.link select').val();

      this.$('.server select option, .link select option').show();
      this.$('.server select option[value="' + link + '"]').hide();
      this.$('.link select option[value="' + server + '"]').hide();
    },
    onOk: function() {
      this.setLoading('Attaching link...');
      var model = new ServerLinkModel();
      var server = this.$('.server select').val();
      lastServer = server;
      model.save({
        id: this.$('.link select').val(),
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

  return ModalAttachLinkView;
});

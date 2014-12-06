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
    title: 'Link Servers',
    okText: 'Link',
    events: function() {
      return _.extend({
        'change .server select, .link select': 'onSelectChange',
        'click .use-local-toggle': 'onUseLocalSelect',
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
    getUseLocalSelect: function() {
      return this.$('.use-local-toggle .selector').hasClass('selected');
    },
    setUseLocalSelect: function(state) {
      if (state) {
        this.$('.use-local-toggle .selector').addClass('selected');
        this.$('.use-local-toggle .selector-inner').show();
      }
      else {
        this.$('.use-local-toggle .selector').removeClass('selected');
        this.$('.use-local-toggle .selector-inner').hide();
      }
    },
    onUseLocalSelect: function() {
      this.setUseLocalSelect(!this.getUseLocalSelect());
    },
    onOk: function() {
      var useLocal = this.getUseLocalSelect();

      this.setLoading('Attaching link...');

      var model = new ServerLinkModel();
      var server = this.$('.server select').val();
      lastServer = server;

      model.save({
        id: this.$('.link select').val(),
        server: server,
        use_local_address: useLocal,
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

define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalModifyLocHost.html'
], function($, _, Backbone, ModalView,
    modalModifyLocHostTemplate) {
  'use strict';
  var ModalModifyLocationView = ModalView.extend({
    className: 'modify-location-host-modal',
    template: _.template(modalModifyLocHostTemplate),
    title: 'Modify Location Host',
    okText: 'Save',
    hasAdvanced: true,
    events: function() {
      return _.extend({
        'click .static-host-toggle': 'onStaticHostSelect'
      }, ModalModifyLocationView.__super__.events);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    getStaticHostSelect: function() {
      return this.$('.static-host-toggle .selector').hasClass('selected');
    },
    setStaticHostSelect: function(state) {
      if (state) {
        this.$('.static-host-toggle .selector').addClass('selected');
        this.$('.static-host-toggle .selector-inner').show();
      } else {
        this.$('.static-host-toggle .selector').removeClass('selected');
        this.$('.static-host-toggle .selector-inner').hide();
      }
    },
    onStaticHostSelect: function() {
      this.setStaticHostSelect(!this.getStaticHostSelect());
    },
    onOk: function() {
      var name = this.$('.name input').val();
      var timeout = parseInt(this.$('.timeout input').val(), 10) || null;
      var priority = parseInt(this.$('.priority input').val(), 10) || 1;
      var staticHost = this.getStaticHostSelect();
      var publicAddress = this.$('.public-address input').val();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }

      this.setLoading('Saving location host...');
      this.model.save({
        name: name,
        timeout: timeout,
        priority: priority,
        static_host: staticHost,
        public_address: publicAddress
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

  return ModalModifyLocationView;
});

define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/linkLocationsList',
  'views/modalModifyLink',
  'views/modalDeleteLink',
  'views/modalRekeyLink',
  'text!templates/linksListItem.html'
], function($, _, Backbone, AlertView, LinkLocationsListView,
    ModalModifyLinkView, ModalDeleteLinkView, ModalRekeyLinkView,
    linksListItemTemplate) {
  'use strict';
  var LinksListItemView = Backbone.View.extend({
    className: 'link',
    template: _.template(linksListItemTemplate),
    events: {
      'click .link-title a': 'onSettings',
      'click .link-del': 'onDelete',
      'click .link-rekey': 'onRekey',
      'click .link-start, .link-stop': 'onOperation',
      'click .toggle-hidden': 'onToggleHidden'
    },
    initialize: function() {
      this.locationsView = new LinkLocationsListView({
        link: this.model
      });
      this.addView(this.locationsView);
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.update();
      this.$el.append(this.locationsView.render().el);
      return this;
    },
    update: function() {
      this.$('.link-title a').text(this.model.get('name'));

      if (this.model.get('status') === 'online') {
        this.$('.link-start').hide();
        this.$('.link-stop').show();
      } else {
        this.$('.link-stop').hide();
        this.$('.link-start').show();
      }
    },
    updateOrgsCount: function() {
      this.orgsCount = this.serverOrgsListView.views.length;
    },
    updateHostsCount: function() {
      this.hostsCount = this.serverHostsListView.views.length;
    },
    onSettings: function() {
      var modal = new ModalModifyLinkView({
        model: this.model.clone()
      });
      this.addView(modal);
    },
    onDelete: function(evt) {
      var model = this.model.clone();

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        this.locationsView.destroy();
        return;
      }

      var modal = new ModalDeleteLinkView({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        this.locationsView.destroy();
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully deleted link.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onRekey: function() {
      var model = this.model.clone();

      var modal = new ModalRekeyLinkView({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully rekeyed link.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onOperation: function(evt) {
      var status;
      var operation;

      if ($(evt.target).hasClass('link-start')) {
        status = 'online';
        operation = 'start';
      } else if ($(evt.target).hasClass('link-stop')) {
        status = 'offline';
        operation = 'stop';
      }
      if (!operation) {
        return;
      }

      $(evt.target).attr('disabled', 'disabled');
      this.model.clone().save({
        status: status
      }, {
        success: function() {
          $(evt.target).removeAttr('disabled');
        }.bind(this),
        error: function(model, response) {
          var alertView;
          $(evt.target).removeAttr('disabled');
          if (response.responseJSON) {
            alertView = new AlertView({
              type: 'danger',
              message: response.responseJSON.error_msg,
              dismissable: true
            });
          } else {
            alertView = new AlertView({
              type: 'danger',
              message: 'Failed to ' + operation +
              ' the link, server error occurred.',
              dismissable: true
            });
          }
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this)
      });
    },
    onToggleHidden: function(evt) {
      if (!evt.ctrlKey && !evt.shiftKey) {
        return;
      }
      if (this.$el.hasClass('show-hidden')) {
        this.$('.toggle-hidden').removeClass('label-success');
        this.$('.toggle-hidden').addClass('label-primary');
        this.$el.removeClass('show-hidden');
      } else {
        this.$('.toggle-hidden').addClass('label-success');
        this.$('.toggle-hidden').removeClass('label-primary');
        this.$el.addClass('show-hidden');
      }
    }
  });

  return LinksListItemView;
});

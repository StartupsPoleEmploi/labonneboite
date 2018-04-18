(function($) {

  $(document).on('lbbready', function () {
    $('.lbb-sidebar-toggle').enableSlidingSidebar();
  });

  $.fn.enableSlidingSidebar = function () {

      // When this class is not found, the classic display is enabled and the sidebar is floating on the left.
      if (!$('.lbb-sidebar-toggle-wrapper').length) {
        return this;
      }

      // Otherwise we are on a mobile device and we can activate the sliding mechanism.
      var sidebarTrigger = $(this);
      var sidebarContainer = $('.lbb-sidebar-wrapper');
      var sidebarInputs = sidebarContainer.find(':input');

      sidebarInputs.attr('tabindex', -1);

      sidebarTrigger.on('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          if (sidebarContainer.hasClass('active')) {  // Close.
            sidebarContainer.removeClass('active');
            sidebarInputs.attr('tabindex', -1);
            sidebarTrigger.focus();
            $('body').css('overflow', 'scroll');  // Enable scrolling on body content.
          } else {  // Open.
            sidebarContainer.addClass('active');
            sidebarInputs.attr('tabindex', 0);
            sidebarContainer.find('.lbb-sidebar-toggle').focus();
            $('body').css('overflow', 'hidden');  // Disable scrolling on body content.
          }
      });

      return this;

  };

})(jQuery);

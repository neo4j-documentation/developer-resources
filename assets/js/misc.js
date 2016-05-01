(function($){
  $(document)
      .foundation({
        tab: {
          callback: function (tab) {
            $(window).trigger('resize');
          }
        }
      })
      .ready(function () {
        var windowWidth = $(window).width(),
            windowHeight = $(window).height();

        function setTopOffset(elem){
          $(elem).data('top', $(elem).offset().top);
        }

        function windowScroll(elem){
          var $cta = $(elem).find('.fixed-cta');
          $cta.toggleClass('fixed', ($(window).scrollTop() + windowHeight - $cta.height()) < $(elem).data('top'));
        }

        $('.accordion-navigation a').on('click', function(){
          var $this = $(this),
              $parent = $this.parents('.accordion'),
              $navigation = $this.parents('.accordion-navigation'),
              $content = $this.siblings('.content'),
              $siblings = $parent.find('.accordion-navigation');

          if($navigation.hasClass('active')){
            $('.active').removeClass('active');
          } else {
            $('.active').removeClass('active');
            $navigation.addClass('active');
            $content.addClass('active')
          }

          console.log($this, $parent, $content, $siblings);
        });

        if($('.single-use_cases')){
          // STICKY CTA
          $('.use-case-footer-cta').each(function(){
            setTopOffset(this);
            windowScroll(this);
          });

          //if(Isotope){
          //  // ISOTOPE
          //  var $grid = $('.grid').isotope({
          //    itemSelector: '.grid-item',
          //    percentPosition: true,
          //    masonry: {
          //      columnWidth: '.grid-sizer',
          //      gutter: '.gutter-sizer'
          //    }
          //  });
          //
          //  // FIX WINDOW LAYOUT ISSUES
          //  $grid.isotope('on', 'arrangeComplete', function(items){
          //    setTopOffset(this);
          //    windowScroll(this);
          //  });
          //}

          // WINDOW SCROLL
          $(window).scroll(function(){
            if(windowWidth > 768){
              $('.use-case-footer-cta').each(function(){
                windowScroll(this);
              });
            }
          });

        }

        // searchHover();
        if(CodeMirror){
          CodeMirror.colorize();
        }
      });
  //var searchHover = function(){
  //    $('body')
  //        .on('hover','#searchsubmit, #s', function(){
  //            $('#s').toggleClass('open');
  //        })
  //        .on('focus','#s', function(){
  //            $(this).addClass('active');
  //        })
  //        .on('blur', '#s', function(){
  //            $(this).removeClass('active');
  //        });
  //    if($('.touch').length > 0){
  //        $('#s').addClass('active');
  //    }
  //}

})(jQuery);

try {
  Typekit.load();
}
catch (e){
}
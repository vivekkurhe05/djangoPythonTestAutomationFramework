// lazyload config
var MODULE_CONFIG = {
    chat:           [
                      '../libs/list.js/dist/list.js',
                      '../libs/notie/dist/notie.min.js',
                      'scripts/plugins/notie.js',
                      'scripts/app/chat.js'
                    ],
    mail:           [
                      '../libs/list.js/dist/list.js',
                      '../libs/notie/dist/notie.min.js',
                      'scripts/plugins/notie.js',
                      'scripts/app/mail.js'
                    ],
    user:           [],
    screenfull:     [
                      '../libs/screenfull/dist/screenfull.js',
                      'scripts/plugins/screenfull.js'
                    ],
    jscroll:        [
                      '../libs/jscroll/jquery.jscroll.min.js'
                    ],
    stick_in_parent:[
                      '../libs/sticky-kit/jquery.sticky-kit.min.js'
                    ],
    scrollreveal:   [
                      '../libs/scrollreveal/dist/scrollreveal.min.js',
                      'scripts/plugins/jquery.scrollreveal.js'
                    ],
    owlCarousel:    [
                      '../libs/owl.carousel/dist/assets/owl.carousel.min.css',
                      '../libs/owl.carousel/dist/assets/owl.theme.css',
                      '../libs/owl.carousel/dist/owl.carousel.min.js'
                    ],
    html5sortable:  [
                      '../libs/html5sortable/dist/html.sortable.min.js',
                      'scripts/plugins/jquery.html5sortable.js',
                      'scripts/plugins/sortable.js'
                    ],
    easyPieChart:   [
                      '../libs/easy-pie-chart/dist/jquery.easypiechart.min.js'
                    ],
    peity:          [
                      '../libs/peity/jquery.peity.js',
                      'scripts/plugins/jquery.peity.tooltip.js',
                    ],
    chart:          [
                      '../libs/moment/min/moment-with-locales.min.js',
                      '../libs/chart.js/dist/Chart.min.js',
                      'scripts/plugins/jquery.chart.js',
                      'scripts/plugins/chartjs.js'
                    ],
    dataTable:      [
                      '../libs/datatables/media/js/jquery.dataTables.min.js',
                      '../libs/datatables.net-bs4/js/dataTables.bootstrap4.js',
                      '../libs/datatables.net-bs4/css/dataTables.bootstrap4.css',
                      'scripts/plugins/datatable.js'
                    ],
    bootstrapTable: [
                      '../libs/bootstrap-table/dist/bootstrap-table.min.css',
                      '../libs/bootstrap-table/dist/bootstrap-table.min.js',
                      '../libs/bootstrap-table/dist/extensions/export/bootstrap-table-export.min.js',
                      '../libs/bootstrap-table/dist/extensions/mobile/bootstrap-table-mobile.min.js',
                      'scripts/plugins/tableExport.min.js',
                      'scripts/plugins/bootstrap-table.js'
                    ],
    bootstrapWizard:[
                      '../libs/twitter-bootstrap-wizard/jquery.bootstrap.wizard.min.js'
                    ],
    datetimepicker: [
                      '../libs/tempusdominus-bootstrap-4/build/css/tempusdominus-bootstrap-4.min.css',
                      '../libs/moment/min/moment-with-locales.min.js',
                      '../libs/tempusdominus-bootstrap-4/build/js/tempusdominus-bootstrap-4.min.js',
                      'scripts/plugins/datetimepicker.js'
                    ],
    fullCalendar:   [
                      '../libs/moment/min/moment-with-locales.min.js',
                      '../libs/fullcalendar/dist/fullcalendar.min.js',
                      '../libs/fullcalendar/dist/fullcalendar.min.css',
                      'scripts/plugins/fullcalendar.js'
                    ],
    parsley:        [
                      '../libs/parsleyjs/dist/parsley.min.js'
                    ],
    summernote:     [
                      '../libs/summernote/dist/summernote.css',
                      '../libs/summernote/dist/summernote-bs4.css',
                      '../libs/summernote/dist/summernote.min.js',
                      '../libs/summernote/dist/summernote-bs4.min.js'
                    ],
    vectorMap:      [
                      '../libs/jqvmap/dist/jqvmap.min.css',
                      '../libs/jqvmap/dist/jquery.vmap.js',
                      '../libs/jqvmap/dist/maps/jquery.vmap.world.js',
                      '../libs/jqvmap/dist/maps/jquery.vmap.usa.js',
                      '../libs/jqvmap/dist/maps/jquery.vmap.france.js',
                      'scripts/plugins/jqvmap.js'
                    ],
    waves:          [
                      '../libs/node-waves/dist/waves.min.css',
                      '../libs/node-waves/dist/waves.min.js',
                      'scripts/plugins/waves.js'
                    ]
  };

var MODULE_OPTION_CONFIG = {
  parsley: {
    errorClass: 'is-invalid',
    successClass: 'is-valid',
    errorsWrapper: '<ul class="list-unstyled text-sm mt-1 text-muted"></ul>'
  }
}
;
/**
 * 0.1.2
 * Deferred load js/css file, used for jquery.plugin.js and Lazy Loading.
 * 
 * @ flatfull.com All Rights Reserved.
 * Author url: http://themeforest.net/user/flatfull
 */
var lazyload = lazyload || {};

(function($, lazyload) {
	"use strict";

	var loaded = [],
	promise = false,
	deferred = $.Deferred();

	/**
	 * Chain loads the given sources
	 * @param srcs array, script or css
	 * @returns {*} Promise that will be resolved once the sources has been loaded.
	 */
	lazyload.load = function (srcs) {
		srcs = $.isArray(srcs) ? srcs : srcs.split(/\s+/);
		if(!promise){
			promise = deferred.promise();
		}

		$.each(srcs, function(index, src) {
			promise = promise.then( function(){
				return loaded[src] ? loaded[src].promise() : (src.indexOf('.css') >=0 ? loadCSS(src) : loadScript(src));
			} );
		});
		deferred.resolve();
		return promise;
	};

	lazyload.unload = function(srcs){
		srcs = $.isArray(srcs) ? srcs : srcs.split(/\s+/);
		$.each(srcs, function(index, src) {
			src.indexOf('.css') >=0 ? $('link[href="'+src+'"]').remove() : $('script[src="'+src+'"]').remove();
			delete loaded[src];
		});
	};

	/**
	 * Dynamically loads the given script
	 * @param src The url of the script to load dynamically
	 * @returns {*} Promise that will be resolved once the script has been loaded.
	 */
	var loadScript = function (src) {
		var deferred = $.Deferred();
		var script = document.createElement('script');
		script.src = src;
		script.onload = function (e) {
			deferred.resolve(e);
		};
		script.onerror = function (e) {
			deferred.reject(e);
		};

		document.body.appendChild(script);
		loaded[src] = deferred;

		return deferred.promise();
	};

	/**
	 * Dynamically loads the given CSS file
	 * @param href The url of the CSS to load dynamically
	 * @returns {*} Promise that will be resolved once the CSS file has been loaded.
	 */
	var loadCSS = function (href) {
		var deferred = $.Deferred();
		var style = document.createElement('link');
		style.rel = 'stylesheet';
		style.type = 'text/css';
		style.href = href;
		style.onload = function (e) {
			deferred.resolve(e);
		};
		style.onerror = function (e) {
			deferred.reject(e);
		};

		var head = document.getElementsByTagName("head")[0]
		head.insertBefore(style, head.firstChild);
		loaded[href] = deferred;

		return deferred.promise();
	};

})(jQuery, lazyload);
;(function ($, MODULE_CONFIG, MODULE_OPTION_CONFIG) {
  	"use strict";
  
	$.fn.plugin = function(){

        return this.each(function(){
        	var self = $(this);
        	var opts = self.attr('data-option') || self.attr('data-plugin-option');
        	var attr = self.attr('data-plugin');

        	// prepare the options
			var options = opts && eval('[' + opts + ']');
			if (options && $.isPlainObject(options[0])) {
				options[0] = $.extend({}, MODULE_OPTION_CONFIG[attr], options[0]);
			}

			// check if the plugin loaded and has option in the attribute
			if(self[attr] && opts){
				// init plugin with the potion on it's attribute
				self[attr].apply(self, options);
			}else{
				// load the plugin
				lazyload.load(MODULE_CONFIG[attr]).then( function(){
					// init plugin with the potion on it's attribute
					opts && self[attr].apply(self, options);
					// call the plugin init()
					self[attr] && self[attr].init && self[attr].init();
					// call other init()
					window[attr] && window[attr].init && window[attr].init();
				});
			}
        });
	}

})(jQuery, MODULE_CONFIG, MODULE_OPTION_CONFIG);
;(function ($) {
	'use strict';

	  window.app = {
      color: {
        primary: '#2499ee',
        accent: '#6284f3',
        warn: '#907eec'
      },
      setting: {
        ajax: true,
        folded: false,
        container: false,
        theme: 'primary',
        aside: 'white',
        brand: 'white',
        header: 'white',
        fixedContent: false,
        fixedAside: false,
        bg: ''
      }
    };

    window.hexToRGB = function(hex, alpha) {
      var r = parseInt(hex.slice(1, 3), 16),
          g = parseInt(hex.slice(3, 5), 16),
          b = parseInt(hex.slice(5, 7), 16);
      return "rgba(" + r + ", " + g + ", " + b + ", " + alpha + ")";
    }

    var namespace = app.color.primary+'-setting',
        theme;

	store(namespace, app.setting);

    var v = window.location.search.substring(1).split('&');

    for (var i = 0; i < v.length; i++){
        var n = v[i].split('=');
        app.setting[n[0]] = (n[1] == "true" || n[1]== "false") ? (n[1] == "true") : n[1];
        store(namespace, app.setting);
    }

    $(document).on('click.setting', '.setting input', function(e){
      var $this = $(this),
          $attr = $this.attr('name');
      app.setting[$attr] = $this.is(':checkbox') ? $this.prop('checked') : $(this).val();
      store(namespace, app.setting);
      setTheme(app.setting);
      $attr == 'ajax' && location.reload();
    });

    setTheme();

    // init
    function setTheme(){
      var that = $('.setting');
      // bg
      $('body').removeClass($('body').attr('ui-class')).addClass(app.setting.bg).attr('ui-class', app.setting.bg);
      // folded
      app.setting.folded ? $('#aside').addClass('folded') : $('#aside').removeClass('folded');
      // container
      app.setting.container ? $('body').addClass('container') : $('body').removeClass('container');
      // aside
      $('#aside .sidenav').removeClass($('#aside .sidenav').attr('ui-class')).addClass(app.setting.aside).attr('ui-class', app.setting.aside);
      // brand
      $('#aside .navbar').removeClass($('#aside .navbar').attr('ui-class')).addClass(app.setting.brand).attr('ui-class', app.setting.brand);
      // fixed header
      app.setting.fixedContent ? $('body').addClass('fixed-content') : $('body').removeClass('fixed-content');
      // fixed aside
      app.setting.fixedAside ? $('body').addClass('fixed-aside') : $('body').removeClass('fixed-aside');

      that.find('input[name="folded"]').prop('checked', app.setting.folded);
      that.find('input[name="fixedContent"]').prop('checked', app.setting.fixedContent);
      that.find('input[name="fixedAside"]').prop('checked', app.setting.fixedAside);
      that.find('input[name="container"]').prop('checked', app.setting.container);
      that.find('input[name="ajax"]').prop('checked', app.setting.ajax);

      that.find('input[name="theme"][value="'+app.setting.theme+'"]').prop('checked', true);
      that.find('input[name="bg"][value="'+app.setting.bg+'"]').prop('checked', true);
      that.find('input[name="aside"][value="'+app.setting.aside+'"]').prop('checked', true);
      that.find('input[name="brand"][value="'+app.setting.brand+'"]').prop('checked', true);

      if(theme != app.setting.theme){
        lazyload.load('/static/theme/assets/css/'+app.setting.theme+'.css').then(function(){
          lazyload.unload('/static/theme/assets/css/'+theme+'.css');
          theme = app.setting.theme;
        });
      }
    }

    // save setting to localstorage
    function store(namespace, data) {
      try{
        if (arguments.length > 1) {
          return localStorage.setItem(namespace, JSON.stringify(data));
        } else {
          var store = localStorage.getItem(namespace);
          return (store && JSON.parse(store)) || false;
        }
      }catch(err){

      }
    }

})(jQuery);
;(function ($) {
	'use strict';

    var TRANSITION_DURATION = 600;

    $(document).on('pjax:send', function() {
      $(document).trigger('pjaxSend');
    });

    $(document).on('pjaxSend', function(){
		$('#alert').remove()
		$('.popover').remove()
      // close the aside on mobile
      $('#aside').modal('hide');
      $('body').removeClass('modal-open').find('.modal-backdrop').remove();
      // remove the tags created by plugins
      $('.jqvmap-label, .note-popover, .dz-hidden-input').remove();
    });

    $(document).on('refresh', function() {
      main_pjax && main_pjax.refresh();
      sub_pjax && sub_pjax.refresh();
    });

    $(document).on('pjax:success', function() {
      if(bootstrap && bootstrap.Util){
        $(document).one(bootstrap.Util.TRANSITION_END, function(){
          $('.js-Pjax-onswitch').removeClass('js-Pjax-onswitch');
          $(document).trigger('pjaxEnd');
        }).emulateTransitionEnd(TRANSITION_DURATION);
      }else{
        $(document).trigger('pjaxEnd');
      }
    });

    if( app.setting.ajax ){
      var switch_h_option = {
        classNames: {
          // class added on the element that will be removed
          remove: 'animate animate-reverse animate-fast animate-no-delay',
          // class added on the element that will be added
          add: 'animate',
          // class added on the element when it go backward
          backward: 'fadeInRight',
          // class added on the element when it go forward (used for new page too)
          forward: 'fadeInLeft'
        },
        callbacks: {
          addElement: function(el){
            $(el).parent().addClass('js-Pjax-onswitch');
          },
          removeElement: function(el) {
            $(el).css( 'width', $(el).parent().width() );
          }
        }
      };

      var main_pjax = new Pjax({
        cacheBust: false,
        elements: '#aside a:not(.no-ajax), #content-header a, #nav a, .app-header a, #content-main a:not(.no-ajax)',
        selectors: ['title', '#content-header', '#content-footer', '#content-main', '#aside .modal-dialog #sidenav-list'],
        switches: {
          '#content-main': function(oldEl, newEl, options, switchOptions){
            this.switches.sideBySide.bind(this)(oldEl, newEl, options, switchOptions);
          }
        },
        switchesOptions: {
          '#content-main': switch_h_option
        }
      });

      var sub_pjax = new Pjax({
        cacheBust: false,
        elements: '#content-aside a, #content-body a, #header a, #content-footer a',
        selectors: ['#content-body', '#content-footer'],
        switches: {
          '#content-body': function(oldEl, newEl, options, switchOptions){
            this.switches.sideBySide.bind(this)(oldEl, newEl, options, switchOptions);
          }
        },
        switchesOptions: {
          '#content-body': switch_h_option
        }
      });

    }

})(jQuery);
;window.user = {};

(function($, list) {
    'use strict';

    var nav_el = '#user-nav',
        list_el = '#user-list',
        tagFilter = '',
        filter = '',
        navList, list, noticed = false;
    $(document).on('click', nav_el + ' a', function() {
        tagFilter = $(this).find('.nav-text').text();
        filter = '';
        if (tagFilter == 'All') tagFilter = '';
        $('input.search').attr('placeholder', 'Search ' + tagFilter);
        update(list);
        $('#content-aside').modal('hide');
    });

    $(document).on('click', '#filter a', function() {
        filter = $(this).text().toLowerCase();
        update(list);
    });

    function update(list) {
        if (!list.filter) return;
        list.filter(function(item) {
            if (item.values().tag.indexOf(tagFilter) > -1) {
                if (filter !== '') {
                    if (item.values()['item-title'].toLowerCase().indexOf(filter) == 0) {
                        return true;
                    } else {
                        return false;
                    }
                } else {
                    return true;
                }
            } else {
                return false;
            }
        });

        list.update();
        $('.list', list_el).removeClass('hide').addClass('animate fadeIn');
    }

    function updateCount(count) {
        $('#count').text(count);
    }

    var init = function() {
        $(document).trigger('refresh');

        // nav
        navList = new List(nav_el.substr(1), {
            listClass: 'nav',
            item: '<li><a href class="link"><span class="nav-text name"></span></a></li>',
            valueNames: [
                'name',
                {
                    name: 'link',
                    attr: 'href'
                }
            ]
        });

        // list
        if ($(list_el).length) {
            list = new List(list_el.substr(1), {
                valueNames: [
                    'item-title',
                    'item-except',
                    'tag'
                ]
            });

            list.on('updated', function(list) {
                updateCount(list.matchingItems.length);
                if (list.matchingItems.length > 0) {
                    $('.no-result').addClass('hide');
                } else {
                    $('.no-result').removeClass('hide');
                }
            });

            updateCount(list.items.length);
            update(list);
        }

    }

    // for ajax to init again
    list.init = init;

})(jQuery, window.user);
;(function($, notie) {
    'use strict';

    var app = window.app = window.app || {};

    var navigator = window.navigator;
    var userAgent = navigator.userAgent;

    // ie
    if (Boolean(userAgent.match(/MSIE/i)) || Boolean(userAgent.match(/Trident.*rv:11\./))) {
        $('body').addClass('ie');
    }
    if (userAgent.match(/MSIE 10\./i)) {
        $('body').addClass('ie10');
    }

    // iOs, Android, Blackberry, Opera Mini, and Windows mobile devices
    var ua = userAgent || navigator.vendor || window.opera;
    if ((/iPhone|iPod|iPad|Silk|Android|BlackBerry|Opera Mini|IEMobile/).test(ua)) {
        $('body').addClass('touch');
    }

    // fix z-index on ios safari
    if ((/iPhone|iPod|iPad/).test(ua)) {
        $(document, '.modal, .aside').on('shown.bs.modal', function(e) {
            var backDrop = $('.modal-backdrop');
            $(e.target).after($(backDrop));
        });
    }

    //resize
    $(window).on('resize', function() {
        var $w = $(window).width(),
            $lg = 1200,
            $md = 991,
            $sm = 768;
        if ($w > $lg) {
            $('.aside-lg').modal('hide');
        }
        if ($w > $md) {
            $('#aside').modal('hide');
            $('.aside-md, .aside-sm').modal('hide');
        }
        if ($w > $sm) {
            $('.aside-sm').modal('hide');
        }
    });

    // Assessment form / answers page
    var assessment = app.assessment = app.assessment || {};

    // Callback to show/hide elements based on their value and the
    // `required-on-change` data
    assessment.requiredOnChange = function() {
        var $el = $(this);
        var data = $el.data('required-on-change');
        var value = $el.val();
        $.each(data, function(lookup, values) {
            var required = $.inArray(value, values) > -1;
            var target = $(lookup);
            var isDueDate = (lookup.indexOf('due_date')) >= 0 ? true : false;
            if (required) {
                target.find(':input').prop({required: true, disabled: false});
                if(isDueDate) {
                    target.show();
                }
            } else {
                var targetValues = {required: false, disabled: false};
                if(isDueDate) {
                    targetValues.disabled = true;
                    target.hide();
                }
                target.find(':input').val('').prop(targetValues);
            }
        });

        var $attach_document_form = $el.closest('.js-answer-form').find('.js-attach-document-form');
        if ($attach_document_form.length) {
            var show_attach = $.inArray(value, ['yes', 'in-progress']) > -1;
            if (show_attach) {
                $attach_document_form.show();
            } else {
                $attach_document_form.hide();
            }
        }
    };

    // Initialise answer form state
    assessment.initAnswerForm = function (element) {
        // Initialise the data-required-on-change state
        $(element).find('input[data-required-on-change]').filter(':checked').each(assessment.requiredOnChange);

        // Select upload or attach tab
        $(element).find('.js-operation[value]').each(function () {
            var operation = $(this).val();
            $(this).closest('.js-answer-form').find(
                '.js-attach-document-form .nav-is-link[data-operation="' + operation + '"]'
            ).click();
        });
    };


    // load method called once on page load
    // Used for one time initialisation code (e.g. `$(document.body).on()`)
    assessment.load = function () {

        // Level / tier form
        //

        // Used on level switch select field reveal/hide.
        $(document.body).on('click', '[data-toggle]', function () {
            var target = $(this).data('toggle');
            $(target).toggle();
        });

        // Submit the level form on change to load different progress.
        $(document.body).on('change', '#div_id_level :input[name=level]', function() {
            $(this).parents('form').submit();
        });

        // Level / tier sections
        //

        //Show-hide levels on btn clicks
        $(document.body).on('click', 'input[name=toggleSection]', function() {

            var $level = $(this).data('val');
            var $btn_text = $(this).val();
            var $level_icon = $('#level_icon_' + $level);
            var $box = $('#level_' + $level);
            if ($btn_text.toLowerCase() === 'show') {
                $(this).val('Hide');
                $box.collapse('show');
                if($level_icon.length) {
                    $level_icon.addClass('fa-rotate-90');
                }
            } else {
                $(this).val('Show');
                $box.collapse('hide');
                if($level_icon.length) {
                    $level_icon.removeClass('fa-rotate-90');
                }
            }
        });

        // Answer forms
        //

        $(document.body).on('change', 'input[data-required-on-change]', assessment.requiredOnChange);

        // Question options (chekbox list)
        //

        var answerValue = '.js-answer-value';
        var answerOptions = '.js-answer-options';
        var answerValueInput = 'form:has(' + answerOptions + ' input) ' + answerValue + ' input';
        // Check all options if "Yes" is checked
        $(document.body).on('change', answerValueInput + '[value=yes]', function () {
            var $this = $(this);
            if ($this.prop('checked')) {
                var $options = $this.parents('form').find(answerOptions + ' input');
                $options.prop('checked', true);
            }
        });
        // Uncheck all options if "No" or "Not Applicable" is checked
        $(document.body).on('change', answerValueInput + '[value=no],[value=not-applicable]', function () {
            var $this = $(this);
            if ($this.prop('checked')) {
                var $options = $this.parents('form').find(answerOptions + ' input');
                $options.prop('checked', false);
            }
        });
        // Check "In Progress" if some but not all options are checked
        $(document.body).on('change', 'form ' + answerOptions + ' input', function () {
            var $this = $(this);
            var $options = $this.parents('form').find(answerOptions + ' input');
            var checked_count = $options.filter(':not(:checked)').length;
            var options_count = $options.length;
            if (checked_count && checked_count < options_count) {
                var $inporgress = $this.parents('form').find(answerValue + ' input[value=in-progress]');
                $inporgress.prop('checked', true);
            }
        });

        var submitAndLoadAnswer = function (form, target) {
            var $form = $(form);
            var $target = $(target || form).closest('.js-answer-form');
            $form.ajaxSubmit({
                target: $target,
                success: function() {
                    // update options when document uploaded
                    var options = $target.find('.js-attach-document-select select').html();
                    $('.js-answer-form .js-attach-document-select select').html(options);
                    // Global app setup
                    app.initGlobal($target);
                    // Answer form setup
                    assessment.initAnswerForm($target);
                    // Show the alerts as `notie`ces
                    $target.find('.alert').each(function () {
                        notie.alert({type: 'success', text: $(this).text()});
                    }).remove();
                },
            });
        };
        var submitAnswer = function (event, operation) {
            var $form = $(this).closest('form');
            $form.find('.js-operation').val(operation || '');
            return submitAndLoadAnswer($form);
        };

        $(document.body).on('change', '.js-answer-form .js-main-answer-form :input', submitAnswer);
        $(document.body).on('click', '.js-answer-form .js-operation-button', function (event) {
            // call submitAnswer with the extra form_action argument
            submitAnswer.apply(this, [event, $(this).val()]);
            // prevent browser submit
            return false;
        });
        $(document.body).on('click', 'button[data-submit-and-load-answer]', function () {
            var $this = $(this);
            var $form = $this.closest('form');
            var question = $this.data('submit-and-load-answer');
            var $target = $('.js-answer-form[data-question="' + question + '"]');
            submitAndLoadAnswer($form, $target);
            // prevent browser submit
            return false;
        });

    };

    // init method called for every pjax request
    assessment.init = function () {

        // Progress
        //

        $('#progress').on('scroll', function() {
            var $active_popover = $('.popover').attr('id');
            if ($active_popover) {
                $('#' + $active_popover).popover('hide');
                $('div.status-dot[aria-describedby=' + $active_popover + ']').blur();
            }
        });

        assessment.initAnswerForm(document.body);
    };

    // Global app bindings
    app.initGlobal = function(element) {
        var $element = $(element);
        $element.find('[data-toggle="popover"]').popover();
        $element.find('[data-toggle="tooltip"]').tooltip();
        $element.find('[data-plugin]').plugin();
    };

    app.init = function() {
        app.initGlobal(document.body);
        app.assessment.init();
    };

    app.init();
    app.assessment.load();

    // Select file
    var removeFile = function () {
        $('#select-file-box input[type=file]').val('');
        $('#file-info').hide();
        $('#file-label').fadeIn();
    };
    $(document).on('change', '#select-file-box input[type=file]', function() {
        var fileList = $('#select-file-box input[type=file]')[0].files;
        if (fileList.length) {
            $('#file-label').hide();
            $('#file-info').fadeIn();
            $('#file-name').text(fileList[0].name);
        } else {
            removeFile();
        }
    });
    $(document).on('click', '#file-remove', removeFile);

    $(document).on('pjaxEnd', function() {
        app.init();
    });

    app.scrollTo = function(id) {
        $('html, body').animate({ scrollTop: $('#' + id).offset().top}, 2000);
    };

    app.loadModal = function(url, title) {
        $('#load-modal .modal-title').text(title || '');
        $('#load-modal .modal-body').load(url, function() {
            $('#load-modal').modal('toggle');
        });
    };

    app.acceptInvite = function(url) {
        $('#invite-modal-body').load(url, function() {
            $('#invite-modal').modal('toggle');
        });
    };

    app.showTab = function (id) {
        $('.nav-tabs a[href="#'+id+'"]').tab('show');
    };

    app.deleteUser = function(url) {
        $('#delete-user-modal-body').load(url, function() {
            $('#delete-user-modal').modal('toggle');
        });
    };

    app.toggleInviteForm = function(currentForm) {
        var toggleFormMap = {
            grantee_invite_form: 'org_invite_form',
            org_invite_form: 'grantee_invite_form',
        };
        $('.'+currentForm).hide();
        $('.'+toggleFormMap[currentForm]).show();

        if(currentForm === 'org_invite_form'){
            $('[name="is_organisation_invite"]').attr('checked', false);
        }else{
            $('[name="is_organisation_invite"]').attr('checked', true);
        }
    };

})(window.jQuery, window.notie);

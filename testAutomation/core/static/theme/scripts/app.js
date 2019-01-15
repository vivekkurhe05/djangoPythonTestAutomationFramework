(function($, notie) {
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

    // Callback to set elements required based on their value and the
    // `required-on-change` data
    // Also hides the due_date and sets it disabled when not required.
    assessment.requiredOnChange = function() {
        var $el = $(this);
        var data = $el.data('required-on-change');
        var value = $el.val();
        $.each(data, function(lookup, values) {
            var required = $.inArray(value, values) > -1;
            var target = $(lookup);
            var targetValues = {required: required};
            var isDueDate = (lookup.indexOf('due_date')) >= 0 ? true : false;
            if(isDueDate) {
                targetValues.disabled = !required;
                target.toggle(required);
            }
            target.find(':input').prop(targetValues);
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

        // order.html : checkbox
        $(document.body).on('click', 'input[name=subscription]', function() {
            var total_amt = 0 ;
            var $order_form = $('#order-form');
            var subscription_amt = parseFloat($order_form.data('subscription-amount'));
            var $total_amt_label = $('#total-amount');
            var has_active_subscription = $order_form.data('has-active-subscription');
            var is_renewal_due = $order_form.data('is-renewal-due');

            if(has_active_subscription === 'False' || (has_active_subscription === 'True' && is_renewal_due === 'False') ) {
                // do not disselect the checkbox from ui
                return false;
            }
            var $subscriptionSelected = $(this).is(':checked');
            var $selectedPackage = $('input[name=package]:checked');
            if ($subscriptionSelected) {
                total_amt += subscription_amt;
            }
            if($selectedPackage.length){
                total_amt += parseFloat($selectedPackage.attr('data-value'), 10);
            }
            total_amt = parseFloat(Math.round(total_amt * 100) / 100).toFixed(2);
            $total_amt_label.text('$'+total_amt);
        });
        $(document.body).on('click', 'input[name=package]', function() {
            var total_amt = 0;
            var $order_form = $('#order-form');
            var subscription_amt = parseFloat($order_form.data('subscription-amount'));
            var $total_amt_label = $('#total-amount');
            var $this = $(this);
            var $last_selected_package = $('#package-list').find('tr.text-bold');
            var $subscription = $('#id_subscription');

            if($last_selected_package) {
                $last_selected_package.removeClass('text-bold _700');
            }
            $this.parents('tr').addClass('text-bold _700');
            var $subscriptionSelected = $subscription.is(':checked');

            if ($subscriptionSelected) {
                total_amt += subscription_amt;
            }
            total_amt += parseFloat($this.attr('data-value'), 10);
            total_amt = parseFloat(Math.round(total_amt * 100) / 100).toFixed(2);
            $total_amt_label.text('$'+total_amt);
        });

    };

    // init method called for every pjax request
    assessment.init = function () {

        // Progress
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

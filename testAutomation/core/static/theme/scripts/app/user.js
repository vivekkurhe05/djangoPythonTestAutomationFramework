window.user = {};

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

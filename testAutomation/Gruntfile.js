/* eslint-env node */
'use strict';

module.exports = function (grunt) {

    if (grunt.option('help')) {
        // Load all tasks so they can be viewed in the help: grunt -h or --help.
        require('load-grunt-tasks')(grunt);
    } else {
        // Use jit-grunt to only load necessary tasks for each invocation of grunt.
        require('jit-grunt')(grunt, {sasslint: 'grunt-sass-lint'});
    }

    grunt.initConfig({
        config: {
            paths: {
                baseDir: 'core',
                sassDir: '<%= config.paths.baseDir %>/sass',
                sassFiles: ['<%= config.paths.sassDir %>/**/*.scss'],
                staticDir: '<%= config.paths.baseDir %>/static',
                themeDir: '<%= config.paths.staticDir %>/theme',
                bowerDir: 'bower_components',
                cssDir: '<%= config.paths.staticDir %>/css',
                jsDir: '<%= config.paths.staticDir %>/js',
                imagesDir: '<%= config.paths.staticDir %>/images',
                svgDir: '<%= config.paths.imagesDir %>/svg',
                fontsDir: '<%= config.paths.staticDir %>/fonts',
                templatesDir: '<%= config.paths.baseDir %>/templates',
                compiledSvgDir: '<%= config.paths.templatesDir %>/svg',
                scripts: [
                    '<%= config.paths.themeDir %>/scripts/app.js',
                    'Gruntfile.js',
                ],
            },
        },
    });

    grunt.config.set('livereload', grunt.option('livereload') || false);

    grunt.config.merge({
        watch: {
            options: {livereload: grunt.option('livereload') || false},
            sass: {
                files: '<%= config.paths.sassFiles %>',
                tasks: 'sass',
            },
            svgstore: {
                files: '<%= config.paths.svgDir %>/*.svg',
                tasks: 'svgstore',
            },
            js: {
                files: '<%= config.paths.themeDir %>/scripts/**/*.js',
                tasks: 'concat:concatappjs',
            },
        },
        concat: {
            concatlibjs: {
                options: { separator: ';'},
                src: [
                    '<%= config.paths.bowerDir %>/bluebird/js/browser/bluebird.min.js',
                    '<%= config.paths.bowerDir %>/jquery/dist/jquery.js',
                    '<%= config.paths.bowerDir %>/jquery-form/dist/jquery.form.min.js',
                    '<%= config.paths.bowerDir %>/popper.js/dist/umd/popper.js',
                    '<%= config.paths.bowerDir %>/bootstrap/dist/js/bootstrap.js',
                    '<%= config.paths.bowerDir %>/select2/dist/js/select2.js',
                    '<%= config.paths.bowerDir %>/bootstrap-datepicker/dist/js/bootstrap-datepicker.js',
                    '<%= config.paths.bowerDir %>/PACE/pace.js',
                    '<%= config.paths.themeDir %>/libs/pjax/pjax.js',
                    '<%= config.paths.bowerDir %>/notie/dist/notie.js',
                    '<%= config.paths.bowerDir %>/list.js/dist/list.js',
                ],
                dest: '<%= config.paths.jsDir %>/lib.js',
            },
            concatappjs: {
                options: { separator: ';'},
                src: [
                    '<%= config.paths.themeDir %>/scripts/lazyload.config.js',
                    '<%= config.paths.themeDir %>/scripts/lazyload.js',
                    '<%= config.paths.themeDir %>/scripts/plugin.js',
                    '<%= config.paths.themeDir %>/scripts/theme.js',
                    '<%= config.paths.themeDir %>/scripts/ajax.js',
                    '<%= config.paths.themeDir %>/scripts/app/user.js',
                    '<%= config.paths.themeDir %>/scripts/app.js',
                ],
                dest: '<%= config.paths.jsDir %>/app.js',
            },
            concatlibcss: {
                src: ['<%= config.paths.bowerDir %>/bootstrap/dist/css/bootstrap.css',
                    '<%= config.paths.bowerDir %>/select2/dist/css/select2.css',
                    '<%= config.paths.bowerDir %>/font-awesome/css/font-awesome.css',
                    '<%= config.paths.bowerDir %>/bootstrap-datepicker/dist/css/bootstrap-datepicker.css',
                    '<%= config.paths.themeDir %>/assets/css/app.css',
                ],
                dest: '<%= config.paths.cssDir %>/lib.css',
            },
        },
        sass: {dist: {files: {'<%= config.paths.cssDir %>/app.css': '<%= config.paths.sassDir %>/main.scss'}}},
        svgstore: {
            options: {
                // This will prefix each ID
                prefix: 'svg-',
                // will add and overide the the default xmlns="http://www.w3.org/2000/svg" attribute to the resulting SVG
                svg: {
                    viewBox: '0 0 100 100',
                    xmlns: 'http://www.w3.org/2000/svg',
                },
            },
            default: {files: {'<%= config.paths.compiledSvgDir %>/svg-defs.svg': ['<%= config.paths.svgDir %>/*.svg']} },
        },
        svgmin: {
            dist: {
                files: [{
                    expand: true,
                    src: '<%= config.paths.imagesDir %>/**/*.svg',
                }],
            },
        },
        eslint: {all: '<%= config.paths.scripts %>'},

    });

    // - - - T A S K S - - -
    grunt.registerTask('default', 'dev');

    grunt.registerTask('dev', [
        'svgstore',
        'sass',
        'watch',
    ]);

    grunt.registerTask('build', [
        'svgstore',
        'svgmin',
        'concat:concatlibjs',
        'concat:concatappjs',
        'concat:concatlibcss',
        'sass',
    ]);

    grunt.registerTask('test', [
        'sass',
        'eslint',
    ]);

};

/* jshint node: true */
module.exports = function(grunt) {
    "use strict";

    // Project configuration.
    grunt.initConfig({
        // Metadata.
        pkg: grunt.file.readJSON('package.json'),
        banner: '/**\n' +
                '* <%= pkg.name %>.js v<%= pkg.version %> by @fat and @mdo\n' +
                '* Copyright <%= grunt.template.today("yyyy") %> <%= pkg.author %>\n' +
                '* <%= _.pluck(pkg.licenses, "url").join(", ") %>\n' +
                '*/\n',
        jqueryCheck: 'if (!jQuery) { throw new Error(\"Bootstrap requires jQuery\") }\n\n',
        // Task configuration.
        clean: {
            dist: ['dist']
        },
        concat: {
            options: {
                banner: '<%= banner %><%= jqueryCheck %>',
                stripBanners: false
            },
            bootstrap: {
                src: ['js/transition.js', 'js/alert.js', 'js/button.js', 'js/carousel.js', 'js/collapse.js', 'js/dropdown.js', 'js/modal.js', 'js/tooltip.js', 'js/popover.js', 'js/scrollspy.js', 'js/tab.js', 'js/affix.js'],
                dest: 'dist/js/<%= pkg.name %>.js'
            }
        },
        jshint: {
            options: {
                ignores: [],// HACK: workaround https://github.com/gruntjs/grunt-contrib-jshint/issues/86
                jshintrc: 'js/.jshintrc'
            },
            gruntfile: {
                src: 'Gruntfile.js'
            },
            src: {
                src: ['js/*.js']
            },
            test: {
                src: ['js/tests/unit/*.js']
            }
        },
        recess: {
            options: {
                compile: true
            },
            bootstrap: {
                files: {
                    'dist/css/bootstrap.css': ['less/bootstrap.less']
                }
            },
            min: {
                options: {
                    compress: true
                },
                files: {
                    'dist/css/bootstrap.min.css': ['less/bootstrap.less']
                }
            }
        },
        uglify: {
            options: {
                banner: '<%= banner %>'
            },
            bootstrap: {
                files: {
                    'dist/js/<%= pkg.name %>.min.js': ['<%= concat.bootstrap.dest %>']
                }
            }
        },
        qunit: {
            options: {
                inject: 'js/tests/unit/phantom.js'
            },
            files: ['js/tests/*.html']
        },
        connect: {
            server: {
                options: {
                    port: 3000,
                    base: '.'
                }
            }
        },
        watch: {
            src: {
                files: '<%= jshint.src.src %>',
                tasks: ['jshint:src', 'qunit']
            },
            test: {
                files: '<%= jshint.test.src %>',
                tasks: ['jshint:test', 'qunit']
            },
            recess: {
                files: 'less/*.less',
                tasks: ['recess']
            }
        }
    });


    // These plugins provide necessary tasks.
    grunt.loadNpmTasks('grunt-contrib-connect');
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-qunit');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-recess');


    // Test task.
    grunt.registerTask('test', ['jshint', 'qunit']);

    // JS distribution task.
    grunt.registerTask('dist-js', ['concat', 'uglify']);

    // CSS distribution task.
    grunt.registerTask('dist-css', ['recess']);

    // Full distribution task.
    grunt.registerTask('dist', ['clean', 'dist-css', 'dist-js']);

    // Default task.
    grunt.registerTask('default', ['test', 'dist']);
};

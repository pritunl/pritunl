/*jshint strict:false */
var wget = function(files) {
  var dir;
  var cmds = {};

  for (var file in files) {
    dir = file.split('/');
    dir = dir.slice(0, dir.length - 1).join('/');

    cmds[file] = {
      cmd: 'mkdir -p ' + dir + '; wget -O ' + file + ' ' + files[file]
    };
  }

  return cmds;
};

module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    jshint: {
      options: {
        bitwise: true,
        camelcase: true,
        curly: true,
        eqeqeq: true,
        immed: true,
        latedef: true,
        newcap: true,
        noarg: true,
        noempty: true,
        quotmark: 'single',
        regexp: true,
        undef: true,
        unused: true,
        strict: true,
        trailing: true,
        browser: true,
        maxlen: 79,
        globals: {
          module: true,
          define: true,
          require: true
        }
      },
      all: [
        'collections/*.js',
        'init/*.js',
        'models/*.js',
        'routers/*.js',
        'views/*.js',
        '*.js',
      ]
    },

    clean: {
      dist: ['dist']
    },

    requirejs: {
      test: {
        options: {
          name: 'main',
          optimize: 'uglify2',
          out: 'dist/js/main.js',
          mainConfigFile: 'main.js',
          generateSourceMaps: true,
          preserveLicenseComments: false,
          uglify2: {
            mangle: false
          },
          paths: {
            backbone: 'vendor/backbone/backbone.min',
            bootstrap: 'vendor/bootstrap/bootstrap.min',
            d3: 'vendor/d3/d3.min',
            googleAnalytics: 'vendor/googleAnalytics/googleAnalytics.min',
            jquery: 'vendor/jquery/jquery.min',
            less: 'vendor/less/less.min',
            text: 'vendor/requireText/text',
            underscore: 'vendor/underscore/underscore.min',
            initialize: 'init/production'
          }
        }
      },
      demo: {
        options: {
          name: 'main',
          optimize: 'uglify2',
          out: 'dist/js/main.js',
          mainConfigFile: 'main.js',
          generateSourceMaps: false,
          preserveLicenseComments: true,
          uglify2: {
            mangle: false
          },
          paths: {
            backbone: 'vendor/backbone/backbone.min',
            bootstrap: 'vendor/bootstrap/bootstrap.min',
            d3: 'vendor/d3/d3.min',
            googleAnalytics: 'vendor/googleAnalytics/googleAnalytics.min',
            jquery: 'vendor/jquery/jquery.min',
            less: 'vendor/less/less.min',
            text: 'vendor/requireText/text',
            underscore: 'vendor/underscore/underscore.min',
            initialize: 'init/demo'
          }
        }
      },
      production: {
        options: {
          name: 'main',
          optimize: 'uglify2',
          out: 'dist/js/main.js',
          mainConfigFile: 'main.js',
          generateSourceMaps: false,
          preserveLicenseComments: true,
          uglify2: {
            mangle: false
          },
          paths: {
            backbone: 'vendor/backbone/backbone.min',
            bootstrap: 'vendor/bootstrap/bootstrap.min',
            d3: 'vendor/d3/d3.min',
            googleAnalytics: 'vendor/googleAnalytics/googleAnalytics.min',
            jquery: 'vendor/jquery/jquery.min',
            jqueryUi: 'vendor/jqueryUi/jqueryUi.min',
            less: 'vendor/less/less.min',
            text: 'vendor/requireText/text',
            underscore: 'vendor/underscore/underscore.min',
            initialize: 'init/production'
          }
        }
      }
    },

    less: {
      compile: {
        options: {
          paths: ['styles']
        },
        files: {
          'dist/css/main.css': 'styles/main.less'
        }
      }
    },

    copy: {
      dist: {
        files: {
          'dist/js/require.min.js': 'vendor/require/require.min.js',
          'dist/favicon.ico': 'img/favicon.ico',
          'dist/robots.txt': 'root/robots.txt',
          'dist/index.html': 'root/index.html'
        }
      }
    },

    exec: wget({
      'vendor/backbone/backbone.js':
        'https://raw.github.com/amdjs/backbone/master/backbone.js',
      'vendor/backbone/backbone.min.js':
        'https://raw.github.com/amdjs/backbone/master/backbone-min.js',

      'vendor/bootstrap/bootstrap.js':
        'https://raw.github.com/twbs/bootstrap/master/' +
          'dist/js/bootstrap.js',
      'vendor/bootstrap/bootstrap.min.js':
        'https://raw.github.com/twbs/bootstrap/master/' +
          'dist/js/bootstrap.min.js',

      'vendor/d3/d3.js':
        'https://raw.github.com/mbostock/d3/master/d3.js',
      'vendor/d3/d3.min.js':
        'https://raw.github.com/mbostock/d3/master/d3.min.js',

      'vendor/googleAnalytics/googleAnalytics.min.js':
        'https://www.google-analytics.com/ga.js',

      'vendor/jquery/jquery.js':
        'http://code.jquery.com/jquery.js',
      'vendor/jquery/jquery.min.js':
        'http://code.jquery.com/jquery.min.js',

      'vendor/less/less.js':
        'https://raw.github.com/less/less.js/master/dist/less-1.4.2.js',
      'vendor/less/less.min.js':
        'https://raw.github.com/less/less.js/master/dist/less-1.4.2.min.js',

      'vendor/require/require.js':
        'https://raw.github.com/jrburke/requirejs/master/require.js',
      'vendor/require/require.min.js':
        'http://requirejs.org/docs/release/2.1.8/minified/require.js',

      'vendor/requireText/text.js':
        'https://raw.github.com/requirejs/text/master/text.js',

      'vendor/underscore/underscore.js':
        'https://raw.github.com/amdjs/underscore/master/underscore.js',
      'vendor/underscore/underscore.min.js':
        'https://raw.github.com/amdjs/underscore/master/underscore-min.js',

      'fonts/glyphicons-halflings-regular.eot':
        'https://github.com/twbs/bootstrap/raw/master/' +
          'dist/fonts/glyphicons-halflings-regular.eot',
      'fonts/glyphicons-halflings-regular.svg':
        'https://github.com/twbs/bootstrap/raw/master/' +
          'dist/fonts/glyphicons-halflings-regular.svg',
      'fonts/glyphicons-halflings-regular.ttf':
        'https://github.com/twbs/bootstrap/raw/master/' +
          'dist/fonts/glyphicons-halflings-regular.ttf',
      'fonts/glyphicons-halflings-regular.woff':
        'https://github.com/twbs/bootstrap/raw/master/' +
          'dist/fonts/glyphicons-halflings-regular.woff'
    })
  });

  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-requirejs');
  grunt.loadNpmTasks('grunt-exec');

  grunt.registerTask('default', ['jshint', 'clean', 'requirejs:production',
    'less', 'copy']);

  grunt.registerTask('test', ['jshint', 'clean', 'requirejs:test', 'less',
    'copy']);

  grunt.registerTask('demo', ['jshint', 'clean', 'requirejs:demo', 'less',
    'copy']);

  grunt.registerTask('lint', ['jshint']);

  grunt.registerTask('update', ['exec']);
};

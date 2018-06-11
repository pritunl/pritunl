/* jshint strict:false */

module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    jshint: {
      options: {
        bitwise: true,
        camelcase: false,
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
        '*.js'
      ]
    },

    clean: {
      dist: ['vendor/dist']
    },

    requirejs: {
      test: {
        options: {
          name: 'main',
          optimize: 'uglify2',
          out: 'vendor/dist/js/main.js',
          mainConfigFile: 'main.js',
          generateSourceMaps: true,
          preserveLicenseComments: false,
          uglify2: {
            mangle: false
          },
          paths: {
            ace: 'vendor/ace/ace',
            aceModeLog: 'vendor/ace/mode-log',
            aceModeSh: 'vendor/ace/mode-sh',
            aceModeText: 'vendor/ace/mode-text',
            aceThemePritunl: 'vendor/ace/theme-pritunl',
            backbone: 'vendor/backbone/backbone.min',
            bootstrap: 'vendor/bootstrap/bootstrap.min',
            d3: 'vendor/d3/d3.min',
            jquery: 'vendor/jquery/jquery.min',
            less: 'vendor/less/less.min',
            qrcode: 'vendor/qrcode/qrcode.min',
            rickshaw: 'vendor/rickshaw/rickshaw.min',
            select: 'vendor/select/select.min',
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
          out: 'vendor/dist/js/main.js',
          mainConfigFile: 'main.js',
          generateSourceMaps: false,
          preserveLicenseComments: true,
          uglify2: {
            mangle: false
          },
          paths: {
            ace: 'vendor/ace/ace',
            aceModeLog: 'vendor/ace/mode-log',
            aceModeSh: 'vendor/ace/mode-sh',
            aceModeText: 'vendor/ace/mode-text',
            aceThemePritunl: 'vendor/ace/theme-pritunl',
            backbone: 'vendor/backbone/backbone.min',
            bootstrap: 'vendor/bootstrap/bootstrap.min',
            d3: 'vendor/d3/d3.min',
            jquery: 'vendor/jquery/jquery.min',
            less: 'vendor/less/less.min',
            qrcode: 'vendor/qrcode/qrcode.min',
            rickshaw: 'vendor/rickshaw/rickshaw.min',
            select: 'vendor/select/select.min',
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
          out: 'vendor/dist/js/main.js',
          mainConfigFile: 'main.js',
          generateSourceMaps: false,
          preserveLicenseComments: true,
          uglify2: {
            mangle: false
          },
          paths: {
            ace: 'vendor/ace/ace',
            aceModeLog: 'vendor/ace/mode-log',
            aceModeSh: 'vendor/ace/mode-sh',
            aceModeText: 'vendor/ace/mode-text',
            aceThemePritunl: 'vendor/ace/theme-pritunl',
            backbone: 'vendor/backbone/backbone.min',
            bootstrap: 'vendor/bootstrap/bootstrap.min',
            d3: 'vendor/d3/d3.min',
            jquery: 'vendor/jquery/jquery.min',
            less: 'vendor/less/less.min',
            qrcode: 'vendor/qrcode/qrcode.min',
            rickshaw: 'vendor/rickshaw/rickshaw.min',
            select: 'vendor/select/select.min',
            text: 'vendor/requireText/text',
            underscore: 'vendor/underscore/underscore.min',
            initialize: 'init/production'
          }
        }
      }
    },

    copy: {
      dist: {
        files: {
          'vendor/dist/css/main.css': 'styles/vendor/main.css',
          'vendor/dist/fonts/FontAwesome.otf': 'fonts/FontAwesome.otf',
          'vendor/dist/fonts/fontawesome-webfont.eot':
            'fonts/fontawesome-webfont.eot',
          'vendor/dist/fonts/fontawesome-webfont.svg':
            'fonts/fontawesome-webfont.svg',
          'vendor/dist/fonts/fontawesome-webfont.ttf':
            'fonts/fontawesome-webfont.ttf',
          'vendor/dist/fonts/fontawesome-webfont.woff':
            'fonts/fontawesome-webfont.woff',
          'vendor/dist/fonts/fontawesome-webfont.woff2':
            'fonts/fontawesome-webfont.woff2',
          'vendor/dist/fonts/fredoka-one.eot': 'fonts/fredoka-one.eot',
          'vendor/dist/fonts/fredoka-one.woff': 'fonts/fredoka-one.woff',
          'vendor/dist/fonts/glyphicons-halflings-regular.eot':
            'fonts/glyphicons-halflings-regular.eot',
          'vendor/dist/fonts/glyphicons-halflings-regular.svg':
            'fonts/glyphicons-halflings-regular.svg',
          'vendor/dist/fonts/glyphicons-halflings-regular.ttf':
            'fonts/glyphicons-halflings-regular.ttf',
          'vendor/dist/fonts/glyphicons-halflings-regular.woff':
            'fonts/glyphicons-halflings-regular.woff',
          'vendor/dist/fonts/ubuntu-bold.eot': 'fonts/ubuntu-bold.eot',
          'vendor/dist/fonts/ubuntu-bold.woff': 'fonts/ubuntu-bold.woff',
          'vendor/dist/fonts/ubuntu.eot': 'fonts/ubuntu.eot',
          'vendor/dist/fonts/ubuntu.woff': 'fonts/ubuntu.woff',
          'vendor/dist/js/require.min.js': 'vendor/require/require.min.js',
          'vendor/dist/robots.txt': 'root/robots.txt',
          'vendor/dist/index.html': 'root/index.html'
        }
      },
      demo: {
        files: {
          'vendor/dist/css/main.css': 'styles/vendor/main.css',
          'vendor/dist/fonts/fredoka-one.eot': 'fonts/fredoka-one.eot',
          'vendor/dist/fonts/fredoka-one.woff': 'fonts/fredoka-one.woff',
          'vendor/dist/fonts/glyphicons-halflings-regular.eot':
            'fonts/glyphicons-halflings-regular.eot',
          'vendor/dist/fonts/glyphicons-halflings-regular.svg':
            'fonts/glyphicons-halflings-regular.svg',
          'vendor/dist/fonts/glyphicons-halflings-regular.ttf':
            'fonts/glyphicons-halflings-regular.ttf',
          'vendor/dist/fonts/glyphicons-halflings-regular.woff':
            'fonts/glyphicons-halflings-regular.woff',
          'vendor/dist/fonts/ubuntu-bold.eot': 'fonts/ubuntu-bold.eot',
          'vendor/dist/fonts/ubuntu-bold.woff': 'fonts/ubuntu-bold.woff',
          'vendor/dist/fonts/ubuntu.eot': 'fonts/ubuntu.eot',
          'vendor/dist/fonts/ubuntu.woff': 'fonts/ubuntu.woff',
          'vendor/dist/js/require.min.js': 'vendor/require/require.min.js',
          'vendor/dist/index.html': 'root/demo_index.html'
        }
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-requirejs');

  grunt.registerTask('default', ['jshint', 'clean',
    'requirejs:production', 'copy:dist']);

  grunt.registerTask('test', ['jshint', 'clean', 'requirejs:test',
    'copy:dist']);

  grunt.registerTask('demo', ['jshint', 'clean', 'requirejs:demo',
    'copy:demo']);

  grunt.registerTask('lint', ['jshint']);
};

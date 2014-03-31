/* jshint strict:false */

var fs = require('fs');
var path = require('path');
var crypto = require('crypto');

module.exports = function(grunt) {
  grunt.registerMultiTask('versioning', 'Version static files', function() {
    var options = this.options({
      hashLength: 6,
      encoding: 'utf8',
      replaceFiles: []
    });
    var i;
    var data;
    var filePath;
    var filePathNew;
    var replacePath;
    var hash;
    var staticFiles = this.data.staticFiles;
    var replaceFiles = this.data.replaceFiles;
    var searchStr;
    var replaceStr;
    var replaces = {};

    for (i = 0; i < staticFiles.length; i++) {
      filePath = staticFiles[i];

      hash = crypto.createHash('md5').update(grunt.file.read(
        filePath, options.encoding)).digest('hex');
      hash = hash.substr(0, options.hashLength);

      filePathNew = path.dirname(filePath) + path.sep + path.basename(
        filePath, path.extname(filePath)) + '.' + hash + path.extname(
        filePath);

      fs.rename(filePath, filePathNew);
      replaces[path.basename(filePath)] = path.basename(filePathNew);
    }

    for (i = 0; i < replaceFiles.length; i++) {
      replacePath = replaceFiles[i];
      data = grunt.file.read(replacePath, options.encoding);

      for (searchStr in replaces) {
        replaceStr = replaces[searchStr];
        data = data.replace(new RegExp(searchStr, 'g'), replaceStr);
      }

      grunt.file.write(replacePath, data, options.encoding);
    }
  });

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
        '*.js',
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
            aceModeSh: 'vendor/ace/mode-sh',
            aceModeText: 'vendor/ace/mode-text',
            aceThemeAmbiance: 'vendor/ace/theme-ambiance',
            aceThemeChrome: 'vendor/ace/theme-chrome',
            aceThemeGithub: 'vendor/ace/theme-github',
            aceThemeMonokai: 'vendor/ace/theme-monokai',
            aceThemeTwilight: 'vendor/ace/theme-twilight',
            backbone: 'vendor/backbone/backbone.min',
            bootstrap: 'vendor/bootstrap/bootstrap.min',
            d3: 'vendor/d3/d3.min',
            jquery: 'vendor/jquery/jquery.min',
            less: 'vendor/less/less.min',
            qrcode: 'vendor/qrcode/qrcode.min',
            rickshaw: 'vendor/rickshaw/rickshaw.min',
            select: 'vendor/select/select.min',
            sjcl: 'vendor/sjcl/sjcl.min',
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
            aceModeSh: 'vendor/ace/mode-sh',
            aceModeText: 'vendor/ace/mode-text',
            aceThemeAmbiance: 'vendor/ace/theme-ambiance',
            aceThemeChrome: 'vendor/ace/theme-chrome',
            aceThemeGithub: 'vendor/ace/theme-github',
            aceThemeMonokai: 'vendor/ace/theme-monokai',
            aceThemeTwilight: 'vendor/ace/theme-twilight',
            backbone: 'vendor/backbone/backbone.min',
            bootstrap: 'vendor/bootstrap/bootstrap.min',
            d3: 'vendor/d3/d3.min',
            jquery: 'vendor/jquery/jquery.min',
            less: 'vendor/less/less.min',
            qrcode: 'vendor/qrcode/qrcode.min',
            rickshaw: 'vendor/rickshaw/rickshaw.min',
            select: 'vendor/select/select.min',
            sjcl: 'vendor/sjcl/sjcl.min',
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
            aceModeSh: 'vendor/ace/mode-sh',
            aceModeText: 'vendor/ace/mode-text',
            aceThemeAmbiance: 'vendor/ace/theme-ambiance',
            aceThemeChrome: 'vendor/ace/theme-chrome',
            aceThemeGithub: 'vendor/ace/theme-github',
            aceThemeMonokai: 'vendor/ace/theme-monokai',
            aceThemeTwilight: 'vendor/ace/theme-twilight',
            backbone: 'vendor/backbone/backbone.min',
            bootstrap: 'vendor/bootstrap/bootstrap.min',
            d3: 'vendor/d3/d3.min',
            jquery: 'vendor/jquery/jquery.min',
            less: 'vendor/less/less.min',
            qrcode: 'vendor/qrcode/qrcode.min',
            rickshaw: 'vendor/rickshaw/rickshaw.min',
            select: 'vendor/select/select.min',
            sjcl: 'vendor/sjcl/sjcl.min',
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
          'vendor/dist/css/main.css': 'styles/main.less'
        }
      }
    },

    copy: {
      dist: {
        files: {
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
          'vendor/dist/favicon.ico': 'img/favicon.ico',
          'vendor/dist/robots.txt': 'root/robots.txt',
          'vendor/dist/index.html': 'root/index.html'
        }
      },
      demo: {
        files: {
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
          'vendor/dist/favicon.ico': 'img/favicon.ico',
          'vendor/dist/index.html': 'root/demo_index.html'
        }
      }
    },

    versioning: {
      all: {
        staticFiles: [
          'vendor/dist/css/main.css',
          'vendor/dist/js/main.js',
        ],
        replaceFiles: [
          'vendor/dist/index.html'
        ],
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-requirejs');

  grunt.registerTask('default', ['jshint', 'clean',
    'requirejs:production', 'less', 'copy:dist', 'versioning']);

  grunt.registerTask('test', ['jshint', 'clean', 'requirejs:test',
    'less', 'copy:dist', 'versioning']);

  grunt.registerTask('demo', ['jshint', 'clean', 'requirejs:demo',
    'less', 'copy:demo', 'versioning']);

  grunt.registerTask('lint', ['jshint']);
};

ace.define("ace/theme/pritunl",["require","exports","module","ace/lib/dom"], function(require, exports, module) {

exports.isDark = false;
exports.cssClass = "ace-pritunl";
exports.cssText = ".ace-pritunl .ace_gutter {\
background: #ebebeb;\
color: #333;\
overflow : hidden;\
}\
.ace-pritunl .ace_print-margin {\
width: 1px;\
background: #e8e8e8;\
}\
.ace-pritunl {\
background-color: #FFFFFF;\
color: black;\
}\
.ace-pritunl .ace_cursor {\
color: black;\
}\
.ace-pritunl .ace_invisible {\
color: rgb(191, 191, 191);\
}\
.ace-pritunl .ace_constant.ace_buildin {\
color: rgb(88, 72, 246);\
}\
.ace-pritunl .ace_constant.ace_language {\
color: rgb(88, 92, 246);\
}\
.ace-pritunl .ace_constant.ace_library {\
color: rgb(6, 150, 14);\
}\
.ace-pritunl .ace_invalid {\
/* MODIFIED */\
color: rgb(197, 0, 0);\
}\
.ace-pritunl .ace_fold {\
}\
.ace-pritunl .ace_support.ace_function {\
color: rgb(60, 76, 114);\
}\
.ace-pritunl .ace_support.ace_constant {\
color: rgb(6, 150, 14);\
}\
.ace-pritunl .ace_support.ace_type,\
.ace-pritunl .ace_support.ace_class\
.ace-pritunl .ace_support.ace_other {\
color: rgb(109, 121, 222);\
}\
.ace-pritunl .ace_variable.ace_parameter {\
font-style:italic;\
color:#FD971F;\
}\
.ace-pritunl .ace_keyword.ace_operator {\
color: rgb(104, 118, 135);\
}\
.ace-pritunl .ace_comment {\
/* MODIFIED */\
color: #0059a6;\
}\
.ace-pritunl .ace_comment.ace_doc {\
color: #236e24;\
}\
.ace-pritunl .ace_comment.ace_doc.ace_tag {\
color: #236e24;\
}\
.ace-pritunl .ace_constant.ace_numeric {\
color: rgb(0, 0, 205);\
}\
.ace-pritunl .ace_variable {\
/* MODIFIED */\
color: rgb(202, 152, 4);\
}\
.ace-pritunl .ace_xml-pe {\
color: rgb(104, 104, 91);\
}\
.ace-pritunl .ace_entity.ace_name.ace_function {\
color: #0000A2;\
}\
.ace-pritunl .ace_heading {\
color: rgb(12, 7, 255);\
}\
.ace-pritunl .ace_list {\
color:rgb(185, 6, 144);\
}\
.ace-pritunl .ace_marker-layer .ace_selection {\
background: rgb(181, 213, 255);\
}\
.ace-pritunl .ace_marker-layer .ace_step {\
background: rgb(252, 255, 0);\
}\
.ace-pritunl .ace_marker-layer .ace_stack {\
background: rgb(164, 229, 101);\
}\
.ace-pritunl .ace_marker-layer .ace_bracket {\
margin: -1px 0 0 -1px;\
border: 1px solid rgb(192, 192, 192);\
}\
.ace-pritunl .ace_marker-layer .ace_active-line {\
background: rgba(0, 0, 0, 0.07);\
}\
.ace-pritunl .ace_gutter-active-line {\
background-color : #dcdcdc;\
}\
.ace-pritunl .ace_marker-layer .ace_selected-word {\
background: rgb(250, 250, 255);\
border: 1px solid rgb(200, 200, 250);\
}\
.ace-pritunl .ace_storage,\
.ace-pritunl .ace_keyword,\
.ace-pritunl .ace_meta.ace_tag {\
/* MODIFIED */\
color: rgb(34, 107, 46);\
}\
.ace-pritunl .ace_string.ace_regex {\
color: rgb(255, 0, 0)\
}\
.ace-pritunl .ace_string {\
color: #1A1AA6;\
}\
.ace-pritunl .ace_entity.ace_other.ace_attribute-name {\
color: #994409;\
}\
.ace-pritunl .ace_indent-guide {\
background: url(\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAACCAYAAACZgbYnAAAAE0lEQVQImWP4////f4bLly//BwAmVgd1/w11/gAAAABJRU5ErkJggg==\") right repeat-y;\
}\
.dark .ace-pritunl .ace_gutter {\
background: #25282c;\
color: #C5C8C6\
}\
.dark .ace-pritunl .ace_print-margin {\
width: 1px;\
background: #25282c\
}\
.dark .ace-pritunl {\
background-color: #1D1F21;\
color: #C5C8C6\
}\
.dark .ace-pritunl .ace_cursor {\
color: #AEAFAD\
}\
.dark .ace-pritunl .ace_marker-layer .ace_selection {\
background: #373B41\
}\
.dark .ace-pritunl.ace_multiselect .ace_selection.ace_start {\
box-shadow: 0 0 3px 0px #1D1F21;\
border-radius: 2px\
}\
.dark .ace-pritunl .ace_marker-layer .ace_step {\
background: rgb(102, 82, 0)\
}\
.dark .ace-pritunl .ace_marker-layer .ace_bracket {\
margin: -1px 0 0 -1px;\
border: 1px solid #4B4E55\
}\
.dark .ace-pritunl .ace_marker-layer .ace_active-line {\
background: #282A2E\
}\
.dark .ace-pritunl .ace_gutter-active-line {\
background-color: #282A2E\
}\
.dark .ace-pritunl .ace_marker-layer .ace_selected-word {\
border: 1px solid #373B41\
}\
.dark .ace-pritunl .ace_invisible {\
color: #4B4E55\
}\
.dark .ace-pritunl .ace_keyword,\
.dark .ace-pritunl .ace_meta,\
.dark .ace-pritunl .ace_storage,\
.dark .ace-pritunl .ace_storage.ace_type,\
.dark .ace-pritunl .ace_support.ace_type {\
/* MODIFIED */\
color: rgb(34, 107, 46);\
}\
.dark .ace-pritunl .ace_keyword.ace_operator {\
color: #8ABEB7\
}\
.dark .ace-pritunl .ace_constant.ace_character,\
.dark .ace-pritunl .ace_constant.ace_language,\
.dark .ace-pritunl .ace_constant.ace_numeric,\
.dark .ace-pritunl .ace_keyword.ace_other.ace_unit,\
.dark .ace-pritunl .ace_support.ace_constant,\
.dark .ace-pritunl .ace_variable.ace_parameter {\
color: #DE935F\
}\
.dark .ace-pritunl .ace_constant.ace_other {\
color: #CED1CF\
}\
.dark .ace-pritunl .ace_invalid {\
/* MODIFIED */\
color: rgb(197, 0, 0);\
}\
.dark .ace-pritunl .ace_invalid.ace_deprecated {\
color: #CED2CF;\
background-color: #B798BF\
}\
.dark .ace-pritunl .ace_fold {\
background-color: #81A2BE;\
border-color: #C5C8C6\
}\
.dark .ace-pritunl .ace_entity.ace_name.ace_function,\
.dark .ace-pritunl .ace_support.ace_function,\
.dark .ace-pritunl .ace_variable {\
color: #81A2BE\
}\
.dark .ace-pritunl .ace_support.ace_class,\
.dark .ace-pritunl .ace_support.ace_type {\
color: #F0C674\
}\
.dark .ace-pritunl .ace_heading,\
.dark .ace-pritunl .ace_markup.ace_heading,\
.dark .ace-pritunl .ace_string {\
color: #B5BD68\
}\
.dark .ace-pritunl .ace_entity.ace_name.ace_tag,\
.dark .ace-pritunl .ace_entity.ace_other.ace_attribute-name,\
.dark .ace-pritunl .ace_meta.ace_tag,\
.dark .ace-pritunl .ace_string.ace_regexp,\
.dark .ace-pritunl .ace_variable {\
/* MODIFIED */\
color: rgb(202, 152, 4);\
}\
.dark .ace-pritunl .ace_comment {\
/* MODIFIED */\
color: #0059a6;\
}\
.dark .ace-pritunl .ace_indent-guide {\
background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAACCAYAAACZgbYnAAAAEklEQVQImWNgYGBgYHB3d/8PAAOIAdULw8qMAAAAAElFTkSuQmCC) right repeat-y\
}\
";

var dom = require("../lib/dom");
dom.importCssString(exports.cssText, exports.cssClass);
});
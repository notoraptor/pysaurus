System.register(["./functions.js"], function (_export, _context) {
  "use strict";

  var formatString, FieldInfo, FieldMap, GroupPermission, FieldType, FIELD_MAP, SEARCH_TYPE_TITLE, PAGE_SIZES, VIDEO_DEFAULT_PAGE_SIZE, VIDEO_DEFAULT_PAGE_NUMBER, SOURCE_TREE, Characters;
  return {
    setters: [function (_functionsJs) {
      formatString = _functionsJs.formatString;
    }],
    execute: function () {
      _export("GroupPermission", GroupPermission = {
        FORBIDDEN: 0,
        ONLY_MANY: 1,
        ALL: 2
      });

      FieldType = {
        bool: 0,
        int: 1,
        float: 2,
        str: 3,
        sortable: 4,
        unsortable: 5
      };
      FieldInfo = class FieldInfo {
        /**
         * @param name {string}
         * @param title {string}
         * @param groupPermission {number}
         * @param fieldType {number}
         */
        constructor(name, title, groupPermission, fieldType) {
          this.name = name;
          this.title = title ? title : name.replace(/_/g, " ");
          this.groupPermission = groupPermission;
          this.fieldType = fieldType;
        }

        isForbidden() {
          return this.groupPermission === GroupPermission.FORBIDDEN;
        }

        isOnlyMany() {
          return this.groupPermission === GroupPermission.ONLY_MANY;
        }

        isAll() {
          return this.groupPermission === GroupPermission.ALL;
        }

        isString() {
          return this.fieldType === FieldType.str;
        }

        isSortable() {
          return this.fieldType !== FieldType.unsortable;
        }

      };
      FieldMap = class FieldMap {
        /**
         * @param fieldInfoList {Array.<FieldInfo>}
         */
        constructor(fieldInfoList) {
          this.list = fieldInfoList;
          this.allowed = [];
          this.sortable = [];
          this.fields = {};

          for (let fieldInfo of fieldInfoList) {
            if (this.fields.hasOwnProperty(fieldInfo.name)) throw new Error(formatString(PYTHON_LANG.error_duplicated_field, {
              name: fieldInfo.name
            }));
            this.fields[fieldInfo.name] = fieldInfo;

            if (!fieldInfo.isForbidden()) {
              this.allowed.push(fieldInfo);
              if (fieldInfo.isSortable()) this.sortable.push(fieldInfo);
            }
          }

          this.list.sort(FieldMap.compareFieldInfo);
          this.allowed.sort(FieldMap.compareFieldInfo);
        }
        /**
         * Comparison method for FieldInfo class.
         * @param f1 {FieldInfo}
         * @param f2 {FieldInfo}
         * @returns {number}
         */


        static compareFieldInfo(f1, f2) {
          return f1.title.localeCompare(f2.title) || f1.name.localeCompare(f2.name);
        }

      };

      _export("FIELD_MAP", FIELD_MAP = new FieldMap([new FieldInfo('audio_bit_rate', PYTHON_LANG.attr_audio_bit_rate, GroupPermission.ALL, FieldType.int), new FieldInfo('audio_codec', PYTHON_LANG.attr_audio_codec, GroupPermission.ALL, FieldType.str), new FieldInfo('audio_codec_description', PYTHON_LANG.attr_audio_codec_description, GroupPermission.ALL, FieldType.str), new FieldInfo('bit_depth', PYTHON_LANG.attr_bit_depth, GroupPermission.ALL, FieldType.int), new FieldInfo('container_format', PYTHON_LANG.attr_container_format, GroupPermission.ALL, FieldType.str), new FieldInfo('date', PYTHON_LANG.attr_date, GroupPermission.ONLY_MANY, FieldType.sortable), new FieldInfo('day', PYTHON_LANG.attr_day, GroupPermission.ALL, FieldType.str), new FieldInfo('disk', PYTHON_LANG.attr_disk, GroupPermission.ALL, FieldType.str), new FieldInfo('extension', PYTHON_LANG.attr_extension, GroupPermission.ALL, FieldType.str), new FieldInfo('file_size', PYTHON_LANG.attr_file_size, GroupPermission.ONLY_MANY, FieldType.int), new FieldInfo('file_title', PYTHON_LANG.attr_file_title, GroupPermission.ONLY_MANY, FieldType.str), new FieldInfo('file_title_numeric', PYTHON_LANG.attr_file_title_numerixc, GroupPermission.ONLY_MANY, FieldType.sortable), new FieldInfo('filename', PYTHON_LANG.attr_filename, GroupPermission.ONLY_MANY, FieldType.str), new FieldInfo('frame_rate', PYTHON_LANG.attr_frame_rate, GroupPermission.ALL, FieldType.float), new FieldInfo('height', PYTHON_LANG.attr_height, GroupPermission.ALL, FieldType.int), new FieldInfo('length', PYTHON_LANG.attr_length, GroupPermission.ONLY_MANY, FieldType.sortable), new FieldInfo('move_id', PYTHON_LANG.attr_move_id, GroupPermission.ONLY_MANY, FieldType.unsortable), new FieldInfo('properties', PYTHON_LANG.attr_properties, GroupPermission.FORBIDDEN, FieldType.unsortable), new FieldInfo('quality', PYTHON_LANG.attr_quality, GroupPermission.ONLY_MANY, FieldType.float), new FieldInfo('sample_rate', PYTHON_LANG.attr_sample_rate, GroupPermission.ALL, FieldType.int), new FieldInfo('similarity_id', PYTHON_LANG.attr_similarity_id, GroupPermission.ONLY_MANY, FieldType.unsortable), new FieldInfo('size', PYTHON_LANG.attr_size, GroupPermission.ONLY_MANY, FieldType.sortable), new FieldInfo('thumbnail_path', PYTHON_LANG.attr_thumbnail_path, GroupPermission.FORBIDDEN, FieldType.str), new FieldInfo('title', PYTHON_LANG.attr_title, GroupPermission.ONLY_MANY, FieldType.str), new FieldInfo('title_numeric', PYTHON_LANG.attr_title_numeric, GroupPermission.ONLY_MANY, FieldType.sortable), new FieldInfo('video_codec', PYTHON_LANG.attr_video_codec, GroupPermission.ALL, FieldType.str), new FieldInfo('video_codec_description', PYTHON_LANG.attr_video_codec_description, GroupPermission.ALL, FieldType.str), new FieldInfo('video_id', PYTHON_LANG.attr_video_id, GroupPermission.FORBIDDEN, FieldType.int), new FieldInfo('width', PYTHON_LANG.attr_width, GroupPermission.ALL, FieldType.int)]));

      _export("SEARCH_TYPE_TITLE", SEARCH_TYPE_TITLE = {
        exact: PYTHON_LANG.search_exact,
        and: PYTHON_LANG.search_and,
        or: PYTHON_LANG.search_or,
        id: PYTHON_LANG.search_id
      });

      _export("PAGE_SIZES", PAGE_SIZES = [1, 10, 20, 50, 100]);

      _export("VIDEO_DEFAULT_PAGE_SIZE", VIDEO_DEFAULT_PAGE_SIZE = PAGE_SIZES[PAGE_SIZES.length - 1]);

      _export("VIDEO_DEFAULT_PAGE_NUMBER", VIDEO_DEFAULT_PAGE_NUMBER = 0);

      _export("SOURCE_TREE", SOURCE_TREE = {
        unreadable: {
          not_found: false,
          found: false
        },
        readable: {
          not_found: {
            with_thumbnails: false,
            without_thumbnails: false
          },
          found: {
            with_thumbnails: false,
            without_thumbnails: false
          }
        }
      });

      _export("Characters", Characters = {
        CROSS: "\u2715",
        SETTINGS: "\u2630",
        ARROW_DOWN: "\u25BC",
        ARROW_UP: "\u25B2",
        SMART_ARROW_LEFT: "\u2B9C",
        SMART_ARROW_RIGHT: "\u2B9E",
        WARNING_SIGN: "\u26A0" // ⚠

      });
    }
  };
});
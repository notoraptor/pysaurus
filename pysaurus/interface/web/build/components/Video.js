System.register(["./MenuPack.js", "../dialogs/Dialog.js", "../forms/FormVideoEditProperties.js", "./Collapsable.js", "./MenuItem.js", "./Menu.js", "../utils/backend.js", "../utils/constants.js", "../language.js", "../forms/GenericFormRename.js"], function (_export, _context) {
  "use strict";

  var MenuPack, Dialog, FormVideoEditProperties, Collapsable, MenuItem, Menu, backend_error, python_call, Characters, LangContext, GenericFormRename, Video;

  function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

  /**
   * Generate class name for common value of videos grouped by similarity
   * @param value {boolean?}
   * @returns {string}
   */
  function cc(value) {
    return value === undefined ? "" : value ? "common-true" : "common-false";
  }

  _export("Video", void 0);

  return {
    setters: [function (_MenuPackJs) {
      MenuPack = _MenuPackJs.MenuPack;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_formsFormVideoEditPropertiesJs) {
      FormVideoEditProperties = _formsFormVideoEditPropertiesJs.FormVideoEditProperties;
    }, function (_CollapsableJs) {
      Collapsable = _CollapsableJs.Collapsable;
    }, function (_MenuItemJs) {
      MenuItem = _MenuItemJs.MenuItem;
    }, function (_MenuJs) {
      Menu = _MenuJs.Menu;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }, function (_utilsConstantsJs) {
      Characters = _utilsConstantsJs.Characters;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
    }, function (_formsGenericFormRenameJs) {
      GenericFormRename = _formsGenericFormRenameJs.GenericFormRename;
    }],
    execute: function () {
      _export("Video", Video = class Video extends React.Component {
        constructor(props) {
          super(props);
          this.openVideo = this.openVideo.bind(this);
          this.confirmDeletion = this.confirmDeletion.bind(this);
          this.deleteVideo = this.deleteVideo.bind(this);
          this.openContainingFolder = this.openContainingFolder.bind(this);
          this.copyMetaTitle = this.copyMetaTitle.bind(this);
          this.copyFileTitle = this.copyFileTitle.bind(this);
          this.copyFilePath = this.copyFilePath.bind(this);
          this.copyVideoID = this.copyVideoID.bind(this);
          this.renameVideo = this.renameVideo.bind(this);
          this.editProperties = this.editProperties.bind(this);
          this.onSelect = this.onSelect.bind(this);
          this.reallyDeleteVideo = this.reallyDeleteVideo.bind(this);
          this.confirmMove = this.confirmMove.bind(this);
          this.moveVideo = this.moveVideo.bind(this);
          this.dismissSimilarity = this.dismissSimilarity.bind(this);
          this.reallyDismissSimilarity = this.reallyDismissSimilarity.bind(this);
          this.resetSimilarity = this.resetSimilarity.bind(this);
          this.reallyResetSimilarity = this.reallyResetSimilarity.bind(this);
        }

        render() {
          return this.props.data.readable ? this.renderVideo() : this.renderVideoState();
        }

        renderVideo() {
          const data = this.props.data;
          const audio_bit_rate = Math.round(data.audio_bit_rate / 1000);
          data.extension = data.extension.toUpperCase();
          data.frame_rate = Math.round(data.frame_rate);
          data.quality = Math.round(data.quality * 100) / 100;
          const title = data.title;
          const file_title = data.file_title;
          const meta_title = title === file_title ? null : title;
          const hasThumbnail = data.with_thumbnails;
          const htmlID = `video-${data.video_id}`;
          const alreadyOpened = APP_STATE.videoHistory.has(data.filename);
          const common = this.props.groupDef && this.props.groupDef.common || {};
          const groupedBySimilarityID = this.props.groupDef && this.props.groupDef.field === "similarity_id";
          return /*#__PURE__*/React.createElement("div", {
            className: 'video horizontal' + (data.found ? ' found' : ' not-found')
          }, /*#__PURE__*/React.createElement("div", {
            className: "image p-2"
          }, hasThumbnail ? /*#__PURE__*/React.createElement("img", {
            alt: data.title,
            src: data.thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, this.context.text_no_thumbnail)), /*#__PURE__*/React.createElement("div", {
            className: "video-details horizontal flex-grow-1"
          }, this.renderProperties(), /*#__PURE__*/React.createElement("div", {
            className: "info p-2"
          }, /*#__PURE__*/React.createElement("div", {
            className: "name"
          }, /*#__PURE__*/React.createElement("div", {
            className: "options horizontal"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: `${Characters.SETTINGS}`
          }, data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openVideo
          }, this.context.action_open_file) : /*#__PURE__*/React.createElement("div", {
            className: "text-center bold"
          }, this.context.text_not_found), data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openContainingFolder
          }, this.context.action_open_containing_folder) : "", meta_title ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyMetaTitle
          }, this.context.action_copy_meta_title) : "", file_title ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyFileTitle
          }, this.context.action_copy_file_title) : "", /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyFilePath
          }, this.context.action_copy_path), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyVideoID
          }, this.context.action_copy_video_id), data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.renameVideo
          }, this.context.text_rename_video) : "", data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.moveVideo
          }, this.context.action_move_video_to_another_folder) : "", this.props.groupedByMoves && data.moves.length ? /*#__PURE__*/React.createElement(Menu, {
            title: "Confirm move to ..."
          }, data.moves.map((dst, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            className: "confirm-move",
            action: () => this.confirmMove(data.video_id, dst.video_id)
          }, /*#__PURE__*/React.createElement("code", null, dst.filename)))) : "", groupedBySimilarityID ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.dismissSimilarity
          }, this.context.action_dismiss_similarity) : "", data.similarity_id !== null ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.resetSimilarity
          }, this.context.action_reset_similarity) : "", /*#__PURE__*/React.createElement(MenuItem, {
            className: "red-flag",
            action: this.deleteVideo
          }, data.found ? this.context.text_delete_video : this.context.text_delete_entry)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            checked: this.props.selected,
            id: htmlID,
            onChange: this.onSelect
          }), "\xA0", /*#__PURE__*/React.createElement("label", {
            htmlFor: htmlID
          }, /*#__PURE__*/React.createElement("strong", {
            className: "title"
          }, data.title)))), data.title === data.file_title ? "" : /*#__PURE__*/React.createElement("div", {
            className: "file-title"
          }, /*#__PURE__*/React.createElement("em", null, data.file_title))), /*#__PURE__*/React.createElement("div", {
            className: 'filename-line' + (data.found ? "" : ' horizontal')
          }, data.found ? "" : /*#__PURE__*/React.createElement("div", {
            className: "prepend clickable",
            onClick: this.deleteVideo
          }, /*#__PURE__*/React.createElement("code", {
            className: "text-not-found"
          }, this.context.text_not_found_uppercase), /*#__PURE__*/React.createElement("code", {
            className: "text-delete"
          }, this.context.text_delete)), /*#__PURE__*/React.createElement("div", {
            className: `filename ${alreadyOpened ? "already-opened" : ""}`
          }, /*#__PURE__*/React.createElement("code", _extends({}, data.found ? {
            className: "clickable"
          } : {}, data.found ? {
            onClick: this.openVideo
          } : {}), data.filename))), /*#__PURE__*/React.createElement("div", {
            className: "format horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "prepend"
          }, /*#__PURE__*/React.createElement("code", {
            className: cc(common.extension)
          }, data.extension)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", {
            title: data.file_size,
            className: cc(common.size)
          }, data.size), " /", " ", /*#__PURE__*/React.createElement("span", {
            className: cc(common.container_format)
          }, data.container_format), " ", "(", /*#__PURE__*/React.createElement("span", {
            title: data.video_codec_description,
            className: cc(common.video_codec)
          }, data.video_codec), ",", " ", /*#__PURE__*/React.createElement("span", {
            title: data.audio_codec_description,
            className: cc(common.audio_codec)
          }, data.audio_codec), ")"), /*#__PURE__*/React.createElement("div", {
            className: "prepend"
          }, /*#__PURE__*/React.createElement("code", null, "Quality")), /*#__PURE__*/React.createElement("div", {
            className: cc(common.quality)
          }, /*#__PURE__*/React.createElement("strong", null, /*#__PURE__*/React.createElement("em", null, data.quality)), " %")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", {
            className: cc(common.width)
          }, data.width), " x", " ", /*#__PURE__*/React.createElement("strong", {
            className: cc(common.height)
          }, data.height), " @", " ", /*#__PURE__*/React.createElement("span", {
            className: cc(common.frame_rate)
          }, data.frame_rate, " ", this.context.suffix_fps), ",", " ", /*#__PURE__*/React.createElement("span", {
            className: cc(common.bit_depth)
          }, data.bit_depth, " ", this.context.text_bits), " |", " ", /*#__PURE__*/React.createElement("span", {
            className: cc(common.sample_rate)
          }, data.sample_rate, " ", this.context.suffix_hertz), ",", " ", /*#__PURE__*/React.createElement("span", {
            title: data.audio_bit_rate,
            className: cc(common.audio_bit_rate)
          }, audio_bit_rate, " ", this.context.suffix_kbps), " |", " ", /*#__PURE__*/React.createElement("strong", {
            className: cc(common.length)
          }, data.length), " | ", /*#__PURE__*/React.createElement("code", {
            className: cc(common.date)
          }, data.date)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, "Audio"), ": ", data.audio_languages.length ? data.audio_languages.join(", ") : "(none)", " |", " ", /*#__PURE__*/React.createElement("strong", null, "Subtitles"), ": ", data.subtitle_languages.length ? data.subtitle_languages.join(", ") : "(none)"), !groupedBySimilarityID ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, this.context.text_similarity_id, ":"), " ", /*#__PURE__*/React.createElement("code", null, data.similarity_id === null ? this.context.text_not_yet_compared : data.similarity_id === -1 ? this.context.text_no_similarities : data.similarity_id)) : "", this.props.groupedByMoves && data.moves.length === 1 ? /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: () => this.confirmMove(data.video_id, data.moves[0].video_id)
          }, /*#__PURE__*/React.createElement("strong", null, this.context.text_confirm_move_to, ":"), /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("code", null, data.moves[0].filename))) : "")));
        }

        renderVideoState() {
          const data = this.props.data;
          const errors = data.errors.slice();
          errors.sort();
          const alreadyOpened = APP_STATE.videoHistory.has(data.filename);
          return /*#__PURE__*/React.createElement("div", {
            className: 'video horizontal' + (data.found ? ' found' : ' not-found')
          }, /*#__PURE__*/React.createElement("div", {
            className: "image p-2"
          }, /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, this.context.text_no_thumbnail)), /*#__PURE__*/React.createElement("div", {
            className: "video-details horizontal flex-grow-1"
          }, /*#__PURE__*/React.createElement("div", {
            className: "info p-2"
          }, /*#__PURE__*/React.createElement("div", {
            className: "name"
          }, /*#__PURE__*/React.createElement("div", {
            className: "options horizontal"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: `${Characters.SETTINGS}`
          }, data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openVideo
          }, this.context.action_open_file) : /*#__PURE__*/React.createElement("div", {
            className: "text-center bold"
          }, this.context.text_not_found), data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openContainingFolder
          }, this.context.action_open_containing_folder) : "", /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyFileTitle
          }, this.context.action_copy_file_title), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyFilePath
          }, this.context.action_copy_path), data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.renameVideo
          }, this.context.text_rename_video) : "", /*#__PURE__*/React.createElement(MenuItem, {
            className: "red-flag",
            action: this.deleteVideo
          }, data.found ? this.context.text_delete_video : this.context.text_delete_entry)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", {
            className: "title"
          }, data.file_title)))), /*#__PURE__*/React.createElement("div", {
            className: 'filename-line' + (data.found ? "" : ' horizontal')
          }, data.found ? "" : /*#__PURE__*/React.createElement("div", {
            className: "prepend clickable",
            onClick: this.deleteVideo
          }, /*#__PURE__*/React.createElement("code", {
            className: "text-not-found"
          }, this.context.text_not_found_uppercase), /*#__PURE__*/React.createElement("code", {
            className: "text-delete"
          }, this.context.text_delete)), /*#__PURE__*/React.createElement("div", {
            className: `filename ${alreadyOpened ? "already-opened" : ""}`
          }, /*#__PURE__*/React.createElement("code", _extends({}, data.found ? {
            className: "clickable"
          } : {}, data.found ? {
            onClick: this.openVideo
          } : {}), data.filename))), /*#__PURE__*/React.createElement("div", {
            className: "format horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "prepend"
          }, /*#__PURE__*/React.createElement("code", null, data.extension)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", {
            title: data.file_size
          }, data.size)), " | ", /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("code", null, data.date))), /*#__PURE__*/React.createElement("div", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, this.context.text_video_unreadable, ":")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
            className: "property"
          }, errors.map((element, elementIndex) => /*#__PURE__*/React.createElement("span", {
            className: "value",
            key: elementIndex
          }, element.toString()))))))));
        }

        renderProperties() {
          const props = this.props.data.properties;
          const propDefs = this.props.propDefs;
          if (!propDefs.length) return "";
          return /*#__PURE__*/React.createElement("div", {
            className: "properties p-2"
          }, /*#__PURE__*/React.createElement("div", {
            className: "edit-properties clickable text-center mb-2",
            onClick: this.editProperties
          }, "PROPERTIES"), propDefs.map(def => {
            const name = def.name;
            const value = props.hasOwnProperty(name) ? props[name] : def.defaultValue;
            let noValue;
            if (def.multiple) noValue = !value.length;else noValue = def.type === "str" && !value;
            let printableValues = def.multiple ? value : [value];
            return noValue ? "" : /*#__PURE__*/React.createElement("div", {
              key: name,
              className: `property ${props.hasOwnProperty(name) ? "defined" : ""}`
            }, /*#__PURE__*/React.createElement(Collapsable, {
              title: name
            }, !noValue ? printableValues.map((element, elementIndex) => /*#__PURE__*/React.createElement("span", {
              className: "value clickable",
              key: elementIndex,
              onClick: () => this.props.onSelectPropertyValue(name, element)
            }, element.toString())) : /*#__PURE__*/React.createElement("span", {
              className: "no-value"
            }, this.context.text_no_value)));
          }));
        }

        openVideo() {
          python_call('open_video', this.props.data.video_id).then(() => {
            APP_STATE.videoHistory.add(this.props.data.filename);
            this.props.onInfo(this.context.status_opened.format({
              path: this.props.data.filename
            }));
          }).catch(error => {
            backend_error(error);
            this.props.onInfo(this.context.status_unable_to_open.format({
              path: this.props.data.filename
            }));
          });
        }

        editProperties() {
          const data = this.props.data;
          Fancybox.load( /*#__PURE__*/React.createElement(FormVideoEditProperties, {
            data: data,
            definitions: this.props.propDefs,
            onClose: properties => {
              python_call('set_video_properties', this.props.data.video_id, properties).then(() => this.props.onInfo(this.context.status_properties_updated.format({
                path: data.filename
              }), true)).catch(backend_error);
            }
          }));
        }

        confirmDeletion() {
          const filename = this.props.data.filename;
          const thumbnail_path = this.props.data.thumbnail_path;
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: this.context.form_title_confirm_delete_video,
            yes: this.context.text_delete,
            action: this.reallyDeleteVideo
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-delete-video text-center bold"
          }, this.context.form_head_confirm_delete_video.markdown(), /*#__PURE__*/React.createElement("div", {
            className: "details overflow-auto px-2 py-1"
          }, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, filename)), /*#__PURE__*/React.createElement("p", null, this.props.data.with_thumbnails ? /*#__PURE__*/React.createElement("img", {
            id: "thumbnail",
            alt: "No thumbnail available",
            src: thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, this.context.text_no_thumbnail)))));
        }

        dismissSimilarity() {
          const filename = this.props.data.filename;
          const thumbnail_path = this.props.data.thumbnail_path;
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: this.context.action_dismiss_similarity,
            yes: this.context.text_dismiss,
            action: this.reallyDismissSimilarity
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-delete-video text-center bold"
          }, /*#__PURE__*/React.createElement("h2", null, this.context.form_head_confirm_dismiss), /*#__PURE__*/React.createElement("div", {
            className: "details overflow-auto px-2 py-1"
          }, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, filename)), /*#__PURE__*/React.createElement("p", null, this.props.data.with_thumbnails ? /*#__PURE__*/React.createElement("img", {
            id: "thumbnail",
            alt: "No thumbnail available",
            src: thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, this.context.text_no_thumbnail)))));
        }

        resetSimilarity() {
          const filename = this.props.data.filename;
          const thumbnail_path = this.props.data.thumbnail_path;
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: this.context.action_reset_similarity,
            yes: this.context.text_reset,
            action: this.reallyResetSimilarity
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-delete-video text-center bold"
          }, this.context.form_content_reset_similarity.markdown(), /*#__PURE__*/React.createElement("div", {
            className: "details overflow-auto px-2 py-1"
          }, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, filename)), /*#__PURE__*/React.createElement("p", null, this.props.data.with_thumbnails ? /*#__PURE__*/React.createElement("img", {
            id: "thumbnail",
            alt: "No thumbnail available",
            src: thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, this.context.text_no_thumbnail)))));
        }

        deleteVideo() {
          if (this.props.data.found || this.props.confirmDeletion) this.confirmDeletion();else this.reallyDeleteVideo();
        }

        reallyDeleteVideo() {
          python_call('delete_video', this.props.data.video_id).then(() => this.props.onInfo(this.context.status_video_deleted.format({
            path: this.props.data.filename
          }), true)).catch(backend_error);
        }

        reallyDismissSimilarity() {
          python_call('dismiss_similarity', this.props.data.video_id).then(() => this.props.onInfo(this.context.status_video_similarity_cancelled.format({
            path: this.props.data.filename
          }), true)).catch(backend_error);
        }

        reallyResetSimilarity() {
          python_call('reset_similarity', this.props.data.video_id).then(() => this.props.onInfo(this.context.status_video_similarity_reset.format({
            path: this.props.data.filename
          }), true)).catch(backend_error);
        }

        openContainingFolder() {
          python_call('open_containing_folder', this.props.data.video_id).then(folder => {
            this.props.onInfo(this.context.status_opened_folder.format({
              path: folder
            }));
          }).catch(backend_error);
        }

        copyMetaTitle() {
          const text = this.props.data.title;
          python_call('clipboard', text).then(() => this.props.onInfo(this.context.status_copied_to_clipboard.format({
            text
          }))).catch(() => this.props.onInfo(this.context.status_cannot_copy_meta_title.format({
            text
          })));
        }

        copyFileTitle() {
          const text = this.props.data.file_title;
          python_call('clipboard', text).then(() => this.props.onInfo(this.context.status_copied_to_clipboard.format({
            text
          }))).catch(() => this.props.onInfo(this.context.status_cannot_copy_file_title.format({
            text
          })));
        }

        copyFilePath() {
          python_call('clipboard_video_path', this.props.data.video_id).then(() => this.props.onInfo(this.context.status_copied_to_clipboard.format({
            text: this.props.data.filename
          })).catch(() => this.props.onInfo(this.context.status_cannot_copy_file_path.format({
            text: this.props.data.filename
          }))));
        }

        copyVideoID() {
          python_call('clipboard', this.props.data.video_id).then(() => this.props.onInfo(this.context.status_copied_to_clipboard.format({
            text: this.props.data.video_id
          }))).catch(() => this.props.onInfo(this.context.status_cannot_copy_video_id.format({
            text: this.props.data.video_id
          })));
        }

        confirmMove(srcID, dstID) {
          python_call("set_video_moved", srcID, dstID).then(() => this.props.onInfo(this.context.status_moved.format({
            path: this.props.data.filename
          }), true)).catch(backend_error);
        }

        renameVideo() {
          const filename = this.props.data.filename;
          const title = this.props.data.file_title;
          Fancybox.load( /*#__PURE__*/React.createElement(GenericFormRename, {
            title: this.context.form_title_rename_video,
            header: this.context.text_rename_video,
            description: filename,
            data: title,
            onClose: newTitle => {
              python_call('rename_video', this.props.data.video_id, newTitle).then(() => this.props.onInfo(`Renamed: ${newTitle}`, true)).catch(backend_error);
            }
          }));
        }

        moveVideo() {
          python_call("select_directory", window.APP_STATE.latestMoveFolder).then(directory => {
            if (directory) {
              window.APP_STATE.latestMoveFolder = directory;
              this.props.onMove(this.props.data.video_id, directory);
            }
          }).catch(backend_error);
        }

        onSelect(event) {
          if (this.props.onSelect) {
            this.props.onSelect(this.props.data.video_id, event.target.checked);
          }
        }

      });

      Video.contextType = LangContext;
      Video.propTypes = {
        data: PropTypes.object.isRequired,
        propDefs: PropTypes.arrayOf(PropTypes.object).isRequired,
        groupDef: PropTypes.object.isRequired,
        confirmDeletion: PropTypes.bool,
        groupedByMoves: PropTypes.bool,
        selected: PropTypes.bool,
        // onSelect(videoID, selected)
        onSelect: PropTypes.func,
        // onSelectPropertyValue(propName, propVal)
        onSelectPropertyValue: PropTypes.func.isRequired,
        // onInfo(message: str, backendUpdated: bool)
        onInfo: PropTypes.func.isRequired,
        // onMove(videoID, directory)
        onMove: PropTypes.func.isRequired
      };
    }
  };
});
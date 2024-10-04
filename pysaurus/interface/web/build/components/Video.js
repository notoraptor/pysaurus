System.register(["../dialogs/Dialog.js", "../forms/FormVideoEditProperties.js", "../forms/GenericFormRename.js", "../language.js", "../utils/FancyboxManager.js", "../utils/backend.js", "../utils/constants.js", "../utils/globals.js", "./Collapsable.js", "./Menu.js", "./MenuItem.js", "./MenuPack.js"], function (_export, _context) {
  "use strict";

  var Dialog, FormVideoEditProperties, GenericFormRename, tr, Fancybox, backend_error, python_call, Characters, APP_STATE, Collapsable, Menu, MenuItem, MenuPack, Video;
  function _extends() { _extends = Object.assign ? Object.assign.bind() : function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }
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
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_formsFormVideoEditPropertiesJs) {
      FormVideoEditProperties = _formsFormVideoEditPropertiesJs.FormVideoEditProperties;
    }, function (_formsGenericFormRenameJs) {
      GenericFormRename = _formsGenericFormRenameJs.GenericFormRename;
    }, function (_languageJs) {
      tr = _languageJs.tr;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }, function (_utilsConstantsJs) {
      Characters = _utilsConstantsJs.Characters;
    }, function (_utilsGlobalsJs) {
      APP_STATE = _utilsGlobalsJs.APP_STATE;
    }, function (_CollapsableJs) {
      Collapsable = _CollapsableJs.Collapsable;
    }, function (_MenuJs) {
      Menu = _MenuJs.Menu;
    }, function (_MenuItemJs) {
      MenuItem = _MenuItemJs.MenuItem;
    }, function (_MenuPackJs) {
      MenuPack = _MenuPackJs.MenuPack;
    }],
    execute: function () {
      _export("Video", Video = class Video extends React.Component {
        constructor(props) {
          super(props);
          this.markAsRead = this.markAsRead.bind(this);
          this.openVideo = this.openVideo.bind(this);
          this.openVideoSurely = this.openVideoSurely.bind(this);
          this.confirmDeletion = this.confirmDeletion.bind(this);
          this.deleteVideo = this.deleteVideo.bind(this);
          this.openContainingFolder = this.openContainingFolder.bind(this);
          this.copyToClipboard = this.copyToClipboard.bind(this);
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
          const title = data.title;
          const file_title = data.file_title;
          const meta_title = title === file_title ? null : title;
          const hasThumbnail = data.with_thumbnails;
          const htmlID = `video-${data.video_id}`;
          const alreadyOpened = data.date != data.date_entry_opened;
          const common = this.props.groupDef && this.props.groupDef.common || {};
          const groupedBySimilarityID = this.props.groupDef && this.props.groupDef.field === "similarity_id";
          const errors = data.errors.slice();
          errors.sort();
          return /*#__PURE__*/React.createElement("div", {
            className: "video horizontal" + (data.found ? " found" : " not-found")
          }, /*#__PURE__*/React.createElement("div", {
            className: "image p-2"
          }, hasThumbnail ? /*#__PURE__*/React.createElement("img", {
            alt: data.title,
            src: data.thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, tr("no thumbnail"))), /*#__PURE__*/React.createElement("div", {
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
            action: this.markAsRead
          }, tr("Mark as read")) : "", data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openVideo
          }, tr("Open file")) : /*#__PURE__*/React.createElement("div", {
            className: "text-center"
          }, /*#__PURE__*/React.createElement("strong", null, tr("(not found)"))), data.found && window.PYTHON_HAS_RUNTIME_VLC ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openVideoSurely
          }, /*#__PURE__*/React.createElement("strong", null, /*#__PURE__*/React.createElement("em", null, tr("Open file from local server")))) : "", data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openContainingFolder
          }, tr("Open containing folder")) : "", meta_title ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyMetaTitle
          }, tr("Copy meta title")) : "", file_title ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyFileTitle
          }, tr("Copy file title")) : "", /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyFilePath
          }, tr("Copy path")), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyVideoID
          }, tr("Copy video ID")), data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.renameVideo
          }, tr("Rename video")) : "", data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.moveVideo
          }, tr("Move video to another folder ...")) : "", this.props.groupedByMoves && data.moves.length ? /*#__PURE__*/React.createElement(Menu, {
            title: "Confirm move to ..."
          }, data.moves.map((dst, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            className: "confirm-move",
            action: () => this.confirmMove(data.video_id, dst.video_id)
          }, /*#__PURE__*/React.createElement("code", null, dst.filename)))) : "", groupedBySimilarityID ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.dismissSimilarity
          }, tr("Dismiss similarity")) : "", data.similarity_id !== null ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.resetSimilarity
          }, tr("Reset similarity")) : "", /*#__PURE__*/React.createElement(MenuItem, {
            className: "red-flag",
            action: this.deleteVideo
          }, data.found ? tr("Delete video") : tr("Delete entry"))), /*#__PURE__*/React.createElement("div", {
            title: data.video_id
          }, /*#__PURE__*/React.createElement("input", {
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
            className: "filename-line" + (data.found ? "" : " horizontal")
          }, data.found ? "" : /*#__PURE__*/React.createElement("div", {
            className: "prepend clickable",
            onClick: this.deleteVideo
          }, /*#__PURE__*/React.createElement("code", {
            className: "text-not-found"
          }, tr("NOT FOUND")), /*#__PURE__*/React.createElement("code", {
            className: "text-delete"
          }, tr("DELETE"))), /*#__PURE__*/React.createElement("div", {
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
          }, data.size), " ", "/ ", /*#__PURE__*/React.createElement("span", {
            className: cc(common.container_format)
          }, data.container_format), " (", /*#__PURE__*/React.createElement("span", {
            title: data.video_codec_description,
            className: cc(common.video_codec)
          }, data.video_codec), ",", " ", /*#__PURE__*/React.createElement("span", {
            title: data.audio_codec_description,
            className: cc(common.audio_codec)
          }, data.audio_codec), ")"), /*#__PURE__*/React.createElement("div", {
            className: "prepend"
          }, /*#__PURE__*/React.createElement("code", null, "Bit rate")), /*#__PURE__*/React.createElement("div", {
            className: cc(common.bit_rate)
          }, /*#__PURE__*/React.createElement("strong", null, /*#__PURE__*/React.createElement("em", null, data.bit_rate, "/s")))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", {
            className: cc(common.length)
          }, data.length), " |", " ", /*#__PURE__*/React.createElement("strong", {
            className: cc(common.width)
          }, data.width), " x", " ", /*#__PURE__*/React.createElement("strong", {
            className: cc(common.height)
          }, data.height), " @", " ", /*#__PURE__*/React.createElement("span", {
            className: cc(common.frame_rate)
          }, data.frame_rate, " ", tr("fps")), ",", " ", /*#__PURE__*/React.createElement("span", {
            className: cc(common.bit_depth)
          }, data.bit_depth, " ", tr("bits")), " ", "|", " ", /*#__PURE__*/React.createElement("span", {
            className: cc(common.sample_rate)
          }, data.sample_rate, " ", tr("Hz"), " x ", data.audio_bits || "32?", " ", tr("bits"), " (", data.channels, " ", tr("channels"), ")"), ",", " ", /*#__PURE__*/React.createElement("span", {
            title: data.audio_bit_rate,
            className: cc(common.audio_bit_rate)
          }, audio_bit_rate, " ", tr("Kb/s"))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("code", {
            className: cc(common.date)
          }, data.date), " |", " ", /*#__PURE__*/React.createElement("em", null, "(entry)", " ", /*#__PURE__*/React.createElement("code", {
            className: cc(common.date_entry_modified)
          }, data.date_entry_modified)), " ", "|", " ", /*#__PURE__*/React.createElement("em", null, "(opened) ", /*#__PURE__*/React.createElement("code", {
            className: cc(common.date_entry_opened)
          }, data.date_entry_opened))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, "Audio"), ":", " ", data.audio_languages.length ? data.audio_languages.join(", ") : "(none)", " |", " ", /*#__PURE__*/React.createElement("strong", null, "Subtitles"), ":", " ", data.subtitle_languages.length ? data.subtitle_languages.join(", ") : "(none)"), errors.length ? /*#__PURE__*/React.createElement("div", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, "Errors:"), "\xA0"), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
            className: "property"
          }, errors.map((element, elementIndex) => /*#__PURE__*/React.createElement("span", {
            className: "value",
            key: elementIndex
          }, element.toString()))))) : "", !groupedBySimilarityID ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, tr("Similarity ID"), ":"), " ", /*#__PURE__*/React.createElement("code", null, data.similarity_id === null ? tr("(not yet compared)") : data.similarity_id === -1 ? tr("(no similarities)") : data.similarity_id)) : "", this.props.groupedByMoves && data.moves.length === 1 ? /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: () => this.confirmMove(data.video_id, data.moves[0].video_id)
          }, /*#__PURE__*/React.createElement("strong", null, tr("Confirm move to"), ":"), /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("code", null, data.moves[0].filename))) : "")));
        }
        renderVideoState() {
          const data = this.props.data;
          const errors = data.errors.slice();
          errors.sort();
          const alreadyOpened = APP_STATE.videoHistory.has(data.filename);
          return /*#__PURE__*/React.createElement("div", {
            className: "video horizontal" + (data.found ? " found" : " not-found")
          }, /*#__PURE__*/React.createElement("div", {
            className: "image p-2"
          }, /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, tr("no thumbnail"))), /*#__PURE__*/React.createElement("div", {
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
          }, tr("Open file")) : /*#__PURE__*/React.createElement("div", {
            className: "text-center"
          }, /*#__PURE__*/React.createElement("strong", null, tr("(not found)"))), data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openContainingFolder
          }, tr("Open containing folder")) : "", /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyFileTitle
          }, tr("Copy file title")), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyFilePath
          }, tr("Copy path")), data.found ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.renameVideo
          }, tr("Rename video")) : "", /*#__PURE__*/React.createElement(MenuItem, {
            className: "red-flag",
            action: this.deleteVideo
          }, data.found ? tr("Delete video") : tr("Delete entry"))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", {
            className: "title"
          }, data.file_title)))), /*#__PURE__*/React.createElement("div", {
            className: "filename-line" + (data.found ? "" : " horizontal")
          }, data.found ? "" : /*#__PURE__*/React.createElement("div", {
            className: "prepend clickable",
            onClick: this.deleteVideo
          }, /*#__PURE__*/React.createElement("code", {
            className: "text-not-found"
          }, tr("NOT FOUND")), /*#__PURE__*/React.createElement("code", {
            className: "text-delete"
          }, tr("DELETE"))), /*#__PURE__*/React.createElement("div", {
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
          }, data.size)), " | ", /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("code", null, data.date)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("em", null, "(entry) ", /*#__PURE__*/React.createElement("code", null, data.date_entry_modified)), " ", "|", " ", /*#__PURE__*/React.createElement("em", null, "(opened) ", /*#__PURE__*/React.createElement("code", null, data.date_entry_opened)))), /*#__PURE__*/React.createElement("div", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, tr("Video unreadable"), ":")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
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
            const printableValues = props.hasOwnProperty(name) ? props[name] : def.defaultValues;
            const noValue = !printableValues.length || printableValues.length === 1 && printableValues[0] === "";
            return noValue ? "" : /*#__PURE__*/React.createElement("div", {
              key: name,
              className: `property ${props.hasOwnProperty(name) ? "defined" : ""}`
            }, /*#__PURE__*/React.createElement(Collapsable, {
              title: name
            }, printableValues.map((element, elementIndex) => /*#__PURE__*/React.createElement("span", {
              className: "value clickable",
              key: elementIndex,
              onClick: () => this.props.onSelectPropertyValue(name, element)
            }, element.toString()))));
          }));
        }
        markAsRead() {
          python_call("mark_as_read", this.props.data.video_id).then(() => {
            APP_STATE.videoHistory.add(this.props.data.filename);
            this.props.onInfo(tr("Marked as read: {path}", {
              path: this.props.data.filename
            }), true);
          }).catch(error => {
            backend_error(error);
            this.props.onInfo(tr("Unable to mark as read: {path}", {
              path: this.props.data.filename
            }));
          });
        }
        openVideo() {
          python_call("open_video", this.props.data.video_id).then(() => {
            APP_STATE.videoHistory.add(this.props.data.filename);
            this.props.onInfo(tr("Opened: {path}", {
              path: this.props.data.filename
            }), true);
          }).catch(error => {
            backend_error(error);
            this.props.onInfo(tr("Unable to open: {path}", {
              path: this.props.data.filename
            }));
          });
        }
        openVideoSurely() {
          python_call("open_from_server", this.props.data.video_id).then(url => {
            APP_STATE.videoHistory.add(this.props.data.filename);
            this.props.onInfo(tr("Opened: {path}", {
              path: url
            }), true);
          }).catch(error => {
            backend_error(error);
            this.props.onInfo(tr("Unable to open: {path}", {
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
              python_call("set_video_properties", this.props.data.video_id, properties).then(() => this.props.onInfo(tr("Properties updated: {path}", {
                path: data.filename
              }), true)).catch(backend_error);
            }
          }));
        }
        confirmDeletion() {
          const filename = this.props.data.filename;
          const thumbnail_path = this.props.data.thumbnail_path;
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: tr("Confirm deletion"),
            yes: tr("DELETE"),
            action: this.reallyDeleteVideo
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-delete-video text-center"
          }, tr("## Are you sure you want to !!definitely!! delete this video?", null, "markdown"), /*#__PURE__*/React.createElement("div", {
            className: "details overflow-auto px-2 py-1"
          }, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, filename)), /*#__PURE__*/React.createElement("p", null, this.props.data.with_thumbnails ? /*#__PURE__*/React.createElement("img", {
            id: "thumbnail",
            alt: "No thumbnail available",
            src: thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, tr("no thumbnail"))))));
        }
        dismissSimilarity() {
          const filename = this.props.data.filename;
          const thumbnail_path = this.props.data.thumbnail_path;
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: tr("Dismiss similarity"),
            yes: tr("dismiss"),
            action: this.reallyDismissSimilarity
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-delete-video text-center"
          }, /*#__PURE__*/React.createElement("h2", null, tr("Are you sure you want to dismiss similarity for this video?")), /*#__PURE__*/React.createElement("div", {
            className: "details overflow-auto px-2 py-1"
          }, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, filename)), /*#__PURE__*/React.createElement("p", null, this.props.data.with_thumbnails ? /*#__PURE__*/React.createElement("img", {
            id: "thumbnail",
            alt: "No thumbnail available",
            src: thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, tr("no thumbnail"))))));
        }
        resetSimilarity() {
          const filename = this.props.data.filename;
          const thumbnail_path = this.props.data.thumbnail_path;
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: tr("Reset similarity"),
            yes: tr("reset"),
            action: this.reallyResetSimilarity
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-delete-video text-center"
          }, tr(`
## Are you sure you want to reset similarity for this video?

### Video will then be re-compared at next similarity search
`, null, "markdown"), /*#__PURE__*/React.createElement("div", {
            className: "details overflow-auto px-2 py-1"
          }, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, filename)), /*#__PURE__*/React.createElement("p", null, this.props.data.with_thumbnails ? /*#__PURE__*/React.createElement("img", {
            id: "thumbnail",
            alt: "No thumbnail available",
            src: thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, tr("no thumbnail"))))));
        }
        deleteVideo() {
          if (this.props.data.found || this.props.confirmDeletion) this.confirmDeletion();else this.reallyDeleteVideo();
        }
        reallyDeleteVideo() {
          python_call("delete_video", this.props.data.video_id).then(() => this.props.onInfo(tr("Video deleted! {path}", {
            path: this.props.data.filename
          }), true)).catch(backend_error);
        }
        reallyDismissSimilarity() {
          python_call("set_similarities", [this.props.data.video_id], [-1]).then(() => this.props.onInfo(tr("Current similarity cancelled: {path}", {
            path: this.props.data.filename
          }), true)).catch(backend_error);
        }
        reallyResetSimilarity() {
          python_call("set_similarities", [this.props.data.video_id], [null]).then(() => this.props.onInfo(tr("Current similarity reset: {path}", {
            path: this.props.data.filename
          }), true)).catch(backend_error);
        }
        openContainingFolder() {
          python_call("open_containing_folder", this.props.data.video_id).then(folder => {
            this.props.onInfo(tr("Opened folder: {path}", {
              path: folder
            }));
          }).catch(backend_error);
        }
        copyMetaTitle() {
          this.copyToClipboard("title");
        }
        copyFileTitle() {
          this.copyToClipboard("file_title");
        }
        copyFilePath() {
          this.copyToClipboard("filename");
        }
        copyVideoID() {
          this.copyToClipboard("video_id");
        }
        copyToClipboard(field) {
          const text = this.props.data[field];
          python_call("clipboard", text).then(() => this.props.onInfo(tr("Copied to clipboard: {text}", {
            text
          }))).catch(() => this.props.onInfo(tr("Cannot copy {field} to clipboard: {text}", {
            field,
            text
          })));
        }
        confirmMove(srcID, dstID) {
          python_call("set_video_moved", srcID, dstID).then(() => this.props.onInfo(tr("Moved: {path}", {
            path: this.props.data.filename
          }), true)).catch(backend_error);
        }
        renameVideo() {
          const filename = this.props.data.filename;
          const title = this.props.data.file_title;
          Fancybox.load( /*#__PURE__*/React.createElement(GenericFormRename, {
            title: tr("Rename video"),
            header: tr("Rename video"),
            description: filename,
            data: title,
            onClose: newTitle => {
              python_call("rename_video", this.props.data.video_id, newTitle).then(() => this.props.onInfo(`Renamed: ${newTitle}`, true)).catch(backend_error);
            }
          }));
        }
        moveVideo() {
          python_call("select_directory", APP_STATE.latestMoveFolder).then(directory => {
            if (directory) {
              APP_STATE.latestMoveFolder = directory;
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
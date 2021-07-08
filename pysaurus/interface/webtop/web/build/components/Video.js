System.register(["./MenuPack.js", "../forms/FormVideoRename.js", "../dialogs/Dialog.js", "../forms/FormVideoProperties.js", "./Collapsable.js", "./MenuItem.js", "../utils/backend.js", "../utils/constants.js"], function (_export, _context) {
  "use strict";

  var MenuPack, FormVideoRename, Dialog, FormVideoProperties, Collapsable, MenuItem, backend_error, python_call, Characters, Video;

  _export("Video", void 0);

  return {
    setters: [function (_MenuPackJs) {
      MenuPack = _MenuPackJs.MenuPack;
    }, function (_formsFormVideoRenameJs) {
      FormVideoRename = _formsFormVideoRenameJs.FormVideoRename;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_formsFormVideoPropertiesJs) {
      FormVideoProperties = _formsFormVideoPropertiesJs.FormVideoProperties;
    }, function (_CollapsableJs) {
      Collapsable = _CollapsableJs.Collapsable;
    }, function (_MenuItemJs) {
      MenuItem = _MenuItemJs.MenuItem;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }, function (_utilsConstantsJs) {
      Characters = _utilsConstantsJs.Characters;
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
          this.renameVideo = this.renameVideo.bind(this);
          this.editProperties = this.editProperties.bind(this);
          this.onSelect = this.onSelect.bind(this);
          this.reallyDeleteVideo = this.reallyDeleteVideo.bind(this);
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
          const hasThumbnail = data.has_thumbnail;
          const htmlID = `video-${data.video_id}`;
          const alreadyOpened = APP_STATE.videoHistory.has(data.filename);
          return /*#__PURE__*/React.createElement("div", {
            className: 'video horizontal' + (data.exists ? ' found' : ' not-found')
          }, /*#__PURE__*/React.createElement("div", {
            className: "image"
          }, hasThumbnail ? /*#__PURE__*/React.createElement("img", {
            alt: data.title,
            src: data.thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, "no thumbnail")), /*#__PURE__*/React.createElement("div", {
            className: "video-details horizontal"
          }, this.renderProperties(), /*#__PURE__*/React.createElement("div", {
            className: "info"
          }, /*#__PURE__*/React.createElement("div", {
            className: "name"
          }, /*#__PURE__*/React.createElement("div", {
            className: "options horizontal"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: `${Characters.SETTINGS}`
          }, data.exists ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openVideo
          }, "Open file") : /*#__PURE__*/React.createElement("div", {
            className: "not-found"
          }, "(not found)"), data.exists ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openContainingFolder
          }, "Open containing folder") : '', meta_title ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyMetaTitle
          }, "Copy meta title") : '', file_title ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyFileTitle
          }, "Copy file title") : '', data.exists ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.renameVideo
          }, "Rename video") : '', /*#__PURE__*/React.createElement(MenuItem, {
            className: "menu-delete",
            action: this.deleteVideo
          }, data.exists ? 'Delete video' : 'Delete entry')), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            checked: this.props.selected,
            id: htmlID,
            onChange: this.onSelect
          }), "\xA0", /*#__PURE__*/React.createElement("label", {
            htmlFor: htmlID
          }, /*#__PURE__*/React.createElement("strong", {
            className: "title"
          }, data.title)))), data.title === data.file_title ? '' : /*#__PURE__*/React.createElement("div", {
            className: "file-title"
          }, /*#__PURE__*/React.createElement("em", null, data.file_title))), /*#__PURE__*/React.createElement("div", {
            className: 'filename-line' + (data.exists ? '' : ' horizontal')
          }, data.exists ? '' : /*#__PURE__*/React.createElement("div", {
            className: "prepend",
            onClick: this.deleteVideo
          }, /*#__PURE__*/React.createElement("code", {
            className: "text-not-found"
          }, "NOT FOUND"), /*#__PURE__*/React.createElement("code", {
            className: "text-delete"
          }, "DELETE")), /*#__PURE__*/React.createElement("div", {
            className: `filename ${alreadyOpened ? "already-opened" : ""}`
          }, /*#__PURE__*/React.createElement("code", data.exists ? {
            onClick: this.openVideo
          } : {}, data.filename))), /*#__PURE__*/React.createElement("div", {
            className: "format horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "prepend"
          }, /*#__PURE__*/React.createElement("code", null, data.extension)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", {
            title: data.file_size
          }, data.size), " / ", data.container_format, " ", "(", /*#__PURE__*/React.createElement("span", {
            title: data.video_codec_description
          }, data.video_codec), ",", " ", /*#__PURE__*/React.createElement("span", {
            title: data.audio_codec_description
          }, data.audio_codec), ")"), /*#__PURE__*/React.createElement("div", {
            className: "prepend"
          }, /*#__PURE__*/React.createElement("code", null, "Quality")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, /*#__PURE__*/React.createElement("em", null, data.quality)), " %")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, data.width), " x ", /*#__PURE__*/React.createElement("strong", null, data.height), " @", " ", data.frame_rate, " fps, ", data.bit_depth, " bits | ", data.sample_rate, " Hz,", " ", /*#__PURE__*/React.createElement("span", {
            title: data.audio_bit_rate
          }, audio_bit_rate, " Kb/s"), " |", " ", /*#__PURE__*/React.createElement("strong", null, data.length), " | ", /*#__PURE__*/React.createElement("code", null, data.date)))));
        }

        renderVideoState() {
          const data = this.props.data;
          const errors = data.errors.slice();
          errors.sort();
          const alreadyOpened = APP_STATE.videoHistory.has(data.filename);
          return /*#__PURE__*/React.createElement("div", {
            className: 'video horizontal' + (data.exists ? ' found' : ' not-found')
          }, /*#__PURE__*/React.createElement("div", {
            className: "image"
          }, /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, "no thumbnail")), /*#__PURE__*/React.createElement("div", {
            className: "video-details horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "info"
          }, /*#__PURE__*/React.createElement("div", {
            className: "name"
          }, /*#__PURE__*/React.createElement("div", {
            className: "options horizontal"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: `${Characters.SETTINGS}`
          }, data.exists ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openVideo
          }, "Open file") : /*#__PURE__*/React.createElement("div", {
            className: "not-found"
          }, "(not found)"), data.exists ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openContainingFolder
          }, "Open containing folder") : '', /*#__PURE__*/React.createElement(MenuItem, {
            action: this.copyFileTitle
          }, "Copy file title"), data.exists ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.renameVideo
          }, "Rename video") : '', /*#__PURE__*/React.createElement(MenuItem, {
            className: "menu-delete",
            action: this.deleteVideo
          }, data.exists ? 'Delete video' : 'Delete entry')), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", {
            className: "title"
          }, data.file_title)))), /*#__PURE__*/React.createElement("div", {
            className: 'filename-line' + (data.exists ? '' : ' horizontal')
          }, data.exists ? '' : /*#__PURE__*/React.createElement("div", {
            className: "prepend",
            onClick: this.deleteVideo
          }, /*#__PURE__*/React.createElement("code", {
            className: "text-not-found"
          }, "NOT FOUND"), /*#__PURE__*/React.createElement("code", {
            className: "text-delete"
          }, "DELETE")), /*#__PURE__*/React.createElement("div", {
            className: `filename ${alreadyOpened ? "already-opened" : ""}`
          }, /*#__PURE__*/React.createElement("code", data.exists ? {
            onClick: this.openVideo
          } : {}, data.filename))), /*#__PURE__*/React.createElement("div", {
            className: "format horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "prepend"
          }, /*#__PURE__*/React.createElement("code", null, data.extension)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", {
            title: data.file_size
          }, data.size)), " | ", /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("code", null, data.date))), /*#__PURE__*/React.createElement("div", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, "Video unreadable:")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
            className: "property"
          }, errors.map((element, elementIndex) => /*#__PURE__*/React.createElement("span", {
            className: "value",
            key: elementIndex
          }, element.toString()))))))));
        }

        renderProperties() {
          const props = this.props.data.properties;
          const propDefs = this.props.propDefs;
          if (!propDefs.length) return '';
          return /*#__PURE__*/React.createElement("div", {
            className: "properties"
          }, /*#__PURE__*/React.createElement("div", {
            className: "edit-properties",
            onClick: this.editProperties
          }, "PROPERTIES"), propDefs.map(def => {
            const name = def.name;
            const value = props.hasOwnProperty(name) ? props[name] : def.defaultValue;
            let noValue;
            if (def.multiple) noValue = !value.length;else noValue = def.type === "str" && !value;
            let printableValues = def.multiple ? value : [value];
            return noValue ? '' : /*#__PURE__*/React.createElement("div", {
              key: name,
              className: `property ${props.hasOwnProperty(name) ? "defined" : ""}`
            }, /*#__PURE__*/React.createElement(Collapsable, {
              title: name
            }, !noValue ? printableValues.map((element, elementIndex) => /*#__PURE__*/React.createElement("span", {
              className: "value",
              key: elementIndex,
              onClick: () => this.props.onSelectPropertyValue(name, element)
            }, element.toString())) : /*#__PURE__*/React.createElement("span", {
              className: "no-value"
            }, "no value")));
          }));
        }

        openVideo() {
          python_call('open_video', this.props.data.video_id).then(() => {
            APP_STATE.videoHistory.add(this.props.data.filename);
            this.props.onInfo('Opened: ' + this.props.data.filename);
          }).catch(() => this.props.onInfo('Unable to open: ' + this.props.data.filename));
        }

        editProperties() {
          const data = this.props.data;
          Fancybox.load( /*#__PURE__*/React.createElement(FormVideoProperties, {
            data: data,
            definitions: this.props.propDefs,
            onClose: properties => {
              python_call('set_video_properties', this.props.data.video_id, properties).then(() => this.props.onInfo(`Properties updated: ${data.filename}`, true)).catch(backend_error);
            }
          }));
        }

        confirmDeletion() {
          const filename = this.props.data.filename;
          const thumbnail_path = this.props.data.thumbnail_path;
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: "Confirm deletion",
            yes: "delete",
            action: this.reallyDeleteVideo
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-delete-video"
          }, /*#__PURE__*/React.createElement("h2", null, "Are you sure you want to ", /*#__PURE__*/React.createElement("strong", null, "definitely"), " delete this video?"), /*#__PURE__*/React.createElement("div", {
            className: "details"
          }, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, filename)), /*#__PURE__*/React.createElement("p", null, this.props.data.has_thumbnail ? /*#__PURE__*/React.createElement("img", {
            id: "thumbnail",
            alt: "No thumbnail available",
            src: thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, "no thumbnail")))));
        }

        deleteVideo() {
          if (this.props.data.exists || this.props.confirmDeletion) this.confirmDeletion();else this.reallyDeleteVideo();
        }

        reallyDeleteVideo() {
          python_call('delete_video', this.props.data.video_id).then(() => this.props.onInfo('Video deleted! ' + this.props.data.filename, true)).catch(backend_error);
        }

        openContainingFolder() {
          python_call('open_containing_folder', this.props.data.video_id).then(folder => {
            this.props.onInfo(`Opened folder: ${folder}`);
          }).catch(backend_error);
        }

        copyMetaTitle() {
          const text = this.props.data.title;
          python_call('clipboard', text).then(() => this.props.onInfo('Copied to clipboard: ' + text)).catch(() => this.props.onInfo(`Cannot copy meta title to clipboard: ${text}`));
        }

        copyFileTitle() {
          const text = this.props.data.file_title;
          python_call('clipboard', text).then(() => this.props.onInfo('Copied to clipboard: ' + text)).catch(() => this.props.onInfo(`Cannot copy file title to clipboard: ${text}`));
        }

        renameVideo() {
          const filename = this.props.data.filename;
          const title = this.props.data.file_title;
          Fancybox.load( /*#__PURE__*/React.createElement(FormVideoRename, {
            filename: filename,
            title: title,
            onClose: newTitle => {
              python_call('rename_video', this.props.data.video_id, newTitle).then(() => this.props.onInfo(`Renamed: ${newTitle}`, true)).catch(backend_error);
            }
          }));
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
        confirmDeletion: PropTypes.bool,
        selected: PropTypes.bool,
        // onSelect(videoID, selected)
        onSelect: PropTypes.func,
        // onSelectPropertyValue(propName, propVal)
        onSelectPropertyValue: PropTypes.func.isRequired,
        // onInfo(message: str, backendUpdated: bool)
        onInfo: PropTypes.func.isRequired
      };
    }
  };
});
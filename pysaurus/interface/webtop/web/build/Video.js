System.register(["./MenuPack.js", "./FormRenameVideo.js", "./Dialog.js", "./FormSetProperties.js", "./Collapsable.js"], function (_export, _context) {
  "use strict";

  var MenuPack, MenuItem, FormRenameVideo, Dialog, FormSetProperties, Collapsable, Video;

  _export("Video", void 0);

  return {
    setters: [function (_MenuPackJs) {
      MenuPack = _MenuPackJs.MenuPack;
      MenuItem = _MenuPackJs.MenuItem;
    }, function (_FormRenameVideoJs) {
      FormRenameVideo = _FormRenameVideoJs.FormRenameVideo;
    }, function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }, function (_FormSetPropertiesJs) {
      FormSetProperties = _FormSetPropertiesJs.FormSetProperties;
    }, function (_CollapsableJs) {
      Collapsable = _CollapsableJs.Collapsable;
    }],
    execute: function () {
      _export("Video", Video = class Video extends React.Component {
        constructor(props) {
          // parent
          // index
          // data
          // confirmDeletion: bool
          // selected: bool
          // onSelect(videoID, selected)
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
          this.focusPropertyValue = this.focusPropertyValue.bind(this);
        }

        render() {
          const index = this.props.index;
          const data = this.props.data;
          const audio_bit_rate = Math.round(data.audio_bit_rate / 1000);
          data.extension = data.extension.toUpperCase();
          data.frame_rate = Math.round(data.frame_rate);
          data.quality = Math.round(data.quality * 100) / 100;
          const title = data.title;
          const file_title = data.file_title;
          const meta_title = title === file_title ? null : title;
          const hasThumbnail = data.hasThumbnail;
          const htmlID = `video-${this.props.index}`;
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
            title: `${Utils.CHARACTER_SETTINGS}`
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
            className: "filename"
          }, /*#__PURE__*/React.createElement("code", data.exists ? {
            onClick: this.openVideo
          } : {}, data.filename))), /*#__PURE__*/React.createElement("div", {
            className: "format horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "prepend"
          }, /*#__PURE__*/React.createElement("code", null, data.extension)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", {
            title: data.file_size
          }, data.size), " / ", data.container_format, " (", /*#__PURE__*/React.createElement("span", {
            title: data.video_codec_description
          }, data.video_codec), ", ", /*#__PURE__*/React.createElement("span", {
            title: data.audio_codec_description
          }, data.audio_codec), ")"), /*#__PURE__*/React.createElement("div", {
            className: "prepend"
          }, /*#__PURE__*/React.createElement("code", null, "Quality")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, /*#__PURE__*/React.createElement("em", null, data.quality)), " %")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, data.width), " x ", /*#__PURE__*/React.createElement("strong", null, data.height), " @ ", data.frame_rate, " fps | ", data.sample_rate, " Hz, ", /*#__PURE__*/React.createElement("span", {
            title: data.audio_bit_rate
          }, audio_bit_rate, " Kb/s"), " | ", /*#__PURE__*/React.createElement("strong", null, data.length), " | ", /*#__PURE__*/React.createElement("code", null, data.date)))));
        }

        renderProperties() {
          const props = this.props.data.properties;
          const propDefs = this.props.parent.state.properties;
          if (!propDefs.length) return '';
          return /*#__PURE__*/React.createElement("div", {
            className: "properties"
          }, /*#__PURE__*/React.createElement("div", {
            className: "edit-properties",
            onClick: this.editProperties
          }, "PROPERTIES"), propDefs.map((def, index) => {
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
              onClick: () => this.focusPropertyValue(name, element)
            }, element.toString())) : /*#__PURE__*/React.createElement("span", {
              className: "no-value"
            }, "no value")));
          }));
        }

        focusPropertyValue(propertyName, propertyValue) {
          this.props.parent.focusPropertyValue(propertyName, propertyValue);
        }

        openVideo() {
          python_call('open_video', this.props.data.video_id).then(() => this.props.parent.updateStatus('Opened: ' + this.props.data.filename)).catch(() => this.props.parent.updateStatus('Unable to open: ' + this.props.data.filename));
        }

        editProperties() {
          const data = this.props.data;
          const definitions = this.props.parent.state.properties;
          this.props.parent.props.app.loadDialog('Edit video properties', onClose => /*#__PURE__*/React.createElement(FormSetProperties, {
            data: data,
            definitions: definitions,
            onClose: properties => {
              onClose();

              if (properties) {
                python_call('set_video_properties', this.props.data.video_id, properties).then(() => this.props.parent.updateStatus(`Properties updated: ${data.filename}`, true)).catch(backend_error);
              }
            }
          }));
        }

        confirmDeletion() {
          /*
          return view.dialog({
              url: 'html/delete.html',
              parameters: {filename: this.props.data.filename, thumbnail_path: this.props.data.thumbnail_path}}
          );
          */
          const filename = this.props.data.filename;
          const thumbnail_path = this.props.data.thumbnail_path;
          this.props.parent.props.app.loadDialog('Confirm deletion', onClose => /*#__PURE__*/React.createElement(Dialog, {
            yes: "delete",
            no: "cancel",
            onClose: yes => {
              onClose();
              if (yes) this.reallyDeleteVideo();
            }
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-delete-video"
          }, /*#__PURE__*/React.createElement("h2", null, "Are you sure you want to ", /*#__PURE__*/React.createElement("strong", null, "definitely"), " delete this video?"), /*#__PURE__*/React.createElement("div", {
            className: "details"
          }, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, filename)), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("img", {
            id: "thumbnail",
            alt: "No thumbnail available",
            src: thumbnail_path
          })))));
        }

        deleteVideo() {
          if (this.props.data.exists || this.props.confirmDeletion) this.confirmDeletion();else this.reallyDeleteVideo();
        }

        reallyDeleteVideo() {
          python_call('delete_video', this.props.data.video_id).then(() => this.props.parent.updateStatus('Video deleted! ' + this.props.data.filename, true)).catch(backend_error);
        }

        openContainingFolder() {
          python_call('open_containing_folder', this.props.data.video_id).then(folder => {
            this.props.parent.updateStatus(`Opened folder: ${folder}`);
          }).catch(backend_error);
        }

        copyMetaTitle() {
          const text = this.props.data.title;
          python_call('clipboard', text).then(() => this.props.parent.updateStatus('Copied to clipboard: ' + text)).catch(() => this.props.parent.updateStatus(`Cannot copy meta title to clipboard: ${text}`));
        }

        copyFileTitle() {
          const text = this.props.data.file_title;
          python_call('clipboard', text).then(() => this.props.parent.updateStatus('Copied to clipboard: ' + text)).catch(() => this.props.parent.updateStatus(`Cannot copy file title to clipboard: ${text}`));
        }

        renameVideo() {
          const filename = this.props.data.filename;
          const title = this.props.data.file_title;
          this.props.parent.props.app.loadDialog('Rename', onClose => /*#__PURE__*/React.createElement(FormRenameVideo, {
            filename: filename,
            title: title,
            onClose: newTitle => {
              onClose();

              if (newTitle) {
                python_call('rename_video', this.props.data.video_id, newTitle).then(() => this.props.parent.updateStatus(`Renamed: ${newTitle}`, true)).catch(backend_error);
              }
            }
          }));
        }

        onSelect(event) {
          if (this.props.onSelect) {
            this.props.onSelect(this.props.data.video_id, event.target.checked);
          }
        }

      });
    }
  };
});
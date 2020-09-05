System.register(["./MenuPack.js", "./FormRenameVideo.js", "./Dialog.js", "./FormSetProperties.js"], function (_export, _context) {
  "use strict";

  var MenuPack, MenuItem, FormRenameVideo, Dialog, FormSetProperties, ReadOnlyVideo;

  _export("ReadOnlyVideo", void 0);

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
    }],
    execute: function () {
      _export("ReadOnlyVideo", ReadOnlyVideo = class ReadOnlyVideo extends React.Component {
        constructor(props) {
          // index
          // data
          // propDefs
          super(props);
          this.openVideo = this.openVideo.bind(this);
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
          const hasThumbnail = data.hasThumbnail;
          return /*#__PURE__*/React.createElement("div", {
            className: 'video horizontal' + (index % 2 ? ' even' : ' odd') + (data.exists ? ' found' : ' not-found')
          }, /*#__PURE__*/React.createElement("div", {
            className: "image"
          }, hasThumbnail ? /*#__PURE__*/React.createElement("img", {
            alt: data.title,
            src: data.thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, "no thumbnail")), /*#__PURE__*/React.createElement("div", {
            className: "info"
          }, /*#__PURE__*/React.createElement("div", {
            className: "name"
          }, /*#__PURE__*/React.createElement("strong", {
            className: "title"
          }, data.title), data.title === data.file_title ? '' : /*#__PURE__*/React.createElement("div", {
            className: "file-title"
          }, /*#__PURE__*/React.createElement("em", null, data.file_title))), /*#__PURE__*/React.createElement("div", {
            className: 'filename-line' + (data.exists ? '' : ' horizontal')
          }, /*#__PURE__*/React.createElement("div", {
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
          }, audio_bit_rate, " Kb/s"), " | ", /*#__PURE__*/React.createElement("strong", null, data.length), " | ", /*#__PURE__*/React.createElement("code", null, data.date)), this.renderProperties()));
        }

        renderProperties() {
          const props = this.props.data.properties;
          const propDefs = this.props.propDefs;
          if (!propDefs.length) return '';
          return /*#__PURE__*/React.createElement("div", {
            className: "properties"
          }, /*#__PURE__*/React.createElement("div", {
            className: "table"
          }, propDefs.map((def, index) => {
            const name = def.name;
            const value = props.hasOwnProperty(name) ? props[name] : def.defaultValue;
            const valueString = propertyValueToString(def.type, def.multiple ? value.join(', ') : value.toString());
            return /*#__PURE__*/React.createElement("div", {
              key: name,
              className: "property table-row"
            }, /*#__PURE__*/React.createElement("div", {
              className: "table-cell property-name"
            }, /*#__PURE__*/React.createElement("strong", props.hasOwnProperty(name) ? {
              className: "defined"
            } : {}, name), ":"), /*#__PURE__*/React.createElement("div", {
              className: "table-cell"
            }, valueString ? /*#__PURE__*/React.createElement("span", null, valueString) : /*#__PURE__*/React.createElement("span", {
              className: "no-value"
            }, "no value")));
          })));
        }

        openVideo() {
          python_call('open_video_from_filename', this.props.data.filename).then(result => {
            if (result) this.props.parent.updateStatus('Opened: ' + this.props.data.filename);else this.props.parent.updateStatus('Unable to open: ' + this.props.data.filename);
          }).catch(backend_error);
        }

      });
    }
  };
});
System.register(["./buttons.js", "./constants.js", "./MenuPack.js", "./Pagination.js", "./ReadOnlyVideo.js", "./GroupView.js"], function (_export, _context) {
  "use strict";

  var SettingIcon, Cross, PAGE_SIZES, VIDEO_DEFAULT_PAGE_SIZE, VIDEO_DEFAULT_PAGE_NUMBER, MenuPack, MenuItem, Menu, MenuItemCheck, Pagination, ReadOnlyVideo, GroupView, ClassificationPage;

  _export("ClassificationPage", void 0);

  return {
    setters: [function (_buttonsJs) {
      SettingIcon = _buttonsJs.SettingIcon;
      Cross = _buttonsJs.Cross;
    }, function (_constantsJs) {
      PAGE_SIZES = _constantsJs.PAGE_SIZES;
      VIDEO_DEFAULT_PAGE_SIZE = _constantsJs.VIDEO_DEFAULT_PAGE_SIZE;
      VIDEO_DEFAULT_PAGE_NUMBER = _constantsJs.VIDEO_DEFAULT_PAGE_NUMBER;
    }, function (_MenuPackJs) {
      MenuPack = _MenuPackJs.MenuPack;
      MenuItem = _MenuPackJs.MenuItem;
      Menu = _MenuPackJs.Menu;
      MenuItemCheck = _MenuPackJs.MenuItemCheck;
    }, function (_PaginationJs) {
      Pagination = _PaginationJs.Pagination;
    }, function (_ReadOnlyVideoJs) {
      ReadOnlyVideo = _ReadOnlyVideoJs.ReadOnlyVideo;
    }, function (_GroupViewJs) {
      GroupView = _GroupViewJs.GroupView;
    }],
    execute: function () {
      _export("ClassificationPage", ClassificationPage = class ClassificationPage extends React.Component {
        parametersToState(parameters, state) {
          state.properties = parameters.properties;
          state.property = parameters.property;
          state.path = parameters.path;
          state.groups = parameters.groups;
          state.videos = parameters.videos;
        }

        constructor(props) {
          // parameters: {properties, property, path, groups, videos}
          // app: App
          super(props);
          this.state = {
            status: 'Loaded.',
            pageSize: VIDEO_DEFAULT_PAGE_SIZE,
            pageNumber: VIDEO_DEFAULT_PAGE_NUMBER,
            stackFilter: false,
            stackGroup: false,
            groupID: 0
          };
          this.parametersToState = this.parametersToState.bind(this);
          this.back = this.back.bind(this);
          this.changePage = this.changePage.bind(this);
          this.unstack = this.unstack.bind(this);
          this.showGroup = this.showGroup.bind(this);
          this.selectGroup = this.selectGroup.bind(this);
          this.resetStatus = this.resetStatus.bind(this);
          this.setPageSize = this.setPageSize.bind(this);
          this.scrollTop = this.scrollTop.bind(this);
          this.stackGroup = this.stackGroup.bind(this);
          this.stackFilter = this.stackFilter.bind(this);
          this.concatenatePath = this.concatenatePath.bind(this);
          this.parametersToState(this.props.parameters, this.state);
        }

        render() {
          const nbVideos = this.state.videos.length;
          const nbPages = Math.floor(nbVideos / this.state.pageSize) + (nbVideos % this.state.pageSize ? 1 : 0);
          const stringProperties = this.getStringProperties(this.state.properties);
          return /*#__PURE__*/React.createElement("div", {
            id: "videos",
            className: "classifier"
          }, /*#__PURE__*/React.createElement("header", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.back
          }, "\u2B9C"), /*#__PURE__*/React.createElement("strong", {
            className: "classifier-title"
          }, "Classifier for ", /*#__PURE__*/React.createElement("em", null, "\"", this.state.property, "\"")), /*#__PURE__*/React.createElement(MenuPack, {
            title: "Videos page size ..."
          }, PAGE_SIZES.map((count, index) => /*#__PURE__*/React.createElement(MenuItemCheck, {
            key: index,
            checked: this.state.pageSize === count,
            action: checked => {
              if (checked) this.setPageSize(count);
            }
          }, count, " video", count > 1 ? 's' : '', " per page"))), this.state.path.length > 1 && stringProperties.length ? /*#__PURE__*/React.createElement(MenuPack, {
            title: "Concatenate path into ..."
          }, stringProperties.map((def, i) => /*#__PURE__*/React.createElement(MenuItem, {
            key: i,
            action: () => this.concatenatePath(def.name)
          }, def.name))) : '', /*#__PURE__*/React.createElement("div", {
            className: "pagination"
          }, /*#__PURE__*/React.createElement(Pagination, {
            singular: "page",
            plural: "pages",
            nbPages: nbPages,
            pageNumber: this.state.pageNumber,
            key: this.state.pageNumber,
            onChange: this.changePage
          }))), /*#__PURE__*/React.createElement("div", {
            className: "frontier"
          }), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, /*#__PURE__*/React.createElement("div", {
            className: "side-panel"
          }, /*#__PURE__*/React.createElement("div", {
            className: "stack filter"
          }, /*#__PURE__*/React.createElement("div", {
            className: "stack-title",
            onClick: this.stackFilter
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, "Filter"), /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, this.state.stackFilter ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP)), this.state.stackFilter ? '' : /*#__PURE__*/React.createElement("div", {
            className: "stack-content"
          }, this.state.path.map((value, index) => /*#__PURE__*/React.createElement("div", {
            key: index,
            className: "path-step horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, value.toString()), index === this.state.path.length - 1 ? /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, /*#__PURE__*/React.createElement(Cross, {
            title: "unstack",
            action: this.unstack
          })) : '')))), /*#__PURE__*/React.createElement("div", {
            className: "stack group"
          }, /*#__PURE__*/React.createElement("div", {
            className: "stack-title",
            onClick: this.stackGroup
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, "Groups"), /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, this.state.stackGroup ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP)), this.state.stackGroup ? '' : /*#__PURE__*/React.createElement("div", {
            className: "stack-content"
          }, /*#__PURE__*/React.createElement(GroupView, {
            key: this.state.path.join('-'),
            groupID: this.state.groupID,
            field: `:${this.state.property}`,
            sorting: "field",
            reverse: false,
            groups: this.state.groups,
            onSelect: this.showGroup,
            onPlus: this.selectGroup
          })))), /*#__PURE__*/React.createElement("div", {
            className: "main-panel videos"
          }, this.renderVideos())), /*#__PURE__*/React.createElement("footer", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "footer-status",
            onClick: this.resetStatus
          }, this.state.status), /*#__PURE__*/React.createElement("div", {
            className: "footer-information"
          }, /*#__PURE__*/React.createElement("div", {
            className: "info group"
          }, "Group ", this.state.groupID + 1, "/", this.state.groups.length), /*#__PURE__*/React.createElement("div", {
            className: "info count"
          }, nbVideos, " video", nbVideos > 1 ? 's' : ''))));
        }

        renderVideos() {
          const start = this.state.pageSize * this.state.pageNumber;
          const end = Math.min(start + this.state.pageSize, this.state.videos.length);
          return this.state.videos.slice(start, end).map((data, index) => /*#__PURE__*/React.createElement(ReadOnlyVideo, {
            key: data.video_id,
            data: data,
            index: index,
            propDefs: this.state.properties,
            parent: this
          }));
        }

        back() {
          this.props.app.loadVideosPage();
        }

        changePage(pageNumber) {
          this.setState({
            pageNumber
          }, this.scrollTop);
        }

        unstack() {
          python_call('classifier_back', this.state.property, this.state.path).then(data => this.setState({
            groupID: 0,
            pageNumber: 0,
            path: data.path,
            groups: data.groups,
            videos: data.videos
          })).catch(backend_error);
        }

        showGroup(index) {
          python_call('classifier_show_group', index).then(data => this.setState({
            groupID: index,
            videos: data.videos
          })).catch(backend_error);
        }

        selectGroup(index) {
          python_call('classifier_select_group', this.state.property, this.state.path, index).then(data => this.setState({
            groupID: 0,
            pageNumber: 0,
            path: data.path,
            groups: data.groups,
            videos: data.videos
          })).catch(backend_error);
        }

        updateStatus(status) {
          this.setState({
            status
          });
        }

        resetStatus() {
          this.setState({
            status: "Ready."
          });
        }

        setPageSize(count) {
          if (count !== this.state.pageSize) this.setState({
            pageSize: count,
            pageNumber: 0
          }, this.scrollTop);
        }

        scrollTop() {
          const videos = document.querySelector('#videos .videos');
          videos.scrollTop = 0;
        }

        stackGroup() {
          this.setState({
            stackGroup: !this.state.stackGroup
          });
        }

        stackFilter() {
          this.setState({
            stackFilter: !this.state.stackFilter
          });
        }

        concatenatePath(outputPropertyName) {
          python_call('classifier_concatenate_path', this.state.path, this.state.property, outputPropertyName).then(data => this.setState({
            groupID: 0,
            pageNumber: 0,
            path: [],
            groups: data.groups,
            videos: data.videos
          })).catch(backend_error);
        }

        getStringProperties(definitions) {
          const properties = [];

          for (let def of definitions) {
            if (def.type === "str" && def.name !== this.state.property) properties.push(def);
          }

          return properties;
        }

      });
    }
  };
});

class GuiTree {
    // ==== JavaSscript User interface Structure ====
    // tag str
    // classees str || [str]
    // id str
    // codeId str
    // title str
    // text str XOR children
    // children [template]
    // input: type str
    // input: name str
    // input: value str
    // label: htmlFor str

    static parse(tree, domIndexed, codeIndexed) {
        const element = document.createElement((tree.tag && tree.tag.toLowerCase()) || 'div');
        if (!domIndexed)
            domIndexed = {};
        if (!codeIndexed)
            codeIndexed = {};
        if (tree.classes) {
            if (tree.classes.constructor === String) {
                element.className = tree.classes;
            } else if (tree.classes.constructor === Array) {
                element.classList.add.apply(element.classList, tree.classes);
            }
        }
        if (tree.id) {
            element.id = tree.id;
            if (domIndexed.hasOwnProperty(tree.id))
                throw new Error(`Duplicated ID: ${tree.id}`);
            domIndexed[tree.id] = element;
        }
        if (tree.codeId) {
            if (codeIndexed.hasOwnProperty(tree.codeId))
                throw new Error(`Duplicated code ID: ${tree.codeId}`);
            codeIndexed[tree.codeId] = element;
        }
        if (tree.title)
            element.title = tree.title;
        if (element.tagName === 'input') {
            if (tree.type)
                element.type = tree.type;
            if (tree.name)
                element.name = tree.name;
            if (tree.value)
                element.value = tree.value;
        } else if (element.tagName === 'label') {
            if (tree.htmlFor) {
                element.htmlFor = tree.htmlFor;
            }
        }
        if (tree.text) {
            if (tree.children)
                throw new Error(`Text and children are mutually exclusive.`);
            element.textContent = tree.text;
        }
        if (tree.children) {
            for (let child of tree.children) {
                const structure = GuiTree.parse(child, domIndexed, codeIndexed);
                element.appendChild(structure.root);
            }
        }
        return {root: element, dom: domIndexed, code: codeIndexed};
    }
}

class FancyBox {

    static onClose(fancyBox) {
        document.getElementById('page').removeChild(fancyBox);
    }

    static functionOnClose(fancyBox, onClose) {
        return () => {
            if (onClose)
                onClose();
            FancyBox.onClose(fancyBox);
        };
    }

    static preventPropagation(event) {
        if (!event)
            event = window.event;
        if (event.hasOwnProperty('cancelBubble'))
            event.cancelBubble = true;
        if (event.stopPropagation)
            event.stopPropagation();
    }

    static load(title, loader, onClose) {
        const gui = GuiTree.parse({
            codeId: 'wrapper',
            classes: 'fancy-box',
            children: [{
                codeId: 'container',
                classes: ['container', 'd-flex', 'flex-column'],
                children: [
                    {
                        codeId: 'rowHeader',
                        classes: ['row', 'fancy-header'],
                        children: [
                            {
                                codeId: 'boxTitle',
                                classes: ['col-sm-11', 'align-self-center', 'text-sm-left', 'fancy-title'],
                                text: title
                            },
                            {
                                codeId: 'boxClose',
                                classes: ['col-sm', 'align-self-center', 'text-sm-right', 'fancy-box-close'],
                                children: [{
                                    tag: 'button',
                                    codeId: 'buttonClose',
                                    classes: ['btn', 'btn-danger', 'fancy-button-close'],
                                    text: '\u00D7'
                                }]
                            }
                        ]
                    },
                    {
                        classes: ['row', 'flex-grow-1', 'd-flex', 'flex-column'],
                        children: [{
                            codeId: 'rowContent',
                            classes: ['col', 'fancy-content', 'flex-grow-1', 'd-flex', 'flex-column']
                        }]
                    }
                ]
            }]
        });
        const fnOnClose = FancyBox.functionOnClose(gui.code.wrapper, onClose);
        gui.code.wrapper.onclick = fnOnClose;
        gui.code.container.onclick = FancyBox.preventPropagation;
        gui.code.buttonClose.onclick = fnOnClose;
        if (loader)
            gui.code.rowContent.appendChild(loader(fnOnClose));
        document.getElementById('page').appendChild(gui.root);
    }
}

class FileBox {
    static _on_click_folder(parentDirectory, localPath, gui) {
        console.log(`Clicked on folder ${localPath}`);
        const newPath = `${parentDirectory}/${localPath}`;
        Pysaurus.open_folder(newPath, (result) => {
            gui.code.labelFolder.textContent = result.error ? newPath : result.folder;
            const list = gui.code.list;
            gui.code.buttonUp.onclick = () => FileBox._on_click_folder(result.error ? parentDirectory : result.folder, result.error ? '' : '..', gui);
            while (list.firstChild) {
                list.removeChild(list.firstChild);
            }
            if (result.error) {
                const elementGui = GuiTree.parse({
                    classes: ['empty'],
                    text: `Erreur: ${result.error}`
                });
                list.appendChild(elementGui.root);
            } else if (result.contentPage) {
                for (let pathDesc of result.contentPage) {
                    const path = pathDesc[0];
                    const isDirectory = pathDesc[1];
                    const text = isDirectory ? `... ${path}` : `    ${path}`;
                    const className = isDirectory ? 'folder' : 'file';
                    const elementGui = GuiTree.parse({
                        classes: [className, 'entry'],
                        children: [
                            {classes: ['icon']},
                            {classes: ['path'], text: path}
                        ]
                    });
                    if (isDirectory) {
                        elementGui.root.onclick = () => FileBox._on_click_folder(result.folder, path, gui);
                    }
                    list.appendChild(elementGui.root);
                }
            } else {
                const elementGui = GuiTree.parse({
                    classes: ['empty'],
                    text: 'Ce dossier est vide'
                });
                list.appendChild(elementGui.root);
            }
        });
    }
    static _link() {

    }
    static load(folderData, onClose) {
        const gui = GuiTree.parse({
            classes: ['flex-grow-1', 'd-flex', 'flex-column', 'file-box'],
            children: [
                {
                    classes: ['file-header'],
                    children: [
                        {
                            tag: 'button',
                            codeId: 'buttonRoot',
                            classes: ['button-root'],
                            text: '|<-'
                        },
                        {
                            tag: 'button',
                            codeId: 'buttonUp',
                            classes: ['button-up'],
                            text: '<-'
                        },
                        {
                            codeId: 'labelFolder',
                            classes: ['label-folder'],
                        }
                    ]
                },
                {
                    classes: ['flex-grow-1', 'file-content', 'd-flex', 'flex-column'],
                    children: [
                        {
                            codeId: 'list',
                            classes: ['file-list', 'flex-grow-1', 'text-left']
                        },
                        {
                            codeId: 'pagination',
                            classes: ['pagination']
                        }
                    ]
                },
                {
                    classes: [],
                    children: [
                        {
                            tag: 'button',
                            codeId: 'buttonChoose',
                            classes: ['button-choose'],
                            text: 'choose'
                        },
                        {
                            tag: 'button',
                            codeId: 'buttonCancel',
                            classes: ['button-cancel'],
                            text: 'cancel'
                        }
                    ]
                }
            ]
        });
        gui.code.labelFolder.textContent = folderData.folder;
        const list = gui.code.list;
        gui.code.buttonRoot.onclick = () => FileBox._on_click_folder('', '', gui);
        gui.code.buttonUp.onclick = () => FileBox._on_click_folder(folderData.folder, '..', gui);
        if (folderData.contentPage) {
            for (let pathDesc of folderData.contentPage) {
                const path = pathDesc[0];
                const isDirectory = pathDesc[1];
                const className = isDirectory ? 'folder' : 'file';
                const elementGui = GuiTree.parse({
                    classes: [className, 'entry'],
                    children: [
                        {classes: ['icon']},
                        {classes: ['path'], text: path}
                    ]
                });
                if (isDirectory) {
                    elementGui.root.onclick = () => FileBox._on_click_folder(folderData.folder, path, gui);
                }
                list.appendChild(elementGui.root);
            }
        } else {
            const elementGui = GuiTree.parse({
                classes: ['empty'],
                text: 'Ce dossier est vide'
            });
            list.appendChild(elementGui.root);
        }
        gui.code.buttonCancel.onclick = onClose;
        return gui.root;
    }
}
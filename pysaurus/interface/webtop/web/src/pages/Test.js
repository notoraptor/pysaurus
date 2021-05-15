import {MenuPack} from "../components/MenuPack.js";
import {PAGE_SIZES} from "../utils/constants.js";
import {ComponentController, SetInput} from "../components/SetInput.js";
import {Dialog} from "../dialogs/Dialog.js";
import {Cross} from "../components/Cross.js";
import {MenuItem} from "../components/MenuItem.js";
import {MenuItemCheck} from "../components/MenuItemCheck.js";
import {Menu} from "../components/Menu.js";

export class Test extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            pageSize: PAGE_SIZES[0],
            confirmDeletion: false,
            arr: ['a', 'b', 'ccc']
        };
    }

    render() {
        const c = new ComponentController(this, 'arr');
        return (
            <div>
                <SetInput identifier="entry" controller={c} values={['my', 'name', 'is', 'Emninem']}/>
                <MenuPack title="Options">
                    <MenuItem shortcut="Ctrl+S" action={() => console.log('select videos')}>Select videos ...</MenuItem>
                    <MenuItem action={() => console.log('reload database')}>Reload database ...</MenuItem>
                    <MenuItem action={() => console.log('manage properties')}>Manage properties</MenuItem>
                    <Menu title="Page size ...">
                        <Menu title={"again"}>
                            <MenuItem>a</MenuItem>
                            <MenuItem>b</MenuItem>
                            <MenuItem>c</MenuItem>
                        </Menu>
                        {PAGE_SIZES.map((count, index) => (
                            <MenuItemCheck key={index}
                                           checked={this.state.pageSize === count}
                                           action={checked => {
                                               if (checked) this.setState({pageSize: count});
                                           }}>
                                {count} video{count > 1 ? 's' : ''} per page
                            </MenuItemCheck>
                        ))}
                    </Menu>
                    <MenuItemCheck checked={this.state.confirmDeletion}
                                   action={checked => this.setState({confirmDeletion: checked})}>
                        confirm deletion for entries not found
                    </MenuItemCheck>
                </MenuPack>
                Hello! <Cross action={() => console.log('cross!')}/>
                <a href="https://google.fr">yayayayayaya!</a>
                <input type="text"/>
                Hello! <button onClick={() => this.fancy()}>click here!</button>
            </div>
        );
    }

    fancy() {
        this.props.app.loadDialog("Test fancy box!", onClose => (
            <Dialog onClose={yes => {
                onClose();
                console.log(`Choice: ${yes ? 'yes' : 'no'}`);
            }}>
                <h1>hello world</h1>
                <h1>hello world</h1>
                <h1>hello world</h1>
                <h1>hello world</h1>
                <h1>hello world</h1>
                <h1>hello world</h1>
                <h1>hello world</h1>
                <h1>hello world</h1>
                <h1>hello world</h1>
                <h1>hello world</h1>
                <h1>hello world</h1>
            </Dialog>
        ))
    }
}
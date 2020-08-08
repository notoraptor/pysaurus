export class LikeButton extends React.Component {
    constructor(props) {
        super(props);
        this.state = { liked: false };
    }

    render() {
        python.get_name(name => python.print('Called from javascript:', name));
        if (this.state.liked) {
            return 'You liked this.';
        }
        return <button onClick={() => this.setState({liked: true})}>Like</button>;
    }
}
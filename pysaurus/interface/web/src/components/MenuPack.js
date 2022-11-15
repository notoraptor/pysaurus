export function MenuPack(props) {
	return (
		<div className="menu-pack clickable position-relative">
			<div className="title">
				<div className="text">{props.title}</div>
			</div>
			<div className="content">{props.children}</div>
		</div>
	);
}

MenuPack.propTypes = {
	title: PropTypes.string.isRequired,
};

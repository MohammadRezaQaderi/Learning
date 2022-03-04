import PropTypes from 'prop-types'
const Header = ({title}) => {
  return (
    <header>
        <h1 style={headerstyle}>{title}</h1>
    </header>
  )
}

Header.defaultProps = {
    title: 'Task Manager',
}

Header.prototype ={
    title: PropTypes.string,
}

const headerstyle = {
    color: 'red',
    backgroundColor: "black",
}
export default Header
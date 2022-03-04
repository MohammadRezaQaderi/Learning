import PropTypes from 'prop-types'
import Button from './Button.js'
const Header = ({title, onAdd, showAdd}) => {
  return (
    <header className='header'>
        <h1 >{title}</h1>
        <Button text={showAdd ? 'Close' : 'Add'} color={showAdd ? 'Red' : 'green'} onClick={onAdd} />
    </header>
  )
}

Header.defaultProps = {
    title: 'Task Manager',
}

Header.prototype ={
    title: PropTypes.string.isRequired,
}

// ccs in Js
// const headesrstyle = {
//     color: 'red',
//     backgroundColor: "black",
// }
export default Header
import PropTypes from 'prop-types'
import Button from './Button.js'
const Header = ({title}) => {
    const onClick =  () =>{
        
    }
  return (
    <header className='header'>
        <h1 >{title}</h1>
        <Button onClick={onClick} />
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
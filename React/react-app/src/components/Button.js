import PropTypes from 'prop-types'
const Button = ({color, text, onClick}) => {
    return <button onClick={onClick} style={{backgroundColor: color}} className='btn'>{text}</button>
}

Button.defaultProps = {
    color: 'black',
    text: 'Add',
}

Button.propType ={
    color: PropTypes.string,
    text: PropTypes.string,
    onClick: PropTypes.func.isRequired,
}
export default Button
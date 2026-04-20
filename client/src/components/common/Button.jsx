import React from 'react';
import styles from '../../styles/Button.module.scss';

const Button = ({ children, primary, secondary, onClick }) => {
  const buttonClass = primary ? styles.primary : 
                    secondary ? styles.secondary : 
                    styles.default;
  
  return (
    <button 
      className={`${styles.button} ${buttonClass}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

export default Button;
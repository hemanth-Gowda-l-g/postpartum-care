import React from 'react';
import styles from '../../styles/MentalHealth.module.scss';

const MentalHealth = () => {
  return (
    <div className={styles.container}>
      <h1>Mental Health Support</h1>
      <div className={styles.content}>
        <section className={styles.info}>
          <h2>Your Mental Health Journey</h2>
          <p>We're here to support you through your postpartum journey. Remember, it's okay to not be okay, and seeking help is a sign of strength.</p>
        </section>
        
        <section className={styles.resources}>
          <h2>Available Resources</h2>
          <ul>
            <li>Professional Counseling</li>
            <li>Support Groups</li>
            <li>Self-Care Tips</li>
            <li>Emergency Contacts</li>
          </ul>
        </section>
      </div>
    </div>
  );
};

export default MentalHealth; 
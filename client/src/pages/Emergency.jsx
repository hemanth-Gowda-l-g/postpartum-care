import React from 'react';
import styles from '../styles/Emergency.module.scss';

const Emergency = () => {
  const emergencyContacts = [
    {
      id: 1,
      title: 'All-in-one Emergency (ERSS)',
      number: '112',
      description: 'National Emergency Response Support System (India)',
      whenToCall: 'Call for police, fire, or medical emergencies requiring immediate response.'
    },
    {
      id: 2,
      title: 'Ambulance',
      number: '108',
      description: 'Emergency ambulance services (India, many states)',
      whenToCall: 'Call for urgent medical transport to the nearest hospital.'
    },
    {
      id: 3,
      title: 'Women Helpline',
      number: '1091',
      description: 'Women safety and support helpline (India)',
      whenToCall: 'Call for assistance in situations of threat, harassment, or violence.'
    },
    {
      id: 4,
      title: 'KIRAN Mental Health Helpline',
      number: '1800-599-0019',
      description: '24x7 national mental health helpline (MoHFW, India)',
      whenToCall: 'Call if you or someone you know is experiencing a mental health crisis or needs counseling.'
    },
    {
      id: 5,
      title: 'Childline',
      number: '1098',
      description: '24x7 emergency helpline for children (India)',
      whenToCall: 'Call for any emergency assistance related to children.'
    }
  ];

  const warningSigns = [
    {
      category: 'Physical Warning Signs',
      signs: [
        'Severe bleeding',
        'Difficulty breathing',
        'Chest pain',
        'High fever (above 100.4°F)',
        'Severe abdominal pain',
        'Seizures'
      ]
    },
    {
      category: 'Mental Health Warning Signs',
      signs: [
        'Thoughts of harming yourself or your baby',
        'Feeling disconnected from your baby',
        'Extreme anxiety or panic attacks',
        'Inability to sleep or sleeping too much',
        'Loss of appetite or overeating',
        'Feeling hopeless or worthless'
      ]
    }
  ];

  return (
    <div className={styles.emergencyContainer}>
      <h1>Emergency Resources</h1>
      
      {/* Emergency Contacts */}
      <section className={styles.emergencyContacts}>
        <h2>Emergency Contacts</h2>
        <div className={styles.contactGrid}>
          {emergencyContacts.map((contact) => (
            <div key={contact.id} className={styles.contactCard}>
              <h3>{contact.title}</h3>
              <a href={`tel:${contact.number.replace(/-/g, '')}`} className={styles.phoneNumber}>
                {contact.number}
              </a>
              <p className={styles.description}>{contact.description}</p>
              <p className={styles.whenToCall}>{contact.whenToCall}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Warning Signs */}
      <section className={styles.warningSigns}>
        <h2>Warning Signs to Watch For</h2>
        <div className={styles.signsGrid}>
          {warningSigns.map((category) => (
            <div key={category.category} className={styles.signsCard}>
              <h3>{category.category}</h3>
              <ul>
                {category.signs.map((sign, index) => (
                  <li key={index}>{sign}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Actions */}
      <section className={styles.quickActions}>
        <h2>Quick Actions</h2>
        <div className={styles.actionButtons}>
          <a href="tel:112" className={styles.emergencyButton}>
            Call 112 (ERSS)
          </a>
          <a href="tel:18005990019" className={styles.crisisButton}>
            Call KIRAN Mental Health
          </a>
          <a href="/resources" className={styles.resourcesButton}>
            View Resources
          </a>
        </div>
      </section>

      {/* Important Note */}
      <div className={styles.importantNote}>
        <p>
          <strong>Important:</strong> If you're experiencing a medical emergency in India, 
          call 112 immediately. Don't wait to seek help.
        </p>
      </div>
    </div>
  );
};

export default Emergency;
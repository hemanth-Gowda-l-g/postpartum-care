import React, { useState } from 'react';
import styles from '../styles/Resources.module.scss';

const Resources = () => {
  const [selectedCategory, setSelectedCategory] = useState('All');

  const categories = ['All', 'For Mothers', 'For Partners', 'For Family', 'Emergency'];

  const resources = [
    {
      id: 1,
      title: 'Postpartum Recovery Guide',
      description: 'A comprehensive guide to physical and emotional recovery after childbirth.',
      category: 'For Mothers',
      link: 'https://www.womenshealth.gov/pregnancy/childbirth-and-beyond/recovering-from-birth'
    },
    {
      id: 2,
      title: 'Partner Support Guide',
      description: 'How to support your partner during the postpartum period.',
      category: 'For Partners',
      link: 'https://www.postpartum.net/get-help/for-partners/'
    },
    {
      id: 3,
      title: 'Family Support Tips',
      description: 'Ways family members can help new parents during this transition.',
      category: 'For Family',
      link: 'https://www.helpguide.org/articles/parenting-family/helping-new-parents.htm'
    },
    {
      id: 4,
      title: 'Emergency Contacts',
      description: 'Important emergency numbers and when to call them.',
      category: 'Emergency',
      link: 'https://www.postpartum.net/get-help/emergency/'
    },
    {
      id: 5,
      title: 'Breastfeeding Support',
      description: 'Resources and tips for successful breastfeeding.',
      category: 'For Mothers',
      link: 'https://www.womenshealth.gov/breastfeeding'
    },
    {
      id: 6,
      title: 'Mental Health Resources',
      description: 'Support and information for postpartum mental health.',
      category: 'For Mothers',
      link: 'https://www.postpartum.net/get-help/'
    }
  ];

  const filteredResources = selectedCategory === 'All' 
    ? resources 
    : resources.filter(resource => resource.category === selectedCategory);

  return (
    <div className={styles.resourcesContainer}>
      <h1>Helpful Resources</h1>
      
      {/* Categories */}
      <div className={styles.categories}>
        {categories.map((category) => (
          <button
            key={category}
            className={`${styles.categoryButton} ${selectedCategory === category ? styles.active : ''}`}
            onClick={() => setSelectedCategory(category)}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Resources List */}
      <div className={styles.resourcesList}>
        {filteredResources.map((resource) => (
          <div key={resource.id} className={styles.resourceCard}>
            <h3>{resource.title}</h3>
            <p>{resource.description}</p>
            <a 
              href={resource.link} 
              target="_blank" 
              rel="noopener noreferrer"
              className={styles.resourceLink}
            >
              Learn More
            </a>
          </div>
        ))}
      </div>

      {/* Emergency Section */}
      <div className={styles.emergencySection}>
        <h2>Need Immediate Help?</h2>
        <p>If you're experiencing a mental health emergency, please call:</p>
        <div className={styles.emergencyNumbers}>
          <div className={styles.emergencyCard}>
            <h3>National Crisis Hotline</h3>
            <a href="tel:988">988</a>
          </div>
          <div className={styles.emergencyCard}>
            <h3>Postpartum Support International</h3>
            <a href="tel:18009447733">1-800-944-4773</a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Resources; 
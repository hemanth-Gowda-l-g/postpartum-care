import React from 'react';
import { ReactComponent as TrackerIcon } from '../../assets/icons/tracker.svg';
import { ReactComponent as MentalHealthIcon } from '../../assets/icons/mental-health.svg';
import { ReactComponent as LactationIcon } from '../../assets/icons/lactation.svg';
import { ReactComponent as NutritionIcon } from '../../assets/icons/nutrition.svg';
import styles from '../../styles/FeatureCard.module.scss';

const iconComponents = {
  tracker: TrackerIcon,
  'mental-health': MentalHealthIcon,
  lactation: LactationIcon,
  nutrition: NutritionIcon
};

const FeatureCard = ({ icon, title, description, link }) => {
  const IconComponent = iconComponents[icon];
  
  return (
    <div className={styles.featureCard}>
      <div className={styles.icon}>
        <IconComponent />
      </div>
      <h3>{title}</h3>
      <p>{description}</p>
      <a href={link} className={styles.learnMore}>Learn More →</a>
    </div>
  );
};

export default FeatureCard;
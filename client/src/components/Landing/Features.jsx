import React from 'react';
import FeatureCard from './FeatureCard';
import styles from '../../styles/Features.module.scss';

const features = [
  {
    icon: 'tracker',
    title: "Recovery Tracker",
    description: "Monitor your healing progress with daily check-ins",
    link: "/recovery"
  },
  {
    icon: 'mental-health',
    title: "Mental Health Hub",
    description: "Resources and tools for emotional wellbeing",
    link: "/mental-health"
  },
  {
    icon: 'lactation',
    title: "Ask a Lactation Expert",
    description: "Get answers to breastfeeding questions",
    link: "/experts"
  },
  {
    icon: 'nutrition',
    title: "Meal Delivery",
    description: "Nutritious meals tailored for postpartum recovery",
    link: "/nutrition"
  }
];

const Features = () => {
  return (
    <section className={styles.features}>
      <h2>Key Features</h2>
      <div className={styles.featuresGrid}>
        {features.map((feature, index) => (
          <FeatureCard 
            key={index}
            icon={feature.icon}
            title={feature.title}
            description={feature.description}
            link={feature.link}
          />
        ))}
      </div>
    </section>
  );
};

export default Features;
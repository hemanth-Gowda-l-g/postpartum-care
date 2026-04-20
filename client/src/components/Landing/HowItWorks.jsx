import React from 'react';
import { ReactComponent as AssessmentIcon } from '../../assets/icons/assessment.svg';
import { ReactComponent as PlanIcon } from '../../assets/icons/plan.svg';
import { ReactComponent as ConnectIcon } from '../../assets/icons/connect.svg';
import styles from '../../styles/HowItWorks.module.scss';

const HowItWorks = () => {
  const steps = [
    {
      icon: <AssessmentIcon />,
      title: "Take a Quick Assessment",
      description: "Answer a few questions about your delivery and health history"
    },
    {
      icon: <PlanIcon />,
      title: "Get Your Custom Plan",
      description: "Receive a personalized recovery plan tailored to your needs"
    },
    {
      icon: <ConnectIcon />,
      title: "Track & Connect",
      description: "Monitor progress and connect with experts when needed"
    }
  ];

  return (
    <section className={styles.howItWorks}>
      <h2>How It Works</h2>
      <div className={styles.steps}>
        {steps.map((step, index) => (
          <div key={index} className={styles.step}>
            <div className={styles.iconContainer}>
              {step.icon}
            </div>
            <h3>{step.title}</h3>
            <p>{step.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
};

export default HowItWorks;
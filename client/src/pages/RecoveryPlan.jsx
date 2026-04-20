import React from 'react';
import styles from '../styles/RecoveryPlan.module.scss';

const RecoveryPlan = () => {
  return (
    <div className={styles.recoveryPlan}>
      <h1>Your Recovery Plan</h1>
      <div className={styles.timeline}>
        <section className={styles.phase}>
          <h2>Week 1-2: Initial Recovery</h2>
          <div className={styles.tasks}>
            <div className={styles.task}>
              <h3>Physical Care</h3>
              <ul>
                <li>Rest as much as possible</li>
                <li>Take prescribed pain medication</li>
                <li>Keep incision area clean and dry</li>
              </ul>
            </div>
            <div className={styles.task}>
              <h3>Emotional Support</h3>
              <ul>
                <li>Accept help from family and friends</li>
                <li>Practice self-care activities</li>
                <li>Join support groups</li>
              </ul>
            </div>
          </div>
        </section>

        <section className={styles.phase}>
          <h2>Week 3-4: Building Strength</h2>
          <div className={styles.tasks}>
            <div className={styles.task}>
              <h3>Physical Activity</h3>
              <ul>
                <li>Start gentle walking</li>
                <li>Begin pelvic floor exercises</li>
                <li>Practice proper posture</li>
              </ul>
            </div>
            <div className={styles.task}>
              <h3>Nutrition</h3>
              <ul>
                <li>Stay hydrated</li>
                <li>Eat nutrient-rich foods</li>
                <li>Take prenatal vitamins</li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default RecoveryPlan;
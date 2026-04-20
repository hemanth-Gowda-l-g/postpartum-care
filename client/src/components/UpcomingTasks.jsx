import React from 'react';
import styles from '../styles/UpcomingTasks.module.scss';

const UpcomingTasks = () => {
  const tasks = [
    { id: 1, title: 'Take medication', time: '9:00 AM', completed: false },
    { id: 2, title: 'Doctor appointment', time: '2:00 PM', completed: false },
    { id: 3, title: 'Rest period', time: '4:00 PM', completed: false },
  ];

  return (
    <div className={styles.upcomingTasks}>
      <h2>Upcoming Tasks</h2>
      <div className={styles.taskList}>
        {tasks.map((task) => (
          <div key={task.id} className={styles.taskItem}>
            <div className={styles.taskInfo}>
              <h3>{task.title}</h3>
              <p>{task.time}</p>
            </div>
            <input
              type="checkbox"
              checked={task.completed}
              onChange={() => {}}
              className={styles.checkbox}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default UpcomingTasks; 
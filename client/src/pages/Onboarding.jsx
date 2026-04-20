import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
// import { motion, AnimatePresence } from 'framer-motion';
// import { FaBaby, FaCalendarAlt, FaVenusMars, FaUserAlt } from 'react-icons/fa';
// import { MdOutlineDeliveryDining } from 'react-icons/md';
import styles from '../styles/Onboarding.module.scss';

const Onboarding = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    deliveryType: '',
    dueDate: '',
    babyGender: '',
    babyName: ''
  });
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (step < 3) {
      setStep(step + 1);
    } else {
      // TODO: Save onboarding data
      navigate('/dashboard');
    }
  };

  // const steps = [
  //   {
  //     title: "Delivery Information",
  //     icon: <MdOutlineDeliveryDining className={styles.stepIcon} />,
  //     description: "Let's start with your delivery details"
  //   },
  //   {
  //     title: "Baby Information",
  //     icon: <FaBaby className={styles.stepIcon} />,
  //     description: "Tell us about your little one"
  //   },
  //   {
  //     title: "Final Details",
  //     icon: <FaUserAlt className={styles.stepIcon} />,
  //     description: "Almost there! Just a few more details"
  //   }
  // ];

  return (
    <div className={styles.onboardingContainer}>
      <div className={styles.onboardingContent}>
        {/* <motion.div 
          className={styles.header}
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1>Welcome to Your Postpartum Journey</h1>
          <p>Let's personalize your experience</p>
        </motion.div> */}

        {/* <div className={styles.progressContainer}>
          {steps.map((s, index) => (
            <motion.div
              key={index}
              className={`${styles.progressStep} ${step > index + 1 ? styles.completed : ''} ${step === index + 1 ? styles.active : ''}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.2 }}
            >
              <div className={styles.stepNumber}>{index + 1}</div>
              <div className={styles.stepInfo}>
                <h3>{s.title}</h3>
                <p>{s.description}</p>
              </div>
            </motion.div>
          ))}
        </div> */}

        {/* <AnimatePresence mode="wait"> */}
          <form
            // key={step}
            onSubmit={handleSubmit}
            className={styles.form}
            // initial={{ opacity: 0, x: 20 }}
            // animate={{ opacity: 1, x: 0 }}
            // exit={{ opacity: 0, x: -20 }}
            // transition={{ duration: 0.3 }}
          >
            {step === 1 && (
              <div
                // initial={{ opacity: 0 }}
                // animate={{ opacity: 1 }}
                // transition={{ delay: 0.2 }}
              >
                <div className={styles.formGroup}>
                  <label htmlFor="deliveryType">
                    {/* <MdOutlineDeliveryDining className={styles.inputIcon} /> */}
                    Delivery Type
                  </label>
                  <select
                    id="deliveryType"
                    name="deliveryType"
                    value={formData.deliveryType}
                    onChange={handleChange}
                    required
                    className={styles.select}
                  >
                    <option value="">Select delivery type</option>
                    <option value="vaginal">Vaginal</option>
                    <option value="cesarean">Cesarean</option>
                  </select>
                </div>
                <div className={styles.formGroup}>
                  <label htmlFor="dueDate">
                    {/* <FaCalendarAlt className={styles.inputIcon} /> */}
                    Due Date
                  </label>
                  <input
                    type="date"
                    id="dueDate"
                    name="dueDate"
                    value={formData.dueDate}
                    onChange={handleChange}
                    required
                    className={styles.input}
                  />
                </div>
              </div>
            )}

            {step === 2 && (
              <div
                // initial={{ opacity: 0 }}
                // animate={{ opacity: 1 }}
                // transition={{ delay: 0.2 }}
              >
                <div className={styles.formGroup}>
                  <label htmlFor="babyGender">
                    {/* <FaVenusMars className={styles.inputIcon} /> */}
                    Baby's Gender
                  </label>
                  <select
                    id="babyGender"
                    name="babyGender"
                    value={formData.babyGender}
                    onChange={handleChange}
                    required
                    className={styles.select}
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
            )}

            {step === 3 && (
              <div
                // initial={{ opacity: 0 }}
                // animate={{ opacity: 1 }}
                // transition={{ delay: 0.2 }}
              >
                <div className={styles.formGroup}>
                  <label htmlFor="babyName">
                    {/* <FaBaby className={styles.inputIcon} /> */}
                    Baby's Name
                  </label>
                  <input
                    type="text"
                    id="babyName"
                    name="babyName"
                    value={formData.babyName}
                    onChange={handleChange}
                    required
                    className={styles.input}
                    placeholder="Enter your baby's name"
                  />
                </div>
              </div>
            )}

            {/* <motion.div 
              className={styles.buttonGroup}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            > */}
              <div className={styles.buttonGroup}>
              {step > 1 && (
                <button
                  type="button"
                  onClick={() => setStep(step - 1)}
                  className={styles.secondaryButton}
                >
                  Back
                </button>
              )}
              <button type="submit" className={styles.primaryButton}>
                {step === 3 ? 'Complete' : 'Next'}
              </button>
              </div>
            {/* </motion.div> */}
          </form>
        {/* </AnimatePresence> */}
      </div>
    </div>
  );
};

export default Onboarding;
import React from 'react';
// import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
// import { FaHeartbeat, FaUserMd, FaUsers, FaChartLine } from 'react-icons/fa';
import { Button } from '../components/common/Button';
import hospitalPartners from '../assets/images/partner-logos.png';
import heroImage from '../assets/illustrations/hero-mom-baby.png';
import styles from '../styles/LandingPage.module.scss';

// const features = [
//   {
//     icon: <FaHeartbeat />,
//     title: 'Personalized Care',
//     description: 'Tailored recovery plans based on your unique postpartum journey'
//   },
//   {
//     icon: <FaUserMd />,
//     title: 'Expert Guidance',
//     description: 'Access to healthcare professionals and specialists'
//   },
//   {
//     icon: <FaUsers />,
//     title: 'Community Support',
//     description: 'Connect with other mothers going through similar experiences'
//   },
//   {
//     icon: <FaChartLine />,
//     title: 'Progress Tracking',
//     description: 'Monitor your recovery and celebrate milestones'
//   }
// ];

const LandingPage = () => {
  return (
    <div className={styles.landingPage}>
      {/* <nav className={styles.navbar}>
        <div className={styles.logo}>PostpartumCare</div>
        <div className={styles.navLinks}>
          <Link to="/about">About</Link>
          <Link to="/features">Features</Link>
          <Link to="/contact">Contact</Link>
          <Link to="/login" className={styles.loginButton}>Login</Link>
          <Link to="/signup" className={styles.signupButton}>Sign Up</Link>
        </div>
      </nav> */}

      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <h1>Your Postpartum Recovery, Simplified</h1>
          <p className={styles.subtext}>
            Personalized care plans, expert support, and community—all in one place
          </p>
          <div className={styles.ctaButtons}>
            <Link to="/signup">
              <Button primary>Get Started</Button>
            </Link>
            {/* <Link to="/how-it-works">
              <Button secondary>How It Works</Button>
            </Link> */}
          </div>
          <div className={styles.trustSignals}>
            <p>Trusted by:</p>
            <img src={hospitalPartners} alt="Partner hospitals" />
          </div>
        </div>
        <div className={styles.heroImage}>
          <img src={heroImage} alt="Mother and baby" />
        </div>
      </section>

      {/* <section className={styles.features}>
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          Why Choose Us
        </motion.h2>
        <div className={styles.featureGrid}>
          {features.map((feature, index) => (
            <motion.div
              key={index}
              className={styles.featureCard}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              <div className={styles.featureIcon}>{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section> */}

      {/* <section className={styles.testimonials}>
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          What Mothers Say
        </motion.h2>
        <div className={styles.testimonialGrid}>
          <motion.div
            className={styles.testimonialCard}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <p className={styles.quote}>
              "This platform made my postpartum journey so much easier. The personalized care plan was exactly what I needed."
            </p>
            <div className={styles.author}>
              <img src="/path-to-avatar.jpg" alt="Sarah M." />
              <div>
                <h4>Sarah M.</h4>
                <p>First-time mother</p>
              </div>
            </div>
          </motion.div>
          {/* Add more testimonials as needed */}
        </div>
      </section> */}

      {/* <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <div className={styles.footerSection}>
            <h3>PostpartumCare</h3>
            <p>Supporting mothers through their postpartum journey</p>
          </div>
          <div className={styles.footerSection}>
            <h4>Quick Links</h4>
            <Link to="/about">About</Link>
            <Link to="/features">Features</Link>
            <Link to="/contact">Contact</Link>
          </div>
          <div className={styles.footerSection}>
            <h4>Connect</h4>
            <div className={styles.socialLinks}>
              <a href="#" aria-label="Facebook">FB</a>
              <a href="#" aria-label="Twitter">TW</a>
              <a href="#" aria-label="Instagram">IG</a>
            </div>
          </div>
        </div>
        <div className={styles.footerBottom}>
          <p>&copy; 2024 PostpartumCare. All rights reserved.</p>
        </div>
      </footer> */}
    </div>
  );
};

export default LandingPage;

import React, { useState } from 'react';
import Chatbot from '../components/Chatbot/Chatbot';
import ChatSidebar from '../components/Chatbot/ChatSidebar';
import styles from '../styles/ChatPage.module.scss';
import axios from 'axios';

const ChatPage = () => {
  const [selectedChatId, setSelectedChatId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [openQuestionIndex, setOpenQuestionIndex] = useState(null);

  // Example suggested questions and answers
  const suggestedQuestions = [
    {
      question: 'What are common postpartum symptoms?',
      answer: `Common symptoms include fatigue, sore muscles, vaginal discharge (lochia), breast changes, and emotional shifts. It's important to monitor these and consult a healthcare provider if you have concerns.`,
    },
    {
      question: 'How can I get help for postpartum depression?',
      answer: `If you suspect you have postpartum depression, reach out to your doctor or a mental health professional immediately. Support groups, therapy, and medication are all potential options.`,
    },
    {
      question: 'What foods are good for recovery?',
      answer: `Nutrient-rich foods are crucial for recovery. Focus on lean proteins, whole grains, fruits, vegetables, and healthy fats. Staying hydrated is also key.`,
    },
    {
      question: 'How much sleep do newborns need?',
      answer: `Newborns typically sleep 14-17 hours per day, but in short bursts. They don't have a day-night cycle yet, so expect frequent waking for feeding.`,
    },
  ];

  const toggleQuestion = (index) => {
    setOpenQuestionIndex(openQuestionIndex === index ? null : index);
  };

  const handleSelectChat = async (chatId) => {
    setSelectedChatId(chatId);
    if (chatId) {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`/api/chatbot/history/${chatId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setChatMessages(res.data.messages || []);
      } catch (err) {
        setChatMessages([]);
      }
    } else {
      setChatMessages([]);
    }
  };

  return (
    <div className={styles.chatPageWrapper}>
      <ChatSidebar onSelectChat={handleSelectChat} selectedChatId={selectedChatId} />
      <div className={styles.chatMainContent}>
        <div className={styles.chatBanner}></div>
        <div className={styles.chatContent}>
          <h1>Chat with Assistant</h1>
          <p className={styles.introText}>
            Ask the Postpartum Care Assistant any questions you have about your recovery, your baby, or finding resources.
          </p>
          <div className={styles.suggestedQuestions}>
            <h2>Popular Questions</h2>
            <ul>
              {suggestedQuestions.map((item, index) => (
                <li key={index} className={styles.dropdownContainer}>
                  <div
                    className={styles.dropdownHeader}
                    onClick={() => toggleQuestion(index)}
                  >
                    {item.question}
                  </div>
                  <div
                    className={`${styles.dropdownContent} ${openQuestionIndex === index ? styles.active : ''}`}
                  >
                    {item.answer}
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <Chatbot chatId={selectedChatId} messages={chatMessages} />
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
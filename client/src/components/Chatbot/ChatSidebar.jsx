import React, { useEffect, useState } from "react";
import axios from "axios";
import styles from "../../styles/ChatPage.module.scss";

const ChatSidebar = ({ onSelectChat, selectedChatId }) => {
  const [chats, setChats] = useState([]);

  useEffect(() => {
    const fetchChats = async () => {
      try {
        const token = localStorage.getItem("token");
        const res = await axios.get("/api/chatbot/history", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setChats(res.data);
      } catch (err) {
        setChats([]);
      }
    };
    fetchChats();
  }, []);

  return (
    <div className={styles.chatSidebar}>
      <h3>Chat History</h3>
      {chats.length === 0 ? (
        <div className={styles.noChats}>No Past Chats</div>
      ) : (
        chats.map((chat) => (
          <div
            key={chat._id}
            className={`${styles.chatHistoryItem} ${selectedChatId === chat._id ? styles.selected : ""}`}
            onClick={() => onSelectChat(chat._id)}
          >
            <div>{chat.title || "Chat"}</div>
            <div className={styles.chatDate}>{new Date(chat.created_at).toLocaleString()}</div>
          </div>
        ))
      )}
    </div>
  );
};

export default ChatSidebar; 
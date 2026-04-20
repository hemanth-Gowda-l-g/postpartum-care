import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import styles from '../styles/Forum.module.scss';

const Forum = () => {
  const { currentUser } = useAuth();
  const [posts, setPosts] = useState([
    {
      id: 1,
      author: 'Sarah M.',
      content: 'Looking for advice on managing sleep with a 2-week-old. Any tips for establishing a routine?',
      category: 'Sleep',
      timestamp: '2 hours ago'
    },
    {
      id: 2,
      author: 'Emily R.',
      content: 'Just wanted to share my positive experience with postpartum yoga. It really helped with my recovery!',
      category: 'Recovery',
      timestamp: '5 hours ago'
    }
  ]);
  const [newPost, setNewPost] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [showNewPostForm, setShowNewPostForm] = useState(false);

  const categories = ['All', 'Sleep', 'Recovery', 'Nutrition', 'Mental Health', 'Breastfeeding', 'Exercise'];

  const handleNewPost = (e) => {
    e.preventDefault();
    if (newPost.trim()) {
      const post = {
        id: posts.length + 1,
        author: currentUser?.name || 'Anonymous',
        content: newPost,
        category: selectedCategory,
        timestamp: 'Just now'
      };
      setPosts([post, ...posts]);
      setNewPost('');
      setShowNewPostForm(false);
    }
  };

  return (
    <div className={styles.forumContainer}>
      <h1>Community Forum</h1>
      
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

      {/* New Post Button */}
      <button
        className={styles.newPostButton}
        onClick={() => setShowNewPostForm(true)}
      >
        Share Your Experience
      </button>

      {/* New Post Form */}
      {showNewPostForm && (
        <form onSubmit={handleNewPost} className={styles.newPostForm}>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className={styles.categorySelect}
          >
            {categories.filter(cat => cat !== 'All').map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
          <textarea
            value={newPost}
            onChange={(e) => setNewPost(e.target.value)}
            placeholder="What's on your mind?"
            className={styles.postTextarea}
            rows={4}
          />
          <div className={styles.formButtons}>
            <button type="button" onClick={() => setShowNewPostForm(false)} className={styles.cancelButton}>
              Cancel
            </button>
            <button type="submit" className={styles.submitButton}>
              Post
            </button>
          </div>
        </form>
      )}

      {/* Posts Feed */}
      <div className={styles.postsList}>
        {posts.map((post) => (
          <div key={post.id} className={styles.postCard}>
            <div className={styles.postHeader}>
              <span className={styles.author}>{post.author}</span>
              <span className={styles.timestamp}>{post.timestamp}</span>
              <span className={styles.category}>{post.category}</span>
            </div>
            <p className={styles.postContent}>{post.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Forum; 

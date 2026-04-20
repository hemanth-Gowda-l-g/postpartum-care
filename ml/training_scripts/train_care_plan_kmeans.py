import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class CarePlanKMeansModel:
    """
    K-means clustering model for personalized postpartum care plan recommendations
    """
    
    def __init__(self, data_path=None):
        self.data_path = data_path or r'D:\postpartum-care-platform\ml\datasets\care_plan\care_plan_dataset_3000.xls'
        self.data = None
        self.kmeans_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.pca = None
        self.feature_names = []
        self.cluster_profiles = {}
        self.n_clusters = 6  # Will be optimized
        
        # Care plan templates for each cluster
        self.care_plan_templates = {
            'tasks': {
                'physical_recovery': [
                    "Take prescribed pain medication as needed",
                    "Do gentle pelvic floor exercises (5 minutes daily)",
                    "Walk for 10-15 minutes daily",
                    "Monitor incision site for signs of infection",
                    "Apply ice pack to reduce swelling (15 minutes, 3x daily)",
                    "Practice deep breathing exercises",
                    "Get adequate sleep (8+ hours when possible)",
                    "Attend follow-up appointments with healthcare provider"
                ],
                'mental_health': [
                    "Practice mindfulness meditation (10 minutes daily)",
                    "Journal your feelings and thoughts",
                    "Connect with other new mothers (support groups)",
                    "Schedule regular check-ins with partner/family",
                    "Take breaks when feeling overwhelmed",
                    "Consider counseling if mood symptoms persist",
                    "Practice gratitude exercises",
                    "Limit social media if it increases anxiety"
                ],
                'feeding_support': [
                    "Maintain proper feeding schedule",
                    "Stay hydrated (8-10 glasses of water daily)",
                    "Eat nutrient-rich meals regularly",
                    "Seek lactation consultant if breastfeeding issues arise",
                    "Track feeding patterns and baby's weight gain",
                    "Prepare bottles and feeding supplies in advance",
                    "Create comfortable feeding environment",
                    "Join feeding support groups"
                ],
                'family_support': [
                    "Ask family/friends for help with household tasks",
                    "Communicate your needs clearly to support system",
                    "Accept help when offered",
                    "Create a support network of other parents",
                    "Delegate childcare responsibilities when possible",
                    "Schedule regular family meetings to discuss needs",
                    "Set boundaries with visitors",
                    "Consider hiring help if financially feasible"
                ]
            },
            'resources': {
                'physical': [
                    "Video: Postpartum Exercise Basics",
                    "Article: C-Section Recovery Timeline",
                    "Guide: Recognizing Infection Signs",
                    "Checklist: Postpartum Warning Signs",
                    "Video: Pelvic Floor Exercises"
                ],
                'mental': [
                    "Article: Understanding Baby Blues vs PPD",
                    "Resource: Local Support Groups",
                    "Guide: Mindfulness for New Mothers",
                    "Hotline: Postpartum Support International",
                    "App: Meditation for Mothers"
                ],
                'feeding': [
                    "Guide: Breastfeeding Positions",
                    "Article: Formula Feeding Best Practices",
                    "Resource: Lactation Consultant Directory",
                    "Video: Pumping and Storage Tips",
                    "Checklist: Feeding Supplies"
                ],
                'support': [
                    "Directory: Local Parent Groups",
                    "Guide: Building Your Support Network",
                    "Article: Communicating Your Needs",
                    "Resource: Postpartum Doula Services",
                    "Checklist: Help Request Ideas"
                ]
            }
        }
    
    def load_and_preprocess_data(self):
        """Load and preprocess the care plan dataset"""
        print("Loading care plan dataset...")
        
        try:
            # Load data
            self.data = pd.read_csv(self.data_path)
            print(f"Loaded {len(self.data)} records")
            
            # Display basic info about the dataset
            print("\nDataset Info:")
            print(self.data.info())
            print("\nFirst few rows:")
            print(self.data.head())
            
            # Calculate days since delivery
            self.data['delivery_date'] = pd.to_datetime(self.data['delivery_date'])
            current_date = datetime.now()
            self.data['days_since_delivery'] = (current_date - self.data['delivery_date']).dt.days
            
            # Feature engineering
            self.data['is_high_risk_ppd'] = (self.data['epds_score'] >= 13).astype(int)
            self.data['is_early_postpartum'] = (self.data['postpartum_week'] <= 2).astype(int)
            self.data['is_late_postpartum'] = (self.data['postpartum_week'] >= 12).astype(int)
            
            # Encode categorical variables
            categorical_features = ['delivery_type', 'feeding', 'specific_concerns']
            for feature in categorical_features:
                le = LabelEncoder()
                self.data[f'{feature}_encoded'] = le.fit_transform(self.data[feature])
                self.label_encoders[feature] = le
            
            # Select features for clustering
            self.feature_names = [
                'epds_score', 'postpartum_week', 'days_since_delivery',
                'delivery_type_encoded', 'feeding_encoded', 'specific_concerns_encoded',
                'is_high_risk_ppd', 'is_early_postpartum', 'is_late_postpartum'
            ]
            
            print(f"\nFeatures selected for clustering: {self.feature_names}")
            print(f"Feature matrix shape: {self.data[self.feature_names].shape}")
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def find_optimal_clusters(self, max_clusters=10):
        """Find optimal number of clusters using elbow method and silhouette score"""
        print("Finding optimal number of clusters...")
        
        X = self.data[self.feature_names].values
        X_scaled = self.scaler.fit_transform(X)
        
        inertias = []
        silhouette_scores = []
        K_range = range(2, max_clusters + 1)
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X_scaled)
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(X_scaled, kmeans.labels_))
        
        # Plot elbow curve and silhouette scores
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Elbow curve
        ax1.plot(K_range, inertias, 'bo-')
        ax1.set_xlabel('Number of Clusters (k)')
        ax1.set_ylabel('Inertia')
        ax1.set_title('Elbow Method for Optimal k')
        ax1.grid(True)
        
        # Silhouette scores
        ax2.plot(K_range, silhouette_scores, 'ro-')
        ax2.set_xlabel('Number of Clusters (k)')
        ax2.set_ylabel('Silhouette Score')
        ax2.set_title('Silhouette Score vs Number of Clusters')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('cluster_optimization.png')
        plt.close()
        
        # Find optimal k (highest silhouette score)
        optimal_k = K_range[np.argmax(silhouette_scores)]
        self.n_clusters = optimal_k
        
        print(f"Optimal number of clusters: {optimal_k}")
        print(f"Best silhouette score: {max(silhouette_scores):.3f}")
        
        return optimal_k
    
    def train_kmeans_model(self):
        """Train K-means clustering model"""
        print(f"Training K-means model with {self.n_clusters} clusters...")
        
        try:
            # Prepare features
            X = self.data[self.feature_names].values
            X_scaled = self.scaler.fit_transform(X)
            
            # Apply PCA for visualization (optional)
            self.pca = PCA(n_components=2, random_state=42)
            X_pca = self.pca.fit_transform(X_scaled)
            
            # Train K-means model
            self.kmeans_model = KMeans(
                n_clusters=self.n_clusters,
                random_state=42,
                n_init=10,
                max_iter=300
            )
            
            cluster_labels = self.kmeans_model.fit_predict(X_scaled)
            
            # Add cluster labels to data
            self.data['cluster'] = cluster_labels
            
            # Calculate silhouette score
            silhouette_avg = silhouette_score(X_scaled, cluster_labels)
            print(f"Average silhouette score: {silhouette_avg:.3f}")
            
            # Analyze clusters
            self.analyze_clusters()
            
            # Visualize clusters
            self.visualize_clusters(X_pca, cluster_labels)
            
            print("✅ K-means model trained successfully")
            return True
            
        except Exception as e:
            print(f"Error training K-means model: {e}")
            return False
    
    def analyze_clusters(self):
        """Analyze and profile each cluster"""
        print("\nAnalyzing cluster profiles...")
        
        self.cluster_profiles = {}
        
        for cluster_id in range(self.n_clusters):
            cluster_data = self.data[self.data['cluster'] == cluster_id]
            
            profile = {
                'size': len(cluster_data),
                'avg_epds_score': cluster_data['epds_score'].mean(),
                'avg_postpartum_week': cluster_data['postpartum_week'].mean(),
                'most_common_delivery': cluster_data['delivery_type'].mode()[0],
                'most_common_feeding': cluster_data['feeding'].mode()[0],
                'most_common_concern': cluster_data['specific_concerns'].mode()[0],
                'high_risk_ppd_percentage': cluster_data['is_high_risk_ppd'].mean() * 100,
                'early_postpartum_percentage': cluster_data['is_early_postpartum'].mean() * 100
            }
            
            self.cluster_profiles[cluster_id] = profile
            
            print(f"\n--- Cluster {cluster_id} Profile ---")
            print(f"Size: {profile['size']} patients ({profile['size']/len(self.data)*100:.1f}%)")
            print(f"Average EPDS Score: {profile['avg_epds_score']:.1f}")
            print(f"Average Postpartum Week: {profile['avg_postpartum_week']:.1f}")
            print(f"Most Common Delivery: {profile['most_common_delivery']}")
            print(f"Most Common Feeding: {profile['most_common_feeding']}")
            print(f"Most Common Concern: {profile['most_common_concern']}")
            print(f"High Risk PPD: {profile['high_risk_ppd_percentage']:.1f}%")
            print(f"Early Postpartum: {profile['early_postpartum_percentage']:.1f}%")
    
    def visualize_clusters(self, X_pca, cluster_labels):
        """Visualize clusters using PCA"""
        plt.figure(figsize=(12, 8))
        
        # Create scatter plot
        colors = plt.cm.Set3(np.linspace(0, 1, self.n_clusters))
        for i in range(self.n_clusters):
            cluster_points = X_pca[cluster_labels == i]
            plt.scatter(cluster_points[:, 0], cluster_points[:, 1], 
                       c=[colors[i]], label=f'Cluster {i}', alpha=0.6, s=50)
        
        # Plot cluster centers (transformed to PCA space)
        centers_pca = self.pca.transform(self.kmeans_model.cluster_centers_)
        plt.scatter(centers_pca[:, 0], centers_pca[:, 1], 
                   c='red', marker='x', s=200, linewidths=3, label='Centroids')
        
        plt.xlabel('First Principal Component')
        plt.ylabel('Second Principal Component')
        plt.title('K-means Clustering of Postpartum Care Profiles')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('kmeans_clusters_visualization.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create cluster distribution plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # EPDS Score distribution by cluster
        self.data.boxplot(column='epds_score', by='cluster', ax=axes[0,0])
        axes[0,0].set_title('EPDS Score by Cluster')
        axes[0,0].set_xlabel('Cluster')
        
        # Postpartum week distribution by cluster
        self.data.boxplot(column='postpartum_week', by='cluster', ax=axes[0,1])
        axes[0,1].set_title('Postpartum Week by Cluster')
        axes[0,1].set_xlabel('Cluster')
        
        # Delivery type distribution
        delivery_counts = pd.crosstab(self.data['cluster'], self.data['delivery_type'])
        delivery_counts.plot(kind='bar', ax=axes[1,0])
        axes[1,0].set_title('Delivery Type by Cluster')
        axes[1,0].set_xlabel('Cluster')
        axes[1,0].legend(title='Delivery Type')
        
        # Feeding type distribution
        feeding_counts = pd.crosstab(self.data['cluster'], self.data['feeding'])
        feeding_counts.plot(kind='bar', ax=axes[1,1])
        axes[1,1].set_title('Feeding Type by Cluster')
        axes[1,1].set_xlabel('Cluster')
        axes[1,1].legend(title='Feeding Type')
        
        plt.tight_layout()
        plt.savefig('cluster_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Cluster visualizations saved")
    
    def generate_care_plan(self, user_profile):
        """Generate personalized care plan based on user profile and cluster assignment"""
        try:
            # Prepare user features
            user_features = self.prepare_user_features(user_profile)
            
            # Scale features
            user_features_scaled = self.scaler.transform([user_features])
            
            # Predict cluster
            cluster_id = self.kmeans_model.predict(user_features_scaled)[0]
            
            print(f"User assigned to Cluster {cluster_id}")
            
            # Get cluster profile
            cluster_profile = self.cluster_profiles[cluster_id]
            
            # Generate personalized care plan
            care_plan = self.create_personalized_plan(user_profile, cluster_profile, cluster_id)
            
            return care_plan
            
        except Exception as e:
            print(f"Error generating care plan: {e}")
            return None
    
    def prepare_user_features(self, user_profile):
        """Prepare user features for cluster prediction"""
        features = []
        
        # EPDS score
        features.append(user_profile.get('epds_score', 10))
        
        # Postpartum week
        features.append(user_profile.get('postpartum_week', 4))
        
        # Days since delivery (calculated from postpartum_week)
        features.append(user_profile.get('postpartum_week', 4) * 7)
        
        # Encoded categorical features
        delivery_type = user_profile.get('delivery_type', 'vaginal')
        if delivery_type in self.label_encoders['delivery_type'].classes_:
            features.append(self.label_encoders['delivery_type'].transform([delivery_type])[0])
        else:
            features.append(0)  # Default to first class
        
        feeding = user_profile.get('feeding', 'breastfeeding')
        if feeding in self.label_encoders['feeding'].classes_:
            features.append(self.label_encoders['feeding'].transform([feeding])[0])
        else:
            features.append(0)
        
        specific_concerns = user_profile.get('specific_concerns', 'Mood swings')
        if specific_concerns in self.label_encoders['specific_concerns'].classes_:
            features.append(self.label_encoders['specific_concerns'].transform([specific_concerns])[0])
        else:
            features.append(0)
        
        # Derived features
        features.append(1 if user_profile.get('epds_score', 10) >= 13 else 0)  # is_high_risk_ppd
        features.append(1 if user_profile.get('postpartum_week', 4) <= 2 else 0)  # is_early_postpartum
        features.append(1 if user_profile.get('postpartum_week', 4) >= 12 else 0)  # is_late_postpartum
        
        return features
    
    def create_personalized_plan(self, user_profile, cluster_profile, cluster_id):
        """Create personalized care plan based on user profile and cluster characteristics"""
        
        care_plan = {
            'user_profile': user_profile,
            'cluster_id': cluster_id,
            'cluster_profile': cluster_profile,
            'week_indicator': f"You are in Week {user_profile.get('postpartum_week', 4)} of Postpartum Recovery",
            'priorities': [],
            'daily_tasks': [],
            'resources': [],
            'progress_tracking': {
                'total_tasks': 0,
                'completed_tasks': 0,
                'completion_percentage': 0
            }
        }
        
        # Determine priorities based on cluster profile and user specifics
        epds_score = user_profile.get('epds_score', 10)
        postpartum_week = user_profile.get('postpartum_week', 4)
        delivery_type = user_profile.get('delivery_type', 'vaginal')
        feeding = user_profile.get('feeding', 'breastfeeding')
        concerns = user_profile.get('specific_concerns', 'Mood swings')
        
        # Priority 1: Mental Health (if high EPDS or mood-related concerns)
        if epds_score >= 13 or 'mood' in concerns.lower() or 'overwhelmed' in concerns.lower():
            care_plan['priorities'].append({
                'icon': '😌',
                'title': 'Mental Health & Emotional Well-being',
                'description': 'Your emotional health is our top priority'
            })
            care_plan['daily_tasks'].extend([
                {
                    'id': 'mental_1',
                    'task': 'Practice 10-minute mindfulness meditation',
                    'category': 'mental_health',
                    'completed': False,
                    'priority': 'high'
                },
                {
                    'id': 'mental_2', 
                    'task': 'Journal your feelings for 5 minutes',
                    'category': 'mental_health',
                    'completed': False,
                    'priority': 'high'
                },
                {
                    'id': 'mental_3',
                    'task': 'Connect with your support person today',
                    'category': 'mental_health',
                    'completed': False,
                    'priority': 'medium'
                }
            ])
            care_plan['resources'].extend([
                'Article: Understanding Postpartum Depression',
                'Hotline: Postpartum Support International: 1-800-944-4773',
                'App: Headspace for Mothers'
            ])
        
        # Priority 2: Physical Recovery (especially for C-section or early postpartum)
        if delivery_type == 'c_section' or postpartum_week <= 4 or 'pain' in concerns.lower():
            care_plan['priorities'].append({
                'icon': '💪',
                'title': 'Physical Recovery & Healing',
                'description': 'Your body is doing important healing work'
            })
            
            if delivery_type == 'c_section':
                care_plan['daily_tasks'].extend([
                    {
                        'id': 'physical_1',
                        'task': 'Check incision site for signs of infection',
                        'category': 'physical_recovery',
                        'completed': False,
                        'priority': 'high'
                    },
                    {
                        'id': 'physical_2',
                        'task': 'Take prescribed pain medication as needed',
                        'category': 'physical_recovery',
                        'completed': False,
                        'priority': 'high'
                    }
                ])
            
            care_plan['daily_tasks'].extend([
                {
                    'id': 'physical_3',
                    'task': 'Take a gentle 10-minute walk',
                    'category': 'physical_recovery',
                    'completed': False,
                    'priority': 'medium'
                },
                {
                    'id': 'physical_4',
                    'task': 'Do 5 minutes of pelvic floor exercises',
                    'category': 'physical_recovery',
                    'completed': False,
                    'priority': 'medium'
                }
            ])
            
            care_plan['resources'].extend([
                'Video: C-Section Recovery Timeline' if delivery_type == 'c_section' else 'Video: Postpartum Exercise Basics',
                'Guide: Recognizing Infection Signs',
                'Checklist: Postpartum Warning Signs'
            ])
        
        # Priority 3: Feeding Support
        if feeding in ['breastfeeding', 'mixed'] or 'milk' in concerns.lower() or 'feeding' in concerns.lower():
            care_plan['priorities'].append({
                'icon': '🍼',
                'title': 'Feeding & Nutrition Support',
                'description': 'Nourishing both you and your baby'
            })
            
            care_plan['daily_tasks'].extend([
                {
                    'id': 'feeding_1',
                    'task': 'Stay hydrated - drink water with each feeding',
                    'category': 'feeding_support',
                    'completed': False,
                    'priority': 'high'
                },
                {
                    'id': 'feeding_2',
                    'task': 'Eat a nutritious meal every 3-4 hours',
                    'category': 'feeding_support',
                    'completed': False,
                    'priority': 'medium'
                }
            ])
            
            if 'milk' in concerns.lower():
                care_plan['daily_tasks'].append({
                    'id': 'feeding_3',
                    'task': 'Consider contacting a lactation consultant',
                    'category': 'feeding_support',
                    'completed': False,
                    'priority': 'high'
                })
            
            care_plan['resources'].extend([
                'Guide: Breastfeeding Positions and Techniques',
                'Resource: Lactation Consultant Directory',
                'Article: Increasing Milk Supply Naturally'
            ])
        
        # Priority 4: Support System
        if 'support' in concerns.lower() or cluster_profile['size'] < len(self.data) * 0.15:  # Smaller clusters might need more support
            care_plan['priorities'].append({
                'icon': '🤝',
                'title': 'Building Your Support Network',
                'description': 'You dont have to do this alone'
            })
            
            care_plan['daily_tasks'].extend([
                {
                    'id': 'support_1',
                    'task': 'Reach out to one family member or friend today',
                    'category': 'family_support',
                    'completed': False,
                    'priority': 'medium'
                },
                {
                    'id': 'support_2',
                    'task': 'Accept help when offered',
                    'category': 'family_support',
                    'completed': False,
                    'priority': 'low'
                }
            ])
            
            care_plan['resources'].extend([
                'Directory: Local New Parent Support Groups',
                'Guide: How to Ask for Help',
                'Resource: Postpartum Doula Services'
            ])
        
        # Update progress tracking
        care_plan['progress_tracking']['total_tasks'] = len(care_plan['daily_tasks'])
        
        return care_plan
    
    def save_model(self, model_path=None):
        """Save the trained model and components"""
        if model_path is None:
            model_path = Path(__file__).parent.parent / 'models' / 'care_plan_kmeans_model.pkl'
        
        model_data = {
            'kmeans_model': self.kmeans_model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'pca': self.pca,
            'feature_names': self.feature_names,
            'cluster_profiles': self.cluster_profiles,
            'n_clusters': self.n_clusters,
            'care_plan_templates': self.care_plan_templates
        }
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(model_data, model_path)
        print(f"✅ Care Plan K-means model saved to {model_path}")
    
    def load_model(self, model_path):
        """Load a saved model"""
        try:
            model_data = joblib.load(model_path)
            
            self.kmeans_model = model_data['kmeans_model']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.pca = model_data['pca']
            self.feature_names = model_data['feature_names']
            self.cluster_profiles = model_data['cluster_profiles']
            self.n_clusters = model_data['n_clusters']
            self.care_plan_templates = model_data['care_plan_templates']
            
            print("✅ Care Plan K-means model loaded successfully")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise


def main():
    """Main function to train the Care Plan K-means model"""
    print("=== Care Plan K-means Clustering Model Training ===\n")
    
    try:
        # Initialize model
        model = CarePlanKMeansModel()
        
        # Load and preprocess data
        if not model.load_and_preprocess_data():
            return
        
        # Find optimal number of clusters
        optimal_k = model.find_optimal_clusters(max_clusters=10)
        
        # Train K-means model
        if not model.train_kmeans_model():
            return
        
        # Test with example users
        example_users = [
            {
                'name': 'Sarah - High PPD Risk, Early Postpartum',
                'profile': {
                    'epds_score': 16,
                    'postpartum_week': 2,
                    'delivery_type': 'c_section',
                    'feeding': 'breastfeeding',
                    'specific_concerns': 'Severe fatigue'
                }
            },
            {
                'name': 'Maria - Moderate Risk, Mid Postpartum',
                'profile': {
                    'epds_score': 8,
                    'postpartum_week': 6,
                    'delivery_type': 'vaginal',
                    'feeding': 'mixed',
                    'specific_concerns': 'Low milk supply'
                }
            },
            {
                'name': 'Lisa - Low Risk, Late Postpartum',
                'profile': {
                    'epds_score': 4,
                    'postpartum_week': 12,
                    'delivery_type': 'vaginal',
                    'feeding': 'formula',
                    'specific_concerns': 'Sleep deprivation'
                }
            }
        ]
        
        # Generate care plans for example users
        for user_info in example_users:
            print(f"\n{'='*60}")
            print(f"Generating Care Plan for: {user_info['name']}")
            print(f"{'='*60}")
            
            care_plan = model.generate_care_plan(user_info['profile'])
            
            if care_plan:
                print(f"\n{care_plan['week_indicator']}")
                print(f"Assigned to Cluster: {care_plan['cluster_id']}")
                
                print(f"\n📋 This Week's Priorities:")
                for priority in care_plan['priorities']:
                    print(f"  {priority['icon']} {priority['title']}: {priority['description']}")
                
                print(f"\n✅ Daily Tasks ({len(care_plan['daily_tasks'])} tasks):")
                for task in care_plan['daily_tasks'][:5]:  # Show first 5 tasks
                    priority_icon = "🔴" if task['priority'] == 'high' else "🟡" if task['priority'] == 'medium' else "🟢"
                    print(f"  {priority_icon} {task['task']}")
                
                print(f"\n📚 Recommended Resources:")
                for resource in care_plan['resources'][:3]:  # Show first 3 resources
                    print(f"  • {resource}")
        
        # Save the trained model
        model.save_model()
        
        print(f"\n{'='*60}")
        print("✅ Care Plan K-means Model Training Complete!")
        print(f"Model trained on {len(model.data)} records")
        print(f"Optimal clusters: {model.n_clusters}")
        print("Model saved and ready for production use.")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

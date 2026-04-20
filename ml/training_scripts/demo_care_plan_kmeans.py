import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns
import os

def load_and_analyze_dataset():
    """Load and analyze the care plan dataset"""
    print("=== Care Plan K-means Clustering Demo ===\n")
    
    # Load the dataset
    data_path = r'D:\postpartum-care-platform\ml\datasets\care_plan\care_plan_dataset_3000.xls'
    
    try:
        data = pd.read_csv(data_path)
        print(f"✅ Loaded dataset with {len(data)} records")
        
        # Display basic statistics
        print(f"\nDataset Overview:")
        print(f"- Total records: {len(data)}")
        print(f"- Columns: {list(data.columns)}")
        
        print(f"\nEPDS Score Distribution:")
        print(f"- Mean: {data['epds_score'].mean():.2f}")
        print(f"- Min: {data['epds_score'].min()}")
        print(f"- Max: {data['epds_score'].max()}")
        print(f"- High Risk (≥13): {(data['epds_score'] >= 13).sum()} ({(data['epds_score'] >= 13).mean()*100:.1f}%)")
        
        print(f"\nPostpartum Week Distribution:")
        print(f"- Mean: {data['postpartum_week'].mean():.2f}")
        print(f"- Range: {data['postpartum_week'].min()} - {data['postpartum_week'].max()} weeks")
        
        print(f"\nDelivery Type Distribution:")
        print(data['delivery_type'].value_counts().to_string())
        
        print(f"\nFeeding Type Distribution:")
        print(data['feeding'].value_counts().to_string())
        
        print(f"\nTop Concerns:")
        print(data['specific_concerns'].value_counts().head().to_string())
        
        return data
        
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return None

def preprocess_data(data):
    """Preprocess data for K-means clustering"""
    print(f"\n=== Data Preprocessing ===")
    
    # Feature engineering
    data['is_high_risk_ppd'] = (data['epds_score'] >= 13).astype(int)
    data['is_early_postpartum'] = (data['postpartum_week'] <= 2).astype(int)
    data['is_late_postpartum'] = (data['postpartum_week'] >= 12).astype(int)
    
    # Encode categorical variables
    label_encoders = {}
    categorical_features = ['delivery_type', 'feeding', 'specific_concerns']
    
    for feature in categorical_features:
        le = LabelEncoder()
        data[f'{feature}_encoded'] = le.fit_transform(data[feature])
        label_encoders[feature] = le
        print(f"✅ Encoded {feature}: {len(le.classes_)} categories")
    
    # Select features for clustering
    feature_names = [
        'epds_score', 'postpartum_week',
        'delivery_type_encoded', 'feeding_encoded', 'specific_concerns_encoded',
        'is_high_risk_ppd', 'is_early_postpartum', 'is_late_postpartum'
    ]
    
    print(f"✅ Selected {len(feature_names)} features for clustering")
    
    return data, feature_names, label_encoders

def find_optimal_clusters(data, feature_names, max_clusters=8):
    """Find optimal number of clusters using elbow method"""
    print(f"\n=== Finding Optimal Number of Clusters ===")
    
    X = data[feature_names].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    inertias = []
    silhouette_scores = []
    K_range = range(2, max_clusters + 1)
    
    print("Testing different cluster numbers...")
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
        sil_score = silhouette_score(X_scaled, kmeans.labels_)
        silhouette_scores.append(sil_score)
        print(f"k={k}: Inertia={kmeans.inertia_:.2f}, Silhouette={sil_score:.3f}")
    
    # Find optimal k (highest silhouette score)
    optimal_k = K_range[np.argmax(silhouette_scores)]
    best_silhouette = max(silhouette_scores)
    
    print(f"\n✅ Optimal number of clusters: {optimal_k}")
    print(f"✅ Best silhouette score: {best_silhouette:.3f}")
    
    return optimal_k, scaler, X_scaled

def train_kmeans_model(data, feature_names, n_clusters, X_scaled):
    """Train K-means clustering model"""
    print(f"\n=== Training K-means Model with {n_clusters} Clusters ===")
    
    # Train K-means model
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
    cluster_labels = kmeans.fit_predict(X_scaled)
    
    # Add cluster labels to data
    data['cluster'] = cluster_labels
    
    # Calculate final silhouette score
    silhouette_avg = silhouette_score(X_scaled, cluster_labels)
    print(f"✅ Model trained successfully")
    print(f"✅ Final silhouette score: {silhouette_avg:.3f}")
    
    return kmeans, cluster_labels

def analyze_clusters(data, n_clusters):
    """Analyze and profile each cluster"""
    print(f"\n=== Cluster Analysis ===")
    
    cluster_profiles = {}
    
    for cluster_id in range(n_clusters):
        cluster_data = data[data['cluster'] == cluster_id]
        
        profile = {
            'size': len(cluster_data),
            'percentage': len(cluster_data) / len(data) * 100,
            'avg_epds_score': cluster_data['epds_score'].mean(),
            'avg_postpartum_week': cluster_data['postpartum_week'].mean(),
            'most_common_delivery': cluster_data['delivery_type'].mode()[0],
            'most_common_feeding': cluster_data['feeding'].mode()[0],
            'most_common_concern': cluster_data['specific_concerns'].mode()[0],
            'high_risk_ppd_percentage': cluster_data['is_high_risk_ppd'].mean() * 100,
            'early_postpartum_percentage': cluster_data['is_early_postpartum'].mean() * 100
        }
        
        cluster_profiles[cluster_id] = profile
        
        print(f"\n--- Cluster {cluster_id} Profile ---")
        print(f"Size: {profile['size']} patients ({profile['percentage']:.1f}%)")
        print(f"Average EPDS Score: {profile['avg_epds_score']:.1f}")
        print(f"Average Postpartum Week: {profile['avg_postpartum_week']:.1f}")
        print(f"Most Common Delivery: {profile['most_common_delivery']}")
        print(f"Most Common Feeding: {profile['most_common_feeding']}")
        print(f"Most Common Concern: {profile['most_common_concern']}")
        print(f"High Risk PPD: {profile['high_risk_ppd_percentage']:.1f}%")
        print(f"Early Postpartum: {profile['early_postpartum_percentage']:.1f}%")
    
    return cluster_profiles

def generate_sample_care_plans(cluster_profiles):
    """Generate sample care plans for each cluster"""
    print(f"\n=== Sample Care Plans by Cluster ===")
    
    care_plan_templates = {
        'high_risk_mental_health': {
            'priorities': ['Mental Health Support', 'Professional Care', 'Family Support'],
            'tasks': [
                'Schedule mental health screening appointment',
                'Practice daily mindfulness (10 minutes)',
                'Connect with support person daily',
                'Monitor mood changes and symptoms'
            ],
            'resources': [
                'Postpartum Depression Screening Tools',
                'Mental Health Professional Directory',
                'Crisis Hotline Numbers'
            ]
        },
        'physical_recovery': {
            'priorities': ['Physical Healing', 'Pain Management', 'Gradual Activity'],
            'tasks': [
                'Monitor incision/healing sites daily',
                'Take prescribed medications as directed',
                'Gentle walking (10-15 minutes)',
                'Pelvic floor exercises'
            ],
            'resources': [
                'C-Section Recovery Guide',
                'Postpartum Exercise Videos',
                'Pain Management Techniques'
            ]
        },
        'feeding_support': {
            'priorities': ['Feeding Success', 'Nutrition', 'Lactation Support'],
            'tasks': [
                'Track feeding sessions and baby weight',
                'Stay hydrated (8-10 glasses water daily)',
                'Contact lactation consultant if needed',
                'Maintain nutritious meal schedule'
            ],
            'resources': [
                'Breastfeeding Position Guide',
                'Lactation Consultant Directory',
                'Nutrition for Breastfeeding Mothers'
            ]
        },
        'general_support': {
            'priorities': ['Self-Care', 'Family Adjustment', 'Routine Building'],
            'tasks': [
                'Establish daily routine',
                'Ask for help with household tasks',
                'Take time for personal care',
                'Connect with other new parents'
            ],
            'resources': [
                'New Parent Support Groups',
                'Postpartum Self-Care Guide',
                'Family Adjustment Tips'
            ]
        }
    }
    
    # Assign care plan types to clusters based on their characteristics
    for cluster_id, profile in cluster_profiles.items():
        print(f"\n--- Cluster {cluster_id} Care Plan ---")
        
        # Determine care plan type based on cluster characteristics
        if profile['high_risk_ppd_percentage'] > 60:
            plan_type = 'high_risk_mental_health'
            print("🔴 HIGH PRIORITY MENTAL HEALTH SUPPORT")
        elif profile['most_common_delivery'] == 'c_section' and profile['avg_postpartum_week'] < 6:
            plan_type = 'physical_recovery'
            print("💪 PHYSICAL RECOVERY FOCUS")
        elif 'milk' in profile['most_common_concern'].lower() or 'feeding' in profile['most_common_concern'].lower():
            plan_type = 'feeding_support'
            print("🍼 FEEDING SUPPORT FOCUS")
        else:
            plan_type = 'general_support'
            print("🌟 GENERAL SUPPORT & WELLNESS")
        
        plan = care_plan_templates[plan_type]
        
        print(f"Week {int(profile['avg_postpartum_week'])} Recovery Plan")
        print(f"Priorities: {', '.join(plan['priorities'])}")
        print(f"Daily Tasks:")
        for task in plan['tasks']:
            print(f"  • {task}")
        print(f"Resources:")
        for resource in plan['resources']:
            print(f"  • {resource}")

def test_user_predictions(data, kmeans, scaler, feature_names, cluster_profiles):
    """Test predictions for sample users"""
    print(f"\n=== Testing User Predictions ===")
    
    # Sample test users
    test_users = [
        {
            'name': 'Sarah - High PPD Risk, Early Postpartum',
            'epds_score': 16,
            'postpartum_week': 2,
            'delivery_type': 'c_section',
            'feeding': 'breastfeeding',
            'specific_concerns': 'Severe fatigue'
        },
        {
            'name': 'Maria - Moderate Risk, Feeding Issues',
            'epds_score': 8,
            'postpartum_week': 4,
            'delivery_type': 'vaginal',
            'feeding': 'mixed',
            'specific_concerns': 'Low milk supply'
        },
        {
            'name': 'Lisa - Low Risk, Late Postpartum',
            'epds_score': 4,
            'postpartum_week': 12,
            'delivery_type': 'vaginal',
            'feeding': 'formula',
            'specific_concerns': 'Sleep deprivation'
        }
    ]
    
    # Get label encoders from the original data
    label_encoders = {}
    for feature in ['delivery_type', 'feeding', 'specific_concerns']:
        le = LabelEncoder()
        le.fit(data[feature])
        label_encoders[feature] = le
    
    for user in test_users:
        print(f"\n--- Predicting for {user['name']} ---")
        
        # Prepare user features
        user_features = [
            user['epds_score'],
            user['postpartum_week'],
            label_encoders['delivery_type'].transform([user['delivery_type']])[0],
            label_encoders['feeding'].transform([user['feeding']])[0],
            label_encoders['specific_concerns'].transform([user['specific_concerns']])[0],
            1 if user['epds_score'] >= 13 else 0,  # is_high_risk_ppd
            1 if user['postpartum_week'] <= 2 else 0,  # is_early_postpartum
            1 if user['postpartum_week'] >= 12 else 0,  # is_late_postpartum
        ]
        
        # Scale features and predict
        user_features_scaled = scaler.transform([user_features])
        predicted_cluster = kmeans.predict(user_features_scaled)[0]
        
        print(f"Predicted Cluster: {predicted_cluster}")
        print(f"Cluster Profile:")
        profile = cluster_profiles[predicted_cluster]
        print(f"  - Average EPDS: {profile['avg_epds_score']:.1f}")
        print(f"  - Average Week: {profile['avg_postpartum_week']:.1f}")
        print(f"  - Common Delivery: {profile['most_common_delivery']}")
        print(f"  - Common Feeding: {profile['most_common_feeding']}")
        print(f"  - High Risk PPD: {profile['high_risk_ppd_percentage']:.1f}%")

def main():
    """Main demo function"""
    # Load and analyze dataset
    data = load_and_analyze_dataset()
    if data is None:
        return
    
    # Preprocess data
    data, feature_names, label_encoders = preprocess_data(data)
    
    # Find optimal clusters
    optimal_k, scaler, X_scaled = find_optimal_clusters(data, feature_names)
    
    # Train K-means model
    kmeans, cluster_labels = train_kmeans_model(data, feature_names, optimal_k, X_scaled)
    
    # Analyze clusters
    cluster_profiles = analyze_clusters(data, optimal_k)
    
    # Generate sample care plans
    generate_sample_care_plans(cluster_profiles)
    
    # Test user predictions
    test_user_predictions(data, kmeans, scaler, feature_names, cluster_profiles)
    
    print(f"\n{'='*60}")
    print("✅ K-means Care Plan Demo Complete!")
    print(f"Successfully clustered {len(data)} patients into {optimal_k} groups")
    print("Each cluster represents a distinct care profile with specific needs")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()


import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import silhouette_score

def run_analysis():
    print("=== Care Plan K-means Clustering Analysis ===\n")
    
    # Load dataset
    data_path = r"D:\postpartum-care-platform\ml\datasets\care_plan\care_plan_dataset_3000.xls"
    data = pd.read_csv(data_path)
    print(f"✅ Loaded dataset with {len(data)} records")
    
    # Dataset overview
    print(f"\nDataset Overview:")
    print(f"- EPDS Score range: {data['epds_score'].min()} to {data['epds_score'].max()}")
    print(f"- Average EPDS Score: {data['epds_score'].mean():.2f}")
    print(f"- High Risk PPD (≥13): {(data['epds_score'] >= 13).sum()} patients ({(data['epds_score'] >= 13).mean()*100:.1f}%)")
    print(f"- Postpartum weeks: {data['postpartum_week'].min()} to {data['postpartum_week'].max()}")
    
    print(f"\nDelivery Types:")
    delivery_counts = data['delivery_type'].value_counts()
    for delivery_type, count in delivery_counts.items():
        print(f"- {delivery_type}: {count} ({count/len(data)*100:.1f}%)")
    
    print(f"\nFeeding Types:")
    feeding_counts = data['feeding'].value_counts()
    for feeding_type, count in feeding_counts.items():
        print(f"- {feeding_type}: {count} ({count/len(data)*100:.1f}%)")
    
    print(f"\nTop 5 Concerns:")
    concern_counts = data['specific_concerns'].value_counts().head()
    for concern, count in concern_counts.items():
        print(f"- {concern}: {count} ({count/len(data)*100:.1f}%)")
    
    # Feature engineering
    data['is_high_risk_ppd'] = (data['epds_score'] >= 13).astype(int)
    data['is_early_postpartum'] = (data['postpartum_week'] <= 2).astype(int)
    data['is_late_postpartum'] = (data['postpartum_week'] >= 12).astype(int)
    
    # Encode categorical variables
    le_delivery = LabelEncoder()
    le_feeding = LabelEncoder()
    le_concerns = LabelEncoder()
    
    data['delivery_encoded'] = le_delivery.fit_transform(data['delivery_type'])
    data['feeding_encoded'] = le_feeding.fit_transform(data['feeding'])
    data['concerns_encoded'] = le_concerns.fit_transform(data['specific_concerns'])
    
    print(f"\n✅ Feature engineering complete")
    print(f"- Encoded {len(le_delivery.classes_)} delivery types")
    print(f"- Encoded {len(le_feeding.classes_)} feeding types") 
    print(f"- Encoded {len(le_concerns.classes_)} concern types")
    
    # Prepare features for clustering
    feature_columns = [
        'epds_score', 'postpartum_week', 'delivery_encoded', 
        'feeding_encoded', 'concerns_encoded', 'is_high_risk_ppd', 
        'is_early_postpartum', 'is_late_postpartum'
    ]
    
    X = data[feature_columns].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"✅ Prepared {len(feature_columns)} features for clustering")
    
    # Find optimal number of clusters
    print(f"\n=== Finding Optimal Clusters ===")
    silhouette_scores = []
    K_range = range(2, 8)
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, cluster_labels)
        silhouette_scores.append(score)
        print(f"k={k}: Silhouette Score = {score:.3f}")
    
    optimal_k = K_range[np.argmax(silhouette_scores)]
    best_score = max(silhouette_scores)
    print(f"\n✅ Optimal number of clusters: {optimal_k}")
    print(f"✅ Best silhouette score: {best_score:.3f}")
    
    # Train final K-means model
    print(f"\n=== Training Final K-means Model ===")
    kmeans_final = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    final_labels = kmeans_final.fit_predict(X_scaled)
    data['cluster'] = final_labels
    
    print(f"✅ Model trained with {optimal_k} clusters")
    
    # Analyze each cluster
    print(f"\n=== Cluster Analysis ===")
    cluster_profiles = {}
    
    for cluster_id in range(optimal_k):
        cluster_data = data[data['cluster'] == cluster_id]
        size = len(cluster_data)
        percentage = size / len(data) * 100
        
        profile = {
            'size': size,
            'percentage': percentage,
            'avg_epds': cluster_data['epds_score'].mean(),
            'avg_week': cluster_data['postpartum_week'].mean(),
            'high_risk_pct': cluster_data['is_high_risk_ppd'].mean() * 100,
            'early_postpartum_pct': cluster_data['is_early_postpartum'].mean() * 100,
            'common_delivery': cluster_data['delivery_type'].mode().iloc[0],
            'common_feeding': cluster_data['feeding'].mode().iloc[0],
            'common_concern': cluster_data['specific_concerns'].mode().iloc[0]
        }
        
        cluster_profiles[cluster_id] = profile
        
        print(f"\n--- Cluster {cluster_id} Profile ---")
        print(f"Size: {size} patients ({percentage:.1f}%)")
        print(f"Average EPDS Score: {profile['avg_epds']:.1f}")
        print(f"Average Postpartum Week: {profile['avg_week']:.1f}")
        print(f"High Risk PPD: {profile['high_risk_pct']:.1f}%")
        print(f"Early Postpartum: {profile['early_postpartum_pct']:.1f}%")
        print(f"Most Common Delivery: {profile['common_delivery']}")
        print(f"Most Common Feeding: {profile['common_feeding']}")
        print(f"Most Common Concern: {profile['common_concern']}")
    
    # Generate care plan recommendations for each cluster
    print(f"\n=== Care Plan Recommendations by Cluster ===")
    
    care_plan_mapping = {}
    
    for cluster_id, profile in cluster_profiles.items():
        print(f"\n--- Cluster {cluster_id} Care Plan ---")
        
        # Determine care plan focus based on cluster characteristics
        if profile['high_risk_pct'] > 60:
            focus = "🔴 HIGH-PRIORITY MENTAL HEALTH SUPPORT"
            priorities = ["Immediate Mental Health Screening", "Professional Support", "Crisis Prevention"]
            tasks = [
                "Schedule mental health evaluation within 24-48 hours",
                "Practice mindfulness meditation (10 minutes daily)",
                "Connect with support person twice daily",
                "Monitor mood symptoms and seek help if worsening"
            ]
            resources = [
                "Postpartum Depression Screening Tools",
                "Mental Health Crisis Hotline: 988",
                "Local Mental Health Professional Directory"
            ]
        
        elif profile['common_delivery'] == 'c_section' and profile['avg_week'] < 6:
            focus = "💪 PHYSICAL RECOVERY & HEALING FOCUS"
            priorities = ["Surgical Recovery", "Pain Management", "Gradual Activity Increase"]
            tasks = [
                "Monitor C-section incision daily for infection signs",
                "Take prescribed pain medication as directed",
                "Gentle walking for 10-15 minutes daily",
                "Perform pelvic floor exercises (5 minutes daily)"
            ]
            resources = [
                "C-Section Recovery Timeline Guide",
                "Post-Surgical Exercise Videos",
                "Infection Warning Signs Checklist"
            ]
        
        elif 'milk' in profile['common_concern'].lower() or 'feeding' in profile['common_concern'].lower():
            focus = "🍼 FEEDING & LACTATION SUPPORT"
            priorities = ["Feeding Success", "Lactation Support", "Nutritional Wellness"]
            tasks = [
                "Track feeding sessions and baby's output",
                "Stay hydrated (8-10 glasses of water daily)",
                "Contact lactation consultant if supply concerns",
                "Maintain regular, nutritious meal schedule"
            ]
            resources = [
                "Breastfeeding Position Guide",
                "Lactation Consultant Directory",
                "Nutrition for Breastfeeding Mothers"
            ]
        
        elif profile['avg_week'] > 8:
            focus = "🌟 WELLNESS & FAMILY ADJUSTMENT"
            priorities = ["Self-Care Routine", "Family Support", "Long-term Wellness"]
            tasks = [
                "Establish daily self-care routine (30 minutes)",
                "Schedule regular family support check-ins",
                "Connect with other parents in similar stage",
                "Plan gradual return to normal activities"
            ]
            resources = [
                "New Parent Support Groups",
                "Self-Care for New Mothers Guide",
                "Family Adjustment Resources"
            ]
        
        else:
            focus = "⚖️ BALANCED RECOVERY SUPPORT"
            priorities = ["Overall Wellness", "Gradual Recovery", "Support Building"]
            tasks = [
                "Monitor physical and emotional recovery daily",
                "Maintain regular sleep schedule when possible",
                "Ask for help with household tasks",
                "Practice stress management techniques"
            ]
            resources = [
                "General Postpartum Recovery Guide",
                "Stress Management Techniques",
                "Building Your Support Network"
            ]
        
        care_plan_mapping[cluster_id] = {
            'focus': focus,
            'priorities': priorities,
            'tasks': tasks,
            'resources': resources
        }
        
        print(f"Focus: {focus}")
        print(f"Priorities: {', '.join(priorities)}")
        print(f"Daily Tasks:")
        for task in tasks:
            print(f"  • {task}")
        print(f"Resources:")
        for resource in resources:
            print(f"  • {resource}")
    
    # Test sample predictions
    print(f"\n=== Testing Sample User Predictions ===")
    
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
            'postpartum_week': 5,
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
    
    for user in test_users:
        print(f"\n--- Testing: {user['name']} ---")
        
        # Prepare user features
        user_features = [
            user['epds_score'],
            user['postpartum_week'],
            le_delivery.transform([user['delivery_type']])[0],
            le_feeding.transform([user['feeding']])[0],
            le_concerns.transform([user['specific_concerns']])[0],
            1 if user['epds_score'] >= 13 else 0,
            1 if user['postpartum_week'] <= 2 else 0,
            1 if user['postpartum_week'] >= 12 else 0
        ]
        
        # Scale and predict
        user_scaled = scaler.transform([user_features])
        predicted_cluster = kmeans_final.predict(user_scaled)[0]
        
        print(f"Predicted Cluster: {predicted_cluster}")
        print(f"Care Plan Focus: {care_plan_mapping[predicted_cluster]['focus']}")
        print(f"Top Priority: {care_plan_mapping[predicted_cluster]['priorities'][0]}")
        
        # Show similar patients in cluster
        similar_patients = cluster_profiles[predicted_cluster]
        print(f"Similar Patients Profile:")
        print(f"  - Average EPDS: {similar_patients['avg_epds']:.1f}")
        print(f"  - Average Week: {similar_patients['avg_week']:.1f}")
        print(f"  - High Risk Rate: {similar_patients['high_risk_pct']:.1f}%")
    
    print(f"\n{'='*60}")
    print("✅ K-means Care Plan Analysis Complete!")
    print(f"Successfully analyzed {len(data)} patient records")
    print(f"Identified {optimal_k} distinct care profiles")
    print(f"Generated personalized care plan templates")
    print(f"Model ready for real-time care plan generation")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_analysis()

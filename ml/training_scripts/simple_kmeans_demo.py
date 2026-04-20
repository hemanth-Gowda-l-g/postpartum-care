import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import silhouette_score

def main():
    print("=== Care Plan K-means Clustering Demo ===\n")
    
    # Load the dataset
    data_path = r'D:\postpartum-care-platform\ml\datasets\care_plan\care_plan_dataset_3000.xls'
    
    try:
        data = pd.read_csv(data_path)
        print(f"✅ Loaded dataset with {len(data)} records")
        
        # Basic statistics
        print(f"\nDataset Overview:")
        print(f"- EPDS Score range: {data['epds_score'].min()} - {data['epds_score'].max()}")
        print(f"- Average EPDS: {data['epds_score'].mean():.2f}")
        print(f"- High Risk PPD (≥13): {(data['epds_score'] >= 13).sum()} patients ({(data['epds_score'] >= 13).mean()*100:.1f}%)")
        print(f"- Postpartum weeks range: {data['postpartum_week'].min()} - {data['postpartum_week'].max()}")
        
        print(f"\nDelivery Types:")
        for delivery, count in data['delivery_type'].value_counts().items():
            print(f"- {delivery}: {count} ({count/len(data)*100:.1f}%)")
        
        print(f"\nFeeding Types:")
        for feeding, count in data['feeding'].value_counts().items():
            print(f"- {feeding}: {count} ({count/len(data)*100:.1f}%)")
        
        print(f"\nTop 5 Concerns:")
        for concern, count in data['specific_concerns'].value_counts().head().items():
            print(f"- {concern}: {count} ({count/len(data)*100:.1f}%)")
        
        # Feature engineering
        data['is_high_risk_ppd'] = (data['epds_score'] >= 13).astype(int)
        data['is_early_postpartum'] = (data['postpartum_week'] <= 2).astype(int)
        data['is_late_postpartum'] = (data['postpartum_week'] >= 12).astype(int)
        
        # Encode categorical variables
        le_delivery = LabelEncoder()
        le_feeding = LabelEncoder()
        le_concerns = LabelEncoder()
        
        data['delivery_type_encoded'] = le_delivery.fit_transform(data['delivery_type'])
        data['feeding_encoded'] = le_feeding.fit_transform(data['feeding'])
        data['concerns_encoded'] = le_concerns.fit_transform(data['specific_concerns'])
        
        print(f"\n✅ Encoded categorical features")
        
        # Select features for clustering
        features = ['epds_score', 'postpartum_week', 'delivery_type_encoded', 
                   'feeding_encoded', 'concerns_encoded', 'is_high_risk_ppd', 
                   'is_early_postpartum', 'is_late_postpartum']
        
        X = data[features].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        print(f"✅ Prepared {len(features)} features for clustering")
        
        # Find optimal clusters
        print(f"\n=== Finding Optimal Clusters ===")
        silhouette_scores = []
        K_range = range(2, 8)
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels)
            silhouette_scores.append(score)
            print(f"k={k}: Silhouette Score = {score:.3f}")
        
        optimal_k = K_range[np.argmax(silhouette_scores)]
        best_score = max(silhouette_scores)
        print(f"\n✅ Optimal clusters: {optimal_k} (Silhouette: {best_score:.3f})")
        
        # Train final model
        print(f"\n=== Training K-means with {optimal_k} clusters ===")
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        data['cluster'] = cluster_labels
        
        # Analyze clusters
        print(f"\n=== Cluster Analysis ===")
        for cluster_id in range(optimal_k):
            cluster_data = data[data['cluster'] == cluster_id]
            size = len(cluster_data)
            percentage = size / len(data) * 100
            
            print(f"\n--- Cluster {cluster_id} ---")
            print(f"Size: {size} patients ({percentage:.1f}%)")
            print(f"Average EPDS: {cluster_data['epds_score'].mean():.1f}")
            print(f"Average Week: {cluster_data['postpartum_week'].mean():.1f}")
            print(f"High Risk PPD: {cluster_data['is_high_risk_ppd'].mean()*100:.1f}%")
            print(f"Most common delivery: {cluster_data['delivery_type'].mode().iloc[0]}")
            print(f"Most common feeding: {cluster_data['feeding'].mode().iloc[0]}")
            print(f"Most common concern: {cluster_data['specific_concerns'].mode().iloc[0]}")
        
        # Test predictions
        print(f"\n=== Testing Sample Predictions ===")
        
        test_cases = [
            {
                'name': 'High Risk PPD, Early Postpartum',
                'epds_score': 16,
                'postpartum_week': 2,
                'delivery_type': 'c_section',
                'feeding': 'breastfeeding',
                'specific_concerns': 'Severe fatigue'
            },
            {
                'name': 'Moderate Risk, Feeding Issues',
                'epds_score': 8,
                'postpartum_week': 5,
                'delivery_type': 'vaginal',
                'feeding': 'mixed',
                'specific_concerns': 'Low milk supply'
            },
            {
                'name': 'Low Risk, Late Postpartum',
                'epds_score': 4,
                'postpartum_week': 12,
                'delivery_type': 'vaginal',
                'feeding': 'formula',
                'specific_concerns': 'Sleep deprivation'
            }
        ]
        
        for test_case in test_cases:
            print(f"\n--- {test_case['name']} ---")
            
            # Prepare features
            test_features = [
                test_case['epds_score'],
                test_case['postpartum_week'],
                le_delivery.transform([test_case['delivery_type']])[0],
                le_feeding.transform([test_case['feeding']])[0],
                le_concerns.transform([test_case['specific_concerns']])[0],
                1 if test_case['epds_score'] >= 13 else 0,
                1 if test_case['postpartum_week'] <= 2 else 0,
                1 if test_case['postpartum_week'] >= 12 else 0
            ]
            
            test_scaled = scaler.transform([test_features])
            predicted_cluster = kmeans.predict(test_scaled)[0]
            
            print(f"Predicted Cluster: {predicted_cluster}")
            
            # Show cluster characteristics
            cluster_data = data[data['cluster'] == predicted_cluster]
            print(f"Cluster Profile:")
            print(f"  - Avg EPDS: {cluster_data['epds_score'].mean():.1f}")
            print(f"  - Avg Week: {cluster_data['postpartum_week'].mean():.1f}")
            print(f"  - High Risk: {cluster_data['is_high_risk_ppd'].mean()*100:.1f}%")
        
        # Generate care plan recommendations
        print(f"\n=== Care Plan Recommendations by Cluster ===")
        
        care_plans = {
            0: {
                'focus': 'High-Risk Mental Health Support',
                'priorities': ['Mental Health Screening', 'Professional Support', 'Crisis Prevention'],
                'tasks': [
                    'Schedule mental health evaluation within 48 hours',
                    'Practice daily mindfulness (10 minutes)',
                    'Connect with support person twice daily',
                    'Monitor mood and symptoms hourly'
                ]
            },
            1: {
                'focus': 'Physical Recovery & Pain Management',
                'priorities': ['Healing Support', 'Pain Control', 'Gradual Activity'],
                'tasks': [
                    'Monitor incision/healing sites daily',
                    'Take pain medication as prescribed',
                    'Gentle walking (10-15 minutes)',
                    'Pelvic floor exercises (5 minutes)'
                ]
            },
            2: {
                'focus': 'Feeding & Nutrition Support',
                'priorities': ['Feeding Success', 'Lactation Support', 'Nutrition'],
                'tasks': [
                    'Track feeding sessions and output',
                    'Contact lactation consultant if needed',
                    'Stay hydrated (8-10 glasses daily)',
                    'Maintain regular meal schedule'
                ]
            },
            3: {
                'focus': 'General Wellness & Support',
                'priorities': ['Self-Care', 'Family Support', 'Routine Building'],
                'tasks': [
                    'Establish daily self-care routine',
                    'Ask for help with household tasks',
                    'Connect with other new parents',
                    'Maintain regular sleep schedule'
                ]
            }
        }
        
        for cluster_id in range(min(optimal_k, len(care_plans))):
            if cluster_id in care_plans:
                plan = care_plans[cluster_id]
                cluster_size = len(data[data['cluster'] == cluster_id])
                
                print(f"\n--- Cluster {cluster_id} Care Plan ({cluster_size} patients) ---")
                print(f"🎯 Focus: {plan['focus']}")
                print(f"📋 Priorities: {', '.join(plan['priorities'])}")
                print(f"✅ Daily Tasks:")
                for task in plan['tasks']:
                    print(f"   • {task}")
        
        print(f"\n{'='*60}")
        print("✅ K-means Care Plan Clustering Complete!")
        print(f"Successfully analyzed {len(data)} patients")
        print(f"Identified {optimal_k} distinct care profiles")
        print(f"Model ready for personalized care plan generation")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

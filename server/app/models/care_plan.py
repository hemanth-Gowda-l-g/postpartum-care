from datetime import datetime, timedelta
from bson import ObjectId
from ..utils.database import mongo
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib
import os

class CarePlan:
    """
    Care Plan model for managing ML-powered personalized postpartum recovery plans
    """
    
    def __init__(self):
        # Get the absolute path to the project root (go up 3 levels from server/app/models)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        self.model_path = os.path.join(project_root, 'ml', 'models', 'care_plan_kmeans_model.pkl')
        self.kmeans_model = None
        self.scaler = None
        self.label_encoders = {}
        self.cluster_profiles = {}
        self.load_model()
    
    def load_model(self):
        """Load the trained K-means model"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.kmeans_model = model_data.get('kmeans_model')
                self.scaler = model_data.get('scaler')
                self.label_encoders = model_data.get('label_encoders', {})
                self.cluster_profiles = model_data.get('cluster_profiles', {})
                print("✅ Care Plan K-means model loaded successfully")
            else:
                print("⚠️ Care Plan model not found, will use fallback logic")
                self.initialize_fallback_model()
        except Exception as e:
            print(f"Error loading Care Plan model: {e}")
            self.initialize_fallback_model()
    
    def initialize_fallback_model(self):
        """Initialize fallback model with sample data for demonstration"""
        # Create sample cluster profiles based on common postpartum scenarios
        self.cluster_profiles = {
            0: {  # High-risk PPD, early postpartum
                'avg_epds_score': 16.5,
                'avg_postpartum_week': 2.1,
                'most_common_delivery': 'c_section',
                'most_common_feeding': 'breastfeeding',
                'most_common_concern': 'Severe fatigue',
                'high_risk_ppd_percentage': 85.0,
                'care_focus': ['mental_health', 'physical_recovery']
            },
            1: {  # Moderate risk, feeding issues
                'avg_epds_score': 8.2,
                'avg_postpartum_week': 4.5,
                'most_common_delivery': 'vaginal',
                'most_common_feeding': 'mixed',
                'most_common_concern': 'Low milk supply',
                'high_risk_ppd_percentage': 25.0,
                'care_focus': ['feeding_support', 'physical_recovery']
            },
            2: {  # Low risk, late postpartum
                'avg_epds_score': 4.1,
                'avg_postpartum_week': 10.2,
                'most_common_delivery': 'vaginal',
                'most_common_feeding': 'formula',
                'most_common_concern': 'Sleep deprivation',
                'high_risk_ppd_percentage': 5.0,
                'care_focus': ['family_support', 'self_care']
            },
            3: {  # C-section recovery focus
                'avg_epds_score': 7.8,
                'avg_postpartum_week': 3.2,
                'most_common_delivery': 'c_section',
                'most_common_feeding': 'breastfeeding',
                'most_common_concern': 'Incision pain',
                'high_risk_ppd_percentage': 35.0,
                'care_focus': ['physical_recovery', 'pain_management']
            },
            4: {  # Support system issues
                'avg_epds_score': 12.1,
                'avg_postpartum_week': 6.8,
                'most_common_delivery': 'assisted',
                'most_common_feeding': 'mixed',
                'most_common_concern': 'No family support',
                'high_risk_ppd_percentage': 60.0,
                'care_focus': ['family_support', 'mental_health']
            }
        }
    
    @staticmethod
    def create_care_plan(user_id, user_profile):
        """
        Create a new care plan for a user based on their profile using ML clustering
        Allow multiple generations for testing purposes
        
        Args:
            user_id (str): User's MongoDB ObjectId
            user_profile (dict): User profile data including delivery info, health metrics
        
        Returns:
            str: Care plan ID if successful, None otherwise
        """
        try:
            # Remove any existing care plans for this user (for testing)
            mongo.db.care_plans.delete_many({'user_id': ObjectId(user_id)})
            
            care_plan_model = CarePlan()
            
            # Generate ML-powered care plan
            ml_care_plan = care_plan_model.generate_ml_care_plan(user_profile)
            
            care_plan_data = {
                'user_id': ObjectId(user_id),
                'user_profile': user_profile,
                'cluster_id': ml_care_plan.get('cluster_id', 0),
                'postpartum_week': ml_care_plan.get('postpartum_week', user_profile.get('postpartum_week', 4)),
                'cluster_info': ml_care_plan.get('cluster_info', {}),
                'weekly_priorities': ml_care_plan.get('weekly_priorities', []),
                'daily_tasks': ml_care_plan.get('daily_tasks', []),
                'resources': ml_care_plan.get('resources', []),
                'completed_tasks': ml_care_plan.get('completed_tasks', 0),
                'completion_percentage': ml_care_plan.get('completion_percentage', 0),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'week_start': datetime.utcnow(),
                'is_active': True
            }
            
            result = mongo.db.care_plans.insert_one(care_plan_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error creating care plan: {e}")
            return None
    
    def generate_ml_care_plan(self, user_profile):
        """Generate ML-powered care plan using K-means clustering"""
        try:
            # Predict cluster (fallback to rule-based if model not available)
            cluster_id = self.predict_cluster(user_profile)
            
            # Get cluster profile
            cluster_profile = self.cluster_profiles.get(cluster_id, self.cluster_profiles[0])
            
            # Generate personalized care plan
            care_plan = self.create_personalized_plan(user_profile, cluster_profile, cluster_id)
            
            return care_plan
            
        except Exception as e:
            print(f"Error generating ML care plan: {e}")
            return self.generate_fallback_plan(user_profile)
    
    def predict_cluster(self, user_profile):
        """Predict cluster for user profile"""
        if self.kmeans_model and self.scaler:
            try:
                # Prepare features for ML model
                features = self.prepare_user_features(user_profile)
                features_scaled = self.scaler.transform([features])
                cluster_id = self.kmeans_model.predict(features_scaled)[0]
                return int(cluster_id)
            except Exception as e:
                print(f"Error in ML prediction: {e}")
        
        # Fallback rule-based cluster assignment
        return self.rule_based_cluster_assignment(user_profile)
    
    def rule_based_cluster_assignment(self, user_profile):
        """Rule-based cluster assignment as fallback"""
        # Use PPD risk percentage if available, otherwise use EPDS score
        ppd_risk = user_profile.get('ppd_risk_percentage')
        if ppd_risk is not None:
            risk_score = ppd_risk
            high_risk_threshold = 70
            moderate_risk_threshold = 40
        else:
            epds_score = user_profile.get('epds_score', 10)
            risk_score = epds_score * 3.7  # Convert EPDS to percentage scale
            high_risk_threshold = 55
            moderate_risk_threshold = 30
        
        postpartum_week = user_profile.get('postpartum_week', 4)
        delivery_type = user_profile.get('delivery_type', 'vaginal')
        concerns = user_profile.get('specific_concerns', '').lower()
        
        # High-risk PPD, early postpartum
        if risk_score >= high_risk_threshold and postpartum_week <= 3:
            return 0
        
        # Feeding issues
        elif 'milk' in concerns or 'feeding' in concerns:
            return 1
        
        # Late postpartum, low risk
        elif postpartum_week >= 10 and risk_score < moderate_risk_threshold:
            return 2
        
        # C-section recovery
        elif delivery_type == 'c_section' and postpartum_week <= 6:
            return 3
        
        # Support system issues
        elif 'support' in concerns or risk_score >= moderate_risk_threshold:
            return 4
        
        # Default to moderate risk
        else:
            return 1
    
    def prepare_user_features(self, user_profile):
        """Prepare user features for ML model (7 features to match trained model)"""
        # Use PPD risk percentage if available, otherwise convert EPDS score
        ppd_risk = user_profile.get('ppd_risk_percentage')
        if ppd_risk is not None:
            epds_equivalent = ppd_risk * 0.27  # Convert percentage to EPDS scale
            is_high_risk = ppd_risk >= 50  # 50% risk threshold
        else:
            epds_equivalent = user_profile.get('epds_score', 10)
            is_high_risk = epds_equivalent >= 13
        
        # Match the 7 features expected by the trained model
        features = [
            epds_equivalent,
            user_profile.get('postpartum_week', 4),
            user_profile.get('postpartum_week', 4) * 7,  # days_since_delivery
            1 if user_profile.get('delivery_type') == 'c_section' else 0,  # delivery_type_encoded
            1 if user_profile.get('feeding') == 'breastfeeding' else 0,  # feeding_encoded
            1 if is_high_risk else 0,  # is_high_risk_ppd
            1 if user_profile.get('postpartum_week', 4) <= 2 else 0,  # is_early_postpartum
        ]
        return features
    
    def generate_care_plan_tasks(self, user_profile, cluster_id):
        """Generate ML-driven personalized care plan tasks"""
        care_plan = {
            'user_id': user_profile['user_id'],
            'postpartum_week': user_profile['postpartum_week'],
            'cluster_id': cluster_id,
            'cluster_info': self.cluster_profiles.get(cluster_id, {}),
            'sentiment_context': user_profile.get('sentiment_context', {}),
            'weekly_priorities': [],
            'daily_tasks': [],
            'resources': [],
            'health_monitoring': self._generate_health_monitoring_plan(user_profile, cluster_id),
            'personalization_context': self._build_personalization_context(user_profile),
            'created_at': datetime.utcnow(),
            'week_start': datetime.utcnow(),
            'completed_tasks': 0,
            'completion_percentage': 0
        }
        
        # Generate ML-driven daily tasks based on comprehensive analysis
        daily_tasks = self._generate_ml_daily_tasks(user_profile, cluster_id)
        care_plan['daily_tasks'] = daily_tasks
        
        # Generate dynamic weekly priorities based on ML predictions
        weekly_priorities = self._generate_ml_weekly_priorities(user_profile, cluster_id)
        care_plan['weekly_priorities'] = weekly_priorities
        
        # Generate personalized resources
        resources = self._generate_personalized_resources(user_profile, cluster_id)
        care_plan['resources'] = resources
        
        # Sentiment-adaptive suggested daily time budget
        sctx = user_profile.get('sentiment_context', {}) or {}
        s = sctx.get('sent_blended')
        if s is None:
            suggested_budget = 60
        elif s <= -0.3:
            suggested_budget = 40
        elif s <= 0.0:
            suggested_budget = 50
        elif s >= 0.4:
            suggested_budget = 75
        else:
            suggested_budget = 60
        care_plan['daily_time_budget_minutes'] = suggested_budget
        
        return care_plan
    
    def _generate_ml_daily_tasks(self, user_profile, cluster_id):
        """Generate ML-driven daily tasks based on user profile and cluster"""
        tasks = []
        
        # Extract key variables for ML-based task generation
        postpartum_week = user_profile.get('postpartum_week', 4)
        epds_score = user_profile.get('epds_score', 10)
        delivery_type = user_profile.get('delivery_type', 'vaginal')
        feeding = user_profile.get('feeding', 'breastfeeding')
        pain_level = user_profile.get('pain_level', 3)
        mood_score = user_profile.get('mood_score', 5)
        energy_level = user_profile.get('energy_level', 4)
        sleep_hours = user_profile.get('sleep_hours', 5)
        sctx = user_profile.get('sentiment_context', {}) or {}
        sent_blended = sctx.get('sent_blended')
        
        # Mental health tasks (ML-driven based on EPDS score and mood)
        if epds_score >= 12 or mood_score <= 4:
            if epds_score >= 15:  # High risk
                tasks.extend([
                    {
                        'title': 'Complete mood check-in questionnaire',
                        'description': 'Track your emotional state to identify patterns',
                        'category': 'mental_health',
                        'priority': 'high',
                        'duration_minutes': 5
                    },
                    {
                        'title': 'Practice guided breathing exercise',
                        'description': 'Use deep breathing to manage anxiety and stress',
                        'category': 'mental_health',
                        'priority': 'high',
                        'duration_minutes': 10
                    }
                ])
            else:
                tasks.append({
                    'title': 'Journal three positive moments from today',
                    'description': 'Focus on gratitude and positive experiences',
                    'category': 'mental_health',
                    'priority': 'medium',
                    'duration_minutes': 10
                })
        
        # Physical recovery tasks (ML-driven based on delivery type and pain level)
        if delivery_type == 'c_section' or pain_level >= 5:
            if delivery_type == 'c_section' and postpartum_week <= 2:
                tasks.extend([
                    {
                        'title': 'Monitor incision site for healing',
                        'description': 'Check for redness, swelling, or unusual discharge',
                        'category': 'physical_recovery',
                        'priority': 'high',
                        'duration_minutes': 5
                    },
                    {
                        'title': 'Practice gentle abdominal breathing',
                        'description': 'Support core recovery with breathing exercises',
                        'category': 'physical_recovery',
                        'priority': 'medium',
                        'duration_minutes': 10
                    }
                ])
            elif postpartum_week > 2:
                tasks.append({
                    'title': 'Take a 10-15 minute gentle walk',
                    'description': 'Gradually increase activity as cleared by doctor',
                    'category': 'physical_recovery',
                    'priority': 'medium',
                    'duration_minutes': 15
                })
        
        # Feeding support tasks (ML-driven based on feeding type)
        if feeding in ['breastfeeding', 'mixed']:
            tasks.extend([
                {
                    'title': 'Log feeding session details',
                    'description': 'Track duration, frequency, and baby satisfaction',
                    'category': 'feeding',
                    'priority': 'high',
                    'duration_minutes': 3
                },
                {
                    'title': 'Perform breast care routine',
                    'description': 'Apply nipple cream and check for issues',
                    'category': 'feeding',
                    'priority': 'medium',
                    'duration_minutes': 5
                }
            ])
        
        # Sleep optimization tasks (ML-driven based on sleep patterns)
        if sleep_hours < 6 or energy_level <= 4:
            if sleep_hours < 5:
                tasks.append({
                    'title': 'Plan strategic nap opportunity',
                    'description': 'Identify 20-30 minute nap window when baby sleeps',
                    'category': 'sleep',
                    'priority': 'high',
                    'duration_minutes': 30
                })
            
            if energy_level <= 3:
                tasks.append({
                    'title': 'Practice energy-boosting stretches',
                    'description': 'Gentle movements to improve circulation and energy',
                    'category': 'wellness',
                    'priority': 'medium',
                    'duration_minutes': 10
                })
        
        # Essential wellness tasks (always included but personalized)
        tasks.extend([
            {
                'title': 'Hydration check and water intake',
                'description': 'Aim for 8-10 glasses, more if breastfeeding',
                'category': 'wellness',
                'priority': 'high',
                'duration_minutes': 2
            },
            {
                'title': 'Take prescribed vitamins/supplements',
                'description': 'Continue prenatal vitamins as recommended',
                'category': 'wellness',
                'priority': 'high',
                'duration_minutes': 1
            }
        ])

        # Sentiment-aware adjustments to adapt intensity and prioritization
        if sent_blended is not None:
            # Low sentiment: lighter/self-care focus, boost MH and sleep, reduce strenuous tasks
            if sent_blended <= -0.3:
                # Add a gentle self-care task
                tasks.append({
                    'title': '10-minute mindful self-care break',
                    'description': 'Quiet time, breathing, or short compassion meditation',
                    'category': 'mental_health',
                    'priority': 'high',
                    'duration_minutes': 10
                })
                # Encourage sleep hygiene if sleep is low
                if sleep_hours < 6:
                    tasks.append({
                        'title': 'Bedtime wind-down routine',
                        'description': 'Dim lights, no screens 30 min before bed, warm shower',
                        'category': 'sleep',
                        'priority': 'high',
                        'duration_minutes': 15
                    })
                # Reduce duration for medium/strenuous physical tasks
                for t in tasks:
                    if t.get('category') == 'physical_recovery' and t.get('duration_minutes', 0) >= 10:
                        t['duration_minutes'] = max(5, int(t['duration_minutes'] * 0.7))
                        if t.get('priority') == 'medium':
                            t['priority'] = 'low'
            # Moderately low sentiment: slight softening
            elif sent_blended < 0.1:
                for t in tasks:
                    if t.get('category') == 'physical_recovery' and t.get('duration_minutes', 0) >= 15:
                        t['duration_minutes'] = int(t['duration_minutes'] * 0.85)
            # Positive sentiment: allow gentle progressions
            elif sent_blended >= 0.4 and energy_level >= 4 and pain_level <= 4:
                for t in tasks:
                    if t.get('category') == 'physical_recovery' and t.get('duration_minutes', 0) >= 10:
                        t['duration_minutes'] = min(25, int(t['duration_minutes'] * 1.2))
                        if t.get('priority') == 'medium':
                            t['priority'] = 'high'

        # Add unique IDs and mark as incomplete
        for i, task in enumerate(tasks):
            task['id'] = f"{task['category']}_{i+1}"
            task['completed'] = False

        return tasks
    
    def _generate_ml_weekly_priorities(self, user_profile, cluster_id):
        """Generate ML-driven weekly priorities"""
        priorities = []
        
        # Priority 1: Based on highest risk factor
        epds_score = user_profile.get('epds_score', 10)
        if epds_score >= 12:
            priorities.append({
                'icon': '🧠',
                'title': 'Mental Health & Emotional Wellbeing',
                'description': 'Focus on mood monitoring and stress management techniques'
            })
        # Elevate MH priority when sentiment is low
        sctx = user_profile.get('sentiment_context', {}) or {}
        if sctx.get('sent_blended') is not None and sctx.get('sent_blended') <= -0.3:
            priorities.append({
                'icon': '😔',
                'title': 'Gentle Self-Care Focus',
                'description': 'Prioritize low-effort self-care and rest this week'
            })
        
        # Priority 2: Based on physical needs
        delivery_type = user_profile.get('delivery_type', 'vaginal')
        pain_level = user_profile.get('pain_level', 3)
        if delivery_type == 'c_section' or pain_level >= 5:
            priorities.append({
                'icon': '💪',
                'title': 'Physical Recovery & Healing',
                'description': 'Support your body\'s healing process with targeted activities'
            })
        
        # Priority 3: Based on feeding and nutrition
        feeding = user_profile.get('feeding', 'breastfeeding')
        if feeding in ['breastfeeding', 'mixed']:
            priorities.append({
                'icon': '🍼',
                'title': 'Feeding Success & Nutrition',
                'description': 'Optimize feeding experience and nutritional intake'
            })
        
        # Default priorities if none of the above apply
        if not priorities:
            priorities = [
                {
                    'icon': '💪',
                    'title': 'Physical Recovery',
                    'description': 'Focus on gentle recovery and healing'
                },
                {
                    'icon': '😌',
                    'title': 'Mental Wellbeing',
                    'description': 'Maintain emotional balance and self-care'
                },
                {
                    'icon': '🤱',
                    'title': 'Baby Care & Bonding',
                    'description': 'Build confidence in caring for your baby'
                }
            ]
        
        return priorities[:3]  # Limit to top 3 priorities
    
    def _generate_personalized_resources(self, user_profile, cluster_id):
        """Generate personalized resources based on ML analysis"""
        resources = []
        
        # Helper to create resource objects
        def R(title, url=None, rtype=None):
            item = {'title': title}
            if url:
                item['url'] = url
            if rtype:
                item['type'] = rtype
            return item
        
        # Base resources
        resources.extend([
            R(
                'Emergency: When to Call Your Doctor - Personalized Warning Signs',
                'https://www.acog.org/womens-health/faqs/postpartum-warning-signs',
                'emergency'
            ),
            R(
                'Guide: Week-by-Week Recovery Expectations',
                'https://www.nhs.uk/conditions/baby/support-and-services/your-postnatal-check/',
                'guide'
            )
        ])
        
        # Condition-specific resources
        epds_score = user_profile.get('epds_score', 10)
        if epds_score >= 12:
            resources.extend([
                R('App: Mood tracking and mental health support', 'https://www.7cups.com/', 'app'),
                R('Hotline: 24/7 Postpartum Support International', 'https://www.postpartum.net/get-help/help-for-moms/', 'hotline'),
                R('Article: Understanding Your PPD Risk Factors', 'https://www.who.int/news-room/fact-sheets/detail/depression', 'article')
            ])
        
        delivery_type = user_profile.get('delivery_type', 'vaginal')
        if delivery_type == 'c_section':
            resources.extend([
                R('Video: C-Section Recovery Exercise Progression', 'https://www.youtube.com/watch?v=xqR1zQbN0tM', 'video'),
                R('Guide: Scar Care and Healing Timeline', 'https://www.healthline.com/health/pregnancy/c-section-recovery', 'guide')
            ])
        
        feeding = user_profile.get('feeding', 'breastfeeding')
        if feeding == 'breastfeeding':
            resources.extend([
                R('Contact: Local Lactation Consultant Directory', 'https://www.ilca.org/why-ibclc/falc', 'contact'),
                R('App: Breastfeeding tracker with AI insights', 'https://www.huckleberrycare.com/', 'app')
            ])
        
        return resources
    
    def _build_personalization_context(self, user_profile):
        """Build comprehensive personalization context"""
        return {
            'risk_factors': self._identify_risk_factors(user_profile),
            'support_level': user_profile.get('support_level', 3),
            'cultural_considerations': user_profile.get('cultural_preferences', {}),
            'previous_experience': {
                'pregnancies': user_profile.get('previous_pregnancies', 0),
                'complications': user_profile.get('has_complications', False)
            },
            'current_challenges': self._identify_current_challenges(user_profile)
        }
    
    def _identify_risk_factors(self, user_profile):
        """Identify risk factors based on user profile"""
        risk_factors = []
        
        if user_profile.get('epds_score', 10) >= 12:
            risk_factors.append('high_ppd_risk')
        if user_profile.get('support_level', 3) <= 2:
            risk_factors.append('low_support')
        if user_profile.get('sleep_hours', 5) < 4:
            risk_factors.append('severe_sleep_deprivation')
        if user_profile.get('pain_level', 3) >= 7:
            risk_factors.append('high_pain')
        
        return risk_factors
    
    def _identify_current_challenges(self, user_profile):
        """Identify current challenges for targeted support"""
        challenges = []
        
        if user_profile.get('mood_score', 5) <= 3:
            challenges.append('mood_regulation')
        if user_profile.get('energy_level', 4) <= 3:
            challenges.append('low_energy')
        if user_profile.get('pain_level', 3) >= 6:
            challenges.append('pain_management')
        
        return challenges
    
    def _generate_health_monitoring_plan(self, user_profile, cluster_id):
        """Generate comprehensive health monitoring plan"""
        monitoring_plan = {
            'daily_metrics': [
                {'metric': 'mood_score', 'scale': '1-10', 'frequency': 'daily'},
                {'metric': 'pain_level', 'scale': '1-10', 'frequency': 'daily'},
                {'metric': 'energy_level', 'scale': '1-10', 'frequency': 'daily'},
                {'metric': 'sleep_hours', 'scale': 'hours', 'frequency': 'daily'}
            ],
            'weekly_assessments': [
                {'assessment': 'epds_screening', 'frequency': 'weekly'},
                {'assessment': 'physical_recovery_check', 'frequency': 'weekly'}
            ],
            'alerts': self._generate_health_alerts(user_profile),
            'integration_ready': {
                'wearables': True,
                'symptom_tracking': True,
                'mood_tracking': True
            }
        }
        
        return monitoring_plan
    
    def _generate_health_alerts(self, user_profile):
        """Generate health monitoring alerts"""
        alerts = []
        
        if user_profile.get('epds_score', 10) >= 15:
            alerts.append({
                'type': 'high_priority',
                'condition': 'epds_score >= 15',
                'message': 'High PPD risk detected - consider immediate professional consultation'
            })
        
        if user_profile.get('pain_level', 3) >= 8:
            alerts.append({
                'type': 'medical_attention',
                'condition': 'pain_level >= 8',
                'message': 'Severe pain reported - contact healthcare provider'
            })
        # Persistent low sentiment advisory
        sctx = user_profile.get('sentiment_context', {}) or {}
        if sctx.get('sent_last7_avg') is not None and sctx.get('sent_last7_avg') <= -0.3:
            alerts.append({
                'type': 'monitoring',
                'condition': 'low average sentiment last 7 days',
                'message': 'Recent mood indicates low emotional wellbeing—increase support and consider check-in'
            })
        
        return alerts
    
    def create_personalized_plan(self, user_profile, cluster_profile, cluster_id):
        """Create personalized care plan based on cluster analysis"""
        return self.generate_care_plan_tasks(user_profile, cluster_id)
    
    def generate_fallback_plan(self, user_profile):
        """Generate comprehensive fallback care plan using ML methods"""
        # Use cluster 0 (default) and generate full plan using ML methods
        cluster_id = 0
        
        # Generate comprehensive care plan using the same ML methods
        care_plan = {
            'user_id': user_profile.get('user_id'),
            'postpartum_week': user_profile.get('postpartum_week', 4),
            'cluster_id': cluster_id,
            'cluster_info': {'name': 'General Recovery', 'description': 'Comprehensive postpartum recovery support'},
            'weekly_priorities': self._generate_ml_weekly_priorities(user_profile, cluster_id),
            'daily_tasks': self._generate_ml_daily_tasks(user_profile, cluster_id),
            'resources': self._generate_personalized_resources(user_profile, cluster_id),
            'health_monitoring': self._generate_health_monitoring_plan(user_profile, cluster_id),
            'personalization_context': self._build_personalization_context(user_profile),
            'created_at': datetime.utcnow(),
            'week_start': datetime.utcnow(),
            'completed_tasks': 0,
            'completion_percentage': 0
        }
        
        # Calculate progress tracking
        total_tasks = len(care_plan['daily_tasks'])
        care_plan['progress_tracking'] = {
            'total_tasks': total_tasks,
            'completed_tasks': 0,
            'completion_percentage': 0
        }
        
        return care_plan
    
    @staticmethod
    def get_care_plan_by_user_id(user_id):
        """Get active care plan for a user"""
        try:
            return mongo.db.care_plans.find_one({
                'user_id': ObjectId(user_id),
                'is_active': True
            })
        except Exception as e:
            print(f"Error getting care plan: {e}")
            return None
    
    @staticmethod
    def update_task_completion(care_plan_id, task_id, completed=True):
        """Update task completion status"""
        try:
            # Update the specific task
            result = mongo.db.care_plans.update_one(
                {
                    '_id': ObjectId(care_plan_id),
                    'daily_tasks.id': task_id
                },
                {
                    '$set': {
                        'daily_tasks.$.completed': completed,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Recalculate progress
                care_plan = mongo.db.care_plans.find_one({'_id': ObjectId(care_plan_id)})
                if care_plan:
                    total_tasks = len(care_plan['daily_tasks'])
                    completed_tasks = sum(1 for task in care_plan['daily_tasks'] if task.get('completed', False))
                    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                    
                    # Update progress tracking
                    mongo.db.care_plans.update_one(
                        {'_id': ObjectId(care_plan_id)},
                        {
                            '$set': {
                                'progress_tracking.completed_tasks': completed_tasks,
                                'progress_tracking.completion_percentage': completion_percentage,
                                'updated_at': datetime.utcnow()
                            }
                        }
                    )
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error updating task completion: {e}")
            return False
    
    @staticmethod
    def regenerate_weekly_plan(user_id):
        """Regenerate care plan for a new week"""
        try:
            # Get current care plan
            current_plan = CarePlan.get_care_plan_by_user_id(user_id)
            if not current_plan:
                return None
            
            # Update user profile with new week
            user_profile = current_plan['user_profile'].copy()
            user_profile['postpartum_week'] = user_profile.get('postpartum_week', 4) + 1
            
            # Deactivate current plan
            mongo.db.care_plans.update_one(
                {'_id': current_plan['_id']},
                {'$set': {'is_active': False, 'updated_at': datetime.utcnow()}}
            )
            
            # Create new plan
            new_plan_id = CarePlan.create_care_plan(user_id, user_profile)
            return new_plan_id
            
        except Exception as e:
            print(f"Error regenerating weekly plan: {e}")
            return None

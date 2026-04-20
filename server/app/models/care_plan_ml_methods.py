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
    
    # Mental health tasks (ML-driven based on EPDS score and mood)
    if epds_score >= 12 or mood_score <= 4:
        if epds_score >= 15:  # High risk
            tasks.extend([
                {
                    'title': 'Complete mood check-in questionnaire',
                    'description': 'Track your emotional state to identify patterns',
                    'category': 'mental_health',
                    'priority': 'high',
                    'duration_minutes': 5,
                    'optimal_time': 'morning'
                },
                {
                    'title': 'Practice guided breathing exercise',
                    'description': 'Use deep breathing to manage anxiety and stress',
                    'category': 'mental_health',
                    'priority': 'high',
                    'duration_minutes': 10,
                    'optimal_time': 'evening'
                }
            ])
        else:
            tasks.append({
                'title': 'Journal three positive moments from today',
                'description': 'Focus on gratitude and positive experiences',
                'category': 'mental_health',
                'priority': 'medium',
                'duration_minutes': 10,
                'optimal_time': 'evening'
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
                    'duration_minutes': 5,
                    'optimal_time': 'morning'
                },
                {
                    'title': 'Practice gentle abdominal breathing',
                    'description': 'Support core recovery with breathing exercises',
                    'category': 'physical_recovery',
                    'priority': 'medium',
                    'duration_minutes': 10,
                    'optimal_time': 'afternoon'
                }
            ])
        elif postpartum_week > 2:
            tasks.append({
                'title': 'Take a 10-15 minute gentle walk',
                'description': 'Gradually increase activity as cleared by doctor',
                'category': 'physical_recovery',
                'priority': 'medium',
                'duration_minutes': 15,
                'optimal_time': 'morning'
            })
    
    # Feeding support tasks (ML-driven based on feeding type)
    if feeding in ['breastfeeding', 'mixed']:
        tasks.extend([
            {
                'title': 'Log feeding session details',
                'description': 'Track duration, frequency, and baby satisfaction',
                'category': 'feeding',
                'priority': 'high',
                'duration_minutes': 3,
                'optimal_time': 'flexible'
            },
            {
                'title': 'Perform breast care routine',
                'description': 'Apply nipple cream and check for issues',
                'category': 'feeding',
                'priority': 'medium',
                'duration_minutes': 5,
                'optimal_time': 'flexible'
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
                'duration_minutes': 30,
                'optimal_time': 'afternoon'
            })
        
        if energy_level <= 3:
            tasks.append({
                'title': 'Practice energy-boosting stretches',
                'description': 'Gentle movements to improve circulation and energy',
                'category': 'wellness',
                'priority': 'medium',
                'duration_minutes': 10,
                'optimal_time': 'morning'
            })
    
    # Essential wellness tasks (always included but personalized)
    tasks.extend([
        {
            'title': 'Hydration check and water intake',
            'description': 'Aim for 8-10 glasses, more if breastfeeding',
            'category': 'wellness',
            'priority': 'high',
            'duration_minutes': 2,
            'optimal_time': 'flexible'
        },
        {
            'title': 'Take prescribed vitamins/supplements',
            'description': 'Continue prenatal vitamins as recommended',
            'category': 'wellness',
            'priority': 'high',
            'duration_minutes': 1,
            'optimal_time': 'morning'
        }
    ])
    
    # Add unique IDs and mark as incomplete
    for i, task in enumerate(tasks):
        task['id'] = f'{task["category"]}_{i+1}'
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
    
    # Base resources
    resources.extend([
        'Emergency: When to Call Your Doctor - Personalized Warning Signs',
        'Guide: Week-by-Week Recovery Expectations'
    ])
    
    # Condition-specific resources
    epds_score = user_profile.get('epds_score', 10)
    if epds_score >= 12:
        resources.extend([
            'App: Mood tracking and mental health support',
            'Hotline: 24/7 Postpartum Support International',
            'Article: Understanding Your PPD Risk Factors'
        ])
    
    delivery_type = user_profile.get('delivery_type', 'vaginal')
    if delivery_type == 'c_section':
        resources.extend([
            'Video: C-Section Recovery Exercise Progression',
            'Guide: Scar Care and Healing Timeline'
        ])
    
    feeding = user_profile.get('feeding', 'breastfeeding')
    if feeding == 'breastfeeding':
        resources.extend([
            'Contact: Local Lactation Consultant Directory',
            'App: Breastfeeding tracker with AI insights'
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
    
    return alerts

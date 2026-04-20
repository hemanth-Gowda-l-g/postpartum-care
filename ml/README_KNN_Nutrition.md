# K-NN Based Nutrition Recommendation System for Postpartum Mothers

## Overview

This system implements a personalized meal plan recommender using k-Nearest Neighbors (k-NN) algorithm, specifically designed for postpartum mothers. The system matches users with similar nutritional needs and dietary preferences to provide tailored food recommendations.

## Features

### Core Functionality
- **Health Metrics Integration**: Iron levels, Vitamin D, BMI, lactation status
- **Dietary Preferences**: Vegan, vegetarian, gluten-free, allergies support
- **Recovery Stage Awareness**: Weeks postpartum, C-section vs. vaginal birth
- **Personalized Scoring**: AI-powered food recommendations based on user similarity

### Technical Implementation
- **K-NN Algorithm**: Uses cosine similarity for sparse data
- **Feature Engineering**: Health metrics, dietary restrictions, recovery factors
- **Dimensionality Reduction**: PCA for high-dimensional feature spaces
- **Model Persistence**: Save/load trained models for production use

## Architecture

### Data Flow
1. **User Input** → Health metrics, dietary preferences, recovery stage
2. **Feature Processing** → Normalization, encoding, PCA transformation
3. **K-NN Search** → Find similar users in feature space
4. **Recommendation Generation** → Score foods based on similarity and nutritional needs
5. **Meal Planning** → Generate daily meal plans with personalized insights

### Key Components

#### 1. PostpartumKNNNutritionRecommender (Training Script)
- **Location**: `ml/training_scripts/knn_nutrition_recommender.py`
- **Purpose**: Full-featured training and recommendation system
- **Features**: Complete food database integration, meal planning, model training

#### 2. KNNNutritionService (Server Integration)
- **Location**: `server/app/ml_services/knn_nutrition_service.py`
- **Purpose**: Lightweight service for server integration
- **Features**: Synthetic profile generation, K-NN insights, recommendation enhancement

#### 3. Enhanced Nutrition Routes
- **Location**: `server/app/routes/nutrition.py`
- **New Endpoints**:
  - `POST /nutrition/knn-recommendations` - K-NN enhanced recommendations
  - `POST /nutrition/personalized-insights` - AI-powered insights

## Data Requirements

### User Profile Features
```python
user_profile = {
    'iron_level': 0.3,        # Normalized 0-1 (0.3 = low iron)
    'vitamin_d': 0.4,         # Normalized 0-1 (0.4 = moderate)
    'calcium': 0.6,           # Normalized 0-1 (0.6 = moderate)
    'is_vegetarian': 1,       # Binary (1 = yes, 0 = no)
    'is_vegan': 0,            # Binary
    'is_gluten_free': 0,      # Binary
    'breastfeeding': 1,       # Binary
    'weeks_postpartum': 0.2,  # Normalized (0.2 = 1-2 weeks)
    'birth_type': 0,          # Binary (0 = vaginal, 1 = C-section)
    'bmi': 0.5                # Normalized (0.5 = normal BMI)
}
```

### Nutrition Datasets
- **food.csv**: 7,795 food items with descriptions
- **nutrient.csv**: 476 nutrients with units
- **food_nutrient.csv**: Food-nutrient relationships
- **food_category.csv**: 28 food categories

## Installation & Setup

### 1. Install Dependencies
```bash
cd ml/
pip install -r requirements_knn.txt
```

### 2. Train the Model
```bash
cd ml/training_scripts/
python knn_nutrition_recommender.py
```

### 3. Test the Service
```bash
cd server/app/ml_services/
python knn_nutrition_service.py
```

## Usage Examples

### Basic K-NN Recommendations
```python
from app.ml_services.knn_nutrition_service import KNNNutritionService

# Initialize service
knn_service = KNNNutritionService()

# User profile
user_profile = {
    'iron_level': 0.2,      # Low iron
    'vitamin_d': 0.4,       # Moderate vitamin D
    'calcium': 0.6,         # Moderate calcium
    'is_vegetarian': 1,     # Vegetarian
    'breastfeeding': 1,     # Breastfeeding
    # ... other features
}

# Get personalized insights
insights = knn_service.get_personalized_insights(user_profile)
print(f"Found {insights['similar_users_found']} similar users")
```

### API Integration
```bash
# Get K-NN enhanced recommendations
curl -X POST http://localhost:5000/nutrition/knn-recommendations \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "breastfeeding": "yes",
    "dietType": "vegetarian",
    "allergies": "none",
    "deficiency": "iron",
    "preferredCuisine": "indian"
  }'
```

## Algorithm Details

### K-NN Implementation
1. **Feature Normalization**: Min-Max scaling for numerical features
2. **Dimensionality Reduction**: PCA to 5 components for efficiency
3. **Similarity Metric**: Cosine similarity for sparse, high-dimensional data
4. **Neighbor Selection**: k=3 nearest neighbors (configurable)

### Recommendation Scoring
```python
final_score = 0.7 * nutrition_score + 0.3 * similarity_score

# Where:
# nutrition_score = nutrient deficiency matching + dietary compliance
# similarity_score = average similarity to k nearest neighbors
```

### Safety Features
- **Deficiency Detection**: Identifies low iron, vitamin D, calcium levels
- **Dietary Filtering**: Respects vegetarian, vegan, gluten-free preferences
- **Allergy Avoidance**: Filters out foods containing allergens
- **Nutritional Thresholds**: Ensures minimum nutrient requirements

## Performance & Scalability

### Current Performance
- **Training Time**: ~2-3 seconds for 4 synthetic profiles
- **Inference Time**: ~50-100ms per recommendation request
- **Memory Usage**: ~50-100MB for model + data

### Scalability Considerations
- **User Profiles**: Currently 4 synthetic profiles, can scale to thousands
- **Food Database**: 7,795 foods, can handle larger databases
- **Real-time Updates**: Model can be retrained with new user data

## Integration Points

### Existing System
- **Nutrition Routes**: Enhanced with K-NN endpoints
- **User Profiles**: Integrated with existing nutrition profiles
- **Authentication**: JWT-based user identification
- **Database**: Uses existing nutrition profile models

### Future Enhancements
- **Real User Data**: Replace synthetic profiles with actual user data
- **Feedback Loop**: Incorporate user ratings and preferences
- **A/B Testing**: Compare K-NN vs. rule-based recommendations
- **Mobile App**: Frontend integration for real-time recommendations

## Testing & Validation

### Test Scenarios
1. **Iron Deficiency**: Low iron users get iron-rich food recommendations
2. **Vegetarian Diet**: Respects dietary restrictions
3. **Breastfeeding**: Provides lactation-supportive nutrition advice
4. **Allergy Safety**: Filters out allergenic foods

### Validation Metrics
- **Similarity Accuracy**: K-NN finds truly similar users
- **Recommendation Relevance**: Foods match user needs
- **Dietary Compliance**: Recommendations respect restrictions
- **Performance**: Response time under 100ms

## Troubleshooting

### Common Issues
1. **Model Not Loading**: Check file paths and dependencies
2. **No Similar Users**: Verify user profile format and feature values
3. **Slow Performance**: Consider reducing PCA components or food database size
4. **Memory Errors**: Reduce batch size or use data streaming

### Debug Mode
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual components
knn_service = KNNNutritionService()
similar_users = knn_service.find_similar_users(test_profile)
print(f"Similar users: {similar_users}")
```

## Contributing

### Development Workflow
1. **Feature Branch**: Create branch for new features
2. **Testing**: Run tests with sample data
3. **Documentation**: Update README and code comments
4. **Integration**: Test with existing nutrition system
5. **Review**: Submit pull request for review

### Code Standards
- **Python**: PEP 8 compliance
- **Documentation**: Docstrings for all methods
- **Error Handling**: Comprehensive exception handling
- **Logging**: Structured logging for debugging

## License & Acknowledgments

This system is part of the Postpartum Care Platform and follows the same licensing terms.

**Key Technologies**:
- scikit-learn: K-NN implementation
- pandas: Data manipulation
- numpy: Numerical computations
- Flask: Web framework integration

**Research Basis**:
- Postpartum nutrition requirements (WHO guidelines)
- K-NN recommendation systems research
- Maternal health data analysis

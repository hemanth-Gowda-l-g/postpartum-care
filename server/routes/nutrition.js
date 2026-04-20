const express = require('express');
const router = express.Router();

// Nutrition prediction endpoint
router.post('/predict', async (req, res) => {
  try {
    const {
      breastfeeding,
      dietType,
      allergies,
      deficiency,
      preferredCuisine
    } = req.body;

    // TODO: Integrate with your nutrition prediction model here
    // For now, returning mock recommendations based on input
    const recommendations = generateMockRecommendations({
      breastfeeding,
      dietType,
      allergies,
      deficiency,
      preferredCuisine
    });

    res.json({ recommendations });
  } catch (error) {
    console.error('Nutrition prediction error:', error);
    res.status(500).json({ error: 'Failed to generate nutrition recommendations' });
  }
});

// Helper function to generate mock recommendations
function generateMockRecommendations(userData) {
  const recommendations = [];

  // Breastfeeding recommendations
  if (userData.breastfeeding === 'yes') {
    recommendations.push({
      title: 'Breastfeeding Nutrition',
      description: 'Increase your daily caloric intake by 500 calories and ensure adequate hydration. Include foods rich in omega-3 fatty acids and calcium.'
    });
  }

  // Diet type specific recommendations
  if (userData.dietType === 'vegan') {
    recommendations.push({
      title: 'Vegan Diet Support',
      description: 'Focus on plant-based protein sources like legumes, tofu, and quinoa. Consider supplementing with B12 and iron if needed.'
    });
  }

  // Deficiency specific recommendations
  if (userData.deficiency === 'iron') {
    recommendations.push({
      title: 'Iron-Rich Foods',
      description: 'Include iron-rich foods like spinach, lentils, and fortified cereals. Pair with vitamin C-rich foods to enhance absorption.'
    });
  }

  // Cuisine specific recommendations
  if (userData.preferredCuisine.toLowerCase() === 'indian') {
    recommendations.push({
      title: 'Indian Cuisine Recommendations',
      description: 'Include traditional postpartum foods like ghee, moong dal, and methi. Opt for whole grain rotis and include plenty of vegetables.'
    });
  }

  // General postpartum recommendations
  recommendations.push({
    title: 'General Postpartum Nutrition',
    description: 'Focus on whole foods, stay hydrated, and eat regular meals. Include a variety of fruits, vegetables, and protein sources.'
  });

  return recommendations;
}

module.exports = router; 
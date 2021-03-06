const models = require('../../models');
const Recipe = models.mongo.Recipe;
// const User = models.sql.User;
const router = require('express').Router();
const key = 'recipe';

// GET /recipe
router.get('/:uuid', (req, res) => {
    const query = Recipe.findOne({uuid: req.params.uuid}).populate('ingredients tags');

    // TODO: cross-reference user key in recipe.author with User entity

    query.exec((err, recipe) => {
        if (err || !recipe) {
            console.error(err);
            require('../middleware').catch404(req, res);
        } else res.render(key, {
            title: key.charAt(0).toUpperCase() + key.slice(1),
            section: key,
            recipe: recipe
        });
    });
});

exports = module.exports = router;

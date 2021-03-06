const crypto = require('crypto');
const mongoose = require('mongoose');
const mongooseAlgolia = require('mongoose-algolia');
const findOrCreate = require('mongoose-find-or-create');
const Schema = mongoose.Schema;
const isTest = process.env.NODE_ENV === 'test';

let schema = new Schema({
    uuid: String,
    name: String,
    type: String,
    origURL: String,
    steps: [String],
    time: Number, //in minutes
    servings: String, //in servings
    author: String, // Sequelize user primary key
    likes: Number,
    photoURL: String,
    created: Date,
    ingredients: [{
        type: Schema.ObjectId,
        ref: 'Ingredient'
    }],
    tags: [{
        type: Schema.ObjectId,
        ref: 'Tag'
    }],
    nutrition: {
        calTotal: Number,
        calFromFat: Number,
        totalFat: Number, //in grams
        saturatedFat: Number, //in grams
        cholesterol: Number, // in mg
        sodium: Number, // in mg
        carbs: Number, // in grams
        fiber: Number, // in grams
        sugars: Number, // in grams
        protein: Number, // in grams
        calcium: Number // in mg
    }
});

schema.pre('validate', function(next) {
    this.uuid = crypto.createHash('md5').update(this.name).digest('hex').toString().slice(8);
    next();
});

schema.plugin(findOrCreate);

if (!isTest) schema.plugin(mongooseAlgolia, {
	appId: process.env.ALGOLIA_APP_ID,
	apiKey: process.env.ALGOLIA_ADMIN_API_KEY,
	indexName: 'Recipes',
	populate: {
		path: 'ingredients tags',
		select: 'name'
	},
	debug: process.env.NODE_ENV === 'development' || process.env.NODE_ENV === 'test' ? true : false
});

const model = mongoose.model('Recipe', schema);

if (!isTest) model.SyncToAlgolia();

module.exports = model;

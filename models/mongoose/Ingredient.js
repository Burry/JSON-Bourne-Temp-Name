const mongoose = require('mongoose');
const mongooseAlgolia = require('mongoose-algolia');
const findOrCreate = require('mongoose-find-or-create');
const Schema = mongoose.Schema;
const isTest = process.env.NODE_ENV === 'test';

let schema = new Schema({
    _id: String,
    name: String,
    type: String,
    avgPrice: Number, // price in USD
    tags: [{
        type : Schema.ObjectId,
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

schema.plugin(findOrCreate);

if (!isTest) schema.plugin(mongooseAlgolia, {
	appId: process.env.ALGOLIA_APP_ID,
	apiKey: process.env.ALGOLIA_ADMIN_API_KEY,
	indexName: 'Ingredients',
	populate: {
		path: 'tags',
		select: 'name'
	},
	debug: process.env.NODE_ENV === 'development' || process.env.NODE_ENV === 'test' ? true : false
});

const model = mongoose.model('Ingredient', schema);

if (!isTest) model.SyncToAlgolia();

module.exports = model;

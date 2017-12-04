const _ = require('lodash')
const async = require('async')
const keystone = require('keystone')
const passport = require('passport')
const passportFacebookStrategy = require('passport-facebook').Strategy
const User = keystone.list('User')

let credentials = {
	clientID: process.env.FACEBOOK_CLIENT_ID,
	clientSecret: process.env.FACEBOOK_CLIENT_SECRET,
	callbackURL: process.env.FACEBOOK_CALLBACK_URL,
	profileFields: ['id', 'email', 'displayName']
}

exports.authenticateUser = function(req, res, next) {
	console.log('[services.facebook] - Triggered authentication process...')

	// Initalise Facebook credentials
	var facebookStrategy = new passportFacebookStrategy(credentials, (accessToken, refreshToken, profile, done) => {
		done(null, {
			accessToken: accessToken,
			refreshToken: refreshToken,
			profile: profile
		})
	})

	// Pass through authentication to passport
	passport.use(facebookStrategy)

	// Save user data once returning from Facebook
	if (_.has(req.query, 'cb')) {
		console.log('[services.facebook] - Callback workflow detected, attempting to process data...')

		passport.authenticate('facebook', {session: false}, (err, data, info) => {
			if (err || !data) {
				console.log("[services.facebook] - Error retrieving Facebook account data - " + JSON.stringify(err))
				return res.redirect('/sign-in')
			}

			console.log('[services.facebook] - Successfully retrieved Facebook account data, processing...')

			var name = data.profile && data.profile.displayName ? data.profile.displayName.split(' ') : []

			var auth = {
				type: 'facebook',
				name: {
					first: name.length ? name[0] : '',
					last: name.length > 1 ? name[1] : ''
				},
				email: data.profile.emails.length ? _.first(data.profile.emails).value : null,
				profileId: data.profile.id,
				username: data.profile.username,
				avatar: 'https://graph.facebook.com/' + data.profile.id + '/picture?width=600&height=600',
				accessToken: data.accessToken,
				refreshToken: data.refreshToken
			}
			req.session.auth = auth
			return res.redirect('/auth/confirm')
		})(req, res, next)

	// Perform inital authentication request to Facebook
	} else {
		console.log('[services.facebook] - Authentication workflow detected, attempting to request access...')

		passport.authenticate('facebook', {scope: ['email']})(req, res, next)
	}
}
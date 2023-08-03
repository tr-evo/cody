import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

//authentification
import { isValidJwt, EventBus } from '../util'

Vue.use(Vuex)

export default new Vuex.Store({
	state: {
		codes: [
			{
				text: 'No document selected',
				color: '#FFAB91',
			},
			{
				text: 'Please select or upload a document',
				color: '#80CBC4',
			},
		],

		annotations: [],

		newAnnotationsLastUpdate: null,

		inputDocument: null,

		serverDocuments: [],

		currentDocument: null,

		saveSuccess: null,

		isLoading: false,

		CRloading: false,
		MLloading: false,

		changeCounter: 0,

		//adjust for prod and dev environment | prod: http://217.160.57.62 // dev: http://localhost:5000
		serverAdress: process.env.VUE_APP_API_URL,
		serverStatus: 1,

		//last requested code rule
		codeRule: null,

		userData: {},
		jwt: '',

		documentScroll: {},
	},

	getters: {
		//reusable data accessor
		isAuthenticated(state) {
			return isValidJwt(state.jwt.token)
		},

		numberCRsug(state) {
			return (state.annotations.filter(an => an.confidence == 1)).length
		},

		numberMLsug(state) {
			return (state.annotations.filter(an => an.confidence < 1 && an.confidence != null)).length
		}
	},

	mutations: {
		updateCodes (state, v) {
			//Labels from server come as array of arrays, push to labels object
			//empty labels array first
			state.codes = []
			let laObj = {} //temp object for push
			for(let labels of v) {
				laObj = {
					text: labels[0],
					color: labels[1],
				}
				state.codes.push(laObj)
			}
		},

		updateOrder(state, v) {
			state.codes = v.slice(0)
		},

		updateDocument(state, v) {
			state.inputDocument = v
		},

		updateAnnotations(state, v) {
			//annotations from server come as array of arrays, push to annotations object
			//empty annotations array first
			const numberOldAnnotations = state.annotations.filter(an => an.isRecommendation == 1).length
			state.annotations = []
			let anObj = {} //temp object for push
			for(let annotation of v) {
				anObj = {
					conversation: annotation[0],
					attribute: annotation[1],
					annotationID: annotation[2],
					id: annotation[3],
					start: annotation[4],
					length: annotation[5],
					label: annotation[6],
					isRecommendation: annotation[7], 
					matchHighlight: annotation[8],
					confidence: annotation[9],
				}
				state.annotations.push(anObj)
			}
			//update info message for users
			const numberSuggestions = state.annotations.filter(an => an.isRecommendation == 1).length - numberOldAnnotations
			state.newAnnotationsLastUpdate = null
			if(numberOldAnnotations == 0) {
				state.newAnnotationsLastUpdate = "Welcome back! [" + numberSuggestions + "] automated suggestion(s) so far!"
			}
			else if (numberSuggestions == 0) {
				state.newAnnotationsLastUpdate = null
			}
			else if (numberSuggestions < 0) {
				state.newAnnotationsLastUpdate = "Removed [" + Math.abs(numberSuggestions) + "] old suggestion(s)" 
			}
			else {
				state.newAnnotationsLastUpdate = "Created [" + numberSuggestions + "] new suggestion(s)" 
			}
		},

		writingSuccessful(state) {
			state.saveSuccess = true
		},

		writingFailure(state) {
			state.saveSuccess = false
		},

		changeLoadingStatus(state) {
			state.isLoading = !state.isLoading
		},

		//set current document
		setCurrentDocument(state, id) {
			//set object document
			state.currentDocument = state.serverDocuments.find( doc => doc.id == id)
		},

		//update state with server get
		addServerDocument(state, doc) {
			state.serverDocuments.push(doc)
		},

		//clean serverDocument state array
		cleanServerDocument(state) {
			state.serverDocuments = []
		},

		//push, update, delete mutations for state
		deleteAnnotation(state, id) {
			//identify index
			let index = state.annotations.findIndex( an => an.annotationID == id)
			//remove from array
			state.annotations.splice(index, 1)
		},

		addAnnotation(state, payload) {
			let newAnnotation = payload
			//find information of new annotation in return
			let an = {
				conversation: newAnnotation.conversation,
				attribute: newAnnotation.attribute,
				annotationID: newAnnotation.annotationID,
				id: newAnnotation.id,
				start: newAnnotation.start,
				length: newAnnotation.length,
				label: newAnnotation.label,
				isRecommendation: 0, 
				matchHighlight: null,
				confidence: null,
			}
			//push to local annotations
			state.annotations.push(an)
		},

		updateAnnotationLabel(state, payload) {
			//input array: [annotationsID, newLabel]
			const index = state.annotations.findIndex( an => an.annotationID == payload[0] )
			state.annotations[index].label = payload[1]
			state.annotations[index].isRecommendation = 0
			state.annotations[index].confidence = null
			state.annotations[index].matchHighlight = null
		},

		updateSuggestions(state, payload) {
			//payload : [binary: CR (0) or ML(1), annotations on server]
			let only_suggestions = null
			let client_before_push = null
			//distinguish case CR and case ML
			/// case CR
			if(payload[0] == 0) {
				//get all CR annotations from server
				only_suggestions = payload[1].filter( an => an[7] == 1 && an[9] == 1 )
				//remove old CR annotations from client > get all annotations with confidence != 1
				client_before_push = state.annotations.filter( an => an.confidence != 1 )
			}
			/// case ML
			else {
				//get all ML annotations from server
				only_suggestions = payload[1].filter( an => an[7] == 1 && an[9] < 1 )
				//remove old CR annotations from client > get all annotations with confidence = 1 & annotations with confidence = null (manual)
				client_before_push = state.annotations.filter( an => an.confidence == null || an.confidence == 1 )
			}
			//update annotations in state
			//set to state without suggestions of either CR or ML 
			state.annotations = client_before_push
			//add these back in
			let anObj = {} //temp object for push
			for(let annotation of only_suggestions) {
				anObj = {
					conversation: annotation[0],
					attribute: annotation[1],
					annotationID: annotation[2],
					id: annotation[3],
					start: annotation[4],
					length: annotation[5],
					label: annotation[6],
					isRecommendation: annotation[7], 
					matchHighlight: annotation[8],
					confidence: annotation[9],
				}
				state.annotations.push(anObj)
			}
		},

		removeMLsuggestions(state) {
			//remove all ML annotations from state
			state.annotations = state.annotations.filter(an => an.confidence == null || an.confidence == 1 )
		},

		changeToManual(state, annotationID) {
			let index = state.annotations.findIndex(an => an.annotationID == annotationID)
			state.annotations[index].isRecommendation = 0
			state.annotations[index].confidence = null
			state.annotations[index].matchHighlight = null
		},

		updateCodeRule(state, v) {
			state.codeRule = v
		},

		changeCRloadingStatus(state) {
			state.CRloading = !state.CRloading
		},

		changeMLloadingStatus(state) {
			state.MLloading = !state.MLloading
		},

		changeServerStatus(state) {
			state.serverStatus = !state.serverStatus
		},

		increaseChangeCounter(state) {
			state.changeCounter = state.changeCounter + 1
		},

		resetChangeCounter(state) {
			state.changeCounter = 0
		},

		//Authentification
		setUserData(state, payload) {
			state.userData = payload.userData
		},

		setJwtToken(state, payload) {
			localStorage.token = payload.jwt.token
			state.jwt = payload.jwt
		},

		setDocumentScroll(state, position) {
			state.documentScroll = position
		},

	},

	actions: {
		documentScrollPosition(context, position) {
			context.commit('setDocumentScroll', position)
		},

		addCode(context, labels) {
			let path = context.state.serverAdress + '/api/labels/' + context.state.currentDocument.id
			axios.post(path, labels, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
			.then(() => {
				//success route
				//get current labels from server and replace labels on FE to prevent building two lists
				axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
					.then((res) => {
						context.commit('updateCodes', res.data)
					})
				context.commit('writingSuccessful')
			}, () => {
				//fail route
				context.commit('changeServerStatus')
				context.commit('writingFailure')
			})
		},

		updateList(context, v) {
			//first local update to wait for server to be ready and update display ahead of time
			//context.commit('updateCodes', v)
			let path = context.state.serverAdress + '/api/labels/all/' + context.state.currentDocument.id
			axios.post(path, v, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
			.then(() => {
				//success route
				//get current labels from server and replace labels on FE to prevent building two lists
				path = context.state.serverAdress + '/api/labels/' + context.state.currentDocument.id
				axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
					.then((res) => {
						context.commit('updateCodes', res.data)
					})
				context.commit('writingSuccessful')
			}, () => {
				//fail route
				context.commit('changeServerStatus')
				context.commit('writingFailure')
			})
		},

		updateDocument(context, v) {
			context.commit('updateDocument', v)
		},

		//upload new document to server
		newDocument(context, v) {
			let path = context.state.serverAdress + '/api/documents'
			axios.post(path, v, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
				.then(() => {
					context.commit('writingSuccessful')
					//retrieve list of documents from server and update vuex state serverDocuments
					context.dispatch('getDocuments')
				}, () => {
					//fail route
					context.commit('changeServerStatus')
					context.commit('writingFailure')
				})
		},

		getDocuments(context) {
			let path = context.state.serverAdress + '/api/documents'
			let request = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
				.then((res) => {
					//success
					context.commit('cleanServerDocument')
					for (var doc of res.data) {
						let temp = {
							id: doc[0],
							name: doc[1],
							owner: doc[2],
							lastChange: doc[3],
							inputType: doc[4],
							uoa: doc[5],
						}
						context.commit('addServerDocument', temp)
					}
					return 1
				}, () => {
					//fail
					context.commit('changeServerStatus')
					return 0
				})
			return request
		},

		//change current document (if necessary)
		changeToDocument(context, id) {

			let continueMethod = function() {
				context.commit('changeLoadingStatus')
				//set document in state
				context.dispatch('getDocuments').then(() => {
					context.commit('setCurrentDocument', id)
				})

				//get input document
				let path = context.state.serverAdress + '/api/sections/' + id
				var p2 = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
					.then((res) => {
						context.commit('updateDocument', res.data)
					})
				//get annotations
				path = context.state.serverAdress + '/api/annotations/' + id
				var p3 = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
					.then((res) => {
						context.commit('updateAnnotations', res.data)
					})
				//get codes
				path = context.state.serverAdress + '/api/labels/' + id
				var p4 = axios.get(path,{ headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
					.then((res) => {
						context.commit('updateCodes', res.data)
					})
				Promise.all([p2, p3, p4]).then(() => {
					//set ready
					context.commit('changeLoadingStatus')
				}, () => {
					//fail route
					context.commit('changeServerStatus')
				})
			}
			
			//change only if currentDocument != selected document
			let currentDocumentExists = context.state.currentDocument == null ? false : true

			if(currentDocumentExists) {
				if(context.state.currentDocument.id != id) {
					continueMethod()
				}
			}

			else {
				continueMethod()
			}
		},

		//push on annotation to internal state, push on server
		//update on annotation in internal state, update on server
		//delete one annotation in internal state, delete on server
		deleteAnnotation(context, annotationID) {
			//input array: [annotationsID, labelPointer]
			let path = context.state.serverAdress + '/api/annotations/' + context.state.currentDocument.id + '/' + annotationID
			axios.delete(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
			.then(() => {
				//success route -> try to mutate only local state to increase speed, but only when post was successful
				context.commit('deleteAnnotation', annotationID)
				context.commit('writingSuccessful')
			}, () => {
				//fail route
				context.commit('changeServerStatus')
				context.commit('writingFailure')
			})
		},

		addAnnotation(context, an) {
			let path = context.state.serverAdress + '/api/annotations/' + context.state.currentDocument.id + '/' + an.annotationID
			axios.post(path, an, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
			.then(() => {
				//success route -> mutate local state based on returned 'new' annotation from server
				//add to state.annotations
					context.commit('addAnnotation', an)
					context.commit('writingSuccessful')
			}, () => {
				//fail route
				context.commit('changeServerStatus')
				context.commit('writingFailure')
			})

			return an.annotationID
		},

		updateAnnotationLabel(context, array) {
			//input array: [annotationsID, newLabel]
			let path = context.state.serverAdress + '/api/annotations/' + context.state.currentDocument.id + '/' + array[0]
			let labelAsJson = { label: array[1] }
			axios.put(path, labelAsJson, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
			.then(() => {
				//success route
				//update elements on client based on input array
				context.commit('updateAnnotationLabel', array)
				context.commit('writingSuccessful')
			}, () => {
				//fail route
				context.commit('changeServerStatus')
				context.commit('writingFailure')
			})
				//dispatch action to call server for update of ML model
				.then(() => {
					if(context.state.changeCounter == 10) {
						context.commit('resetChangeCounter')
						context.dispatch('updateMLAnnotations', array[1])
					}
					else {
						context.commit('increaseChangeCounter')
					}
				})
		},

		//action to get code rule from the server
		getCodeRule(context, label) {
			let path = context.state.serverAdress + '/api/labels/' + context.state.currentDocument.id + '/' + encodeURIComponent(label)
			let request = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
				.then((res) => {
					//promise fulfilled
					if(res.data != null) {
						context.commit('updateCodeRule', res.data[0][0])
						if(res.data[1] == 1) {
							//if new coderule has been created automatically (data[1] = 1), trigger update of CR annotations
							context.dispatch('updateCRAnnotations', label)
						}
					}
				}, 
				//promise failed
				(res) => {
					context.commit('changeServerStatus')
					window.console.log("getCode rule failed with reason: " + res)
				}); 
			return request
		},

		//action to change a code rule
		updateCodeRule(context, array) {
			//input array: [label text, new code rule]
			let path = context.state.serverAdress + '/api/labels/' + context.state.currentDocument.id + '/' + encodeURIComponent(array[0])
			let ruleToJson = { rule: array[1] }
			let request = axios.put(path, ruleToJson, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
				.then(() => {
					context.dispatch('getCodeRule', array[0])
				}, () => {
					//fail route
					context.commit('changeServerStatus')
				})
					//trigger call to server to update CR annotations and retrieve new annotations as part of it
					.then(() => {
						context.dispatch('updateCRAnnotations', array[0])
					})

			return request
		},

		getAnnotations(context) {
			//get annotations
			let path = context.state.serverAdress + '/api/annotations/' + context.state.currentDocument.id
			let request = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
				.then((res) => {
					context.commit('updateAnnotations', res.data)
				}, () => {
					//fail route
					context.commit('changeServerStatus')
				})
			return request
		},

		deleteDocument(context, id) {
			//delete document and everything related on server
			let path = context.state.serverAdress + '/api/documents/' + id
			let request = axios.delete(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
				.then(() => {
					context.dispatch('getDocuments')
					window.console.log("Document [" + id + "] successfully deleted")
				}, //fail route
				() => {
					context.commit('changeServerStatus')
					window.console.log("Deletion of document [" + id + "] failed")
				})
			return request
		}, 

		//action to update a label in a document
		updateLabelandRefresh(context, array) {
			//input array: [label to be updated, new label]
			//set loading
			context.commit('changeLoadingStatus')

			let path = context.state.serverAdress + '/api/labels/single/' + context.state.currentDocument.id + '/' + encodeURIComponent(array[0])
			let ruleToJson = { newLabel: array[1] }
			let request = axios.put(path, ruleToJson, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
			.then(() => {
				//success route
				//get annotations
				path = context.state.serverAdress + '/api/annotations/' + context.state.currentDocument.id
				var p1 = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
					.then((res) => {
						context.commit('updateAnnotations', res.data)
					})
				//get codes
				path = context.state.serverAdress + '/api/labels/' + context.state.currentDocument.id
				var p2 = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
					.then((res) => {
						context.commit('updateCodes', res.data)
					})
				Promise.all([p1, p2]).then(() => {
					//set ready
					context.commit('changeLoadingStatus')
				})
			}, () => {
				//fail route
				context.commit('changeServerStatus')
				context.commit('writingFailure')
			})
			return request
		},

		//action to delete a label in a document
		deleteLabelandRefresh(context, array) {
			//input array: [label to be updated, new label]
			//set loading
			context.commit('changeLoadingStatus')

			let path = context.state.serverAdress + '/api/labels/single/' + context.state.currentDocument.id + '/' + encodeURIComponent(array[0])
			let request = axios.delete(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
			.then(() => {
				//success route
				//get annotations
				path = context.state.serverAdress + '/api/annotations/' + context.state.currentDocument.id
				var p1 = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
					.then((res) => {
						context.commit('updateAnnotations', res.data)
					})
				//get codes
				path = context.state.serverAdress + '/api/labels/' + context.state.currentDocument.id
				var p2 = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
					.then((res) => {
						context.commit('updateCodes', res.data)
					})
				Promise.all([p1, p2]).then(() => {
					//set ready
					context.commit('changeLoadingStatus')
				})
			}, () => {
				//fail route
				context.commit('changeServerStatus')
				context.commit('writingFailure')
			})
			return request
		},

		// AUTHENTIFICATION OF USERS
		login(context, userData) {
			context.commit('setUserData', { userData })
			let path = context.state.serverAdress + '/api/login/'
			return axios.post(path, userData)
				.then(response => context.commit('setJwtToken', { jwt: response.data }))
				.catch(error => {
					window.console.log('Error Authenticating: ', error)
					let msg = ''
					if(error.message == "Network Error") {
						msg = 'We are having problems reaching our server right now. Please try again later. Sorry!'
					}
					else {
						msg = 'Your email or you password seem to be wrong. Please try again.'
					}
					EventBus.$emit('failedAuthentication', msg)
				})
		},

		register(context, userData) {
			context.commit('setUserData', { userData })
			let path = context.state.serverAdress + '/api/register/'
			return axios.post(path, userData)
				.then(() => {
					context.dispatch('login', userData)
				})
				.catch(error => {
					window.console.dir('Error Registering: ', error)
					EventBus.$emit('failedRegistering: ', 'Something appears to have gone wrong while creating your account, or an account with your email has already been created.')
				})
		},

		updateMLAnnotations(context, label) {
			let request = "No update required"
			context.commit('changeMLloadingStatus')
			if(label != 'default') {
				let path = context.state.serverAdress + '/api/recs/ML/' + context.state.currentDocument.id
				request = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
					.then((res) => {
						context.commit('updateSuggestions', [1, res.data])
						context.commit('changeMLloadingStatus')
					}, () => {
						//fail route
						context.commit('changeServerStatus')
					})
			}
			return request
		},

		updateCRAnnotations(context, label) {
			//input array: [label text, new code rule]
			context.commit('changeCRloadingStatus')

			let path = context.state.serverAdress + '/api/recs/CR/' + context.state.currentDocument.id + '/' + encodeURIComponent(label)
			let request = axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
				.then((res) => {
					context.commit('updateSuggestions', [0, res.data])
					context.commit('changeCRloadingStatus')
				}, () => {
					//fail route
					context.commit('changeServerStatus')
				})
					// don't trigger ML update when CR changes or is updated
					// .then(() => {
					// 	if(triggerML == true) {
					// 		context.dispatch('updateMLAnnotations', label)
					// 	}
					// })
			return request
		},

		deleteAllMLsuggestions(context) {
			context.commit('changeMLloadingStatus')
			let path = context.state.serverAdress + '/api/recs/ML/' + context.state.currentDocument.id
			axios.delete(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
			.then(() => {
				context.commit('removeMLsuggestions')
				context.commit('changeMLloadingStatus')
			})
		},

		changeMLtoManual(context, annotationID) {
			let path = context.state.serverAdress + '/api/recs/ML/' + context.state.currentDocument.id + "/" + annotationID
			axios.get(path, { headers: { Authorization: 'Bearer: ' + context.state.jwt.token } })
			.then(() => {
				context.commit('changeToManual', annotationID)
			})
		},

	

	},

	modules: {

	},

})

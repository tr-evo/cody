"""
api.py
- provides the API endpoints for consuming and producing
  REST requests and responses
"""

from flask import Blueprint, jsonify, request, current_app

api = Blueprint('api', __name__)

import json
import time
from datetime import datetime, timedelta
from functools import wraps

import sys, traceback
import os
import shutil
import logging

#for decoding parsed URIs
from urllib.parse import unquote

gen_log = logging.getLogger('general')
stats_log = logging.getLogger('stats')

#import own utilities
import codyapi.codeRuleUtility as codeRuleUtility
import codyapi.mlUtility as mlUtility

#import model.py for user classes
from .models import User, db
import jwt

#control variable for event stream
sendUpdate = False

#RESTful table
# Endpoint										Result											CRUD		HTTP
# /api/annotations/<documentID>					Get all annotations for one document			Read		GET
# /api/annotations/<documentID>/<annotationID>	Add a single annotation 						Create		POST
# /api/annotations/<documentID>/<annotationID>	Updates a single annotation  					Update 		PUT
# /api/annotations/<documentID>/<annotationID>	Deletes a single annotation 					Remove 		DELETE

# /api/labels/<documentID>						Return the codebook for a document  			Read		GET
# /api/labels/<documentID>						Add a single label to the codebook 				Create		POST
# /api/labels/<documentID>/<label>				Retrieve a code rule for a Label 				Read		GET
# /api/labels/<documentID>/<label>				Change a code rule for a Label 					Update 		PUT
# /api/labels/all/<documentID>					Delete codebook and add a new one				Replace		POST		<- for changing order of labels
# /api/labels/single/<documentID>/<label>		Change a label and update annotations 			Update 		PUT			<- editing labels
# /api/labels/single/<documentID>/<label>		Delete a label and all annotations 				Delete 		DELETE		<- delete single label

# /api/recs/ML/<documentID>						Trigger ML retraining for document 				Read 		GET
# /api/recs/ML/<documentID>						Delete all ML suggestions for document 			Remove 		DELETE
# /api/recs/ML/<documentID>/<annotationID>		Change ML suggestion to "manual" annotation 	Update 		PUT
# /api/recs/CR/<documentID>/<label>				Trigger CR retraining for document and label	Read 		GET

# /api/documents								Retrieve the list of documents on the server	Read		GET
# /api/documents								Save a document on the server					Create		POST
# /api/documents/<documentID>					Delete a document from the server				Remove		DELETE

# /api/sections/<documentID>					Retrieve array of document sections				Read		GET
#		- Build an array of objects in tree shape: ConversationID -> Attributes (3): Text for attribute as String separated by \n & \n\n																
#
# /ping											Sanity check									Read		GET

#helper function to save timestamp of change whenever changes are made
def saveChangeTimestamp(documentID):
	try:
		call = db.session.execute(
			"UPDATE documents SET lastChanged = :last WHERE id = :id",
			{"last": time.time(), "id": documentID})
		db.session.commit()
		return "Timestamp saved"
	except:
		gen_log.info("Error msg saveChangeTimestamp: %s", traceback.format_exc())
		return False

#decorator that makes sure that requests come with a valid JWT token in their header
def token_required(f):
	@wraps(f)
	def _verify(*args, **kwargs):
		auth_headers = request.headers.get('Authorization', '').split()

		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		expired_msg = {
			'message': 'Expired token. Reauthentication required.',
			'authenticated': False
		}

		if len(auth_headers) != 2:
			return jsonify(invalid_msg), 401

		try:
			token = auth_headers[1]
			data = jwt.decode(token, current_app.config['SECRET_KEY'])
			
			#cursor = connection.cursor()
			call = db.session.execute(
				"SELECT id FROM users WHERE email = :mail",
				{"mail": data['sub']})
			#user[0] = id, user[1] = password
			user = call.fetchone()[0]
			db.session.commit()

			if not user:
				raise RuntimeError('User not found')

			#add list of all documents belonging to user to user return object
			call = db.session.execute(
				"SELECT id FROM documents WHERE owner = :owner",
				{"owner": user})
			documents = call.fetchall()
			db.session.commit()

			user_object = {'id': user, 'documents': documents}

			return f(user_object, *args, **kwargs)
		except jwt.ExpiredSignatureError:
			return jsonify(expired_msg), 401 # 401 is Unauthorized HTTP status code
		except (jwt.InvalidTokenError, Exception) as e:
			gen_log.info(e)
			return jsonify(invalid_msg), 401

	return _verify




#POST route to register a new user
@api.route('/register/', methods=('POST',))
def register():
	data = request.json
	user = User(**data)

	try:
		#cursor = connection.cursor()
		call = db.session.execute(
			"INSERT INTO users (email, password) VALUES (:mail, :pw)",
			{"mail": user.email, "pw": user.password})
		db.session.commit()

		return jsonify(user.to_dict()), 201

	except Exception:
		print("error occured: %s", traceback.format_exc())
		gen_log.info("Error with commiting new user in register in api.py: %s", traceback.format_exc())

@api.route('/login/', methods=('POST',))
def login():
	data = request.json
	user = User.authenticate(**data)

	if not user:
		return jsonify({'message': 'Invalid credentials', 'authenticated': False}), 401

	token = jwt.encode({
		'sub': user['email'],
		'iat': datetime.utcnow(),
		'exp': datetime.utcnow() + timedelta(minutes=480)},
		current_app.config['SECRET_KEY'])

	stats_log.info("> Login user: %s", user['email'])
	return jsonify({'token': token.decode('UTF-8') })




#GET/POST route to receive and return ALL ANNOTATIONS for one document
@api.route('/annotations/<documentID>', methods=['GET'])
@token_required
def collection(current_user, documentID):
	if (int(documentID), ) in current_user["documents"]:
		all_annotations = get_all_annotations(documentID)
		return json.dumps(all_annotations)
	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401


def get_all_annotations(id):
	try:
		call = db.session.execute(
			"SELECT conversation, attribute, annotationID, document, start, length, label, isRecommendation, matchHighlight, confidence FROM annotations WHERE documentID = :id",
			{"id": id})
		all_annotations = call.fetchall()
		db.session.commit()

		result = []
		for row in all_annotations:
			result.append(row.values())

		return result
	except:
		gen_log.info("Error msg get_all_annotations: %s", traceback.format_exc())
		return ("Error with fetching annotations for document id " + id)





#POST/DELETE/PUT route for one single annotations
@api.route('/annotations/<documentID>/<annotationID>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@token_required
def single_annotation(current_user, documentID, annotationID):
	if (int(documentID), ) in current_user["documents"]:
		saveChangeTimestamp(documentID)
		if request.method == 'POST':
			data = request.json
			result = add_single_annotation(documentID, annotationID, data)
			return jsonify(result)
		elif request.method == 'PUT':
			data = request.json
			result = edit_single_annotation(documentID, annotationID, data["label"])

			return jsonify(result)

		elif request.method == 'DELETE':
			result = delete_single_annotation(documentID, annotationID)
			return jsonify(result)

		elif request.method == 'GET':
			result = get_single_annotation(documentID, annotationID)
			return jsonify(result)

	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401


def add_single_annotation(documentID, annotationID, data):
	try:
		currentSection = getSectionLink(documentID, data["conversation"], data["attribute"], data["id"], data["start"])
			
		call = db.session.execute(
			"INSERT INTO annotations (documentID, conversation, attribute, annotationID, document, start, length, label, isRecommendation, sectionLink) values (:docID, :conv, :att, :annID, :doc, :start, :length, :label, :isRec, :secLink)",
			{"docID": documentID, "conv": data["conversation"], "att": data["attribute"], "annID": annotationID, "doc": data["id"], "start": data["start"], "length": data["length"], "label": data["label"], "isRec": 0, "secLink": currentSection})
		db.session.commit()
		result = {'status': 1, 'message': 'New annotation saved'}
	
	except:
		gen_log.info("Error msg add_single_annotation: %s", traceback.format_exc())
		result = {'status': 0, 'message': 'Error with PUSH one annotation: ' + documentID + '//' + annotationID}
	
	stats_log.info("%s-ADD", documentID)
	return result

def edit_single_annotation(documentID, annotationID, newLabel):
	try:
		#is the annotation to be edited a recommendation?
		call = db.session.execute(
			"SELECT isRecommendation FROM annotations WHERE documentID = :id AND annotationID = :annID",
			{"id": documentID, "annID": annotationID})
		isRecommendation = call.fetchone()[0]
		db.session.commit()

		#set isRecommendation to 0 because manual change
		db.session.execute(
			"UPDATE annotations SET label = :label, isRecommendation = 0, confidence = Null WHERE documentID = :id AND annotationID = :annID",
			{"label": newLabel, "id": documentID, "annID": annotationID})
		db.session.commit()

		#if a annotation is updated that is a recommendation -> the recommendations for this annotationID need to be deleted
		if isRecommendation == 1:
			stats_log.info("%s-EDIT-REC-%s", documentID, newLabel)
			#remove recommendations for this annotationID
			db.session.execute(
				"DELETE FROM recommendations WHERE documentID = :id AND annotationID = :annID",
				{"id": documentID, "annID": annotationID})
			db.session.commit()
		else:
			stats_log.info("%s-EDIT-MAN-%s", documentID, newLabel)

		result = {'status': 1, 'message': 'Annotation ' + annotationID + ' updated!'}
	
	except:
		gen_log.info("Error msg edit_single_annotation: %s", traceback.format_exc())
		result = {'status': 0, 'message': 'Error with one annotation: ' + documentID + '//' + annotationID}

	return result

def delete_single_annotation(documentID, annotationID):
	try:
		db.session.execute(
			"DELETE FROM annotations WHERE documentID = :id AND annotationID = :annID",
			{"id": documentID, "annID": annotationID})
		db.session.commit()

		result = {'status': 1, 'message': 'Annotation ' + annotationID + ' deleted!'}

	except:
		gen_log.info("Error msg delete_single_annotation: %s", traceback.format_exc())
		result = {'status': 0, 'message': 'Error with DELETE one annotation: ' + documentID + '//' + annotationID}

	stats_log.info("%s-DELETE", documentID)
	return result

def get_single_annotation(documentID, annotationID):
	try:
		call = db.session.execute(
			"SELECT conversation, attribute, annotationID, document, start, length, label, isRecommendation, matchHighlight, confidence FROM annotations WHERE documentID = :id AND annotationID = :annID",
			{"id": documentID, "annID": annotationID})
		single = call.fetchone()
		db.session.commit()

		result = single.values()

	except:
		gen_log.info("Error msg get_single_annotation: %s", traceback.format_exc())
		result = {'status': 0, 'message': 'Error with GET one annotation: ' + documentID + '//' + annotationID}

	return result

#helper to get section link based on annotated text / conversation / attribute
def getSectionLink(documentID, conversation, attribute, text, start):
	try:
		#first retrieve id and text for all sections that might be annotated
		call = db.session.execute(
			"SELECT id, section FROM sections WHERE documentID = :id AND conversation = :conv AND attribute = :att",
			{"id": documentID, "conv": conversation, "att": attribute})
		relevant_sections = call.fetchall()
		db.session.commit()
		#transform RowProxy to list of lists
		result = []
		for row in relevant_sections:
			result.append(row.values())
		relevant_sections = result

		#make sure that no id is returned because words were matched prematurely for text
		sum_length = 0
		text_parts = text.split("\n")
		#get longest part in text_parts
		longest_text_break = max(text_parts, key=len)
		#loop over relevant sections and compare to text
		for section in relevant_sections:
			sum_length = sum_length + len(section[1]) + 2
			#paragraph annotation case
			if(text in section[1] and start < sum_length):
				return section[0]
			#free form with annotations across sections - return ID of longest matching section
			elif(longest_text_break in section[1] and start < sum_length):
				return section[0]

	except:
		gen_log.info("Error occured in 'getSectionLink' when identifying section id on adding an annotation")
		gen_log.info("Unexpected error: %s", traceback.format_exc())







#GET route to receive and return ENTIRE CODEBOOK | POST to add one entry
@api.route('/labels/<documentID>', methods=['GET', 'POST'])
@token_required
def codebook(current_user, documentID):
	if (int(documentID), ) in current_user["documents"]:
		if request.method == 'GET':
			#return list of document names and ID
			all_labels = get_all_labels(documentID)
			return json.dumps(all_labels)
		elif request.method == 'POST':
			data = request.json
			result = add_single_label(documentID, data)

			return jsonify(result)
	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401
	

def get_all_labels(id):
	try:
		call = db.session.execute(
			"SELECT label, color, codeRule FROM labels WHERE documentID = :id",
			{"id": id})
		all_labels = call.fetchall()
		db.session.commit()

		#transform RowProxy to list of lists
		result = []
		for row in all_labels:
			result.append(row.values())

		return result
	except:
		gen_log.info("Unexpected error get_all_labels: %s", traceback.format_exc())
		return ("Error with fetching labels for document id " + id)
		

def add_single_label(documentID, label):
	try:
		#perform insert for all objects in labels input
		db.session.execute(
			"INSERT INTO labels (documentID, label, color) values (:id, :label, :color)",
			{"id": documentID, "label": label["text"], "color": label["color"]})
		db.session.commit()

		result = {'status': 1, 'message': 'New Label added'}
	except:
		result = {'status': 0, 'message': 'Error with PUSH new label'}
		gen_log.info("Unexpected error add_single_label: %s", traceback.format_exc())
	
	stats_log.info("%s-NEW-LABEL", documentID)
	return result






#GET / PUT route for code rules for a specific label and document
@api.route('/labels/<documentID>/<path:label>', methods=['GET', 'PUT'])
@token_required
def codeRules(current_user, documentID, label):
	#decode encoded uri label
	decodeLabel = unquote(label)
	
	if (int(documentID), ) in current_user["documents"]:
		if request.method == 'GET':
			#return code rule for specific label (document + label is unique)
			singleCodeRule = get_single_rule(documentID, decodeLabel)
			return json.dumps(singleCodeRule)
		elif request.method == 'PUT':
			#change code rule for specific label
			stats_log.info("%s-EDIT-CR-%s", documentID, decodeLabel)
			data = request.json
			capData = toUpper(data["rule"])
			result = change_single_rule(documentID, decodeLabel, capData)

			#when code rule is changed, we need to update recommendations for that particular label
			limit = None
			#register executor
			#executor = Executor(current_app)
			#executor.submit(updateCRRecommendations, documentID, capData, limit, label)

			return jsonify(result)
	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401


def get_single_rule(documentID, label):
	#default has no code rule
	if label != "default":
		try:
			call = db.session.execute(
				"SELECT codeRule FROM labels WHERE documentID = :id AND label = :label",
				{"id": documentID, "label": label})
			single_rule = call.fetchone()
			db.session.commit()

			generateNewRule = False
			if single_rule == None:
				gen_log.info("no rule found")
				generateNewRule = True
			elif single_rule[0] == None:
				gen_log.info("No rule set")
				generateNewRule = True

			gen_log.info("found this: %s", single_rule)
			gen_log.info("new rule? %s", generateNewRule)

			#if no code rule exists - create one! No thread since FE waits for CR return value
			if generateNewRule == True:
				#create new rule as tuple
				generateNewRule = generateCR(documentID, label, 1)
				stats_log.info("%s-NEW-CR", documentID)
				return [(generateNewRule, ), 1]
			else:
				#return existing rule, use values to transform RowProxy object
				return [single_rule.values(), 0]
				
		except:
			gen_log.info("Error msg get_single_rule: %s", traceback.format_exc())
			return ("Error with getting code rule for document id " + documentID + " and label: " + label)

def change_single_rule(documentID, label, data):
	try:
		db.session.execute(
			"UPDATE labels SET codeRule = :CR WHERE documentID = :id AND label = :label",
			{"CR": data, "id": documentID, "label": label})
		db.session.commit()

		result = {'status': 1, 'message': 'Label ' + label + ' updated!'}

	except:
		gen_log.info("Error msg change_single_rule: %s", traceback.format_exc())
		result = {'status': 0, 'message': 'Error with UPDATE one code rule: ' + documentID + '//' + label}

	return result

#helper to upper-case all query-style words in code rules
def toUpper(string):
	s = string.strip().split(' ')
	st = ''
	accepted_strings = {'and', 'or', 'not'}

	for word in s:
		if word in accepted_strings:
			st += word.replace(word, word.upper()) + " "
		else:
			st += word + " "

	return st

#Thread for code rule generation
def generateCR(documentID, label, iteration):
	#retrieve section for which label is currently used
	#include a little break, so label can be attributed to annotatoion
	#time.sleep(1)
	if iteration <= 3:
		try:
			section = []
			#select annotation content from annotation with this label
			gen_log.info("%s, %s", documentID, label)
			call = db.session.execute(
				"SELECT document FROM annotations WHERE documentID = :id AND label = :label",
				{"id": documentID, "label": label})
			section = call.fetchone()
			db.session.commit()

			gen_log.info("found this section in generateCR %s", section)

			#get suggestion for code rule
			if section != None:
				ruleSuggestion = codeRuleUtility.codeRuleSuggestion(documentID, label, section[0])
				gen_log.info("new rule suggestion generated // %s", ruleSuggestion)

				#update code rule
				executor = change_single_rule(documentID, label, ruleSuggestion)

				return ruleSuggestion

			else:
				#potentiall remove dangerous recursive call, could crash everything
				return generateCR(documentID, label, iteration + 1)
		
		except Exception:
			gen_log.info("Error occured in 'generateCR' when identifying content of annotation with new label")
			gen_log.info("Unexpected error: %s", traceback.format_exc())

	else:
		return "Sorry, could not generate a code rule suggestion."





#GET / PUT route for code rules for a specific label and document
@api.route('/recs/ML/<documentID>', methods=['GET', 'DELETE'])
@token_required
def newMLInput(current_user, documentID):
	if (int(documentID), ) in current_user["documents"]:
		if request.method == 'GET':
			#retrain ML model and define new annotations, make use of existing CR annotations
			execute = updateMLonAddAnnotation(documentID, 1)
			#return all annotations to client
			all_annotations = get_all_annotations(documentID)
			return json.dumps(all_annotations)
		elif request.method == 'DELETE':
			stats_log.info("%s-DELETE-ALL-ML", documentID)
			#delete all ML suggestions for document
			execute = removeMLSuggestions(documentID)
			return jsonify(execute)
	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401

#thread helper to trigger ML update and make recommendations if necessary
def updateMLonAddAnnotation(documentID, useCRRecommendations):
	updateAnnotationsNecessary = False
	try:
		updateAnnotationsNecessary = mlUtility.iterateSGDprediction(documentID, useCRRecommendations)
	except:
		gen_log.info("Error when updating ML on AddAnnotation in api.py: %s", traceback.format_exc())

	if updateAnnotationsNecessary:
		#create new annotation recommendations based on result list and existing recommendations for label
		#global sendUpdate
		sendUpdate = mlUtility.updateRecommendationAnnotations(documentID)

def removeMLSuggestions(documentID):
	try:
		db.session.execute(
			"UPDATE recommendations SET deletionFlag = 1 WHERE documentID = :docID AND confidence < 1",
			{"docID": documentID})
		db.session.commit()
		#update annotations
		return mlUtility.updateRecommendationAnnotations(documentID)

	except Exception:
		gen_log.info("Error occured in 'generateCR' when identifying content of annotation with new label")
		gen_log.info("Unexpected error: %s", traceback.format_exc())
		return False

#PUT to accept ML suggestions
@api.route('/recs/ML/<documentID>/<annotationID>', methods=['GET'])
@token_required
def changeToManual(current_user, documentID, annotationID):
	if (int(documentID), ) in current_user["documents"]:
		if request.method == 'GET':
			stats_log.info("%s-ML-TO-MANUAL", documentID)
			#retrain ML model and define new annotations, make use of existing CR annotations
			execute = changeMLtoManual(documentID, annotationID)
			return jsonify(execute)

	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401

def changeMLtoManual(documentID, annotationID):
	try:
		db.session.execute(
			"UPDATE annotations SET isRecommendation = 0, matchHighlight = NULL, confidence = NULL WHERE documentID = :docID AND annotationID = :anID",
			{"docID": documentID, "anID": annotationID})
		db.session.execute(
			"DELETE FROM recommendations WHERE documentID = :docID AND annotationID = :anID",
			{"docID": documentID, "anID": annotationID})
		db.session.commit()

		return True

	except Exception:
		gen_log.info("Error occured in 'generateCR' when identifying content of annotation with new label")
		gen_log.info("Unexpected error: %s", traceback.format_exc())
		return False


#GET / PUT route for code rules for a specific label and document
@api.route('/recs/CR/<documentID>/<path:label>', methods=['GET'])
@token_required
def newCRInput(current_user, documentID, label):
	#decode encoded uri label
	decodeLabel = unquote(label)

	if (int(documentID), ) in current_user["documents"]:
		if request.method == 'GET':
			#update recommendations based on changed code rule
			limit = None
			#get label from db
			call = db.session.execute(
				"SELECT codeRule FROM labels WHERE documentID = :id AND label = :label",
				{"id": documentID, "label": decodeLabel})
			single_rule = call.fetchone()
			db.session.commit()
			#run helper function, single_rule[0] to get string instead of tuple
			execute = updateCRRecommendations(documentID, single_rule[0], limit, decodeLabel)
			#return code rule for specific label (document + label is unique)
			all_annotations = get_all_annotations(documentID)
			return json.dumps(all_annotations)
	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401

#thread to act on code rule change to make recommendations
def updateCRRecommendations(documentID, query, limit, label):
	#get list of search results
	searchResults = (codeRuleUtility.search(documentID, query, limit)).copy()

	#update recommendations table
	mlUtility.updateRecommendationsTable(documentID, searchResults, label)

	#create new annotation recommendations based on result list and existing recommendations for label
	#global sendUpdate
	sendUpdate = mlUtility.updateRecommendationAnnotations(documentID)








#PUT route to change a label and update all annotations accordingly
@api.route('/labels/single/<documentID>/<path:label>', methods=['PUT', 'DELETE'])
@token_required
def updateSingleLabel(current_user, documentID, label):
	#decode encoded uri label
	decodeLabel = unquote(label)
	
	if (int(documentID), ) in current_user["documents"]:
		if request.method == 'PUT':
			data = request.json
			result = update_single_label(documentID, decodeLabel, data["newLabel"])
			return jsonify(result)
		elif request.method == 'DELETE':
			result = delete_single_label(documentID, decodeLabel)
			return jsonify(result)
	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401

#method to update or if necessary merge labels
def update_single_label(documentID, label, data):
	#COULD REINTRODUCE ROLLBACK HANDELING HERE IF ERROR OCCURES
	try:
		#check if label exists already in labels table
		call = db.session.execute(
			"SELECT label FROM labels WHERE documentID = :id",
			{"id": documentID})
		codebookRP = call.fetchall()
		#transform RowProxy results to list
		codebookList = []
		for row in codebookRP:
			codebookList.append(row.values()[0])

		if data in codebookList and data != label:
			#delete old label, new one exists already
			db.session.execute(
				"DELETE FROM labels WHERE documentID = :id AND label = :labelWhere",
				{"id": documentID, "labelWhere": label})
			db.session.commit()

		else:
			#update label in labels table if doesn't exist already
			db.session.execute(
				"UPDATE labels SET label = :labelSet WHERE documentID = :id AND label = :labelWhere",
				{"labelSet": data, "id": documentID, "labelWhere": label})
			db.session.commit()

		#second, update all annotations with label and update accordingly --> if new label exists already, that is a merge of existing and "new" annotations
		db.session.execute(
			"UPDATE annotations SET label = :labelSet WHERE documentID = :id AND label = :labelWhere",
			{"labelSet": data, "id": documentID, "labelWhere": label})
		db.session.commit()

		#third, update all recommendations with label and update accordingly
		db.session.execute(
			"UPDATE recommendations SET labelCR = :labelCR, labelMR = :labelMR WHERE documentID = :id AND (labelCR = :CRfilter OR labelMR = :MRfilter)",
			{"labelCR": data, "labelMR": data, "id": documentID, "CRfilter": label, "MRfilter": label})
		db.session.commit()

		stats_log.info("%s-EDIT-LABEL-%s", documentID, label)
		return 1

	except:
		db.session.rollback()
		gen_log.info("Update of label %s in document with id [%s] failed!", label, documentID)
		gen_log.info("Error msg:", traceback.format_exc())
		return 0

def delete_single_label(documentID, label):
	#COULD REINTRODUCE ROLLBACK HANDELING HERE IF ERROR OCCURES
	try:
		#update label in labels table
		db.session.execute(
			"DELETE FROM labels WHERE documentID = :id AND label = :labelWhere",
			{"id": documentID, "labelWhere": label})
		db.session.commit()

		#second, update all annotations with label and update accordingly
		db.session.execute(
			"DELETE FROM annotations WHERE documentID = :id AND label = :labelWhere",
			{"id": documentID, "labelWhere": label})
		db.session.commit()

		#third, update all recommendations with label and update accordingly
		db.session.execute(
			"DELETE FROM recommendations WHERE documentID = :id AND (labelCR = :CRfilter OR labelMR = :MRfilter)",
			{"id": documentID, "CRfilter": label, "MRfilter": label})
		db.session.commit()

		stats_log.info("%s-DELETE-LABEL-%s", documentID, label)
		return 1

	except:
		db.session.rollback()
		gen_log.info("Deletion of label %s in document with id [%s] failed!", label, documentID)
		gen_log.info("Error msg:", traceback.format_exc())
		return 0


			


#POST route to change the order of labels by rewriting the entire codebook for a document
@api.route('/labels/all/<documentID>', methods=['POST'])
@token_required
def updateEntireCodebook(current_user, documentID):
	if (int(documentID), ) in current_user["documents"]:
		data = request.json
		result = updateList(documentID, data)
		return jsonify(result)
	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401


def updateList(documentID, data):
	#CONTINUE WORK HERE SO LABELS ARE UPDATED!
	try:
		#delete existing labels
		db.session.execute(
			"DELETE FROM labels WHERE documentID = :id",
			{"id": documentID})
		db.session.commit()

		#loop over data and update new labels
		for key in data:
			db.session.execute(
				"INSERT INTO labels (documentID, label, color) values (:id, :label, :color)",
				{"id": documentID, "label": key["text"], "color": key["color"]})
		db.session.commit()
			
		result = {'status': 1, 'message': 'Labels updated changed'}

	except:
		gen_log.info("Error msg updateList: %s", traceback.format_exc())
		result = {'status': 0, 'message': 'Error with updating /all new labels'}

	return result





#GET ALL documents / POST route for (new) documents
@api.route('/documents', methods=['GET', 'POST'])
@token_required
def list(current_user):
	if request.method == 'GET':
		all_documents = get_all_documents(current_user)
		return json.dumps(all_documents)
	elif request.method == 'POST':
		data = request.json
		#test creation methods
		result = newDocument(data, current_user)
		return jsonify(result)


def get_all_documents(current_user):
	try:
		call = db.session.execute(
			"SELECT * FROM documents WHERE owner = :owner",
			{"owner": current_user["id"]})
		all_documents = call.fetchall()
		db.session.commit()

		result = []
		for row in all_documents:
			result.append(row.values())

		return result
	except:
		gen_log.info("Error msg get_all_documents: %s", traceback.format_exc())
		return "Error with fetching documents"

def newDocument(feInput, current_user):
	try:
		#populate overview documents table with new document name / settings
		db.session.execute(
			"INSERT INTO documents (name, owner, lastChanged, inputType, unitOfAnalysis) values (:name, :owner, :lastChanged, :inputType, :unitOfAnalysis)",
			{"name": feInput["name"], "owner": current_user["id"], "lastChanged": time.time(), "inputType": feInput["settings"]["type"], "unitOfAnalysis": feInput["settings"]["uoa"]})	
		db.session.commit()

		#populate sections table with document input with documentID of this document
		call = db.session.execute(
			"SELECT id FROM documents WHERE name = :name AND owner = :owner",
			{"name": feInput["name"], "owner": current_user["id"]})
		documentID = call.fetchone()
		db.session.commit()

		#create new dict to save the input temporary to process it for constructing the search index
		sectionDict  = {}

		if feInput["settings"]["type"] == 0:
			sectionDict = write_Text_Document(documentID[0], feInput["content"])
		elif feInput["settings"]["type"] == 1:
			sectionDict = write_CSV_Document(documentID[0], feInput["content"])
		elif feInput["settings"]["type"] == 2:
			sectionDict = write_LadderBot_Document(documentID[0], feInput["content"])

		#use sectionDict to construct search index syncronous to prevent errors due to index and language of document not existing in db
		codeRuleUtility.setup(documentID[0], sectionDict)

		result = {'status': 1, 'message': 'Document saved'}

	except:
		gen_log.info("Error msg newDocument: %s", traceback.format_exc())
		result = {'status': 0, 'message': 'ERROR with save'}
	return result

#Input = Text
def write_Text_Document(documentID, text):
	#case text
	#temp var for return
	sectionID = 0
	result = {}
	conv = "Interview"
	attr = "Interview"

	try:
		#break on every section / return
		for section in iter(text.splitlines()):
			#write every line as section with delimiter "."
			for line in section.split("."):
				#save the id of INSERT row to write them in dict
				strippedLine = line.strip()
				if len(strippedLine) > 0:
					strippedLine = strippedLine + "."
					call = db.session.execute(
						"INSERT INTO sections (documentID, conversation, attribute, section, label, isRecommendation) values (:documentID, :conversation, :attribute, :section, :label, :isRecommendation)",
						{"documentID": documentID, "conversation": conv, "attribute": attr, "section": strippedLine, "label": "", "isRecommendation": 0})
					db.session.commit()

					sectionID = call.lastrowid
					#write to dict
					tempDict = {'id': sectionID, 'section': strippedLine}
					result[sectionID] = tempDict
		#return the dict
		return result

	except:
		gen_log.info("Error msg write_Text_Document: %s", traceback.format_exc())

#Input = CSV
def write_CSV_Document(documentID, text):
	# CSV shape >> LadderID, Attribute, Section -> fields separated by comma, lines separated by line breakes
	#temp var for return
	sectionID = 0
	result = {}

	try:
		#get next id that will be used when new document is inserted (necessary to match ID of sections table to later match search results and sections table)
		previousChunks = [0, 0, 0]
		#loop over lines
		for line in iter(text.splitlines()):
			#break line into columns | 0: ladder id, 1: attribute, 2: section
			chunks = line.split(';')

			#if ladder id or attribute are empty, use the last known entry
			if chunks[0] == "":
				chunks[0] = previousChunks[0]
			if chunks[1] == "":
				chunks[1] = previousChunks[1]
			previousChunks = chunks
			#write as section
			#save the id of INSERT row to write them in dict
			chunks[2] = chunks[2].strip()
			call = db.session.execute(
				"INSERT INTO sections (documentID, conversation, attribute, section, label, isRecommendation) values (:id, :conv, :att, :section, :label, :isRec)",
				{"id": documentID, "conv": chunks[0], "att": chunks[1], "section": chunks[2], "label": "", "isRec": 0})
			db.session.commit()
			sectionID = call.lastrowid
			#write to dict
			tempDict = {'id': sectionID, 'section': chunks[2]}
			result[sectionID] = tempDict
		#return the dict
		return result

	except:
		gen_log.info("Issue occured with writing CSV document")
		gen_log.info("Unexpected error: %s", traceback.format_exc())

#Input = Ladderbot Json
def write_LadderBot_Document(documentID, json):
	#temp var for return
	sectionID = 0
	result = {}

	try:
		#case ladderbot
		#loop through every conversation
		for conv in json:
			#loop through every utterance starting with 8 -> first question first ladder
			temp = ""
			for idx, key in enumerate(json[conv], 0):
			##to start with 8
				if idx > 7:
				 #write every question / answer combination to db as section
					if key["sender"] == "LadderBot":
						temp = key["message"]
						#get next attribute as long as index is not out of bounds
						tempAttribute = json[conv][(idx + 1) % len(json[conv])]["seed"]
					else:
						temp = temp + "\n\t" + key["message"]
						tempAttribute = key["seed"]
						#write to db
						#save the id of INSERT row to write them in dict
						call = db.session.execute(
							"INSERT INTO sections (documentID, conversation, attribute, section, label, isRecommendation) values (:id, :conv, :att, :section, :label, :isRec)",
							{"id": documentID, "conv": conv, "att": tempAttribute, "section": temp, "label": "", "isRec": 0})
						db.session.commit()
						sectionID = call.lastrowid

						#write to dict
						tempDict = {'id': sectionID, 'section': temp}
						result[sectionID] = tempDict
		#return the dict
		return result

	except:
		gen_log.info("Issue occured with writing Ladderbot document")
		gen_log.info("Unexpected error: %s", traceback.format_exc())




#DELETE ONE document
@api.route('/documents/<documentID>', methods=['DELETE'])
@token_required
def removeDocument(current_user, documentID):
	if (int(documentID), ) in current_user["documents"]:
		if request.method == 'DELETE':
			remove = delete_document(documentID)
			return jsonify(remove)
	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401

		
def delete_document(documentID):
	try:
		#remove annotations, documents, labels, recommendations, sections
		db.session.execute(
			"DELETE FROM annotations WHERE documentID = :id",
			{"id": documentID})
		db.session.execute(
			"DELETE FROM documents WHERE id = :id",
			{"id": documentID})
		db.session.execute(
			"DELETE FROM labels WHERE documentID = :id",
			{"id": documentID})
		db.session.execute(
			"DELETE FROM recommendations WHERE documentID = :id",
			{"id": documentID})
		db.session.execute(
			"DELETE FROM sections WHERE documentID = :id",
			{"id": documentID})
		db.session.commit()
		#delete index for document as well by deleting relevant folder
		foldername = "document_" + str(documentID)
		if os.path.exists("indexdir/" + foldername):
			shutil.rmtree("indexdir/" + foldername)
		return 1

	except:
		db.session.rollback()
		gen_log.info("Deletion of document with id [", documentID, "] failed!")
		gen_log.info("Error msg: %s", traceback.format_exc())
		return 0





#GET Route for getting ALL SECTIONS for on documentID
@api.route('/sections/<documentID>', methods=['GET', 'POST'])
@token_required
def getSections(current_user, documentID):
	if (int(documentID), ) in current_user["documents"]:
		if request.method == 'GET':
			all_sections = get_all_sections(documentID)
			return json.dumps(all_sections)
		elif request.method == 'POST':
			#later for ML
			pass
	else:
		invalid_msg = {
			'message': 'Invalid token. Registeration and / or authentication required',
			'authenticated': False
		}
		return jsonify(invalid_msg), 401


def get_all_sections(id):
	try:
		#identify type of document
		call = db.session.execute(
			"SELECT inputType FROM documents WHERE id = :id",
			{"id": id})	
		inputType = call.fetchone()
		db.session.commit()

		#format output if there are multiple conversations: Text processed as laddering with one conversation & one attribute
		call = db.session.execute(
			"SELECT conversation, attribute, section FROM sections WHERE documentID = :id",
			{"id": id})
		all_sections = call.fetchall()
		db.session.commit()
		#react to LadderBot input
		currentConv = ''
		currentAttr = ''
		newDict = {}
		tempString = ''

		for entry in all_sections:
			#add Conv to dict if new conv
			if currentConv != entry[0]:
				currentConv = entry[0]
				currentAttr = ''
				newDict[currentConv] = {}

			#if current Attr is new add to dict
			if currentAttr != entry[1]:
				currentAttr = entry[1]
				newDict[currentConv][currentAttr] = {}
				tempString = ''

			#add section to dict
			tempString = tempString + entry[2] + '\n\n'
			newDict[currentConv][currentAttr] = tempString

		return newDict

	except:
		gen_log.info("Error msg get_all_sections: %s", traceback.format_exc())
		return ("Error with fetching sections for document id " + id)







#sanity check route
@api.route('/ping', methods=['GET'])
def ping_pong():
		return jsonify('PONG!')

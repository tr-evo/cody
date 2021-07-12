from .models import db

from random import randrange
import sys, traceback
import codyapi.codeRuleUtility as codeRuleUtility
import itertools
import logging

gen_log = logging.getLogger('general')
stats_log = logging.getLogger('stats')

#Utils to retrain classifier for text classification using scikit learn
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import  TfidfVectorizer

#from sklearn.svm import SVC
from sklearn.linear_model import SGDClassifier

from sklearn.model_selection import train_test_split

from sklearn import metrics

import pandas as pd
import numpy as np

from time import time

from spacy.lang.en.stop_words import STOP_WORDS as stop_en
from spacy.lang.de.stop_words import STOP_WORDS as stop_de


#return list of existing recommendations | params(label)
def recommendationsForLabel(documentID, label, isMLRecommendationList):
	try:
		call = None
		#differentiate between CR and ML recommendations
		if isMLRecommendationList == False:
			#get list of existing recommendations for label (isRecommendation = 1)
			call = db.session.execute(
				"SELECT sectionID FROM recommendations WHERE labelCR = :lCR AND documentID = :docID",
				{"lCR": label, "docID": documentID})

		else: #case ML recommendations, retrieve only those recommendations made with ML model
			#get list of existing recommendations for label (isRecommendation = 1)
			call = db.session.execute(
				"SELECT sectionID FROM recommendations WHERE labelMR = :lMR AND documentID = :docID",
				{"lMR": label, "docID": documentID})

		#process results
		resultsTuple = call.fetchall()
		db.session.commit()

		resultsList = []
		for tup in resultsTuple:
			resultsList.append(tup[0])

		return resultsList

	except:
		gen_log.info("Error // recommendationsForLabel // couldnt fetch list")
		gen_log.info("Unexpected error: %s", traceback.format_exc())

#update recommendations table based on search results and label | params(documentID, searchResults, label)
def updateRecommendationsTable(documentID, searchResults, label):	
	#flag for ML recommendations
	isMLRecommendationList = False
	#take list from searchResults input object
	IDList = searchResults["IDList"]
	#take List of highlights from highlightsList if available
	if "highlightsList" in searchResults:
		highlightsList = searchResults["highlightsList"]
	else:
		#if highlightsList is not available, then we deal with ML recommendations, which are treated a little differently:
		isMLRecommendationList = True
		probaList = searchResults["probaList"]
		criticalWordsList = searchResults["criticalWords"]

	#controlprint
	gen_log.info("using ML recommendation route: %s", isMLRecommendationList)
	#retrieve list of sectionIDs that already have a recommendations for the current label
	oldRecommendations = recommendationsForLabel(documentID, label, isMLRecommendationList)

	#update sections table based on comparision of old and new recommendations
	#two sets of differences are needed, based on old and new recommendations
	inNewNotOld = set(IDList).difference(oldRecommendations)
	inOldNotNew = set(oldRecommendations).difference(IDList)

	print("> DELETE ENTRIES SOON: ", inOldNotNew)

	#if contained in both (union): do nothing | if in new but not in old (difference): add | if in old but not in new (difference): remove
	try:
		#differentiate ML and CR recommendation cases:
		if isMLRecommendationList == False:
			#case CR
			for entry in inNewNotOld:
				#check if there isnt any existing recommendation with this label for this particular section to prevent double recommendation of a section
				call = db.session.execute(
					"SELECT id FROM recommendations WHERE sectionID = :secID AND labelCR = :lCR AND documentID = :docID",
					{"secID": entry, "lCR": label, "docID": documentID})
				results = call.fetchone()
				db.session.commit()
				#if this particular recommendation exists already, skip insertion step
				if results != None:
					continue

				db.session.execute(
					"INSERT INTO recommendations (documentID, sectionID, labelCR, confidence, deletionFlag, ruleHighlight) values (:id, :secID, :lCR, :conf, :delFlag, :rule)",
					{"id": documentID, "secID": entry, "lCR": label, "conf": 1.0, "delFlag": 0, "rule": highlightsList[IDList.index(entry)]})
				db.session.commit()

				stats_log.info("%s-ADD-CR-%s", documentID, label)

			for entry in inOldNotNew:
				#FUTURE REFERENCE: At this point, it would be nice to check if there is another label that would make sense for this section
				db.session.execute(
					"UPDATE recommendations SET deletionFlag = :flag WHERE sectionID = :secID AND labelCR = :lCR AND documentID = :docID",
					{"flag": 1, "secID": entry, "lCR": label, "docID": documentID})
				db.session.commit()

				stats_log.info("%s-DELETE-CR-%s", documentID, label)

		#differentiate ML and CR recommendation cases:
		else:
			#case ML
			for entry in inNewNotOld:
				criticalWordsToString = ", ".join(criticalWordsList[IDList.index(entry)])
				#check if there isnt any existing recommendation with this label for this particular section to prevent double recommendation of a section
				call = db.session.execute(
					"SELECT id FROM recommendations WHERE sectionID = :secID AND labelMR = :lMR AND documentID = :docID",
					{"secID": entry, "lMR": label, "docID": documentID})
				results = call.fetchone()
				db.session.commit()
				#if this particular recommendation exists already, skip insertion step
				if results != None:
					continue

				db.session.execute(
					"INSERT INTO recommendations (documentID, sectionID, labelMR, confidence, deletionFlag, ruleHighlight) values (:id, :secID, :lMR, :conf, :flag, :rule)",
					{"id": documentID, "secID": entry, "lMR": label, "conf": probaList[IDList.index(entry)], "flag": 0, "rule": criticalWordsToString})
				db.session.commit()

				stats_log.info("%s-ADD-ML-%s", documentID, label)

			for entry in inOldNotNew:
				#FUTURE REFERENCE: At this point, it would be nice to check if there is another label that would make sense for this section
				db.session.execute(
					"UPDATE recommendations SET deletionFlag = :flag WHERE sectionID = :secID AND labelMR = :lMR AND documentID = :docID",
					{"flag": 1, "secID": entry, "lMR": label, "docID": documentID})
				db.session.commit()
				 	
				stats_log.info("%s-DELETE-ML-%s", documentID, label)

	except:
		gen_log.info("Error // updateRecommendationsTable // couldnt update table")
		gen_log.info("Unexpected error: %s", traceback.format_exc())

#helper function to update recommendation annotations | params(none)
def updateRecommendationAnnotations(documentID):
	gen_log.info(">>> updateRecommendationAnnotations")
	#method takes recommendations table as input and adjusts annotations accordingly
	#if deletionFlag = 1 -> remove annotation
	#if annotationID = empty -> add annotation and update annotationID
		#add annotation only if no human annotation for label and sectionID exists already

	#if deletionFlag = 1 -> remove annotation
	try:
		#get list of sectionIDs for recommendations to be deleted
		call = db.session.execute(
			"SELECT annotationID FROM recommendations WHERE deletionFlag = 1 AND documentID = :id",
			{"id": documentID})
		deletionList = call.fetchall()
		db.session.commit()

		for entry in deletionList:
			#delete annotation from table
			db.session.execute(
				"DELETE FROM annotations WHERE annotationID = :anID AND isRecommendation = :isRec AND documentID = :docID",
				{"anID": entry[0], "isRec": 1, "docID": documentID})
			db.session.commit()

		#delete all flagged recommendations
		db.session.execute(
			"DELETE FROM recommendations WHERE deletionFlag = 1 AND documentID = :id",
			{"id": documentID})
		db.session.commit()
	except:
		gen_log.info("Error // deleting old recommendations & annotations")
		gen_log.info("Unexpected error: %s", traceback.format_exc())

	#if annotationID = empty -> add annotation and update annotationID
		#add annotation only if no human annotation for label and sectionID exists already
	try:
		#get list of sectionIDs for which annotationID is not set in recommendation table
		call = db.session.execute(
			"SELECT sectionID, labelCR, labelMR, documentID, ruleHighlight, confidence FROM recommendations WHERE annotationID IS NULL AND documentID = :id",
			{"id": documentID})
		insertionList = call.fetchall()
		db.session.commit()

		for entry in insertionList:
			sectionID = entry[0]
			#differentiate ML and CR case
			label = entry[1] if entry[1] != None else entry[2]
			documentID = entry[3]
			#differentiate ML and CR case
			ruleHighlight = entry[4] if entry[4] != None else "No highlight for ML recommendation so far"
			confidence = entry[5]

			#first, we need to retrieve conversation, attribute and text based on section ID
			call = db.session.execute(
				"SELECT conversation, attribute, section FROM sections WHERE id = :id AND documentID = :docID",
				{"id": sectionID, "docID": documentID})
			fetchedInfo = call.fetchone()
			db.session.commit()

			conversation = fetchedInfo[0]
			attribute = fetchedInfo[1]
			document = fetchedInfo[2]
			#second, we can collect all sections for this particular attribute 
			call = db.session.execute(
				"SELECT id, section FROM sections WHERE documentID = :id AND conversation = :conv AND attribute = :att ORDER BY id",
				{"id": documentID, "conv": conversation, "att": attribute})
			fetchedInfo = call.fetchall()
			db.session.commit()
			#third, calculate start and length of annotation from attribute block information
			start = 0
			for section in fetchedInfo:
				#use all ids smaller than then sectionID of section to add up length
				if section[0] < sectionID:
					#count the characters in section and add 3 to account for white-characters
					start = start + len(section[1]) + 2
			length = len(document)
			#fill the annotation parameters and write to the annotations table
			annotationID = "{}{}{}{}{}{}{}{}{}".format(conversation[0], '-', attribute[0], '-', start, '-', length, '-', randrange(10000))

			#check if human annotation exists for this particular section and label already:
			call = db.session.execute(
				"SELECT annotationID FROM annotations WHERE documentID = :docID AND sectionLink = :link AND label = :label AND isRecommendation = :isRec",
				{"docID": documentID, "link": sectionID, "label": label, "isRec": 0})
			humanAnnotationExists = call.fetchone()
			db.session.commit()

			if humanAnnotationExists == None:
				#add new annotation
				db.session.execute(
					"INSERT INTO annotations (documentID, conversation, attribute, annotationID, document, start, length, label, isRecommendation, sectionLink, matchHighlight, confidence) values (:id, :conv, :att, :anID, :doc, :start, :length, :label, :isRec, :link, :match, :conf)",
					{"id": documentID, "conv": conversation, "att": attribute, "anID": annotationID, "doc": document, "start": start, "length": length, "label": label, "isRec": 1, "link": sectionID, "match": ruleHighlight, "conf": confidence})
				db.session.commit()

			#update annotationID in recommendations table
				#if human annotation exists, link annotationID anyways - can be used to verify human annotations later
			# - CR recommendation route
			if entry[1] != None:
				db.session.execute(
					"UPDATE recommendations SET annotationID = :anID WHERE documentID = :docID AND sectionID = :secID AND labelCR = :lCR",
					{"docID": documentID, "anID": annotationID, "secID": sectionID, "lCR": label})
				db.session.commit()

			# - ML recommendation route
			else:
				db.session.execute(
					"UPDATE recommendations SET annotationID = :anID WHERE documentID = :docID AND sectionID = :secID AND labelMR = :lMR",#
					{"docID": documentID, "anID": annotationID, "secID": sectionID, "lMR": label})
				db.session.commit()

		return True
	
	except:
		gen_log.info("Error: Adding new recommendation annotation for ID: %s", str(entry))
		gen_log.info("Unexpected error: %s", traceback.format_exc())



#New Approach: Combination of SGDClassifier and using Spies to determine prediction cutoff
# c.f. S. Schrunner, B. C. Geiger, A. Zernig, and R. Kern, “A generative semi-supervised classifier for datasets with unknown classes,” Proc. ACM Symp. Appl. Comput., pp. 1066–1074, 2020.
def iterateSGDprediction(documentID, allowRecommendations):
	gen_log.info(">>> ML Prediction for documentID [%s]", documentID)
# - collect all labeled sections -> positives (L)
	# set some variables for entire function
	df = None
	resultsTupleList = None

	#get annotations document, label field from annotations table filtering for documentID and isRecommendation
	try:
		call = None
		#two approaches can be used: only use human annotations -> allowRecommendations: 0, or use CR recommendations as well -> allowRecommendations: 1
		if allowRecommendations == 0:
			call = db.session.execute(
					"SELECT document, label, sectionLink FROM annotations WHERE documentID = :id AND isRecommendation = 0",
					{"id": documentID})

		else:
			#make sure to not select ML-based recommendations to not get into a loop of self-supporting suggestions
			call = db.session.execute(
					"SELECT document, label, sectionLink, isRecommendation FROM annotations WHERE documentID = :id AND confidence = 1 OR documentID = :id AND isRecommendation = 0",
					{"id": documentID})

		resultsTupleList = call.fetchall()
		db.session.commit()

	except:
		gen_log.info("Error with fetching positives for documentID %s in iterateSEMprediction() in mlUtility.py", documentID)
		gen_log.info("Unexpected error: %s", traceback.format_exc())

	#create data frame from selected results
	if resultsTupleList != None:
		df = pd.DataFrame(resultsTupleList, columns = ['Feature', 'Label', 'SectionLink', 'Manual'])

# - collect all unlabeled sections -> (For prediction of new labels later) (D)
	#get sectionIDs for that no labels exist currently (all - IDs from df)
	try:
		call = db.session.execute(
				"SELECT id, section FROM sections WHERE documentID = :id",
				{"id": documentID})
		resultsTupleList = call.fetchall()
		db.session.commit()

	except:
		gen_log.info("Error with fetching every section for documentID %s in iterateSEMprediction() in mlUtility.py", documentID)
		gen_log.info("Unexpected error: %s", traceback.format_exc())

	#use different intendation to indicate closing the sqlite3 connection
	sections = None

	#create data frame from selected results
	if resultsTupleList != None:
		sections = pd.DataFrame(resultsTupleList, columns = ['SectionLink', 'Feature'])
		gen_log.info("Found a total of sections: %s", len(sections))
		#reduce sections to those sections where not annotations are available already (only for CR recommendations though, allow algorithm to make new suggestions for ML sections to remove old ones)
		#df[SectionLink does not include ML recommendations, so new suggestions are created
		sections = sections[~sections['SectionLink'].isin(df['SectionLink'])]
		gen_log.info("Reduced by existing annotations remain: %s", len(sections))
		#add new coloum with label 'None'
		sections['Label'] = 'greygoo'

	#create new dataframe that contains all sections with sectionID < sectionID of last manual annotation
	manual_annotations = df[df['Manual'] == 0]
	sectionID_last_manual_annotation = max(manual_annotations['SectionLink'])
	artificial_negatives = sections[sections['SectionLink'] < sectionID_last_manual_annotation].copy()
	gen_log.info("From [%s] sections, selected [%s] with sectionID lower than last manual annoation", len(sections), len(artificial_negatives))
	artificial_negatives['Manual'] = 1

# - sample a random set of spys (S) from the labeled (positive) set so that |S| = delta * |positives|; delta = 0.1. Remove spies from positive set. Train_test_split via scikit learn
	try:
		X_train, X_spies, y_train, y_spies = train_test_split(df['Feature'], df['Label'], test_size = 0.1)
	except ValueError:
		gen_log.info("Sample size to low to train model. Please try again later!")
		return False
	gen_log.info("Recruited [%s] spies", len(X_spies))
	gen_log.info("Positive set had [%s] before the spies left", len(df))
	gen_log.info("Now [%s] elements remain", len(X_train))

# - add 'artificial negatives' (= Sections that we assume were skipped by the coder and as such are not relevant) to the training set, after splitting was done (we want to test "real" spies, not artificial spies)
	try:
		AFX_train, AFX_spies, AFy_train, AFy_spies = train_test_split(artificial_negatives['Feature'], artificial_negatives['Label'], test_size = 0.1)
	except ValueError:
		gen_log.info("Sample size to low to add negatives and train model. Please try again later!")
		return False
	X_train = pd.concat([X_train, AFX_train])
	y_train = pd.concat([y_train, AFy_train])
	gen_log.info("Added [%s] artificial 'greygoo' sections to make the classifier smarter, training with [%s] examples now", len(AFX_train), len(X_train))

# - train a classifier using the SGD fitting a logistic regression classifier
	#get language of sample
	newSample = resultsTupleList[0][0]
	getLanguage = codeRuleUtility.getLanguage(documentID, newSample)
	stopwords_dynamic = list(stop_en) if getLanguage == 'en' else list(stop_de)
	#prepare model pipline with TfidfVectorizer and SGDClassifier
	model = Pipeline([
				('tfidf', TfidfVectorizer(
					sublinear_tf=True,
					min_df=2,
					norm='l2',
					encoding='latin-1',
					ngram_range=(1, 2),
					stop_words=stopwords_dynamic)
				),
				('clf', SGDClassifier(
					loss='log',
					class_weight="balanced",
					penalty="elasticnet"
					)
				),
			])
	#fit the model
	model.fit(X_train, y_train)

# - calculate threshold as cutoff for "likely unknowns" -> t = min probability with which a spy was assigned with the correct label
	proba_correct_spies = []
	# create list of labels where labels were correctly predicted in spies
	list_confident_labels = []
	list_unconfident_labels = []

	#access accuracy using classification report for all spies
	gen_log.info("> Classification report: original labels")
	y_pred = model.predict(X_spies)
	gen_log.info(metrics.classification_report(y_spies, y_pred))
	#access accuracy using classification report for greygoo labels
	gen_log.info("> Classification report: greygoo labels")
	AFy_pred = model.predict(AFX_spies)
	gen_log.info(metrics.classification_report(AFy_spies, AFy_pred))
	#overall classification_report
	gen_log.info("> Classification report: total labels")
	merge_pred = model.predict(pd.concat([X_spies, AFX_spies]))
	gen_log.info(metrics.classification_report(pd.concat([y_spies, AFy_spies]), merge_pred))
	stats_log.info("%s-NEW-MODEL-F1-%s", documentID, metrics.f1_score(pd.concat([y_spies, AFy_spies]), merge_pred, average='weighted'))
	#create list of used labels to get the ordering that the classifier used
	labels_list = model.classes_.tolist()
	gen_log.info(labels_list)
	#check the predictions for all spies (where label isnt 'default')
	for index, row in X_spies.iteritems():
		proba_pred = model.predict_proba([row])[0]
		label_pred = model.predict([row])[0]

		# add labels for which spies were correctly predicted to list
		if y_spies[index] == label_pred:
			# get prediction proba of correct label for spies. Control for default label
			if y_spies[index] != 'default':
				index_correct_label = labels_list.index(y_spies[index])
				proba_correct_spies.append(proba_pred[index_correct_label])
			else:
				continue
			#append label to list of correct labels	
			list_confident_labels.append(label_pred)
		# it prediction was wrong, add prediction that was made to list of unconfident predictions -> to prevent recall optimization on cost of precision
		else:
			list_unconfident_labels.append(label_pred) 

	#End here if no spy was predicted correctly
	if proba_correct_spies == []:
		#in that case, remove all ML predictions, as confidence is too low
		deletionDict = {}
		for label in labels_list:
			deletionDict[label] = {
						'IDList': [],
						'probaList': [],
						'criticalWords': []
					}
			updateRecommendationsTable(documentID, deletionDict[label], label)
			gen_log.info(">> Failed to predict anything: Cleaning up and deleting existing ML suggestions")
		return True
	# defined cutoff based on prediction of spy proba: t = min(proba of correct label prediction)
	spy_cutoff = min(proba_correct_spies)
	list_confident_labels = np.unique(list_confident_labels).ravel()
	list_unconfident_labels = np.unique(list_unconfident_labels).ravel()
	#compare the two lists to only return labels that have been predicted correctly 100% of the time
	list_perfect_predictions = [l for l in list_confident_labels if l not in list_unconfident_labels]
	gen_log.info("We have a winner for the minimum probability for a correct label amongst spies: [%s]", spy_cutoff)
	gen_log.info("Spies were correctly predicted for %s", list_perfect_predictions)

# - define those predictions that are below the threshold as "likely unknowns"
	list_above_threshold = []
	list_below_threshold = []
	predictions_above = []
	predictions_below = []
	# dict to hold 'allowed' suggestions; contains branches of labels with the sectionIDs for which this label is suggested
	recommendationsDict = {}
	number_of_allowed_suggestions = 0 

	t0 = time()
	for index, row in sections.iterrows():
		proba_pred = model.predict_proba([row['Feature']])[0]
		label_pred = model.predict([row['Feature']])[0]

		if max(proba_pred) < spy_cutoff:
			list_below_threshold.append(row['SectionLink'])
			predictions_below.append(label_pred)
		else:
			list_above_threshold.append(row['SectionLink'])
			predictions_above.append(label_pred)
			#prepare prediction for updateEngine, only make suggestions for prediction != greygoo and contained in list_perfect_predictions
			if label_pred != 'greygoo' and label_pred in list_perfect_predictions:
				#add these predictions to dict recommendationsDict to trigger recommendationsUpdate
				if label_pred not in recommendationsDict:
					#either build the branch when not existing yet or add to list of sectionIDs
					recommendationsDict[label_pred] = {
						'IDList': [],
						'probaList': [],
						'criticalWords': []
					}
				recommendationsDict[label_pred]['IDList'].append(row['SectionLink'])
				recommendationsDict[label_pred]['probaList'].append(max(proba_pred))
				number_of_allowed_suggestions = number_of_allowed_suggestions + 1
				#add explanations for ID, as a list of lists
				criticalWordsForID = explainModelPrediction(model, row['Feature'], label_pred, 1)
				recommendationsDict[label_pred]['criticalWords'].append(criticalWordsForID)
				print("Finished preparing explanations for suggestion [%s] in: %s s", label_pred, round(time()-t0, 3))

	#gen_log.info a classification report
	gen_log.info("Finished calculating suggestions and explanations in %s s", round(time()-t0, 3))
	gen_log.info("When extending predictions to all unlabeled sections, [%s] documents were belove the threshold, while [%s] exceeded the threshold.", len(list_below_threshold), len(list_above_threshold))
	gen_log.info("Predicted the following labels x times ABOVE threshold")
	for x in labels_list:
		gen_log.info("%s : %s", x, predictions_above.count(x))
	gen_log.info("Predicted the following labels x times BELOW threshold")
	for x in labels_list:
		gen_log.info("%s : %s", x, predictions_below.count(x))

	gen_log.info(">>> Submitting a total of [%s] suggestions for [%s] labels!", number_of_allowed_suggestions, len(recommendationsDict))

# - for predictions that are above threshold (D \ U): submit those suggestions to update Engine that are made for labels in list_perfect_predictions
	#update recommendations table accordingly by looping over key in recommendationsDict and ordering an recommendations table update
	for key in recommendationsDict:
		#trigger recommendations table update
		updateRecommendationsTable(documentID, recommendationsDict[key], key)

	return True


#concept based on Martens & Provost 2014
def explainModelPrediction(MLmodel, feature, predLabel, iteration):
	#input: trained MLmodel, feature (sentence) for which to provide an explanation, predLabel that was predicted for entire sentence
	listOfCriticalWords = []
	
	#if listOfCriticalWords is empty after one iteration, start again and compare more words (as long as lengthOfCombinations < number of words in feature)

	# - make list of all words in feature and remove stopwords to save operations
	feature_tokens = feature.split()
	#remove stopwords
	tokens_without_sw = [word for word in feature_tokens if not word in stop_de]

	lengthOfCombinations = iteration
	tempPrediction = None

	#limit to 3 word combinations max
	if lengthOfCombinations < 3:

		# - based on lengthOfCombinations, make object including all possible combinations
		combinationsToTest = itertools.combinations(tokens_without_sw, lengthOfCombinations)

		# - for every item in list, check if deleting these from feature results in prediction change
		for combination in combinationsToTest:
			feature_without_combination = [word for word in tokens_without_sw if not word in combination]
			toSentence = " ".join(feature_without_combination)
			tempPrediction = MLmodel.predict([toSentence])[0]
			# - if yes, save this combination in additional list
			combination_to_words = ""
			#gen_log.info("Iteration: ", iteration, " and predicted label for [", toSentence, "] is ", predLabel)
			if tempPrediction != predLabel:
				for word in combination:
					combination_to_words = combination_to_words + "+" + word if combination_to_words != "" else word
				listOfCriticalWords.append(combination_to_words)

		# - if list of criticalwords is still empty, repeat with lengthOfCombinations++
		if listOfCriticalWords == []:
			return explainModelPrediction(MLmodel, feature, predLabel, lengthOfCombinations + 1)

		#return: list of words that are relevant for the classification
		else:
			return listOfCriticalWords

	else:
		return ['no critical words found']


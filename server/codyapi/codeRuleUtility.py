import os, os.path, traceback

from whoosh.fields import Schema, TEXT, STORED
from whoosh import index
from whoosh.qparser import QueryParser
from whoosh.analysis import LanguageAnalyzer, StandardAnalyzer
from whoosh.support import levenshtein

import spacy
from spacy_cld import LanguageDetector

from .models import db

import warnings
import logging

gen_log = logging.getLogger('general')
stats_log = logging.getLogger('stats')


#on new document upload | build searchable schema, index, and add documents
def setup(documentID, sectionDictionary):
	#build the schema
	#get language for LanguageAnalyzer Setup - list(dict.keys) returns first element in dictionary sectionDictionary
	language = getLanguage(documentID, sectionDictionary)
	gen_log.info("// Language of document is [%s]", language)
	#schema = Schema(content = TEXT(stored = True, analyzer = LanguageAnalyzer(language)), ID = STORED)
	schema = Schema(content = TEXT(stored = True, analyzer = StandardAnalyzer(stoplist = None)), ID = STORED)

	#build the index
	if not os.path.exists("indexdir"):
		os.mkdir("indexdir")

	#create folder for document
	foldername = "document_" + str(documentID)
	if not os.path.exists(os.path.join("indexdir", foldername)):
		os.mkdir(os.path.join("indexdir", foldername))

	gen_log.info("// Start building index for new doc: %s", str(documentID))
	ix = index.create_in(os.path.join("indexdir", foldername), schema = schema, indexname = "index-doc" + str(documentID))

	#next, we can add documents to the index
	writer = ix.writer()

	for doc in sectionDictionary:
		ident = sectionDictionary[doc]['id']
		cont = sectionDictionary[doc]['section']
		writer.add_document(content = cont, ID = ident)

	writer.commit()
	gen_log.info("// Index complete")

#perform a search on an index | return list of IDs that match the query including score for each ID
def search(documentID, query, limit):
	#open search index
	foldername = "document_" + str(documentID)
	ix = index.open_dir("indexdir/" + foldername, indexname = "index-doc" + str(documentID))

	qp = QueryParser("content", schema = ix.schema)
	q = qp.parse(query)
	gen_log.info("// Query parsed into")
	gen_log.info(q)

	IDList = []
	highlightsList = []

	with ix.searcher() as searcher:
		results = searcher.search(q, limit = limit)
		for r in results:
			IDList.append(r["ID"])
			highlightsList.append(r.highlights("content"))

	resultDict = {
		"IDList": IDList,
		"highlightsList": highlightsList,
	}
	return resultDict


#get language of current document based on example
def getLanguage(documentID, sectionDict):
	#get example sentence on document creation
	longest_example = ""
	
	if type(sectionDict) == dict:
		for doc in sectionDict:
			cont = sectionDict[doc]['section']
			if len(cont) > len(longest_example):
				longest_example = cont

	#could rework this entire section so that language gets do not have to transmit a section any more / or make use of section as fallback
	try:
		call = db.session.execute(
					"SELECT language FROM documents WHERE id = :id",
					{"id": documentID})

		#handle fetchone only once
		fetcher = call.fetchone()
		db.session.commit()

		if fetcher == None:
			language = fetcher
		else:
			language = fetcher[0]

		if language == None:

			nlp = spacy.load('de_core_news_sm')

			try:
				nlp.add_pipe(LanguageDetector())
			except ValueError:
				gen_log.info("Language extension already added")

			tokens = nlp(longest_example)

			db.session.execute(
						"UPDATE documents SET language = :lang WHERE id = :id",
						{"lang": tokens._.languages[0], "id": documentID})
			db.session.commit()

			return tokens._.languages[0]

		else:
			return language
	except:
		gen_log.info("Error with accessing db to retrieve language for documentID %s in getLanguage() in codeRuleUtility.py", documentID)
		gen_log.info("Unexpected error: %s", traceback.format_exc())

#create code rule suggestion using whoosh keywords with levenshtein distance and spancy similarity scores based on small model for relevant language
def codeRuleSuggestion(documentID, label, section):
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		#select the correct dictionary according to language
		language = getLanguage(documentID, section)
		if language == 'de':
			nlp = spacy.load('de_core_news_sm')
		else:
			nlp = spacy.load('en_core_web_sm')

		unprocessedSection = nlp(section)
		#preprocessing of section | remove tokens that are stop words, whitespace or punctuation
		processedSection = [token.text for token in unprocessedSection if not token.is_stop if not token.is_space if not token.is_punct]
		#process processed string with NLP
		tokensSection = nlp(' '.join(processedSection))
		tokensLabel = nlp(label)

		ruleSuggestion = ""

		#configuration for cutoffs
		levCutoff = .3 #cutoff for levenshtein distance
		simCutoff = .45 #cutoff for similarity score

		#iterate over all tokens in label and section for levenshtein suggestions
		for tL in tokensLabel:
			for tS in tokensSection:
				#calculate levenshtein distance
				lev = levenshtein.relative(tL.lemma_, tS.lemma_)
				if lev > levCutoff:
					#add new term only if isnt included already
					nextWordIncluded = (tL.lemma_ + "*").lower() in ruleSuggestion
					if nextWordIncluded == False:
						if ruleSuggestion != "":
							ruleSuggestion = ruleSuggestion + " AND "
						#add new term
						ruleSuggestion = ruleSuggestion + "{}*".format(tL.lemma_.lower())

		#formating placeholder
		preventNextOR = True
		startBracketAdded = False

		#iterate over all tokens in label and section for similarity suggestions
		for tL in tokensLabel:
			for tS in tokensSection:
				#calculate similarity distance
				sim = tL.similarity(tS)
				#add new term only if isnt included already
				nextWordIncluded = (tS.lemma_ + "*").lower() in ruleSuggestion

				if sim > simCutoff and nextWordIncluded == False:
					#begin first entry with a bracket and calculate if AND is necessary
					if startBracketAdded == False:
						#combine levenshtein and similarity suggestions as: LEV AND (Sim1 OR Sim2 …), if LEV suggestions != empty
						if(ruleSuggestion != ""):
							ruleSuggestion = ruleSuggestion + " AND ("
						else:
							ruleSuggestion = "("
						startBracketAdded = True

					if preventNextOR == False:
						ruleSuggestion = ruleSuggestion + " OR "
					else:
						preventNextOR = False
		
					ruleSuggestion = ruleSuggestion + (tS.lemma_).lower() + "*"

		#close brackets
		if startBracketAdded == True:
			ruleSuggestion = ruleSuggestion + ")"
		
		return ruleSuggestion



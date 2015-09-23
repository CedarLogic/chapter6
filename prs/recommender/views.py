from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse
from django.http import HttpResponse

from itertools import combinations

import json

def hello(request):
	return HttpResponse('Hello')

def chart(request):
	cursor = connection.cursor()
	cursor.execute('SELECT \
						content_id,\
						mov.title,\
						count(*) as sold\
					FROM    public."evidenceCollector_log" log\
					JOIN    public.movies mov ON CAST(log.content_id AS INTEGER) = CAST(mov.id AS INTEGER)\
					WHERE 	event like \'buy\' \
					GROUP BY content_id, mov.title \
					ORDER BY sold desc \
					LIMIT 10')

	data = dictfetchall(cursor)
	return JsonResponse(data, safe=False)

def item_support(request):
	minsupport = 0.01
	data = get_items(minsupport)	
	return JsonResponse(data, safe=False)

def itemsets_support(request):
	data = get_itemsets()
	return JsonResponse(data, safe=False)

def dictfetchall(cursor):
	"Returns all rows from a cursor as a dict"
	desc = cursor.description
	return [
		dict(zip([col[0] for col in desc], row))
		for row in cursor.fetchall()
		]


def get_items(minsupport):
	cursor = connection.cursor()

	cursor.execute('select itemsets.* \
	FROM (	\
		SELECT \
			content_id,  \
			count("sessionId") as count, \
			count("sessionId")::float / (select count(distinct "sessionId") from "evidenceCollector_log" where event = \'buy\') as support \
		FROM 	"evidenceCollector_log"  \
		WHERE 	event = \'buy\' \
		GROUP BY content_id\
		order by count desc) itemsets \
		WHERE itemsets.support > ' + repr(minsupport))
	data = dictfetchall(cursor)
	return data

def get_itemsets():
	cursor = connection.cursor()

	cursor.execute ('\
		SELECT e1.content_id as source,\
			   e2.content_id as target, \
			   count(e2."sessionId") as freq, \
			   count(e2."sessionId")::float / (select count(distinct "sessionId") from "evidenceCollector_log" where event = \'buy\') as support \
		FROM  "evidenceCollector_log" e1 \
		INNER JOIN \
			(SELECT evidence.content_id, \
					evidence."sessionId", \
					session_count \
 			FROM 	"evidenceCollector_log" evidence \
 			INNER JOIN \
	 		 (SELECT "sessionId", \
	 			 	 count("content_id") as session_count \
			  FROM 	"evidenceCollector_log" \
			  WHERE 	event = \'buy\' \
			  GROUP BY "sessionId") as sessions \
			ON evidence."sessionId" = sessions."sessionId"\
			WHERE   sessions.session_count > 1 \
				    and event = \'buy\') as e2\
		ON e1."sessionId" = e2."sessionId"\
		WHERE e1.event = \'buy\' \
		      and e1.content_id != e2.content_id \
		GROUP BY e1.content_id, e2.content_id\
		order by freq desc, source;\
		')
	data = dictfetchall(cursor)
	return data


def calculate_support_confidence(transactions, min_sup = 0.01):

	N = len(transactions)	
	
	one_itemsets = dict()
	two_itemsets = dict()
	
	one_itemsets = calculate_itemsets_one(transactions, min_sup)    
	two_itemsets = calculate_itemsets_two(transactions, one_itemsets, min_sup)	

	rules = calculate_association_rules(one_itemsets, two_itemsets, N)

	return sorted(rules)

def calculate_association_rules(one_itemsets, two_itemsets, N):

	rules = []
	for source, source_freq in one_itemsets.items():
		for key, group_freq in two_itemsets.items():
			if (source.issubset(key)):
				target = key.difference(source)
				support = group_freq/N
				confidence = group_freq/source_freq
				rules.append((next(iter(source)), next(iter(target)), confidence, support))


	return rules

def calculate_itemsets_two(transactions, one_itemsets, min_sup = 0.01):
	N = len(transactions)
	two_itemsets = dict()

	for key, items in transactions.items():
		if (len(items) > 2):
			for perm in combinations(items, 2):
				if frozenset(perm) not in two_itemsets: 
					if hasSupport(perm, one_itemsets):
						two_itemsets[frozenset(perm)] = 1
				else: 
					two_itemsets[frozenset(perm)] += 1
		elif len(items) == 2:
			if frozenset(items) not in two_itemsets: 
				if hasSupport(items, one_itemsets):
						two_itemsets[frozenset(items)] = 1
			else:
				two_itemsets[frozenset(items)] += 1
				 
	return two_itemsets

def hasSupport(perm, one_itemsets):
	return frozenset({perm[0]}) in one_itemsets and \
		   frozenset({perm[1]}) in one_itemsets

def calculate_itemsets_one(transactions, min_sup = 0.01):
	N = len(transactions)
	temp = dict()
	one_itemsets = dict()

	for key, items in transactions.items():
		for item in items:
			print (item)
			inx = frozenset({item})
			if inx not in temp: 
				temp[inx] = 1
			else: 
				temp[inx] += 1

	# remove all items that is not supported.	
	for key,itemset in temp.items():
		if itemset > min_sup * N:
			one_itemsets[key] = itemset

	return one_itemsets

def get_all_transactions(request):
	#data = retrieve_transactions()
	#data = generate_transactions(data)
	
	
	data = dict()
	data = {'1': ['bread', 'yogurt'], \
		    '2': ['milk', 'bread', 'carrots'], \
		    '3': ['bread', 'carrots'], \
		    '4': ['milk', 'bread'], \
		    '5': ['milk', 'dates', 'carrots'], \
		    '6': ['milk', 'dates', 'yogurt', 'bread']}
	data = calculate_support_confidence(data, 0.4)
	return JsonResponse(data, safe=False)

def generate_transactions(data):
	transactions = dict()
	
	for transaction_item in data:
		transaction_id = transaction_item["sessionId"]
		if transaction_id not in transactions:
			transactions[transaction_id] = []
		transactions[transaction_id].append(transaction_item["content_id"])

	return transactions

def retrieve_transactions():
	cursor = connection.cursor()

	cursor.execute(\
		'SELECT * \
		 FROM "evidenceCollector_log" \
		 WHERE event = \'buy\' \
		 ORDER BY "sessionId", content_id'\
		)

	data = dictfetchall(cursor)
	return data


import urllib2
import json
import nltk
import re
from nltk.corpus import stopwords
import csv
from collections import defaultdict


def getCommonWords(data):
	regex = re.compile('[^a-zA-Z0-9 ]')
	other_stop_words = ['ive', '']

	all_words = []
	bigrams = []
	# trigrams = []
	for r in data:
		text = ""
		# cause some something stupid.
		if 'href' in r['text']:
			text = r['text']['text'].encode('utf-8')
		else:
			text = r['text'].encode('utf-8')
			
		text = regex.sub('', text).rstrip().lower()
		words = text.split(' ')

		# for word in words:
		# 	# don't add stop words
		# 	if (word not in	stopwords.words('english') and word not in other_stop_words):
		# 		all_words.append(word)

		bi = nltk.bigrams(words)
		for b in bi:
			# don't add bigram with stop words
			if b[0] not in stopwords.words('english') and b[0] not in other_stop_words:
				if b[1] not in stopwords.words('english') and b[1] not in other_stop_words:
					bigrams.append(b)

		# trigrams.extend(nltk.trigrams(words))

	# fdist = nltk.FreqDist(all_words)
	fdistbi = nltk.FreqDist(bigrams)
	# fdisttri = nltk.FreqDist(trigrams)

	# print words

	# print "most commmon:"
	# print fdist.most_common(20)

	return fdistbi.most_common(20)
	# print "trigrams:"
	# print fdisttri.most_common(50)

	# fdist.plot(50, cumulative=False)
	# fdistbi.plot(50, cumulative=False)


def getRestaurants():   
	offset = 0    
	all_items = []

	# there's a limit of 2500 per page. To get all data, offset by 2500
	while True:
		url = "https://www.kimonolabs.com/api/3ml5tw30?apikey=6r5gMHTWiXWVI3d1Ej3NdYJvj59rzKD6&kimbypage=true&kimoffset=%d" % offset
		results = json.load(urllib2.urlopen(url))

		print "url:",url
		if results['results']:
			# print "current length of all_items ", len(all_items)
			offset += 2500
			all_items.extend(results['results'])
		else:
			break 
	# print "end loop"

	return all_items



####################################################
#################### MAIN ##########################

restaurants = getRestaurants()

counter = defaultdict(list)
i = 0
for r in restaurants:

	try:
		freq_words = getCommonWords(r['Review'])

		# print r['url']
		# print freq_words
		restaurant_id = r['url'].rsplit('/',1)[1]
		restaurant_rating = float(r['Restaurant'][0]['restaurant_rating'].encode('utf-8').split(' ')[0])

		for bigram in freq_words:
			words = bigram[0][0] + '_' + bigram[0][1]
			if words not in counter:
				counter[words] = []
			counter[words].append({'id': restaurant_id, 'count': bigram[1], 'rating': restaurant_rating})
				
		# print "-----"
	except:
		print "###### ERROR:", r['url'].rsplit('/',1)[1]
	
	print i
	i += 1

mostCommonBigrams = []
for k,v in counter.iteritems():
	if len(v) >= 5:
		mostCommonBigrams.append({'term': k, 'restaurants': v})

with open("mostCommonBigrams.json", "w") as outfile:
  json.dump(mostCommonBigrams, outfile, indent=4)
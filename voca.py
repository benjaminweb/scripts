# Run via voc_add.py "put your expression here"
# http://www.xsteve.at/prg/python/

# XPath http://doc.scrapy.org/en/0.7/topics/selectors.html
# inspired by http://extract-web-data.com/python-lxml-scrape-online-dictionary/
# 2013-08-11
#!/bin/env python3
import lxml.html, os, sys, itertools, urllib.request
from collections import defaultdict

### CONFIG BEGIN ###
# Maximum words to consider
max = 10
#
# Output File --> Pflege append ein! @TODO 
file = "/Users/benjaminweb/vocs/INBOX2.txt"
#
# Schema to write to file --> embed @TODO
delim = "=" # separates two languages
sep = "," # separates multiple meanings
#
# result list
result = [] 
#
# input word
#word = ' '.join(sys.argv[1:])
#word = word.strip('\"')
#word = word.strip()
#
sources = []
#
#for i in sys.argv[1:]:
#	word = 
#
#for i in arg: word = ' '.join(arg)
#word.strip("\"")
#
### CONFIG END ###
#
### HELPING FUNCTIONS BEGIN ###
#
# collect all words to translate
def collect(): # 2013-08-31 works
	f = open(file, 'r') # w truncates the file!
	targets = []
	for line in f.readlines():
		if not " = " in line:
			targets.append(str(line.replace('\n','').strip()))
			# check whether target is valid! @TODO 2013-08-31
	f.close()
	return targets
	
# remove duplicates
def clean(L):
	seen = set()
	for item in L:
		item = item.rstrip()
		item = item.replace('[ ]', '')
		item = ' '.join(item.split())
		seen.add(item)
	return sorted(seen)

# clean duplicates in translations
def deldups(dups):
	q = ""
	for i in dups.split(','):
		if i not in q:
			q += ",%s" % i
	q = q.lstrip(",")
	return q

def load_existing(word):
	existing = []
	exists = 0
	f = open(file, 'r') # w truncates the file!	
	for line in f:
		if "%s = " % word in line:
			exists = 1
			break
	if exists:
		existing = (line.split(" = ")[1].replace("\n","")).split(",")
	return existing

def clean_selection(selection):
	out = []
	for i in selection:
		if not i == '':
			out.append(i)
	return out 

### HELPING FUNCTIONS END ###
#
### MAIN FUNCTIONS BEGIN ###
#
# merge & sort entries in existing file; truncate file; write file completely new, entry by entry
def merge():
	f = open(file, 'r+') # w truncates the file!
	v = []
	g = []
	q = ""
	on_file = defaultdict(list)
	for line in f.readlines():
		v.append(line.replace('\n','').rstrip(",").split(' = '))
	f.close()
	for word, trans in v:
		on_file[word].append(trans)
	# missing ending comma for each line causes duplicates in selection --> Screenshots
	result = [(key, ",".join(value)) for key, value in on_file.items()]
	for i, j in result:
		# build entry
		g.append("%s = %s" % (i, deldups(j))) # remove any duplicate translation
	text = "\n".join(g)
	with open(file, "w") as myfile:
		myfile.write(text)

def build_entry(selection, word): # schema: word = trans1,trans2,trans3
	selection = sep.join(selection)
	entry = "%s %s %s" %(word, delim, selection)
	#entry = "\n" + entry.rstrip(',') + "\n"
	return entry

def remove(expression):
	list = []
	for i in f.readlines():
		if not expression in i:
			list.append(i.replace("\n",""))
	return list

def write(text):
	f = open(file, 'w') # truncates file!
	for element in text:
		f.write("%s\n" % element)
	f.close() # close file, required!

def save(word, entry=None):
	# open file in read mode
	f = open(file, 'r') # w truncates the file!	
	text = []
	text = remove("%s =" % word)
	# add new entry
	if entry:
		text.append(entry)
	# sort elements of file
	text.sort() # still working?
	# write text elements to file
	write(text)	
	
# voc1 = linguee():
def linguee(word): # 2013-08-11 works
	try:
		response = []
		# make request & get raw data
		doc = lxml.html.parse("http://www.linguee.de/deutsch-englisch/search?source=auto&query=%s" % word)
		# delete inexact entries & examples
		for elem in doc.xpath("//div[@class='inexact']"): elem.getparent().remove(elem)
		# provide response to list
		response = doc.xpath("//a[@class='smalldictentry']/text()")
		response = [x for x in response if len(x)>0]
		response = response[:max] # cut to max elements
		return response
	except OSError:
		input("IP blocked by linguee.de. [ENTER] ")
	#IOError:	

# voc2 = dictcc(word)
def dictcc(word): # 2013-08-11 works, 
	response = []
	doc = lxml.html.parse("http://www.dict.cc/?s=%s" % word)
	for i in range(1, max): response.append(' '.join(doc.xpath("//*[@id='tr%d']/td[3]/a/text()" % i)))
	return response		

# voc3 = leo(word)	
def leo(word): # 2013-08-26 wrong encoding provisioning of site fixed, 
	response = []
	url = ("http://pda.leo.org/?search=%s" % word)
	content = urllib.request.urlopen(url).read()
	# override wrong encoding information the site provides
	parser = lxml.html.HTMLParser(encoding='utf-8')
	doc = lxml.html.fromstring(content, parser=parser, base_url=url)
	lim = max+4
	for i in range(4, lim): response.append(' '.join(doc.xpath("//tr[%d]/td[2]/text()" % i)))
	response = [x for x in response if len(x)>0]
	return response

# look up 1 to 3 & merge them

translators = {
    'linguee.de': linguee,
    'dict.cc': dictcc,
#    'dict.leo.org': leo
}

def translate(word):
#	try:
	inputs = []
	for source, func in translators.items():
		translation = func(word)
		if translation:
			sources.append(source)
			inputs.append(translation)
	# build one big list out of three: ['A', 'B', 'C'] ['D', 'E', 'F'] ['G', 'H', 'I', 'J', 'K'] -> ['A', 'D', 'G', 'B', 'E', 'H', 'C', 'F', 'I', 'J', 'K']
	result = [_f for _f in itertools.chain(*itertools.zip_longest(*inputs)) if _f]
	result.sort()
#	except urllib.error.URLError or OSError:
#		input("Check your internet connectivity.\n~ ")
	return clean(result)
	
#http://www.cyberciti.biz/faq/python-raw_input-examples/
def main(result, word): # 2013-08-12 works
	selection = []
	is_valid = 0
	existing = load_existing(word)
	selection = existing
	remaining = list(set(result).difference(selection))
	#merge()
	while not is_valid:
		#selection = clean_selection(selection)
		tcount = len(result)
		scount = len(set(selection).intersection(result))
		mcount = len(selection)-scount # count of manual
		# which elements of selection are part of result? (does *not* contain manual entries)
		#selection = list(set(selection).intersection(result))
		#print "RESULT"
		#for index, item in enumerate(result, start=1):
		#	print index, item
		os.system("clear") # add for Windows os.system("cls") here
		print (60 * '=')
		print ("Translation Builder - Usage:\t./voc_add.py \'your expression\'")
		print (60 * '=')
		print
		print (60 * '-')
		print ("%s available translations for \"%s\"" % (len(result), word))#, lambda sources: ', '.join(sources)))
		print (60 * '-')
		# order list
		remaining.sort()
		# kill duplicates
		list(set(remaining))
		for index, item in enumerate(remaining, start=1):
			print ("[%s]	%s " %(result.index(item)+1, item))
		print
		print (60 * '-')
		selection.sort()
		if not selection:
			print ("Your selection is empty.")
		else:
			if mcount == 0:
				print ("%s/%s of available selected:" % (scount, tcount))
			elif mcount == 1:
				print ("%s/%s of available + %s manual entry selected:" % (scount, tcount, mcount))
			else:
				print ("%s/%s of available + %s manual entries selected:" % (scount, tcount, mcount))
		print (60 * '-')# if selection is empty drop lines! @TODO
		print
		for index, item in enumerate(selection, start=1):
			if item in result:
				print ("[%s]\t%s " %(result.index(item)+1, item))
			else:
				print ("\t%s" % item)
		print (60 * '-')
		print ("Function\t\tInput")
		print (60 * '-')
		print ("[1-%d]\tAdd & Remove translation" % tcount)
		print ("word\tAdd & Remove \"word\"")
		print ("[D]\tDelete selection")
		print ("[ENTER]\tSave & Next")
		print ("[S]\tSkip")
		print ("[Q]\tQuit")
		print (60 * '-')
		print
		choice = input("~ ")
		if choice == "":
			is_valid = 1
		# if choice is integer
		try:
			# add result(choice) to selection if not there!
			if result[int(choice)-1] in selection:
				selection.remove(result[int(choice)-1])
			# remove result(choice) if in selection!
			else:
				selection.append(result[int(choice)-1])
		# if choice is manual	
		except ValueError:
			# clean(choice)
			choice = choice.strip()
			# add manual choice 
			if choice not in selection:
				selection.append(choice)
			# remove manual choice
			elif choice in selection:
				selection.remove(choice)
		except IndexError:
			input("Not available.\n~ ")
		if choice == "D" or choice == "d":
			selection = []
		elif choice == "Q" or choice == "q":
			quit()
		elif choice == "S" or choice == "s":
			is_valid = 1 # out of loop
		# remove empty elements in selection
		if selection:
			selection = clean_selection(selection)
		remaining = list(set(result).difference(selection))
		#print("SELECTION %s" % len(selection)) ##DEBUG
		#print(repr(selection)) ##DEBUG
	if not selection: # work 2013-08-29
		save(None)
	elif not choice == "S" and not choice == "s":
		entry = build_entry(selection, word)
		save(word, entry)		
	return
### MAIN FUNCTIONS END ###

#def count():



# 2 modi:
#1. valid file path provided: open file and translate to_translate
#2. no valid file path, suggest provided arg is word, translate it
#3. no arg, no valid arg -> error message
# design function call for 2 modi @TODO 2013-08-29

# modi 1
# open input file
f = open(file, 'r') # w truncates the file!
targets = ""

# collect all words not translated yet


targets = collect()

for target in targets:
	translations = translate(target)
	main(translations, target)
	if len(targets) > 1:
		targets.remove(target)
	elif len(targets) == 1:
		break
	

		# if translation of target present, delete originating target entry 
#	if "%s = " % target in line:
#		f = open(file, 'r') # w truncates the file!	
#		text = []
#		text = remove("%s =" % target)
#		write(text)
	
#if selection:
#	drop_entry("%s = \n" % to_translate)	

# modi 2
#translations=translate(word)
#main(translations)

#for line in f.readlines():
#		v.append(line.replace('\n','').rstrip(",").split(' = '))
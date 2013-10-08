# Run via voc_add.py "put your expression here"
# http://www.xsteve.at/prg/python/

# XPath http://doc.scrapy.org/en/0.7/topics/selectors.html
# inspired by http://extract-web-data.com/python-lxml-scrape-online-dictionary/
# 2013-08-11
#!/bin/env python3
import lxml.html, os, sys, itertools, urllib.request
from collections import defaultdict
#
### CONFIG BEGIN ###
# Maximum words to consider
max = 10
#
# Output File --> Pflege append ein! @TODO 
infile = "/Users/benjaminweb/vocs/mth_in.txt"
outfile = "/Users/benjaminweb/vocs/mth_out.txt"
manual = "/Users/benjaminweb/vocs/mth_man.txt"
#
# Schema to write to file --> embed @TODO
delim = "=" # separates two languages
sep = "," # separates multiple meanings
#
targets = []
#
# result list
result = []
voc_count = 0
translated_count = 0
#
choice = ""
# input word
#word = ' '.join(sys.argv[1:])
#word = word.strip('\"')
#word = word.strip()
word = ""
#
sources = []
#
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
# collect all words to translate from infile
# @TODO 2013-10-03: BUG: Catch UnicodeEncodeError in load next word, e.g.: protégé
def collect(file): # 2013-08-31 works
	f = open(file, 'r') # w truncates the file!
	for line in f.readlines():
		if not " = " in line:
			targets.append(str(line.replace('\n','').strip()))
			# check whether target is valid! @TODO 2013-08-31
	f.close()
	return
#	
#	
#	
# remove duplicates
def clean(L):
	seen = set()
	for item in L:
		item = item.rstrip()
		item = item.replace('[ ]', '')
		item = ' '.join(item.split())
		seen.add(item)
	return sorted(seen)
#
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
	f = open(outfile, 'r') # w truncates the file!	
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
def merge(file):
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

def build_entry(word, selection): # schema: word = trans1,trans2,trans3
	selection = sep.join(selection)
	entry = "%s %s %s" %(word, delim, selection)
	#entry = "\n" + entry.rstrip(',') + "\n"
	return entry

#### clarify & abstract! 
#### with or without file open?
#### use in save(word) & remove word from infile @TODO 2013-09-01
#

## @WIP 2013-09-01
def remove(word, file):
	text = []
	f = open(file, "r")
	for i in f.readlines():
		if "%s" % word not in i:
			text.append(i.replace("\n",''))
	f.close()
	f = open(file, "w") # truncate file
	write(text, file)	
	
def write(text, file):
	text.sort()
	f = open(file, 'w') # truncates file!
	for element in text:
		f.write("%s\n" % element)
	f.close() # close file, required!

# write entry to outfile
def add(word, selection, file):
	f = open(file, "a")
	entry = build_entry(word, selection)
	f.write("%s\n" % entry) # word = trans1,trans2,trans3
	f.close()

#
#
#
# voc1 = linguee():
def linguee(word): # 2013-08-11 works
	try:
		response = []
		# make request & get raw data
		doc = lxml.html.parse("http://www.linguee.de/deutsch-englisch/search?source=auto&query=%s" % word)
		# delete inexact entries & examples
		#for elem in doc.xpath("//div[@class='inexact']"): elem.getparent().remove(elem)
		# provide response to list
		response = doc.xpath("//a[@class='smalldictentry']/text()")
		response = [x for x in response if len(x)>0]
		response = response[:max] # cut to max elements
		return response
	except OSError:
		print("IP blocked by linguee.de.")
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
	url = ("http://pda.leo.org/?search=%s" % word).replace(" ", "%20")
	content = urllib.request.urlopen(url).read()
	# override wrong encoding information the site provides
	parser = lxml.html.HTMLParser(encoding='utf-8')
	doc = lxml.html.fromstring(content, parser=parser, base_url=url)
	trs = doc.xpath("//tr")
	for tr in trs:
		th = tr.xpath("th/text()")
		td = ''.join(tr.xpath("td[2]/text()"))
		if 'Weitere Treffer' in th or 'More Results' in th:
			break
		empty = td == ''
		new_line = '\n' in td
		tab = '\t' in td
		if not empty and not new_line and not tab:
			response.append(td)
	#response = [x for x in response if len(x)>0]
	return response

# look up 1 to 3 & merge them
def translate(word):
	translators = {
#    	'linguee.de': linguee,
#	    'dict.cc': dictcc,
	    'dict.leo.org': leo
	}
#	try:
	inputs = []
	for source, func in translators.items():
		word = word.replace(' ', '+') # replace whitespace with '+'
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
#	
#	
#	
#	
#http://www.cyberciti.biz/faq/python-raw_input-examples/
def select(target, result): # 2013-08-12 works
#
	def skip(append=None):
		selection = None
		targets.remove(target)
		remove(target, infile)
		if append:
			f = open(infile, "a")
			f.write("%s\n" % target)
			f.close()

	selection = []
	is_valid = 0
	existing = load_existing(target)
	selection = existing
	remaining = list(set(result).difference(selection))
	voc_count = len(targets)
	#merge()
	while True:
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
		#### include here display of sourced used! @TODO 2013-09-01
		print ("{} available translations for \"{}\" [{}/{} = {:.0%}]".format(len(result), target, translated_count, voc_count, translated_count/voc_count))
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
		print ("[E]\tRename to base / infinitive")
		print ("[M]\tMove to manual edit file")
		print ("[R]\tRemove \"%s\" from input file" % target)
		print ("")
		print ("[ENTER]\tSave & Next (& Quit when input file empty.)")
		print ("[Q]\tQuit")
		print (60 * '-')
		print
		choice = input("~ ")
		# if [ENTER] = SAVE & NEXT is hit, interrupt loop
		#repr(choice) ## DEBUG
		if choice == "" and selection == []:
			skip(append=True)
			break
		elif choice == "": # works 2013-09-01
			break
		#
		### begin change selection ###
		# if choice is integer -> change selection
		try:
			# add result(choice) to selection if not there!
			if result[int(choice)-1] in selection:
				selection.remove(result[int(choice)-1])
			# remove result(choice) if in selection!
			else:
				selection.append(result[int(choice)-1])
		# if choice is not integer -> 	
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
		# truncate selection
		if choice == "D" or choice == "d":
			selection = []
		# quit
		elif choice == "Q" or choice == "q":
			quit()
		elif choice == "E" or choice == "e":
			renamed = input("Infinitive or base form of \"%s\": " % target)
			if renamed == target:
				break
			if renamed and not renamed == target:
				targets.remove(target)
				targets.insert(0, renamed)
				selection.remove(choice)
				remove(target, infile)
				break
		elif choice == "R" or choice == "r":
			targets.remove(target)
			remove(target, infile)
			selection = []
			break
		elif choice == "M" or choice == "m":
			f = open(manual, "a")
			f.write("%s\n" % target) # word = trans1,trans2,trans3
			f.close()
			selection = None
			skip(append=None)
			break
		# clean selection from empty elements: ''
		if selection:
			selection = clean_selection(selection)
		# what is available and has not been selected?
		remaining = list(set(result).difference(selection))
		#print("SELECTION %s" % len(selection)) ##DEBUG
		#print(repr(selection)) ##DEBUG
		### end change selection###
	return selection

def save(target, selection):
	if not choice == "S" and not choice == "s":
		if selection:
			# remove translated word from infile
			remove(target, infile)
			# remove translated word from outfile (= overwrite existing translations!)
			remove(target, outfile)
			# add word to outfile
			add(target, selection, outfile)
			if target in targets:
				targets.remove(target)
		elif not selection:
			remove(target, outfile)
			#### add it back to infile, even if never was present in infile? @TODO 2013-09-01

### MAIN FUNCTIONS END ###


# 2 modi:
#1. valid file path provided: open file and translate to_translate
#2. no valid file path, suggest provided arg is word, translate it
#3. no arg, no valid arg -> error message
# design function call for 2 modi @TODO 2013-08-29

#### BEGIN MAIN PROGRAM ####

# modi 1
# collect all words not translated yet
collect(infile)

while True:
	# 1. get stuff to translate, out: targets
	word = targets[0]
	# 2. get translations, build selection, out: selection
	translations = translate(word)
	selection = select(word, translations)
	# 3. write results to files
	save(word, selection) #### @WIP 2013-09-01
	translated_count += 1
	#yield 
	if not targets:
		print("Finished.")
		quit()



#### END MAIN PROGRAM ####


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


#def count():

# The MIT License (MIT)

# Copyright (c) 2013 Benjamin Weber
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the “Software”), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


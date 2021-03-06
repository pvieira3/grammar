import operator
import itertools
import random
import sys
import heapq
import distance
import scorer
import test
from nlputils import *


def printf(x):
    print x

def correct(text, between=False):
    sents = splitSentence(text)
    if between:
        sents = map(lambda s: list(intersperse(s, "")), sents)
    print len(sents),
    sys.stdout.flush()
    candSents = confusionSets(sents)
    print len(candSents),
    sys.stdout.flush()

    scoreEvaler = [-0.01,1,2,3,4,5]
    scoredgrams = []
    for n in xrange(1,6):
        print n,
        sys.stdout.flush()
        # create trigrams from candidate sentences
        grams = []
        cid = 0
        for (cs, sid) in candSents:
            cs = map(operator.itemgetter(1), cs)
            grams += gramify(n, cs, (sid, cid, n))
            cid += 1

        #run score function
        #scoredgrams = map(lambda (t0, t1, t2, ((sid, cid), wid)):
        #        (sid, cid, wid, t1, 1), trigrams)
        grams.sort()
        (sg, count, total) = scorer.getScore(grams, n)
        scoredgrams += sg
        scoreEvaler[n] = float(n*n*n*n)/total

    scoredgrams.sort()
    #print scoredgrams

    nsentences = []
    bsid = 0
    bcid = 0
    cand = []
    candS = []
    candidates = []
    for (((sid, cid, n), wid), t, score) in scoredgrams + [(((None, None, None), None), None, None)]:
        if (bcid != cid or bsid != sid) and cand != []:
            #print cand
            candidates.append( calcScore(cand, sents[bsid], scoreEvaler) )
            cand = []
        if bsid != sid:
            candidates.sort(reverse=True)
            map(printf,candidates)
            print
            nsentences.append(candidates[0][2])
            candidates = []
        cand.append( (t, score, wid, n) )
        #print sid,cid,wid, cand
        bsid = sid
        bcid = cid
    #print
    #print scoredgrams
    #print
    #print nsentences
    return " ".join(map(lambda s: " ".join(filter(lambda x: x!=""
                                                 ,s))
                       ,nsentences))

def linComb(s, r):
    return sum(map(lambda (a,b): a*b, zip(s, r)))

def calcScore(s, os, evaler):
    assert( len(s) != 0 )
    rs = []
    scores = [0,0,0,0,0,0]
    for (t, score, wid, n) in s:
        if score == -1:
            score = -2
        scores[n] += score
        if n==1 and wid != 0:
            w = t[0]
            if w != "$":
                rs.append(w)
                if len(os) <= wid-1:
                    scores[0] += len(w)
                else:
                    scores[0] += distance.distance(w, os[wid-1])
    return (linComb(scores, evaler)/len(os), scores, rs)

# Takes a list of sentences formed by comma-separated words
# and  
def confusionSets(sentences):

	# gets a list of lists of trigrams for each sentence
	# in the text and sets tcgrams equal to it
    tcgrams = taggedConfusionTrigrams(sentences)
    #print tcgrams
    #print
    tcgrams.sort() # how is this sorted

    #run candidate generator
    #tcgrams = map(lambda (t0, t1, t2, (sid, wid)):
    #        ((sid, wid), t1, random.random()), tcgrams)
	# generates sets of confusion words based on trigrams
    tcgrams = scorer.generate(tcgrams)
    tcgrams.sort()
    #print tcgrams
    #print

	# generate a list of n empty list, where n
	# is the number of sentences in the text.
	# this will be used to store a list of candidate
	# sentences
    candidates = nEmpty(len(sentences))

	# for each word in the confusion set of each word in
	# each sentence store this candidate word, its score,
	# sentence id and word id in 'candidates' list and
	# do this for each confusion set word to create a list
	# of candidate sentences to replace the original sentence
    for ((sid, wid), t1, score) in tcgrams:
        if len(candidates[sid]) == 0:
            candidates[sid] = nEmpty(len(sentences[sid]))
        candidates[sid][wid].append((t1, score))

	# for each sentence and candidate sentence get each
	# corresponding word and candidate word and calculate
	# the Damerau Levenshtein distance between them
    candSents = []
    sid = 0
    for (s,css) in zip(sentences, candidates):

        print "a", sum(map(len, css)), 
        sys.stdout.flush()

        ncss = []
        for (word,cs) in zip(s,css):
            ncs = []
            if word == "^^^":
                print word,
                ncss.append([ ((0,-1), word) ])
                continue

            thescore = -1
            for (candidate,score) in cs:
                if candidate == word:
                    thescore = score
                #if len(candidate) <= 2*len(word) and len(candidate)*2 >= len(word):
                dist = distance.distance(candidate, word)
                if dist <= (len(word)+1)/2:
                    heapq.heappush(ncs, ((-dist, score), candidate) )
            #print word, ncs

            tops = 2
            if thescore == -1:
                tops = 5
            ncss.append(heapq.nlargest(tops, ncs))
            #ncs.sort(reverse=True)
            #ncss.append(ncs)
        
        print "b", len(ncss),
        sys.stdout.flush()
        for cs in combinations3(ncss):
            candSents.append( (cs, sid) )
            #if not cs[-1][1] in [".", ":", "?", "!", ";"]:
            #    candSents.append( (cs + [((-1, -1), ".")], sid) )

        print "c"
        sid += 1
    #print candidates
    #print candSents
    candSents.sort()
    return candSents

# Create a list of n empty lists, where n is the
# number of sentences in the text being corrected
def nEmpty(n):
    return [[] for i in xrange(n)]

def taggedConfusionTrigrams(sentences):
    o = []		#create empty list
    sid = 0		
	# for each sentence in 'sentences' create a list
	# of all the trigrams and their sentence and word id's
	# and add each one to the list 'o'
    for s in sentences:
        o += trigramify(s, sid)
        #o += betweens(s, sid)
        sid += 1
    return o

def combinations(ls):
    if len(ls) == 0:
        return []
    if len(ls) == 1:
        return ls[0]
    tail = combinations(ls[1:])
    return [l+" "+t for l in ls[0] for t in tail]

def combinations2(ls):
    if len(ls) == 0:
        return [[]]
    tail = combinations2(ls[1:])
    return [[l]+t for l in ls[0] for t in tail]

def combinations3(ls, k=1):
    if ls == [] or ls == [[]]:
        return []
    a = map(operator.itemgetter(0), ls)
    rr = [a]
    rrr = [a]
    for i in xrange(k):
        r = []
        for a in rr:
            a = list(a)
            b = []
            for l in ls:
                t = a.pop(0)
                for c in l[1:]:
                    r.append(b + [c] + a)
                b.append(t)

        rr = []
        for e in r:
            if not e in rrr:
                rrr.append(e)
                rr.append(e)
        if rr == []:
            break
    return rrr


def runFile(fnr, fnw):
    fr = open(fnr, 'r')
    p = [1]
    ps = []
    while p != []:
        p = test.readparagraph(fr)
        ps.append(p)
    fr.close()

    r = "\n ^^^ . \n".join(map(unsentences, ps))
    w = correct(r)
    w = "\n\n".join(map(lambda x: x.strip(),w.split("^^^ .")))

    fw = open(fnw, 'w')
    fw.write(w)
    fw.close()


if __name__ == '__main__':
    #print combinations([["0","1"], ["2","3"], ["4","5"]])
    #print combinations([["0","1"], ["2","3","5"]])
    #print combinations([["0","1","3"], ["2","3","5"]])
    #print combinations([["0","1"], ["0","1"]])
    #print combinations([["0","1"], ["0","1"], ["0","1"]])
    #print combinations([[], ["0","1"]])
    #print combinations([[]])
    #print combinations([])
    #print combinations2([["0","1"], ["0","1"]])
    #print combinations2([[], ["0","1"]])
    #print combinations2([[]])
    #print combinations2([])
    #print combinations3([["0","1"], ["0","1"]], 0)
    #print combinations3([["0","1"], ["0","1"]], 1)
    #print combinations3([["0","1"], ["0","1"]], 2)
    #print combinations3([["0","1"], ["0","1"]], 3)
    #print combinations3([[]])
    #print combinations3([])

	# text to be checked
    ss = ["I am .", "This is a sentence .", "This is another sentence .",
            "Hello !", "This sentence is bid .", "Forgotten period"]
    #print taggedConfusionTrigrams(map(words, ss))
	# run spell checker and print result
    print correct(" ".join(ss))

    runFile('test/gplchi.txt', 'test/gpl-corrected.txt')

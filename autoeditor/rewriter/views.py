# -*- coding: utf-8 -*-

import re
import string
import os

from django.http import HttpResponse
from django.template import RequestContext, loader


class Rewriter:

    def __init__(self):
        module_dir = os.path.dirname(__file__)  # get current directory
        file_path = os.path.join(module_dir, 'static/rewriter/wordsInOrder.txt')
        self.wordFile = open(file_path, 'r')

        self.wordFileContents = self.wordFile.read()
        self.wordFileList = []
        self.rareWordCutoff = 25000

        self.prepWords()

# prep

    def prepWords(self):
        wordFileLines = self.wordFileContents.split("\n")
        for index, wordFileLine in enumerate(wordFileLines):
            self.wordFileList.append(wordFileLine)

    def cleanedInput(self, dirtyInput):
        allow = string.ascii_letters + string.digits + " " + "\n"
        dirtyInput = re.sub('[^%s]' % allow, '', dirtyInput) # filter out non-alphanumeric characters
        return dirtyInput.lower()

# Per-word operations

    def wordFrequencyRank(self, word):
        if word in self.wordFileList:
            index = self.wordFileList.index(word)
        else:
            index = -1
        return index

    def getRareWords(self, wordArray, wordFrequencyArray):
        rareWords = []
        unknownWords = []
        for index, wordFrequencyValue in enumerate(wordFrequencyArray):
            if wordFrequencyValue > self.rareWordCutoff and wordFrequencyValue > -1:
                rareWords.append(wordArray[index])
            elif wordFrequencyValue == -1:
                unknownWords.append(wordArray[index])
        return rareWords, unknownWords

    def frequencyArrayOfWords(self, words):
        wordFrequencyArray = []
        for word in words:
            wordFrequencyArray.append(self.wordFrequencyRank(word))
        return wordFrequencyArray

    def wordsInText(self, text):
        return re.findall(r"[\w']+", text)

    def syllableCountEstimateForWord(self, word):
        return 0

# Per-sentence operations

    def sentencesInText(self, text):
        return text.split(".")

# High-level calculations

    def analyzeWordRarityInText(self, words):
        # Clean up input
        cleanedInput = self.cleanedInput(words)
        wordArray = self.wordsInText(cleanedInput)

        # Get word frequencies
        wordFrequencyArray = self.frequencyArrayOfWords(wordArray)

        # Calculate rare words
        rareWords, unknownWords = self.getRareWords(wordArray, wordFrequencyArray)

        return rareWords, unknownWords


def index(request):
    return HttpResponse("Hello, world. You're at the rewriter index.")

def runrewriter(request):
    template = loader.get_template('rewriter/base.html')
    rewr = Rewriter()
    text = ""
    if (request.POST):
        text = request.POST['text']
        sentences_in_text = []
        rare_words = []
        unknown_words = []
        highlighted_formatted_text = text
        if (request.POST['operation'] == "rareWords"):
            rare_words, unknown_words = Rewriter.analyzeWordRarityInText(rewr, text)
        elif (request.POST['operation'] == "highlightSentences"):
            sentences_in_text = Rewriter.sentencesInText(rewr, text)
        else:
            print("Unexpected value in POST['operation']: " + request.POST['operation'])

        # Add visual formatting for each rare word
        for word in rare_words:
            print("Replacing " + word)
            highlighted_formatted_text = highlighted_formatted_text.replace(word, "<div class=\"b1\">" + word + "</div>")
        for word in unknown_words:
            print("Replacing " + word)
            highlighted_formatted_text = highlighted_formatted_text.replace(word, "<div class=\"b0\">" + word + "</div>")

        print(highlighted_formatted_text)

        # Hand calculated text off to the template
        context = RequestContext(request, {
            'sentences_in_text': sentences_in_text,
            'rare_words': rare_words,
            'unknown_words': unknown_words,
            'original_text': text,
            'highlighted_formatted_text': highlighted_formatted_text
        })
    else :
        # No text / initial load of page

        if len(text) <= 0:
            text = 'Those values are all pretty close together and thats another problem. If I take all pitchers that have at least 250 recorded pitches this season and average their Nasty Factors, the results go from a highest Nasty Factor of 48 (Mike MacDougal) to a low of 40 (Daniel Schlereth) and the standard deviation is a mere 1.4 points. Such a small spread makes me skeptical theres anything useful there to tease out.'
        context = RequestContext(request, {
            'sentences_in_text': [],
            'rare_words': [],
            'unknown_words': [],
            'original_text': text
        })

    return HttpResponse(template.render(context));
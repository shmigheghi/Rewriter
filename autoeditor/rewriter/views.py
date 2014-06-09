# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.template import RequestContext, loader

import re
import string
import os

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
        return dirtyInput.lower()

# Per-word operations

    def wordFrequencyRank(self, word):
        if word in self.wordFileList:
            index = self.wordFileList.index(word)
        else:
            index = -1
        return index

    def rareWords(self, wordArray, wordFrequencyArray):
        rareWords = []
        for index, wordFrequencyValue in enumerate(wordFrequencyArray):
            if wordFrequencyValue > self.rareWordCutoff or wordFrequencyValue == -1:
                rareWords.append(wordArray[index])
        return rareWords

    def frequencyArrayOfWords(self, words):
        wordFrequencyArray = []
        for word in words:
            allow = string.ascii_letters + string.digits
            word = re.sub('[^%s]' % allow, '', word) # filter out non-alphanumeric characters
            wordFrequencyArray.append(self.wordFrequencyRank(word))
        return wordFrequencyArray

    def wordsInText(self, text):
        return text.split(" ")

# Per-sentence operations

    def sentencesInText(self, text):
        return text.split(".")

    def syllableCountEstimateForWord(self, word):
        return 0

# High-level calculations

    def showRareWordsInText(self, words):
        # Clean up input
        cleanedInput = self.cleanedInput(words)
        wordArray = self.wordsInText(cleanedInput)

        # Get word frequencies
        wordFrequencyArray = self.frequencyArrayOfWords(wordArray)

        # Calculate rare words
        rareWords = self.rareWords(wordArray, wordFrequencyArray)

        return rareWords


def index(request):
    return HttpResponse("Hello, world. You're at the rewriter index.")

def runrewriter(request):
    template = loader.get_template('rewriter/base.html')
    rewr = Rewriter()

    text = ""
    if (request.POST):
        text = request.POST['text']

    if len(text) <= 0:
        text = 'This is default text. The following comes from an email exchange between myself and John Barnes, whose story I critiqued and who has given permission to reprint the exchange. I know that this question often comes up for newer writers. They see writers who write long, elaborate sentences and wonder why they then get criticized for overly long and complicated sentences. '

    rare_words = Rewriter.showRareWordsInText(rewr, text)
    sentences_in_text = Rewriter.sentencesInText(rewr, text)

    context = RequestContext(request, {
        'sentences_in_text': sentences_in_text,
        'rare_words': rare_words,
        'original_text': text
    })
    return HttpResponse(template.render(context));
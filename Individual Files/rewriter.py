# -*- coding: utf-8 -*-

import re
import string

class Rewriter:

    def __init__(self):
        self.wordFile = open('wordsInOrder.txt', 'r')

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
        print(wordFrequencyArray)
        for index, wordFrequencyValue in enumerate(wordFrequencyArray):
            if wordFrequencyValue > self.rareWordCutoff or wordFrequencyValue == -1:
                rareWords.append(wordArray[index])
        return rareWords

    def frequencyArrayOfWords(self, words):
        wordFrequencyArray = []
        for word in words:
            allow = string.letters + string.digits
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

        print('Rare words in %s:' % words)
        print (rareWords)


rewr = Rewriter()

text = 'But dressing up a piece of prose with thesaurus-words tends not to work well. And here’s why: a thesaurus suggests words without explaining nuances of meaning and levels of diction. So if you choose substitute-words from a thesaurus, it’s likely that your writing will look as though you’ve done just that. The thesaurus-words are likely to look odd and awkward, or as a writer relying on Microsoft Word’s thesaurus might put it, “extraordinary and uncoordinated.” When I see that sort of strange diction in a student’s writing and ask whether a thesaurus is involved, the answer, always, is yes. A thesaurus might be a helpful tool to jog a writer’s memory by calling up a familiar word that’s just out of reach. But to expand the possibilities of a writer’s vocabulary, a collegiate dictionary is a much better choice, offering explanations of the differences in meaning and use among closely related words. Here’s just one example: Merriam-Webster’s treatment of synonyms for awkward. What student-writers need to realize is that it’s not ornate vocabulary or word-substitution that makes good writing. Clarity, concision, and organization are far more important in engaging and persuading a reader to find merit in what you’re saying. If you’re tempted to use the thesaurus the next time you’re working on an essay, consider what is about to happen to this sentence:'

Rewriter.showRareWordsInText(rewr, text)
Rewriter.sentencesInText(rewr, text)

print(Rewriter.sentencesInText(rewr, text))
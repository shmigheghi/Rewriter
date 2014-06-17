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

        syllable_file_path = os.path.join(module_dir, 'static/rewriter/mhyph.txt')
        self.syllableFile = open(syllable_file_path, 'r', encoding="ISO-8859-1")
        self.syllableFileContents = self.syllableFile.read()
        self.syllableFileList = []

        no_hyphen_syllable_file_path = os.path.join(module_dir, 'static/rewriter/mhyphnohyphens.txt')
        self.no_hyphensyllableFile = open(no_hyphen_syllable_file_path, 'r')
        self.no_hyphensyllableFileContents = self.no_hyphensyllableFile.read()
        self.no_hyphensyllableFileList = []

        self.prepWords()

# prep

    def prepWords(self):
        wordFileLines = self.wordFileContents.split("\n")
        for index, wordFileLine in enumerate(wordFileLines):
            self.wordFileList.append(wordFileLine)

        syllableFileLines = self.syllableFileContents.split("\n")
        for index, syllableFileLine in enumerate(syllableFileLines):
            self.syllableFileList.append(syllableFileLine)

        no_hyphensyllableFileLines = self.no_hyphensyllableFileContents.split("\n")
        for index, no_hyphensyllableFileLine in enumerate(no_hyphensyllableFileLines):
            self.no_hyphensyllableFileList.append(no_hyphensyllableFileLine)

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

    def syllableCountForWord(self, word):
        try:
            syllableIndex = self.no_hyphensyllableFileList.index(word.lower())
            if syllableIndex > -1:
                syllableContainingWord = self.syllableFileList[syllableIndex]
                print("Word: "+ word)
                print("Syll word: "+ syllableContainingWord)
                print("Len 1: % d Len 2: % d", len(word), len(syllableContainingWord))
                syllableCount = 1
                processingLetters = True
                for letter in syllableContainingWord:
                    if letter.isalpha() and not processingLetters:
                        syllableCount += 1
                        processingLetters = True
                    elif not letter.isalpha():
                        processingLetters = False
                return syllableCount
        except ValueError: # Word not present in no_hyphen list
            return len(word) // 3 # guesstimate, needs improvement. Many words are missing like 'values' from the list

    def stringCompIgnoringSpecialChars(self, a, b):
        return [c for c in a if c.isalpha()] == [c for c in b if c.isalpha()]

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

    def fleschKincaidGradeLevelForText(self, text):
        wordsInText = self.wordsInText(text)
        totalSentences = len(self.sentencesInText(text))
        totalWords = len(wordsInText)

        totalSyllables = 0
        for word in wordsInText:
            totalSyllables += self.syllableCountForWord(word)
            print(str(totalSyllables) + " syllables so far")
        print("Syllables: "+ str(totalSyllables))
        fkGradeLevel = 0.39 * (totalWords / totalSentences) + 11.8 * (totalSyllables / totalWords) - 15.59

        return fkGradeLevel

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
        grade_level_sentences = []
        highlighted_formatted_text = ""
        fkGrade = ""
        words_in_text = rewr.wordsInText(text)
        if (request.POST['operation'] == "rareWords"):
            rare_words, unknown_words = Rewriter.analyzeWordRarityInText(rewr, text)
        elif (request.POST['operation'] == "highlightSentences"):
            sentences_in_text = Rewriter.sentencesInText(rewr, text)
        elif (request.POST['operation'] == "fkGradeLevel"):
            # grade_level_sentences = Rewriter.gradeLevelForSentences(rewr, text)
            fkGrade = Rewriter.fleschKincaidGradeLevelForText(rewr, text)
            print("F-K Grade: "+ str(fkGrade))
        else:
            print("Unexpected value in POST['operation']: " + request.POST['operation'])

        # Add visual formatting for each rare word
        for word in words_in_text:
            if word in rare_words:
                highlighted_formatted_text += "<span class=\"b1\">" + word + "</span>"
            elif word in unknown_words:
                highlighted_formatted_text += "<span class=\"b0\">" + word + "</span>"
            else:
                highlighted_formatted_text += word
            highlighted_formatted_text += " "
        print(highlighted_formatted_text)

        # Hand calculated text off to the template
        context = RequestContext(request, {
            'sentences_in_text': sentences_in_text,
            'rare_words': rare_words,
            'unknown_words': unknown_words,
            'original_text': text,
            'grade_level_sentences': grade_level_sentences,
            'flesch_kincaid_grade': str(fkGrade),
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
            'grade_level_sentences': [],
            'flesch_kincaid_grade': "",
            'original_text': text
        })

    return HttpResponse(template.render(context));
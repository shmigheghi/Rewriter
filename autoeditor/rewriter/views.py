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
        wordFile = open(file_path, 'r')
        wordFileContents = wordFile.read()
        self.wordFileList = self.wordListFromFileContents(wordFileContents)
        self.rareWordCutoff = 25000

        syllable_file_path = os.path.join(module_dir, 'static/rewriter/mhyph.txt')
        syllableFile = open(syllable_file_path, 'r', encoding="ISO-8859-1")
        syllableFileContents = syllableFile.read()
        self.syllableFileList = self.wordListFromFileContents(syllableFileContents)

        no_hyphen_syllable_file_path = os.path.join(module_dir, 'static/rewriter/mhyphnohyphens.txt')
        no_hyphen_syllableFile = open(no_hyphen_syllable_file_path, 'r')
        no_hyphen_syllableFileContents = no_hyphen_syllableFile.read()
        self.no_hyphen_syllableFileList = self.wordListFromFileContents(no_hyphen_syllableFileContents)

    def wordListFromFileContents(self, fileContents):
        wordFileList = [];
        wordFileLines = fileContents.split("\n")
        for index, wordFileLine in enumerate(wordFileLines):
            wordFileList.append(wordFileLine)
        return wordFileList

# prep

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
        rareWordStratusArrays = [[], [], [], []] # three stratuses, and a bucket for the words not in the word list

        cutoffOne = 5000
        cutoffTwo = 20000
        cutoffThree = 40000

        for index, wordFrequencyValue in enumerate(wordFrequencyArray):
            word = wordArray[index]
            if wordFrequencyValue > self.rareWordCutoff and wordFrequencyValue > -1:
                rareWords.append(word)
            elif wordFrequencyValue == -1:
                unknownWords.append(word)

            if wordFrequencyValue == -1:
                rareWordStratusArrays[3].append(word)
            elif wordFrequencyValue < cutoffOne:
                rareWordStratusArrays[0].append(word)
            elif wordFrequencyValue < cutoffTwo:
                rareWordStratusArrays[1].append(word)
            elif wordFrequencyValue < cutoffThree:
                rareWordStratusArrays[2].append(word)

        return rareWords, unknownWords, rareWordStratusArrays

    def frequencyArrayOfWords(self, words):
        wordFrequencyArray = []
        for word in words:
            wordFrequencyArray.append(self.wordFrequencyRank(word))
        return wordFrequencyArray

    def wordsInText(self, text):
        return re.findall(r"[\w']+", text)

    def syllableCountForWord(self, word):
        try:
            syllableIndex = self.no_hyphen_syllableFileList.index(word.lower())
            if syllableIndex > -1:
                syllableContainingWord = self.syllableFileList[syllableIndex]
                print("Word: "+ word + " Syll word: "+ syllableContainingWord)
                syllableCount = 1
                processingLetters = True
                for letter in syllableContainingWord:
                    if letter.isalpha() and not processingLetters:
                        syllableCount += 1
                        processingLetters = True
                    elif not letter.isalpha():
                        processingLetters = False
                print("Syllable count: " + str(syllableCount))
                return syllableCount
        except ValueError: # Word not present in no_hyphen list
            print("Can't find " + word + " in hyphen list")
            return max(len(word) // 3, 1) # guesstimate, needs improvement. Many words are missing like 'values' from the list

    def stringCompIgnoringSpecialChars(self, a, b):
        return [c for c in a if c.isalpha()] == [c for c in b if c.isalpha()]

# Per-sentence operations

    def sentencesInText(self, text):
        return text.split(".")

    def formattedSentencesByGradeLevel(self, text):
        formattedText = ""
        sentences = self.sentencesInText(text)
        for sentence in sentences:
            fkSentenceLevel = self.fleschKincaidGradeLevelForText(sentence)
            fkAsInt = int(fkSentenceLevel)
            fkBounded = max(min(15, fkAsInt), 1) # keeps the grade level from 1-15 for highlighting purposes
            formattedText += "Level " + str(fkBounded) + ": <span class=\"fk" + str(fkBounded) + "\">" + sentence + "</span><br>"
        return formattedText


# High-level calculations

    def analyzeWordRarityInText(self, words):
        # Clean up input
        cleanedInput = self.cleanedInput(words)
        wordArray = self.wordsInText(cleanedInput)

        # Get word frequencies
        wordFrequencyArray = self.frequencyArrayOfWords(wordArray)

        # Calculate rare words
        rareWords, unknownWords, rareWordStratusArrays = self.getRareWords(wordArray, wordFrequencyArray)

        return rareWords, unknownWords, rareWordStratusArrays

    def fleschKincaidGradeLevelForText(self, text):
        wordsInText = self.wordsInText(text)
        totalSentences = len(self.sentencesInText(text))
        totalWords = len(wordsInText)
        if totalWords == 0:
            return 0

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
        error_text = ''
        rareWordStratusArrays = []
        words_in_text = rewr.wordsInText(text)

        operationValue = request.POST.get('operation', '')
        if (operationValue == "rareWords"):
            rare_words, unknown_words, rareWordStratusArrays = Rewriter.analyzeWordRarityInText(rewr, text)
        elif (operationValue == "highlightSentences"):
            sentences_in_text = Rewriter.sentencesInText(rewr, text)
        elif (operationValue == "fkGradeLevel"):
            grade_level_sentences = Rewriter.formattedSentencesByGradeLevel(rewr, text)
            fkGrade = Rewriter.fleschKincaidGradeLevelForText(rewr, text)
            print("F-K Grade: "+ str(fkGrade))
        elif (operationValue == ''):
            error_text = "No operation selected " + operationValue
        else:
            error_text = "Unexpected operation value: " + operationValue

        # Add visual formatting for each rare word
        for word in words_in_text:
            if word in unknown_words:
                    highlighted_formatted_text += "<span class=\"bu\">" + word + "</span>"
            else:
                found = False
                for index, stratus in enumerate(rareWordStratusArrays):
                   if rewr.cleanedInput(word) in stratus:
                       highlighted_formatted_text += "<span class=\"b" + str(index) + "\">" + word + "</span>"
                       found = True
                       break
                if not found:
                    highlighted_formatted_text += word
            highlighted_formatted_text += " "
        print(highlighted_formatted_text)

        # Hand calculated text off to the template
        context = RequestContext(request, {
            'sentences_in_text': sentences_in_text,
            'rare_words': rare_words,
            'unknown_words': unknown_words,
            'original_text': text,
            'grade_level_sentences_formatted': grade_level_sentences,
            'flesch_kincaid_grade': str(fkGrade),
            'highlighted_formatted_text': highlighted_formatted_text,
            'error_text': error_text
        })
    else :
        # No text / initial load of page

        if len(text) <= 0:
            text = "Losing two games against Boston isn't too surprising. However, losing by scores of 1-0 and 2-1 at Fenway Park is not what I'd have expected. The Twins have definitely done enough to win these games, but they just haven't been able to find any clutch hitting. No Oswaldo Arcia in the lineup today, as he's really been struggling lately. Also, we should expect some news either after the game or early tomorrow on who is being sent down to make room for Yohan Pino. The foregone conclusion has been that Mike Pelfrey will be placed on the 60-day disabled list, but the corresponding 25-man roster move is still unknown. Ron Gardenhire said it will be a pitcher, but no one has really been awful except Jared Burton. Would the Twins be bold enough to DFA him and save Pelfrey to the 60-day DL to make room for someone else? Kyle Gibson takes the mound for the Twins, and while his success has been a bit luck-aided this year, it's still nice to see him rebound from a tough rookie season. His 3.55 ERA is second on the team among starters thanks to a low .266 BABIP allowed, along with a nice 0.47 HR/9 (major league average is around 1.00). In spite of his low strikeout rate, he's put together a nice year so far. Opposing him on the mound is John Lackey, who has turned into the pitcher the Red Sox were expecting when they signed him back in 2010 from the Angels. Despite a rough 2011 and then missing 2012 because of Tommy John surgery, Lackey has returned to form from posting a career low walk rate, along with the best velocity of his career. The Twins may have some trouble avoiding the sweep today with him on the mound."
        context = RequestContext(request, {
            'sentences_in_text': [],
            'rare_words': [],
            'unknown_words': [],
            'grade_level_sentences_formatted': [],
            'flesch_kincaid_grade': '',
            'original_text': text,
            'error_text': ''
        })

    return HttpResponse(template.render(context));
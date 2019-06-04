from nltk.stem.lancaster import LancasterStemmer
from nltk.stem.snowball import SnowballStemmer

def stem_words(words):
	# lancaster_stemmer = LancasterStemmer()
	# return lancaster_stemmer.stem(words)
	stemmer = SnowballStemmer("english")
	return stemmer.stem(words)
	
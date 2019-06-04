def remove_symbol(string, chars = ['~', '!', '#', '$', '%', '^', '&', '*', '(', ')', '-', '+', '[', ']', '{', '}', ':', ';', '"', "'", '<', ',', '.', '>', '?', '/', 'II', 'III', 'IV','=']):
	for char in chars:
		string = string.replace(char,' ')
	return string
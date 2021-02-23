# Коэффициент Танимото
def tanimoto(s1, s2):
	a, b, c = len(s1), len(s2), 0.0
	for sym in s1:
		if sym in s2:
			c += 1
	return c / (a + b - c)

def levenshtein_distance(a, b):
	n, m = len(a), len(b)
	# убедимся что n <= m, чтобы использовать минимум памяти O(min(n, m))
	if n > m:
		a, b = b, a
		n, m = m, n
	current_row = range(n + 1)  # 0 ряд - просто восходящая последовательность (одни вставки)
	for i in range(1, m + 1):
		previous_row, current_row = current_row, [i] + [0] * n
		for j in range(1, n + 1):
			add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
			if a[j - 1] != b[i - 1]:
				change += 1
			current_row[j] = min(add, delete, change)
	return current_row[n]

def lev_dis(a, b):
	return (1 - levenshtein_distance(a, b) / max(len(a), len(b)))

#Очистка от дубликатов с сохранением последовательности
def duplicate_clean(seq):
	seen = set()
	seen_add = seen.add
	return [x for x in seq if not (x in seen or seen_add(x))]

#Функция очистки и подготовки токенов
def preparer_instruction(tokens, input, trust_level = 0.5, id_duplicate_clean = True):
	format_tokens = []
	unknown_tokens = []
	for word in tokens:
		end_form, simil = None, 0
		for end_form_variant, words_variants in input.items():
			for variant in words_variants:
				compare = lev_dis(word, variant)
				if compare > trust_level and compare > simil:
					end_form = end_form_variant
					simil = compare
		if simil == 0:
			unknown_tokens.append(word)
		else:
			format_tokens.append(end_form)
	#Удаляем повторяющиеся слова сохраняя последовательность
	end_format_tokens = duplicate_clean(format_tokens) if id_duplicate_clean else format_tokens
	return end_format_tokens, unknown_tokens


if __name__ == '__main__':
	import sys
	import json

	tokens = sys.argv[1].split(' ')
	vocabulary = {}
	with open('/etc/assol/vocabulary.json', 'r') as f:
		vocabulary = json.loads(f.read())

	for i in range(1, 11):
		token_instruction, unknown_tokens = preparer_instruction(tokens, vocabulary['input'], i/10)
		print(i/10, 'схожесть ФИЛЬТР:', token_instruction)
		print('Неизвестные токены:', unknown_tokens)


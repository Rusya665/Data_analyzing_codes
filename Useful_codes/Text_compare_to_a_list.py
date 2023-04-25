import re


path_text = r'C:\Users\runiza\OneDrive - O365 Turun yliopisto\Desktop/Text.txt'
path_AWL = r'C:\Users\runiza\OneDrive - O365 Turun yliopisto\Desktop/AWL.txt'

forbidden_list = ['so', 'non']
AWL_list = []
words_list = []
matches = []
counter = 0
word_counter = 0


with open(path_text, encoding="utf8") as my_file:
    with open(path_AWL, encoding="utf8") as txt_AWL:
        for lines in txt_AWL:
            for case in re.findall("\w+", lines.lower()):
                AWL_list.append(case)
        for line in my_file:
            for word in re.findall("\w+", line.lower()):
                word_counter += 1
                if word not in forbidden_list:
                    if word in AWL_list:
                        print(word)
                        counter += 1

print(f'In the total {word_counter} we have {counter} AW')

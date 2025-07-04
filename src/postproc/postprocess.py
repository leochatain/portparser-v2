#################################################
### Post Processing Program to Portparser.v2
#################################################
#
#  (c) Lucelene Lopes 2024
#
##################
#  main function: fixLemmaFeatures()
#    It performs the correction of some lemmas and morphological
#    features from the input file and saves it in the output file.
#    The options are:
#        -h or -help       to print out the options
#        -o or -output     to inform (next) the output file
#        -l or -lemma      to perform only the lemma corrections
#        -f or -feats      to perform only the features corrections
#        -q or -quiet      to not generate the changes report (.rep.tsv)
##################
import sys, os
import lexikon
from conlluFile import conlluFile
lex = lexikon.UDlexPT()

#################################################
### Function CMD line arguments capture
#################################################
def parseOptions(arguments):
    # default options, doLemma e doFeats alteráveis para True, se ambos False
    output_file, input_file, doLemma, doFeats, quiet = "", "", False, False, False
    #print(arguments)
    i = 1
    while i < len(arguments):
        if (arguments[i][0] == "-"):
            # ajuda (help) - mostra ajuda, nada é executado
            if ((arguments[i][1] == "h") and (len(arguments[i])==2)) or \
               (arguments[i] == "-help"):
                print("Opções:\n-h ajuda\n-o arquivo de saída", \
                      "\n-l executa apenas correção de lemma", \
                      "\n-f executa apenas correção de features", \
                      "\n-q não salva relatório (correção Quieta)", \
                      "\nExemplo de utilização:", \
                      "\n   python3 postproc.py -o yyy.conllu xxx.conllu", \
                      "\nBusca as sentenças no arquivo 'xxx.conllu',", \
                      "  corrige lemmas e features e salva as", \
                      "  sentenças no arquivo 'yyy.conllu''", \
                      sep="")
                return None
            # faz correção de lemma
            elif ((arguments[i][1] == "l") and (len(arguments[i])==2)) or \
               (arguments[i] == "-lemma"):
                doLemma = True
                i += 1
            # faz correção de feats
            elif ((arguments[i][1] == "f") and (len(arguments[i])==2)) or \
               (arguments[i] == "-feats"):
                doFeats = True
                i += 1
            # modo quieto (sem relatório)
            elif ((arguments[i][1] == "q") and (len(arguments[i])==2)) or \
               (arguments[i] == "-quiet"):
                quiet = True
                i += 1
            # arquivo de saída
            elif ((arguments[i][1] == "o") and (len(arguments[i])==2)) or \
               (arguments[i] == "-output"):
                output_file = arguments[i+1]
                i += 2
        # arquivo de entrada - último parâmetro (sem -i antes)
        else:
            if (os.path.isfile(arguments[i])):
                input_file = arguments[i]
                break
            else:
                print("O arquivo {} não foi encontrado, por favor execute novamente".format(arguments[i]))
                return None
    if (not doLemma and not doFeats):
        doLemma, doFeats = True, True
    #print(output_file, input_file, doLemma, doFeats)
    output_file, input_file = arguments[2], arguments[3]
    return [output_file, input_file, doLemma, doFeats, quiet]

#################################################
### Function - read usual abbreviations
#################################################
def getUsualAbbr():
    infile = open("./src/postproc/usAbbr.tsv", "r")
    dayW, month, abbr, ordinal = [], [], [], []
    for line in infile:
        if (line[0] == "#"):
            continue
        buf = line[:-1].split("\t")
        if (buf[1] == "week"):
            dayW.append([buf[0], buf[2], buf[3], buf[4]])
        elif (buf[1] == "month"):
            month.append([buf[0], buf[2], buf[3], buf[4]])
        elif (buf[1] == "abbr"):
            abbr.append([buf[0], buf[2], buf[3], buf[4]])
        elif (buf[1] == "ordinal"):
            ordinal.append([buf[0], buf[2], buf[3], buf[4]])
    return dayW, month, abbr, ordinal

#################################################
### Function - Check if word is in an abbreviation list
#################################################
def isWithin(listAbbr, form):
    for a in listAbbr:
        if (form == a[0]):
            return a[1],a[2],a[3]
    return None, None, None

#################################################
### Function - Check if word is in an abbreviation list
#################################################
def print_reps(repfile, accName, acc):
    print("\n==========================================================\n", file=repfile)
    for i in range(len(acc)):
        print("{:8} - fixed: {:6>}".format(accName[i], acc[i]), file=repfile)
        print("{:8} - fixed: {:6>}".format(accName[i], acc[i]))

#################################################
### Main Function - Fix Lemma and Features
#################################################
def fixLemmaFeatures():
    lexCloseTags = ["ADP", "ADV", "CCONJ", "DET", "PRON", "SCONJ"]
    lexOpenTags  = ["ADJ", "INTJ", "NOUN", "NUM"]
    lexVerbTags  = ["AUX", "VERB"]
    lexOutOfTags = ["PROPN", "PUNCT", "SYM"]
    # the POS tag "X" is dealt differently
    if (len(sys.argv) == 1):
        arguments = ["xxx.conllu", "yyy.conllu", True, True, False]
        print("Assumindo default: 'yyy.conllu' como arquivo de entrada, 'xxx.conllu' como arquivo de saída, e executando correção de lemas e features.")
    else:
        arguments = parseOptions(sys.argv)
    if (arguments != None):
        if (arguments[0] == ""):
            print("Assumindo 'xxx.conllu' como arquivo de saída")
            arguments[0] = 'xxx.conllu'
        if not os.path.isfile(arguments[1]):
            print("Arquivo de entrada inválido - por favor corrija e tente novamente")
        else:
            outfile = open(arguments[0], "w")
            repfile = open(arguments[0]+".rep.tsv", "w")
            base = conlluFile(arguments[1])
            # contadores
            accName = ["Lchanged", "LnoLEX", "L1LEX", "LmLEX", "LunkTAG", \
                       "LdaysW", "Lmonth", "LuAbbr", "Lord", "LrepTAG", \
                       "Fchanged", "FnoLEX", "F1LEX", "FmLEX", "FunkTAG", \
                       "FdaysW", "Fmonth", "FuAbbr", "Ford", "FrepTAG", \
                      ]
            acc = [0]*len(accName)
            # usual Abbr (lidas de um .tsv no formato "forma", "tipo", "POS", "lemma", "feats")
            dayW, month, abbr, ordinal = getUsualAbbr()
            # main loop
            for i in range(base.getS()):
                b = base.getSentByIndex(i)
                for tk in b[4]:
                    # skip contracted words
                    if ("-" in tk[0]):
                        continue
                    # check if abbreviation
                    pos, lem, feat = isWithin(abbr, tk[1].lower())
                    if (pos == tk[3]):
                        if (arguments[2]):    # fix Lemma
                            if (tk[2] != lem):
                                acc[accName.index("Lchanged")] += 1
                                acc[accName.index("LuAbbr")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "LuAbbr", tk[2], lem, sep="\t", file=repfile)
                                tk[2] = lem
                        if (arguments[3]):    # fix Features
                            if (tk[5] != feat):
                                acc[accName.index("Fchanged")] += 1
                                acc[accName.index("FuAbbr")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "FuAbbr", tk[5], feat, sep="\t", file=repfile)
                                tk[5] = feat
                    # check if day of the week
                    elif ("NOUN" == tk[3]):
                        pos, lem, feat = isWithin(dayW, tk[1].lower())
                        if (arguments[2]) and (pos is not None):    # fix Lemma
                            if (tk[2] != lem):
                                acc[accName.index("Lchanged")] += 1
                                acc[accName.index("LdaysW")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "LdaysW", tk[2], lem, sep="\t", file=repfile)
                                tk[2] = lem
                        if (arguments[3]) and (pos is not None):    # fix Features
                            if (tk[5] != feat):
                                acc[accName.index("Fchanged")] += 1
                                acc[accName.index("FdaysW")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "FdaysW", tk[5], feat, sep="\t", file=repfile)
                                tk[5] = feat
                    # check if month
                    elif ("NOUN" == tk[3]):
                        pos, lem, feat = isWithin(month, tk[1].lower())
                        if (arguments[2]) and (pos is not None):    # fix Lemma
                            if (tk[2] != lem):
                                acc[accName.index("Lchanged")] += 1
                                acc[accName.index("Lmonth")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "Lmonth", tk[2], lem, sep="\t", file=repfile)
                                tk[2] = lem
                        if (arguments[3]) and (pos is not None):    # fix Features
                            if (tk[5] != feat):
                                acc[accName.index("Fchanged")] += 1
                                acc[accName.index("Fmonth")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "Fmonth", tk[5], feat, sep="\t", file=repfile)
                                tk[5] = feat
                    # check if ordinal
                    elif ("ADJ" == tk[3]):
                        pos, lem, feat = isWithin(ordinal, tk[1].lower())
                        if (arguments[2]) and (pos is not None):    # fix Lemma
                            if (tk[2] != lem):
                                acc[accName.index("Lchanged")] += 1
                                acc[accName.index("Lord")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "Lord", tk[2], lem, sep="\t", file=repfile)
                                tk[2] = lem
                        if (arguments[3]) and (pos is not None):    # fix Features
                            if (tk[5] != feat):
                                acc[accName.index("Fchanged")] += 1
                                acc[accName.index("Ford")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "Ford", tk[5], feat, sep="\t", file=repfile)
                                tk[5] = feat
                    # check if POS tag X
                    elif (tk[3] == "X"):
                        if (arguments[2]):    # fix Lemma
                            if (tk[1] != tk[2]):
                                acc[accName.index("Lchanged")] += 1
                                acc[accName.index("LrepTAG")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "LrepTAG", tk[2], tk[1], sep="\t", file=repfile)
                                tk[2] = tk[1]
                        if (arguments[3]):    # fix Features
                            if (tk[5] not in ["Foreign=Yes", "_"]):
                                acc[accName.index("Fchanged")] += 1
                                acc[accName.index("FrepTAG")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "FrepTAG", tk[5], "Foreign=Yes", sep="\t", file=repfile)
                                tk[5] = "Foreign=Yes"
                    # check if POS tag out of the Lexicon
                    elif (tk[3] in lexOutOfTags):
                        if (arguments[2]):    # fix Lemma
                            if (tk[1] != tk[2]):
                                acc[accName.index("Lchanged")] += 1
                                acc[accName.index("LrepTAG")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "LrepTAG", tk[2], tk[1], sep="\t", file=repfile)
                                tk[2] = tk[1]
                        if (arguments[3]):    # fix Features
                            if (tk[5] != "_"):
                                acc[accName.index("Fchanged")] += 1
                                acc[accName.index("FrepTAG")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "FrepTAG", tk[5], "_", sep="\t", file=repfile)
                                tk[5] = "_"
                    # check NUM in numeric form
                    elif (tk[3] == "NUM") and ((tk[1][0].isdigit()) or \
                            ((tk[1][0] in ["-", "+"]) and (tk[1][1].isdigit()))):
                        if (arguments[2]):    # fix Lemma
                            if (tk[1] != tk[2]):
                                acc[accName.index("Lchanged")] += 1
                                acc[accName.index("LrepTAG")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "LrepTAG", tk[2], tk[1], sep="\t", file=repfile)
                                tk[2] = tk[1]
                        if (arguments[3]):    # fix Features
                            if (tk[5] not in ["NumType=Card", "_"]):
                                acc[accName.index("Fchanged")] += 1
                                acc[accName.index("FrepTAG")] += 1
                                if (not arguments[4]):
                                    print(b[0], tk[0], tk[1], "FrepTAG", tk[5], "NumType=Card", sep="\t", file=repfile)
                                tk[5] = "NumType=Card"
                    # check Close POS tags (ADP, ADV, CCONJ, DET, PRON, SCONJ)
                    elif (tk[3] in lexCloseTags):
                        lowForm = tk[1].lower()
                        options = lex.pget(lowForm, tk[3])
                        if (len(options) == 0):                       ### not found
                            if (arguments[2]):    # fix Lemma
                                if (tk[1] != tk[2]):
                                    acc[accName.index("Lchanged")] += 1
                                    acc[accName.index("LnoLEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "LnoLEX", tk[2], tk[1], sep="\t", file=repfile)
                                    tk[2] = tk[1]
                            if (arguments[3]):    # fix Features
                                if (tk[5] != "_"):
                                    acc[accName.index("Fchanged")] += 1
                                    acc[accName.index("FnoLEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "FnoLEX", tk[5], "_", sep="\t", file=repfile)
                                    tk[5] = "_"
                        elif (len(options) == 1):                     ### single option
                            if (arguments[2]):    # fix Lemma
                                if (options[0][0] != tk[2]):
                                    acc[accName.index("Lchanged")] += 1
                                    acc[accName.index("L1LEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "L1LEX", tk[2], options[0][0], sep="\t", file=repfile)
                                    tk[2] = options[0][0]
                            if (arguments[3]):    # fix Features
                                if (options[0][2] != tk[5]):
                                    acc[accName.index("Fchanged")] += 1
                                    acc[accName.index("F1LEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "F1LEX", tk[5], options[0][2], sep="\t", file=repfile)
                                    tk[5] = options[0][2]
                        elif (len(options) > 1):                     ### multiple option
                            lemmas, guess = [], "x"*100
                            for o in options:
                                lemmas.append(o[0])
                                if (len(o[0]) < len(guess)):
                                    guess = o[0]
                            if (arguments[2]):    # fix Lemma
                                if (tk[2] not in lemmas):
                                    acc[accName.index("Lchanged")] += 1
                                    acc[accName.index("LmLEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "LmLEX", tk[2], guess, sep="\t", file=repfile)
                                    tk[2] = guess
                            feats, guess = [], "x"*100
                            for o in options:
                                feats.append(o[2])
                                if (tk[3] in ["DET", "PRON"]) and ("Person" in o[2]) and ("Person" not in guess):
                                    guess = o[2]
                                elif (tk[3] in ["DET", "PRON"]) and ("Person" in o[2]) and ("Person" in guess) and (len(o[2]) < len(guess)):
                                    guess = o[2]
                            if (arguments[3]):    # fix Features
                                if (tk[5] not in feats):
                                    acc[accName.index("Fchanged")] += 1
                                    acc[accName.index("FmLEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "FmLEX", tk[5], guess, sep="\t", file=repfile)
                                    tk[5] = guess
                    # check Open POS tags (ADJ, INTJ, NOUN, NUM)
                    elif (tk[3] in lexOpenTags):
                        lowForm = tk[1].lower()
                        options = lex.pget(lowForm, tk[3])
                        if (len(options) == 0):                       ### not found
                            continue
                        elif (len(options) == 1):                     ### single option
                            if (arguments[2]):    # fix Lemma
                                if (options[0][0] != tk[2]):
                                    acc[accName.index("Lchanged")] += 1
                                    acc[accName.index("L1LEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "L1LEX", tk[2], options[0][0], sep="\t", file=repfile)
                                    tk[2] = options[0][0]
                            if (arguments[3]):    # fix Features
                                if (options[0][2] != tk[5]):
                                    acc[accName.index("Fchanged")] += 1
                                    acc[accName.index("F1LEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "F1LEX", tk[5], options[0][2], sep="\t", file=repfile)
                                    tk[5] = options[0][2]
                        elif (len(options) > 1):                     ### multiple option
                            lemmas, guess = [], "x"*100
                            for o in options:
                                lemmas.append(o[0])
                                if (len(o[0]) < len(guess)):
                                    guess = o[0]
                            if (arguments[2]):    # fix Lemma
                                if (tk[2] not in lemmas) and (guess[:5] != "xxxxx"):
                                    acc[accName.index("Lchanged")] += 1
                                    acc[accName.index("LmLEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "LmLEX", tk[2], guess, sep="\t", file=repfile)
                                    tk[2] = guess
                            feats, guess = [], "x"*100
                            for o in options:
                                feats.append(o[2])
                                if (len(o[2]) < len(guess)):
                                    guess = o[2]
                            if (arguments[3]):    # fix Features
                                if (tk[5] not in feats) and (guess[:5] != "xxxxx"):
                                    acc[accName.index("Fchanged")] += 1
                                    acc[accName.index("FmLEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "FmLEX", tk[5], guess, sep="\t", file=repfile)
                                    tk[5] = guess
                    # check VERB and AUX POS tags
                    elif (tk[3] in lexVerbTags):
                        lowForm = tk[1].lower()
                        options = lex.pget(lowForm, tk[3])
                        if (len(options) == 0):                       ### not found
                            continue
                        elif (len(options) == 1):                     ### single option
                            if (arguments[2]):    # fix Lemma
                                if (options[0][0] != tk[2]):
                                    acc[accName.index("Lchanged")] += 1
                                    acc[accName.index("L1LEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "L1LEX", tk[2], options[0][0], sep="\t", file=repfile)
                                    tk[2] = options[0][0]
                            if (arguments[3]):    # fix Features
                                if (options[0][2] != tk[5].replace("|Voice=Pass", "")):
                                    acc[accName.index("Fchanged")] += 1
                                    acc[accName.index("F1LEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "F1LEX", tk[5], options[0][2], sep="\t", file=repfile)
                                    tk[5] = options[0][2]
                        elif (len(options) > 1):                     ### multiple option
                            lemmas, guess = [], "x"*100
                            for o in options:
                                lemmas.append(o[0])
                                if (len(o[0]) < len(guess)):
                                    guess = o[0]
                            if (arguments[2]):    # fix Lemma
                                if (tk[2] not in lemmas) and (guess[:5] != "xxxxx"):
                                    acc[accName.index("Lchanged")] += 1
                                    acc[accName.index("LmLEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "LmLEX", tk[2], guess, sep="\t", file=repfile)
                                    tk[2] = guess
                            feats, guess = [], "x"*100
                            for o in options:
                                feats.append(o[2])
                                if ("Person=3" in o[2]) and ("Person=3" not in guess):
                                    guess = o[2]
                                elif ("Person=3" in o[2]) and ("Person=3" in guess):
                                    if (len(o[2]) < len(guess)):
                                        guess = o[2]
                            if (arguments[3]):    # fix Features
                                if (tk[5].replace("|Voice=Pass", "") not in feats) and (guess[:5] != "xxxxx"):
                                    acc[accName.index("Fchanged")] += 1
                                    acc[accName.index("FmLEX")] += 1
                                    if (not arguments[4]):
                                        print(b[0], tk[0], tk[1], "FmLEX", tk[5], guess, sep="\t", file=repfile)
                                    tk[5] = guess

            print_reps(repfile, accName, acc)
            base.printNoHeader(outfile)
            repfile.close()
            outfile.close()

fixLemmaFeatures()



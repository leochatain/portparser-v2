#################################################
### Post Processing Program to Portparser.v3
#################################################
#
#  (c) Lucelene Lopes 2025
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
    abbr = []
    for line in infile:
        if (line[0] == "#"):
            continue
        buf = line[:-1].split("\t")
        if (buf[1] == "abbr"):
            abbr.append([buf[0], buf[2], buf[3], buf[4]])
    return abbr

#################################################
### Function - Check if word is in the abbreviation
#################################################
def isAbbr(listAbbr, form):
    for a in listAbbr:
        if (form == a[0]):
            return True
    return False

#################################################
### Function - get info word is in an abbreviation list
#################################################
def isWithin(listAbbr, form):
    for a in listAbbr:
        if (form == a[0]):
            return a[1],a[2],a[3]
    return None, None, None

#################################################
### Function - Print a frequency list
#################################################
def print_reps(repfile, accName, acc):
    print("\n==========================================================\n", file=repfile)
    for i in range(len(acc)):
        print("{:8} - fixed: {:6>}".format(accName[i], acc[i]), file=repfile)
        print("{:8} - fixed: {:6>}".format(accName[i], acc[i]))

#################################################
### Function - fix upper letters in coumpound words
#################################################
def fixCompoundUpper(form, lemma, upos, feats):
    if (upos in ["PROPN", "SYM", "X", "PUNCT"]):
        return upos, form, "_"
    else:
        lemma = lemma.lower()
        # # deal with the lemma
        # dashesF = form.count("-")
        # dashesL = lemma.count("-")
        # if (dashesF == dashesL):
        #     buf = lemma
        #     bits = []
        #     for i in range(dashesL):
        #         dash = buf.index("-")
        #         bits.append(buf[:dash])
        #         buf = buf[dash+1:]
        #         for j in range(1,len(bits[-1])):
        #             if (bits[-1][j].isupper()):
        #                 bits[-1] = bits[-1][:j]+bits[-1][j].lower()+bits[-1][j+1:]
        #     lemma = bits[0]
        #     for i in range(1,len(bits)):
        #         lemma += "-"+bits[i]
        #     lemma += "-"+buf
        # deal with the features
        #### not yet
        return upos, lemma, feats

#################################################
### Function - assemble feats
#################################################
def featsFull(feat, abbr=False, extpos="", voicepass=False, prontype="", verbform="", numtype=""):
    def ignoreCase(f):
        return f.lower()
    # disassemble the string
    if (feat == "_"):
        feats = []
    else:
        feats = feat.split("|")
    # deal with Abbr=Yes
    if (abbr) and ("Abbr=Yes" not in feats):
        feats.append("Abbr=Yes")
    if (not abbr) and ("Abbr=Yes" in feats):
        feats.remove("Abbr=Yes")
    # deal with ExtPos=
    if (extpos != "") and ("ExtPos="+extpos not in feats):
        feats.append("ExtPos="+extpos)
    to_rem = []
    for f in feats:
        if (f[:7] == "ExtPos=") and (f != "ExtPos="+extpos):
            to_rem.append(f)
    for trf in to_rem:
        feats.remove(trf)
    # deal with Voice=Pass
    if (voicepass) and ("Voice=Pass" not in feats):
        feats.append("Voice=Pass")
    if (not voicepass) and ("Voice=Pass" in feats):
        feats.remove("Voice=Pass")
    # deal with PronType=
    if (prontype != None):
        if (prontype != "") and ("PronType="+prontype not in feats):
            feats.append("PronType="+prontype)
        to_rem = []
        for f in feats:
            if (f[:9] == "PronType=") and (f != "PronType="+prontype):
                to_rem.append(f)
        for trf in to_rem:
            feats.remove(trf)
    # deal with VerbForm=
    if (verbform != None):
        if (verbform != "") and ("VerbForm="+verbform not in feats):
            feats.append("VerbForm="+verbform)
        to_rem = []
        for f in feats:
            if (f[:9] == "VerbForm=") and (f != "VerbForm="+verbform):
                to_rem.append(f)
        for trf in to_rem:
            feats.remove(trf)
    # deal with NumType=
    if (numtype != None):
        if (numtype != "") and ("NumType="+numtype not in feats):
            feats.append("NumType="+numtype)
        to_rem = []
        for f in feats:
            if (f[:8] == "NumType=") and (f != "NumType="+numtype):
                to_rem.append(f)
        for trf in to_rem:
            feats.remove(trf)
    # assemble the string
    if (feats == []):
        return "_"
    else:
        feats.sort(key=ignoreCase)
        ans = ""
        for f in feats:
            ans += f+"|"
        return ans[:-1]

#################################################
### Function - locate the fixed heads in the sentence
#################################################
def locateExtPos(tks):
    fixeds = []
    for tk in tks:
        if (tk[7] == "fixed") and (tk[6] not in fixeds):
            fixeds.append(tk[6])
    return fixeds

#################################################
### Function - check options separating lemma and features
#################################################
def sepLEMMA_FEATS(options):
    opLEMMA = []
    opFEATS = []
    for o in options:
        if (o[0] not in opLEMMA):
            opLEMMA.append(o[0])
        if (o[2] not in opFEATS):
            opFEATS.append(o[2])
    return opLEMMA, opFEATS

#################################################
### Main Function - Postprocess fix of UPOS, LEMMA and FEATS
#################################################
def posprocFix():
    # if compound word                                 # fix - replace upper case in Lemma only
    # if the word is within known unambiguous abbr     # correct arbitrarily
    lexOutOfTags   = ["PROPN", "PUNCT", "SYM", "X"]    # correct arbitrarily
    lexCloseTags   = ["ADP", "ADV", "CCONJ", "SCONJ"]  # correct if unique in lex, erase feats (features are impossible)
    lexPronDetTags = ["DET", "PRON"]                   # correct if unique in lex, require 'PronType', erase impossible features
    lexOpenTags    = ["ADJ", "INTJ", "NOUN", "NUM"]    # correct if unique in lex, erase impossible features
    lexVerbTags    = ["AUX", "VERB"]                   # correct if unique in lex, require 'VerbForm', erase impossible features
    digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    ordinalsignsFem = ['ª', 'a']
    ordinalsignsMasc = ['º', '°', 'o']
    ordinalsignsNeut = ['.']

    if (len(sys.argv) == 1):
        arguments = ["xxx.conllu", "yyy.conllu", True, True, False] # output file, input file, do lemmas, do features, run quiet(false)
        print("Assumindo default: 'yyy.conllu' como arquivo de entrada, 'xxx.conllu' como arquivo de saída, e executando correção de lemas e features.")
    else:
        arguments = parseOptions(sys.argv)
    if (arguments != None):
        if (arguments[0] == ""):
            print("Assumindo 'xxx.conllu' como arquivo de saída")
            arguments[0] = 'xxx.conllu'
        if not os.path.isfile(arguments[1]):
            print(arguments[1], "Arquivo de entrada inválido - por favor corrija e tente novamente")
        else:
            outfile = open(arguments[0], "w")
            if (not arguments[4]): repfile = open(arguments[0]+".rep.tsv", "w")
            base = conlluFile(arguments[1])
            # counters
            accName = ["Pchanged", "Lchanged", "Fchanged"]
            acc = [0]*len(accName)
            # usual Abbr (read from .tsv with "form", "kind", "UPOS", "LEMMA", "FEATS")
            usualAbbr = getUsualAbbr()
            # main loop
            for i in range(base.getS()):
                b = base.getSentByIndex(i)
                fixeds = locateExtPos(b[4])
                for tk in b[4]:
                    # level down contracted tokens info, but ID and FORM
                    if ("-" in tk[0]):
                        tk[2], tk[3], tk[4], tk[5], tk[6], tk[7], tk[8], tk[9] = "-", "-", "-", "-", "-", "-", "-", "-"
                        continue
                    # fix out of lexikon tokens
                    if (tk[3] in lexOutOfTags):
                        if (tk[3] in ["PROPN", "PUNCT", "SYM"]):
                            pos, lem, feat = tk[3], tk[1], "_"
                        elif (tk[3] == "X"):
                            if ("Foreign=Yes" in tk[5]):
                                pos, lem, feat = tk[3], tk[1], "Foreign=Yes"
                            else:
                                pos, lem, feat = tk[3], tk[1], "_"
                    # fix only lemma in compound words
                    elif ("-" in tk[1]):
                        pos, lem, feat = fixCompoundUpper(tk[1], tk[2], tk[3], tk[5])
                    # fix known abbreviations
                    elif (isAbbr(usualAbbr, tk[1].lower())) and (tk[3] in ["ADP", "NOUN"]):
                        pos, lem, feat = isWithin(usualAbbr, tk[1].lower())
                    # fix numerical NUM, ADJ, NOUN
                    elif (tk[3] in ["ADJ", "NOUN", "NUM"]) and (not tk[1].isalpha()):
                        if (tk[3] == "NOUN"):
                            pos, lem, feat = tk[3], tk[1], "_"
                        elif (tk[3] == "ADJ"):
                            if (tk[1][-1] in ordinalsignsMasc):
                                pos, lem, feat = tk[3], tk[1], "Gender=Masc|NumType=Ord"
                            elif (tk[1][-1] in ordinalsignsFem):
                                pos, lem, feat = tk[3], tk[1], "Gender=Fem|NumType=Ord"
                            elif (tk[1][-1] in ordinalsignsNeut):
                                pos, lem, feat = tk[3], tk[1], "NumType=Ord"
                            else:
                                pos, lem, feat = tk[3], tk[1], "_"
                        elif (tk[3] == "NUM"):
                            if (tk[1][-1] in ordinalsignsMasc):
                                pos, lem, feat = tk[3], tk[1], "Gender=Masc|NumType=Ord"
                            elif (tk[1][-1] in ordinalsignsFem):
                                pos, lem, feat = tk[3], tk[1], "Gender=Fem|NumType=Ord"
                            elif (tk[1][-1] in ordinalsignsNeut):
                                pos, lem, feat = tk[3], tk[1], "NumType=Ord"
                            else:
                                pos, lem, feat = tk[3], tk[1], "NumType=Card"
                    # fix closed tags - ADP, ADV, CCONJ, SCONJ
                    elif (tk[3] in lexCloseTags):
                        options = lex.pget(tk[1].lower(), tk[3])
                        opLEMMA, opFEATS = sepLEMMA_FEATS(options)
                        abbr = ("Abbr=Yes" in tk[5]) and (tk[1].lower() != tk[2])
                        if (tk[0] in fixeds):
                            if   (tk[7] == "cc"):
                                extpos = "CCONJ"
                            elif (tk[7] == "advmod"):
                                extpos = "ADV"
                            elif (tk[7] == "case"):
                                extpos = "ADP"
                            elif (tk[7] == "mark"):
                                extpos = "SCONJ"
                            elif (tk[3] == "PRON"):
                                extpos = "PRON"
                            else:
                                extpos = tk[3]
                        else:
                            extpos = ""
                        if (len(options) == 0):      # out of the lex
                            pos, lem, feat = tk[3], tk[2].lower(), featsFull("_", abbr, extpos=extpos)
                        elif (len(options) == 1):    # unambiguous in the lex
                            pos, lem, feat = tk[3], options[0][0], featsFull(options[0][2], abbr, extpos=extpos)
                        else:                        # ambiguous in the lex - do nothing
                            pos = tk[3]
                            lem = opLEMMA[0] if (len(opLEMMA) == 1) else tk[2].lower()
                            feat = opFEATS[0] if (len(opFEATS) == 1) else tk[5]
                    # fix Pron and Det tags - PRON, DET
                    elif (tk[3] in lexPronDetTags):
                        options = lex.pget(tk[1].lower(), tk[3])
                        opLEMMA, opFEATS = sepLEMMA_FEATS(options)
                        abbr = ("Abbr=Yes" in tk[5]) and ((tk[1].lower() != tk[2]) or ("/" in tk[1]) or ("." in tk[1]))
                        if (tk[0] in fixeds):
                            if   (tk[7] == "cc"):
                                extpos = "CCONJ"
                            elif (tk[7] == "advmod"):
                                extpos = "ADV"
                            elif (tk[7] == "case"):
                                extpos = "ADP"
                            elif (tk[7] == "mark"):
                                extpos = "SCONJ"
                            elif (tk[3] == "PRON"):
                                extpos = "PRON"
                            else:
                                extpos = tk[3]
                        else:
                            extpos = ""
                        if ("PronType" in tk[5]):
                            idx = tk[5].index("PronType=")+9
                            prontype = tk[5][idx:idx+3]
                        elif (tk[3] == "PRON"):
                            prontype = "Dem"
                        elif (tk[3] == "DET"):
                            prontype = "Art"
                        if (len(options) == 0):      # out of the lex
                            pos, lem, feat = tk[3], tk[2].lower(), featsFull(tk[5], abbr, extpos=extpos, prontype=prontype)
                        elif (len(options) == 1):    # unambiguous in the lex
                            pos, lem, feat = tk[3], options[0][0], featsFull(options[0][2], abbr, extpos=extpos, prontype=None)
                        else:                        # ambiguous in the lex - do nothing
                            pos = tk[3]
                            lem = opLEMMA[0] if (len(opLEMMA) == 1) else tk[2].lower()
                            feat = opFEATS[0] if (len(opFEATS) == 1) else tk[5]
                    # fix Open tags - ADJ, INTJ, NOUN, NUM
                    elif (tk[3] in lexOpenTags):
                        options = lex.pget(tk[1].lower(), tk[3])
                        opLEMMA, opFEATS = sepLEMMA_FEATS(options)
                        abbr = ("Abbr=Yes" in tk[5]) and ((tk[1].lower() != tk[2]) or ("/" in tk[1]) or ("." in tk[1]))
                        if (tk[0] in fixeds):
                            if   (tk[7] == "cc"):
                                extpos = "CCONJ"
                            elif (tk[7] == "advmod"):
                                extpos = "ADV"
                            elif (tk[7] == "case"):
                                extpos = "ADP"
                            elif (tk[7] == "mark"):
                                extpos = "SCONJ"
                            elif (tk[3] == "PRON"):
                                extpos = "PRON"
                            else:
                                extpos = tk[3]
                        else:
                            extpos = ""
                        if ("VerbForm=Part" in tk[5]) and (tk[3] == "ADJ"):
                            verbform = "Part"
                        else:
                            verbform = ""
                        if ("NumType=Ord" in tk[5]) and (tk[3] in ["ADJ", "NUM"]):
                            numtype = "Ord"
                        elif ("NumType=Card" in tk[5]) and (tk[3] == "NUM"):
                            numtype = "Card"
                        else:
                            numtype = ""
                        if (len(options) == 0):      # out of the lex
                            pos, lem, feat = tk[3], tk[2].lower(), featsFull(tk[5], abbr, extpos=extpos, verbform=verbform, numtype=numtype)
                        elif (len(options) == 1):    # unambiguous in the lex
                            pos, lem, feat = tk[3], options[0][0], featsFull(options[0][2], abbr, extpos=extpos, verbform=None, numtype=None)
                        else:                        # ambiguous in the lex - do nothing
                            pos = tk[3]
                            lem = opLEMMA[0] if (len(opLEMMA) == 1) else tk[2].lower()
                            feat = opFEATS[0] if (len(opFEATS) == 1) else tk[5]
                    # fix Verb tags - AUX, VERB
                    elif (tk[3] in lexVerbTags):
                        options = lex.pget(tk[1].lower(), tk[3])
                        opLEMMA, opFEATS = sepLEMMA_FEATS(options)
                        abbr = ("Abbr=Yes" in tk[5]) and (tk[1].lower() != tk[2])
                        if (tk[0] in fixeds):
                            if   (tk[7] == "cc"):
                                extpos = "CCONJ"
                            elif (tk[7] == "advmod"):
                                extpos = "ADV"
                            elif (tk[7] == "case"):
                                extpos = "ADP"
                            elif (tk[7] == "mark"):
                                extpos = "SCONJ"
                            elif (tk[3] == "PRON"):
                                extpos = "PRON"
                            else:
                                extpos = tk[3]
                        else:
                            extpos = ""
                        if   ("VerbForm=Inf" in tk[5]):
                            verbform = "Inf"
                        elif ("VerbForm=Ger" in tk[5]):
                            verbform = "Ger"
                        elif ("VerbForm=Part" in tk[5]):
                            verbform = "Part"
                        elif ("VerbForm=Fin" in tk[5]):
                            verbform = "Fin"
                        else:
                            if (tk[1][-1].lower() == "r"):
                                verbform = "Inf"
                            else:
                                verbform = "Fin"
                        if ("Voice=Pass" in tk[5]):
                            voicepass = True
                        else:
                            voicepass = False
                        if (len(options) == 0):      # out of the lex
                            pos, lem, feat = tk[3], tk[2].lower(), featsFull(tk[5], abbr, extpos=extpos, verbform=verbform, voicepass=voicepass)
                        elif (len(options) == 1):    # unambiguous in the lex
                            pos, lem, feat = tk[3], options[0][0], featsFull(options[0][2], abbr, extpos=extpos, verbform=None, voicepass=voicepass)
                        else:                        # ambiguous in the lex - do nothing
                            pos = tk[3]
                            lem = opLEMMA[0] if (len(opLEMMA) == 1) else tk[2].lower()
                            feat = opFEATS[0] if (len(opFEATS) == 1) else tk[5]
                    # do reports and change
                    if (pos != tk[3]):
                        print(b[0], tk[0], tk[1], tk[3], "UPOS", tk[3], pos, sep="\t", file=repfile)
                        acc[accName.index("Pchanged")] += 1
                        tk[3] = pos
                    if (lem != tk[2]):
                        print(b[0], tk[0], tk[1], tk[3], "LEMMA", tk[2], lem, sep="\t", file=repfile)
                        acc[accName.index("Lchanged")] += 1
                        tk[2] = lem
                    if (feat != tk[5]):
                        if ("ExtPos=" not in feat):
                            print(b[0], tk[0], tk[1], tk[3], "FEATS", tk[5], feat, sep="\t", file=repfile)
                            acc[accName.index("Fchanged")] += 1
                        tk[5] = feat
            if (not arguments[4]): print_reps(repfile, accName, acc)
            if (not arguments[4]): repfile.close()
            base.printNoHeader(outfile)
            outfile.close()

posprocFix()

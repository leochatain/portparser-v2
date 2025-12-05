# portTokenizer - tokenizador de sentenças em Portugues para um arquivo CoNLL-U
#
# Este programa recebe um arquivo de entrada textual com uma sentença
#    por linha e gera um arquivo CoNLL-U devidamente tokenizado.
#
# Este programa utiliza um léxico de Português, PortiLexicon-UD através da
#    chamada da classe UDlexPT incluída no arquivo "lexikon.py" disponível
#    em conjunto com este arquivo ("portTok.py") e com os arquivos textuais
#    do léxico ("ADJ.tsv", "ADP.tsv", "ADV.tsv", "AUX.tsv", "CCONJ.tsv", 
#    "DET.tsv", "INTJ.tsv", "NOUN.tsv", "NUM.tsv", "PRON.tsv", "SCONJ.tsv", 
#    "VERB.tsv", "WORDmaster.txt").
#
# Opções:
#
# -h help
# -o output file
# -p preserve as one token itemizations as a) b) and i) ii)
# -m matches the paired punctuations
# -t trims headlines (heuristic)
# -s sentence id (sid) model
#
# Exemplo de utilização:
#
# portTok -o sents.conllu -p -m -t -s S000000 sents.txt
#
# Busca as sentenças no arquivo 'sents.txt',
#   preserva tokens em itens como a) b) i) ii),
#   corrige pontuações casadas (aspas, parenteses, etc),
#   remove possíveis MANCHETES que precedem as frases,
#   usa S000000 como modelo de identificador de sentença e
#   salva as sentenças devidamente tokenizadas no arquivo 'sents.conllu'
#
# last edit: 10/05/2025
# created by Lucelene Lopes - lucelene@gmail.com

import os
import argparse

from lexikon import UDlexPT

lex = UDlexPT()


#################################################
### Captura de argumentos da linha de comando
#################################################
def _existing_file(path: str) -> str:
    """Argparse type that validates file exists."""
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"O arquivo '{path}' não foi encontrado")
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments using argparse."""
    parser = argparse.ArgumentParser(
        prog="portTok",
        description="Tokenizador de sentenças em Português para arquivo CoNLL-U",
        epilog="Exemplo: portTok -o sents.conllu --no-preserve -m -t -s S000000 sents.txt"
    )
    
    parser.add_argument(
        "input_file",
        nargs="?",
        default="sents.txt",
        type=_existing_file,
        help="Arquivo de entrada com sentenças (uma por linha) (default: %(default)s)"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_file",
        default="sents.conllu",
        help="Arquivo de saída CoNLL-U (default: %(default)s)"
    )
    parser.add_argument(
        "-p", "--preserve", "--no-preserve",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="preserve",
        help="Preserva tokens de itemização como a) b) i) ii) (default: %(default)s)"
    )
    parser.add_argument(
        "-m", "--match", "--no-match",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="match",
        help="Corrige pontuações casadas (aspas, parênteses, etc) (default: %(default)s)"
    )
    parser.add_argument(
        "-t", "--trim", "--no-trim",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="trim",
        help="Remove possíveis manchetes que precedem as frases (default: %(default)s)"
    )
    parser.add_argument(
        "-s", "--sid",
        dest="sid_model",
        default="S000000",
        help="Modelo de identificador de sentença (default: %(default)s)"
    )
    
    return parser.parse_args(argv)


#############################################################################
#  Increment a name index
#############################################################################
def nextName(name: str) -> str:
    # increment the digits from right to left
    ans = ""
    while name != "":
        digit, name = name[-1], name[:-1]
        if digit == "9":
            ans = "0" + ans
        elif digit == "8":
            ans = "9" + ans
            return name+ans
        elif digit == "7":
            ans = "8" + ans
            return name+ans
        elif digit == "6":
            ans = "7" + ans
            return name+ans
        elif digit == "5":
            ans = "6" + ans
            return name+ans
        elif digit == "4":
            ans = "5" + ans
            return name+ans
        elif digit == "3":
            ans = "4" + ans
            return name+ans
        elif digit == "2":
            ans = "3" + ans
            return name+ans
        elif digit == "1":
            ans = "2" + ans
            return name+ans
        elif digit == "0":
            ans = "1" + ans
            return name+ans
        else:
            ans = "1" + ans
            return name+ans
    return "overflow"+ans

#############################################################################
#  Trim the unwanted bits at the sentence - trimIt (step 1)
#############################################################################
def trimIt(s: str) -> str:
    # generate the bits separated by blanks trimming blanks before, after, and multiples
    bits = s.strip().replace("  ", " ").replace("  ", " ").split(" ")
    start = 0
    # remove itemize symbols
    if (bits[0] in ["*", "★", "-", "—", "–", ">", "."]):
        if (len(bits) == 1):
            return ""
        else:
            start = 1
    # remove (BELO HORIZONTE) ... kind
    if (bits[start][0] == "(") and (bits[-1][-1] != ")"):
        for i in range(len(bits)):
            if (bits[i][-1] == ")"):
                start = i+1
                break
    # remove CRONOLOGIA .... kind
    i = start
    while (i<len(bits)):
        if (bits[i].isupper()):
            start = i
            i += 1
        else:
            break
    if ((len(bits[start]) > 1) and (bits[start].isupper())) and \
        (start+1 < len(bits)):              # make sure the next after all upper
        if (bits[start+1][0].isupper()):    #   is not a beginning of sentence
            start += 1
    ans = bits[start]
    for i in range(start+1,len(bits)):
        ans += " "+bits[i]
    return ans

#############################################################################
#  Tag the itemize prompts and double paragraph with //*||*\\ or //*|(|*\\ - tagIt (step 2)
#############################################################################
def tagIt(s: str) -> str:
    romans = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", \
              "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", \
              "xix", "xx", "xxi", "xxii", "xxiii", "xxiv", "xxvi", "xxvii", \
              "xxviii", "xxix", "xxx", "xxxi", "xxxii", "xxxiii", "xxxiv", "xxxv"]
                # limited up to 35
    letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", \
               "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
                # limited to single letters
    itemizePrompts = romans+letters
    # go over the sent string looking for itemize prompt patern
    ans = ""
    bits = s.split(" ")
    for i in range(len(bits)):
        if (bits[i][-1] == ")"):
            if (bits[i][0] == "("):
                if (bits[i][1:-1] in itemizePrompts):
                    ans += "//*||*\\\\"+bits[i]+"//*||*\\\\ "
                else:
                    ans += bits[i]+" "
            else:
                if (bits[i][0:-1] in itemizePrompts):
                    ans += "//*|(|*\\\\"+bits[i]+"//*||*\\\\ "
                else:
                    ans += bits[i]+" "
        elif (bits[i] == "§§"):
            ans += "//*||*\\\\"+bits[i]+"//*||*\\\\ "
        else:
            ans += bits[i]+" "
    return ans

#############################################################################
#  Clear matching punctuations - punctIt (step 3)
#############################################################################
def punctIt(s: str) -> str:
    def notAlphaNum(sent: str) -> bool:
        ans = True
        for c in sent:
            if c.isalpha() or c.isdigit():
                ans = False
                break
        return ans
    doubleQuotes = s.count('"')
    singleQuotes = s.count("'")
    openParentes = s.count("(")
    closParentes = s.count(")")
    openBrackets = s.count("[")
    closBrackets = s.count("]")
    openCurBrace = s.count("{")
    closCurBrace = s.count("}")
    openAligator = s.count("<")
    closAligator = s.count(">")
    if  ((doubleQuotes == 2 ) and (s[0] == '"') and (s[-1] == '"')) or \
        ((singleQuotes == 2 ) and (s[0] == "'") and (s[-1] == "'")) or \
        ((openParentes == 1 ) and (closParentes == 1 ) and (s[0] == "(") and (s[-1] == ")")) or \
        ((openBrackets == 1 ) and (closBrackets == 1 ) and (s[0] == "[") and (s[-1] == "]")) or \
        ((openCurBrace == 1 ) and (closCurBrace == 1 ) and (s[0] == "{") and (s[-1] == "}")) or \
        ((openAligator == 1 ) and (closAligator == 1 ) and (s[0] == "<") and (s[-1] == ">")):
        S = s[1:-1].strip()
    else:
        S = s.strip()
    if (doubleQuotes % 2 != 0):
        S = S.replace('"', '')
    if (singleQuotes % 2 != 0):
        S = S.replace("'", "")
    if (openParentes != closParentes):
        S = S.replace("(", "").replace(")", "")
    if (openBrackets != closBrackets):
        S = S.replace("[", "").replace("]", "")
    if (openCurBrace != closCurBrace):
        S = S.replace("{", "").replace("}", "")
    if (openAligator != closAligator):
        S = S.replace("<", "").replace(">", "")
    if (S == "") or (notAlphaNum(S) and ()):
        return ""
    elif (S[-2:] == "..") and S[-3:] != "...":
        S = S[:-2]+"."
    elif (S[-2:] in [":.", ";."]):
        S = S[:-2]+"."
    elif (S[-1] not in [".", "!", "?", ":", ";"]):
        if (S[-1] in ["'", '"', ")", "]", "}", ">"]) and (S[-2] in [".", "!", "?", ":", ";"]):
            S = S[:-2]+S[-1]+S[-2]
        else:
            S = S+"."
    return S.replace("  ", " ").replace("  ", " ")

#############################################################################
#  Decide if ambiguous tokens are contracted or not - desambIt (within step 4)
#############################################################################
def desambIt(token: str, bits: list[str], i: int, lastField: str, s: str, SID: str, tokens: list[list[str]]) -> None:
    def stripWord(w: str) -> str:
        start, end = 0, len(w)
        for j in range(len(w)):
            if (not w[j].isalpha()):
                start = j+1
            else:
                break
        for j in range(start,len(w)):
            if (not w[j].isalpha()):
                end = j
                break
        return w[start:end].lower()
    # nos - em os - nos
    if (token.lower() == "nos"):
        if (i > 0):
            preVERB = lex.pexists(stripWord(bits[i-1]), "VERB") or lex.pexists(stripWord(bits[i-1]), "AUX")
        else:
            preVERB = False
        if (i < len(bits)-1):
            posVERB = lex.pexists(stripWord(bits[i+1]), "VERB") or lex.pexists(stripWord(bits[i+1]), "AUX")
            posNOUNDET = lex.pexists(stripWord(bits[i+1]), "NOUN") or lex.pexists(stripWord(bits[i+1]), "ADJ") or lex.pexists(stripWord(bits[i+1]), "DET")
            if (posNOUNDET):
                possible = lex.pget(stripWord(bits[i+1]), "NOUN")+lex.pget(stripWord(bits[i+1]), "ADJ")+lex.pget(stripWord(bits[i+1]), "DET")
                agree = False
                for feats in possible:
                    if ("Number=Sing" not in feats[2]) and ("Gender=Fem" not in feats[2]):
                        agree = True
                        break
                if (not agree):
                    posNOUNDET = False
        else:
            posVERB = False
            posNOUNDET = False
        if (posVERB and not posNOUNDET):
            tokens.append([token, lastField])  # don't break
        else:
            tokens.append([token, "c"+lastField])  # break
            if (token.isupper()):
                tokens.append(["EM","_"])
                tokens.append(["OS","_"])
            elif (token[0].isupper()):
                tokens.append(["Em","_"])
                tokens.append(["os","_"])
            else:
                tokens.append(["em","_"])
                tokens.append(["os","_"])
    # consigo - com si - consigo
    elif (token.lower() == "consigo"):
        if (i > 0):
            prePRONADV = lex.pexists(stripWord(bits[i-1]), "PRON") or lex.pexists(stripWord(bits[i-1]), "ADV")
        else:
            prePRONADV = False
        if (i < len(bits)-1):
            posVERB = lex.pexists(stripWord(bits[i+1]), "VERB") or lex.pexists(stripWord(bits[i+1]), "AUX")
        else:
            posVERB = False
        if (i < len(bits)-2):
            doQue = ((bits[i+1] == "do") and (bits[i+2] == "que")) or ((bits[i+1] == "sua"))
        else:
            doQue = False
        if ((prePRONADV) or (posVERB)) and (not doQue):
            tokens.append([token, lastField])  # don't break
        else:
            tokens.append([token, "c"+lastField])  # break
            if (token.isupper()):
                tokens.append(["COM","_"])
                tokens.append(["SI","_"])
            elif (token[0].isupper()):
                tokens.append(["Com","_"])
                tokens.append(["si","_"])
            else:
                tokens.append(["com","_"])
                tokens.append(["si","_"])
    # pra - para a - para
    elif (token.lower() == "pra"):
        if (i < len(bits)-1):
            posNOUNDET = lex.pexists(stripWord(bits[i+1]), "NOUN") or lex.pexists(stripWord(bits[i+1]), "ADJ") or lex.pexists(stripWord(bits[i+1]), "DET")
            if (posNOUNDET):
                possible = lex.pget(stripWord(bits[i+1]), "NOUN")+lex.pget(stripWord(bits[i+1]), "ADJ")+lex.pget(stripWord(bits[i+1]), "DET")
                agree = False
                for feats in possible:
                    if ("Number=Plur" not in feats[2]) and ("Gender=Masc" not in feats[2]):
                        agree = True
                        break
                if (not agree):
                    posNOUNDET = False
        else:
            posNOUNDET = False
        if (posNOUNDET):
            tokens.append([token, "c"+lastField])  # break
            if (token.isupper()):
                tokens.append(["PARA","_"])
                tokens.append(["A","_"])
            elif (token[0].isupper()):
                tokens.append(["Para","_"])
                tokens.append(["a","_"])
            else:
                tokens.append(["para","_"])
                tokens.append(["a","_"])
        else:
            tokens.append([token, lastField])  # don't break
    # pela - por a - pela
    elif (token.lower() == "pela"):
        if (i < len(bits)-1):
            posNOUNDET = lex.pexists(stripWord(bits[i+1]), "NOUN") or lex.pexists(stripWord(bits[i+1]), "ADJ") or lex.pexists(stripWord(bits[i+1]), "NUM") or lex.pexists(stripWord(bits[i+1]), "DET")
            properNOUNDIGIT = bits[i+1][0].isupper() or bits[i+1][0].isnumeric()
        else:
            posNOUNDET = False
            properNOUNDIGIT = False
        if (posNOUNDET) or (properNOUNDIGIT):
            tokens.append([token, "c"+lastField])  # break
            if (token.isupper()):
                tokens.append(["POR","_"])
                tokens.append(["A","_"])
            elif (token[0].isupper()):
                tokens.append(["Por","_"])
                tokens.append(["a","_"])
            else:
                tokens.append(["por","_"])
                tokens.append(["a","_"])
        else:
            tokens.append([token, lastField])  # don't break
    # pelas - por as - pelas
    elif (token.lower() == "pelas"):
        if (i < len(bits)-1):
            posNOUNDET = lex.pexists(stripWord(bits[i+1]), "NOUN") or lex.pexists(stripWord(bits[i+1]), "ADJ") or lex.pexists(stripWord(bits[i+1]), "NUM") or lex.pexists(stripWord(bits[i+1]), "DET")
            properNOUNDIGIT = bits[i+1][0].isupper() or bits[i+1][0].isnumeric()
        else:
            posNOUNDET = False
            properNOUNDIGIT = False
        if (posNOUNDET) or (properNOUNDIGIT):
            tokens.append([token, "c"+lastField])  # break
            if (token.isupper()):
                tokens.append(["POR","_"])
                tokens.append(["AS","_"])
            elif (token[0].isupper()):
                tokens.append(["Por","_"])
                tokens.append(["as","_"])
            else:
                tokens.append(["por","_"])
                tokens.append(["as","_"])
        else:
            tokens.append([token, lastField])  # don't break
    # pelo - por o - pelo
    elif (token.lower() == "pelo"):
        if (i > 0):
            preART = lex.pexists(stripWord(bits[i-1]), "DET")
            if (preART):
                possible = lex.pget(stripWord(bits[i-1]), "DET")
                agree = False
                for feats in possible:
                    if ("Number=Plur" not in feats[2]) and ("Gender=Fem" not in feats[2]):
                        agree = True
                        break
                if (not agree):
                    preART = False
                else:
                    preART = (stripWord(bits[i-1]) != "que") and (stripWord(bits[i-1]) != "dado") and (stripWord(bits[i-1]) != "tanto") and (stripWord(bits[i-1]) != "quanto") and (stripWord(bits[i-1]) != "mais")
        else:
            preART = False
        if (i < len(bits)-1):
            posNOUNDET = lex.pexists(stripWord(bits[i+1]), "NOUN") or lex.pexists(stripWord(bits[i+1]), "ADJ") or lex.pexists(stripWord(bits[i+1]), "DET")
            posLower = not bits[i+1][0].isupper()
            if (posNOUNDET):
                possible = lex.pget(stripWord(bits[i+1]), "NOUN")+lex.pget(stripWord(bits[i+1]), "ADJ")+lex.pget(stripWord(bits[i+1]), "DET")
                agree = False
                for feats in possible:
                    if ("Number=Plur" not in feats[2]) and ("Gender=Fem" not in feats[2]):
                        agree = True
                        break
                if (not agree):
                    posNOUNDET = False
        else:
            posNOUNDET = False
            posLower = True
        if (preART) and (not posNOUNDET) and (posLower):
            tokens.append([token, lastField])  # don't break
        else:
            tokens.append([token, "c"+lastField])  # break
            if (token.isupper()):
                tokens.append(["POR","_"])
                tokens.append(["O","_"])
            elif (token[0].isupper()):
                tokens.append(["Por","_"])
                tokens.append(["o","_"])
            else:
                tokens.append(["por","_"])
                tokens.append(["o","_"])
    # pelos - por os - pelos
    elif (token.lower() == "pelos"):
        if (i > 0):
            preART = lex.pexists(stripWord(bits[i-1]), "DET")
            if (preART):
                possible = lex.pget(stripWord(bits[i-1]), "DET")
                agree = False
                for feats in possible:
                    if ("Number=Sing" not in feats[2]) and ("Gender=Fem" not in feats[2]) and ("PronType=Art" in feats[2]):
                        agree = True
                        break
                if (not agree):
                    preART = False
                else:
                    preART = (stripWord(bits[i-1]) != "que") and (stripWord(bits[i-1]) != "dado") and (stripWord(bits[i-1]) != "tanto") and (stripWord(bits[i-1]) != "quanto") and (stripWord(bits[i-1]) != "mais")
        else:
            preART = False
        if (i < len(bits)-1):
            posNOUNDET = lex.pexists(stripWord(bits[i+1]), "NOUN") or lex.pexists(stripWord(bits[i+1]), "ADJ") or lex.pexists(stripWord(bits[i+1]), "DET")
            posLower = not bits[i+1][0].isupper()
            if (posNOUNDET):
                possible = lex.pget(stripWord(bits[i+1]), "NOUN")+lex.pget(stripWord(bits[i+1]), "ADJ")+lex.pget(stripWord(bits[i+1]), "DET")
                agree = False
                for feats in possible:
                    if ("Number=Sing" not in feats[2]) and ("Gender=Fem" not in feats[2]) and ("PronType=Art" in feats[2]):
                        agree = True
                        break
                if (not agree):
                    posNOUNDET = False
        else:
            posNOUNDET = False
            posLower = True
        if (preART) and (not posNOUNDET) and (posLower):
            tokens.append([token, lastField])  # don't break
        else:
            tokens.append([token, "c"+lastField])  # break
            if (token.isupper()):
                tokens.append(["POR","_"])
                tokens.append(["OS","_"])
            elif (token[0].isupper()):
                tokens.append(["Por","_"])
                tokens.append(["os","_"])
            else:
                tokens.append(["por","_"])
                tokens.append(["os","_"])

#############################################################################
#  Tokenizing - tokenizeIt (step 4)
#############################################################################
def tokenizeIt(s: str, SID: str) -> list[str]:
    removable = ["'", '"', "(", ")", "[", "]", "{", "}", "<", ">", \
                 "!", "?", ",", ";", ":", "=", "+", "*", "★", "|", "/", "\\", \
                 "&", "^", "_", "`", "'", "~", "%", "§"]
    ignored   = ["@", "#"]
    digits  = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    contracts = {"à":["a","a"],
                 "às":["a","as"],
                 "ao":["a", "o"],
                 "aos":["a", "os"],
                 "àquela":["a", "aquela"],
                 "àquelas":["a", "aquelas"],
                 "àquele":["a", "aquele"],
                 "àqueles":["a", "aqueles"],
                 "comigo":["com", "mim"],
                 "contigo":["com", "ti"],
                 "consigo":["com", "si"],
                 "conosco":["com", "nós"],
                 "convosco":["com", "vós"],
                 "da":["de", "a"],
                 "das":["de", "as"],
                 "do":["de", "o"],
                 "dos":["de", "os"],
                 "dali":["de", "ali"],
                 "daqui":["de", "aqui"],
                 "daí":["de", "aí"],
                 "dentre":["de", "entre"],
                 "desta":["de", "esta"],
                 "destas":["de", "estas"],
                 "deste":["de", "este"],
                 "destes":["de", "estes"],
                 "dessa":["de", "essa"],
                 "dessas":["de", "essas"],
                 "desse":["de", "esse"],
                 "desses":["de", "esses"],
                 "daquela":["de", "aquela"],
                 "daquelas":["de", "aquelas"],
                 "daquele":["de", "aquele"],
                 "daqueles":["de", "aqueles"],
                 "disto":["de", "isto"],
                 "disso":["de", "isso"],
                 "daquilo":["de", "aquilo"],
                 "dela":["de", "ela"],
                 "delas":["de", "elas"],
                 "dele":["de", "ele"],
                 "deles":["de", "eles"],
                 "doutra":["de", "outra"],
                 "doutras":["de", "outras"],
                 "doutro":["de", "outro"],
                 "doutros":["de", "outros"],
                 "dum":["de", "um"],
                 "duns":["de", "uns"],
                 "duma":["de", "uma"],
                 "dumas":["de", "umas"],
                 "na":["em", "a"],
                 "nas":["em", "as"],
                 "no":["em", "o"],
                 "nos":["em", "os"],
                 "nesta":["em", "esta"],
                 "nestas":["em", "estas"],
                 "neste":["em", "este"],
                 "nestes":["em", "estes"],
                 "nessa":["em", "essa"],
                 "nessas":["em", "essas"],
                 "nesse":["em", "esse"],
                 "nesses":["em", "esses"],
                 "naquela":["em", "aquela"],
                 "naquelas":["em", "aquelas"],
                 "naquele":["em", "aquele"],
                 "naqueles":["em", "aqueles"],
                 "nisto":["em", "isto"],
                 "nisso":["em", "isso"],
                 "naquilo":["em", "aquilo"],
                 "nela":["em", "ela"],
                 "nelas":["em", "elas"],
                 "nele":["em", "ele"],
                 "neles":["em", "eles"],
                 "noutra":["em", "outra"],
                 "noutras":["em", "outras"],
                 "noutro":["em", "outro"],
                 "noutros":["em", "outros"],
                 "num":["em", "um"],
                 "nuns":["em", "uns"],
                 "numa":["em", "uma"],
                 "numas":["em", "umas"],
                 "pela":["por", "a"],
                 "pelas":["por", "as"],
                 "pelo":["por", "o"],
                 "pelos":["por", "os"],
                 "pra":["para", "a"],
                 "pras":["para", "as"],
                 "pro":["para", "o"],
                 "pros":["para", "os"],
                 "prum":["para", "um"],
                 "pruns":["para", "uns"],
                 "pruma":["para", "uma"],
                 "prumas":["para", "umas"]}
    ambigous = ["nos", "consigo", "pra", "pela", "pelas", "pelo", "pelos"]
#    ambigous = ["nos", "consigo", "pra", "pelo", "pelos"]
    enclisis = ['me', 'te', 'se', 'lhe', 'o', 'a', 'nos', 'vos', 'lhes', 'os', 'as', 'lo', 'la', 'los', 'las']
    doubleEnclisis = ["mo", "to", "lho", "lhos", "ma", "ta", "lha", "lhas", "mos", "tos"]
    doubleEnclisisTri = ["no-lo", "vo-lo", "no-la", "vo-la", "no-los", "vo-los", "no-las", "vo-las"]
    terminations = ["ia", "ias", "as", "iamos", "ieis", "iam", "ei", "as", "a", "emos", "eis", "ão", "á"]
    abbrev = [
        "dr.", "dra.", "sr.", "sra.", "prof.", "profa.", "Dr.", "Dra.", "Sr.", "Sra.", "Prof.", "Profa.", "DR.", "DRA.", "SR.", "SRA.", "PROF.", "PROFA.",
        "ilmo.", "Ilmo.", "ILMO.", "bel.", "Bel.", "BEL.", "eng.", "Eng.", "ENG.", "reg.", "Reg.", "REG.", "visc.", "Visc.", "VISC.", "bar.", "Bar.", "BAR.",
        "cond.", "Cond.", "COND.", "séc.", "Séc.", "SÉC.", "jr.", "Jr.", "JR.", "ir.", "Ir.", "IR.", "st.", "St.", "ST.", "app.", "App.", "APP.",
        "gov.", "Gov.", "GOV.", "des.", "Des.", "DES.", "gen.", "Gen.", "GEN.", "gal.", "Gal.", "GAL.", "cel.", "Cel.", "CEL.", "col.", "Col.", "COL.",
        "maj.", "Maj.", "MAJ.", "ten.", "Ten.", "TEN.", "cap.", "Cap.", "CAP.", "capt.", "Capt.", "CAPT.", "com.", "Com.", "COM.", "brig.", "Brig.", "BRIG.",
        "estac.", "Estac.", "ESTAC.", "tel.", "Tel.", "TEL.", "ave.", "Ave.", "AVE.", "av.", "Av.", "AV.", "trav.", "Trav.", "TRAV.", "con.", "Con.", "CON.",
        "jd.", "Jd.", "JD.", "ed.", "Ed.", "ED.", "lj.", "Lj.", "LJ.", "cj.", "Cj.", "CJ.", "apto.", "Apto.", "APTO.", "apt.", "Apt.", "APT.", "ingr.", "Ingr.", "INGR.",
        "ap.", "Ap.", "AP.", "dir.", "Dir.", "DIR.", "min.", "Min.", "MIN.", "sec.", "Sec.", "SEC.", "kg.", "Kg.", "KG.", "ml.", "Ml.", "ML.", "km.", "Km.", "KM.", "cm.", "Cm.", "CM.",
        "vol.", "Vol.", "VOL.", "PP.", "pp.", "Pp", "pag.", "Pag", "PAG.", "pág.", "Pág", "PÁG.", "al.", "Al.", "AL.", "etc.", "i.e.", "e.g.", "cia.", "Cia.", "CIA.",
        "co.", "Co.", "CO.", "ltda.", "Ltda.", "LTDA.", "ex.", "Ex.", "EX.", "ac.", "Ac.", "AC.", "dc.", "Dc.", "DC.", "bros.", "Bros.", "BROS.", "pq.", "Pq.", "PQ.",
        "br.", "Br.", "BR.", "cent.", "Cent.", "CENT.", "ft.", "Ft.", "FT.", "net.", "Net.", "NET.", "no.", "No.", "NO.", "nr.", "Nr.", "NR.", "tr.", "Tr.", "TR.",
        "mi.", "Mi.", "MI.", "sta.", "Sta.", "STA.", "sto.", "Sto.", "STO.", "int.", "Int.", "INT.", "inf.", "Inf.", "INF.", "cult.", "Cult.", "CULT.", "op.", "Op.", "OP.",
        "aprox.", "Aprox.", "APROX.", "it.", "It.", "IT.", "ex.", "Ex.", "EX.", "flex.", "Flex.", "FLEX.", "ass.", "Ass.", "ASS.", "pç.", "Pç.", "PÇ.", "ind.", "Ind.", "IND.",
        "vl.", "Vl.", "VL.", "imp.", "Imp.", "IMP.", "emp.", "Emp.", "EMP.", "esq.", "Esq.", "ESQ.", "dir.", "Dir.", "DIR.", "ingr.", "Ingr.", "INGR.", "pça.", "Pça.", "PÇA.",
        "art.", "Art.", "ART.", "sec.", "Sec.", "SEC.", "inc.", "Inc.", "INC.", "a.", "A.", "b.", "B.", "c.", "C.", "d.", "D.", "e.", "E.", "f.", "F.", "g.", "G.", "h.", "H.", "i.", "I.",
        "j.", "J.", "k.", "K.", "l.", "L.", "m.", "M.", "n.", "N.", "o.", "O.", "p.", "P.", "q.", "Q.", "r.", "R.", "s.", "S.", "t.", "T.", "u.", "U.", "v.", "V.", "w.", "W.", "x.", "X.", "y.", "Y.", "z.", "Z.",
        "seg.", "ter.", "qua.", "qui.", "sex.", "sab.", "sáb.", "dom.", "Seg.", "Ter.", "Qua.", "Qui.", "Sex.", "Sab.", "Sáb.", "Dom.", "SEG.", "TER.", "QUA.", "QUI.", "SEX.", "SAB.", "SÁB.", "DOM.",
        "jan.", "fev.", "mar.", "abr.", "mai.", "jun.", "jul.", "ago.", "sep.", "out.", "nov.", "dez.", "Jan.", "Fev.", "Mar.", "Abr.", "Mai.", "Jun.", "Jul.", "Ago.", "Sep.", "Out.", "Nov.", "Dez.",
        "JAN.", "FEV.", "MAR.", "ABR.", "MAI.", "JUN.", "JUL.", "AGO.", "SET.", "OUT.", "NOV.", "DEZ."
    ]
    #abbrev = []
    #infile = open("abbrev.txt", "r")
    #for line in infile:
    #    abbrev.append(line[:-1])
    #infile.close()
    def isAbbrev(chunk, abbrev):
        abbr = False
        for a in abbrev:
            if (chunk == a):
                abbr = True
                break
            #else:
            #    lasts = -len(a)
            #    if (chunk[lasts:] == a) and (not chunk[lasts-1].isalpha()):
            #        abbr = True
            #        break
        return abbr
    tokens = []
    bits = s.split(" ")
    k = 0
    for b in bits:
        pretagged = False
        if (len(b) > 16):
            if (b[:8] == "//*||*\\\\") or (b[:9] == "//*|(|*\\\\"):
                pretagged = True
        if (pretagged):
            # keep the bit as token and clean the tags //*||*\\ before and after
            tokens.append([b.replace("//*||*\\\\", "").replace("//*||*\\\\", "").replace("//*|(|*\\\\", ""), "_"])
        else:
            # deal with the pre (before) middle
            pre = []
            changed = True
            while (changed) and (len(b) > 1):
                changed = False
                if (b[0] in removable) or ((b[0] == "$") and (b[1] in digits)) or ((b[0] == "-") and (b[1] not in digits)):
                    pre.append(b[0])
                    b = b[1:]
                    changed = True
            # deal with the pos (after) middle
            tmp = []
            changed = True
            while (changed) and (len(b) > 1):
                if (isAbbrev(b, abbrev)):
                    break
                changed = False
                if (b[-1] in removable+["-", "."]):
                    tmp.append(b[-1])
                    b = b[:-1]
                    changed = True
            pos = []
            reticent = ""
            for i in range(len(tmp)-1, -1, -1):
                if (tmp[i] == "."):
                    if (reticent == ""):
                        reticent = "."
                    elif (reticent == "."):
                        reticent = ".."
                    elif (reticent == ".."):
                        pos.append("...")
                        reticent = ""
                else:
                    if (reticent != ""):
                        pos.append(reticent)
                        reticent = ""
                    pos.append(tmp[i])
            if (reticent != ""):
                pos.append(reticent)
            # deal with the middle
            buf = b.split("-")
            if (len(buf) == 1):
                parts = pre+[b]+pos
            # enclisis (types I - infinitive e.g. cumprí-lo and type II - sonore e.g. satisfê-lo)
            elif (len(buf) == 2) and (buf[1] in enclisis):
                if (buf[0][-1] == "á"):
                    if (lex.pexists(buf[0][:-1]+"ar", "VERB")):
                        parts = pre+["*^*"+b, buf[0][:-1]+"ar", buf[1]]+pos
                    else:
                        if (lex.pexists(buf[0][:-1]+"as", "VERB")):
                            parts = pre+["*^*"+b, buf[0][:-1]+"as", buf[1]]+pos
                        else:
                            parts = pre+["*^*"+b, buf[0][:-1]+"az", buf[1]]+pos
                elif (buf[0][-1] == "ê"):
                    if (lex.pexists(buf[0][:-1]+"er", "VERB")):
                        parts = pre+["*^*"+b, buf[0][:-1]+"er", buf[1]]+pos
                    else:
                        if (lex.pexists(buf[0][:-1]+"es", "VERB")):
                            parts = pre+["*^*"+b, buf[0][:-1]+"es", buf[1]]+pos
                        else:
                            parts = pre+["*^*"+b, buf[0][:-1]+"ez", buf[1]]+pos
                elif (buf[0][-1] == "í"):
                    if (lex.pexists(buf[0][:-1]+"ir", "VERB")):
                        parts = pre+["*^*"+b, buf[0][:-1]+"ir", buf[1]]+pos
                    else:
                        if (lex.pexists(buf[0][:-1]+"is", "VERB")):
                            parts = pre+["*^*"+b, buf[0][:-1]+"is", buf[1]]+pos
                        else:
                            parts = pre+["*^*"+b, buf[0][:-1]+"iz", buf[1]]+pos
                elif (buf[0][-1] == "ô"):
                    if (lex.pexists(buf[0][:-1]+"or", "VERB")):
                        parts = pre+["*^*"+b, buf[0][:-1]+"or", buf[1]]+pos
                    else:
                        if (lex.pexists(buf[0][:-1]+"os", "VERB")):
                            parts = pre+["*^*"+b, buf[0][:-1]+"os", buf[1]]+pos
                        else:
                            parts = pre+["*^*"+b, buf[0][:-1]+"oz", buf[1]]+pos
                else:
                    parts = pre+["*^*"+b, buf[0], buf[1]]+pos
            # double enclisis - type II (e.g. disse-lhos, dei-ta)
            elif (len(buf) == 2) and (buf[1] in doubleEnclisis):
                if (buf[1][-1] == "a"):
                    parts = pre+["*^^*"+b, buf[0], buf[1][:-1]+"e", buf[1][-1]]+pos
                elif (buf[1][-1] == "o"):
                    parts = pre+["*^^*"+b, buf[0], buf[1][:-1]+"e", buf[1][-1]]+pos
                elif (buf[1][-2:] == "as"):
                    parts = pre+["*^^*"+b, buf[0], buf[1][:-2]+"e", buf[1][-2:]]+pos
                elif (buf[1][-2:] == "os"):
                    parts = pre+["*^^*"+b, buf[0], buf[1][:-2]+"e", buf[1][-2:]]+pos
                else:
                    parts = pre+["*^*"+b, buf[0], buf[1]]+pos
            # double enclisis - type I (e.g. dá-se-lhes)
            elif (len(buf) == 3) and (buf[1] in enclisis) and (buf[2] in enclisis):
                if (buf[0][-1] == "á"):
                    parts = pre+["*^^*"+b, buf[0][:-1]+"ar", buf[1], buf[2]]+pos
                elif (buf[0][-1] == "ê"):
                    parts = pre+["*^^*"+b, buf[0][:-1]+"er", buf[1], buf[2]]+pos
                elif (buf[0][-1] == "í"):
                    parts = pre+["*^^*"+b, buf[0][:-1]+"ir", buf[1], buf[2]]+pos
                elif (buf[0][-1] == "ô"):
                    parts = pre+["*^^*"+b, buf[0][:-1]+"or", buf[1], buf[2]]+pos
                else:
                    parts = pre+["*^^*"+b, buf[0], buf[1], buf[2]]+pos
            # mesoclisis - type I (e.g. dar-lo-ia)
            elif (len(buf) == 3) and (buf[1] in enclisis) \
                and (buf[0][-1] == "r") and (buf[2] in terminations):
                parts = pre+["*^*"+b, buf[0]+buf[2], buf[1]]+pos
            # mesoclisis - type II (e.g. dá-lo-ia)
            elif (len(buf) == 3) and (buf[1] in enclisis) \
                and (buf[0][-1] in ["á", "ê", "í", "ô"]) and (buf[2] in terminations):
                if (buf[0][-1] == "á"):
                    parts = pre+["*^*"+b, buf[0][:-1]+"ar"+buf[2], buf[1]]+pos
                elif (buf[0][-1] == "ê"):
                    parts = pre+["*^*"+b, buf[0][:-1]+"er"+buf[2], buf[1]]+pos
                elif (buf[0][-1] == "í"):
                    parts = pre+["*^*"+b, buf[0][:-1]+"ir"+buf[2], buf[1]]+pos
                elif (buf[0][-1] == "ô"):
                    parts = pre+["*^*"+b, buf[0][:-1]+"or"+buf[2], buf[1]]+pos
            else:
                parts = pre+[b]+pos
            # transform parts into tokens to be added
            i = 0
            while (i < len(parts)):
                if (i == len(parts)-1):
                    lastField = "_"
                else:
                    lastField = "SpaceAfter=No"
                if (parts[i][:3] == "*^*"):
                    if (i+3 == len(parts)):
                        tokens.append([parts[i][3:], "c_"])
                    else:
                        tokens.append([parts[i][3:], "cSpaceAfter=No"])
                    i += 1
                    tokens.append([parts[i], "_"])
                    i += 1
                    tokens.append([parts[i], "_"])
                elif (parts[i][:4] == "*^^*"):
                    if (i+4 == len(parts)):
                        tokens.append([parts[i][4:], "C_"])
                    else:
                        tokens.append([parts[i][4:], "CSpaceAfter=No"])
                    i += 1
                    tokens.append([parts[i], "_"])
                    i += 1
                    tokens.append([parts[i], "_"])
                    i += 1
                    tokens.append([parts[i], "_"])
                elif (parts[i] not in ambigous):
                    ans = contracts.get(parts[i].lower())
                    if (ans == None):
                        tokens.append([parts[i], lastField])
                    else:
                        tokens.append([parts[i], "c"+lastField])
                        if (parts[i].isupper()):
                            tokens.append([ans[0].upper(),"_"])
                            tokens.append([ans[1].upper(),"_"])
                        elif (parts[i][0].isupper()):
                            tokens.append([ans[0][0].upper()+ans[0][1:],"_"])
                            tokens.append([ans[1],"_"])
                        else:
                            tokens.append([ans[0],"_"])
                            tokens.append([ans[1],"_"])
                else:
                    desambIt(parts[i], bits, k, lastField, s, SID, tokens)
                i += 1
        k += 1
    # output the sentence with all the tokens
    lines = []
    lines.append("# sent_id = " + SID)
    lines.append("# text = " + s.replace("//*||*\\\\", "").replace("//*||*\\\\", "").replace("//*|(|*\\\\", ""))
    ## build token lines
    toks = 0
    for i in range(len(tokens)):
        if (tokens[i][1][0] == "c"):
            # contracted word (two parts)
            lines.append("\t".join([str(toks+1)+"-"+str(toks+2), tokens[i][0], "_", "_", "_", "_", "_", "_", "_", tokens[i][1][1:]]))
        elif (tokens[i][1][0] == "C"):
            # contracted word (three parts)
            lines.append("\t".join([str(toks+1)+"-"+str(toks+3), tokens[i][0], "_", "_", "_", "_", "_", "_", "_", tokens[i][1][1:]]))
        elif (tokens[i][0].strip() != ""):
            # non contracted word
            toks += 1
            lines.append("\t".join([str(toks), tokens[i][0].strip(), "_", "_", "_", "_", "_", "_", "_", tokens[i][1]]))
    lines.append("")  # empty line at end
    return lines

#################################################
### Deal with a sentence, clean it, if required, then tokenize it
#################################################
def processIt(sent: str, SID: str, preserve: bool, match: bool, trim: bool) -> list[str]:
    if (trim):       # step 1
        sent = trimIt(sent)
    if (preserve):   # step 2
        sent = tagIt(sent)
    if (match):      # step 3
        sent = punctIt(sent)
    if (sent != ""): # step 4
        return tokenizeIt(sent, SID)
    else:
        return []


#################################################
### Process multiple sentences and return CoNLL-U output
#################################################
def processSentences(
    sentences: list[str],
    sid_start: str = "S000000",
    preserve: bool = True,
    match: bool = True,
    trim: bool = True
) -> str:
    """
    Convert a list of sentences to CoNLL-U format.
    
    Args:
        sentences: List of sentences to tokenize.
        sid_start: Starting sentence ID model (default: "S000000").
        preserve: Preserve itemization tokens like a) b) i) ii) (default: True).
        match: Correct paired punctuation (quotes, parentheses, etc) (default: True).
        trim: Remove possible headlines preceding sentences (default: True).
    
    Returns:
        CoNLL-U formatted string with all tokenized sentences.
    """
    all_output_lines: list[str] = []
    sid = sid_start
    
    for sentence in sentences:
        sid = nextName(sid)
        processed_lines = processIt(sentence, sid, preserve, match, trim)
        if processed_lines:
            all_output_lines.extend(processed_lines)
    
    return "\n".join(all_output_lines) + "\n"


#################################################
### função principal do programa - busca argumentos e chama 'tokenize' para cada sentença da entrada
#################################################
def main() -> None:
    args = parse_args()
    
    # Read sentences from file
    with open(args.input_file, "r") as infile:
        sentences = [line.rstrip('\n') for line in infile]
    
    # Process all sentences
    output = processSentences(
        sentences,
        sid_start=args.sid_model,
        preserve=args.preserve,
        match=args.match,
        trim=args.trim
    )
    
    # Write output
    with open(args.output_file, "w") as outfile:
        outfile.write(output)
    
    # Count sentences in output
    s_total = output.count("# sent_id = ")
    print(f"Tokenização terminada com {s_total} sentenças extraídas e salvas em {args.output_file}")

if __name__ == "__main__":
    main()

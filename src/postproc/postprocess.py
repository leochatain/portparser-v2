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
import io
import os
import argparse
from dataclasses import dataclass, field

from lexikon import UDlexPT
from conlluFile import ConlluFile

lex = UDlexPT()


@dataclass
class PostProcessResult:
    """Result of post-processing a CoNLL-U file."""
    output: str = ""
    changes: dict[str, int] = field(default_factory=lambda: {"Pchanged": 0, "Lchanged": 0, "Fchanged": 0})
    report_lines: list[str] = field(default_factory=list)

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
        prog="postprocess",
        description="Pós-processamento para correção de UPOS, LEMMA e FEATS em arquivos CoNLL-U",
        epilog="Exemplo: python postprocess.py -o output.conllu input.conllu"
    )
    
    parser.add_argument(
        "input_file",
        type=_existing_file,
        help="Arquivo de entrada CoNLL-U"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_file",
        default="xxx.conllu",
        help="Arquivo de saída CoNLL-U (default: %(default)s)"
    )
    parser.add_argument(
        "-l", "--lemma", "--no-lemma",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="lemma",
        help="Executa correção de lemma (default: %(default)s)"
    )
    parser.add_argument(
        "-f", "--feats", "--no-feats",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="feats",
        help="Executa correção de features (default: %(default)s)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        default=False,
        help="Não gera relatório de mudanças (.rep.tsv)"
    )
    
    return parser.parse_args(argv)


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
### Core Function - Postprocess fix of UPOS, LEMMA and FEATS
#################################################
def fixLemmaFeatures(base: ConlluFile, usualAbbr: list) -> PostProcessResult:
    """
    Fix UPOS, LEMMA and FEATS in a CoNLL-U file.
    
    Args:
        base: A ConlluFile object to process (modified in place).
        usualAbbr: List of usual abbreviations from getUsualAbbr().
    
    Returns:
        PostProcessResult with lines, changes counts, and report lines.
    """
    # Tag categories
    lexOutOfTags   = ["PROPN", "PUNCT", "SYM", "X"]    # correct arbitrarily
    lexCloseTags   = ["ADP", "ADV", "CCONJ", "SCONJ"]  # correct if unique in lex, erase feats (features are impossible)
    lexPronDetTags = ["DET", "PRON"]                   # correct if unique in lex, require 'PronType', erase impossible features
    lexOpenTags    = ["ADJ", "INTJ", "NOUN", "NUM"]    # correct if unique in lex, erase impossible features
    lexVerbTags    = ["AUX", "VERB"]                   # correct if unique in lex, require 'VerbForm', erase impossible features
    digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    ordinalsignsFem = ['ª', 'a']
    ordinalsignsMasc = ['º', '°', 'o']
    ordinalsignsNeut = ['.']

    # result
    result = PostProcessResult()
    
    # main loop
    for i in range(base.getS()):
        b = base.getSentByIndex(i)
        fixeds = locateExtPos(b[4])
        for tk in b[4]:
            # level down contracted tokens info, but ID and FORM
            if ("-" in tk[0]):
                tk[2], tk[3], tk[4], tk[5], tk[6], tk[7], tk[8], tk[9] = "_", "_", "_", "_", "_", "_", "_", "_"
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
                    feat = featsFull(opFEATS[0], abbr, extpos=extpos) if (len(opFEATS) == 1) else featsFull(tk[5], abbr, extpos=extpos)
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
                    feat = featsFull(opFEATS[0], abbr, extpos=extpos, prontype=prontype) if (len(opFEATS) == 1) else featsFull(tk[5], abbr, extpos=extpos, prontype=prontype)
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
                    feat = featsFull(opFEATS[0], abbr, extpos=extpos, verbform=None, numtype=None) if (len(opFEATS) == 1) else featsFull(tk[5], abbr, extpos=extpos, verbform=None, numtype=None)
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
                    feat = featsFull(opFEATS[0], abbr, extpos=extpos, verbform=None, voicepass=voicepass) if (len(opFEATS) == 1) else featsFull(tk[5], abbr, extpos=extpos, verbform=None, voicepass=voicepass)
            # do reports and change
            if (pos != tk[3]):
                result.report_lines.append("\t".join([b[0], tk[0], tk[1], tk[3], "UPOS", tk[3], pos]))
                result.changes["Pchanged"] += 1
                tk[3] = pos
            if (lem != tk[2]):
                result.report_lines.append("\t".join([b[0], tk[0], tk[1], tk[3], "LEMMA", tk[2], lem]))
                result.changes["Lchanged"] += 1
                tk[2] = lem
            if (feat != tk[5]):
                if ("ExtPos=" not in feat):
                    result.report_lines.append("\t".join([b[0], tk[0], tk[1], tk[3], "FEATS", tk[5], feat]))
                    result.changes["Fchanged"] += 1
                tk[5] = feat

    # Generate output from the modified base
    output_buffer = io.StringIO()
    base.printNoHeader(output_buffer)
    result.output = output_buffer.getvalue()

    return result


#################################################
### Main Function - CLI entry point
#################################################
def main() -> None:
    args = parse_args()
    
    # Load data
    base = ConlluFile(args.input_file)
    usualAbbr = getUsualAbbr()
    
    # Process
    result = fixLemmaFeatures(base, usualAbbr)
    
    # Write output
    with open(args.output_file, "w") as outfile:
        outfile.write(result.output)
    
    # Write report if requested
    if not args.quiet:
        with open(args.output_file + ".rep.tsv", "w") as repfile:
            for line in result.report_lines:
                print(line, file=repfile)
            # Print summary
            accName = ["Pchanged", "Lchanged", "Fchanged"]
            accList = [result.changes[name] for name in accName]
            print_reps(repfile, accName, accList)

    print(f"Pós-processamento concluído. Resultado salvo em {args.output_file}")


if __name__ == "__main__":
    main()

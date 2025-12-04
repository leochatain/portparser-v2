# portSentencer - sentenciador de texto puro para o Portugues
#
# Este programa recebe diversos arquivos de entrada em formato
#    textual e gera um arquivo textual com uma sentença por linha.
#
# Opções:
#
# -h help
# -o output file
# -r replace non standart characters
# -l limit the number of characters per sentence
#
# Exemplo de utilização:
#
# portSent -o sents.txt -r -l 2048 text1.txt text2.txt
#
# Busca o texto nos arquivos 'text1.txt' e 'text2.txt',
#   substitui caracteres não usuais,
#   gera sentenças com limite máximo de 2048 carateres e
#   salva as sentenças no arquivo 'sents.txt'
#
# last edit: 01/21/2024
# created by Lucelene Lopes - lucelene@gmail.com

import os
import argparse
from typing import TextIO


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
        prog="portSent",
        description="Sentenciador de texto puro para o Português",
        epilog="Exemplo: portSent -o sents.txt --no-replace -l 2048 text1.txt text2.txt"
    )
    
    parser.add_argument(
        "input_files",
        nargs="+",
        type=_existing_file,
        help="Arquivos de entrada com texto"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_file",
        default="sents.txt",
        help="Arquivo de saída com sentenças (default: %(default)s)"
    )
    parser.add_argument(
        "-r", "--replace", "--no-replace",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Substitui caracteres não padrão (default: %(default)s)"
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=0,
        help="Limite de caracteres por sentença, 0 para sem limite (default: %(default)s)"
    )
    
    return parser.parse_args(argv)

#################################################
### função stripSents - faz de fato o sentenciamento
#################################################
def stripSents(inputText: str, outfile: TextIO, limit: int, replace: bool) -> int:
    def cleanPrint(sent: str, outfile: TextIO) -> int:
        # do not print empty sentences
        if (sent == "") or (sent == ".") or (sent == ".."):
            return 0
        # remove second . in sentences ending by ..
        elif (len(sent) > 2) and (sent[-3:] != "...") and (sent[-2:] == ".."):
            print(sent[:-1], file=outfile)
            return 1
        # insert . in sentences not ending by punctuation
        elif (sent[-1] not in [".", "!", "?", ":", ";"]) and \
            not ((sent[-1] in ["'", '"']) and (sent[-2] in [".", "!", "?"])):
            print(sent+".", file=outfile)
            return 1
        # remove encompassing quotations " or ' if the quotations do not appear inside the sentence
        elif (sent[0] == sent[1]) and ((sent[0] == "'") or (sent[0] == '"')) and (sent.count(sent[0]) == 2):
            print(sent[1:-1], file=outfile)
            return 1
        # otherwise print it as it is
        else:
            print(sent, file=outfile)
            return 1
    def isAbbrev(chunk: str, abbrev: list[str]) -> bool:
        abbr = False
        for a in abbrev:
            if (chunk == a):
                abbr = True
                break
            else:
                lasts = -len(a)
                if (chunk[lasts:] == a) and (not chunk[lasts-1].isalpha()):
                    abbr = True
                    break
        return abbr
    # the function stripSents main body
    abbrev = []
    infile = open("./src/portSentencer/abbrev.txt", "r")
    for line in infile:
        abbrev.append(line[:-1])
    infile.close()
    if (replace):
        replaceables = [[" ", " "], \
                        ["—", "-"], ["–", "-"], \
                        ['＂', '"'], \
                        ['“', '"'], ['”', '"'], \
                        ['‟', '"'], ['″', '"'], \
                        ['‶', '"'], ['〃', '"'], \
                        ['״', '"'], ['˝', '"'], \
                        ['ʺ', '"'], ['˶', '"'], \
                        ['ˮ', '"'], ['ײ', '"'], \
                        [" ‣", "."], [" >>", "."], [" ○", "."], [" *", "."], \
                        [" | ", ". "], [" .", "."], \
                        ["\n", " "], ["\t", " "]]
    else:
        replaceables = [["\n", " "], ["\t", " "]]
    tmp = inputText.replace("  "," ")
    for r in replaceables:
        tmp = tmp.replace(r[0], r[1])
    while (tmp.find("  ") != -1):
        tmp = tmp.replace("  "," ")
    if (tmp[0] == " "):
        tmp = tmp[1:]
    bagOfChunks = tmp.split(" ")
    s, sent = 0, ""
    if (bagOfChunks[-1] == ""):
        bagOfChunks.pop()
    for i in range(len(bagOfChunks)):
        # if it is the last chunk, it is the end of sentence
        if (i == len(bagOfChunks)-1):
            sent += " " + bagOfChunks[i]
            s += cleanPrint(sent[1:], outfile)
            break
        chunk = bagOfChunks[i]
        # if there is a limit and the chunk is greater than the limit, discard it
        if (limit != 0) and (len(chunk) > limit):
            continue
        # if there is a limit and it is reached, ends the sentence arbitrarily
        elif (limit != 0) and (len(sent) + len(chunk) > limit):
            s += cleanPrint(sent[1:], outfile)
            sent = chunk
        # if the chunk is too short
        elif (len(chunk) < 3) and (len(chunk) != 0):
            sent += " " + chunk
        # if the chunk is empty
        elif (len(chunk) == 0):
            continue
        # ! ? or ... always mark an end of sentence
        elif (chunk[-3:] == "...") or (chunk[-1] == "!") or (chunk[-1] == "?"):
            sent += " " + chunk
            s += cleanPrint(sent[1:], outfile)
            sent = ""
        # a . : or ; followed by a lowercase chunk is not an end of sentence
        elif ((chunk[-1] == ".") or (chunk[-1] == ":") or (chunk[-1] == ";")) and (bagOfChunks[i+1][0].islower()):
            sent += " " + chunk
        # a : or ; not followed by a lowercase chunk is an end of sentence
        elif ((chunk[-1] == ":") or (chunk[-1] == ";")) and (not bagOfChunks[i+1][0].islower()):
            sent += " " + chunk
            s += cleanPrint(sent[1:], outfile)
            sent = ""
        # chunk ends with ! or ? followed by quotations that had appear before an odd number is an end of sentence
        elif (chunk[-2:] in ["!'", '!"', "?'", '?"']):
            sent += " " + chunk
            s += cleanPrint(sent[1:], outfile)
            sent = ""
        elif (chunk[-2:] in [".'", '."']):
            sent += " " + chunk
            abbr = isAbbrev(chunk[:-1], abbrev)
            if not abbr:
                s += cleanPrint(sent[1:], outfile)
                sent = ""
        # a chunk not ending with ! ? ... ; : or . is not an end of sentence
        elif (chunk[-1] != "."):
            sent += " " + chunk
        # chunk ending by . is either a know abbreviation (not an end of sentence), or an end of sentence
        elif (chunk[-1] == "."):
            abbr = isAbbrev(chunk, abbrev)
            if (abbr):
                sent += " " + chunk
            else:
                sent += " " + chunk
                s += cleanPrint(sent[1:], outfile)
                sent = ""
    # return the number of generated sentences
    return s

#################################################
### função principal do programa - busca argumentos e chama 'stripSents' que faz de fato o sentenciamento
#################################################
def main() -> None:
    args = parse_args()
    
    with open(args.output_file, "w") as outfile:
        input_text = ""
        for input_path in args.input_files:
            with open(input_path, "r") as infile:
                input_text += infile.read()
        s = stripSents(input_text, outfile, args.limit, args.replace)
    
    print(f"Sentenciamento terminado com {s} sentenças extraídas e salvas em {args.output_file}")


if __name__ == "__main__":
    main()

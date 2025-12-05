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

import logging
import os
import argparse

from lexikon import ends_with_abbreviation

logger = logging.getLogger(__name__)


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
        dest="replace",
        help="Substitui caracteres não padrão (default: %(default)s)"
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=0,
        help="Limite de caracteres por sentença, 0 para sem limite (default: %(default)s)"
    )
    
    return parser.parse_args(argv)

def _clean_sentence(sent: str) -> str | None:
    """
    Clean and normalize a sentence for output.
    
    Returns the cleaned sentence, or None if it should be skipped.
    """
    # do not print empty sentences
    if (sent == "") or (sent == ".") or (sent == ".."):
        return None
    # remove second . in sentences ending by ..
    elif (len(sent) > 2) and (sent[-3:] != "...") and (sent[-2:] == ".."):
        return sent[:-1]
    # insert . in sentences not ending by punctuation
    elif (sent[-1] not in [".", "!", "?", ":", ";"]) and \
        not ((sent[-1] in ["'", '"']) and (sent[-2] in [".", "!", "?"])):
        return sent + "."
    # remove encompassing quotations " or ' if the quotations do not appear inside the sentence
    elif (sent[0] == sent[1]) and ((sent[0] == "'") or (sent[0] == '"')) and (sent.count(sent[0]) == 2):
        return sent[1:-1]
    # otherwise return it as it is
    else:
        return sent




#################################################
### função stripSents - faz de fato o sentenciamento
#################################################
def stripSents(inputText: str, limit: int = 0, replace: bool = True) -> list[str]:
    """
    Segment input text into sentences.
    
    Args:
        inputText: The text to segment into sentences.
        limit: Maximum characters per sentence, 0 for no limit.
        replace: Whether to replace non-standard characters.
    
    Returns:
        A list of sentences.
    """
    sentences: list[str] = []
    
    def add_sentence(sent: str) -> None:
        """Clean and add sentence to the list if valid."""
        cleaned = _clean_sentence(sent)
        if cleaned is not None:
            sentences.append(cleaned)
    
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
    sent = ""
    if (bagOfChunks[-1] == ""):
        bagOfChunks.pop()
    for i in range(len(bagOfChunks)):
        # if it is the last chunk, it is the end of sentence
        if (i == len(bagOfChunks)-1):
            sent += " " + bagOfChunks[i]
            add_sentence(sent[1:])
            break
        chunk = bagOfChunks[i]
        # if there is a limit and the chunk is greater than the limit, discard it
        if (limit != 0) and (len(chunk) > limit):
            continue
        # if there is a limit and it is reached, ends the sentence arbitrarily
        elif (limit != 0) and (len(sent) + len(chunk) > limit):
            add_sentence(sent[1:])
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
            add_sentence(sent[1:])
            sent = ""
        # a . : or ; followed by a lowercase chunk is not an end of sentence
        elif ((chunk[-1] == ".") or (chunk[-1] == ":") or (chunk[-1] == ";")) and (bagOfChunks[i+1][0].islower()):
            sent += " " + chunk
        # a : or ; not followed by a lowercase chunk is an end of sentence
        elif ((chunk[-1] == ":") or (chunk[-1] == ";")) and (not bagOfChunks[i+1][0].islower()):
            sent += " " + chunk
            add_sentence(sent[1:])
            sent = ""
        # chunk ends with ! or ? followed by quotations that had appear before an odd number is an end of sentence
        elif (chunk[-2:] in ["!'", '!"', "?'", '?"']):
            sent += " " + chunk
            add_sentence(sent[1:])
            sent = ""
        elif (chunk[-2:] in [".'", '."']):
            sent += " " + chunk
            if not ends_with_abbreviation(chunk[:-1]):
                add_sentence(sent[1:])
                sent = ""
        # a chunk not ending with ! ? ... ; : or . is not an end of sentence
        elif (chunk[-1] != "."):
            sent += " " + chunk
        # chunk ending by . is either a know abbreviation (not an end of sentence), or an end of sentence
        elif (chunk[-1] == "."):
            sent += " " + chunk
            if not ends_with_abbreviation(chunk):
                add_sentence(sent[1:])
                sent = ""
    
    return sentences

#################################################
### função principal do programa - busca argumentos e chama 'stripSents' que faz de fato o sentenciamento
#################################################
def main() -> None:
    args = parse_args()
    
    input_text = ""
    for input_path in args.input_files:
        with open(input_path, "r") as infile:
            input_text += infile.read()
    
    sentences = stripSents(input_text, limit=args.limit, replace=args.replace)
    
    with open(args.output_file, "w") as outfile:
        for sentence in sentences:
            outfile.write(sentence + "\n")
    
    logger.info(f"Sentenciamento terminado com {len(sentences)} sentenças extraídas e salvas em {args.output_file}")


if __name__ == "__main__":
    main()

# conlluFile.py - a Python 3 package to handle a CoNNL-U files (.conllu) in data structure (base)
#
# (c) Lucelene Lopes 2023
#
# member functions:
#    conlluFile - the constructor from an input conllu file (name) - default no name creates an empty base
#                                                                  - default considering contracted word (skipAg=True if not)
# Acessors
#    getBase(self):              # return the whole base
#    getHeader(self):            # return in a single string the initial lines of the conllu
#    getS(self):                 # return the number of sentences
#    getT(self):                 # return the number of tokens (ignoring contracted words)
#    getSandT(self):             # return the number of sentences and tokens
#    getSentByID(self, SID):     # return a sentence by its SID (string) - return none if absent
#    getSentByIndex(self, ind):  # return a sentence by its index (int) - return none if absent
#    getSentInd(self, SID):      # return the index (int) of the sentence with SID (string) - return -1 if absent
#    getSentID(self, ind):       # return the SID (string) for the sentence indexed by ind - return -1 if absent
#    isSIDin(self, SID):         # return True if the SID is in the base
#    isINDin(self, ind):         # return True if the index (int) is in the base
#    isSentTagged(self, ind):    # return True if the sentence indexed by ind (int) has a non empty tag (b[5])
#    numberSentSize(self, size): # return how many sentences in the base have this size
#    sentSizeRange(self):        # return the smallest and largest sentence size within the base
#    getAllSIDs(self):           # return the list with all sentence IDs
# Mutators
#    addToBase(self, name):          # add a conllu file (name) to the base considering contracted word or not (skipAg)
#    removeSentInd(self, s):         # remove the sentence with id s from base
#    removeSentSID(self, s):         # remove the sentence with SID s (string) from base
#    tagTokenAtSID(self,s,t,tag):    # sets tag (string) for s is the SID (string), t is the token id (string)
#    tagTokenAtSent(self,s,t,tag):   # sets tag (string) for s is the sentence index (int), t is the token id (string)
#    tagSent(self,s,tag):            # sets tag (string) for s is the sentence index (int)
#    setSentTags(self):              # set the sentence tags (additional info) based on the tokens tags (additional info)
#    sortBase(self):                 # sort the base according to SID
# Prints
#    printSent(self, ind, outfile, nodeprel=False): # prints out a sentence by its index (int) in a outfile with all 10 fields
#    printHeaderToo(self, outfile, nodeprel=False): # prints out the whole base in an outfile
#    printNoHeader(self, outfile, nodeprel=False):  # prints out the whole base in an outfile
#
# Sentence structure
    ## b[0] SID - sentence ID
    ## b[1] TEXT - text of the sentence
    ## b[2] number of tokens (not including the contracted word lines)
    ## b[3] lines of the header (including, but not limited to, the '# sent_id =' and '# text' lines)
    ## b[4] token lines (including contracted word lines)
    ##   each token line has 10 elements of the CoNLL-U format, plus one place holder for information
    ## b[5] status of change (a place holder for information)


class conlluFile:
    def __init__(self, name="", skipAg=False):   # create a base from an input conllu file (name) considering contracted word or not (skipAg)
        # Instance variables:
        #   self.base      - the whole base
        #   self.header    - the first lines before the actual sentences
        #   self.s         - the total number of sentences
        #   self.t         - the total number of tokens
        self.base = []
        if (name == ""):
            self.header, self.s, self.t = "", 0, 0
        else:
            infile = open(name, "r")
            self.s, self.t = 0, 0
            SID = "HEADER"
            self.header = ""
            for line in infile:
                if ((SID == "HEADER") and (line[:12] != "# sent_id = ")):
                    self.header += line
                elif (((SID == "") or SID == "HEADER") and (line[:12] == "# sent_id = ")):
                    SID = line[12:-1]
                    dumpHead = []
                    dumpHead.append(line[:-1])
                    logiS = []
                    TEXT = ""
                    tk = 0
                elif ((SID != "") and (line[:-1] != "")):
                    if (line[0] == "#"):
                        dumpHead.append(line[:-1])
                        if (line[:9] == "# text = "):
                            TEXT = line[9:-1]
                    else:
                        buf = line[:-1].split()
                        if (buf[3][0] == "["):
                            buf[3] = buf[3][1:-1]
                        buf.append("")  # holder for token change status (information place holder)
                        if (skipAg):
                            if ("-" not in buf[0]):
                                tk += 1
                                logiS.append(buf)
                        else:
                            logiS.append(buf)
                            if ("-" not in buf[0]):
                                tk += 1
                elif ((SID != "") and (line[:-1] == "")):
                    if not (self.isSIDin(SID)):
                        self.base.append([SID,TEXT,tk,dumpHead,logiS,""])
                        ## b[0] SID
                        ## b[1] TEXT
                        ## b[2] number of tokens (not including contracted words)
                        ## b[3] lines of the header
                        ## b[4] tokens (including contracted words)
                        ## b[5] status of change (initially empty)
                        self.s += 1
                        self.t += tk
                    else:
                        print("Duplicated SID:", SID)
                    SID = ""
            if (SID != ""):
                if not (self.isSIDin(SID)):
                    self.base.append([SID,TEXT,tk,dumpHead,logiS])
                    self.s += 1
                    self.t += tk
                else:
                    print("Duplicated SID:", SID)
            infile.close()
        self.base.sort()
    def addToBase(self,name, skipAg=False): # add a conllu file (name) to the base considering contracted word or not (skipAg)
        newAcc = 0
        infile = open(name, "r")
        SID = "HEADER"
        self.header = ""
        for line in infile:
            if ((SID == "HEADER") and (line[:12] != "# sent_id = ")):
                self.header += line
            elif (((SID == "") or SID == "HEADER") and (line[:12] == "# sent_id = ")):
                SID = line[12:-1]
                dumpHead = []
                dumpHead.append(line[:-1])
                logiS = []
                TEXT = ""
                tk = 0
            elif ((SID != "") and (line[:-1] != "")):
                if (line[0] == "#"):
                    dumpHead.append(line[:-1])
                    if (line[:9] == "# text = "):
                        TEXT = line[9:-1]
                else:
                    buf = line[:-1].split("\t")
                    if (buf[3][0] == "["):
                        buf[3] = buf[3][1:-1]
                    buf.append("")  # holder for token change status
                    if (skipAg):
                        if ("-" not in buf[0]):
                            tk += 1
                            logiS.append(buf)
                    else:
                        logiS.append(buf)
                        if ("-" not in buf[0]):
                            tk += 1
            elif ((SID != "") and (line[:-1] == "")):
                if not (self.isSIDin(SID)):
                    self.base.append([SID,TEXT,tk,dumpHead,logiS,""])
                        ## b[0] SID
                        ## b[1] TEXT
                        ## b[2] number of tokens (not including contracted words)
                        ## b[3] lines of the header
                        ## b[4] tokens (including contracted words)
                        ## b[5] status of change (initially empty)
                    self.s += 1
                    self.t += tk
                else:
                    newAcc += 1
                SID = ""
        if (SID != ""):
            if not (self.isSIDin(SID)):
                self.base.append([SID,TEXT,tk,dumpHead,logiS,""])
                self.s += 1
                self.t += tk
            else:
                newAcc += 1
        infile.close()
        print("Already existent:", newAcc)
    def removeSentInd(self, s):         # remove the sentence with id s (int) from base
        self.s -= 1
        self.t -= self.base[s][2]
        self.base.remove(s)
    def removeSentSID(self, s):         # remove the sentence with SID s (string) from base
        for i in range(self.s):
            if (self.base[i][0] == s):
                break
        if (i < self.s):
            self.s -= 1
            self.t -= self.base[s][2]
            self.base.remove(s)
        else:
            input("Trying to remove an absent SID")
    def getBase(self):   # return the whole base
        return self.base
    def getHeader(self):  # return in a single string the initial lines of the conllu
        return self.header
    def getS(self):   # return the number of sentences
        return self.s
    def getT(self):   # return the number of tokens (ignoring contracted words)
        return self.t
    def getSandT(self):   # return the number of sentences and tokens (ignoring contracted words)
        return self.s, self.t
    def getSentByID(self, SID):   # return a sentence by its SID (string) - return none if absent
        for b in self.base:
            if (b[0] == SID):
                return b
        return "none"
    def getSentByIndex(self, ind):  # return a sentence by its index (int) - return none if absent
        if (ind < self.s):
            return self.base[ind]
        else:
            return "none"
    def getSentInd(self, SID):  # return the index (int) of the sentence with SID (string) - return -1 if absent
        for i in range(len(self.base)):
            if (self.base[i][0] == SID):
                return i
        return -1
    def getSentID(self, ind):  # return the SID (string) for the sentence indexed by ind - return -1 if absent
        if (ind < self.s):
            return self.base[ind][0]
        else:
            return -1
    def isSIDin(self, SID):  # return True if the SID (string) is in the base
        for b in self.base:
            if (b[0] == SID):
                return True
        return False
    def isINDin(self, ind):  # return True if the index (int) is in the base
        return (ind < self.s)
    def isSentTagged(self, ind):  # return True if the sentence indexed by ind (int) has a non empty tag (b[5])
        return (self.base[ind][5] != "")
    def numberSentSize(self, size):  # return how many sentences have this size
        ans = 0
        for b in self.base:
            if (b[2] == size):
                ans += 1
        return ans
    def sentSizeRange(self):   # return the smallest and largest sentence size within the base
        smallest, largest = self.base[0][2], self.base[0][2]
        for b in self.base:
            if (b[2] < smallest):
                smallest = b[2]
            if (b[2] > largest):
                largest = b[2]
        return smallest, largest
    def getAllSIDs(self):           # return the list with all sentence IDs
        ans = []
        for b in self.base:
            ans.append(b[0])
        ans.sort()
        return ans
    def tagTokenAtSID(self,s,t,tag): # sets tag (string) for s is the SID (string), t is the token id (string)
        ind = self.getSentInd(s)
        for tk in self.base[ind][4]:
            if (t == tk[0]):
                tk[10] = tag
    def tagTokenAtSent(self,s,t,tag): # sets tag (string) for s is the sentence index (int), t is the token id (string)
        for tk in self.base[s][4]:
            if (t == tk[0]):
                tk[10] = tag
    def tagSent(self,s,tag):    # sets tag (string) for s is the sentence index (int)
        self.base[s][5] = tag
    def setSentTags(self):  # set the sentence tags (additional info) based on the tokens tags (additional info)
        for b in self.base:
            for tk in b[4]:
                if (tk[10] != ""):
                    if (b[5] == ""):
                        b[5] = tk[10]
                    else:
                        if (tk[10] < b[5]):
                            b[5] = tk[10]
    def sortBase(self):
        self.base.sort()
    def printSent(self, ind, outfile, nodeprel=False): # prints out a sentence by its index (int) in a outfile with all 10 fields
        for line in self.base[ind][3]:
            print(line, file=outfile)
        for tk in self.base[ind][4]:
            if nodeprel:
                print(tk[0], tk[1], tk[2], tk[3], tk[4], tk[5], "_", "_", "_", tk[9], sep="\t", file=outfile)
            else:
                print(tk[0], tk[1], tk[2], tk[3], tk[4], tk[5], tk[6], tk[7], tk[8], tk[9], sep="\t", file=outfile)
        print(file=outfile)
    def printHeaderToo(self, outfile, nodeprel=False): # prints out the whole base in an outfile with header
        print(self.header, end="", file=outfile)
        for ind in range(self.s):
            for line in self.base[ind][3]:
                print(line, file=outfile)
            for tk in self.base[ind][4]:
                if nodeprel:
                    print(tk[0], tk[1], tk[2], tk[3], tk[4], tk[5], "_", "_", "_", tk[9], sep="\t", file=outfile)
                else:
                    print(tk[0], tk[1], tk[2], tk[3], tk[4], tk[5], tk[6], tk[7], tk[8], tk[9], sep="\t", file=outfile)
            print(file=outfile)
    def printNoHeader(self, outfile, nodeprel=False): # prints out the whole base in an outfile without header
        for ind in range(self.s):
            for line in self.base[ind][3]:
                print(line, file=outfile)
            for tk in self.base[ind][4]:
                if nodeprel:
                    print(tk[0], tk[1], tk[2], tk[3], tk[4], tk[5], "_", "_", "_", tk[9], sep="\t", file=outfile)
                else:
                    print(tk[0], tk[1], tk[2], tk[3], tk[4], tk[5], tk[6], tk[7], tk[8], tk[9], sep="\t", file=outfile)
            print(file=outfile)


def usageExample(name):
    # Open a .conllu file with "name"
    base = conlluFile(name)
    # Get the number of sentences and tokens
    s, t = base.getSandT()
    # to count all tokens tagged with PUNCT PoS tag
    total_PUNCT = 0
    # get all sentences, one after another
    for i in range(s):
        b = base.getSentByIndex(i)
        # get all token, one after another
        for tk in b[4]:
            if (tk[3] == "PUNCT"):
                total_PUNCT += 1
    # say the percentage of PUNCT in the base
    print("Tokens tagged as PUNCT are {} out of {} ({}%)".format(total_PUNCT, t, round(t*100/t, 2)))






    


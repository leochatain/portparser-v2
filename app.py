import sys, os, datetime, random, base64, time
import streamlit as st
import streamlit.components.v1 as components
from tempfile import mkdtemp
from pathlib import Path
import pandas as pd
from huggingface_hub import hf_hub_download

#-----Initial Parameters----

# Must be always False in production. When DEBUG is set to True the interface do not call the parser. Mode to debug interface features in local development.   
DEBUG=False
# Embedding model. Options are: 'bert-base-portuguese-cased' or 'bert-base-multilingual-uncased'
MODEL='bert-base-portuguese-cased'


#-----Fuctions-----

# Format external files for interface compatibility
def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

def img_to_html(img_path, img_style='max-width: 100%;'):
    img_html = f"<img src='data:image/png;base64,{img_to_bytes(img_path)}' style='{img_style}'>"
    return img_html

# Call parser steps
def make_sentences(path_raw_text, path_text):
    try:
        #st.text(f'python ./src/portSentencer/portSent.py -o {path_text} -r -l 2048 {path_raw_text}')
        outcome = os.system(f'python ./src/portSentencer/portSent.py -o {path_text} -r -l 2048 {path_raw_text}')
        return f'S'+str(outcome)
    except Exception as e:
        return str(e)

def make_conllu(path_text, path_empty_conllu):
    try:
        outcome = os.system(f'python ./src/portTokenizer/portTok.py -o {path_empty_conllu} -m -s S000000 {path_text}')
        return 'T'+str(outcome)
    except Exception as e:
        return str(e)
        
def make_pred(path_empty_conllu, target_directory, model):
    try:
        outcome = os.system(f'python ./src/evalatin2024-latinpipe/latinpipe_evalatin24.py --load {model} --exp {target_directory} --test {path_empty_conllu}')
        return f'P'+str(outcome)
    except Exception as e:
        return str(e)

def make_postproc(path_predicted_conllu, path_final_conllu):
    try:
        outcome = os.system(f'python ./src/postproc/postprocess.py -o {path_final_conllu} {path_predicted_conllu}')
        return f'F'+str(outcome)
    except Exception as e:
        return str(e)

def get_predictions(path_prediction):
    try:
        with open(path_prediction, 'r') as f:
            st.text(f.read())
    except Exception as e:
        st.text('Resposta: '+e)


def run_pipeline(tmp_dir,code):

    path_text             = tmp_dir+"/"+code+"_input.txt"
    path_empty_conllu     = tmp_dir+"/"+code+"_input.conllu"
    #path_predicted_annot  = './src/annotation/'+code+'_input.predicted.conllu'
    path_predicted_conllu = tmp_dir+"/"+code+"_input.predicted.conllu"
    path_final_conllu     = tmp_dir+"/"+code+"_parsed.conllu"
    #model = '../Portparser.v2-latinpipe-core/model.weights.h5'
    model = hf_hub_download(repo_id="lucelene/Portparser.v2-latinpipe-core",
                            filename="model.weights.h5",
                            repo_type="model")
    model_op = hf_hub_download(repo_id="lucelene/Portparser.v2-latinpipe-core",
                               filename="options.json",
                               repo_type="model")
    model_mks = hf_hub_download(repo_id="lucelene/Portparser.v2-latinpipe-core",
                               filename="mappings.pkl",
                               repo_type="model")
    print("links", model, model_op)

#    with st.spinner(f'Tok {path_text} into {path_empty_conllu}'): 
    with st.spinner('Generating CoNLL-U...'): 
        #time.sleep(1)
        try:
            outcome = make_conllu(path_text, path_empty_conllu)
            #st.write("Tok executou!")
            #time.sleep(10)
        except Exception as e:
            st.write("Tok: "+e)
            time.sleep(10)
#    with st.spinner(f'{outcome} - Pred {path_empty_conllu} with {model} into {path_predicted_conllu}'): 
    with st.spinner('Predicting annotation...'): 
        #time.sleep(1)
        try:
            outcome = make_pred(path_empty_conllu, tmp_dir, model)
            #st.write("Pred executou!")
            #time.sleep(10)
        except Exception as e:
            st.write("Pred: "+e)
            time.sleep(10)
        #infile = open(path_predicted_conllu, "r")
        #empFile = infile.read()
        #infile.close()
    #with st.spinner(path_predicted_conllu+"\n"+empFile):
        #time.sleep(10)
#    with st.spinner(f'{outcome} - Post {path_predicted_conllu} into {path_final_conllu}'): 
    with st.spinner('Postprocessing...'): 
        #time.sleep(1)
        try:
            outcome = make_postproc(path_predicted_conllu, path_final_conllu)
            #st.write("Postp executou!")
            #time.sleep(10)
        except Exception as e:
            st.write("Postp: "+e)
            time.sleep(10)
#    with st.spinner(f'{outcome} - Done at {path_final_conllu}'):
    with st.spinner('Parsed!'):
        #infile = open(path_final_conllu, "r")
        #empFile = infile.read()
        #infile.close()
        time.sleep(1)
    return path_final_conllu

#-----Main Stuff-----
print("Running the HF server...")
print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}")
tmp_dir = mkdtemp()
#print(tmp_dir)
code = f'{datetime.datetime.now().strftime("%d%m%Y_%H%M%S%f")+"_"+str(random.randint(0, 9))}'
#print(code)
work_dir = './temp/'
os.chdir('.')
path_text = f'{tmp_dir}/{code}_input.txt'
path_final_conllu = f'{work_dir}parsed.conllu' # default to display
area=0
with open(path_final_conllu, 'r', encoding='utf-8') as f:content = f.read().split('\n')

#-----Interface-----
with open('./src/arborator-draft/arborator-draft.css','rb') as f: arborator_css = f.read().decode()
with open('./src/style.css') as f: css = f.read()

st.set_page_config(page_title='Portparser v.2', layout="wide")
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Grid
rowall = st.columns([2,26,2])
with rowall[1]:
    row2 = st.columns([6,4])
    # Head
    with row2[0]:
        st.markdown("<p id='logo-position'><b id='logo-title'><i>Portparser</i></b><b id='logo-version'>v.2</b><br><b id='logo-subtitle'>A parsing model for Brazilian Portuguese</b></p>",unsafe_allow_html=True)
        st.markdown("<p class='text'> This is Portparser, a parsing model for Brazilian Portuguese that follows the <a href='https://universaldependencies.org/'>Universal Dependencies (UD)</a> framework.\
        We built our model by using a recently released manually annotated corpus, the Porttinari-base, \
        and we explored different parsing methods and parameters for training. We also test multiple embedding models and parsing methods. \
        Portparser is the result of the best combination achieved in our experiments.</p><p class='text'>This model (version 2) is an evolution of the work previously reported \
        by <a href='https://aclanthology.org/2024.propor-1.41/'>Lopes and Pardo (2024)</a>, and all datasets and full instructions to reproduce our experiments are\
        freely available at the <a href='https://github.com/LuceleneL/Portparser.v2'>Portparser v2 repository</a>. More details about this work may also be found at \
        the <a href='https://sites.google.com/icmc.usp.br/poetisa'>POeTiSA project webpage</a>.</p>",unsafe_allow_html=True)
        with st.expander('To cite Portparser', expanded=False):
            st.code("""
            @inproceedings{lopes2024towards,
                title={Towards Portparser-a highly accurate parsing system for Brazilian Portuguese following the Universal Dependencies framework},
                author={Lopes, Lucelene and Pardo, Thiago},
                booktitle={Proceedings of the 16th International Conference on Computational Processing of Portuguese},
                pages={401--410},
                year={2024}
            }""")
    with row2[1]:
        st.markdown(img_to_html('./src/img/wordcloud_brasil5.png','width:100%; object-position: center top;'), unsafe_allow_html=True)
    # Mode to parse sentence 
    mode1, mode2 = st.tabs(['Single sentence', 'Multiple sentences'])
    # 'Single sentence'
    with mode1:
        rowmode1 = st.columns([1,28,1])
        with rowmode1[1]:
            st.write('Write a sentence and run to parse:')
            with st.form("parser"):
                text = st.text_input('Text: ')+' '
                #print("TEXTO",text,"TEXTO")
                #model_selected = MODEL+'-last4'
                submit = st.form_submit_button('Run')
            tab3, tab2, tab1 = st.tabs(["Tree","Table","CoNLL-U"])
            #with open(path_prediction, 'r', encoding='utf-8') as f: content = f.read()
            if submit:
                if not text.strip(): st.text("Can not parse empty text. Write a text above to parse.")                
                else:
                    try:
                        with open(path_text,'w',encoding='utf-8') as f: f.write(text)
                        if not DEBUG: path_final_conllu = run_pipeline(tmp_dir,code)
                        area=650
                        with open(path_final_conllu, 'r', encoding='utf-8') as f:
                            content = f.read()
                            tab1.text(content)
                            content = content.split('\n')
                            table = pd.DataFrame([line.split('\t') for line in content[2:]])
                            table.columns = ['ID','FORM','LEMMA','UPOS','XPOS','FEATS','HEAD','DEPREL','DEPS','MISC']
                            tab2.dataframe(table[:-2], use_container_width=True,hide_index=True)
                    except Exception as e:
                            st.text('Não deu certo a predição.'+str(e)+repr(e))
            with tab3:
                # Prepare UD tree
                content_str = '\n'.join(content)
                components.html(
                '<style>'+open('./src/arborator-draft/arborator-draft.css','rb').read().decode()+'</style>'+
                #'<style>{arborator_css}</style>'+
                """
                <script language="JavaScript" type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/d3/4.10.0/d3.js"></script>
                <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
                """+
                '<script>'+open('./src/arborator-draft/arborator-draft.js','rb').read().decode()+'</script>'+
                f'<conll>{content_str}</conll>'+
                '<script>new ArboratorDraft();</script>',height=area)

    # 'Multiple sentences'
    with mode2:
        rowmode2 = st.columns([1,13,1,14,1])
        predictions = False
        with rowmode2[1]:
            explanation  = 'To analyze several sentences at the same time, upload a text file. Your text must be in txt format (UTF-8). \
            If your text contains one sentence per line, select the "already segmented, ready to be parsed" option. \
            If your text contains several sentences in the same segment, select the "segment the text before parsing" option.'
            option1, option2 = 'already segmented, ready to be parsed','segment the text before parsing'
            split_option = st.radio(explanation,[option1,option2])
        with rowmode2[3]:
            with st.form("uploadfile_parser"):
                uploaded_file = st.file_uploader("Choose a file")
                submit = st.form_submit_button('Run')
            if submit:
                if uploaded_file is not None:
                    # Segment text first 
                    if split_option==option2:
                        path_raw_text = path_text[:-4]+'_raw.txt'
                        with open(path_raw_text, 'w') as f: f.write(uploaded_file.read().decode('utf-8'))
                        outcome = make_sentences(path_raw_text, path_text)
                    # Do not segment text first    
                    else:
                        with open(path_text,'w', encoding="utf-8") as f:f.write(uploaded_file.read().decode('utf-8')+' ')
                    if not DEBUG: path_final_conllu = run_pipeline(tmp_dir,code)
                    st.download_button( 
                        label="Download predictions",
                        data=open(path_final_conllu, 'r', encoding='utf-8').read(),
                        file_name='portparser_generated.conllu')
                    predictions = True
                else:
                    st.text('Submit a text file to parse.')
        if predictions:
            row1mode2 = st.columns([1,28,1])
            with row1mode2[1]:
                tab1mode2, tab2mode2 = st.tabs(["Sentences","CoNLL-U"])
                tab1mode2.text(open(path_text,"r").read())
                tab2mode2.text(open(path_final_conllu,"r").read())

    # Foot
    with st.container():
        logorow1 = st.columns([7,4,1,4,1,4,7])
        with logorow1[1]:      
            st.markdown("<a href='https://www.icmc.usp.br/'>"+img_to_html('./src/img/icmc.png')+"</a>",unsafe_allow_html=True)
        with logorow1[3]:      
            st.markdown("<a href='https://c4ai.inova.usp.br/pt/inicio/'>"+img_to_html('./src/img/c4ia.png')+"</a>",unsafe_allow_html=True)
        with logorow1[5]:
            st.markdown("<a href='https://sites.google.com/view/nilc-usp/'>"+img_to_html('./src/img/nilc-removebg.png','max-width:80%')+"</a>",unsafe_allow_html=True)
        logorow2 = st.columns([7,4,1,4,1,5,7])
        with logorow2[1]:      
            st.markdown("<a href='https://inova.usp.br/'>"+img_to_html('./src/img/inova_nobackground.png')+"</a>",unsafe_allow_html=True)
        with logorow2[3]:
            st.markdown("<a href='https://softex.br/'>" + img_to_html('./src/img/softex_nobackground.png') + "</a>",unsafe_allow_html=True)
        with logorow2[5]:      
            st.markdown("<a href='https://www.gov.br/mcti/pt-br'>" + img_to_html('./src/img/mcti_nobackground.png') + "</a>",unsafe_allow_html=True)
        logorow3 = st.columns([7,4,1,4,1,4,7])
        with logorow3[3]:      
            st.markdown("<a href='https://www.motorola.com.br/'>"+img_to_html('./src/img/motorola_nobackground.png', 'max-width:70%; object-position: center bottom')+"</a>",unsafe_allow_html=True)
        creditrow = st.columns([7,14,7])
        with creditrow[1]:      
            st.markdown('<p style="text-align: center;margin-top:10px"> Developed by Lucelene Lopes\
            <a href="https://github.com/LuceleneL"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-github" viewBox="0 0 16 16">\
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8"/>\
            </svg></i></a><br>Interface by Ana Carolina Rodrigues\
            <a href="https://github.com/anasampa"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-github" viewBox="0 0 16 16">\
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8"/>\
            </svg></i></a></p>',unsafe_allow_html=True)

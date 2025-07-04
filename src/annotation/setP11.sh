# Install Python3 and Libraries as a local user. 
python_config() {
    export PYTHON_VER="3.11.11" 
    export PYTHON_VER_SHORT="$(echo ${PYTHON_VER} | cut -d '.' -f1,2)"
    export PYTHON_REQ="/evalatin2024-latinpipe/requirements.txt"
    cd ~ 
    rm -rf ~/python && mkdir -p ~/python 
    echo "" >> ~/.bashrc 
    echo "export PATH=~/python/bin:$PATH" >> ~/.bashrc 
    source ~/.bashrc 
    wget --quiet --no-check-certificate "https://www.python.org/ftp/python/${PYTHON_VER}/Python-${PYTHON_VER}.tgz" 
    tar -zxvf ~/Python-${PYTHON_VER}.tgz 1>/dev/null 
    cd ~/Python-${PYTHON_VER}/ 
    echo "Python ${PYTHON_VER} - Installing in current logged-in user - $(whoami)" 
    echo "Python ${PYTHON_VER} - Installation in-progress. Please wait..." 
    ./configure --enable-optimizations --prefix=$HOME/python > /dev/null 2>&1; 
    echo "Python ${PYTHON_VER} - ETA: upto 5mins. Please wait..." 
    make altinstall > /dev/null 2>&1; 
    ln -s ~/python/bin/python${PYTHON_VER_SHORT} ~/python/bin/python3 
    ln -s ~/python/bin/pip${PYTHON_VER_SHORT} ~/python/bin/pip3 
     

    # Install PIP3
    wget --quiet --no-check-certificate https://bootstrap.pypa.io/get-pip.py -O - | python3 - --prefix=$HOME/python
    source ~/.bashrc
    ~/python/bin/pip3 install --upgrade pip 
    ~/python/bin/pip3 install --upgrade --no-cache-dir -r ${PYTHON_REQ} --use-pep517 
    cd ~ && rm -rf ~/Python-${PYTHON_VER}*


    ~/python/bin/python3 --version 
    ~/python/bin/pip3 --version 
    echo "Python ${PYTHON_VER} - Setup Completed!" 
}

# Function Call
python_config
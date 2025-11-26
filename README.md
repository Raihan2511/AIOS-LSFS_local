<!-- # AIOS-LSFS
This is the official code implementation of paper [From Commands to Prompts: LLM-based Semantic File System for AIOS](https://arxiv.org/pdf/2410.11843).

## 🏠 Architecture of LSFS
<p align="center">
<img src="assets/lsfs-arc.png">
</p>

## 🚀 Quickstart

### ⚙️ Installation
```
conda create -n lsfs python=3.11
conda activate lsfs
pip install -r requirements.txt
```

### 🏃Run

> [!IMPORTANT]
> Please make sure you have read the instructions in [AIOS](https://github.com/agiresearch/AIOS) to set up the environment and launch the AIOS kernel and set up the configurations in ```aios/config/config.yaml```.

> [!WARNING]
> The rollback feature of the AIOS terminal requires the connection to the redis server. Make sure you have the redis server running if you would like to use the rollback feature.

· You need to create a folder to put the files you want to manage, which will be mounted as the root directory of LSFS. By default, it is ```./root```.

After that, you can run the following command to start the LSFS terminal.

```
python scripts/run_terminal.py
```
When you successfully enter the system, the interface is as follows:

<p align="center">
<img src="assets/example.png">
</p>


Then you can start interacting with the LSFS terminal by typing natural language commands. 

## 📎 Available Functions
LSFS currently supports the following operations, with more features planned for future releases:

| Operation | Description | Example Commands |
|-----------|-------------|------------------|
| Mount | Mount a directory as the root folder for LSFS | `mount the /root as the root folder for the LSFS` |
| Create | Create files or directories with semantic indexing | `create a aios.txt file in the root folder` |
| Write | Write content to a file | `write 'this is AIOS' into the aios.txt file` |
| Search file | Perform keyword-based or semantic search of files | `search 3 files that are mostly related to Machine Learning` |
| Rollback | Restore files to previous versions | `rollback the aios.txt to its previous 2 versions` |
| Share | Generate shareable links for files | `generate a shareable link for the aios.txt` |

## APIs
Please refer to the [Cerebrum (AIOS SDK)](https://github.com/agiresearch/Cerebrum) for more details of the LSFS APIs. 
- [Traditional file operations](https://github.com/agiresearch/Cerebrum/blob/main/cerebrum/storage/apis.py)
- [Semantic file operations](https://github.com/agiresearch/Cerebrum/blob/main/cerebrum/llm/apis.py)

## 🌹Reference
If you find this project useful, please cite our paper:

```
@inproceedings{
  shi2025from,
  title={From Commands to Prompts: {LLM}-based Semantic File System for AIOS},
  author={Zeru Shi and Kai Mei and Mingyu Jin and Yongye Su and Chaoji Zuo and Wenyue Hua and Wujiang Xu and Yujie Ren and Zirui Liu and Mengnan Du and Dong Deng and Yongfeng Zhang},
  booktitle={The Thirteenth International Conference on Learning Representations},
  year={2025},
  url={https://openreview.net/forum?id=2G021ZqUEZ}
}
``` -->

# AIOS-LSFS_local – Ubuntu Setup Guide

This README provides a step-by-step workflow to install, configure, and run **AIOS-LSFS_local** on Ubuntu.

---

## 1. Install Miniconda

```bash
cd ~
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

Restart the terminal, then verify:

```bash
conda --version
```

---

## 2. Create Conda Environment

```bash
conda create -n lsfs python=3.11 -y
```

---

## 3. Clone the Repository

Check if Git is installed:

```bash
git --version
```

If not:

```bash
sudo apt install git -y
```

Clone the project:

```bash
cd ~
git clone https://github.com/Raihan2511/AIOS-LSFS_local
cd AIOS-LSFS_local
```

Checkout your working branch:

```bash
git checkout my-new-branch
```

---

## 4. Activate Environment & Install Dependencies

```bash
conda activate lsfs
pip install -r requirements.txt
pip install sentence-transformers
```

---

## 5. Configure the Application

Open:

```
aios/config/config.yaml
```

### Option A – Using API Key

```yaml
llm_provider: openai
api_key: "your_api_key_here"
```

### Option B – Using Local Ollama Model

1. Download Ollama: [https://ollama.com/download](https://ollama.com/download)
2. Start server:

```bash
ollama serve
```

3. Pull a model:

```bash
ollama pull qwen2.5:7b
```

4. Update config.yaml:

```yaml
llm_provider: ollama
model_name: "qwen2.5:7b"
```

---

## 6. Start the Kernel

Inside the project directory:

```bash
bash runtime/launch_kernel.sh
```

---

## 7. Start the Terminal Interface

Open a new terminal:

```bash
conda activate lsfs
python Scripts/run_terminal.py
```

Inside the LSFS terminal, type:

```
help
```

---

This completes the setup for AIOS-LSFS_local on Ubuntu.


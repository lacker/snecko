# Snecko Brain
Analyzing Slay the Spire, using machine learning.

# Setting up the AI part

```bash
# Install conda. I'll leave that to another guide, but I used Python 3.7 / 3.8 and miniconda.
# First create a conda environment:
conda create --name snecko
conda activate snecko

# Install dependencies
conda install -c pytorch -c fastai fastai
conda install -c conda-forge jupyterlab
conda install -c conda-forge notebook

# Run jupyter, then open scratch.ipynb
jupyter notebook

# In subsequent runs, instead of creating a new environment, reactivate your old one:
conda activate snecko
```

# Setting up the Slay The Spire mod

Install mods...

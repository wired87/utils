







# 2 cpu, 4gib ram

create_=r"""
"""

def init_debian(repo):
    return rf"""
sudo apt update && sudo apt install python3.11-venv python3-tk git tmux -y && \
python3 -m venv workenv && git clone https://github.com/wired87/qfs.git && \
export PYTHONPATH=$PYTHONPATH:$(pwd) && source workenv/bin/activate && cd qfs && pip install -r r.txt  

DJ + && \ python manage.py migrate && python manage.py collectstatic 
"""

ENDODE_META=f"""
python3 admin_data/extractors/functions/encode/cell_line_processor/metadata_processor.py
"""


PULL_SUB = "cd qf_sim && git pull && cd .."

#sudo tail -n 100 /var/log/nginx/error.log

# 18728
RUN_ENCODE = "admin_data/extractors/functions/encode/cell_line_processor/metadata_processor.py"
RUN_THALMUS_TRANSCRIPT = "export PYTHONPATH=$PYTHONPATH:$(pwd) gnn/processing/layer/cell_layer.py"
R_CELL_LIKNE_PROC=rf"""python3 admin_data/extractors/functions/encode/cell_line_processor/cell_line_processor.py"""
REMBEDER = f"""python3 ggoogle/spanner/dj/views/embedder.py"""

IMIT=rf"""
source workenv/bin/activate && cd qfs && export PYTHONPATH=$PYTHONPATH:$(pwd)
"""
token="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"
RUN_PROTEIN=f"gnn/processing/layer/uniprot/main.py"
run = "python3 gnn/processing/layer/gene_layer.py"

check_fiel_size="""stat --format="%s bytes" train_data/non_neuronal_cell.h5ad"""
restart = """
cd work && source workenv/bin/activate && cd brainmaster_processing && export PYTHONPATH=$PYTHONPATH:$(pwd)  
"""

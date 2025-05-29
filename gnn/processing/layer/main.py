"""
from data.extractors.functions.encode.cell_line_processor.cell_line_processor import CellLineProcessor
from ggoogle.spanner.from_nx import SpannerFromNx
from gnn.processing.layer.encode_experiment.processor import EncodeProcessor
from gnn.processing.layer.gocam_layer import GoCam
from gnn.processing.layer.owl.ro.main import ROHandler
from gnn.processing.layer.uniprot.main import UniProtKBGraphBuilder
from gnn.processing.layer.cell_layer import CellLayer
from gnn.processing.layer.eco_layer import ECO
from gnn.processing.layer.gene_layer import GeneLayer
from gnn.processing.layer.goterm_layer import GoTermLayer
from gnn.processing.layer.reactome_layer import ReactomeLayer


class LayerProcessor:

    def __init__.py(self, bucket, success_list):

        self.bucket = bucket
        self.spanner_batch = SpannerFromNx()
        self.success_list=success_list

    async def process_layer(self, data=None, parent=None, layer=None):
        todo:
        - create flat hierarchy for nodes - now just embed whole nested obj
        - save ckpt instant to cloud -> todo: merge
        if parent == "site":
            pass
        elif parent == "free_mode":
            pass

        print(f"working {parent}.{layer}")
        if layer == "ECO":
            # v1 done
            eco = ECO(parent=parent, layer=layer)
            await eco.main(data)

        #if parent == "cell":
        if layer == "transcriptomes":
            cell_layer = CellLayer(parent=parent, layer=layer)
            await cell_layer.main(data)

        if layer == "gocam":
            # v1 done
            gc=GoCam(parent=parent, layer=layer)
            await gc.main(data)

        elif layer == "reactome":
            reactome = ReactomeLayer(parent=parent, layer=layer)
            await reactome.main(data)

        elif layer == "gene":
            # sub type non important
            gene_layer = GeneLayer(parent=parent, layer=layer)
            await gene_layer.main(data)

        elif layer == "protein":
            up = UniProtKBGraphBuilder(data=data, parent=parent, layer=layer)
            await up.build_graph()

        elif layer == "GO":
            # v1 done
            goterm_layer = GoTermLayer(parent=parent, layer=layer)
            await goterm_layer.process(data)

        elif layer == "RO":
            ro_handler = ROHandler(parent=parent, layer=layer)
            await ro_handler.main(data)



        if layer == "cell_line":
            encode_cl_processor = CellLineProcessor(layer, parent)
            await encode_cl_processor.process_main(data)

        if layer == "brain_experiment":
            #metadata = data.pop("@graph")
            encode_handler = EncodeProcessor()
            await encode_handler.main(data=data)


"""

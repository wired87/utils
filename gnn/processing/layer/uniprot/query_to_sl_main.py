
from utils.file import convert_tsv
from ggoogle.spanner.acore import SpannerAsyncHelper
from ggoogle.spanner.dj import SpannerEmbedder
from ggoogle.spanner.graph_loader import SpannerRAG, SpannerCore
from ggoogle.vertexai.gem.query_to_keywords import gem_extract_goterm_keywords
from gnn.processing.layer.gene.ensembl_core import EnsCore
from utils.utils import GraphUtils
import asyncio
import pprint
from typing import Dict, List

class UPQueryToSLGenes:

    def __init__(self):
        self.table_name = "SL"
        self.rag = SpannerRAG()
        self.g_utils = GraphUtils(table_name=self.table_name, upload_to="sp")
        self.sl_file = r"C:\Users\wired\OneDrive\Desktop\Projects\bm\gnn\processing\layer\uniprot\sl.tsv"
        self.sp = SpannerCore()
        self.asp = SpannerAsyncHelper()
        self.sembedder = SpannerEmbedder()
        self.ckpt_path = r"C:\Users\wired\OneDrive\Desktop\Projects\bm\gnn\processing\layer\uniprot\cc_pred_ckpt.json"
        self.ens_handler = EnsCore()
        self.up = False

        self.embed_cols = [
            "id",
            "name",
            "description",
            "synonyms",
            "content"
        ]
        self.embed_keys_not_null = [
                "id",
                "name",
                "description"
            ]

        self.len_all_ids = len(self.g_utils.get_ids())

    def embed_sl(self):
        self.sembedder.main(
            tables=[self.table_name],
            keys=self.embed_cols,
            keys_not_null=self.embed_keys_not_null,
            embed_limit=self.len_all_ids
        )


    async def filter_col_names(self, row: dict) -> dict:
        """Sanitize column names and format row properly"""
        new_row = {"id": row.get("Subcellular location ID")}
        # print("new_row:", new_row)
        for k, v in row.items():
            if k != "Subcellular location ID":
                sanitized_key = k.replace(" ", "_").replace("(", "").replace(")", "").lower()
                new_row[sanitized_key] = v
                new_row["type"] = self.table_name
                new_row["parent"] = ["cell"]
        return new_row

    async def upload_sl_table_process(self):
        map_content: List[Dict] = convert_tsv(path=self.sl_file)
        self.sp.check_add_table(
            table_name=self.table_name,
            ttype="node",
            schema_fetch=False
        )

        sanetized_content = []
        for row in map_content:
            sanetized_content.append(await self.filter_col_names(row))
        print("Sanetized content")
        pprint.pp(sanetized_content)

        format_keys={}
        format_keys.update({
            k.lower().replace(" ", "_"): self.sp.get_spanner_type(v)
            for k, v in sanetized_content[0].items()
        })

        self.sp.check_add_cols_batch(
            keys=format_keys,
            t=self.table_name
        )
        print(f"Upsert {len(sanetized_content)} to {self.table_name}")
        self.sp.update_insert(
            table=self.table_name,
            rows=sanetized_content
        )

    def gene_for_sl_url(self, sl_name):
        return f"https://rest.uniprot.org/uniprotkb/search?query=organism_id:9606+AND+cc_subcellular_location:%22{'+'.join(sl_name.split(' '))}%22+AND+reviewed:true&fields=gene_names,accession&format=tsv&size=500"

    async def genes_for_sl(self, item):
        sl_name = item["name"]
        #print("Get genes from sl", sl_name)

        content = await self.g_utils.utils.aget(url=self.gene_for_sl_url(sl_name), j=False)

        #print("Contenet", content)

        if isinstance(content, tuple):
            content = content[0]

        sl_name = item["name"].lower().replace(" ", '_')
        struct = {
            "name": sl_name,
            "genes": []
        }

        map_content: Dict = convert_tsv(content=content)
        for gene in map_content:
            gene_main_name = gene["Gene Names"].split()[0]

            #print("single gene:", gene_main_name)
            struct["genes"].append(
                {
                    "gene_name": gene_main_name,
                }
            )
        #pprint.pp(struct)
        return struct



    async def gene_coords_sp(self, struct_item:dict):

        async def gene_processor(gene_name):
            query = f"""
                    SELECT name, start, `end`, coord_system_seq_name FROM GENE 
                    WHERE name = '{gene_name}'
                    """
            coords = await self.asp.asnap(
                query=query
            )
            #coords = coords[0]
            #pprint.pp(coords)
            coords=[row for row in coords.rows]####################
            if len(coords):
                if len(coords) > 1:
                    for coord in coords:
                        if coord[3].isnumeric() or coord[3] in ["X", "Y"]:
                            coords = coord
                            break
                        elif "HSCHR" in coord[3]:
                            coord_sys_raw:str = coord[3].split("_")[0] #HSCHR6
                            coord_sys=""
                            for char in coord_sys_raw:
                                if char.isnumeric():
                                    coord_sys+=char
                            coord[3] = coord_sys
                            coords = coord
                            break
                else:
                    coords = coords[0]

                #print("Coords", coords)
                return {
                        "gene_name": coords[0],
                        "start": coords[1],
                        "end": coords[2],
                        "coord_sys": coords[3],
                    }
            else:
                # case given is the gene family instead of a single gene -> nothing found
                print(f"Content for gene {gene_name} couldnt be gathered", )
                return {
                        "gene_name": gene_name,
                    }


        struct_item["genes"]=await asyncio.gather(*[
            gene_processor(
                gene_name=gene["gene_name"]
            )for gene in struct_item["genes"]
        ])
        return struct_item


    async def regulatory_handler(self, struct_item:dict):


        async def regulatory_processor(gene_item:dict):
            start = gene_item.get("start")
            end = gene_item.get("end")
            coord_sys = gene_item.get("coord_sys")
            if start and end and coord_sys:
                regulatory_content=await self.g_utils.utils.aget(
                    url=self.ens_handler.regulatory_url(
                        start=start,
                        end=end,
                        coord_sys=coord_sys,
                        ),
                        j="y",
                    )
                print("Regulatory content fetched:", regulatory_content)
                if isinstance(regulatory_content, tuple):
                    regulatory_content = regulatory_content[0]
                """
                SHOULD BE LIST [
                    bound_end: 153725827
                    bound_start: 153724867
                    description: Predicted promoter
                    end: 153725827
                    feature_type: regulatory
                    id: ENSRX_9492FR
                    seq_region_name: X
                    source: Regulatory_Build
                    start: 153725327
                    strand: 0
                ]
                """
                gene_item["regulatory_elements"] = regulatory_content

            else:
                gene_item["regulatory_elements"] = []
            return gene_item

        struct_item["genes"] = await asyncio.gather(*[
            regulatory_processor(item) for item in struct_item["genes"]
        ])

        return struct_item



    async def main(self, query:str):
        session=await self.asp.acreate_session()
        if self.up:
            await self.upload_sl_table_process()
        else:

            keywords = await gem_extract_goterm_keywords(query)

            keywords = keywords["answer"].split(",")

            response = self.rag.spanner_vector_search(
                data=keywords,
                table_name="SL",
                custom=True,
                limit=3,
                select=["id", "name"],
                embed_row="embed"
            )
            filtered_res = []
            for r in response:
                filtered_res.append({
                    "id": r[0],
                    "name": r[1],
                    "distance": r[2],
                })

            struct:List[Dict]=await asyncio.gather(*[
                self.genes_for_sl(row) for row in filtered_res
            ])
            #pprint.pp(struct)

            print("Start coord process")
            struct =await asyncio.gather(*[
                self.gene_coords_sp(item) for item in struct
            ])

            print("Fetch regulatory features")
            struct =await asyncio.gather(*[
                self.regulatory_handler(item) for item in struct
            ])

            pprint.pp(struct)
            print("Process finished")
            self.g_utils.save_ckpt(path=self.ckpt_path, content=struct)
            await self.asp.aclient.delete_session(name=session.name)
            return struct



if __name__ == "__main__":
    main = UPQueryToSLGenes()
    struct = asyncio.run(main.main(query="Membrane"))
    #main.embed_sl()
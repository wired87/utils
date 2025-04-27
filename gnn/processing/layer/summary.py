"""
cellular_component -> defined in uniprot layer
EXAMPLE:
{
    "evidences": [
      {
        "evidenceCode": "ECO:0000256",
        "source": "RuleBase",
        "id": "RU367096"
      }
    ],
    "id": "KW-1003",
    "category": "Cellular component",
    "name": "Cell membrane"
},

references -> def in uniprot layer





"""


all_layers = {
    "cellular_component": {

    },
    "references": {},
    "uniprot": {

    },
    "reactome": {

    },
    "species": {
        "set": [
            "reactome",
            "uniprot"
        ]
    },
    "goterm": {}, #ICLUDE CHEBI ONTOLOGY -> ETCH CEHBI AND RUN TOGETHER
    "bfo": {}, #         "property": "BFO:0000050",

}
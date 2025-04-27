"""
Todo:
Reactome compartment have refer to goterms that doesn not exist in nodes -> build function
Todo: remove xref fields after creating edges
Relational ontology: change "go -> ro -> molecule etc" TO go -> ro , ro -> molecule
rm go ->




NODE SCHEMAS SET: [
'CHEBI:9',
'GO:20', '
NCBITAXON:11',
 'PR:9',
  'UBERON:12',#
   'CL:15',#
    'GOCHE:5',
    'OMO:6',
    'OBA:9',
    'IAO:12',
    'RO:24',
    'PATO:14',
    'FAO:7',
    'SO:12', #
    'GOREL:9',
    'BSPO:4',
    'PO:9',
    'OPL:6',
    'BFO:16', 'CARO:6', 'DDANAT:7', 'IS:2',

    'INVERSEOF:2', 'SUBPROPERTYOF:2', 'MOD:2', 'ENVO:10',
    'TYPE:2', 'IDO:2', 'NBO:2', 'OBI:7']
EDGE SCHEMAS SET: ['IS_relationship_destination_CHEBI:4\n', 'CHEBI_is_a_CHEBI:4\n', 'CHEBI_relationship_destination_IS:4\n', 'RO_relationship_destination_CHEBI:4\n', 'GO_ro:0004009_CHEBI:4\n', 'GO_ro:0004007_CHEBI:4\n', 'GO_ro:0004008_CHEBI:4\n', 'CHEBI_relationship_destination_RO:4\n', 'CHEBI_ro:0000087_CHEBI:4\n', 'GO_ro:0000057_CHEBI:4\n', 'GO_relationship_destination_IS:4\n', 'GO_is_a_GO:7\n', 'GO_relationship_destination_RO:4\n', 'GO_ro:0002162_NCBITAXON:4\n', 'GO_relationship_destination_BFO:4\n', 'GO_bfo:0000050_GO:4\n', 'GO_ro:0004009_GO:4\n', 'RO_relationship_destination_NCBITAXON:4\n', 'NCBITAXON_ro:0002162_NCBITAXON:4\n', 'NCBITAXON_relationship_destination_IS:4\n', 'NCBITAXON_is_a_NCBITAXON:4\n', 'IS_relationship_destination_GO:4\n', 'GO_ro:0002213_GO:4\n', 'GO_bfo:0000066_GO:4\n', 'BFO_relationship_destination_GO:4\n', 'GO_ro:0002211_GO:4\n', 'GO_ro:0002212_GO:4\n', 'GO_ro:0000057_GO:4\n', 'IS_relationship_destination_NCBITAXON:4\n', 'RO_relationship_destination_GO:4\n', 'GO_ro:0002608_CHEBI:4\n', 'GO_ro:0002220_GO:4\n', 'GO_ro:0002608_GO:4\n', 'CL_ro:0002215_GO:4\n', 'GO_ro:0002592_GO:4\n', 'GO_ro:0000053_PATO:4\n', 'GO_ro:0002341_GO:4\n', 'GO_ro:0002339_GO:4\n', 'GO_ro:0004009_GOCHE:4\n', 'GO_ro:0002232_GO:4\n', 'GO_ro:0002588_GO:4\n', 'GOREL_relationship_destination_GO:4\n', 'GO_gorel:0012006_GO:4\n', 'GO_ro:0002215_GO:4\n', 'GO_ro:0012001_CHEBI:4\n', 'GO_ro:0002224_GO:4\n', 'GO_ro:0002342_GO:4\n', 'GO_relationship_destination_GOREL:4\n', 'RO_relationship_destination_PR:4\n', 'GO_ro:0004009_PR:4\n', 'PR_relationship_destination_IS:4\n', 'PR_is_a_PR:4\n', 'PR_is_a_CHEBI:4\n', 'GO_bfo:0000051_GO:4\n', 'GO_ro:0002608_CL:4\n', 'GO_bfo:0000066_CL:4\n', 'GO_ro:0002315_CL:4\n', 'GO_ro:0002565_CL:4\n', 'GO_ro:0002216_GO:4\n', 'CL_ro:0000056_GO:4\n', 'GO_ro:0012008_GO:4\n', 'GO_ro:0002007_GO:4\n', 'GO_ro:0002296_UBERON:4\n', 'RO_relationship_destination_UBERON:4\n', 'GO_ro:0002297_UBERON:4\n', 'UBERON_relationship_destination_IS:4\n', 'UBERON_is_a_UBERON:7\n', 'GO_ro:0012003_CL:4\n', 'GO_ro:0002298_UBERON:4\n', 'GO_ro:0012014_GO:4\n', 'UBERON_ro:0002215_GO:4\n', 'CL_ro:0002160_NCBITAXON:4\n', 'FAO_ro:0002160_NCBITAXON:4\n', 'GO_ro:0004009_NCBITAXON:4\n', 'GO_ro:0002231_GO:4\n', 'CHEBI_relationship_destination_BFO:4\n', 'CHEBI_bfo:0000051_CHEBI:4\n', 'GO_ro:0012013_GO:4\n', 'GO_ro:0002010_GO:4\n', 'IS_relationship_destination_UBERON:4\n', 'GO_ro:0002338_GO:4\n', 'GO_ro:0002590_GO:4\n', 'GO_ro:0002348_CL:4\n', 'GO_ro:0004009_CL:4\n', 'GO_ro:0004009_SO:4\n', 'GO_ro:0002578_GO:4\n', 'UBERON_ro:0000056_GO:4\n', 'UBERON_relationship_destination_RO:4\n', 'UBERON_ro:0002387_UBERON:4\n', 'BFO_relationship_destination_UBERON:4\n', 'UBERON_bfo:0000050_UBERON:4\n', 'GO_ro:0002131_GO:4\n', 'GO_ro:0002296_CL:4\n', 'UBERON_ro:0002576_UBERON:4\n', 'UBERON_relationship_destination_BFO:4\n', 'GO_ro:0002505_CHEBI:4\n', 'GO_bfo:0000066_UBERON:4\n', 'BFO_relationship_destination_CHEBI:4\n', 'GO_bfo:0000051_CHEBI:4\n', 'UBERON_bfo:0000051_CHEBI:4\n', 'GO_ro:0002298_GO:4\n', 'GO_ro:0002332_CHEBI:4\n', 'UBERON_bfo:0000051_UBERON:4\n', 'UBERON_ro:0002252_UBERON:4\n', 'UBERON_ro:0002178_UBERON:4\n', 'UBERON_ro:0002220_UBERON:4\n', 'UBERON_ro:0002179_UBERON:4\n', 'CL_bfo:0000050_UBERON:4\n', 'UBERON_ro:0002176_UBERON:4\n', 'UBERON_ro:0002376_UBERON:4\n', 'GO_ro:0002629_GO:4\n', 'UBERON_ro:0002473_GO:4\n', 'GO_bfo:0000050_CL:4\n', 'GO_ro:0002299_CL:4\n', 'IS_relationship_destination_PR:4\n', 'GO_ro:0019000_OBA:4\n', 'UBERON_relationship_destination_BSPO:4\n', 'UBERON_bspo:0000120_UBERON:4\n', 'UBERON_bspo:0000121_UBERON:4\n', 'UBERON_ro:0002150_UBERON:4\n', 'UBERON_ro:0002572_UBERON:4\n', 'UBERON_ro:0001025_UBERON:4\n', 'UBERON_ro:0002160_NCBITAXON:4\n', 'BSPO_relationship_destination_UBERON:4\n', 'UBERON_ro:0002371_UBERON:4\n', 'GO_ro:0004007_PR:4\n', 'GO_ro:0000057_CL:4\n', 'CL_relationship_destination_BFO:4\n', 'RO_relationship_destination_CL:4\n', 'CL_relationship_destination_IS:4\n', 'CL_is_a_CL:7\n', 'GO_ro:0002230_OPL:4\n', 'GO_ro:0002224_OPL:4\n', 'GO_ro:0019001_OBA:4\n', 'GO_ro:0002349_CL:4\n', 'GO_ro:0002630_GO:4\n', 'GOCHE_relationship_destination_IS:4\n', 'GOCHE_is_a_GOCHE:4\n', 'RO_relationship_destination_GOCHE:4\n', 'GO_ro:0004007_GOCHE:4\n', 'GO_ro:0004008_GOCHE:4\n', 'IS_relationship_destination_GOCHE:4\n', 'UBERON_ro:0002202_UBERON:4\n', 'UBERON_core#subdivision:of_UBERON:4\n', 'UBERON_ro:0002221_UBERON:4\n', 'UBERON_ro:0002219_UBERON:4\n', 'OMO_relationship_destination_TYPE:4\n', 'OMO_type_IAO:4\n', 'OBA_relationship_destination_IS:4\n', 'OBA_is_a_OBA:4\n', 'RO_relationship_destination_OBA:4\n', 'GO_ro:0019002_OBA:4\n', 'GO_ro:0002299_UBERON:4\n', 'GO_ro:0002230_GO:4\n', 'GO_ro:0002231_CL:4\n', 'GO_ro:0002232_CL:4\n', 'CL_ro:0002162_NCBITAXON:4\n', 'UBERON_bspo:0000126_UBERON:4\n', 'UBERON_ro:0002226_UBERON:4\n', 'CHEBI_is_a_PR:4\n', 'GO_ro:0002344_UBERON:4\n', 'GO_ro:0002341_UBERON:4\n', 'GO_ro:0002339_UBERON:4\n', 'GO_ro:0002338_UBERON:4\n', 'UBERON_bfo:0000067_GO:4\n', 'UBERON_core#site:of_GO:4\n', 'GO_ro:0004008_SO:4\n', 'GO_ro:0002355_GO:4\n', 'GO_ro:0002315_PO:4\n', 'GO_ro:0002348_PO:4\n', 'UBERON_ro:0002170_UBERON:4\n', 'IS_relationship_destination_CL:4\n', 'CL_relationship_destination_RO:4\n', 'CL_ro:0000053_PATO:4\n', 'UBERON_ro:0002473_CL:4\n', 'CL_ro:0002203_CL:4\n', 'BFO_relationship_destination_CL:4\n', 'GO_ro:0002131_CL:4\n', 'CL_ro:0002120_CL:4\n', 'UBERON_ro:0002473_UBERON:4\n', 'UBERON_ro:0000086_PATO:4\n', 'CL_ro:0002202_CL:4\n', 'GO_ro:0002297_CL:4\n', 'UBERON_ro:0002433_UBERON:4\n', 'UBERON_bfo:0000051_CL:4\n', 'GO_ro:0002344_GO:4\n', 'UBERON_ro:0002322_ENVO:4\n', 'UBERON_ro:0002551_UBERON:4\n', 'UBERON_ro:0002131_UBERON:4\n', 'UBERON_ro:0002254_UBERON:4\n', 'UBERON_bspo:0000099_UBERON:4\n', 'CL_ro:0002216_GO:4\n', 'CL_ro:0003000_UBERON:4\n', 'CL_ro:0002100_UBERON:4\n', 'UBERON_ro:0002373_UBERON:4\n', 'CL_is_a_BFO:4\n', 'UBERON_is_a_BFO:7\n', 'GO_ro:0002296_GO:4\n', 'GO_ro:0004008_GO:4\n', 'UBERON_ro:0003001_CL:4\n', 'UBERON_ro:0002380_UBERON:4\n', 'UBERON_ro:0002134_UBERON:4\n', 'UBERON_ro:0002216_GO:4\n', 'TYPE_relationship_destination_IAO:4\n', 'IAO_type_IAO:4\n', 'GO_ro:0002296_PO:4\n', 'IAO_relationship_destination_TYPE:4\n', 'PR_ro:0002353_GO:4\n', 'UBERON_ro:0003001_UBERON:4\n', 'GO_bfo:0000050_PO:4\n', 'GO_ro:0002343_GO:4\n', 'GO_ro:0002332_GOCHE:4\n', 'UBERON_ro:0002570_UBERON:4\n', 'UBERON_core#extends:fibers:into_UBERON:4\n', 'UBERON_ro:0002494_UBERON:4\n', 'GO_ro:0002299_PO:4\n', 'CL_ro:0002353_GO:4\n', 'UBERON_ro:0002005_UBERON:4\n', 'GO_ro:0002298_PO:4\n', 'GO_ro:0002297_PO:4\n', 'GO_ro:0000057_PR:4\n', 'GO_gorel:0002004_GO:4\n', 'GO_bfo:0000066_PO:4\n', 'GO_ro:0002412_GO:4\n', 'GO_ro:0002298_CL:4\n', 'GO_ro:0002356_PO:4\n', 'GO_ro:0002297_GO:4\n', 'CL_relationship_destination_GO:4\n', 'CL_relationship_destination_CL:4\n', 'CL_relationship_destination_PR:4\n', 'CL_ro:0002104_GO:4\n', 'RO_relationship_destination_SUBPROPERTYOF:4\n', 'RO_subpropertyof_RO:4\n', 'GO_ro:0002008_SO:4\n', 'GO_ro:0019001_PATO:4\n', 'GO_ro:0019002_PATO:4\n', 'UBERON_ro:0002082_GO:4\n', 'GO_ro:0002356_UBERON:4\n', 'IS_relationship_destination_OBA:4\n', 'PATO_relationship_destination_IS:4\n', 'PATO_is_a_PATO:7\n', 'RO_relationship_destination_PATO:4\n', 'CL_ro:0002292_PR:4\n', 'GO_ro:0002297_FAO:4\n', 'GO_ro:0002608_PR:4\n', 'GO_ro:0002296_FAO:4\n', 'GO_ro:0002334_GO:4\n', 'UBERON_ro:0002473_CHEBI:4\n', 'PR_relationship_destination_BFO:4\n', 'PR_bfo:0000051_MOD:4\n', 'UBERON_ro:0002007_UBERON:4\n', 'CL_cl:4030044_GO:4\n', 'OPL_bfo:0000051_GO:4\n', 'GO_ro:0002092_GO:4\n', 'GO_ro:0002591_GO:4\n', 'UBERON_ro:0002495_UBERON:4\n', 'GO_is_a_CARO:4\n', 'GO_is_a_UBERON:4\n', 'GO_ro:0002356_CL:4\n', 'GO_ro:0002355_UBERON:4\n', 'GO_ro:0002588_CHEBI:4\n', 'GO_ro:0002315_DDANAT:4\n', 'GO_ro:0000057_SO:4\n', 'UBERON_ro:0002491_UBERON:4\n', 'UBERON_ro:0002007_CL:4\n', 'FAO_relationship_destination_BFO:4\n', 'FAO_bfo:0000050_FAO:4\n', 'FAO_relationship_destination_IS:4\n', 'FAO_is_a_FAO:4\n', 'RO_relationship_destination_FAO:4\n', 'IS_relationship_destination_FAO:4\n', 'UBERON_ro:0002207_UBERON:4\n', 'UBERON_ro:0002256_UBERON:4\n', 'UBERON_ro:0002328_GO:4\n', 'CL_bfo:0000051_GO:4\n', 'CL_cl:4030045_GO:4\n', 'GO_ro:0002342_UBERON:4\n', 'GO_ro:0004007_SO:4\n', 'RO_relationship_destination_SO:4\n', 'SO_relationship_destination_IS:4\n', 'SO_is_a_SO:4\n', 'GO_ro:0019000_PATO:4\n', 'UBERON_bspo:0015101_UBERON:4\n', 'UBERON_ro:0002285_UBERON:4\n', 'UBERON_bspo:0000096_UBERON:4\n', 'UBERON_bfo:0000051_GO:4\n', 'GO_ro:0004009_UBERON:4\n', 'UBERON_core#channels:from_UBERON:4\n', 'UBERON_ro:0002488_UBERON:4\n', 'UBERON_ro:0002385_UBERON:4\n', 'UBERON_bspo:0000098_UBERON:4\n', 'UBERON_bspo:0015102_UBERON:4\n', 'UBERON_ro:0003000_PR:4\n', 'GO_ro:0004008_PR:4\n', 'GO_ro:0002343_CL:4\n', 'IS_relationship_destination_PATO:4\n', 'RO_relationship_destination_PO:4\n', 'PO_relationship_destination_RO:4\n', 'CL_ro:0002220_UBERON:4\n', 'UBERON_core#filtered:through_UBERON:4\n', 'GO_ro:0002234_CHEBI:4\n', 'FAO_relationship_destination_RO:4\n', 'FAO_ro:0002202_FAO:4\n', 'FAO_is_a_BFO:4\n', 'BFO_relationship_destination_FAO:4\n', 'IS_relationship_destination_SO:4\n', 'UBERON_ro:0002353_GO:4\n', 'UBERON_core#proximally:connected:to_UBERON:4\n', 'PO_ro:0002160_NCBITAXON:4\n', 'UBERON_core#channels:into_UBERON:4\n', 'UBERON_core#channel:for_CL:4\n', 'GO_ro:0002343_UBERON:4\n', 'GO_ro:0040036_UBERON:4\n', 'GO_gorel:0002003_GO:4\n', 'UBERON_bfo:0000051_PR:4\n', 'UBERON_ro:0002177_UBERON:4\n', 'UBERON_ro:0002492_UBERON:4\n', 'PATO_relationship_destination_RO:4\n', 'PATO_ro:0015011_PATO:4\n', 'PR_ro:0002160_NCBITAXON:4\n', 'UBERON_bspo:0005001_UBERON:4\n', 'SO_is_a_CHEBI:4\n', 'IS_relationship_destination_PO:4\n', 'PO_is_a_PO:4\n', 'PO_ro:0000057_PO:4\n', 'CHEBI_is_a_SO:4\n', 'UBERON_ro:0002351_UBERON:4\n', 'GO_ro:0002299_GO:4\n', 'UBERON_is_a_GO:4\n', 'CL_bfo:0000051_CL:4\n', 'CL_is_a_GO:4\n', 'UBERON_bspo:0000123_UBERON:4\n', 'UBERON_bspo:0000122_UBERON:4\n', 'GO_ro:0002588_UBERON:4\n', 'CL_ro:0002104_PR:4\n', 'CL_ro:0001025_UBERON:4\n', 'UBERON_ro:0002103_CL:4\n', 'UBERON_ro:0001015_UBERON:4\n', 'UBERON_ro:0002489_UBERON:4\n', 'UBERON_ro:0003000_UBERON:4\n', 'UBERON_ro:0002221_CL:4\n', 'GO_ro:0002338_CL:4\n', 'UBERON_ro:0002374_UBERON:4\n', 'GO_bfo:0000050_FAO:4\n', 'UBERON_core#distally:connected:to_UBERON:4\n', 'UBERON_bspo:0001113_UBERON:4\n', 'UBERON_core#posteriorly:connected:to_UBERON:4\n', 'UBERON_core#anteriorly:connected:to_UBERON:4\n', 'UBERON_ro:0002372_UBERON:4\n', 'UBERON_core#indirectly:supplies_UBERON:4\n', 'UBERON_bspo:0000100_UBERON:4\n', 'UBERON_core#channel:for_UBERON:4\n', 'CL_is_a_UBERON:7\n', 'CL_ro:0015015_PR:4\n', 'CL_cl:4030046_PR:4\n', 'CL_bfo:0000051_PR:4\n', 'CL_cl:4030045_PR:4\n', 'UBERON_ro:0002220_CL:4\n', 'GO_ro:0002339_CL:4\n', 'BFO_relationship_destination_PR:4\n', 'PR_bfo:0000051_PR:4\n', 'GO_bfo:0000051_PR:4\n', 'PR_pr#has:gene:template_SO:4\n', 'PR_relationship_destination_RO:4\n', 'UBERON_ro:0002225_UBERON:4\n', 'UBERON_ro:0002202_CL:4\n', 'UBERON_bfo:0000050_NCBITAXON:4\n', 'BFO_relationship_destination_NCBITAXON:4\n', 'PO_relationship_destination_BFO:4\n', 'PO_bfo:0000050_PO:4\n', 'PO_ro:0002202_PO:4\n', 'PO_relationship_destination_IS:4\n', 'OPL_relationship_destination_IS:4\n', 'OPL_is_a_OPL:4\n', 'RO_relationship_destination_OPL:4\n', 'OPL_relationship_destination_RO:4\n', 'OPL_ro:0002162_OPL:4\n', 'GO_ro:0012008_UBERON:4\n', 'BFO_relationship_destination_PO:4\n', 'GO_ro:0002355_PO:4\n', 'PO_ro:0000056_PO:4\n', 'PO_bfo:0000051_PO:4\n', 'PO_is_a_BFO:4\n', 'GO_ro:0000057_UBERON:4\n', 'IS_relationship_destination_OPL:4\n', 'OPL_ro:0002162_NCBITAXON:4\n', 'GO_ro:0000057_PO:4\n', 'PO_is_a_UBERON:4\n', 'OPL_relationship_destination_BFO:4\n', 'OPL_bfo:0000055_IDO:4\n', 'UBERON_ro:0002131_CL:4\n', 'UBERON_bspo:0001106_UBERON:4\n', 'OPL_is_a_OBI:4\n', 'OPL_is_a_BFO:4\n', 'OPL_is_a_UBERON:4\n', 'UBERON_bspo:0001107_UBERON:4\n', 'GO_ro:0002295_UBERON:4\n', 'UBERON_core#protects_UBERON:4\n', 'GO_bfo:0000063_GO:4\n', 'GO_bfo:0000062_GO:4\n', 'CL_cl:4030046_GO:4\n', 'PO_ro:0002220_PO:4\n', 'CL_ro:0003000_GO:4\n', 'CL_ro:0015016_PR:4\n', 'CL_ro:0015015_GO:4\n', 'INVERSEOF_relationship_destination_RO:4\n', 'RO_inverseof_RO:4\n', 'RO_relationship_destination_INVERSEOF:4\n', 'SUBPROPERTYOF_relationship_destination_RO:4\n', 'CL_ro:0015016_GO:4\n', 'UBERON_ro:0002385_CL:4\n', 'GO_ro:0002565_GO:4\n', 'CL_ro:0002207_CL:4\n', 'UBERON_ro:0002162_NCBITAXON:4\n', 'UBERON_bspo:0001115_UBERON:4\n', 'CL_ro:0002103_CL:4\n', 'UBERON_core#extends:fibers:into_CL:4\n', 'UBERON_bspo:0000097_UBERON:4\n', 'UBERON_bspo:0000108_UBERON:4\n', 'CL_ro:0002102_UBERON:4\n', 'GO_ro:0002295_CL:4\n', 'IS_relationship_destination_BFO:4\n', 'BFO_is_a_BFO:7\n', 'SUBPROPERTYOF_relationship_destination_BFO:4\n', 'RO_subpropertyof_BFO:4\n', 'BFO_relationship_destination_INVERSEOF:4\n', 'BFO_inverseof_BFO:4\n', 'BFO_subpropertyof_RO:4\n', 'INVERSEOF_relationship_destination_BFO:4\n', 'BFO_relationship_destination_IDO:4\n', 'BFO_relationship_destination_MOD:4\n', 'GO_is_a_BFO:7\n', 'CARO_is_a_BFO:4\n', 'CHEBI_is_a_BFO:4\n', 'BFO_relationship_destination_IS:4\n', 'PATO_is_a_BFO:7\n', 'UBERON_bspo:0000124_UBERON:4\n', 'GO_ro:0002343_FAO:4\n', 'RO_relationship_destination_DDANAT:4\n', 'RO_relationship_destination_NBO:4\n', 'UBERON_bspo:0000102_UBERON:4\n', 'RO_relationship_destination_ENVO:4\n', 'UBERON_core#layer:part:of_UBERON:4\n', 'GOREL_subpropertyof_RO:4\n', 'PR_is_a_GO:4\n', 'GO_ro:0004007_GO:4\n', 'GOREL_relationship_destination_SUBPROPERTYOF:4\n', 'GO_ro:0002296_DDANAT:4\n', 'UBERON_bspo:0001108_UBERON:4\n', 'GOCHE_is_a_CHEBI:4\n', 'UBERON_ro:0002497_UBERON:4\n', 'UBERON_is_a_CARO:4\n', 'UBERON_ro:0002002_UBERON:4\n', 'UBERON_ro:0002087_UBERON:4\n', 'UBERON_bfo:0000063_UBERON:4\n', 'UBERON_bfo:0000062_UBERON:4\n', 'UBERON_ro:0002180_UBERON:4\n', 'UBERON_ro:0002230_UBERON:4\n', 'UBERON_ro:0002223_UBERON:4\n', 'UBERON_ro:0002496_UBERON:4\n', 'UBERON_ro:0002216_NBO:4\n', 'UBERON_bspo:0000107_UBERON:4\n', 'UBERON_ro:0002159_UBERON:4\n', 'UBERON_bspo:0001101_UBERON:4\n', 'UBERON_bspo:0001100_UBERON:4\n', 'GO_gorel:0000040_GO:4\n', 'UBERON_ro:0002215_NBO:4\n', 'GO_ro:0002608_SO:4\n', 'CL_ro:0002202_UBERON:4\n', 'PO_ro:0001025_PO:4\n', 'UBERON_ro:0002568_UBERON:4\n', 'UBERON_bfo:0000050_CL:4\n', 'PO_is_a_CARO:4\n', 'CARO_relationship_destination_IS:4\n', 'CARO_is_a_CARO:4\n', 'IS_relationship_destination_CARO:4\n', 'PR_ro:0002215_GO:4\n', 'NCBITAXON_is_a_OBI:4\n', 'IS_relationship_destination_DDANAT:4\n', 'DDANAT_is_a_DDANAT:4\n', 'UBERON_core#sexually:homologous:to_UBERON:4\n', 'GO_ro:0002233_CHEBI:4\n', 'GO_ro:0002608_UBERON:4\n', 'DDANAT_relationship_destination_IS:4\n', 'DDANAT_ddanat#part:of_DDANAT:4\n', 'DDANAT_ddanat#develops:from_DDANAT:4\n', 'UBERON_bspo:0015014_UBERON:4\n', 'CHEBI_is_a_PATO:7\n', 'OBA_is_a_PATO:4\n', 'GO_ro:0002353_GO:4\n', 'SUBPROPERTYOF_relationship_destination_BSPO:4\n', 'GO_ro:0002090_GO:4\n', 'GO_ro:0002093_GO:4\n', 'GO_ro:0002087_GO:4\n', 'IS_relationship_destination_OBI:4\n']








"""
import asyncio

from gnn.graph_helper.validate_node_layer import id_clasiication
from gnn.processing.layer.goterm.extract_id import aget_id
from utils.file.flatten_dict import flatten_attributes
from utils.utils import GraphUtils


class GoTermLayer:
    """
    Todo fetch add details!!
    https://www.ebi.ac.uk/QuickGO/api/index.html#!/gene_products/findByIdUsingGET
    or go website
    """
    def __init__(self, parent, layer):
        self.g_utils = GraphUtils(table_name=layer)
        self.layer = layer
        self.parent = parent

    async def _check_edges(self):
        """
        Todo: check each goterm edge if maybe not existing in nodes. if: api fetch data -> node
        :return:
        """
        return

    async def process_nodes(self, goterm):
        goterm["id"] = await aget_id(goterm["id"])
        goterm["parent"]=self.parent
        goterm["type"] = id_clasiication(goterm["id"])

        try:
            flattened_goterm = flatten_attributes(goterm)
        except Exception as e:
            print("Failed to flatten:", e)
            return
        await self.g_utils.add_node(
            attrs=flattened_goterm,
        )

    async def process_edges(self, edge):

        edge_id = await aget_id(edge['sub'])
        obj_id = await aget_id(edge['obj'])
        rel = edge['pred']

        await self.g_utils.add_node(
            attrs=dict(
                id=obj_id,
                type=id_clasiication(obj_id),
            ))

        await self.g_utils.add_node(
            attrs=dict(
                id=edge_id,
                type=id_clasiication(obj_id),
            ))

        if rel.startswith("http"):
            rel = await aget_id(rel) # -> RO:XXXXX

            await self.g_utils.add_node(
                attrs=dict(
                    id=rel,
                    type=id_clasiication(rel),
                ))
            await self.g_utils.add_edge(
                src=rel,
                trt=obj_id,
                attrs=dict(rel="relationship_destination")
            )

            await self.g_utils.add_edge(
                src=edge_id,
                trt=rel,
                attrs=dict(rel="relationship_destination")
            )
        else:
            await self.g_utils.add_edge(
                src=edge_id,
                trt=obj_id,
                attrs=dict(rel=rel)
            )





    async def process(self, data):
        print("Convert go ids")
        tasks = [self.process_nodes(goterm) for goterm in data["graphs"][0]['nodes']]
        await asyncio.gather(*tasks)
        print("Nodes Processed")
        ed_t = [self.process_edges(edge) for edge in data["graphs"][0].get("edges", [])]
        await asyncio.gather(*ed_t)
        print("Finished Graph creation")


